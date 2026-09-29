"""Common-input ownership heuristic and entity super-node aggregation."""

import hashlib
from typing import Any, Dict

import networkx as nx


def get_entity_clusters(graph: nx.Graph) -> list[Dict[str, Any]]:
    parent: Dict[str, str] = {}

    def find(value: str) -> str:
        parent.setdefault(value, value)
        if parent[value] != value:
            parent[value] = find(parent[value])
        return parent[value]

    def union(left: str, right: str) -> None:
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    tx_wallets: Dict[str, list[str]] = {}
    for tx_node, attrs in graph.nodes(data=True):
        if str(attrs.get("entity_type", "")).lower() != "transaction":
            continue
        wallets = [
            predecessor for predecessor in graph.predecessors(tx_node)
            if str(graph.nodes[predecessor].get("entity_type", "")).lower() == "wallet"
            and graph.edges[predecessor, tx_node].get("relation") == "INPUT_TO"
        ] if graph.is_directed() else []
        tx_wallets[str(tx_node)] = wallets
        for wallet in wallets:
            find(wallet)
        for wallet in wallets[1:]:
            union(wallets[0], wallet)

    clusters: Dict[str, Dict[str, Any]] = {}
    for tx_node, wallets in tx_wallets.items():
        if not wallets:
            continue
        root = find(wallets[0])
        stable_root = hashlib.sha1(root.encode("utf-8")).hexdigest()[:10]
        cluster_id = f"cluster_{stable_root}"
        attrs = graph.nodes[tx_node]
        item = clusters.setdefault(cluster_id, {"cluster_id": cluster_id, "wallets": [], "transaction_ids": [], "total_balance_moved": 0.0, "risk_score": 0.0})
        item["wallets"] = sorted(set(item["wallets"] + [str(graph.nodes[w].get("entity_id", w)) for w in wallets]))
        item["transaction_ids"].append(str(attrs.get("entity_id", tx_node)))
        item["total_balance_moved"] += float(attrs.get("input_amount", attrs.get("amount", 0.0)) or 0.0)
        item["risk_score"] = max(item["risk_score"], float(attrs.get("risk_score", 0.0) or 0.0))

    return list(clusters.values())
