# ARCHITECTURE.md — AI-Powered Bitcoin Transaction Investigation Platform

## 1. Executive Summary
The Bitcoin Transaction Investigation Platform (NTRO 26146) is an end-to-end, offline-capable decision-support system for cyber analysts and law enforcement agencies. It correlates on-chain transaction mechanics with synthetic P2P network telemetry to detect, score, explain, and visualize suspicious cryptocurrency flows.

---

## 2. Layered Architectural Blueprint

```
+-------------------------------------------------------------------------------+
|                             INVESTIGATOR WEB UI                               |
|  React 18 + TypeScript + Vite + Tailwind CSS + Cytoscape.js + Lucide Icons    |
|  Views: Overview | Alerts | Dossier | Graph Links | ML Stats | Data | Status  |
+---------------------------------------+---------------------------------------+
                                        | HTTP / JSON REST APIs
                                        v
+-------------------------------------------------------------------------------+
|                              FASTAPI BACKEND                                  |
|  - Auth & Security: CORS, Pydantic validation, safe XML, rate limiting        |
|  - Routers: /api/alerts, /api/transactions, /api/graph, /api/models, /search  |
|  - Report Engine: Automated PDF / JSON / CSV Dossier Generation              |
+-------------------+---------------------------------------+-------------------+
                    |                                       |
                    v                                       v
+---------------------------------------+ +-------------------------------------+
|        STORAGE & DATA ACCESS          | |        GRAPH ANALYTICS ENGINE       |
|  - DuckDB (data/bitcoin.duckdb)       | |  - NetworkX heterogeneous graph     |
|  - Polars & PyArrow streaming         | |  - PageRank, Betweenness, Centrality|
|  - Ingestion Quarantine (data/errors/)| |  - Multi-hop Exposure, Risk Flow    |
|  - Model Artifact Store (models/)     | |  - Subgraph & Shortest Path Extractor
+-------------------+-------------------+ +------------------+------------------+
                    |                                        |
                    +-------------------+--------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
|                          AI & RISK INFERENCE ENGINE                           |
|  - Supervised Ensemble: XGBoost, Random Forest, Extra Trees, LogReg           |
|  - Unsupervised Anomaly: Isolation Forest, Local Outlier Factor               |
|  - Explainability: TreeSHAP local attributions & human-readable evidence synthesis
|  - Multi-Factor Risk Fusion: 0-100 score (Classifier + Anomaly + Graph + Net) |
+---------------------------------------+---------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
|                       DATA INGESTION & PIPELINE ENGINE                        |
|  - Multi-format loader (CSV, JSON, XML) & Schema Validator                    |
|  - Real Blockchain Dataset (Elliptic 203k transactions)                       |
|  - Deterministic Synthetic Network Generator (10 cyber scenarios)             |
|  - Offline GeoIP / ASN Enrichment Engine                                      |
+-------------------------------------------------------------------------------+
```

---

## 3. Risk Fusion Formula
Risk is calculated deterministically on a calibrated 0–100 scale:

$$\text{Risk Score} = 100 \times \left( 0.40 \cdot P(\text{illicit}) + 0.20 \cdot S_{\text{anomaly}} + 0.20 \cdot R_{\text{graph}} + 0.10 \cdot R_{\text{behavior}} + 0.10 \cdot R_{\text{network}} \right)$$

Where:
- $P(\text{illicit}) \in [0, 1]$: Calibrated supervised classification probability.
- $S_{\text{anomaly}} \in [0, 1]$: Min-max normalized Isolation Forest anomaly score.
- $R_{\text{graph}} \in [0, 1]$: Weighted combination of PageRank, neighbor illicit ratio, and multi-hop taint.
- $R_{\text{behavior}} \in [0, 1]$: Transaction velocity, burstiness, and fee anomaly index.
- $R_{\text{network}} \in [0, 1]$: ASN risk profile, geographic routing anomaly, and connection burstiness.

### Severity Tiers:
- **Low**: $0 \le \text{Score} < 25$
- **Medium**: $25 \le \text{Score} < 50$
- **High**: $50 \le \text{Score} < 75$
- **Critical**: $75 \le \text{Score} \le 100$

---

## 4. Explainable AI & Evidence Synthesis
1. **TreeSHAP Attributions**: For tree-based classifiers (XGBoost/RF), exact Shapley values quantify the positive and negative push of each feature towards the illicit prediction.
2. **Evidence Translation**: Top SHAP features are automatically mapped to domain-specific plain English rationales (e.g. `feat_fan_out > 2.5` $\to$ "Unusual fan-out structure indicating potential peel chain distribution").
3. **Graph & Network Evidence**: Directly extracts flagged counterparty addresses, high-risk ASNs, and rapid connection intervals into the alert dossier.

---

## 5. Security & Offline Guarantees
- **No Remote Telemetry**: Runs completely disconnected from public internet after installation.
- **Safe Parsing**: Uses `defusedxml` to neutralize XXE / XML entity expansion attacks.
- **Strict Parameterization**: SQL queries against DuckDB use bound parameters to prevent SQL injection.
- **Path Traversal Protection**: File export and ingest paths are strictly sanitized within the project sandbox.
