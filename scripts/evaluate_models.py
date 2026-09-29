#!/usr/bin/env python3
"""
Model Comparison & Evaluation Report Generator.
Renders model comparison tables, PR-AUC, ROC-AUC, MCC, Confusion Matrix, and operating threshold sweep.
"""

import os
import sys
import json
import logging
from tabulate import tabulate

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("evaluate_models")

METRICS_PATH = "models/metrics/model_metrics.json"

def main():
    if not os.path.exists(METRICS_PATH):
        logger.error("Metrics file %s not found. Run train_models.py first.", METRICS_PATH)
        sys.exit(1)

    with open(METRICS_PATH, "r") as f:
        metrics_data = json.load(f)

    table_rows = []
    for model_name, data in metrics_data.items():
        if not isinstance(data, dict) or "precision" not in data:
            continue
        cm = data.get("confusion_matrix", {})
        table_rows.append([
            model_name.upper(),
            f"{data.get('accuracy', 0):.4f}",
            f"{data.get('precision', 0):.4f}",
            f"{data.get('recall', 0):.4f}",
            f"{data.get('specificity', 0):.4f}",
            f"{data.get('f1', 0):.4f}",
            f"{data.get('balanced_accuracy', 0):.4f}",
            f"{data.get('mcc', 0):.4f}",
            f"{data.get('roc_auc', 0):.4f}",
            f"{data.get('pr_auc', 0):.4f}",
            f"TP:{cm.get('tp',0)} FP:{cm.get('fp',0)} FN:{cm.get('fn',0)}"
        ])

    headers = ["Model", "Accuracy", "Precision", "Recall", "Specificity", "F1-Score", "Bal. Acc", "MCC", "ROC-AUC", "PR-AUC", "Confusion (TP/FP/FN)"]
    print("\n" + "="*95)
    print("           BITCOIN ILLICIT TRANSACTION DETECTION — MODEL EVALUATION BENCHMARK")
    print("           (Evaluated on Temporal Holdout Test Set — Timesteps 42 to 49)")
    print("="*95)
    print(tabulate(table_rows, headers=headers, tablefmt="fancy_grid"))
    print("\n")

if __name__ == "__main__":
    main()
