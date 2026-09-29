"""
Heterogeneous Graph Construction Engine.
Builds multi-relational graph linking Transactions, Wallets, IPs, ASNs, and Countries.
"""

import logging
from typing import Dict, List, Any, Tuple, Optional
import networkx as nx
import pandas as pd

logger = logging.getLogger(__name__)

class HeterogeneousGraphBuilder:
    """Constructs heterogeneous entity-relationship graph."""

    def __init__(self):
        self.G = nx.DiGraph()

    def build_graph(
        self,
        df_tx: pd.DataFrame,
        df_edges: pd.DataFrame,
        df_net: pd.DataFrame
    ) -> nx.DiGraph:
        """Constructs full heterogeneous graph from processed transaction, edge, and network tables."""
        logger.info("Building heterogeneous graph...")
        self.G.clear()

        # 1. Add Transaction Nodes
        for _, row in df_tx.iterrows():
            txid = str(row["txid"])
            node_id = f"tx_{txid}"
            label = str(row.get("label", "unknown"))
            self.G.add_node(
                node_id,
                entity_id=txid,
                entity_type="Transaction",
                label=label,
                time_step=int(row.get("time_step", 1)),
                is_synthetic=bool(row.get("is_synthetic", False)),
                risk_score=float(row.get("risk_score", 0.0) if "risk_score" in row else (90.0 if label == "illicit" else (15.0 if label == "licit" else 30.0)))
            )

        # 2. Add Transaction -> Transaction Edges (FLOWS / FOLLOWS)
        if not df_edges.empty:
            for _, row in df_edges.iterrows():
                src = f"tx_{str(row['source_txid'])}"
                dst = f"tx_{str(row['target_txid'])}"
                if src in self.G and dst in self.G:
                    self.G.add_edge(src, dst, relation="FOLLOWS", weight=1.0)

        # 3. Add Synthetic Wallet/Address relationships
        # (Generating deterministic synthetic wallet anchors for realistic link-analysis)
        for _, row in df_tx.iterrows():
            txid = str(row["txid"])
            tx_node = f"tx_{txid}"
            # Synthetic deterministic wallet addresses derived from txid
            in_addr = f"1BtcIn_{txid[-6:]}"
            out_addr = f"3BtcOut_{txid[-6:]}"

            in_node = f"wallet_{in_addr}"
            out_node = f"wallet_{out_addr}"

            if in_node not in self.G:
                self.G.add_node(in_node, entity_id=in_addr, entity_type="Wallet", label="address", risk_score=20.0)
            if out_node not in self.G:
                self.G.add_node(out_node, entity_id=out_addr, entity_type="Wallet", label="address", risk_score=20.0)

            self.G.add_edge(in_node, tx_node, relation="INPUT_TO", weight=1.0)
            self.G.add_edge(tx_node, out_node, relation="OUTPUT_TO", weight=1.0)

        # 4. Add Network Telemetry Nodes (IP, ASN, Country)
        if not df_net.empty:
            for _, row in df_net.iterrows():
                txid = str(row["txid"])
                tx_node = f"tx_{txid}"
                if tx_node not in self.G:
                    continue

                src_ip = str(row.get("src_ip", "")).strip()
                asn = str(row.get("asn", "")).strip()
                country = str(row.get("geo_country", "")).strip()

                if src_ip and src_ip != "UNKNOWN":
                    ip_node = f"ip_{src_ip}"
                    if ip_node not in self.G:
                        self.G.add_node(
                            ip_node,
                            entity_id=src_ip,
                            entity_type="IP",
                            label="network_node",
                            asn=asn,
                            country=country,
                            risk_score=60.0 if asn in ["AS200651", "AS60531", "AS206264"] else 15.0
                        )
                    self.G.add_edge(tx_node, ip_node, relation="OBSERVED_FROM", weight=1.0)

                    if asn and asn != "UNKNOWN":
                        asn_node = f"asn_{asn}"
                        if asn_node not in self.G:
                            self.G.add_node(
                                asn_node,
                                entity_id=asn,
                                entity_type="ASN",
                                label="autonomous_system",
                                org=str(row.get("asn_org", "Unknown")),
                                risk_score=75.0 if asn in ["AS200651", "AS60531", "AS206264"] else 10.0
                            )
                        self.G.add_edge(ip_node, asn_node, relation="BELONGS_TO", weight=1.0)

                    if country and country != "UNKNOWN":
                        country_node = f"country_{country}"
                        if country_node not in self.G:
                            self.G.add_node(
                                country_node,
                                entity_id=country,
                                entity_type="Country",
                                label="jurisdiction",
                                risk_score=10.0
                            )
                        self.G.add_edge(ip_node, country_node, relation="LOCATED_IN", weight=1.0)

        logger.info(
            "Heterogeneous Graph constructed: %d nodes, %d edges across %s entity types",
            self.G.number_of_nodes(),
            self.G.number_of_edges(),
            set(nx.get_node_attributes(self.G, "entity_type").values())
        )
        return self.G
