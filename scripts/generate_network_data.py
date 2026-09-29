#!/usr/bin/env python3
"""
Synthetic Network-Layer Metadata Generator for Bitcoin Transaction Monitoring.
Explicitly labeled: "Synthetic network-layer metadata generated for system integration and demonstration."
Simulates realistic P2P network telemetry correlated with transaction IDs across 10 cyber scenarios.
"""

import os
import sys
import argparse
import random
import datetime
import json
import logging
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.enrichment.geoip import enrich_ip

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("network_generator")

DISCLAIMER_TEXT = "Synthetic network-layer metadata generated for system integration and demonstration."

SCENARIOS = [
    "normal_propagation",
    "high_frequency",
    "repeated_connections",
    "multi_ip_association",
    "geographic_anomaly",
    "asn_concentration",
    "rapid_movement",
    "burst_behavior",
    "suspicious_timing",
    "layering_pattern"
]

# Curated seed pools for realistic generation
NORMAL_IP_POOL = [
    "3.85.192.44", "13.107.246.50", "104.18.32.11", "142.250.180.206",
    "88.198.54.2", "78.46.102.19", "51.15.210.88", "141.94.120.30",
    "94.142.241.10", "114.114.114.114", "223.5.5.5", "103.28.249.1",
    "133.130.12.50", "192.241.130.22", "159.203.40.12"
]

SUSPICIOUS_IP_POOL = [
    "185.220.101.5", "185.220.100.240", "194.26.29.112", "185.107.56.88",
    "193.138.218.70", "95.213.130.45", "185.130.44.200", "185.246.188.15"
]

BITCOIN_PEER_IPS = [
    "54.39.130.10", "149.202.80.12", "167.99.140.22", "138.68.10.99",
    "46.101.88.12", "178.62.200.45", "139.59.150.33", "165.227.180.14"
]

