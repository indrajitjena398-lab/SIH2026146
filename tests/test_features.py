import pytest
import pandas as pd
import numpy as np
from src.features.transaction_features import compute_transaction_features
from src.features.behavioral_features import compute_behavioral_features
from src.features.network_features import compute_network_features
from src.features.graph_features import compute_graph_features
from src.features.feature_pipeline import FeaturePipeline

def test_feature_extraction_pipeline():
    df_tx = pd.DataFrame({
        "txid": ["tx_1", "tx_2"],
        "time_step": [1, 2],
        "label": ["licit", "illicit"],
        "is_illicit": [0, 1],
        "is_labeled": [1, 1],
        "feat_0": [0.5, 2.5],
        "feat_1": [1.0, 5.0]
    })
    df_edges = pd.DataFrame({"source_txid": ["tx_1"], "target_txid": ["tx_2"]})
    df_net = pd.DataFrame({
        "txid": ["tx_1", "tx_2"],
        "src_ip": ["88.198.54.2", "185.220.101.5"],
        "geo_country": ["DE", "IS"],
        "asn": ["AS24940", "AS200651"],
        "packet_count": [10, 100],
        "bytes_in": [1000, 50000],
        "connection_duration": [1.0, 0.05],
        "scenario": ["normal_propagation", "burst_behavior"]
    })

    pipeline = FeaturePipeline()
    df_all = pipeline.build_features(df_tx, df_edges, df_net)

    assert "tx_fan_out_ratio" in df_all.columns
    assert "behavior_velocity_index" in df_all.columns
    assert "net_high_risk_asn_flag" in df_all.columns
    assert "graph_pagerank" in df_all.columns
    assert len(df_all) == 2
