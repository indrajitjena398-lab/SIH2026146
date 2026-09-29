"""
Dynamic File Format Converter for Bitcoin Transaction and Network Data.
Automatically detects file format (JSON, XLSX, XLS, XML, CSV) and converts to standardized CSV.
Supports nested structures and complex spreadsheets with automatic schema mapping.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path

import pandas as pd
import openpyxl
import defusedxml.ElementTree as ET
from .auto_detector import AutoSchemaDetector
from .normalizer import DataNormalizer
from .schema_validator import SchemaValidator
from .csv_loader import CSVLoader
from .json_loader import JSONLoader
from .xml_loader import XMLLoader

logger = logging.getLogger(__name__)


def _json_safe(value):
    """Convert pandas/NumPy NA values into JSON-serializable Python values."""
    if isinstance(value, dict):
        return {str(key): _json_safe(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in value]
    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass
    return value


# Standardized schema columns for converted CSV
STANDARDIZED_SCHEMA = [
    "timestamp",
    "src_ip",
    "dst_ip",
    "src_port",
    "dst_port",
    "txid",
    "input_addresses",
    "output_addresses",
    "input_amounts",
    "output_amounts",
    "geo_country",
    "asn"
]


class FileFormatConverter:
    """
    Universal file format converter for heterogeneous blockchain and network data.
    Converts JSON, XLSX, XLS, XML, and CSV to standardized CSV schema.
    """

    def __init__(self, converted_dir: str = "data/converted", error_dir: str = "data/errors"):
        self.converted_dir = converted_dir
        self.error_dir = error_dir
        os.makedirs(self.converted_dir, exist_ok=True)
        os.makedirs(self.error_dir, exist_ok=True)
        
        # Initialize loaders
        self.csv_loader = CSVLoader(error_dir=error_dir)
        self.json_loader = JSONLoader(error_dir=error_dir)
        self.xml_loader = XMLLoader(error_dir=error_dir)
        self.schema_detector = AutoSchemaDetector()

    def detect_file_format(self, filepath: str) -> str:
        """Automatically detect file format from extension and content."""
        ext = Path(filepath).suffix.lower()
        
        if ext == ".csv":
            return "csv"
        elif ext in [".json", ".jsonl"]:
            return "json"
        elif ext in [".xlsx", ".xls"]:
            return "excel"
        elif ext == ".xml":
            return "xml"
        else:
            # Try to infer from content
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read(100)
                    if content.strip().startswith('{') or content.strip().startswith('['):
                        return "json"
                    elif content.strip().startswith('<'):
                        return "xml"
            except:
                pass
            
            logger.warning(f"Unknown file format for {filepath}, attempting CSV")
            return "csv"

    def convert_to_standardized_csv(
        self,
        source_filepath: str,
        output_filename: Optional[str] = None,
        data_type: str = "transaction"
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Convert any supported file format to standardized CSV.
        
        Returns:
            Tuple of (output_csv_path, conversion_metadata)
        """
        file_format = self.detect_file_format(source_filepath)
        
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"converted_{timestamp}_{Path(source_filepath).stem}.csv"
        
        output_path = os.path.join(self.converted_dir, output_filename)
        
        logger.info(f"Converting {file_format} file to standardized CSV: {output_filename}")
        
        try:
            # Load data based on format
            if file_format == "csv":
                df = self._load_csv(source_filepath, data_type)
            elif file_format == "json":
                df = self._load_json(source_filepath, data_type)
            elif file_format == "excel":
                df = self._load_excel(source_filepath, data_type)
            elif file_format == "xml":
                df = self._load_xml(source_filepath, data_type)
            else:
                raise ValueError(f"Unsupported file format: {file_format}")
            
            if df is None or not isinstance(df, pd.DataFrame):
                raise ValueError(f"Failed to parse file into a tabular DataFrame: {source_filepath}")
            if df.empty:
                raise ValueError(f"Uploaded file is empty and cannot be converted: {source_filepath}")

            # Normalize column names to standardized schema
            df = self._normalize_columns(df)
            if df is None or not isinstance(df, pd.DataFrame):
                raise ValueError(f"Normalization failed for {source_filepath}; output DataFrame was null.")
            
            # Ensure all standardized columns exist (with NaN for missing)
            for col in STANDARDIZED_SCHEMA:
                if col not in df.columns:
                    df[col] = None
            
            # Reorder to standardized schema
            df = df[STANDARDIZED_SCHEMA]
            
            # Save to converted directory
            df.to_csv(output_path, index=False)
            
            metadata = {
                "status": "success",
                "source_format": file_format,
                "output_path": output_path,
                "output_filename": output_filename,
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "schema_columns": STANDARDIZED_SCHEMA,
                "timestamp": datetime.now().isoformat(),
                "file_size_bytes": os.path.getsize(output_path),
                "data_type": data_type
            }
            
            logger.info(f"Successfully converted {source_filepath} → {output_path} ({len(df)} rows)")
            return output_path, metadata
            
        except Exception as e:
            logger.error(f"Conversion failed for {source_filepath}: {str(e)}")
            raise

    def _load_csv(self, filepath: str, data_type: str) -> pd.DataFrame:
        """Load CSV file using AutoSchemaDetector."""
        df = self.schema_detector.parse_file(filepath)
        return df

    def _load_json(self, filepath: str, data_type: str) -> pd.DataFrame:
        """Load JSON/JSONL file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            records = []
            
            if content.startswith('['):
                # JSON array format
                records = json.loads(content)
            else:
                # JSONL format (one record per line)
                for line in content.splitlines():
                    line = line.strip()
                    if line:
                        try:
                            records.append(json.loads(line))
                        except json.JSONDecodeError as e:
                            logger.warning(f"Skipping invalid JSON line: {e}")
        
        df = pd.DataFrame(records)
        return df

    def _load_excel(self, filepath: str, data_type: str) -> pd.DataFrame:
        """Load XLSX/XLS file, flattening nested structures if needed."""
        try:
            # Try to read with pandas (handles XLSX)
            df = pd.read_excel(filepath, sheet_name=0)
        except Exception as e:
            logger.warning(f"Failed to read Excel with pandas: {e}, trying openpyxl")
            # Fallback to openpyxl for complex structures
            wb = openpyxl.load_workbook(filepath)
            ws = wb.active
            data = []
            headers = None
            
            for idx, row in enumerate(ws.iter_rows(values_only=True)):
                if idx == 0:
                    headers = row
                else:
                    if headers:
                        data.append(dict(zip(headers, row)))
            
            df = pd.DataFrame(data)
        
        return df

    def _load_xml(self, filepath: str, data_type: str) -> pd.DataFrame:
        """Load XML file with support for nested structures."""
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        records = []
        
        # Detect record elements (most common child type)
        for child in root:
            record = self._extract_xml_record(child)
            if record:
                records.append(record)
        
        df = pd.DataFrame(records) if records else pd.DataFrame()
        return df

    def _extract_xml_record(self, element, parent_key: str = "") -> Dict[str, Any]:
        """Recursively extract XML element data into flat dictionary."""
        record = {}
        
        # Add element attributes
        if element.attrib:
            for key, value in element.attrib.items():
                full_key = f"{parent_key}_{key}" if parent_key else key
                record[full_key] = value
        
        # Add element text if exists
        if element.text and element.text.strip():
            key = parent_key if parent_key else element.tag
            record[key] = element.text.strip()
        
        # Recursively process child elements
        for child in element:
            child_key = f"{parent_key}_{child.tag}" if parent_key else child.tag
            
            # Flatten nested structures
            if len(child) > 0:
                # Has children, recurse
                child_record = self._extract_xml_record(child, child_key)
                record.update(child_record)
            else:
                # Leaf node
                if child.text and child.text.strip():
                    record[child_key] = child.text.strip()
                elif child.attrib:
                    for key, value in child.attrib.items():
                        record[f"{child_key}_{key}"] = value
        
        return record

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Map detected column names to standardized schema using fuzzy matching.
        """
        if df is None or not isinstance(df, pd.DataFrame):
            raise ValueError("Column normalization requires a valid pandas DataFrame.")

        df = df.copy()
        column_mapping = {
            "transaction_hash": "txid",
            "txid": "txid",
            "tx_id": "txid",
            "sender_address": "input_addresses",
            "source_address": "input_addresses",
            "receiver_address": "output_addresses",
            "target_address": "output_addresses",
            "amount_btc": "input_amount",
            "amount": "input_amount",
            "value": "input_amount",
            "output_amount_btc": "output_amount",
            "fee_btc": "fee",
            "source_ip": "src_ip",
            "destination_ip": "dst_ip",
            "country": "geo_country",
            "asn_organization": "asn_org",
            "asn_org": "asn_org",
            "port": "dst_port",
        }

        for col in df.columns:
            col_lower = str(col).lower().strip()

            if col_lower in column_mapping:
                column_mapping[col] = column_mapping[col_lower]
                continue

            # Try exact matches first
            for std_col in STANDARDIZED_SCHEMA:
                if col_lower == std_col.lower():
                    column_mapping[col] = std_col
                    break

            # If no exact match, try partial matches
            if col not in column_mapping:
                for std_col in STANDARDIZED_SCHEMA:
                    if std_col.lower() in col_lower or col_lower in std_col.lower():
                        column_mapping[col] = std_col
                        break

            # If still no match, keep original column name
            if col not in column_mapping:
                column_mapping[col] = col

        # Rename columns
        df = df.rename(columns=column_mapping)

        if "amount_btc" in df.columns:
            if "input_amounts" in df.columns:
                df["input_amounts"] = df["input_amounts"].fillna(df["amount_btc"])
            if "output_amounts" in df.columns:
                df["output_amounts"] = df["output_amounts"].fillna(df["amount_btc"])
            elif "input_amounts" in df.columns:
                df["output_amounts"] = df["input_amounts"].fillna(df["amount_btc"])

        if "port" in df.columns:
            if "dst_port" in df.columns:
                df["dst_port"] = df["dst_port"].fillna(df["port"])
            if "src_port" in df.columns:
                df["src_port"] = df["src_port"].fillna(df["port"])

        # Remove duplicate columns (keep first occurrence)
        df = df.loc[:, ~df.columns.duplicated(keep='first')]
        return df

    def get_conversion_summary(self, output_path: str) -> Dict[str, Any]:
        """Generate summary statistics for converted dataset."""
        try:
            df = pd.read_csv(output_path)
            summary = {
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "schema_columns": list(df.columns),
                "memory_usage_mb": float(df.memory_usage(deep=True).sum() / (1024 ** 2)),
                "null_counts": {str(k): int(v) for k, v in df.isnull().sum().to_dict().items()},
                "sample_records": [
                    _json_safe(record)
                    for record in df.head(3).to_dict(orient='records')
                ]
            }
            return _json_safe(summary)
        except Exception as e:
            logger.error(f"Failed to generate summary for {output_path}: {e}")
            return {"error": str(e)}
