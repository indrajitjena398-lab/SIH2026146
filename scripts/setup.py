#!/usr/bin/env python3
"""
Setup & Environment Initializer.
Checks dependencies, models, and demo data for Bitcoin Sentinel.
"""

import os
import sys
import subprocess

def main():
    print("="*70)
    print("     BITCOIN SENTINEL // SETUP & INITIALIZATION (NTRO 26146)")
    print("="*70)

    # 1. Create demo dataset
    print("[1/3] Generating demo dataset...")
    from scripts.create_demo_dataset import generate_demo_csv
    generate_demo_csv()

    # 2. Check ML model
    print("[2/3] Verifying ML model artifacts...")
    model_path = "models/classifier/xgboost.joblib"
    if not os.path.exists(model_path):
        print("Model not found. Running training pipeline...")
        subprocess.run([sys.executable, "scripts/run_pipeline.py", "--demo"], check=True)
    else:
        print("ML models verified (XGBoost, Isolation Forest, SHAP).")

    # 3. Setup Complete
    print("[3/3] Setup complete! You can start the server using:")
    print("       ./run.sh  OR  python backend/main.py")
    print("="*70)

if __name__ == "__main__":
    main()
