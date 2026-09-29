"""
JSON and JSON Lines (JSONL) Loader with streaming validation and error handling.
"""

import os
import json
import logging
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
from .schema_validator import SchemaValidator
from .normalizer import DataNormalizer

logger = logging.getLogger(__name__)

class JSONLoader:
    """Ingests JSON and JSONL datasets."""

    def __init__(self, error_dir: str = "data/errors"):
        self.error_dir = error_dir
        os.makedirs(self.error_dir, exist_ok=True)

    def load_records(self, filepath: str, record_type: str = "transaction") -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Loads JSON / JSONL records."""
        logger.info("Loading JSON file: %s (type=%s)", filepath, record_type)
        raw_records = []
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content.startswith("["):
                raw_records = json.loads(content)
            else:
                # Treat as JSONL
                for line in content.splitlines():
                    line = line.strip()
                    if line:
                        try:
                            raw_records.append(json.loads(line))
                        except json.JSONDecodeError as e:
                            logger.warning("JSON decode error on line: %s", e)

        valid_records = []
        invalid_records = []

        for rec in raw_records:
            if not isinstance(rec, dict):
                continue
            if record_type == "transaction":
                is_valid, errors = SchemaValidator.validate_transaction_record(rec)
                if is_valid:
                    valid_records.append(DataNormalizer.normalize_transaction_dict(rec))
                else:
                    rec["__validation_errors__"] = "; ".join(errors)
                    invalid_records.append(rec)
            else:
                is_valid, errors = SchemaValidator.validate_network_record(rec)
                if is_valid:
                    valid_records.append(DataNormalizer.normalize_network_dict(rec))
                else:
                    rec["__validation_errors__"] = "; ".join(errors)
                    invalid_records.append(rec)

        df_valid = pd.DataFrame(valid_records)
        df_invalid = pd.DataFrame(invalid_records)

        if not df_invalid.empty:
            err_file = os.path.join(self.error_dir, f"invalid_json_{os.path.basename(filepath)}")
            df_invalid.to_json(err_file, orient="records", indent=2)
            logger.warning("Quarantined %d invalid JSON records to: %s", len(df_invalid), err_file)

        return df_valid, df_invalid
