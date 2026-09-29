"""Structural transaction and network pattern detectors."""

from typing import Any, Dict, Iterable

import networkx as nx


def _badge(name: str, confidence: float, reason: str) -> Dict[str, Any]:
    return {"pattern": name, "confidence": round(max(0.0, min(1.0, confidence)), 4), "reason": reason}


def detect_peeling_chain(tx_record: Dict[str, Any], graph: nx.Graph) -> Dict[str, Any] | None:
    input_count = int(tx_record.get("input_count", 0) or 0)
    output_count = int(tx_record.get("output_count", 0) or 0)
    if input_count != 1 or output_count != 2:
        return None
    total = float(tx_record.get("output_amount", tx_record.get("amount", 0.0)) or 0.0)
    outputs = tx_record.get("output_values") or tx_record.get("outputs") or []
    if outputs:
        values = [float(value) for value in outputs]
        total = sum(values)
        small_fraction = min(values) / total if total else 1.0
    else:
        small_fraction = float(tx_record.get("small_output_fraction", 0.05) or 0.05)
    if total <= 0 or small_fraction >= 0.10:
        return None

    txid = str(tx_record.get("txid", tx_record.get("transaction_id", "")))
    node_id = txid if txid in graph else f"tx_{txid}"
    chain_length = 1
    if node_id in graph:
        current = node_id
        while chain_length < 3:
            next_transactions = [
                neighbor for neighbor in graph.successors(current)
                if str(graph.nodes[neighbor].get("entity_type", "")).lower() == "transaction"
            ] if graph.is_directed() else []
            if not next_transactions:
                break
            current = next_transactions[0]
            chain_length += 1
    if chain_length < 3:
        return None
    return _badge("peeling_chain", min(1.0, 0.65 + chain_length * 0.08), f"One input splits into two outputs; one carries {small_fraction:.1%} and continues across {chain_length} transaction hops.")


def detect_coinjoin(tx_record: Dict[str, Any]) -> Dict[str, Any] | None:
    inputs = int(tx_record.get("input_count", 0) or 0)
    outputs = int(tx_record.get("output_count", 0) or 0)
    values = tx_record.get("output_values") or tx_record.get("outputs") or []
    if inputs < 5 or outputs < 5 or len(values) < 5:
        return None
    numeric = [float(value) for value in values]
    average = sum(numeric) / len(numeric)
    equal = average > 0 and max(abs(value - average) / average for value in numeric) <= 0.01
    return _badge("coinjoin", 0.9 if equal else 0.0, f"Transaction has {inputs} inputs and {outputs} outputs with near-equal output values.") if equal else None


def detect_sybil_ip(src_ip: str, graph: nx.Graph) -> Dict[str, Any] | None:
    node_id = src_ip if src_ip in graph else f"ip_{src_ip}"
    if node_id not in graph:
        return None
    transactions = [
        neighbor for neighbor in graph.neighbors(node_id)
        if str(graph.nodes[neighbor].get("entity_type", "")).lower() == "transaction"
    ]
    if graph.is_directed():
        transactions = list(set(transactions + list(graph.predecessors(node_id))))
    if len(set(transactions)) <= 30:
        return None
    timesteps = [int(graph.nodes[node].get("time_step", 0) or 0) for node in transactions]
    spread = max(timesteps, default=0) - min(timesteps, default=0)
    confidence = min(1.0, 0.7 + len(set(transactions)) / 300.0) if spread <= 10 else 0.65
    return _badge("sybil_ip_burst", confidence, f"Source IP broadcasts to {len(set(transactions))} distinct transactions across a {spread}-timestep window.")


def evaluate_all_patterns(tx_data: Dict[str, Any], graph: nx.Graph) -> list[Dict[str, Any]]:
    badges = []
    peel = detect_peeling_chain(tx_data, graph)
    coinjoin = detect_coinjoin(tx_data)
    sybil = detect_sybil_ip(str(tx_data.get("src_ip", "")), graph) if tx_data.get("src_ip") else None
    for badge in (peel, coinjoin, sybil):
        if badge:
            badges.append(badge)
    return badges
