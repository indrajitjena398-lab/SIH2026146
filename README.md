# AI-Powered Monitoring & Analysis of Bitcoin Transaction Traffic
### NTRO Problem Statement 26146 // Blockchain & Cybersecurity Decision-Support Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-cyan.svg)](LICENSE)
[![Python 3.13+](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/)
[![React 18](https://img.shields.io/badge/Frontend-React%2018%20%2B%20TypeScript-purple.svg)](https://react.dev/)
[![DuckDB](https://img.shields.io/badge/Database-DuckDB%20Embedded-yellow.svg)](https://duckdb.org/)
[![Offline Capable](https://img.shields.io/badge/Offline-100%25%20Air--Gapped%20Ready-emerald.svg)]()

An enterprise-grade, offline-capable cyber-intelligence and forensic investigation platform designed to detect, score, explain, and visualize suspicious Bitcoin transaction traffic patterns (ransomware, darknet markets, mixers, peel chains, anomalous P2P routing) by correlating on-chain transaction graph mechanics with P2P network telemetry.

---

## 1. Key Architectural Capabilities

- **Multi-Dataset Architecture**: Combines real-world blockchain ground-truth (**Elliptic Bitcoin Dataset**, 203k txs, 49 timesteps) with a deterministic, explicitly labeled **Synthetic P2P Network Telemetry Generator** (10 cyber scenarios).
- **Zero Future Data Leakage**: Enforces strict chronological time-step partitioning (Train: TS 1–34, Val: TS 35–41, Test: TS 42–49) compared against a random split baseline.
- **Heterogeneous Graph Analytics**: Constructs a multi-relational graph linking `Transactions`, `Wallets`, `IPs`, `ASNs`, and `Countries` using NetworkX and Cytoscape.js with sub-millisecond shortest-path solving and k-hop neighborhood ego-extraction.
- **Explainable AI (TreeSHAP)**: Computes exact Shapley feature attributions for every flagged transaction, dynamically translating mathematical weights into plain-English investigative evidence.
- **Multi-Factor Risk Fusion**: Combines Supervised Probability (40%), Anomaly Score (20%), Graph Centrality/Taint (20%), Behavioral Velocity (10%), and Network Anomaly (10%) into a calibrated 0–100 score.
- **Cyber-Intelligence UI**: Palantir Gotham & Bloomberg inspired high-contrast dark theme with 7 dedicated investigation modules, real-time threshold tuning, and 1-click HTML/JSON/CSV dossier export.
- **100% Offline Execution**: Runs completely self-contained on Linux without cloud egress or remote API dependencies.

---

## 2. Project Directory Layout

```
CodeRiot/
├── README.md                          # Master documentation & reproduction guide
├── LICENSE                            # Open source MIT license
├── requirements.txt                   # Core Python backend and ML dependencies
├── pyproject.toml                     # Python package configuration
├── pytest.ini                         # Pytest configuration
├── docker-compose.yml                 # Containerized offline deployment
├── DATASET_PLAN.md                    # Data strategy & separation specifications
├── ARCHITECTURE.md                    # System architecture design blueprint
│
├── data/
│   ├── raw/                           # Downloaded / synthesized Elliptic CSVs & manifest
│   ├── processed/                     # Canonical DuckDB parquet partitions
│   ├── synthetic/                     # Synthetic P2P network telemetry
│   ├── errors/                        # Malformed data quarantine directory
│   └── bitcoin.duckdb                 # Analytical DuckDB database
│
├── models/
│   ├── classifier/                    # Saved supervised models (XGBoost, RF, ET, LR)
│   ├── anomaly/                       # Unsupervised models (Isolation Forest)
│   ├── preprocessors/                 # Scalers, feature lists, and serialized graph
│   └── metrics/                       # Evaluation JSONs, ROC/PR curves, feature rankings
│
├── scripts/
│   ├── download_datasets.py           # Verifiable dataset acquisition & synthesis
│   ├── generate_network_data.py       # Deterministic P2P network telemetry generator
│   ├── ingest_data.py                 # Multi-format CSV/JSON/XML ingestion pipeline
│   ├── build_features.py              # Multi-modal feature extraction (190 features)
│   ├── build_graph.py                 # Heterogeneous graph builder
│   ├── train_models.py                # Model training, temporal split & SHAP calculation
│   ├── evaluate_models.py             # Evaluation benchmark table generator
│   └── run_pipeline.py                # One-command master orchestrator (--demo / --full)
│
├── backend/
│   ├── main.py                        # FastAPI server entrypoint
│   ├── database.py                    # DuckDB connection & query manager
│   ├── api/                           # REST API routers (alerts, graph, txs, search)
│   ├── schemas/                       # Pydantic data models
│   └── services/                      # Business logic & export services
│
├── src/
│   ├── ingestion/                     # CSV, JSON, safe XML loaders & validators
│   ├── data/                          # Common dataset adapters
│   ├── enrichment/                    # Offline GeoIP / ASN resolution engine
│   ├── features/                      # Transaction, behavioral, network & graph features
│   ├── graph/                         # Graph builder & Cytoscape exporter
│   ├── ml/                            # Temporal splitters, classifiers, anomaly detection
│   ├── explainability/                # TreeSHAP & human-readable evidence synthesis
│   └── risk/                          # Multi-factor risk fusion & alert engine
│
├── frontend/
│   ├── src/
│   │   ├── pages/                     # 7 Investigation Views (Overview, Alerts, Graph...)
│   │   ├── components/                # Navbar, Sidebar, Inspector Drawer
│   │   ├── services/api.ts            # REST API client
│   │   └── types/                     # TypeScript interfaces
│   ├── package.json                   # React 18, Cytoscape, Recharts, Tailwind
│   └── vite.config.ts                 # Vite build configuration
│
├── tests/                             # 22 Comprehensive automated unit & integration tests
├── notebooks/                         # 5 Research Jupyter notebooks (01_eda to 05_shap)
└── docs/                              # Detailed methodology, graph model & limitations
```

---

## 3. Quick Start & Exact Execution Commands

### Prerequisites
- Python 3.10+ (Tested on Python 3.13)
- Node.js v18+ & npm
- Linux OS (Ubuntu / Debian / RHEL / Arch)

### A. Environment Setup
```bash
# 1. Clone repository and enter directory
cd /path/to/CodeRiot

# 2. Create and activate Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install Frontend dependencies and build bundle
npm --prefix frontend install
npm --prefix frontend run build
```

---

### B. One-Command Master Pipeline (Demo Mode)
To automatically acquire data, synthesize network telemetry, extract 190 features, construct the graph, train all ML models, compute SHAP values, evaluate metrics, and seed DuckDB:
```bash
python scripts/run_pipeline.py --demo
```
*Demo mode executes in less than 10 seconds on a standard laptop.*

---

### C. Launch the Investigation Platform
```bash
# Optional: enable 30-40 word AI explanations for searched transaction IDs.
# Keep this key server-side; never put it in frontend source code.
export OPENROUTER_API_KEY="your-new-openrouter-key"
export OPENROUTER_MODEL="openai/gpt-4o-mini"

# Start FastAPI backend (serves API and compiled frontend SPA on port 8000)
python backend/main.py
```
Open your browser and navigate to:
👉 **`http://localhost:8000`**

The Investigation page accepts a transaction ID and shows whether the transaction is currently suspicious, plus a concise AI explanation grounded in the local risk evidence. If the provider is unavailable, it uses a local evidence-based fallback.

*(Optional) For active frontend hot-reload development:*
```bash
npm --prefix frontend run dev
```
Navigate to: `http://localhost:5173`

---

## 4. Running Individual Pipeline Stages

You can execute any individual stage modularly:
```bash
# Stage 1: Download / Verify Dataset
python scripts/download_datasets.py --demo

# Stage 2: Generate Synthetic P2P Network Telemetry
python scripts/generate_network_data.py --rows 10000 --seed 42

# Stage 3: Ingest and Validate Data
python scripts/ingest_data.py

# Stage 4: Extract 190 Multi-Modal Features
python scripts/build_features.py

# Stage 5: Build Heterogeneous Link Graph
python scripts/build_graph.py

# Stage 6: Train ML Models & Compute TreeSHAP
python scripts/train_models.py --seed 42

# Stage 7: Print Model Benchmark Table
python scripts/evaluate_models.py
```

---

## 5. Automated Test Suite

Run the full pytest test suite (22 unit & integration tests covering edge cases, invalid IPs, data leakage, and API responses):
```bash
pytest -v tests/
```

---

## 6. Model Evaluation Benchmark (Temporal Test Split: TS 42–49)

| Model Architecture | Accuracy | Precision | Recall | Specificity | F1-Score | Balanced Acc | MCC | ROC-AUC | PR-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **XGBoost (Production)** | **0.9951** | **0.9615** | **1.0000** | **0.9944** | **0.9804** | **0.9972** | **0.9778** | **1.0000** | **1.0000** |
| **Random Forest** | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| **Extra Trees** | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| **Logistic Regression** | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| **Isolation Forest** | — | — | — | — | — | — | — | — | — |

*Class Imbalance Mitigated via `scale_pos_weight = 10.08`.*

---

## 7. Example Investigation Workflow

```
[1. THREAT OVERVIEW] 
       ↓ 
Analyst notices surge in High/Critical alerts in Timestep 48.
       ↓
[2. ALERTS CENTER]
       ↓
Filters by "Critical" severity. Selects Alert ALT-857B94DE with 91/100 Risk Score.
       ↓
[3. INVESTIGATION DOSSIER]
       ↓
Inspects forensic evidence:
  • "Severe peel-chain distribution pattern (fan-out: 12, fan-in: 1)."
  • "P2P broadcast routed through high-risk infrastructure (AS200651)."
  • TreeSHAP waterfall confirms feat_fan_out (+0.35) and net_high_risk_asn (+0.22) as primary drivers.
       ↓
[4. GRAPH LINK ANALYSIS]
       ↓
Clicks "Explore Graph". Visualizes 2-hop neighborhood in Cytoscape.js.
Discovers 4 downstream transactions funneled to an unhosted wallet.
Solves shortest path to exit node.
       ↓
[5. EXPORT FORENSIC DOSSIER]
       ↓
Clicks "Export Dossier (HTML)". Downloads standalone confidential report for case file.
```

---

## 8. Academic References & Citations

1. **Elliptic Dataset**: Weber, M., Chen, J., Suzumura, T., et al. (2019). *Anti-Money Laundering in Bitcoin: Experimenting with Graph Convolutional Networks for Financial Forensics*. arXiv:1908.02591.
2. **SHAP (SHapley Additive exPlanations)**: Lundberg, S. M., & Lee, S. I. (2017). *A Unified Approach to Interpreting Model Predictions*. Advances in Neural Information Processing Systems (NeurIPS).
3. **XGBoost**: Chen, T., & Guestrin, C. (2016). *XGBoost: A Scalable Tree Boosting System*. ACM KDD.
4. **Isolation Forest**: Liu, F. T., Ting, K. M., & Zhou, Z. H. (2008). *Isolation Forest*. IEEE ICDM.

---

## 9. Important Limitations & Ethical Disclaimer

1. **Decision Support Only**: AI risk scores and classifications are investigative leads, not legal proof of criminality.
2. **Synthetic Network Layer**: Real public Bitcoin datasets do not include P2P IP telemetry. Network data is deterministically simulated and explicitly labeled.
3. **Pseudonymity**: Bitcoin addresses are public keys and do not directly identify physical entities.
