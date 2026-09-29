"""
Dataset Adapter for Bitcoin Transaction Datasets (Elliptic, Elliptic++, Generic).
Normalizes schemas, validates features, builds edges, classes, and canonical tables.
"""

import os
import json
import logging
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class DatasetAdapter:
    """Adapter interface to normalize multiple Bitcoin transaction datasets into a standard internal representation."""

    ELLIPTIC_CLASSES = {
        "1": "illicit",
        "2": "licit",
        "unknown": "unknown",
        1: "illicit",
        2: "licit",
        0: "unknown"
    }

    def __init__(self, dataset_name: str = "elliptic"):
        self.dataset_name = dataset_name.lower()
        self.feature_columns: List[str] = []
        self.num_timesteps: int = 49

    def load_dataset(
        self,
        features_path: str,
        edgelist_path: str,
        classes_path: str,
        max_rows: Optional[int] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Loads raw feature, edge, and class CSV files and normalizes them.
        """
        logger.info("Loading dataset %s from: %s", self.dataset_name, features_path)

        if not os.path.exists(features_path):
            raise FileNotFoundError(f"Features file not found at: {features_path}")
        if not os.path.exists(edgelist_path):
            raise FileNotFoundError(f"Edgelist file not found at: {edgelist_path}")
        if not os.path.exists(classes_path):
            raise FileNotFoundError(f"Classes file not found at: {classes_path}")

        # Load classes
        df_classes = pd.read_csv(classes_path, nrows=max_rows)
        df_classes.columns = [c.strip() for c in df_classes.columns]
        if "txId" in df_classes.columns:
            df_classes.rename(columns={"txId": "txid"}, inplace=True)
        if "class" in df_classes.columns:
            df_classes.rename(columns={"class": "raw_class"}, inplace=True)

        # Normalize class labels
        df_classes["label"] = df_classes["raw_class"].astype(str).map(
            lambda x: self.ELLIPTIC_CLASSES.get(x, "unknown")
        )
        df_classes["is_illicit"] = (df_classes["label"] == "illicit").astype(int)
        df_classes["is_labeled"] = (df_classes["label"] != "unknown").astype(int)

        # Load edges
        df_edges = pd.read_csv(edgelist_path, nrows=max_rows)
        df_edges.columns = [c.strip() for c in df_edges.columns]
        if "txId1" in df_edges.columns and "txId2" in df_edges.columns:
            df_edges.rename(columns={"txId1": "source_txid", "txId2": "target_txid"}, inplace=True)

        # Load features
        # Note: Elliptic raw features CSV usually has no header: col 0 is txId, col 1 is time_step, col 2-166 are features
        sample = pd.read_csv(features_path, nrows=5, header=None)
        has_header = False
        first_val = str(sample.iloc[0, 0])
        if first_val in ["txId", "txid", "transaction_id"]:
            has_header = True

        if has_header:
            df_features = pd.read_csv(features_path, nrows=max_rows)
            df_features.rename(columns={df_features.columns[0]: "txid", df_features.columns[1]: "time_step"}, inplace=True)
        else:
            df_features = pd.read_csv(features_path, nrows=max_rows, header=None)
            num_cols = df_features.shape[1]
            cols = ["txid", "time_step"] + [f"feat_{i}" for i in range(num_cols - 2)]
            df_features.columns = cols

        df_features["txid"] = df_features["txid"].astype(str)
        df_classes["txid"] = df_classes["txid"].astype(str)
        df_edges["source_txid"] = df_edges["source_txid"].astype(str)
        df_edges["target_txid"] = df_edges["target_txid"].astype(str)

        self.feature_columns = [c for c in df_features.columns if c not in ["txid", "time_step"]]

        logger.info(
            "Dataset loaded: %d transactions, %d edges, %d feature columns",
            len(df_features), len(df_edges), len(self.feature_columns)
        )

        return {
            "features": df_features,
            "classes": df_classes,
            "edges": df_edges
        }

    def validate_schema(self, df_dict: Dict[str, pd.DataFrame]) -> Tuple[bool, List[str]]:
        """Validates that loaded data conforms to the required schema."""
        errors = []
        features = df_dict.get("features")
        classes = df_dict.get("classes")
        edges = df_dict.get("edges")

        if features is None or features.empty:
            errors.append("Features table is missing or empty")
        else:
            if "txid" not in features.columns:
                errors.append("Features missing 'txid' column")
            if "time_step" not in features.columns:
                errors.append("Features missing 'time_step' column")

        if classes is None or classes.empty:
            errors.append("Classes table is missing or empty")
        else:
            if "txid" not in classes.columns:
                errors.append("Classes missing 'txid' column")
            if "label" not in classes.columns:
                errors.append("Classes missing 'label' column")

        if edges is None or edges.empty:
            errors.append("Edges table is missing or empty")
        else:
            if "source_txid" not in edges.columns or "target_txid" not in edges.columns:
                errors.append("Edges missing 'source_txid' or 'target_txid'")

        is_valid = len(errors) == 0
        return is_valid, errors
