#!/usr/bin/env python3
"""
Generates a realistic Demo Bitcoin Transaction & Network Dataset (CSV).
Includes normal baseline transactions and injected suspicious forensic patterns
(e.g., peel chains, fee spikes, bulletproof hosting ASNs, velocity bursts).
"""

import os
import sys
import random
import datetime
import logging
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("create_demo_dataset")

DEMO_DIR = "data/demo"
os.makedirs(DEMO_DIR, exist_ok=True)

SUSPICIOUS_IPS = [
    ("185.220.101.5", "AS200651", "Tor Exit Node Network", "IS"),
    ("194.26.29.112", "AS206264", "Amarutu Bulletproof Transit", "SC"),
    ("185.107.56.88", "AS51852", "Private Layer Offshore", "CH"),
    ("193.138.218.70", "AS207960", "Mullvad VPN Privacy Node", "SE"),
    ("95.213.130.45", "AS49505", "Selectel High-Volume Relay", "RU")
]

NORMAL_IPS = [
    ("3.85.192.44", "AS16509", "Amazon AWS Cloud", "US"),
    ("88.198.54.2", "AS24940", "Hetzner Datacenter", "DE"),
    ("104.18.32.11", "AS13335", "Cloudflare Transit", "US"),
    ("141.94.120.30", "AS16276", "OVH SAS Hosting", "FR"),
    ("103.28.249.1", "AS133119", "Tencent Cloud APAC", "SG")
]

def generate_demo_csv(num_rows: int = 1200, seed: int = 42) -> str:
    random.seed(seed)
    np.random.seed(seed)

    base_time = datetime.datetime(2025, 3, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
    records = []

    for i in range(num_rows):
        tx_hex = f"tx_{random.randint(100000, 999999):x}{i:04x}"
        
        # Inject ~6% critical/high suspicious cases
        is_suspicious = random.random() < 0.08
        scenario_type = "normal"

        if is_suspicious:
            scenario_choice = random.choice(["peel_chain_fanout", "velocity_burst", "high_fee_anomaly", "bulletproof_asn"])
            scenario_type = scenario_choice
            
            if scenario_choice == "peel_chain_fanout":
                in_cnt = 1
                out_cnt = random.randint(10, 35)
                amt = round(random.uniform(10.0, 150.0), 4)
                fee = round(amt * 0.0005, 6)
                ip_info = random.choice(SUSPICIOUS_IPS)
            elif scenario_choice == "velocity_burst":
                in_cnt = random.randint(5, 12)
                out_cnt = 1
                amt = round(random.uniform(50.0, 500.0), 4)
                fee = round(random.uniform(0.005, 0.02), 6)
                ip_info = random.choice(SUSPICIOUS_IPS)
            elif scenario_choice == "high_fee_anomaly":
                in_cnt = 2
                out_cnt = 2
                amt = round(random.uniform(0.5, 5.0), 4)
                fee = round(random.uniform(0.05, 0.25), 6) # Massive fee
                ip_info = random.choice(NORMAL_IPS)
            else: # bulletproof_asn
                in_cnt = 2
                out_cnt = 4
                amt = round(random.uniform(1.0, 25.0), 4)
                fee = round(random.uniform(0.0001, 0.001), 6)
                ip_info = random.choice(SUSPICIOUS_IPS)
        else:
            in_cnt = random.choice([1, 1, 2, 3])
            out_cnt = random.choice([1, 2, 2, 3])
            amt = round(random.uniform(0.01, 8.0), 4)
            fee = round(random.uniform(0.00005, 0.0003), 6)
            ip_info = random.choice(NORMAL_IPS)

        ts_offset = random.randint(0, 86400 * 14)
        ts = base_time + datetime.timedelta(seconds=ts_offset)

        sender_addr = f"1BtcSend_{random.randint(1000, 9999)}"
        recv_addr = f"3BtcRecv_{random.randint(1000, 9999)}"

        records.append({
            "transaction_hash": tx_hex,
            "timestamp": ts.isoformat(),
            "sender_address": sender_addr,
            "receiver_address": recv_addr,
            "amount_btc": amt,
            "fee_btc": fee,
            "input_count": in_cnt,
            "output_count": out_cnt,
            "source_ip": ip_info[0],
            "destination_ip": "54.39.130.10",
            "port": 8333,
            "asn": ip_info[1],
            "asn_organization": ip_info[2],
            "country": ip_info[3]
        })

    df = pd.DataFrame(records)
    out_path = os.path.join(DEMO_DIR, "demo_transactions.csv")
    df.to_csv(out_path, index=False)
    logger.info("Successfully generated Demo dataset at: %s (%d records)", out_path, len(df))
    return out_path

if __name__ == "__main__":
    generate_demo_csv()
