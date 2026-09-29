"""
Transactions API Router.
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Path
from backend.database import db_manager
from backend.services.ml_service import MLService
from backend.schemas.common import TransactionDetail

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.get("/{txid}", response_model=TransactionDetail)
def get_transaction(txid: str = Path(...)):
    con = db_manager.get_connection()
    try:
        # Fetch transaction
        row = con.execute("SELECT * FROM transactions WHERE txid = ? LIMIT 1", [txid]).fetchone()
        if not row:
            # Check if this txid is an alert_id
            alert_match = con.execute("SELECT transaction_id FROM alerts WHERE alert_id = ? LIMIT 1", [txid]).fetchone()
            if alert_match and alert_match[0]:
                txid = alert_match[0]
                row = con.execute("SELECT * FROM transactions WHERE txid = ? LIMIT 1", [txid]).fetchone()
            elif txid.startswith("ALERT-") or txid.startswith("ALT-"):
                clean_id = txid.split("-", 1)[1]
                row = con.execute("SELECT * FROM transactions WHERE txid = ? LIMIT 1", [clean_id]).fetchone()
                if row:
                    txid = clean_id
        if not row:
            raise HTTPException(status_code=404, detail=f"Transaction '{txid}' not found")

        tx_cols = [desc[0] for desc in con.description]
        tx_data = dict(zip(tx_cols, row))

        # Predictions
        pred_row = con.execute("SELECT * FROM model_predictions WHERE txid = ? LIMIT 1", [txid]).fetchone()
        if pred_row:
            p_cols = [desc[0] for desc in con.description]
            p_dict = dict(zip(p_cols, pred_row))
            prob_illicit = p_dict.get("prob_illicit", 0.0)
            anomaly_score = p_dict.get("anomaly_score", 0.0)
        else:
            prob_illicit = 0.85 if tx_data.get("label") == "illicit" else 0.15
            anomaly_score = 0.2

        # Alert if present
        alert_row = con.execute("SELECT * FROM alerts WHERE transaction_id = ? LIMIT 1", [txid]).fetchone()
        if alert_row:
            a_cols = [desc[0] for desc in con.description]
            a_dict = dict(zip(a_cols, alert_row))
            risk_score = a_dict.get("risk_score", 30.0)
            risk_level = a_dict.get("risk_level", "Low")
        else:
            risk_score = 85.0 if tx_data.get("label") == "illicit" else 15.0
            risk_level = "Critical" if risk_score >= 75 else ("High" if risk_score >= 50 else ("Medium" if risk_score >= 25 else "Low"))

        # Network events
        net_rows = con.execute("SELECT * FROM network_events WHERE txid = ?", [txid]).fetchall()
        net_cols = [desc[0] for desc in con.description]
        net_events = [dict(zip(net_cols, nr)) for nr in net_rows]

        # On-demand SHAP explanation
        pred_res = MLService.predict_custom_transaction({
            "txid": txid,
            "input_amount": tx_data.get("input_amount", 1.0),
            "output_amount": tx_data.get("output_amount", 1.0),
            "fee": tx_data.get("fee", 0.0001),
            "input_count": tx_data.get("input_count", 1),
            "output_count": tx_data.get("output_count", 2)
        })

        return {
            "txid": txid,
            "time_step": int(tx_data.get("time_step", 1)),
            "timestamp": str(tx_data.get("timestamp", "2025-01-01T00:00:00Z")),
            "label": str(tx_data.get("label", "unknown")),
            "is_illicit": int(tx_data.get("is_illicit", 0)),
            "input_amount": float(tx_data.get("input_amount", 1.0)),
            "output_amount": float(tx_data.get("output_amount", 1.0)),
            "fee": float(tx_data.get("fee", 0.0001)),
            "input_count": int(tx_data.get("input_count", 1)),
            "output_count": int(tx_data.get("output_count", 2)),
            "is_synthetic": bool(tx_data.get("is_synthetic", False)),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "prob_illicit": prob_illicit,
            "anomaly_score": anomaly_score,
            "network_events": net_events,
            "shap_contributions": pred_res.get("shap_contributions", []),
            "reasons": pred_res.get("reasons", [])
        }
    finally:
        con.close()
