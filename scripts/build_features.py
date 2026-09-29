#!/usr/bin/env python3
"""
Feature Engineering CLI Script.
Assembles transaction, behavioral, network, and graph features and writes features_matrix.parquet.
"""

import os
import sys
import logging
import argparse
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.features.feature_pipeline import FeaturePipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("build_features")

def main():
    parser = argparse.ArgumentParser(description="Extract and engineer multi-modal features.")
    parser.add_argument("--transactions", default="data/processed/canonical_transactions.parquet", help="Path to transactions parquet.")
    parser.add_argument("--edges", default="data/processed/canonical_edges.parquet", help="Path to edges parquet.")
    parser.add_argument("--network", default="data/processed/canonical_network_events.parquet", help="Path to network events parquet.")
    parser.add_argument("--output", default="data/processed/features_matrix.parquet", help="Output feature matrix filepath.")
    args = parser.parse_args()

    if not os.path.exists(args.transactions):
        logger.error("Transactions file not found: %s", args.transactions)
        sys.exit(1)

    df_tx = pd.read_parquet(args.transactions)
    df_edges = pd.read_parquet(args.edges) if os.path.exists(args.edges) else pd.DataFrame()
    df_net = pd.read_parquet(args.network) if os.path.exists(args.network) else pd.DataFrame()

    pipeline = FeaturePipeline()
    df_features = pipeline.build_features(df_tx, df_edges, df_net)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    df_features.to_parquet(args.output, index=False)
    logger.info("Successfully exported features matrix (%d rows, %d columns) to: %s", len(df_features), df_features.shape[1], args.output)

if __name__ == "__main__":
    main()
