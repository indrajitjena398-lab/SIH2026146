# Dataset Documentation — Bitcoin Transaction & Network Telemetry

## 1. Primary Dataset: Elliptic Bitcoin Dataset
The primary dataset used for supervised learning and graph analytics is the **Elliptic Bitcoin Dataset** (Weber et al., 2019).

### Structure:
- `elliptic_txs_features.csv`: 203,769 transactions across 49 distinct timesteps (each ~2-week block interval).
  - First 93 features: Local transaction properties (in/out degree, transacted volume, fee, average fee/output).
  - Remaining 72 features: 1-hop aggregate neighbor properties (mean, std, min, max).
- `elliptic_txs_classes.csv`:
  - `1`: Illicit (ransomware, darknet, scams, mixers) (~2.2%)
  - `2`: Licit (exchanges, miners, wallet services) (~20.6%)
  - `unknown`: Unlabeled transactions (~77.2%)
- `elliptic_txs_edgelist.csv`: 234,355 directed edges representing transaction flow (`txId1` -> `txId2`).

---

## 2. Synthetic Network Telemetry Layer
### Explicit Disclaimer:
> **Synthetic network-layer metadata generated for system integration and demonstration.**
> Public Bitcoin AML datasets do not provide intercepted P2P IP metadata. All IP, port, packet, and ASN telemetry is deterministically generated to model real-world investigative workflows without fabricating real P2P interception.

### Generated Scenarios:
1. `normal_propagation`: Standard gossip broadcast on port 8333.
2. `high_frequency`: Sub-second clustered relays.
3. `repeated_connections`: Repeated announcements from single IPs.
4. `multi_ip_association`: Relayed across 10+ distinct node IPs.
5. `geographic_anomaly`: Transcontinental hops within milliseconds.
6. `asn_concentration`: Clustered in bulletproof / VPN ASNs.
7. `rapid_movement`: High byte payloads with ultra-short connection durations.
8. `burst_behavior`: Massive packet surges.
9. `suspicious_timing`: Off-hour micro-burst intervals.
10. `layering_pattern`: Peel chain sequence of interconnected hops.

---

## 3. GeoIP & ASN Resolution
The platform uses an offline GeoIP resolution table (`src/enrichment/geoip.py`) that maps IP addresses to Country, Continent, Region, ASN, and Organization with RFC 1918 private IP detection and caching.
