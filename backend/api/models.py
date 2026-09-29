"""
Machine Learning Models & Metrics API Router.
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Body
from backend.services.ml_service import MLService
from backend.schemas.common import PredictRequest

router = APIRouter(prefix="/models", tags=["Models"])

@router.get("")
def list_models():
    metrics_data = MLService.get_metrics()
    return {
        "active_model": metrics_data.get("metadata", {}).get("best_model", "XGBoost"),
        "models": metrics_data.get("metadata", {}).get("models_evaluated", []),
        "metadata": metrics_data.get("metadata", {})
    }

@router.get("/metrics")
def get_model_metrics():
    return MLService.get_metrics()

@router.post("/predict")
def predict_transaction(request: PredictRequest):
    result = MLService.predict_custom_transaction(request.model_dump())
    return result
