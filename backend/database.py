"""
DuckDB Database Access Layer.
Manages analytical storage, query optimization, and thread-safe connections to data/bitcoin.duckdb.
"""

import os
import logging
import duckdb
import pandas as pd
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

DB_PATH = "data/bitcoin.duckdb"

class DatabaseManager:
    """Manages local embedded DuckDB analytical database."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_tables()

    def get_connection(self) -> duckdb.DuckDBPyConnection:
        """Returns a DuckDB connection."""
        return duckdb.connect(self.db_path)

    def _init_tables(self):
        """Creates DuckDB tables and schema if they don't exist."""
        con = self.get_connection()
        try:
            # 1. Transactions
            con.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    txid VARCHAR PRIMARY KEY,
                    time_step INTEGER,
                    timestamp VARCHAR,
                    label VARCHAR,
                    is_illicit INTEGER,
                    is_labeled INTEGER,
                    input_amount DOUBLE,
                    output_amount DOUBLE,
                    fee DOUBLE,
                    input_count INTEGER,
                    output_count INTEGER,
                    is_synthetic BOOLEAN
                )
            """)

            # 2. Network Events
            con.execute("""
                CREATE TABLE IF NOT EXISTS network_events (
                    event_id VARCHAR PRIMARY KEY,
                    txid VARCHAR,
                    timestamp VARCHAR,
                    src_ip VARCHAR,
                    dst_ip VARCHAR,
                    src_port INTEGER,
                    dst_port INTEGER,
                    connection_duration DOUBLE,
                    packet_count INTEGER,
                    bytes_in BIGINT,
                    bytes_out BIGINT,
                    geo_country VARCHAR,
                    geo_continent VARCHAR,
                    geo_region VARCHAR,
                    asn VARCHAR,
                    asn_org VARCHAR,
                    scenario VARCHAR,
                    is_synthetic BOOLEAN,
                    disclaimer VARCHAR
                )
            """)

            # 3. Edges
            con.execute("""
                CREATE TABLE IF NOT EXISTS edges (
                    source_id VARCHAR,
                    target_id VARCHAR,
                    relation VARCHAR,
                    weight DOUBLE
                )
            """)

            # 4. Entities
            con.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    entity_id VARCHAR,
                    entity_type VARCHAR,
                    label VARCHAR,
                    risk_score DOUBLE
                )
            """)

            # 5. Alerts
            con.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    alert_id VARCHAR PRIMARY KEY,
                    entity_id VARCHAR,
                    entity_type VARCHAR,
                    transaction_id VARCHAR,
                    risk_score DOUBLE,
                    risk_level VARCHAR,
                    classification_probability DOUBLE,
                    anomaly_score DOUBLE,
                    top_reason VARCHAR,
                    top_reasons_json VARCHAR,
                    evidence_json VARCHAR,
                    status VARCHAR,
                    timestamp VARCHAR,
                    model_version VARCHAR
                )
            """)

            # 6. Model Predictions
            con.execute("""
                CREATE TABLE IF NOT EXISTS model_predictions (
                    txid VARCHAR PRIMARY KEY,
                    time_step INTEGER,
                    label VARCHAR,
                    is_illicit INTEGER,
                    prob_illicit DOUBLE,
                    anomaly_score DOUBLE,
                    graph_risk DOUBLE,
                    behavior_risk DOUBLE,
                    network_risk DOUBLE
                )
            """)

            # Populate tables from processed parquet files if tables are empty
            self._seed_from_parquet(con)

        finally:
            con.close()

    def _seed_from_parquet(self, con: duckdb.DuckDBPyConnection):
        """Loads parquet data files into DuckDB tables if empty."""
        tx_count = con.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        if tx_count == 0:
            tx_parquet = "data/processed/canonical_transactions.parquet"
            if os.path.exists(tx_parquet):
                logger.info("Populating DuckDB transactions from %s...", tx_parquet)
                df_tx = pd.read_parquet(tx_parquet)
                cols_to_insert = [
                    "txid", "time_step", "timestamp", "label", "is_illicit", "is_labeled",
                    "input_amount", "output_amount", "fee", "input_count", "output_count", "is_synthetic"
                ]
                for c in cols_to_insert:
                    if c not in df_tx.columns:
                        if c == "timestamp":
                            df_tx[c] = "2025-01-01T00:00:00Z"
                        elif c in ["input_amount", "output_amount"]:
                            df_tx[c] = 1.0
                        elif c == "fee":
                            df_tx[c] = 0.0001
                        elif c in ["input_count", "output_count"]:
                            df_tx[c] = 1
                        elif c == "is_synthetic":
                            df_tx[c] = False
                con.register("df_tx_view", df_tx[cols_to_insert])
                con.execute("INSERT OR REPLACE INTO transactions SELECT * FROM df_tx_view")
                con.unregister("df_tx_view")

        net_count = con.execute("SELECT COUNT(*) FROM network_events").fetchone()[0]
        if net_count == 0:
            net_parquet = "data/processed/canonical_network_events.parquet"
            if os.path.exists(net_parquet):
                logger.info("Populating DuckDB network_events from %s...", net_parquet)
                con.execute(f"INSERT OR REPLACE INTO network_events SELECT * FROM read_parquet('{net_parquet}')")

        alert_count = con.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
        if alert_count == 0:
            alert_parquet = "models/alerts.parquet"
            if os.path.exists(alert_parquet):
                logger.info("Populating DuckDB alerts from %s...", alert_parquet)
                con.execute(f"INSERT OR REPLACE INTO alerts SELECT * FROM read_parquet('{alert_parquet}')")

        pred_count = con.execute("SELECT COUNT(*) FROM model_predictions").fetchone()[0]
        if pred_count == 0:
            pred_parquet = "models/predictions.parquet"
            if os.path.exists(pred_parquet):
                logger.info("Populating DuckDB model_predictions from %s...", pred_parquet)
                df_preds = pd.read_parquet(pred_parquet)
                con.register("df_preds_view", df_preds)
                con.execute("""
                    INSERT OR REPLACE INTO model_predictions
                    SELECT txid, time_step, label, is_illicit, prob_illicit, anomaly_score, graph_risk, behavior_risk, network_risk
                    FROM df_preds_view
                """)
                con.unregister("df_preds_view")

        edge_count = con.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
        if edge_count == 0:
            edge_parquet = "data/processed/graph_edges.parquet"
            if os.path.exists(edge_parquet):
                logger.info("Populating DuckDB edges from %s...", edge_parquet)
                con.execute(f"INSERT INTO edges SELECT * FROM read_parquet('{edge_parquet}')")

        ent_count = con.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
        if ent_count == 0:
            node_parquet = "data/processed/graph_nodes.parquet"
            if os.path.exists(node_parquet):
                logger.info("Populating DuckDB entities from %s...", node_parquet)
                con.execute(f"INSERT INTO entities SELECT entity_id, entity_type, label, risk_score FROM read_parquet('{node_parquet}')")

# Global singleton
db_manager = DatabaseManager()
