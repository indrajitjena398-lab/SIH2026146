"""
Alert Generation & Prioritization Engine.
Generates structured investigative alert records with evidence payloads and risk levels.
"""

import uuid
import datetime
import logging
from typing import Dict, List, Any, Optional
import pandas as pd
from .risk_fusion import RiskFusionEngine
from src.explainability.evidence_generator import EvidenceGenerator

logger = logging.getLogger(__name__)

class AlertEngine:
    """Generates prioritized investigation alerts."""

    def __init__(self, min_alert_threshold: float = 30.0):
        self.min_alert_threshold = min_alert_threshold
        self.risk_engine = RiskFusionEngine()

    def generate_alerts_dataframe(
        self,
        df_predictions: pd.DataFrame,
        df_tx: pd.DataFrame,
        df_net: pd.DataFrame,
        model_version: str = "v1.0-xgboost"
    ) -> pd.DataFrame:
        """Processes predictions and generates scored alert records."""
        alerts = []
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        for idx, row in df_predictions.iterrows():
            txid = str(row["txid"])
            prob_illicit = float(row.get("prob_illicit", 0.0))
            anomaly_score = float(row.get("anomaly_score", 0.0))
            graph_risk = float(row.get("graph_risk", 0.0))
            behavior_risk = float(row.get("behavior_risk", 0.0))
            network_risk = float(row.get("network_risk", 0.0))

            score, severity = self.risk_engine.compute_risk_score(
                prob_illicit=prob_illicit,
                anomaly_score=anomaly_score,
                graph_risk=graph_risk,
                behavior_risk=behavior_risk,
                network_risk=network_risk
            )

            if score < self.min_alert_threshold:
                continue

            # Gather supporting evidence
            graph_ev = {
                "in_degree": int(row.get("graph_in_degree", 1)),
                "out_degree": int(row.get("graph_out_degree", 1)),
                "neighbor_illicit_ratio": float(row.get("graph_neighbor_illicit_ratio", 0.0))
            }
            net_ev = {
                "has_high_risk_asn": bool(row.get("net_high_risk_asn_flag", 0)),
                "is_burst": bool(row.get("net_burst_scenario_flag", 0)),
                "ip_count": int(row.get("net_ip_count", 1)),
                "asn": str(row.get("asn", "UNKNOWN"))
            }

            shap_contribs = row.get("shap_contributions", [])
            if not isinstance(shap_contribs, list):
                shap_contribs = []

            reasons = EvidenceGenerator.synthesize_reasons(
                shap_contributions=shap_contribs,
                graph_evidence=graph_ev,
                network_evidence=net_ev,
                risk_score=score
            )

            alerts.append({
                "alert_id": f"ALT-{uuid.uuid4().hex[:8].upper()}",
                "entity_id": txid,
                "entity_type": "Transaction",
                "transaction_id": txid,
                "risk_score": score,
                "risk_level": severity,
                "classification_probability": round(prob_illicit, 4),
                "anomaly_score": round(anomaly_score, 4),
                "top_reason": reasons[0] if reasons else "Elevated risk pattern detected",
                "top_reasons_json": str(reasons),
                "evidence_json": str({
                    "graph": graph_ev,
                    "network": net_ev,
                    "shap": shap_contribs
                }),
                "status": "New",
                "timestamp": now_iso,
                "model_version": model_version
            })

        df_alerts = pd.DataFrame(alerts)
        if not df_alerts.empty:
            df_alerts = df_alerts.sort_values(by="risk_score", ascending=False).reset_index(drop=True)

        logger.info("Generated %d alerts (Threshold >= %.1f)", len(df_alerts), self.min_alert_threshold)
        return df_alerts
