"""
Graph Service.
Loads heterogeneous graph from disk and provides subgraphs, shortest paths, and neighbor exploration.
"""

import os
import pickle
import logging
from typing import Dict, List, Any, Optional
import networkx as nx
from src.graph.graph_export import GraphExporter

logger = logging.getLogger(__name__)

GRAPH_PATH = "models/preprocessors/hetero_graph.pickle"

class GraphService:
    """Graph query service for backend link-analysis APIs."""

    _cached_graph: Optional[nx.DiGraph] = None

    @classmethod
    def get_graph(cls) -> nx.DiGraph:
        if cls._cached_graph is None:
            if os.path.exists(GRAPH_PATH):
                logger.info("Loading cached heterogeneous graph from %s...", GRAPH_PATH)
                with open(GRAPH_PATH, "rb") as f:
                    cls._cached_graph = pickle.load(f)
            else:
                logger.warning("Graph file %s not found. Initializing empty graph.", GRAPH_PATH)
                cls._cached_graph = nx.DiGraph()
        return cls._cached_graph

    @classmethod
    def get_subgraph(
        cls,
        entity_id: str,
        depth: int = 2,
        max_nodes: int = 60,
        filter_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        G = cls.get_graph()
        result = GraphExporter.get_ego_subgraph(G, center_node=entity_id, depth=depth, max_nodes=max_nodes)
        
        if filter_types and "nodes" in result:
            allowed = set([t.lower() for t in filter_types])
            filtered_nodes = [n for n in result["nodes"] if n["data"].get("entity_type", "").lower() in allowed or n["data"].get("is_center")]
            node_ids = set([n["data"]["id"] for n in filtered_nodes])
            filtered_edges = [e for e in result["edges"] if e["data"]["source"] in node_ids and e["data"]["target"] in node_ids]
            result["nodes"] = filtered_nodes
            result["edges"] = filtered_edges

        return result

    @classmethod
    def get_shortest_path(cls, source_id: str, target_id: str) -> Dict[str, Any]:
        G = cls.get_graph()
        return GraphExporter.find_shortest_path(G, source_id=source_id, target_id=target_id)
