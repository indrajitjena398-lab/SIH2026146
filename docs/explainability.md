# Explainable AI & Human-Readable Evidence Synthesis

## 1. TreeSHAP Local Attributions
For every flagged transaction, TreeSHAP computes exact Shapley marginal feature contributions:

$$\phi_i(x) = \sum_{S \subseteq F \setminus \{i\}} \frac{|S|!(|F| - |S| - 1)!}{|F|!} \left( f(S \cup \{i\}) - f(S) \right)$$

Features with large positive $\phi_i(x)$ indicate specific drivers pushing the transaction into the suspicious tier.

---

## 2. Evidence Translation Rules
Top SHAP values are dynamically translated into investigator-accessible rationales:
- High `tx_fan_out_ratio` $\to$ "Severe peel-chain distribution pattern (fan-out: X, fan-in: Y)."
- High `net_high_risk_asn_flag` $\to$ "P2P node broadcast routed through high-risk bulletproof ASN."
- High `graph_neighbor_illicit_ratio` $\to$ "Directly connected to X% known illicit counterparties in 1-hop neighborhood."
