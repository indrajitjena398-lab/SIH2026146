"""
Global Multi-Entity Search API Router.
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from backend.database import db_manager
from backend.schemas.common import SearchResultItem

router = APIRouter(prefix="/search", tags=["Search"])

@router.get("", response_model=List[SearchResultItem])
def search_entities(q: str = Query(..., min_length=1, description="Search query")):
    query_term = f"%{q.strip().lower()}%"
    results = []
    con = db_manager.get_connection()
    try:
        # 1. Search Alerts
        alert_rows = con.execute("""
            SELECT alert_id, transaction_id, risk_score, risk_level, top_reason
            FROM alerts
            WHERE LOWER(alert_id) LIKE ? OR LOWER(transaction_id) LIKE ?
            LIMIT 10
        """, [query_term, query_term]).fetchall()

        for aid, txid, score, level, reason in alert_rows:
            results.append({
                "id": aid,
                "type": "Alert",
                "title": f"Alert: {aid}",
                "subtitle": f"TX: {txid} — {reason[:45]}...",
                "risk_score": float(score),
                "risk_level": level
            })

        # 2. Search Transactions
        tx_rows = con.execute("""
            SELECT txid, time_step, label
            FROM transactions
            WHERE LOWER(txid) LIKE ?
            LIMIT 10
        """, [query_term]).fetchall()

        for txid, ts, label in tx_rows:
            is_ill = label == "illicit"
            results.append({
                "id": txid,
                "type": "Transaction",
                "title": f"TX: {txid}",
                "subtitle": f"TimeStep {ts} | Label: {label.upper()}",
                "risk_score": 90.0 if is_ill else (15.0 if label == "licit" else 35.0),
                "risk_level": "Critical" if is_ill else "Low"
            })

        # 3. Search Entities (Wallets, IPs, ASNs)
        ent_rows = con.execute("""
            SELECT entity_id, entity_type, label, risk_score
            FROM entities
            WHERE LOWER(entity_id) LIKE ?
            LIMIT 10
        """, [query_term]).fetchall()

        for eid, etype, label, score in ent_rows:
            if not any(r["id"] == eid for r in results):
                level = "Critical" if score >= 75 else ("High" if score >= 50 else ("Medium" if score >= 25 else "Low"))
                results.append({
                    "id": eid,
                    "type": etype,
                    "title": f"{etype}: {eid}",
                    "subtitle": f"Classification: {label}",
                    "risk_score": float(score),
                    "risk_level": level
                })

        return results[:25]
    finally:
        con.close()
