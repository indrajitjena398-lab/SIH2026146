"""
Unified Multi-Modal Feature Pipeline.
Assembles transaction, behavioral, network, and graph features into a unified dataset.
"""

import os
import json
import logging
from typing import Dict, List, Tuple, Any
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import joblib

from .transaction_features import compute_transaction_features
from .behavioral_features import compute_behavioral_features
from .network_features import compute_network_features
from .graph_features import compute_graph_features

logger = logging.getLogger(__name__)

class FeaturePipeline:
    """End-to-end feature engineering pipeline."""

    def __init__(self, output_dir: str = "models/preprocessors"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.scaler = StandardScaler()
        self.feature_columns: List[str] = []

    def build_features(
        self,
        df_tx: pd.DataFrame,
        df_edges: pd.DataFrame,
        df_net: pd.DataFrame
    ) -> pd.DataFrame:
        """Extracts and concatenates all feature domains."""
        logger.info("Extracting feature domains for %d transactions...", len(df_tx))

        # Base raw features (feat_0 to feat_164 from Elliptic if present)
        raw_feat_cols = [c for c in df_tx.columns if c.startswith("feat_")]
        df_base = df_tx[["txid", "time_step", "label", "is_illicit", "is_labeled"] + raw_feat_cols].copy()

        # Domain feature tables
        df_tx_feat = compute_transaction_features(df_tx)
        df_beh_feat = compute_behavioral_features(df_tx, df_edges)
        df_net_feat = compute_network_features(df_tx, df_net)
        df_graph_feat = compute_graph_features(df_tx, df_edges)

        # Merge all on txid
        df_all = df_base
        for df_sub in [df_tx_feat, df_beh_feat, df_net_feat, df_graph_feat]:
            cols_to_add = [c for c in df_sub.columns if c != "txid" and c not in df_all.columns]
            if cols_to_add:
                df_all = pd.merge(df_all, df_sub[["txid"] + cols_to_add], on="txid", how="left")

        # Fill any remaining NaNs
        non_feat_cols = ["txid", "time_step", "label", "is_illicit", "is_labeled"]
        feat_cols = [c for c in df_all.columns if c not in non_feat_cols]
        df_all[feat_cols] = df_all[feat_cols].fillna(0.0)

        self.feature_columns = feat_cols
        logger.info("Assembled %d total engineered features across %d records", len(feat_cols), len(df_all))

        return df_all

    def fit_transform_scaler(self, df_train: pd.DataFrame) -> Tuple[np.ndarray, StandardScaler]:
        """Fits StandardScaler on training split features only to prevent data leakage."""
        X_train = df_train[self.feature_columns].values
        X_scaled = self.scaler.fit_transform(X_train)
        
        # Save scaler and feature column metadata
        scaler_path = os.path.join(self.output_dir, "feature_scaler.joblib")
        cols_path = os.path.join(self.output_dir, "feature_columns.json")
        joblib.dump(self.scaler, scaler_path)
        with open(cols_path, "w") as f:
            json.dump(self.feature_columns, f, indent=2)

        logger.info("Saved fitted scaler to %s and feature list to %s", scaler_path, cols_path)
        return X_scaled, self.scaler

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """Transforms a dataframe using the fitted scaler."""
        X = df[self.feature_columns].values
        return self.scaler.transform(X)
