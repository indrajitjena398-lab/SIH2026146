"""
Data Normalizer for Bitcoin Transactions and Network Events.
Normalizes timestamps, IDs, formats, handles missing values, and deduplicates records.
"""

import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

class DataNormalizer:
    """Standardizes heterogeneous input records into the Canonical Data Model."""

    @staticmethod
    def normalize_timestamp(ts_val: Any) -> str:
        """Parses various timestamp representations into ISO-8601 UTC string."""
        if ts_val is None or (isinstance(ts_val, float) and np.isnan(ts_val)):
            return datetime.datetime.now(datetime.timezone.utc).isoformat()

        if isinstance(ts_val, datetime.datetime):
            if ts_val.tzinfo is None:
                ts_val = ts_val.replace(tzinfo=datetime.timezone.utc)
            return ts_val.isoformat()

        if isinstance(ts_val, (int, float)):
            # Epoch timestamp in seconds or ms
            if ts_val > 1e11:  # milliseconds
                ts_val = ts_val / 1000.0
            try:
                dt = datetime.datetime.fromtimestamp(ts_val, tz=datetime.timezone.utc)
                return dt.isoformat()
            except Exception:
                return datetime.datetime.now(datetime.timezone.utc).isoformat()

        if isinstance(ts_val, str):
            ts_str = ts_val.strip()
            try:
                dt = datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                return dt.isoformat()
            except Exception:
                pass
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y %H:%M:%S", "%m/%d/%Y %H:%M:%S"]:
                try:
                    dt = datetime.datetime.strptime(ts_str, fmt).replace(tzinfo=datetime.timezone.utc)
                    return dt.isoformat()
                except Exception:
                    pass

        return datetime.datetime.now(datetime.timezone.utc).isoformat()

    @staticmethod
    def normalize_transaction_dict(d: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizes a raw transaction dictionary."""
        txid = str(d.get("txid") or d.get("txId") or d.get("transaction_id") or "").strip()
        time_step = int(d.get("time_step", 1)) if d.get("time_step") is not None else 1
        timestamp = DataNormalizer.normalize_timestamp(d.get("timestamp"))
        label = str(d.get("label", "unknown")).lower()
        if label in ["1", "illicit"]:
            label = "illicit"
        elif label in ["2", "licit"]:
            label = "licit"
        else:
            label = "unknown"

        input_amount = float(d.get("input_amount", d.get("amount", 0.0)))
        output_amount = float(d.get("output_amount", d.get("amount", input_amount)))
        fee = float(d.get("fee", 0.0001))
        input_count = int(d.get("input_count", 1))
        output_count = int(d.get("output_count", 2))

        return {
            "txid": txid,
            "timestamp": timestamp,
            "time_step": time_step,
            "input_amount": round(input_amount, 8),
            "output_amount": round(output_amount, 8),
            "fee": round(fee, 8),
            "transaction_size": int(d.get("transaction_size", 225)),
            "input_count": input_count,
            "output_count": output_count,
            "label": label,
            "is_synthetic": bool(d.get("is_synthetic", False))
        }

    @staticmethod
    def normalize_network_dict(d: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizes a raw network event dictionary."""
        return {
            "event_id": str(d.get("event_id", "")),
            "txid": str(d.get("txid", "")).strip(),
            "timestamp": DataNormalizer.normalize_timestamp(d.get("timestamp")),
            "src_ip": str(d.get("src_ip", "")).strip(),
            "dst_ip": str(d.get("dst_ip", "")).strip(),
            "src_port": int(d.get("src_port", 0)),
            "dst_port": int(d.get("dst_port", 8333)),
            "connection_duration": float(d.get("connection_duration", 0.0)),
            "packet_count": int(d.get("packet_count", 0)),
            "bytes_in": int(d.get("bytes_in", 0)),
            "bytes_out": int(d.get("bytes_out", 0)),
            "geo_country": str(d.get("geo_country", "UNKNOWN")),
            "geo_continent": str(d.get("geo_continent", "UNKNOWN")),
            "geo_region": str(d.get("geo_region", "UNKNOWN")),
            "asn": str(d.get("asn", "UNKNOWN")),
            "asn_org": str(d.get("asn_org", "UNKNOWN")),
            "scenario": str(d.get("scenario", "normal_propagation")),
            "is_synthetic": True,
            "disclaimer": str(d.get("disclaimer", "Synthetic network-layer metadata generated for system integration and demonstration."))
        }
