"""
CSV Loader for high-performance streaming and batch ingestion using Polars/Pandas.
"""

import os
import logging
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
import polars as pl
from .schema_validator import SchemaValidator
from .normalizer import DataNormalizer

logger = logging.getLogger(__name__)

class CSVLoader:
    """Ingests CSV data with schema validation and error quarantine."""

    def __init__(self, error_dir: str = "data/errors"):
        self.error_dir = error_dir
        os.makedirs(self.error_dir, exist_ok=True)

    def load_transactions(self, filepath: str, max_rows: Optional[int] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Loads and normalizes transactions from CSV."""
        logger.info("Loading transaction CSV: %s", filepath)
        df_raw = pd.read_csv(filepath, nrows=max_rows)
        
        valid_records = []
        invalid_records = []

        for idx, row in df_raw.iterrows():
            rec = row.to_dict()
            is_valid, errors = SchemaValidator.validate_transaction_record(rec)
            if is_valid:
                norm_rec = DataNormalizer.normalize_transaction_dict(rec)
                valid_records.append(norm_rec)
            else:
                rec["__validation_errors__"] = "; ".join(errors)
                invalid_records.append(rec)

        df_valid = pd.DataFrame(valid_records)
        df_invalid = pd.DataFrame(invalid_records)

        if not df_invalid.empty:
            err_file = os.path.join(self.error_dir, f"invalid_txs_{os.path.basename(filepath)}")
            df_invalid.to_csv(err_file, index=False)
            logger.warning("Quarantined %d invalid transaction rows to: %s", len(df_invalid), err_file)

        return df_valid, df_invalid

    def load_network_events(self, filepath: str, max_rows: Optional[int] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Loads and normalizes network events from CSV."""
        logger.info("Loading network events CSV: %s", filepath)
        df_raw = pd.read_csv(filepath, nrows=max_rows)

        valid_records = []
        invalid_records = []

        for idx, row in df_raw.iterrows():
            rec = row.to_dict()
            is_valid, errors = SchemaValidator.validate_network_record(rec)
            if is_valid:
                norm_rec = DataNormalizer.normalize_network_dict(rec)
                valid_records.append(norm_rec)
            else:
                rec["__validation_errors__"] = "; ".join(errors)
                invalid_records.append(rec)

        df_valid = pd.DataFrame(valid_records)
        df_invalid = pd.DataFrame(invalid_records)

        if not df_invalid.empty:
            err_file = os.path.join(self.error_dir, f"invalid_net_{os.path.basename(filepath)}")
            df_invalid.to_csv(err_file, index=False)
            logger.warning("Quarantined %d invalid network rows to: %s", len(df_invalid), err_file)

        return df_valid, df_invalid
