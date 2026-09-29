"""
Dataset Threat Scanner & Multi-Layer Attack Classifier.
Parses CSV, JSON, Excel (.xlsx/.xls), and XML files, extracts multi-layer signals,
classifies threat types (Ransomware, Mixer, Darknet, P2P Flood, etc.), detects layer attribution,
and generates forensic explanations for every record.
"""

import os
import io
import json
import time
import logging
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
import numpy as np
import defusedxml.ElementTree as ET

from src.enrichment.geoip import enrich_ip
from src.risk.risk_fusion import RiskFusionEngine
from src.explainability.evidence_generator import EvidenceGenerator
from backend.services.ml_service import MLService

logger = logging.getLogger(__name__)

HIGH_RISK_ASNS = {"AS200651", "AS60531", "AS206264", "AS51852", "AS58271"}

class DatasetScannerService:
    """Scans and analyzes arbitrary dataset files."""

    risk_engine = RiskFusionEngine()

    @classmethod
    def parse_file_to_dataframe(cls, file_bytes: bytes, filename: str) -> pd.DataFrame:
        """Parses CSV, JSON, Excel, or XML bytes into a normalized pandas DataFrame."""
        ext = os.path.splitext(filename)[1].lower()
        
        try:
            if ext in [".xlsx", ".xls"]:
                df = pd.read_excel(io.BytesIO(file_bytes))
            elif ext == ".json":
                content = file_bytes.decode("utf-8", errors="ignore").strip()
                if content.startswith("["):
                    df = pd.read_json(io.StringIO(content))
                else:
                    # JSON Lines (JSONL)
                    df = pd.read_json(io.StringIO(content), lines=True)
            elif ext == ".xml":
                tree = ET.parse(io.BytesIO(file_bytes))
                root = tree.getroot()
                records = []
                for elem in root:
                    rec = {}
                    for child in elem:
                        rec[child.tag] = child.text
                    records.append(rec)
                df = pd.DataFrame(records)
            else:
                # Default CSV / TSV
                try:
                    df = pd.read_csv(io.BytesIO(file_bytes))
                except Exception:
                    df = pd.read_csv(io.BytesIO(file_bytes), sep=None, engine="python")

            # Clean column names
            df.columns = [str(c).strip().lower() for c in df.columns]
            return df
        except Exception as e:
            logger.error("Error parsing file %s: %s", filename, e)
            raise ValueError(f"Failed to parse {filename}: {str(e)}")

    @classmethod
    def analyze_dataset(cls, df: pd.DataFrame, max_rows: int = 500) -> Dict[str, Any]:
        """
        Runs comprehensive multi-modal threat analysis across all rows in the dataframe.
        """
        start_time = time.time()
        records_to_process = df.head(max_rows)

        results = []
        attack_count = 0
        normal_count = 0

        layer_counts = {
            "Blockchain Layer": 0,
            "Network Layer": 0,
            "Graph Layer": 0,
            "Multi-Layer Fusion": 0,
            "None (Normal)": 0
        }

        attack_type_counts: Dict[str, int] = {}

        for idx, row in records_to_process.iterrows():
            row_dict = row.to_dict()

            # 1. Extract / Normalize fields with flexible column naming
            txid = str(
                row_dict.get("txid") or row_dict.get("tx_id") or row_dict.get("transaction_id") or
                row_dict.get("id") or f"TX_{idx+1:05d}"
            ).strip()

            amount = float(row_dict.get("amount") or row_dict.get("output_amount") or row_dict.get("input_amount") or 1.0)
            fee = float(row_dict.get("fee") or 0.0001)
            in_count = int(row_dict.get("input_count") or row_dict.get("inputs") or row_dict.get("in_degree") or 1)
            out_count = int(row_dict.get("output_count") or row_dict.get("outputs") or row_dict.get("out_degree") or 2)
            time_step = int(row_dict.get("time_step") or row_dict.get("timestep") or row_dict.get("epoch") or 1)

            src_ip = str(row_dict.get("src_ip") or row_dict.get("ip") or row_dict.get("source_ip") or "").strip()
            dst_ip = str(row_dict.get("dst_ip") or row_dict.get("destination_ip") or "54.39.130.10").strip()
            raw_asn = str(row_dict.get("asn") or "").strip()
            scenario = str(row_dict.get("scenario") or "").strip().lower()

            # GeoIP enrichment if IP present
            if src_ip and src_ip != "UNKNOWN":
                geo_info = enrich_ip(src_ip)
                country = geo_info.get("geo_country", "UNKNOWN")
                asn = geo_info.get("asn", "UNKNOWN") if not raw_asn else raw_asn
            else:
                country = str(row_dict.get("country") or row_dict.get("geo_country") or "UNKNOWN")
                asn = raw_asn if raw_asn else "AS15169"

            is_bulletproof_asn = asn in HIGH_RISK_ASNS

            # 2. Extract domain risk signals
            # Signal A: On-chain Fan-Out / Peel Chain
            fan_out_ratio = (out_count + 1e-4) / (in_count + 1e-4)
            is_peel_chain = (out_count >= 6 and in_count <= 2) or (fan_out_ratio >= 4.0)

            # Signal B: Fee Anomaly
            fee_ratio = (fee + 1e-6) / (amount + 1e-4)
            is_fee_anomaly = fee_ratio > 0.05 or fee > 0.01

            # Signal C: Network burst / Tor / Bulletproof
            is_net_burst = scenario in ["burst_behavior", "rapid_movement", "high_frequency", "asn_concentration"] or is_bulletproof_asn

            # Signal D: Graph neighbor taint proxy
            neighbor_taint = float(row_dict.get("graph_neighbor_illicit_ratio") or row_dict.get("neighbor_risk") or 0.0)
            is_graph_taint = neighbor_taint > 0.3

            # 3. Predict via ML Model
            ml_pred = MLService.predict_custom_transaction({
                "txid": txid,
                "input_amount": amount,
                "output_amount": amount * 0.99,
                "fee": fee,
                "input_count": in_count,
                "output_count": out_count,
                "asn": asn
            })

            prob_illicit = ml_pred["classification_probability"]
            anomaly_score = ml_pred["anomaly_score"]

            # Compute custom composite risk score
            # Classification 40%, Anomaly 20%, Graph 20%, Behavior 10%, Network 10%
            graph_risk = 0.85 if is_graph_taint else (0.60 if is_peel_chain else 0.15)
            behavior_risk = min(1.0, fan_out_ratio / 5.0)
            network_risk = 0.85 if is_bulletproof_asn else (0.70 if is_net_burst else 0.10)

            score, severity = cls.risk_engine.compute_risk_score(
                prob_illicit=prob_illicit,
                anomaly_score=anomaly_score,
                graph_risk=graph_risk,
                behavior_risk=behavior_risk,
                network_risk=network_risk
            )

            # 4. Determine Classification (Attack / Suspicious vs Normal)
            is_attack = (score >= 45.0) or (prob_illicit >= 0.50) or is_bulletproof_asn or is_peel_chain

            # 5. Determine Attack Type & Detection Layer
            layers_triggered = []
            attack_type = "Normal P2P Propagation"
            reasons = []

            if is_attack:
                attack_count += 1

                if is_peel_chain and is_bulletproof_asn:
                    attack_type = "Ransomware Payout & Fast Layering"
                    layers_triggered.extend(["Blockchain Layer", "Network Layer"])
                    reasons.append(f"Severe peel-chain dispersion ({out_count} outputs) routed through bulletproof ASN {asn}.")
                elif is_peel_chain:
                    attack_type = "Peel-Chain Mixer / Laundering"
                    layers_triggered.append("Blockchain Layer")
                    reasons.append(f"Abnormal fan-out structure ({out_count} outputs to {in_count} inputs) indicating funds layering.")
                elif is_bulletproof_asn:
                    attack_type = "Bulletproof / Tor Infrastructure Relay"
                    layers_triggered.append("Network Layer")
                    reasons.append(f"Originating from known bulletproof/darknet hosting infrastructure ({asn}).")
                elif is_net_burst:
                    attack_type = "P2P Network Relay Burst / Flooding"
                    layers_triggered.append("Network Layer")
                    reasons.append(f"Connection telemetry matches automated P2P relay burst signature ({scenario}).")
                elif is_graph_taint:
                    attack_type = "Darknet / Sanctioned Counterparty Taint"
                    layers_triggered.append("Graph Layer")
                    reasons.append(f"Direct topological proximity to known illicit clusters ({int(neighbor_taint*100)}% tainted neighbors).")
                elif is_fee_anomaly:
                    attack_type = "Anomalous Transaction Fee (Griefing/Dust)"
                    layers_triggered.append("Blockchain Layer")
                    reasons.append(f"Substantial fee anomaly ({fee} BTC) compared to transacted volume ({amount} BTC).")
                else:
                    attack_type = "High-Risk Anomaly Lead"
                    layers_triggered.append("Blockchain Layer")
                    reasons.append("Multiple statistical variance metrics exceeded baseline thresholds.")

                # Check if multiple layers triggered
                if len(set(layers_triggered)) > 1:
                    primary_layer = "Multi-Layer Fusion"
                elif len(layers_triggered) == 1:
                    primary_layer = layers_triggered[0]
                else:
                    primary_layer = "Blockchain Layer"

            else:
                normal_count += 1
                attack_type = "Normal / Licit Bitcoin Traffic"
                primary_layer = "None (Normal)"
                reasons.append("Standard transaction structure, normal fee ratio, and licit network propagation routing.")

            layer_counts[primary_layer] = layer_counts.get(primary_layer, 0) + 1
            attack_type_counts[attack_type] = attack_type_counts.get(attack_type, 0) + 1

            # Build record result
            results.append({
                "row_number": idx + 1,
                "txid": txid,
                "status": "Attack / Suspicious" if is_attack else "Normal / Licit",
                "attack_type": attack_type,
                "detection_layer": primary_layer,
                "risk_score": score,
                "risk_level": severity,
                "ml_probability": round(prob_illicit, 4),
                "anomaly_score": round(anomaly_score, 4),
                "why_flagged": reasons,
                "details": {
                    "amount_btc": amount,
                    "fee_btc": fee,
                    "input_count": in_count,
                    "output_count": out_count,
                    "src_ip": src_ip if src_ip else "N/A",
                    "asn": asn,
                    "country": country,
                    "time_step": time_step,
                    "scenario": scenario if scenario else "standard"
                },
                "shap_contributions": ml_pred.get("shap_contributions", [])[:4]
            })

        total = len(results)
        attack_pct = round((attack_count / total * 100), 2) if total > 0 else 0.0

        return {
            "total_records": total,
            "attack_count": attack_count,
            "normal_count": normal_count,
            "attack_percentage": attack_pct,
            "scan_duration_ms": round((time.time() - start_time) * 1000, 2),
            "layer_breakdown": [{"layer": k, "count": v} for k, v in layer_counts.items() if v > 0],
            "attack_type_breakdown": [{"type": k, "count": v} for k, v in attack_type_counts.items()],
            "records": results
        }
