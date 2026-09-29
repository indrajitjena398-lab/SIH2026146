# Heterogeneous Graph Model & Topological Analytics

## 1. Entity-Relationship Schema
The investigation graph models 5 heterogeneous entity types and directed relations:

### Entities:
1. `Transaction` (`tx_<txid>`): On-chain payment unit.
2. `Wallet` (`wallet_<address>`): Input / Output address anchor.
3. `IP` (`ip_<src_ip>`): P2P network relay node.
4. `ASN` (`asn_<asn>`): Autonomous system network provider.
5. `Country` (`country_<geo_country>`): Geopolitical jurisdiction.

### Directed Relations:
- `INPUT_TO`: Wallet $\to$ Transaction
- `OUTPUT_TO`: Transaction $\to$ Wallet
- `FOLLOWS`: Transaction $\to$ Transaction
- `OBSERVED_FROM`: Transaction $\to$ IP
- `BELONGS_TO`: IP $\to$ ASN
- `LOCATED_IN`: IP $\to$ Country

---

## 2. Graph Metrics Computed
- **PageRank**: Measures topological flow accumulation and centrality.
- **In-Degree & Out-Degree**: Quantifies fan-in aggregation and peel-chain fan-out.
- **Neighborhood Illicit Ratio**: Direct 1-hop proportion of known illicit counterparties.
- **Multi-Hop Exposure**: Downstream taint propagation from darknet clusters.
