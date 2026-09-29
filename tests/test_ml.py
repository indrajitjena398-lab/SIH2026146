import pytest
import numpy as np
import pandas as pd
from src.ml.temporal_split import TemporalSplitter
from src.ml.classifiers import ModelTrainer
from src.ml.anomaly import AnomalyDetector
from src.ml.evaluator import ModelEvaluator

def test_temporal_splitter_no_leakage():
    df = pd.DataFrame({
        "txid": [f"tx_{i}" for i in range(100)],
        "time_step": np.repeat(np.arange(1, 51), 2),
        "is_labeled": [1] * 100,
        "is_illicit": [0, 1] * 50
    })
    splitter = TemporalSplitter(train_timesteps=(1, 34), val_timesteps=(35, 41), test_timesteps=(42, 49))
    splits = splitter.split_temporal(df)

    assert splits["train"]["time_step"].max() <= 34
    assert splits["val"]["time_step"].min() >= 35
    assert splits["val"]["time_step"].max() <= 41
    assert splits["test"]["time_step"].min() >= 42
    assert splits["test"]["time_step"].max() <= 49

def test_classifiers_and_evaluator():
    X = np.random.randn(100, 10)
    y = np.random.choice([0, 1], size=100, p=[0.8, 0.2])

    models = ModelTrainer.get_models()
    for name, model in models.items():
        model.fit(X, y)
        probs = model.predict_proba(X)[:, 1] if hasattr(model, "predict_proba") else model.predict(X)
        metrics = ModelEvaluator.evaluate_predictions(y, probs)
        assert "f1" in metrics
        assert "precision" in metrics
        assert "recall" in metrics
        assert "roc_auc" in metrics

def test_isolation_forest_anomaly_detection():
    X = np.random.randn(100, 10)
    detector = AnomalyDetector()
    detector.fit(X)
    scores = detector.score_anomalies(X)
    assert len(scores) == 100
    assert (scores >= 0.0).all() and (scores <= 1.0).all()
