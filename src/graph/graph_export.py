"""
Graph Export & Link Analysis Service.
Extracts ego-networks, calculates shortest paths, and formats graph elements for Cytoscape.js visualization.
"""

import logging
from typing import Dict, List, Any, Optional, Set
import networkx as nx

logger = logging.getLogger(__name__)

class GraphExporter:
    """Formats and exports NetworkX graph queries for interactive visualization."""

    @staticmethod
    def get_ego_subgraph(
        G: nx.DiGraph,
        center_node: str,
        depth: int = 2,
        max_nodes: int = 80
    ) -> Dict[str, Any]:
        """
        Extracts a k-hop neighborhood subgraph around a center entity.
        Returns Cytoscape-formatted { "nodes": [...], "edges": [...] }.
        """
        if center_node.startswith("ALERT-") or center_node.startswith("ALT-"):
            center_node = center_node.split("-", 1)[1]

        if center_node not in G:
            # Try the displayed entity ID and typed node prefixes.
            matching_node = next(
                (
                    str(node_id)
                    for node_id, attrs in G.nodes(data=True)
                    if str(attrs.get("entity_id", "")) == center_node
                ),
                None,
            )
            if matching_node:
                center_node = matching_node

        if center_node not in G:
            candidates = [f"tx_{center_node}", f"wallet_{center_node}", f"ip_{center_node}", f"asn_{center_node}", f"country_{center_node}"]
            for c in candidates:
                if c in G:
                    center_node = c
                    break

        if center_node not in G:
            return {"nodes": [], "edges": [], "error": f"Node {center_node} not found"}

        # BFS neighborhood
        visited: Set[str] = {center_node}
        current_layer: Set[str] = {center_node}

        for _ in range(depth):
            next_layer: Set[str] = set()
            for node in current_layer:
                nbrs = set(G.successors(node)).union(set(G.predecessors(node)))
                for nbr in nbrs:
                    if nbr not in visited:
                        visited.add(nbr)
                        next_layer.add(nbr)
                        if len(visited) >= max_nodes:
                            break
                if len(visited) >= max_nodes:
                    break
            current_layer = next_layer
            if len(visited) >= max_nodes or not current_layer:
                break

        subgraph = G.subgraph(visited)
        return GraphExporter.to_cytoscape_json(subgraph, highlight_node=center_node)

    @staticmethod
    def find_shortest_path(
        G: nx.DiGraph,
        source_id: str,
        target_id: str
    ) -> Dict[str, Any]:
        """Calculates shortest flow path between two entities."""
        def resolve_node(entity_id: str) -> str:
            if entity_id in G:
                return entity_id

            # The canvas displays attrs['entity_id'], while NetworkX stores
            # typed node IDs such as tx_tx_... and wallet_....
            for node_id, attrs in G.nodes(data=True):
                if str(attrs.get("entity_id", "")) == entity_id:
                    return str(node_id)

            candidates = [
                f"tx_{entity_id}",
                f"wallet_{entity_id}",
                f"ip_{entity_id}",
                f"asn_{entity_id}",
                f"country_{entity_id}",
            ]
            return next((candidate for candidate in candidates if candidate in G), entity_id)

        source_id = resolve_node(source_id)
        target_id = resolve_node(target_id)

        if source_id not in G or target_id not in G:
            return {"nodes": [], "edges": [], "path": [], "found": False}

        try:
            # Directed or undirected path
            path = nx.shortest_path(G.to_undirected(), source=source_id, target=target_id)
            subgraph = G.subgraph(path)
            res = GraphExporter.to_cytoscape_json(subgraph)
            res["path"] = path
            res["found"] = True
            return res
        except nx.NetworkXNoPath:
            return {"nodes": [], "edges": [], "path": [], "found": False}

    @staticmethod
    def to_cytoscape_json(
        subgraph: nx.DiGraph,
        highlight_node: Optional[str] = None
    ) -> Dict[str, Any]:
        """Converts NetworkX subgraph into Cytoscape.js graph JSON elements."""
        nodes = []
        edges = []

        for node_id, attrs in subgraph.nodes(data=True):
            entity_type = attrs.get("entity_type", "Transaction")
            label = attrs.get("label", node_id)
            risk = float(attrs.get("risk_score", 20.0))

            nodes.append({
                "data": {
                    "id": str(node_id),
                    "label": f"{entity_type}: {attrs.get('entity_id', node_id)[:12]}",
                    "full_label": str(attrs.get("entity_id", node_id)),
                    "entity_type": entity_type,
                    "risk_score": risk,
                    "is_center": (node_id == highlight_node),
                    "time_step": attrs.get("time_step", 1),
                    "raw_label": str(attrs.get("label", ""))
                }
            })

        edge_idx = 0
        for u, v, attrs in subgraph.edges(data=True):
            relation = attrs.get("relation", "FLOWS")
            edges.append({
                "data": {
                    "id": f"e_{edge_idx}_{u}_{v}",
                    "source": str(u),
                    "target": str(v),
                    "relation": relation,
                    "weight": float(attrs.get("weight", 1.0))
                }
            })
            edge_idx += 1

        return {"nodes": nodes, "edges": edges}
