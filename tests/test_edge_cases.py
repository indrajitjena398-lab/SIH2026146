import pytest
from src.ingestion.schema_validator import SchemaValidator
from src.enrichment.geoip import enrich_ip
from src.risk.risk_fusion import RiskFusionEngine

def test_edge_case_empty_and_null_records():
    is_valid, errors = SchemaValidator.validate_transaction_record({})
    assert is_valid is False

def test_edge_case_invalid_ips():
    res1 = enrich_ip("999.999.999.999")
    assert res1["is_valid"] is False
    assert res1["geo_country"] == "UNKNOWN"

    res2 = enrich_ip("not_an_ip")
    assert res2["is_valid"] is False

    res3 = enrich_ip("")
    assert res3["is_valid"] is False

def test_edge_case_risk_boundaries():
    engine = RiskFusionEngine()
    # Clamping extreme inputs
    score_max, _ = engine.compute_risk_score(2.0, 5.0, 10.0, 5.0, 5.0)
    assert score_max <= 100.0

    score_min, _ = engine.compute_risk_score(-1.0, -5.0, -10.0, 0.0, 0.0)
    assert score_min >= 0.0