def generate_minimum_synthetic_dataset(
    num_rows: int = 200,
    seed: int = 42,
    suspicious_ratio: float = 0.18,
    base_timestamp: Optional[datetime.datetime] = None
) -> pd.DataFrame:
    """Generate a minimum schema-compliant Bitcoin transaction dataset with benign + illicit patterns."""
    random.seed(seed)
    np.random.seed(seed)
    if base_timestamp is None:
        base_timestamp = datetime.datetime(2026, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)

    records: List[Dict[str, Any]] = []
    normal_ips = [
        "3.85.192.44", "13.107.246.50", "104.18.32.11", "142.250.180.206",
        "88.198.54.2", "78.46.102.19", "51.15.210.88", "141.94.120.30",
        "94.142.241.10", "104.16.0.9"
    ]
    suspicious_ips = [
        "185.220.101.5", "185.220.100.240", "194.26.29.112", "185.107.56.88",
        "193.138.218.70", "95.213.130.45", "185.130.44.200", "185.246.188.15"
    ]
    script_types = ["P2PKH", "P2SH-P2WPKH", "P2WPKH", "P2TR", "MULTISIG"]
    asn_lookup = {
        "3.85.192.44": "AS16509", "13.107.246.50": "AS8075", "104.18.32.11": "AS13335",
        "142.250.180.206": "AS15169", "88.198.54.2": "AS24940", "78.46.102.19": "AS24940",
        "51.15.210.88": "AS12876", "141.94.120.30": "AS16276", "94.142.241.10": "AS49981",
        "104.16.0.9": "AS13335", "185.220.101.5": "AS200651", "185.220.100.240": "AS200651",
        "194.26.29.112": "AS206264", "185.107.56.88": "AS51852", "193.138.218.70": "AS207960",
        "95.213.130.45": "AS49505", "185.130.44.200": "AS58271", "185.246.188.15": "AS48635"
    }

    suspicious_target = max(1, int(num_rows * suspicious_ratio))
    suspicious_ids = set(random.sample(range(num_rows), suspicious_target))

    for i in range(num_rows):
        ts = base_timestamp + datetime.timedelta(seconds=i * 43)
        is_illicit = 1 if i in suspicious_ids else 0
        src_ip = random.choice(suspicious_ips if is_illicit else normal_ips)
        dst_ip = random.choice(normal_ips)
        src_port = random.randint(1024, 65535)
        dst_port = random.choice([8333, 18333, 443])
        fee = round(random.uniform(0.0001, 0.004) if is_illicit else random.uniform(0.00001, 0.0015), 8)
        input_count = random.randint(1, 4)
        output_count = random.randint(1, 6)
        input_amounts = [round(random.uniform(0.05, 2.5), 8) for _ in range(input_count)]
        output_amounts = [round(sum(input_amounts) * random.uniform(0.45, 0.95) / max(1, output_count), 8) for _ in range(output_count)]
        if is_illicit:
            input_amounts = [round(v * random.uniform(1.5, 8.0), 8) for v in input_amounts]
            output_amounts = [round(random.uniform(0.3, 1.5), 8) for _ in range(output_count)]
            script_type = random.choice(["P2SH-P2WPKH", "MULTISIG", "P2TR"])
            if random.random() < 0.5:
                output_amounts = [round(max(0.05, x * random.uniform(0.1, 0.7)), 8) for x in output_amounts]
        else:
            script_type = random.choice(["P2PKH", "P2WPKH", "P2SH-P2WPKH", "P2TR"])

        total_in = sum(input_amounts)
        total_out = sum(output_amounts)
        if total_out > 0:
            actual_fee = max(0.00001, abs(total_in - total_out))
        else:
            actual_fee = fee

        input_addresses = [f"bc1q{random.randint(100000000, 999999999):08x}" for _ in range(input_count)]
        output_addresses = [f"bc1q{random.randint(100000000, 999999999):08x}" for _ in range(output_count)]
        geo_country = "DE" if src_ip in suspicious_ips else "US"
        asn = asn_lookup.get(src_ip, "AS15169")

        records.append({
            "timestamp": ts.isoformat(),
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "src_port": src_port,
            "dst_port": dst_port,
            "txid": f"tx_{i:06d}",
            "input_addresses": json.dumps(input_addresses),
            "output_addresses": json.dumps(output_addresses),
            "input_amounts": json.dumps([round(x, 8) for x in input_amounts]),
            "output_amounts": json.dumps([round(x, 8) for x in output_amounts]),
            "fee": round(actual_fee, 8),
            "script_type": script_type,
            "geo_country": geo_country,
            "asn": asn,
            "is_illicit": is_illicit,
            "is_labeled": 1,
            "label": "illicit" if is_illicit else "licit",
            "time_step": i // 10 + 1,
        })

    df = pd.DataFrame(records)
    logger.info("Generated %d synthetic Bitcoin records with %d illicit labels.", len(df), int(df["is_illicit"].sum()))
    return df


