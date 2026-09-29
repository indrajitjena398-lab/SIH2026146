import pytest
import pandas as pd
import networkx as nx
from src.graph.graph_builder import HeterogeneousGraphBuilder
from src.graph.graph_export import GraphExporter

def test_heterogeneous_graph_construction():
    df_tx = pd.DataFrame({
        "txid": ["tx_100", "tx_101"],
        "label": ["licit", "illicit"],
        "time_step": [1, 1]
    })
    df_edges = pd.DataFrame({"source_txid": ["tx_100"], "target_txid": ["tx_101"]})
    df_net = pd.DataFrame({
        "txid": ["tx_100"],
        "src_ip": ["3.85.192.44"],
        "asn": ["AS16509"],
        "geo_country": ["US"],
        "asn_org": ["Amazon"]
    })

    builder = HeterogeneousGraphBuilder()
    G = builder.build_graph(df_tx, df_edges, df_net)

    assert G.number_of_nodes() > 2
    assert "tx_tx_100" in G
    assert "ip_3.85.192.44" in G
    assert "asn_AS16509" in G

    # Test Cytoscape export
    res = GraphExporter.get_ego_subgraph(G, center_node="tx_tx_100", depth=1)
    assert "nodes" in res
    assert "edges" in res
    assert len(res["nodes"]) > 0
