#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "================================================================="
echo "   BITCOIN SENTINEL // AI INVESTIGATION PLATFORM (NTRO 26146)"
echo "   100% OFFLINE INVESTIGATION CONSOLE"
echo "================================================================="

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

# Ensure demo data exists
if [ ! -f "data/demo/demo_transactions.csv" ]; then
    python scripts/create_demo_dataset.py
fi

echo "Starting server on http://localhost:${PORT:-8002} ..."
PORT=${PORT:-8002} python backend/main.py
