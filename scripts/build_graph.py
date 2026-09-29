#!/usr/bin/env python3
"""
Graph Construction & Analytics Pipeline.
Builds the heterogeneous network and saves graph structure to disk.
"""

import os
import sys
import pickle
import logging
import argparse
import pandas as pd
import networkx as nx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.graph.graph_builder import HeterogeneousGraphBuilder

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("build_graph")

def main():
    parser = argparse.ArgumentParser(description="Construct heterogeneous transaction and entity graph.")
    parser.add_argument("--transactions", default="data/processed/canonical_transactions.parquet")
    parser.add_argument("--edges", default="data/processed/canonical_edges.parquet")
    parser.add_argument("--network", default="data/processed/canonical_network_events.parquet")
    parser.add_argument("--output-graph", default="models/preprocessors/hetero_graph.pickle")
    parser.add_argument("--output-nodes", default="data/processed/graph_nodes.parquet")
    parser.add_argument("--output-edges", default="data/processed/graph_edges.parquet")
    args = parser.parse_args()

    df_tx = pd.read_parquet(args.transactions)
    df_edges = pd.read_parquet(args.edges) if os.path.exists(args.edges) else pd.DataFrame()
    df_net = pd.read_parquet(args.network) if os.path.exists(args.network) else pd.DataFrame()

    builder = HeterogeneousGraphBuilder()
    G = builder.build_graph(df_tx, df_edges, df_net)

    os.makedirs(os.path.dirname(args.output_graph), exist_ok=True)
    with open(args.output_graph, "wb") as f:
        pickle.dump(G, f)

    # Save nodes and edges tables
    node_records = []
    for n, d in G.nodes(data=True):
        node_records.append({
            "node_id": str(n),
            "entity_id": str(d.get("entity_id", n)),
            "entity_type": str(d.get("entity_type", "Unknown")),
            "label": str(d.get("label", "unknown")),
            "risk_score": float(d.get("risk_score", 0.0))
        })
    df_nodes = pd.DataFrame(node_records)
    df_nodes.to_parquet(args.output_nodes, index=False)

    edge_records = []
    for u, v, d in G.edges(data=True):
        edge_records.append({
            "source_id": str(u),
            "target_id": str(v),
            "relation": str(d.get("relation", "FLOWS")),
            "weight": float(d.get("weight", 1.0))
        })
    df_edges_out = pd.DataFrame(edge_records)
    df_edges_out.to_parquet(args.output_edges, index=False)

    logger.info("Successfully serialized heterogeneous graph (%d nodes, %d edges) to %s", G.number_of_nodes(), G.number_of_edges(), args.output_graph)

if __name__ == "__main__":
    main()
