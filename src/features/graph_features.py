"""
Graph Metric Feature Extraction.
Computes PageRank, In/Out-Degree, Centrality, Clustering, and Neighborhood Risk.
"""

import pandas as pd
import numpy as np
import networkx as nx
from typing import Dict, Any

def compute_graph_features(df_tx: pd.DataFrame, df_edges: pd.DataFrame) -> pd.DataFrame:
    """Computes structural topological graph metrics for each transaction."""
    df_feat = df_tx[["txid"]].copy()

    # Build directed graph from transactions
    G = nx.DiGraph()
    for tx in df_tx["txid"]:
        G.add_node(str(tx))

    if not df_edges.empty:
        for _, row in df_edges.iterrows():
            u = str(row["source_txid"])
            v = str(row["target_txid"])
            if u in G and v in G:
                G.add_edge(u, v)

    # Compute PageRank
    try:
        pagerank = nx.pagerank(G, alpha=0.85, max_iter=100)
    except Exception:
        pagerank = {n: 1.0 / max(1, len(G)) for n in G.nodes()}

    # In/Out Degree
    in_degrees = dict(G.in_degree())
    out_degrees = dict(G.out_degree())

    df_feat["graph_pagerank"] = df_feat["txid"].map(lambda x: pagerank.get(str(x), 0.0)).astype(float)
    df_feat["graph_in_degree"] = df_feat["txid"].map(lambda x: in_degrees.get(str(x), 0)).astype(float)
    df_feat["graph_out_degree"] = df_feat["txid"].map(lambda x: out_degrees.get(str(x), 0)).astype(float)
    df_feat["graph_degree_ratio"] = (df_feat["graph_out_degree"] + 1e-4) / (df_feat["graph_in_degree"] + 1e-4)

    # Neighborhood illicit risk propagation
    illicit_set = set(df_tx[df_tx["label"] == "illicit"]["txid"].astype(str))
    neighbor_risk = {}
    for node in G.nodes():
        neighbors = list(G.successors(node)) + list(G.predecessors(node))
        if not neighbors:
            neighbor_risk[node] = 0.0
        else:
            illicit_neighbors = sum(1 for nb in neighbors if nb in illicit_set)
            neighbor_risk[node] = illicit_neighbors / len(neighbors)

    df_feat["graph_neighbor_illicit_ratio"] = df_feat["txid"].map(lambda x: neighbor_risk.get(str(x), 0.0)).astype(float)
    df_feat["graph_multi_hop_exposure"] = df_feat["graph_neighbor_illicit_ratio"] * (df_feat["graph_pagerank"] * 1000.0)

    return df_feat
