"""
Automatic Schema Detector and Flexible Parser.
Detects CSV, JSON, and XML structures, maps fuzzy column variations,
and evaluates dataset coverage across Blockchain, Network, and GeoIP layers.
"""

import os
import re
import json
import logging
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
import defusedxml.ElementTree as ET
from src.enrichment.geoip import enrich_ip

logger = logging.getLogger(__name__)

# Canonical field aliases
FIELD_ALIASES = {
    "txid": ["txid", "tx_id", "transaction_id", "transaction_hash", "tx_hash", "tx", "hash", "txhash", "txid1"],
    "timestamp": ["timestamp", "time", "date", "block_time", "datetime", "created_at", "ts"],
    "time_step": ["time_step", "timestep", "step", "epoch", "block_epoch"],
    "input_addresses": ["input_addresses", "inputs", "input_address", "source_address", "from_address", "sender", "in_addr", "sender_address"],
    "output_addresses": ["output_addresses", "outputs", "output_address", "target_address", "to_address", "receiver", "out_addr", "receiver_address"],
    "input_amount": ["input_amount", "amount", "value", "input_amounts", "volume", "btc_amount", "total_input", "amount_btc", "amount_in"],
    "output_amount": ["output_amount", "output_amounts", "total_output", "out_value", "output_btc", "amount_out"],
    "fee": ["fee", "tx_fee", "fee_amount", "fees", "fee_btc"],
    "input_count": ["input_count", "in_degree", "num_inputs", "vin_count"],
    "output_count": ["output_count", "out_degree", "num_outputs", "vout_count"],
    "src_ip": ["src_ip", "source_ip", "ip_src", "client_ip", "src", "ip", "source"],
    "dst_ip": ["dst_ip", "destination_ip", "ip_dst", "peer_ip", "dst", "target_ip", "destination"],
    "src_port": ["src_port", "source_port", "port_src"],
    "dst_port": ["dst_port", "destination_port", "port_dst", "port"],
    "connection_duration": ["connection_duration", "duration", "conn_time", "latency"],
    "packet_count": ["packet_count", "packets", "num_packets", "pkts"],
    "bytes_in": ["bytes_in", "bytes_recv", "in_bytes", "byte_count"],
    "bytes_out": ["bytes_out", "bytes_sent", "out_bytes"],
    "geo_country": ["geo_country", "country", "country_code", "geo", "location"],
    "asn": ["asn", "autonomous_system", "as_number", "asn_org", "asn_organization"],
    "asn_org": ["asn_org", "asn_organization", "asn_organisation", "org", "organization"]
}

class AutoSchemaDetector:
    """Detects and maps arbitrary Bitcoin transaction and network datasets."""

    @staticmethod
    def parse_file(filepath: str, max_rows: Optional[int] = 100000) -> pd.DataFrame:
        """Parses CSV, JSON, or XML file into a DataFrame."""
        ext = os.path.splitext(filepath)[1].lower()

        if ext in [".csv", ".txt", ".tsv"]:
            sep = "\t" if ext == ".tsv" else ","
            try:
                df = pd.read_csv(filepath, sep=sep, nrows=max_rows)
            except Exception:
                # Try headerless detection if first line has pure numbers
                df = pd.read_csv(filepath, sep=sep, nrows=max_rows, header=None)
                df.columns = [f"col_{i}" for i in range(df.shape[1])]
            return df

        elif ext in [".json", ".jsonl"]:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content.startswith("["):
                    records = json.loads(content)
                    return pd.DataFrame(records[:max_rows])
                else:
                    lines = [json.loads(line) for line in content.splitlines() if line.strip()]
                    return pd.DataFrame(lines[:max_rows])

        elif ext in [".xml"]:
            tree = ET.parse(filepath)
            root = tree.getroot()
            records = []
            for elem in root:
                rec = {}
                for child in elem:
                    rec[child.tag] = child.text
                records.append(rec)
                if len(records) >= max_rows:
                    break
            return pd.DataFrame(records)

        else:
            raise ValueError(f"Unsupported file format '{ext}'. Supported: CSV, JSON, XML.")

    @staticmethod
    def detect_schema_and_map(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str], Dict[str, Any]]:
        """
        Fuzzy matches column names against canonical fields, standardizes the DataFrame,
        and computes layer coverage summary.
        """
        raw_columns = list(df.columns)
        mapping: Dict[str, str] = {}
        normalized_df = pd.DataFrame()

        # Fuzzy match
        for canonical, aliases in FIELD_ALIASES.items():
            matched_col = None
            for col in raw_columns:
                clean_col = re.sub(r"[^a-zA-Z0-9_]", "", str(col).strip().lower())
                if clean_col in aliases:
                    matched_col = col
                    break
            if matched_col is not None:
                mapping[matched_col] = canonical
                normalized_df[canonical] = df[matched_col]

        # Check for raw Elliptic features (feat_0 ... or numeric columns)
        raw_feat_cols = [c for c in raw_columns if str(c).startswith("feat_") or str(c).isdigit() or str(c).startswith("col_")]
        for c in raw_feat_cols:
            if c not in mapping:
                normalized_df[c] = df[c]

        # Generate fallback identifiers if txid missing
        if "txid" not in normalized_df.columns:
            # Check if first column can act as ID
            first_col = raw_columns[0]
            mapping[first_col] = "txid"
            normalized_df["txid"] = df[first_col].astype(str)

        # Standardize strings & numerics
        normalized_df["txid"] = normalized_df["txid"].astype(str)

        # Evaluate Coverage
        has_blockchain = any(f in normalized_df.columns for f in ["txid", "input_amount", "output_amount", "fee", "input_addresses", "output_addresses", "time_step"])
        has_network = any(f in normalized_df.columns for f in ["src_ip", "dst_ip", "src_port", "dst_port", "packet_count", "bytes_in"])
        has_geoip = any(f in normalized_df.columns for f in ["geo_country", "asn"])

        coverage = {
            "blockchain_layer": {
                "available": has_blockchain,
                "status": "Available ✓" if has_blockchain else "Not Available ✗",
                "matched_fields": [mapping[c] for c in mapping if mapping[c] in ["txid", "input_amount", "output_amount", "fee", "input_addresses", "output_addresses", "time_step"]]
            },
            "network_layer": {
                "available": has_network,
                "status": "Available ✓" if has_network else "Not Available in file (Synthetic correlation will be evaluated)",
                "matched_fields": [mapping[c] for c in mapping if mapping[c] in ["src_ip", "dst_ip", "src_port", "dst_port", "packet_count", "bytes_in"]]
            },
            "geoip_asn": {
                "available": has_geoip or has_network,
                "status": "Available via Local Offline Engine ✓" if (has_geoip or has_network) else "Unavailable",
                "matched_fields": [mapping[c] for c in mapping if mapping[c] in ["geo_country", "asn"]]
            }
        }

        logger.info("Detected schema mapping: %s | Total mapped fields: %d", mapping, len(mapping))
        return normalized_df, mapping, coverage
