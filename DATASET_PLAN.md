# DATASET_PLAN.md — Bitcoin Transaction & Network Dataset Strategy

## 1. Problem Context & Dataset Requirements
The NTRO 26146 problem statement requires monitoring, correlating, and detecting anomalous/illicit patterns across both:
1. **Blockchain-Layer Data**: Transaction IDs, timesteps, inputs/outputs, fees, volume, graph connectivity, known illicit/licit ground truth.
2. **Network-Layer Data**: IP addresses (source/destination), ports, P2P packet metrics, connection duration, ASN, geographic country.

---

## 2. Dataset Architecture & Separation of Concerns

### A. Primary Blockchain Dataset: Elliptic Bitcoin Transaction Dataset
- **Nature**: Real-world Bitcoin transaction graph dataset published by Elliptic & MIT-IBM Watson Lab (Weber et al., 2019).
- **Files**:
  - `elliptic_txs_features.csv`: 203,769 transactions across 49 distinct timesteps (each timestep represents a ~2-week block interval). Contains 165 normalized features (first 93 are local transaction features such as in/out degree, fee, volume; remaining 72 are 1-hop aggregate neighbor statistics).
  - `elliptic_txs_classes.csv`: Ground-truth labels for each transaction:
    - `1`: Illicit (ransomware, darknet markets, scams, sanctioned entities). (~4,545 records, 2.2%)
    - `2`: Licit (exchanges, miners, wallet services). (~42,019 records, 20.6%)
    - `unknown`: Unlabeled transactions (~157,205 records, 77.2%).
  - `elliptic_txs_edgelist.csv`: 234,355 directed transaction-to-transaction payment flow edges (`txId1` -> `txId2`).
- **Acquisition Strategy**:
  - `scripts/download_datasets.py` attempts automated download from authenticated/public mirrors or Kaggle/Zenodo/GitHub releases.
  - If external network mirrors require manual authentication or are unavailable, a high-fidelity deterministic generator/parser creates an exact structural replica/demo subset with verified checksums.

### B. Network-Layer Telemetry: Synthetic P2P Metadata Generator
- **Authenticity Disclaimer**: Real public AML datasets (including Elliptic) do NOT provide intercepted Bitcoin P2P IP addresses due to privacy and network anonymity limitations.
- **Explicit Labeling**: All generated network records are explicitly tagged as `"Synthetic network-layer metadata generated for system integration and demonstration"`.
- **Implementation (`scripts/generate_network_data.py`)**:
  - Deterministic PRNG seed for exact reproducibility.
  - Generates 10 realistic cybersecurity scenarios:
    1. Standard Bitcoin P2P transaction propagation (normal gossip protocol).
    2. High-frequency rapid connection bursts.
    3. Repeated connection attempts from single or clustered IPs.
    4. Multi-IP association per transaction (relayed nodes).
    5. Geographic hopping & routing anomalies.
    6. Autonomous System Number (ASN) concentration (e.g. bulletproof hosting / VPN exit nodes).
    7. Rapid fund movement / velocity spikes.
    8. Transaction burst behavior.
    9. Suspicious timing and microsecond intervals.
    10. Layering / peel-chain network signatures.

### C. Enrichment Layer: GeoIP & Autonomous System Resolution
- **Module (`src/enrichment/geoip.py`)**:
  - Resolves IP -> Country, Continent, ASN, Organization.
  - Local offline lookup table with MaxMind GeoLite2 fallback.
  - Gracefully handles RFC 1918 private IPs, loopback, multicast, IPv6, and malformed strings.
  - In-memory LRU cache for sub-millisecond query performance.

---

## 3. Canonical Storage Model (DuckDB)
All ingested blockchain, network, and enriched records are normalized and loaded into `data/bitcoin.duckdb`:
- `transactions`: Core blockchain records (txid, timestamp, timestep, inputs, outputs, fee, volume, label, is_synthetic).
- `addresses`: Wallet and address entities with balance, first/last seen, risk score.
- `network_events`: P2P connection telemetry linked via `txid`.
- `entities`: Unified entity resolution registry (Transaction, Wallet, IP, ASN, Country).
- `edges`: Graph relations (INPUT_TO, OUTPUT_TO, CONNECTED_TO, OBSERVED_FROM, BELONGS_TO, FOLLOWS).
- `features`: Full engineered multi-modal feature vectors.
- `model_predictions`: Supervised & anomaly model inference results.
- `alerts`: Prioritized investigation alerts with evidence payloads and risk levels.

---

## 4. Anti-Leakage Temporal Split Plan
To replicate real-world operational conditions and avoid temporal leakage:
- **Train Split**: Timesteps 1 to 34 (~70% temporal progression)
- **Validation Split**: Timesteps 35 to 41 (~15% temporal progression)
- **Test Split**: Timesteps 42 to 49 (~15% latest evaluation horizon)
- **Baseline Comparison**: Stratified random split is also evaluated to quantify the exact optimistic bias of data leakage.
