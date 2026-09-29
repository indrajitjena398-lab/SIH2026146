import pytest
from starlette.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["database"] == "DuckDB Connected"

def test_api_statistics():
    res = client.get("/api/statistics")
    assert res.status_code == 200
    data = res.json()
    assert data["total_transactions"] > 0
    assert "critical_alerts" in data
    assert "activity_over_time" in data

def test_api_alerts_and_detail():
    res = client.get("/api/alerts?limit=5")
    assert res.status_code == 200
    alerts = res.json()["alerts"]
    assert len(alerts) > 0

    first_id = alerts[0]["alert_id"]
    detail_res = client.get(f"/api/alerts/{first_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["alert_id"] == first_id

def test_api_search():
    res = client.get("/api/search?q=ALT")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_api_graph_subgraph():
    alerts_res = client.get("/api/alerts?limit=1")
    first_tx = alerts_res.json()["alerts"][0]["transaction_id"]
    res = client.get(f"/api/graph/subgraph?entity_id={first_tx}&depth=2")
    assert res.status_code == 200
    assert "nodes" in res.json()
    assert "edges" in res.json()

def test_api_model_metrics():
    res = client.get("/api/models/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "metrics" in data
    assert "xgboost" in data["metrics"]
