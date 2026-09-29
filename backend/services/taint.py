"""Risk-taint propagation over the heterogeneous investigation graph."""

from collections import deque
from typing import Any, Dict, Iterable

import networkx as nx


def _resolve_seed_nodes(graph: nx.Graph, seed_wallets: Iterable[str]) -> list[str]:
    seeds: list[str] = []
    for seed in seed_wallets:
        value = str(seed)
        candidates = [value, f"wallet_{value}"]
        for node_id, attrs in graph.nodes(data=True):
            if str(attrs.get("entity_id", "")) == value:
                candidates.insert(0, str(node_id))
                break
        resolved = next((candidate for candidate in candidates if candidate in graph), None)
        if resolved and resolved not in seeds:
            seeds.append(resolved)
    return seeds


def calculate_taint_propagation(
    graph: nx.Graph,
    seed_wallets: Iterable[str],
    alpha: float = 0.85,
    max_hops: int = 4,
) -> Dict[str, float]:
    """Calculate normalized downstream taint scores using personalized PageRank."""
    if not 0.0 <= alpha < 1.0:
        raise ValueError("alpha must be between 0.0 and 1.0")
    if max_hops < 0:
        raise ValueError("max_hops must be non-negative")

    seeds = _resolve_seed_nodes(graph, seed_wallets)
    if not seeds:
        return {}

    reachable = set(seeds)
    queue = deque((seed, 0) for seed in seeds)
    while queue:
        node, hops = queue.popleft()
        if hops >= max_hops:
            continue
        for neighbor in graph.successors(node) if graph.is_directed() else graph.neighbors(node):
            if neighbor not in reachable:
                reachable.add(neighbor)
                queue.append((neighbor, hops + 1))

    scoped_graph = graph.subgraph(reachable).copy()
    personalization = {node: 0.0 for node in scoped_graph.nodes}
    for seed in seeds:
        personalization[seed] = 1.0 / len(seeds)
    pagerank = nx.pagerank(scoped_graph, alpha=alpha, personalization=personalization)
    maximum = max(pagerank.values(), default=0.0)
    if maximum == 0.0:
        return {node: 0.0 for node in pagerank}
    return {node: round((score / maximum) * 100.0, 4) for node, score in pagerank.items()}


def build_taint_traces(graph: nx.Graph, seed_wallets: Iterable[str], scores: Dict[str, float], max_hops: int) -> list[Dict[str, Any]]:
    """Return shortest downstream paths for nodes with calculated taint."""
    seeds = _resolve_seed_nodes(graph, seed_wallets)
    traces = []
    for node_id, score in sorted(scores.items(), key=lambda item: item[1], reverse=True):
        if node_id in seeds:
            path = [node_id]
        else:
            paths = []
            for seed in seeds:
                try:
                    paths.append(nx.shortest_path(graph, seed, node_id))
                except nx.NetworkXNoPath:
                    continue
            path = min(paths, key=len) if paths else []
        if path and len(path) - 1 <= max_hops:
            traces.append({"node_id": node_id, "risk_score": score, "hops": len(path) - 1, "path": path})
    return traces
