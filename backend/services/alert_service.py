"""
Alert Service.
Fetches, filters, and paginates alert records and detail dossiers from DuckDB.
"""

import json
import ast
import logging
from typing import Dict, List, Any, Optional, Tuple
from backend.database import db_manager
from backend.services.graph_service import GraphService
from backend.services.patterns import evaluate_all_patterns

logger = logging.getLogger(__name__)

class AlertService:
    """Provides alert data querying and status updates."""

    @staticmethod
    def _patterns_for_transaction(con, transaction_id: str) -> List[Dict[str, Any]]:
        row = con.execute("SELECT * FROM transactions WHERE txid = ? LIMIT 1", [transaction_id]).fetchone()
        if not row:
            return []
        columns = [description[0] for description in con.description]
        record = dict(zip(columns, row))
        network = con.execute("SELECT src_ip FROM network_events WHERE txid = ? LIMIT 1", [transaction_id]).fetchone()
        if network:
            record["src_ip"] = network[0]
        return evaluate_all_patterns(record, GraphService.get_graph())

    @staticmethod
    def get_alerts(
        limit: int = 50,
        offset: int = 0,
        risk_level: Optional[str] = None,
        entity_type: Optional[str] = None,
        min_score: Optional[float] = None,
        search: Optional[str] = None,
        sort_by: str = "risk_score",
        sort_order: str = "desc"
    ) -> Tuple[List[Dict[str, Any]], int]:
        con = db_manager.get_connection()
        try:
            where_clauses = ["1=1"]
            params = []

            if risk_level and risk_level.lower() != "all":
                where_clauses.append("LOWER(risk_level) = ?")
                params.append(risk_level.lower())

            if entity_type and entity_type.lower() != "all":
                where_clauses.append("LOWER(entity_type) = ?")
                params.append(entity_type.lower())

            if min_score is not None:
                where_clauses.append("risk_score >= ?")
                params.append(min_score)

            if search:
                where_clauses.append("(LOWER(alert_id) LIKE ? OR LOWER(transaction_id) LIKE ? OR LOWER(entity_id) LIKE ? OR LOWER(top_reason) LIKE ?)")
                term = f"%{search.lower()}%"
                params.extend([term, term, term, term])

            where_str = " AND ".join(where_clauses)
            
            # Count total matching
            count_query = f"SELECT COUNT(*) FROM alerts WHERE {where_str}"
            total_count = con.execute(count_query, params).fetchone()[0]

            # Validate sort column to prevent SQL injection
            allowed_sorts = {"risk_score", "timestamp", "classification_probability", "anomaly_score", "alert_id"}
            sort_col = sort_by if sort_by in allowed_sorts else "risk_score"
            order_str = "ASC" if sort_order.lower() == "asc" else "DESC"

            query = f"""
                SELECT alert_id, entity_id, entity_type, transaction_id, risk_score, risk_level,
                       classification_probability, anomaly_score, top_reason, status, timestamp, model_version
                FROM alerts
                WHERE {where_str}
                ORDER BY {sort_col} {order_str}
                LIMIT ? OFFSET ?
            """
            rows = con.execute(query, params + [limit, offset]).fetchall()
            cols = [
                "alert_id", "entity_id", "entity_type", "transaction_id", "risk_score", "risk_level",
                "classification_probability", "anomaly_score", "top_reason", "status", "timestamp", "model_version"
            ]
            items = [dict(zip(cols, r)) for r in rows]
            for item in items:
                item["patterns"] = AlertService._patterns_for_transaction(con, item["transaction_id"])
            return items, total_count
        finally:
            con.close()

    @staticmethod
    def get_alert_detail(alert_id: str) -> Optional[Dict[str, Any]]:
        con = db_manager.get_connection()
        try:
            query = "SELECT * FROM alerts WHERE alert_id = ? OR transaction_id = ? LIMIT 1"
            row = con.execute(query, [alert_id, alert_id]).fetchone()
            if not row:
                return None

            cols = [desc[0] for desc in con.description]
            item = dict(zip(cols, row))

            # Parse JSON fields safely
            try:
                top_reasons = ast.literal_eval(item.get("top_reasons_json", "[]"))
            except Exception:
                top_reasons = [item.get("top_reason", "")]

            try:
                evidence = ast.literal_eval(item.get("evidence_json", "{}"))
            except Exception:
                evidence = {}

            item["top_reasons"] = top_reasons
            item["evidence"] = evidence
            item["shap_contributions"] = evidence.get("shap", [])

            # Transaction details
            txid = item.get("transaction_id")
            tx_row = con.execute("SELECT * FROM transactions WHERE txid = ? LIMIT 1", [txid]).fetchone()
            if tx_row:
                tx_cols = [desc[0] for desc in con.description]
                item["transaction_details"] = dict(zip(tx_cols, tx_row))

            # Network details
            net_rows = con.execute("SELECT * FROM network_events WHERE txid = ?", [txid]).fetchall()
            if net_rows:
                net_cols = [desc[0] for desc in con.description]
                item["network_details"] = [dict(zip(net_cols, nr)) for nr in net_rows]

            item["patterns"] = AlertService._patterns_for_transaction(con, txid)

            return item
        finally:
            con.close()

    @staticmethod
    def update_alert_status(alert_id: str, status: str) -> bool:
        con = db_manager.get_connection()
        try:
            con.execute("UPDATE alerts SET status = ? WHERE alert_id = ?", [status, alert_id])
            return True
        finally:
            con.close()

    @staticmethod
    def get_statistics() -> Dict[str, Any]:
        con = db_manager.get_connection()
        try:
            total_tx = con.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
            total_entities = con.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
            total_edges = con.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
            total_alerts = con.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
            
            crit = con.execute("SELECT COUNT(*) FROM alerts WHERE risk_score >= 75").fetchone()[0]
            high = con.execute("SELECT COUNT(*) FROM alerts WHERE risk_score >= 50 AND risk_score < 75").fetchone()[0]
            med = con.execute("SELECT COUNT(*) FROM alerts WHERE risk_score >= 25 AND risk_score < 50").fetchone()[0]
            low = max(0, total_tx - (crit + high + med))
            
            avg_risk = con.execute("SELECT COALESCE(AVG(risk_score), 0) FROM alerts").fetchone()[0]
            
            top_entities = con.execute("SELECT alert_id, entity_id, entity_type, transaction_id, risk_score, risk_level, top_reason FROM alerts ORDER BY risk_score DESC LIMIT 10").fetchall()
            top_cols = ["alert_id", "entity_id", "entity_type", "transaction_id", "risk_score", "risk_level", "top_reason"]
            top_risk_entities = [dict(zip(top_cols, r)) for r in top_entities]
            
            # Activity over time
            act_rows = con.execute("""
                SELECT t.time_step, COUNT(t.txid) as tx_count, COUNT(a.alert_id) as alert_count
                FROM transactions t
                LEFT JOIN alerts a ON t.txid = a.transaction_id
                GROUP BY t.time_step
                ORDER BY t.time_step ASC
            """).fetchall()
            activity_over_time = [{"time_step": r[0], "tx_count": r[1], "alert_count": r[2]} for r in act_rows]

            risk_distribution = [
                {"name": "Critical (>=75)", "value": crit},
                {"name": "High (50-74)", "value": high},
                {"name": "Medium (25-49)", "value": med},
                {"name": "Low (0-24)", "value": low}
            ]

            return {
                "total_transactions": total_tx,
                "total_entities": total_entities,
                "total_edges": total_edges,
                "total_alerts": total_alerts,
                "critical_alerts": crit,
                "high_alerts": high,
                "medium_alerts": med,
                "low_alerts": low,
                "average_risk_score": round(float(avg_risk), 2),
                "top_risk_entities": top_risk_entities,
                "activity_over_time": activity_over_time,
                "risk_distribution": risk_distribution
            }
        finally:
            con.close()
