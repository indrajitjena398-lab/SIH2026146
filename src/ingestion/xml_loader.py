"""
Safe XML Loader using defusedxml to guard against XXE and expansion vulnerabilities.
"""

import os
import logging
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
import defusedxml.ElementTree as ET
from .schema_validator import SchemaValidator
from .normalizer import DataNormalizer

logger = logging.getLogger(__name__)

class XMLLoader:
    """Safely ingests XML transaction and network records."""

    def __init__(self, error_dir: str = "data/errors"):
        self.error_dir = error_dir
        os.makedirs(self.error_dir, exist_ok=True)

    def load_records(self, filepath: str, record_type: str = "transaction") -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Parses XML files safely into dataframes."""
        logger.info("Loading XML file: %s (type=%s)", filepath, record_type)
        tree = ET.parse(filepath)
        root = tree.getroot()

        raw_records = []
        for elem in root:
            rec = {}
            for child in elem:
                rec[child.tag] = child.text
            raw_records.append(rec)

        valid_records = []
        invalid_records = []

        for rec in raw_records:
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
            err_file = os.path.join(self.error_dir, f"invalid_xml_{os.path.basename(filepath)}.csv")
            df_invalid.to_csv(err_file, index=False)
            logger.warning("Quarantined %d invalid XML rows to: %s", len(df_invalid), err_file)

        return df_valid, df_invalid
