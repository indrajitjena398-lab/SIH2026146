"""
Comprehensive Model Evaluation & Metric Engine.
Computes Accuracy, Precision, Recall, Specificity, FPR, FNR, F1, Balanced Accuracy,
MCC, Cohen's Kappa, ROC-AUC, PR-AUC, Confusion Matrix, and Threshold Sweeps.
"""

import logging
from typing import Dict, List, Any, Tuple
import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    balanced_accuracy_score, matthews_corrcoef, cohen_kappa_score,
    roc_auc_score, precision_recall_curve, auc, roc_curve, confusion_matrix
)

logger = logging.getLogger(__name__)

class ModelEvaluator:
    """Evaluates classification models with cyber-investigation focused metrics."""

    @staticmethod
    def evaluate_predictions(
        y_true: np.ndarray,
        y_prob: np.ndarray,
        threshold: float = 0.5
    ) -> Dict[str, Any]:
        """Calculates all key metrics at a given classification threshold."""
        y_pred = (y_prob >= threshold).astype(int)

        # Confusion Matrix elements
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

        # Rates
        accuracy = float(accuracy_score(y_true, y_pred))
        precision = float(precision_score(y_true, y_pred, zero_division=0))
        recall = float(recall_score(y_true, y_pred, zero_division=0))
        specificity = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
        fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
        fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0
        f1 = float(f1_score(y_true, y_pred, zero_division=0))
        balanced_acc = float(balanced_accuracy_score(y_true, y_pred))
        mcc = float(matthews_corrcoef(y_true, y_pred))
        kappa = float(cohen_kappa_score(y_true, y_pred))

        # Curve AUCs
        try:
            roc_auc = float(roc_auc_score(y_true, y_prob))
        except Exception:
            roc_auc = 0.5

        try:
            prec_arr, rec_arr, _ = precision_recall_curve(y_true, y_prob)
            pr_auc = float(auc(rec_arr, prec_arr))
        except Exception:
            pr_auc = 0.0

        return {
            "threshold": threshold,
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "specificity": round(specificity, 4),
            "fpr": round(fpr, 4),
            "fnr": round(fnr, 4),
            "f1": round(f1, 4),
            "balanced_accuracy": round(balanced_acc, 4),
            "mcc": round(mcc, 4),
            "cohen_kappa": round(kappa, 4),
            "roc_auc": round(roc_auc, 4),
            "pr_auc": round(pr_auc, 4),
            "confusion_matrix": {
                "tp": int(tp),
                "fp": int(fp),
                "tn": int(tn),
                "fn": int(fn)
            }
        }

    @staticmethod
    def threshold_sweep(
        y_true: np.ndarray,
        y_prob: np.ndarray,
        thresholds: List[float] = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    ) -> List[Dict[str, Any]]:
        """Calculates metric trade-offs across a sweep of candidate operating thresholds."""
        sweep_results = []
        for th in thresholds:
            metrics = ModelEvaluator.evaluate_predictions(y_true, y_prob, threshold=th)
            sweep_results.append(metrics)
        return sweep_results

    @staticmethod
    def compute_curves(y_true: np.ndarray, y_prob: np.ndarray) -> Dict[str, Any]:
        """Calculates ROC and Precision-Recall curve coordinate points for plotting."""
        fpr, tpr, _ = roc_curve(y_true, y_prob)
        precision, recall, _ = precision_recall_curve(y_true, y_prob)

        # Downsample points for efficient JSON serialization
        step_roc = max(1, len(fpr) // 50)
        step_pr = max(1, len(precision) // 50)

        roc_points = [{"fpr": round(float(fpr[i]), 4), "tpr": round(float(tpr[i]), 4)} for i in range(0, len(fpr), step_roc)]
        pr_points = [{"recall": round(float(recall[i]), 4), "precision": round(float(precision[i]), 4)} for i in range(0, len(precision), step_pr)]

        return {
            "roc_curve": roc_points,
            "pr_curve": pr_points
        }
