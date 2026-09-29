"""
Transaction Feature Extraction.
Derives on-chain structural and financial metrics from transaction records.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List

def compute_transaction_features(df_tx: pd.DataFrame) -> pd.DataFrame:
    """Computes transaction-level financial and structural features."""
    df_feat = df_tx[["txid"]].copy()

    # If raw features exist (feat_0 to feat_92 are local features in Elliptic)
    feat_cols = [c for c in df_tx.columns if c.startswith("feat_")]
    if feat_cols:
        # Use first 15 as key local transaction proxies
        df_feat["tx_in_degree"] = df_tx["feat_0"].astype(float)
        df_feat["tx_out_degree"] = df_tx["feat_1"].astype(float)
        df_feat["tx_fee"] = df_tx["feat_2"].astype(float) if len(feat_cols) > 2 else 0.0
        df_feat["tx_volume"] = df_tx["feat_3"].astype(float) if len(feat_cols) > 3 else 1.0
        df_feat["tx_fan_out_ratio"] = (df_feat["tx_out_degree"] + 1e-5) / (df_feat["tx_in_degree"] + 1e-5)
    else:
        df_feat["tx_in_degree"] = df_tx.get("input_count", 1).astype(float)
        df_feat["tx_out_degree"] = df_tx.get("output_count", 2).astype(float)
        df_feat["tx_fee"] = df_tx.get("fee", 0.0001).astype(float)
        df_feat["tx_volume"] = df_tx.get("output_amount", 1.0).astype(float)
        df_feat["tx_fan_out_ratio"] = (df_feat["tx_out_degree"] + 1e-5) / (df_feat["tx_in_degree"] + 1e-5)

    return df_feat
