#!/usr/bin/env python3
"""
Master Data Ingestion Script.
Ingests CSV, JSON, and XML sources, normalizes schemas, verifies data integrity,
and writes canonical tables to data/processed/.
"""

import os
import sys
import logging
import argparse
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.data.dataset_adapter import DatasetAdapter
from src.ingestion.csv_loader import CSVLoader
from src.ingestion.json_loader import JSONLoader
from src.ingestion.xml_loader import XMLLoader

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ingest_data")

PROCESSED_DIR = "data/processed"
ERROR_DIR = "data/errors"

def main():
    parser = argparse.ArgumentParser(description="Ingest and normalize raw Bitcoin and network traffic data.")
    parser.add_argument("--features", default="data/raw/elliptic_txs_features.csv", help="Path to features CSV.")
    parser.add_argument("--classes", default="data/raw/elliptic_txs_classes.csv", help="Path to classes CSV.")
    parser.add_argument("--edgelist", default="data/raw/elliptic_txs_edgelist.csv", help="Path to edgelist CSV.")
    parser.add_argument("--network", default="data/synthetic/network_events.csv", help="Path to network events CSV.")
    parser.add_argument("--output-dir", default=PROCESSED_DIR, help="Destination directory for processed files.")
    parser.add_argument("--max-rows", type=int, default=None, help="Optional max rows for fast ingestion.")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(ERROR_DIR, exist_ok=True)

    adapter = DatasetAdapter(dataset_name="elliptic")
    data_dict = adapter.load_dataset(
        features_path=args.features,
        edgelist_path=args.edgelist,
        classes_path=args.classes,
        max_rows=args.max_rows
    )

    is_valid, errors = adapter.validate_schema(data_dict)
    if not is_valid:
        logger.error("Dataset validation failed: %s", errors)
        sys.exit(1)

    # Merge features with classes for canonical transaction table
    df_feat = data_dict["features"]
    df_cls = data_dict["classes"]
    df_edge = data_dict["edges"]

    df_tx = pd.merge(df_cls, df_feat, on="txid", how="inner")
    
    # Save canonical parquet / csv files
    tx_out = os.path.join(args.output_dir, "canonical_transactions.parquet")
    df_tx.to_parquet(tx_out, index=False)

    edge_out = os.path.join(args.output_dir, "canonical_edges.parquet")
    df_edge.to_parquet(edge_out, index=False)

    # Ingest network events
    if os.path.exists(args.network):
        csv_loader = CSVLoader(error_dir=ERROR_DIR)
        df_net_valid, _ = csv_loader.load_network_events(args.network, max_rows=args.max_rows)
        net_out = os.path.join(args.output_dir, "canonical_network_events.parquet")
        df_net_valid.to_parquet(net_out, index=False)
        logger.info("Ingested and saved %d network events to: %s", len(df_net_valid), net_out)

    logger.info("Data Ingestion Complete: %d transactions, %d edges saved to: %s", len(df_tx), len(df_edge), args.output_dir)

if __name__ == "__main__":
    main()
