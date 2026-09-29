# Machine Learning & Risk Methodology

## 1. Temporal Anti-Leakage Partitioning
Bitcoin transactions are strictly chronological. Mixing future transactions into training sets introduces severe optimistic lookahead bias.

- **Training Split**: Timesteps 1 to 34 (~70% temporal progression)
- **Validation Split**: Timesteps 35 to 41 (~15% temporal progression)
- **Test Holdout Split**: Timesteps 42 to 49 (~15% latest evaluation horizon)

### Leakage Comparison Experiment:
When evaluated on a stratified random split, models report artificially inflated F1-scores due to topological neighbor leakage. Temporal splitting reflects true operational performance.

---

## 2. Supervised & Anomaly Detection Ensembles
1. **Logistic Regression**: Linear baseline with balanced class weighting.
2. **Random Forest Classifier**: Non-linear ensemble with 100 estimators.
3. **Extra Trees Classifier**: Extremely randomized tree ensemble.
4. **XGBoost Classifier**: Gradient boosted decision trees optimized with `scale_pos_weight` for class imbalance.
5. **Isolation Forest**: Unsupervised tree-based anomaly isolation for catching novel, unlabeled threat signatures.

---

## 3. Multi-Factor Risk Fusion Formula
Composite risk is scored on a calibrated 0–100 scale:

$$\text{Risk Score} = 100 \times \left( 0.40 \cdot P(\text{illicit}) + 0.20 \cdot S_{\text{anomaly}} + 0.20 \cdot R_{\text{graph}} + 0.10 \cdot R_{\text{behavior}} + 0.10 \cdot R_{\text{network}} \right)$$

- **Low**: $0 \le \text{Score} < 25$
- **Medium**: $25 \le \text{Score} < 50$
- **High**: $50 \le \text{Score} < 75$
- **Critical**: $75 \le \text{Score} \le 100$
