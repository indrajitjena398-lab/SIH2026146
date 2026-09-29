import pytest
from src.risk.risk_fusion import RiskFusionEngine
from src.explainability.evidence_generator import EvidenceGenerator

def test_risk_fusion_scoring():
    engine = RiskFusionEngine()
    
    # Critical case
    score_crit, level_crit = engine.compute_risk_score(
        prob_illicit=0.95,
        anomaly_score=0.90,
        graph_risk=0.85,
        behavior_risk=0.80,
        network_risk=0.90
    )
    assert score_crit >= 75.0
    assert level_crit == "Critical"

    # Low case
    score_low, level_low = engine.compute_risk_score(
        prob_illicit=0.05,
        anomaly_score=0.10,
        graph_risk=0.10,
        behavior_risk=0.05,
        network_risk=0.05
    )
    assert score_low < 25.0
    assert level_low == "Low"

def test_evidence_generator_reasons():
    shap_contribs = [{"feature": "tx_fan_out_ratio", "shap_value": 0.35, "feature_value": 8.0}]
    graph_ev = {"in_degree": 1, "out_degree": 10, "neighbor_illicit_ratio": 0.4}
    net_ev = {"has_high_risk_asn": True, "asn": "AS200651", "is_burst": True, "ip_count": 5}
    
    reasons = EvidenceGenerator.synthesize_reasons(shap_contribs, graph_ev, net_ev, risk_score=85.0)
    assert len(reasons) >= 3
    assert any("peel chain" in r.lower() or "fan-out" in r.lower() for r in reasons)
    assert any("as200651" in r.lower() or "high-risk" in r.lower() for r in reasons)
