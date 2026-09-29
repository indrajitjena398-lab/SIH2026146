"""
Schema Validator for multi-format Bitcoin Transaction and Network data.
Validates records before ingestion and flags malformed/corrupted entries for quarantine.
"""

import re
import ipaddress
from typing import Dict, Any, List, Tuple, Optional

TXID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]+$")
ADDRESS_PATTERN = re.compile(r"^[13bc1qp][a-zA-Z0-9]{25,62}$|^[a-zA-Z0-9_\-]+$")

REQUIRED_TX_FIELDS = ["txid"]
REQUIRED_NET_FIELDS = ["src_ip", "dst_ip"]

class SchemaValidator:
    """Validates records across transaction and network layers."""

    @staticmethod
    def validate_transaction_record(record: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        txid = record.get("txid") or record.get("txId") or record.get("transaction_id")
        if not txid:
            errors.append("Missing required transaction ID (txid)")
        elif not TXID_PATTERN.match(str(txid)):
            errors.append(f"Malformed transaction ID: '{txid}'")

        # Validate amount if present
        for amt_field in ["input_amount", "output_amount", "amount", "fee"]:
            if amt_field in record and record[amt_field] is not None:
                try:
                    val = float(record[amt_field])
                    if val < 0:
                        errors.append(f"Negative value for {amt_field}: {val}")
                except (ValueError, TypeError):
                    errors.append(f"Invalid numeric value for {amt_field}: {record[amt_field]}")

        # Validate time_step
        if "time_step" in record and record["time_step"] is not None:
            try:
                ts = int(record["time_step"])
                if ts < 1 or ts > 100:
                    errors.append(f"time_step out of valid range [1-100]: {ts}")
            except (ValueError, TypeError):
                errors.append(f"Invalid time_step value: {record['time_step']}")

        return len(errors) == 0, errors

    @staticmethod
    def validate_network_record(record: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        src_ip = str(record.get("src_ip", "")).strip()
        dst_ip = str(record.get("dst_ip", "")).strip()

        if not src_ip:
            errors.append("Missing required field: src_ip")
        else:
            try:
                ipaddress.ip_address(src_ip)
            except ValueError:
                errors.append(f"Invalid IP address format for src_ip: '{src_ip}'")

        if not dst_ip:
            errors.append("Missing required field: dst_ip")
        else:
            try:
                ipaddress.ip_address(dst_ip)
            except ValueError:
                errors.append(f"Invalid IP address format for dst_ip: '{dst_ip}'")

        # Validate ports
        for port_field in ["src_port", "dst_port"]:
            if port_field in record and record[port_field] is not None:
                try:
                    p = int(record[port_field])
                    if p < 0 or p > 65535:
                        errors.append(f"Port {port_field} out of range [0-65535]: {p}")
                except (ValueError, TypeError):
                    errors.append(f"Invalid port number for {port_field}: {record[port_field]}")

        return len(errors) == 0, errors
