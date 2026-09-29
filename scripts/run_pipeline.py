#!/usr/bin/env python3
"""
Master End-to-End Orchestrator Pipeline for Bitcoin Transaction Traffic Platform (NTRO 26146).
Executes all stages: Download -> Network Synthesis -> Ingestion -> Feature Engineering ->
Graph Construction -> ML Training -> Evaluation -> DuckDB Seeding -> Verification.
"""

import os
import sys
import time
import logging
import argparse
import subprocess

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("master_pipeline")

PYTHON_EXEC = sys.executable

def run_step(step_name: str, cmd_args: list):
    """Executes a sub-pipeline script and logs timing and outputs."""
    logger.info("="*80)
    logger.info(">>> STARTING STAGE: %s", step_name)
    logger.info("COMMAND: %s", " ".join(cmd_args))
    logger.info("="*80)

    start_t = time.time()
    result = subprocess.run(cmd_args, capture_output=True, text=True)

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    duration = time.time() - start_t
    if result.returncode != 0:
        logger.error("Stage '%s' FAILED with exit code %d (Time: %.2fs)", step_name, result.returncode, duration)
        sys.exit(result.returncode)
    else:
        logger.info("Stage '%s' COMPLETED SUCCESSFULLY in %.2fs", step_name, duration)

def main():
    parser = argparse.ArgumentParser(description="End-to-End Master Pipeline for Bitcoin Transaction Monitoring.")
    parser.add_argument("--demo", action="store_true", default=True, help="Run in lightweight fast demo mode (5,000 txs).")
    parser.add_argument("--full", action="store_true", help="Run full scale dataset processing.")
    parser.add_argument("--stage", type=str, default="all", choices=["all", "download", "network", "ingest", "features", "graph", "train", "evaluate"])
    parser.add_argument("--seed", type=int, default=42, help="Deterministic random seed.")
    args = parser.parse_args()

    overall_start = time.time()
    logger.info("="*80)
    logger.info("   NTRO 26146: AI BITCOIN TRANSACTION MONITORING & INVESTIGATION PIPELINE")
    logger.info("   Mode: %s | PRNG Seed: %d", "FULL" if args.full else "DEMO", args.seed)
    logger.info("="*80)

    # Stage 1: Dataset Acquisition
    if args.stage in ["all", "download"]:
        download_cmd = [PYTHON_EXEC, "scripts/download_datasets.py"]
        if args.full:
            download_cmd.append("--full")
        else:
            download_cmd.append("--demo")
        run_step("1. Dataset Acquisition & Verification", download_cmd)

    # Stage 2: Synthetic Network Layer Generation
    if args.stage in ["all", "network"]:
        net_cmd = [
            PYTHON_EXEC, "scripts/generate_network_data.py",
            "--rows", "10000",
            "--seed", str(args.seed),
            "--txids-file", "data/raw/elliptic_txs_classes.csv",
            "--output", "data/synthetic/network_events.csv"
        ]
        run_step("2. Synthetic Network Telemetry Generation", net_cmd)

    # Stage 3: Data Ingestion & Canonicalization
    if args.stage in ["all", "ingest"]:
        ingest_cmd = [PYTHON_EXEC, "scripts/ingest_data.py"]
        run_step("3. Ingestion, Normalization & Schema Validation", ingest_cmd)

    # Stage 4: Feature Engineering
    if args.stage in ["all", "features"]:
        feat_cmd = [PYTHON_EXEC, "scripts/build_features.py"]
        run_step("4. Multi-Modal Feature Extraction & Scaling", feat_cmd)

    # Stage 5: Heterogeneous Graph Construction
    if args.stage in ["all", "graph"]:
        graph_cmd = [PYTHON_EXEC, "scripts/build_graph.py"]
        run_step("5. Heterogeneous Graph Construction & Analytics", graph_cmd)

    # Stage 6: ML Model Training & Temporal Holdout Evaluation
    if args.stage in ["all", "train"]:
        train_cmd = [PYTHON_EXEC, "scripts/train_models.py", "--seed", str(args.seed)]
        run_step("6. Machine Learning Training & TreeSHAP Attribution", train_cmd)

    # Stage 7: Model Evaluation Report
    if args.stage in ["all", "evaluate"]:
        eval_cmd = [PYTHON_EXEC, "scripts/evaluate_models.py"]
        run_step("7. Comprehensive Evaluation Benchmark Report", eval_cmd)

    # Final DB Initialization & Verification
    db_init_cmd = [PYTHON_EXEC, "-c", "from backend.database import DatabaseManager; db = DatabaseManager(); print('DuckDB analytical database verified and ready.')"]
    run_step("8. DuckDB Database Verification", db_init_cmd)

    total_time = time.time() - overall_start
    logger.info("="*80)
    logger.info("   PIPELINE COMPLETED SUCCESSFULLY IN %.2f SECONDS!", total_time)
    logger.info("   The platform is start-ready for offline investigation.")
    logger.info("   To launch backend server:")
    logger.info("       python backend/main.py")
    logger.info("   To launch frontend dashboard (development):")
    logger.info("       npm --prefix frontend run dev")
    logger.info("="*80)

if __name__ == "__main__":
    main()
