"""
Temporal Train-Validation-Test Splitter.
Guarantees zero data leakage by splitting strictly across chronological block timesteps.
Also supports stratified random splitting as an experimental comparison baseline.
"""

import logging
from typing import Tuple, Dict, Any
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)

class TemporalSplitter:
    """Splits time-series transaction records without future lookahead leakage."""

    def __init__(
        self,
        train_timesteps: Tuple[int, int] = (1, 34),
        val_timesteps: Tuple[int, int] = (35, 41),
        test_timesteps: Tuple[int, int] = (42, 49)
    ):
        self.train_range = train_timesteps
        self.val_range = val_timesteps
        self.test_range = test_timesteps

    def split_temporal(
        self,
        df_features: pd.DataFrame
    ) -> Dict[str, pd.DataFrame]:
        """Performs strict temporal partitioning."""
        # Filter labeled transactions for supervised training/eval
        df_labeled = df_features[df_features["is_labeled"] == 1].copy()
        
        train_mask = (df_labeled["time_step"] >= self.train_range[0]) & (df_labeled["time_step"] <= self.train_range[1])
        val_mask = (df_labeled["time_step"] >= self.val_range[0]) & (df_labeled["time_step"] <= self.val_range[1])
        test_mask = (df_labeled["time_step"] >= self.test_range[0]) & (df_labeled["time_step"] <= self.test_range[1])

        df_train = df_labeled[train_mask]
        df_val = df_labeled[val_mask]
        df_test = df_labeled[test_mask]

        logger.info(
            "Temporal Split: Train [TS %d-%d]: %d rows (%d illicit) | Val [TS %d-%d]: %d rows (%d illicit) | Test [TS %d-%d]: %d rows (%d illicit)",
            self.train_range[0], self.train_range[1], len(df_train), int(df_train["is_illicit"].sum()),
            self.val_range[0], self.val_range[1], len(df_val), int(df_val["is_illicit"].sum()),
            self.test_range[0], self.test_range[1], len(df_test), int(df_test["is_illicit"].sum())
        )

        return {
            "train": df_train,
            "val": df_val,
            "test": df_test,
            "all_labeled": df_labeled,
            "unlabeled": df_features[df_features["is_labeled"] == 0]
        }

    def split_random_baseline(
        self,
        df_features: pd.DataFrame,
        seed: int = 42
    ) -> Dict[str, pd.DataFrame]:
        """Performs standard stratified random split as a baseline to expose leakage effects."""
        df_labeled = df_features[df_features["is_labeled"] == 1].copy()
        train_val, test = train_test_split(
            df_labeled, test_size=0.15, random_state=seed, stratify=df_labeled["is_illicit"]
        )
        train, val = train_test_split(
            train_val, test_size=0.18, random_state=seed, stratify=train_val["is_illicit"]
        )
        return {
            "train": train,
            "val": val,
            "test": test
        }
