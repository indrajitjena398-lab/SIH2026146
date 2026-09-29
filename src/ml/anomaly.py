"""
Unsupervised Anomaly Detection Suite.
Implements Isolation Forest, Local Outlier Factor, and a compact deep-style autoencoder anomaly model.
"""

import logging
from typing import Dict, Any, Tuple
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.neural_network import MLPRegressor

logger = logging.getLogger(__name__)


class DeepAutoencoderAnomaly:
    """Small reconstruction-based anomaly model approximating an autoencoder using MLP regression."""

    def __init__(self, hidden_layer_sizes=(32, 16, 32), random_state: int = 42, max_iter: int = 500):
        self.model = MLPRegressor(
            hidden_layer_sizes=hidden_layer_sizes,
            activation="relu",
            solver="adam",
            learning_rate_init=0.001,
            max_iter=max_iter,
            random_state=random_state,
            early_stopping=True,
            n_iter_no_change=20,
        )

    def fit(self, X_train: np.ndarray):
        self.model.fit(X_train, X_train)
        return self

    def score_anomalies(self, X: np.ndarray) -> np.ndarray:
        preds = self.model.predict(X)
        errors = np.mean((X - preds) ** 2, axis=1)
        if errors.size == 0:
            return np.zeros((len(X),), dtype=float)
        lo, hi = np.percentile(errors, [5, 95])
        if hi <= lo:
            hi = lo + 1e-6
        norm = (errors - lo) / (hi - lo)
        return np.clip(norm, 0.0, 1.0)


class AnomalyDetector:
    """Unsupervised anomaly detection models."""

    def __init__(self, contamination: float = 0.05, random_state: int = 42):
        self.contamination = contamination
        self.random_state = random_state
        self.isolation_forest = IsolationForest(
            n_estimators=200,
            contamination=contamination,
            random_state=random_state,
            n_jobs=-1
        )
        self.lof = LocalOutlierFactor(
            n_neighbors=20,
            contamination=contamination,
            novelty=True,
            n_jobs=-1
        )
        self.deep_autoencoder = DeepAutoencoderAnomaly(random_state=random_state)

    def fit(self, X_train: np.ndarray):
        """Fits unsupervised models on feature matrix."""
        logger.info("Fitting Isolation Forest on %d samples...", len(X_train))
        self.isolation_forest.fit(X_train)
        logger.info("Fitting Local Outlier Factor on %d samples...", len(X_train))
        self.lof.fit(X_train)
        logger.info("Fitting deep autoencoder anomaly model on %d samples...", len(X_train))
        self.deep_autoencoder.fit(X_train)

    def score_anomalies(self, X: np.ndarray) -> np.ndarray:
        """
        Computes continuous normalized anomaly score in range [0, 1].
        Higher score = more anomalous.
        """
        raw_scores = self.isolation_forest.score_samples(X)
        norm_scores = 0.5 - (raw_scores / 2.0)
        norm_scores = np.clip(norm_scores, 0.0, 1.0)

        auto_scores = self.deep_autoencoder.score_anomalies(X)
        combined = np.clip(0.65 * norm_scores + 0.35 * auto_scores, 0.0, 1.0)
        return combined
