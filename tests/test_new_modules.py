import networkx as nx
import pandas as pd
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.entity_cluster import get_entity_clusters
from backend.services.patterns import detect_coinjoin, detect_peeling_chain, evaluate_all_patterns
from backend.services.taint import calculate_taint_propagation


def build_graph():
    graph = nx.DiGraph()
    graph.add_node("wallet_seed", entity_id="seed", entity_type="Wallet")
    graph.add_node("tx_a", entity_id="tx_a", entity_type="Transaction", time_step=1, input_amount=4.0)
    graph.add_node("tx_b", entity_id="tx_b", entity_type="Transaction", time_step=2, input_amount=3.0)
    graph.add_node("tx_c", entity_id="tx_c", entity_type="Transaction", time_step=3, input_amount=2.0)
    graph.add_node("wallet_other", entity_id="other", entity_type="Wallet")
    graph.add_edge("wallet_seed", "tx_a", relation="INPUT_TO")
    graph.add_edge("tx_a", "tx_b", relation="FOLLOWS")
    graph.add_edge("tx_b", "tx_c", relation="FOLLOWS")
    graph.add_edge("tx_c", "wallet_other", relation="OUTPUT_TO")
    return graph


def test_taint_propagation_normalizes_downstream_scores():
    scores = calculate_taint_propagation(build_graph(), ["seed"], max_hops=4)
    assert scores["wallet_seed"] == 100.0
    assert scores["tx_a"] > 0
    assert scores["tx_c"] > 0


def test_pattern_detectors_return_badges():
    graph = build_graph()
    record = {"txid": "tx_a", "input_count": 1, "output_count": 2, "output_values": [0.2, 4.0]}
    assert detect_peeling_chain(record, graph) is not None
    assert detect_coinjoin({"input_count": 5, "output_count": 5, "output_values": [1, 1, 1, 1, 1]})["pattern"] == "coinjoin"
    assert isinstance(evaluate_all_patterns(record, graph), list)


def test_common_input_cluster_aggregation():
    graph = nx.DiGraph()
    graph.add_node("w1", entity_id="wallet-1", entity_type="Wallet")
    graph.add_node("w2", entity_id="wallet-2", entity_type="Wallet")
    graph.add_node("tx", entity_id="tx-1", entity_type="Transaction", input_amount=12.5, risk_score=80)
    graph.add_edge("w1", "tx", relation="INPUT_TO")
    graph.add_edge("w2", "tx", relation="INPUT_TO")
    clusters = get_entity_clusters(graph)
    assert len(clusters) == 1
    assert set(clusters[0]["wallets"]) == {"wallet-1", "wallet-2"}
    assert clusters[0]["total_balance_moved"] == 12.5


def test_taint_api_validation():
    client = TestClient(app)
    response = client.post("/api/taint/propagate", json={"seed_wallets": []})
    assert response.status_code == 422


def test_graph_entities_endpoint():
    response = TestClient(app).get("/api/graph/entities")
    assert response.status_code == 200
    assert "clusters" in response.json()


def test_stix_export_endpoint():
    client = TestClient(app)
    alerts = client.get("/api/alerts?limit=1").json()["alerts"]
    response = client.get(f"/api/export/stix/{alerts[0]['alert_id']}")
    assert response.status_code == 200
    assert response.json()["type"] == "bundle"


def test_pdf_export_endpoint():
    client = TestClient(app)
    alerts = client.get("/api/alerts?limit=1").json()["alerts"]
    response = client.get(f"/api/export/pdf/{alerts[0]['alert_id']}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
