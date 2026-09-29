"""
Behavioral Feature Extraction.
Derives temporal velocity, burstiness, address reuse, and counterparty dispersion metrics.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any

def compute_behavioral_features(df_tx: pd.DataFrame, df_edges: pd.DataFrame) -> pd.DataFrame:
    """Computes behavioral dynamic features per transaction."""
    df_feat = df_tx[["txid"]].copy()

    # Degree / velocity from edges
    if not df_edges.empty:
        out_counts = df_edges["source_txid"].value_counts().to_dict()
        in_counts = df_edges["target_txid"].value_counts().to_dict()
        
        df_feat["behavior_fan_in"] = df_tx["txid"].map(lambda x: in_counts.get(x, 0)).astype(float)
        df_feat["behavior_fan_out"] = df_tx["txid"].map(lambda x: out_counts.get(x, 0)).astype(float)
        df_feat["behavior_counterparty_diversity"] = df_feat["behavior_fan_in"] + df_feat["behavior_fan_out"]
    else:
        df_feat["behavior_fan_in"] = 0.0
        df_feat["behavior_fan_out"] = 0.0
        df_feat["behavior_counterparty_diversity"] = 0.0

    # Velocity index based on timestep and local features
    if "time_step" in df_tx.columns:
        # Transactions in burst timesteps
        ts_density = df_tx["time_step"].value_counts().to_dict()
        df_feat["behavior_timestep_density"] = df_tx["time_step"].map(lambda x: ts_density.get(x, 1)).astype(float)
    else:
        df_feat["behavior_timestep_density"] = 1.0

    df_feat["behavior_velocity_index"] = (df_feat["behavior_fan_out"] * 1.5 + df_feat["behavior_fan_in"] * 0.8) / (df_feat["behavior_timestep_density"] + 1.0)
    df_feat["behavior_burstiness"] = np.log1p(df_feat["behavior_fan_out"] ** 2 + df_feat["behavior_fan_in"] ** 2)

    return df_feat
