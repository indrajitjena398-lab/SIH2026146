"""
Entities API Router.
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Path
from backend.database import db_manager
from backend.schemas.common import EntityDetail

router = APIRouter(prefix="/entities", tags=["Entities"])

@router.get("/{entity_id}", response_model=EntityDetail)
def get_entity(entity_id: str = Path(...)):
    con = db_manager.get_connection()
    try:
        # Search entity table
        row = con.execute("SELECT * FROM entities WHERE entity_id = ? LIMIT 1", [entity_id]).fetchone()
        if not row:
            # Fallback check if it is a transaction
            tx_row = con.execute("SELECT txid, label FROM transactions WHERE txid = ? LIMIT 1", [entity_id]).fetchone()
            if tx_row:
                row = (tx_row[0], "Transaction", tx_row[1], 80.0 if tx_row[1] == "illicit" else 20.0)
            else:
                raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found")

        cols = [desc[0] for desc in con.description]
        e_dict = dict(zip(cols, row))

        eid = str(e_dict.get("entity_id", entity_id))
        etype = str(e_dict.get("entity_type", "Unknown"))
        risk = float(e_dict.get("risk_score", 20.0))

        # Query connections from edges
        node_id_patterns = [eid, f"tx_{eid}", f"wallet_{eid}", f"ip_{eid}", f"asn_{eid}"]
        placeholders = ",".join(["?"] * len(node_id_patterns))
        
        in_edges = con.execute(f"SELECT source_id, relation FROM edges WHERE target_id IN ({placeholders})", node_id_patterns).fetchall()
        out_edges = con.execute(f"SELECT target_id, relation FROM edges WHERE source_id IN ({placeholders})", node_id_patterns).fetchall()

        connected_txs = []
        associated_ips = []
        associated_asns = []

        for src, rel in in_edges:
            if src.startswith("tx_"):
                connected_txs.append(src[3:])
            elif src.startswith("ip_"):
                associated_ips.append(src[3:])
            elif src.startswith("asn_"):
                associated_asns.append(src[4:])

        for dst, rel in out_edges:
            if dst.startswith("tx_"):
                connected_txs.append(dst[3:])
            elif dst.startswith("ip_"):
                associated_ips.append(dst[3:])
            elif dst.startswith("asn_"):
                associated_asns.append(dst[4:])

        risk_level = "Critical" if risk >= 75 else ("High" if risk >= 50 else ("Medium" if risk >= 25 else "Low"))

        return {
            "entity_id": eid,
            "entity_type": etype,
            "label": str(e_dict.get("label", "unknown")),
            "risk_score": risk,
            "risk_level": risk_level,
            "degree": len(in_edges) + len(out_edges),
            "in_degree": len(in_edges),
            "out_degree": len(out_edges),
            "connected_transactions": list(set(connected_txs))[:20],
            "associated_ips": list(set(associated_ips))[:20],
            "associated_asns": list(set(associated_asns))[:20]
        }
    finally:
        con.close()
