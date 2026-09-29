"""
Human-Readable Evidence Synthesis Engine.
Translates technical SHAP values, graph metrics, and network observations into plain-English investigator evidence.
"""

from typing import Dict, List, Any

# Map feature prefixes and names to clear forensic descriptions
FEATURE_DESCRIPTIONS = {
    "feat_0": "Unusually high input degree (inbound transaction fan-in)",
    "feat_1": "Extremely high output degree (peel chain fan-out dispersion)",
    "feat_2": "Substantial transaction fee anomaly compared to baseline",
    "feat_3": "High transacted volume spike",
    "tx_fan_out_ratio": "Abnormal fan-out to fan-in ratio indicating funds layering",
    "behavior_velocity_index": "Accelerated fund movement velocity across consecutive blocks",
    "behavior_burstiness": "Sudden burst of transaction activity after prolonged inactivity",
    "net_high_risk_asn_flag": "Observed routing originating from known bulletproof hosting / VPN exit ASN",
    "net_burst_scenario_flag": "P2P connection burst characteristics matching automated botnet/mixer telemetry",
    "graph_pagerank": "High topological centrality and flow accumulation in the transaction graph",
    "graph_neighbor_illicit_ratio": "Directly connected to known illicit counterparty entities in 1-hop neighborhood",
    "graph_multi_hop_exposure": "Significant downstream multi-hop taint exposure to sanctioned/darknet clusters"
}

class EvidenceGenerator:
    """Synthesizes human-readable investigative reasoning from multiple evidence layers."""

    @staticmethod
    def synthesize_reasons(
        shap_contributions: List[Dict[str, Any]],
        graph_evidence: Dict[str, Any],
        network_evidence: Dict[str, Any],
        risk_score: float
    ) -> List[str]:
        """Generates a concise list of 4-6 evidentiary bullet points for an alert."""
        reasons = []

        # 1. Check SHAP feature drivers
        for item in shap_contributions:
            fname = item["feature"]
            s_val = item["shap_value"]
            if s_val > 0.05:  # Positively contributing to illicit classification
                desc = FEATURE_DESCRIPTIONS.get(fname)
                if desc and desc not in reasons:
                    reasons.append(desc)
                elif not desc and len(reasons) < 3:
                    reasons.append(f"Elevated statistical metric on feature '{fname}' (+{s_val})")

        # 2. Graph topology evidence
        neighbor_illicit = graph_evidence.get("neighbor_illicit_ratio", 0.0)
        if neighbor_illicit > 0.2:
            reasons.append(f"Connected to {int(neighbor_illicit*100)}% known illicit counterparty entities in immediate neighborhood.")
        
        in_deg = graph_evidence.get("in_degree", 0)
        out_deg = graph_evidence.get("out_degree", 0)
        if out_deg >= 5 and in_deg <= 2:
            reasons.append(f"Severe peel-chain distribution pattern (fan-out: {out_deg}, fan-in: {in_deg}).")

        # 3. Network telemetry evidence
        if network_evidence.get("has_high_risk_asn"):
            asn_name = network_evidence.get("asn", "Anonymous Transit")
            reasons.append(f"P2P node broadcast routed through high-risk infrastructure ({asn_name}).")
        
        if network_evidence.get("is_burst"):
            reasons.append("P2P connection timing exhibits rapid sub-millisecond connection bursts.")

        if network_evidence.get("ip_count", 1) >= 4:
            reasons.append(f"Simultaneously relayed across {network_evidence['ip_count']} distinct geographic IP nodes.")

        # Fallback if no specific triggers
        if not reasons:
            if risk_score >= 50:
                reasons.append("Multiple composite anomaly indicators exceeded risk detection thresholds.")
            else:
                reasons.append("Minor baseline variance detected across transaction and topological metrics.")

        return reasons[:6]
