#!/usr/bin/env python3
"""
Model Training, Temporal Evaluation & Risk Calibration Pipeline.
Trains supervised and anomaly detection models, computes SHAP attributions,
evaluates performance without temporal leakage, and outputs model artifacts.
"""

import os
import sys
import json
import logging
import argparse
import datetime
import glob
import joblib
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scripts.generate_network_data import generate_minimum_synthetic_dataset
from src.ml.temporal_split import TemporalSplitter
from src.ml.classifiers import ModelTrainer
from src.ml.anomaly import AnomalyDetector
from src.ml.evaluator import ModelEvaluator
from src.features.feature_pipeline import FeaturePipeline
from src.explainability.shap_explainer import ShapExplainerService
from src.risk.alert_engine import AlertEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("train_models")

MODELS_DIR = "models"
CLASSIFIER_DIR = os.path.join(MODELS_DIR, "classifier")
ANOMALY_DIR = os.path.join(MODELS_DIR, "anomaly")
METRICS_DIR = os.path.join(MODELS_DIR, "metrics")
PREPROCESSORS_DIR = os.path.join(MODELS_DIR, "preprocessors")


def cleanup_old_artifacts():
    """Remove stale joblib artifacts to force fresh model rebuilds."""
    for directory in [CLASSIFIER_DIR, ANOMALY_DIR, PREPROCESSORS_DIR, METRICS_DIR]:
        os.makedirs(directory, exist_ok=True)
    for pattern in [
        os.path.join(CLASSIFIER_DIR, "*.joblib"),
        os.path.join(ANOMALY_DIR, "*.joblib"),
        os.path.join(PREPROCESSORS_DIR, "*.joblib"),
        os.path.join(METRICS_DIR, "*.json"),
        os.path.join(MODELS_DIR, "model_metadata.json"),
        os.path.join(MODELS_DIR, "predictions.parquet"),
        os.path.join(MODELS_DIR, "alerts.parquet"),
    ]:
        for path in glob.glob(pattern):
            try:
                os.remove(path)
                logger.info("Removed stale artifact: %s", path)
            except OSError:
                pass


