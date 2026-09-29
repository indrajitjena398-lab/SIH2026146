"""
Network Telemetry Feature Extraction.
Aggregates P2P connection telemetry into transaction-level network signatures.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any

# High risk ASNs known for bulletproof hosting or darknet exit
HIGH_RISK_ASNS = {"AS200651", "AS60531", "AS206264", "AS51852", "AS58271"}

def compute_network_features(df_tx: pd.DataFrame, df_net: pd.DataFrame) -> pd.DataFrame:
    """Aggregates synthetic network telemetry per transaction ID."""
    df_feat = df_tx[["txid"]].copy()

    if df_net.empty:
        df_feat["net_ip_count"] = 0.0
        df_feat["net_country_count"] = 0.0
        df_feat["net_asn_count"] = 0.0
        df_feat["net_avg_packet_count"] = 0.0
        df_feat["net_avg_bytes_in"] = 0.0
        df_feat["net_avg_duration"] = 0.0
        df_feat["net_high_risk_asn_flag"] = 0.0
        df_feat["net_burst_scenario_flag"] = 0.0
        return df_feat

    # Aggregate network metrics by txid
    net_agg = df_net.groupby("txid").agg({
        "src_ip": "nunique",
        "geo_country": "nunique",
        "asn": ["nunique", lambda s: int(any(x in HIGH_RISK_ASNS for x in s))],
        "packet_count": "mean",
        "bytes_in": "mean",
        "connection_duration": "mean",
        "scenario": lambda s: int(any(x in ["burst_behavior", "rapid_movement", "high_frequency", "asn_concentration"] for x in s))
    })

    net_agg.columns = [
        "net_ip_count",
        "net_country_count",
        "net_asn_count",
        "net_high_risk_asn_flag",
        "net_avg_packet_count",
        "net_avg_bytes_in",
        "net_avg_duration",
        "net_burst_scenario_flag"
    ]
    net_agg = net_agg.reset_index()

    df_feat = pd.merge(df_feat, net_agg, on="txid", how="left").fillna({
        "net_ip_count": 1.0,
        "net_country_count": 1.0,
        "net_asn_count": 1.0,
        "net_high_risk_asn_flag": 0.0,
        "net_avg_packet_count": 50.0,
        "net_avg_bytes_in": 15000.0,
        "net_avg_duration": 1.0,
        "net_burst_scenario_flag": 0.0
    })

    return df_feat
