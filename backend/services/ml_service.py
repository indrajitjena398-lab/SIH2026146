"""
ML & Inference Service.
Manages model artifacts, metrics, and real-time single-transaction inference.
"""

import os
import json
import logging
import joblib
from typing import Dict, List, Any, Optional
import numpy as np

from src.risk.risk_fusion import RiskFusionEngine
from src.explainability.evidence_generator import EvidenceGenerator

logger = logging.getLogger(__name__)

MODELS_DIR = "models"
METRICS_PATH = os.path.join(MODELS_DIR, "metrics", "model_metrics.json")
CURVES_PATH = os.path.join(MODELS_DIR, "metrics", "model_curves.json")
FEATURE_IMPORTANCE_PATH = os.path.join(MODELS_DIR, "metrics", "feature_importance.json")
MODEL_METADATA_PATH = os.path.join(MODELS_DIR, "model_metadata.json")

class MLService:
    """Provides model metadata, benchmark metrics, and on-demand prediction."""

    _models = {}
    _scaler = None
    _feature_columns = None
    _shap_service = None
    _risk_engine = RiskFusionEngine()

    @classmethod
    def load_resources(cls):
        """Loads cached models, scalers, and explainers into memory."""
        try:
            scaler_path = "models/preprocessors/feature_scaler.joblib"
            cols_path = "models/preprocessors/feature_columns.json"
            shap_path = "models/preprocessors/shap_service.joblib"

            if os.path.exists(scaler_path):
                cls._scaler = joblib.load(scaler_path)
            if os.path.exists(cols_path):
                with open(cols_path, "r") as f:
                    cls._feature_columns = json.load(f)
            if os.path.exists(shap_path):
                cls._shap_service = joblib.load(shap_path)

            for m_name in ["xgboost", "random_forest", "extra_trees", "lightgbm", "logistic_regression"]:
                p = f"models/classifier/{m_name}.joblib"
                if os.path.exists(p):
                    cls._models[m_name] = joblib.load(p)

            for anom_name in ["anomaly_detector", "deep_autoencoder"]:
                anom_p = f"models/anomaly/{anom_name}.joblib"
                if os.path.exists(anom_p):
                    cls._models[anom_name] = joblib.load(anom_p)

            logger.info("Loaded %d ML models, scaler, and SHAP service.", len(cls._models))
        except Exception as e:
            logger.warning("Error loading ML resources: %s", e)

    @classmethod
    def get_metrics(cls) -> Dict[str, Any]:
        """Returns model comparison metrics and curves."""
        metrics = {}
        curves = {}
        feat_imp = []
        meta = {}

        if os.path.exists(METRICS_PATH):
            with open(METRICS_PATH, "r") as f:
                metrics = json.load(f)
        if os.path.exists(CURVES_PATH):
            with open(CURVES_PATH, "r") as f:
                curves = json.load(f)
        if os.path.exists(FEATURE_IMPORTANCE_PATH):
            with open(FEATURE_IMPORTANCE_PATH, "r") as f:
                feat_imp = json.load(f)
        if os.path.exists(MODEL_METADATA_PATH):
            with open(MODEL_METADATA_PATH, "r") as f:
                meta = json.load(f)

        return {
            "metrics": metrics,
            "curves": curves,
            "feature_importance": feat_imp,
            "metadata": meta
        }

    @classmethod
    def predict_custom_transaction(cls, req_data: Dict[str, Any]) -> Dict[str, Any]:
        """Runs real-time inference on arbitrary transaction inputs."""
        if not cls._models:
            cls.load_resources()

        # Build feature vector
        num_features = len(cls._feature_columns) if cls._feature_columns else 190
        raw_vector = np.zeros((1, num_features), dtype=np.float32)

        # Map provided parameters
        in_amt = float(req_data.get("input_amount", 1.0))
        out_amt = float(req_data.get("output_amount", 1.0))
        fee = float(req_data.get("fee", 0.0001))
        in_cnt = int(req_data.get("input_count", 1))
        out_cnt = int(req_data.get("output_count", 2))
        asn = str(req_data.get("asn", "AS15169"))

        # Ingest custom feature list if provided
        custom_feats = req_data.get("features")
        if custom_feats and len(custom_feats) == num_features:
            raw_vector[0, :] = custom_feats
        else:
            # Synthetic feature vector approximation
            raw_vector[0, 0] = in_cnt
            raw_vector[0, 1] = out_cnt
            raw_vector[0, 2] = fee
            raw_vector[0, 3] = out_amt

        # Scale features
        if cls._scaler:
            X_scaled = cls._scaler.transform(raw_vector)
        else:
            X_scaled = raw_vector

        # Model probabilities
        model = cls._models.get("xgboost") or cls._models.get("random_forest")
        if model and hasattr(model, "predict_proba"):
            prob_illicit = float(model.predict_proba(X_scaled)[0, 1])
        else:
            prob_illicit = 0.5

        # Anomaly score
        anom_det = cls._models.get("anomaly_detector")
        if anom_det:
            anomaly_score = float(anom_det.score_anomalies(X_scaled)[0])
        else:
            anomaly_score = 0.3

        # Heuristic graph and network risk
        is_bulletproof_asn = asn in ["AS200651", "AS60531", "AS206264"]
        network_risk = 0.85 if is_bulletproof_asn else 0.15
        graph_risk = 0.70 if (out_cnt >= 8 and in_cnt <= 2) else 0.20
        behavior_risk = min(1.0, out_cnt / 10.0)

        # Risk fusion
        risk_score, severity = cls._risk_engine.compute_risk_score(
            prob_illicit=prob_illicit,
            anomaly_score=anomaly_score,
            graph_risk=graph_risk,
            behavior_risk=behavior_risk,
            network_risk=network_risk
        )

        # TreeSHAP explanation
        if cls._shap_service:
            shap_contribs = cls._shap_service.explain_sample(X_scaled[0], top_k=5)
        else:
            shap_contribs = []

        reasons = EvidenceGenerator.synthesize_reasons(
            shap_contributions=shap_contribs,
            graph_evidence={"in_degree": in_cnt, "out_degree": out_cnt, "neighbor_illicit_ratio": graph_risk},
            network_evidence={"has_high_risk_asn": is_bulletproof_asn, "asn": asn, "is_burst": False, "ip_count": 1},
            risk_score=risk_score
        )

        return {
            "txid": req_data.get("txid", "custom_tx"),
            "risk_score": risk_score,
            "risk_level": severity,
            "classification_probability": round(prob_illicit, 4),
            "anomaly_score": round(anomaly_score, 4),
            "graph_risk": round(graph_risk, 4),
            "network_risk": round(network_risk, 4),
            "reasons": reasons,
            "shap_contributions": shap_contribs
        }
