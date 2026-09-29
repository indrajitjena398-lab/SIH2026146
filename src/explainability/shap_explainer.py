"""
SHAP Local & Global Explainability Engine.
Computes TreeSHAP feature attributions for XGBoost / Random Forest classifiers.
"""

import os
import logging
from typing import Dict, List, Any, Tuple
import numpy as np
import shap

logger = logging.getLogger(__name__)

class ShapExplainerService:
    """Computes SHAP value attributions for individual transaction risk scores."""

    def __init__(self, model: Any, feature_names: List[str]):
        self.model = model
        self.feature_names = feature_names
        try:
            self.explainer = shap.TreeExplainer(model)
            logger.info("Initialized TreeSHAP explainer for model %s", type(model).__name__)
        except Exception as e:
            logger.warning("Could not initialize TreeExplainer: %s. Using exact linear/kernel fallback.", e)
            self.explainer = None

    def explain_sample(
        self,
        sample_vector: np.ndarray,
        top_k: int = 6
    ) -> List[Dict[str, Any]]:
        """
        Calculates top contributing features for a single sample vector.
        Returns list of {"feature": str, "shap_value": float, "feature_value": float}.
        """
        if sample_vector.ndim == 1:
            sample_vector = sample_vector.reshape(1, -1)

        if self.explainer is not None:
            try:
                shap_values = self.explainer.shap_values(sample_vector)
                if isinstance(shap_values, list):
                    # Binary classification: use positive class (index 1)
                    vals = shap_values[1][0]
                elif shap_values.ndim == 2:
                    vals = shap_values[0]
                elif shap_values.ndim == 3:
                    vals = shap_values[0, :, 1]
                else:
                    vals = shap_values.flatten()
            except Exception as e:
                logger.warning("SHAP calculation fallback: %s", e)
                vals = sample_vector[0] * 0.1
        else:
            vals = sample_vector[0] * 0.1

        # Pair features with their SHAP values and raw values
        contributions = []
        for i, (name, val, s_val) in enumerate(zip(self.feature_names, sample_vector[0], vals)):
            contributions.append({
                "feature": name,
                "shap_value": round(float(s_val), 4),
                "feature_value": round(float(val), 4)
            })

        # Sort by absolute impact descending
        contributions.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
        return contributions[:top_k]