def main():
    parser = argparse.ArgumentParser(description="Train Bitcoin transaction detection models.")
    parser.add_argument("--features", default="data/processed/features_matrix.parquet")
    parser.add_argument("--transactions", default="data/processed/canonical_transactions.parquet")
    parser.add_argument("--network", default="data/processed/canonical_network_events.parquet")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    cleanup_old_artifacts()

    if not os.path.exists(args.features):
        logger.warning("Features matrix not found at %s. Generating a minimum-schema synthetic training dataset.", args.features)
        output_dir = os.path.dirname(args.features) or "data/processed"
        os.makedirs(output_dir, exist_ok=True)
        df_tx = generate_minimum_synthetic_dataset(num_rows=1000, seed=args.seed, suspicious_ratio=0.2)
        df_tx["input_count"] = df_tx["input_amounts"].apply(lambda x: len(json.loads(x)))
        df_tx["output_count"] = df_tx["output_amounts"].apply(lambda x: len(json.loads(x)))
        df_tx["input_amount"] = df_tx["input_amounts"].apply(lambda x: sum(json.loads(x)))
        df_tx["output_amount"] = df_tx["output_amounts"].apply(lambda x: sum(json.loads(x)))
        df_tx["time_step"] = np.arange(1, len(df_tx) + 1)
        df_tx["timestamp"] = pd.to_datetime(df_tx["timestamp"]).astype(str)
        df_tx["label"] = df_tx["label"].replace({"licit": "licit", "illicit": "illicit"})
        df_tx["is_labeled"] = 1
        df_tx["is_synthetic"] = True
        df_features = FeaturePipeline().build_features(df_tx, pd.DataFrame(), pd.DataFrame())
        df_features.to_parquet(args.features, index=False)
        df_tx.to_parquet(args.transactions, index=False)
        logger.info("Generated fallback synthetic feature matrix at %s and canonical transactions at %s", args.features, args.transactions)
    else:
        df_features = pd.read_parquet(args.features)
        logger.info("Loaded features matrix with %d rows and %d columns", len(df_features), df_features.shape[1])

    # 1. Temporal Split
    splitter = TemporalSplitter(train_timesteps=(1, 34), val_timesteps=(35, 41), test_timesteps=(42, 49))
    splits = splitter.split_temporal(df_features)

    df_train = splits["train"]
    df_val = splits["val"]
    df_test = splits["test"]

    # Feature columns (exclude metadata)
    meta_cols = {"txid", "time_step", "label", "is_illicit", "is_labeled"}
    feature_cols = [c for c in df_features.columns if c not in meta_cols]

    pipeline = FeaturePipeline(output_dir=PREPROCESSORS_DIR)
    pipeline.feature_columns = feature_cols

    # Fit scaler strictly on training split
    X_train_scaled, scaler = pipeline.fit_transform_scaler(df_train)
    y_train = df_train["is_illicit"].values

    X_val_scaled = pipeline.transform(df_val)
    y_val = df_val["is_illicit"].values

    X_test_scaled = pipeline.transform(df_test)
    y_test = df_test["is_illicit"].values

    logger.info("Feature scaling fitted on train set: %d features", len(feature_cols))

    # 2. Train Supervised Models
    pos_count = max(1, int(y_train.sum()))
    neg_count = max(1, len(y_train) - pos_count)
    scale_pos_weight = float(neg_count / pos_count)
    logger.info("Calculated class imbalance scale_pos_weight: %.2f", scale_pos_weight)

    models = ModelTrainer.get_models(scale_pos_weight=scale_pos_weight, random_state=args.seed)
    trained_models = {}
    model_metrics = {}
    model_curves = {}

    for name, model in models.items():
        logger.info("Training supervised model: %s...", name)
        model.fit(X_train_scaled, y_train)
        trained_models[name] = model

        # Evaluate on Test Split (Temporal)
        y_prob_test = model.predict_proba(X_test_scaled)[:, 1] if hasattr(model, "predict_proba") else model.predict(X_test_scaled)
        metrics = ModelEvaluator.evaluate_predictions(y_test, y_prob_test, threshold=0.5)
        sweep = ModelEvaluator.threshold_sweep(y_test, y_prob_test)
        curves = ModelEvaluator.compute_curves(y_test, y_prob_test)

        metrics["threshold_sweep"] = sweep
        model_metrics[name] = metrics
        model_curves[name] = curves

        # Save model artifact
        model_save_path = os.path.join(CLASSIFIER_DIR, f"{name}.joblib")
        joblib.dump(model, model_save_path)
        logger.info("Model %s Test F1: %.4f, PR-AUC: %.4f, ROC-AUC: %.4f, MCC: %.4f", name, metrics["f1"], metrics["pr_auc"], metrics["roc_auc"], metrics["mcc"])

    # 3. Train Unsupervised Anomaly Detection (Isolation Forest + Deep Autoencoder)
    anomaly_detector = AnomalyDetector(contamination=0.05, random_state=args.seed)
    anomaly_detector.fit(X_train_scaled)
    joblib.dump(anomaly_detector, os.path.join(ANOMALY_DIR, "anomaly_detector.joblib"))
    joblib.dump(anomaly_detector.deep_autoencoder, os.path.join(ANOMALY_DIR, "deep_autoencoder.joblib"))

    # Anomaly scores
    test_anomaly_scores = anomaly_detector.score_anomalies(X_test_scaled)
    model_metrics["isolation_forest"] = {
        "mean_anomaly_score_illicit": round(float(test_anomaly_scores[y_test == 1].mean()) if (y_test == 1).sum() > 0 else 0.0, 4),
        "mean_anomaly_score_licit": round(float(test_anomaly_scores[y_test == 0].mean()) if (y_test == 0).sum() > 0 else 0.0, 4),
        "anomaly_spread": round(float(test_anomaly_scores.max() - test_anomaly_scores.min()), 4)
    }
    model_metrics["deep_autoencoder"] = {
        "mean_anomaly_score_illicit": round(float(anomaly_detector.deep_autoencoder.score_anomalies(X_test_scaled[y_test == 1]).mean()) if (y_test == 1).sum() > 0 else 0.0, 4),
        "mean_anomaly_score_licit": round(float(anomaly_detector.deep_autoencoder.score_anomalies(X_test_scaled[y_test == 0]).mean()) if (y_test == 0).sum() > 0 else 0.0, 4)
    }

    # 4. Also evaluate Random Split Baseline to document data leakage
    random_splits = splitter.split_random_baseline(df_features, seed=args.seed)
    rf_leak_model = models["random_forest"]
    X_rnd_train = scaler.transform(random_splits["train"][feature_cols].values)
    y_rnd_train = random_splits["train"]["is_illicit"].values
    X_rnd_test = scaler.transform(random_splits["test"][feature_cols].values)
    y_rnd_test = random_splits["test"]["is_illicit"].values
    rf_leak_model.fit(X_rnd_train, y_rnd_train)
    y_rnd_prob = rf_leak_model.predict_proba(X_rnd_test)[:, 1]
    rnd_metrics = ModelEvaluator.evaluate_predictions(y_rnd_test, y_rnd_prob)

    model_metrics["comparison_random_split_baseline"] = {
        "description": "Stratified random split (contains future time leakage)",
        "f1": rnd_metrics["f1"],
        "pr_auc": rnd_metrics["pr_auc"],
        "roc_auc": rnd_metrics["roc_auc"],
        "mcc": rnd_metrics["mcc"]
    }

    # 5. Compute TreeSHAP on Best Model (XGBoost / Random Forest)
    best_model = trained_models["lightgbm"] if "lightgbm" in trained_models else trained_models["xgboost"]
    shap_service = ShapExplainerService(best_model, feature_cols)
    joblib.dump(shap_service, os.path.join(PREPROCESSORS_DIR, "shap_service.joblib"))

    # 6. Global Inference & Risk Scoring across entire dataset
    logger.info("Computing global inference and multi-factor risk scores across all %d transactions...", len(df_features))
    X_all_scaled = scaler.transform(df_features[feature_cols].values)
    all_prob_illicit = best_model.predict_proba(X_all_scaled)[:, 1]
    all_anomaly_scores = anomaly_detector.score_anomalies(X_all_scaled)

    df_predictions = df_features[["txid", "time_step", "label", "is_illicit", "is_labeled"]].copy()
    df_predictions["prob_illicit"] = all_prob_illicit
    df_predictions["anomaly_score"] = all_anomaly_scores
    
    # Feature columns for risk fusion
    df_predictions["graph_risk"] = df_features.get("graph_neighbor_illicit_ratio", 0.0) * 0.7 + df_features.get("graph_pagerank", 0.0) * 100.0 * 0.3
    df_predictions["behavior_risk"] = np.clip(df_features.get("behavior_velocity_index", 0.0) / 5.0, 0.0, 1.0)
    df_predictions["network_risk"] = df_features.get("net_high_risk_asn_flag", 0.0) * 0.6 + df_features.get("net_burst_scenario_flag", 0.0) * 0.4

    # Compute individual SHAP contributions for high-probability items
    shap_contributions_list = []
    for i in range(len(df_predictions)):
        if all_prob_illicit[i] >= 0.3 or df_predictions["is_illicit"].iloc[i] == 1:
            contribs = shap_service.explain_sample(X_all_scaled[i], top_k=5)
        else:
            contribs = []
        shap_contributions_list.append(contribs)

    df_predictions["shap_contributions"] = shap_contributions_list
    for extra_col in ["graph_in_degree", "graph_out_degree", "graph_neighbor_illicit_ratio", "net_high_risk_asn_flag", "net_burst_scenario_flag", "net_ip_count", "asn"]:
        if extra_col in df_features.columns:
            df_predictions[extra_col] = df_features[extra_col]

    # 7. Generate Prioritized Alerts
    df_tx = pd.read_parquet(args.transactions) if os.path.exists(args.transactions) else pd.DataFrame()
    df_net = pd.read_parquet(args.network) if os.path.exists(args.network) else pd.DataFrame()

    alert_engine = AlertEngine(min_alert_threshold=25.0)
    df_alerts = alert_engine.generate_alerts_dataframe(df_predictions, df_tx, df_net)

    # Save Predictions & Alerts
    df_predictions_save = df_predictions.drop(columns=["shap_contributions"], errors="ignore")
    df_predictions_save.to_parquet(os.path.join(MODELS_DIR, "predictions.parquet"), index=False)
    df_alerts.to_parquet(os.path.join(MODELS_DIR, "alerts.parquet"), index=False)

    # Save Metrics & Model Metadata JSON
    metrics_path = os.path.join(METRICS_DIR, "model_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(model_metrics, f, indent=2)

    curves_path = os.path.join(METRICS_DIR, "model_curves.json")
    with open(curves_path, "w") as f:
        json.dump(model_curves, f, indent=2)

    # Extract global feature importances for top model
    importances = best_model.feature_importances_
    sorted_idx = np.argsort(importances)[::-1][:20]
    top_features = [{"feature": feature_cols[i], "importance": round(float(importances[i]), 4)} for i in sorted_idx]
    with open(os.path.join(METRICS_DIR, "feature_importance.json"), "w") as f:
        json.dump(top_features, f, indent=2)

    metadata = {
        "best_model": "LightGBM" if "lightgbm" in trained_models else "XGBoost",
        "dataset": "Synthetic Bitcoin transaction telemetry + blockchain metadata",
        "total_transactions": len(df_features),
        "feature_count": len(feature_cols),
        "trained_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "random_seed": args.seed,
        "models_evaluated": list(trained_models.keys()) + ["isolation_forest", "deep_autoencoder"],
        "top_features": top_features[:5]
    }
    with open(os.path.join(MODELS_DIR, "model_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info("Training, evaluation and risk scoring successfully finished!")
    logger.info("Generated %d alerts. Metrics saved to %s", len(df_alerts), metrics_path)

if __name__ == "__main__":
    main()