def generate_synthetic_network_records(
    txids: List[str],
    num_rows: int = 10000,
    suspicious_ratio: float = 0.15,
    seed: int = 42,
    base_timestamp: Optional[datetime.datetime] = None
) -> pd.DataFrame:
    """
    Generates a deterministic synthetic network telemetry dataframe.
    """
    random.seed(seed)
    np.random.seed(seed)

    if base_timestamp is None:
        base_timestamp = datetime.datetime(2025, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)

    if not txids:
        txids = [f"tx_{i:07d}" for i in range(max(100, num_rows // 2))]

    records: List[Dict[str, Any]] = []

    # Map suspicious txids if present
    num_suspicious_txs = int(len(txids) * suspicious_ratio)
    suspicious_tx_set = set(random.sample(txids, max(1, num_suspicious_txs)))

    for i in range(num_rows):
        txid = random.choice(txids)
        is_tx_suspicious = txid in suspicious_tx_set

        if is_tx_suspicious:
            scenario = random.choices(
                SCENARIOS[1:],  # suspicious scenarios
                weights=[0.15, 0.15, 0.15, 0.10, 0.15, 0.10, 0.10, 0.05, 0.05],
                k=1
            )[0]
        else:
            scenario = "normal_propagation"

        # Timestamp generation with scenario variations
        time_offset_seconds = random.randint(0, 86400 * 30)
        if scenario == "high_frequency" or scenario == "suspicious_timing":
            # Clustered in sub-seconds
            micro_offset = random.randint(10, 500) / 1000.0
            event_time = base_timestamp + datetime.timedelta(seconds=time_offset_seconds, milliseconds=micro_offset*1000)
        else:
            event_time = base_timestamp + datetime.timedelta(seconds=time_offset_seconds)

        # IP & Port selection
        if scenario in ["asn_concentration", "layering_pattern"]:
            src_ip = random.choice(SUSPICIOUS_IP_POOL)
        elif scenario == "repeated_connections":
            src_ip = SUSPICIOUS_IP_POOL[0]  # concentrated single IP
        else:
            src_ip = random.choice(NORMAL_IP_POOL)

        dst_ip = random.choice(BITCOIN_PEER_IPS)
        dst_port = 8333 if random.random() < 0.85 else random.choice([8332, 18333, 9333, 443])
        src_port = random.randint(1024, 65535)

        # Telemetry metrics based on scenario
        if scenario == "burst_behavior":
            packet_count = random.randint(500, 5000)
            bytes_in = packet_count * random.randint(800, 1500)
            bytes_out = packet_count * random.randint(400, 1200)
            duration = round(random.uniform(0.05, 0.5), 4)
        elif scenario == "rapid_movement":
            packet_count = random.randint(20, 80)
            bytes_in = packet_count * random.randint(100, 300)
            bytes_out = packet_count * random.randint(100, 300)
            duration = round(random.uniform(0.01, 0.1), 4)
        elif scenario == "high_frequency":
            packet_count = random.randint(5, 30)
            bytes_in = packet_count * random.randint(64, 200)
            bytes_out = packet_count * random.randint(64, 200)
            duration = round(random.uniform(0.005, 0.08), 4)
        else:
            packet_count = random.randint(10, 150)
            bytes_in = packet_count * random.randint(120, 600)
            bytes_out = packet_count * random.randint(120, 600)
            duration = round(random.uniform(0.2, 5.0), 3)

        # Enrich IP
        geo_info = enrich_ip(src_ip)

        records.append({
            "event_id": f"net_ev_{i:08d}",
            "txid": str(txid),
            "timestamp": event_time.isoformat(),
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "src_port": src_port,
            "dst_port": dst_port,
            "connection_duration": duration,
            "packet_count": packet_count,
            "bytes_in": bytes_in,
            "bytes_out": bytes_out,
            "geo_country": geo_info["geo_country"],
            "geo_continent": geo_info["geo_continent"],
            "geo_region": geo_info["geo_region"],
            "asn": geo_info["asn"],
            "asn_org": geo_info["asn_org"],
            "scenario": scenario,
            "is_synthetic": True,
            "disclaimer": DISCLAIMER_TEXT
        })

    df = pd.DataFrame(records)
    logger.info("Generated %d synthetic network records across %d unique txids", len(df), df["txid"].nunique())
    return df

def main():
    parser = argparse.ArgumentParser(description="Generate deterministic synthetic Bitcoin network traffic metadata.")
    parser.add_argument("--rows", type=int, default=10000, help="Number of network events to generate.")
    parser.add_argument("--seed", type=int, default=42, help="PRNG random seed for deterministic generation.")
    parser.add_argument("--suspicious-ratio", type=float, default=0.15, help="Ratio of suspicious network events.")
    parser.add_argument("--output", type=str, default="data/synthetic/network_events.csv", help="Target output CSV filepath.")
    parser.add_argument("--txids-file", type=str, default=None, help="Optional CSV file containing real transaction IDs to map to.")
    args = parser.parse_args()

    txids = []
    if args.txids_file and os.path.exists(args.txids_file):
        try:
            df_tx = pd.read_csv(args.txids_file)
            col = [c for c in df_tx.columns if c.lower() in ["txid", "tx_id", "transaction_id"]][0]
            txids = df_tx[col].astype(str).tolist()
            logger.info("Loaded %d transaction IDs from %s", len(txids), args.txids_file)
        except Exception as e:
            logger.warning("Could not read txids file: %s. Using auto-generated IDs.", e)

    df_net = generate_synthetic_network_records(
        txids=txids,
        num_rows=args.rows,
        suspicious_ratio=args.suspicious_ratio,
        seed=args.seed
    )

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    df_net.to_csv(args.output, index=False)
    logger.info("Successfully wrote synthetic network data to: %s", args.output)

if __name__ == "__main__":
    main()
