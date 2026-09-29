"""
Multi-Factor Risk Fusion Engine.
Combines Supervised Probability, Unsupervised Anomaly Score, Graph Topology Risk,
Behavioral Dynamics, and Network Telemetry into a calibrated 0-100 Risk Score.
"""

import logging
from typing import Dict, Any, Tuple
import numpy as np

logger = logging.getLogger(__name__)

class RiskFusionEngine:
    """Calculates weighted multi-modal risk score and assigns severity tier."""

    DEFAULT_WEIGHTS = {
        "classification": 0.40,
        "anomaly": 0.20,
        "graph": 0.20,
        "behavior": 0.10,
        "network": 0.10
    }

    SEVERITY_TIERS = [
        (75.0, "Critical"),
        (50.0, "High"),
        (25.0, "Medium"),
        (0.0, "Low")
    ]

    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or self.DEFAULT_WEIGHTS
        # Normalize weights to sum to 1.0
        total = sum(self.weights.values())
        self.weights = {k: v / total for k, v in self.weights.items()}

    def compute_risk_score(
        self,
        prob_illicit: float,
        anomaly_score: float,
        graph_risk: float,
        behavior_risk: float,
        network_risk: float
    ) -> Tuple[float, str]:
        """
        Computes composite 0-100 risk score and severity level string.
        """
        # Clamp inputs to [0, 1]
        p = np.clip(prob_illicit, 0.0, 1.0)
        a = np.clip(anomaly_score, 0.0, 1.0)
        g = np.clip(graph_risk, 0.0, 1.0)
        b = np.clip(behavior_risk, 0.0, 1.0)
        n = np.clip(network_risk, 0.0, 1.0)

        raw_score = (
            self.weights["classification"] * p +
            self.weights["anomaly"] * a +
            self.weights["graph"] * g +
            self.weights["behavior"] * b +
            self.weights["network"] * n
        ) * 100.0

        score = round(float(np.clip(raw_score, 0.0, 100.0)), 2)

        # Determine severity level
        severity = "Low"
        for threshold, level in self.SEVERITY_TIERS:
            if score >= threshold:
                severity = level
                break

        return score, severity
