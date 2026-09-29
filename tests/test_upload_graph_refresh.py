import os
import pandas as pd

from backend.api.ingestion import refresh_runtime_dataset_from_dataframe
from backend.services.alert_service import AlertService
from backend.services.graph_service import GraphService


def test_refresh_runtime_dataset_from_uploaded_csv(tmp_path):
    csv_path = tmp_path / "uploaded_transactions.csv"
    df = pd.DataFrame(
        {
            "transaction_hash": ["tx_100", "tx_101"],
            "timestamp": ["2025-03-03T14:38:43+00:00", "2025-03-04T14:38:43+00:00"],
            "sender_address": ["1BtcSend_7912", "1BtcSend_4611"],
            "receiver_address": ["3BtcRecv_1520", "3BtcRecv_8359"],
            "amount_btc": [1.7935, 4.4943],
            "fee_btc": [0.000234, 0.000229],
            "input_count": [2, 1],
            "output_count": [2, 1],
            "source_ip": ["103.28.249.1", "88.198.54.2"],
            "destination_ip": ["54.39.130.10", "54.39.130.10"],
            "port": [8333, 8333],
            "asn": ["AS133119", "AS24940"],
            "asn_organization": ["Tencent Cloud APAC", "Hetzner Datacenter"],
            "country": ["SG", "DE"],
        }
    )
    df.to_csv(csv_path, index=False)

    GraphService._cached_graph = None
    refresh_runtime_dataset_from_dataframe(df, str(csv_path), "uploaded_transactions.csv")

    stats = AlertService.get_statistics()
    assert stats["total_transactions"] >= 2
    graph = GraphService.get_graph()
    assert graph.number_of_nodes() > 0
    assert "tx_tx_100" in graph


def test_refresh_runtime_dataset_from_real_testsample_csv():
    csv_path = os.path.join("data", "demo", "testsample.csv")
    assert os.path.exists(csv_path)

    df = pd.read_csv(csv_path)
    assert len(df) > 0

    GraphService._cached_graph = None
    result = refresh_runtime_dataset_from_dataframe(df, csv_path, "testsample.csv")

    assert result["records_loaded"] == len(df)
    stats = AlertService.get_statistics()
    assert stats["total_transactions"] >= len(df)
    graph = GraphService.get_graph()
    assert graph.number_of_nodes() > 0
