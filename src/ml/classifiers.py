"""
Supervised Classification Suite for Illicit Transaction Detection.
Includes Logistic Regression, Random Forest, Extra Trees, LightGBM, and XGBoost with class-imbalance weighting.
"""

import logging
from typing import Dict, Any, Optional
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
import xgboost as xgb
import lightgbm as lgb

logger = logging.getLogger(__name__)

class ModelTrainer:
    """Trains and manages supervised classifiers."""

    @staticmethod
    def get_models(scale_pos_weight: float = 10.0, random_state: int = 42) -> Dict[str, Any]:
        """Returns initialized supervised classifiers."""
        models = {
            "logistic_regression": LogisticRegression(
                max_iter=1000,
                class_weight="balanced",
                random_state=random_state,
                solver="lbfgs"
            ),
            "random_forest": RandomForestClassifier(
                n_estimators=200,
                max_depth=12,
                class_weight="balanced",
                random_state=random_state,
                n_jobs=-1
            ),
            "extra_trees": ExtraTreesClassifier(
                n_estimators=200,
                max_depth=12,
                class_weight="balanced",
                random_state=random_state,
                n_jobs=-1
            ),
            "lightgbm": lgb.LGBMClassifier(
                n_estimators=250,
                max_depth=8,
                learning_rate=0.05,
                objective="binary",
                class_weight="balanced",
                random_state=random_state,
                n_jobs=-1,
                subsample=0.9,
                colsample_bytree=0.9,
                is_unbalance=True
            ),
            "xgboost": xgb.XGBClassifier(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.08,
                scale_pos_weight=scale_pos_weight,
                random_state=random_state,
                eval_metric="logloss",
                n_jobs=-1
            )
        }
        return models

    @staticmethod
    def train_model(model: Any, X_train: np.ndarray, y_train: np.ndarray) -> Any:
        """Fits a model on training data."""
        model.fit(X_train, y_train)
        return model
