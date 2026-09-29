"""
FastAPI Backend Application for Bitcoin Transaction Traffic Monitoring Platform (NTRO 26146).
Minimalist, high-performance forensic investigation API.
"""

import os
import sys
import time
import logging

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.database import db_manager
from backend.services.ml_service import MLService
from backend.services.analysis_engine import analysis_engine

from backend.api.analysis import router as analysis_router
from backend.api.alerts import router as alerts_router
from backend.api.transactions import router as transactions_router
from backend.api.entities import router as entities_router
from backend.api.graph import router as graph_router
from backend.api.models import router as models_router
from backend.api.search import router as search_router
from backend.api.export import router as export_router
from backend.api.ingestion import router as ingestion_router
from backend.api.explanation import router as explanation_router
from backend.api.taint import router as taint_router
from backend.api.scanner import router as scanner_router
from backend.schemas.common import ThresholdConfig

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("backend")

START_TIME = time.time()

ACTIVE_THRESHOLD_CONFIG = {
    "min_alert_threshold": 30.0,
    "classification_weight": 0.40,
    "anomaly_weight": 0.20,
    "graph_weight": 0.20,
    "behavior_weight": 0.10,
    "network_weight": 0.10
}

app = FastAPI(
    title="Bitcoin Sentinel — AI Transaction Traffic Investigation",
    description="Minimalist, Offline-Capable Bitcoin Forensic Investigation Platform (NTRO Problem 26146)",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    logger.info("Initializing Bitcoin Sentinel Investigation Engine...")
    MLService.load_resources()
    logger.info("System operational for forensic investigations.")

# Mount API Routers
app.include_router(analysis_router, prefix="/api")
app.include_router(alerts_router, prefix="/api")
app.include_router(transactions_router, prefix="/api")
app.include_router(entities_router, prefix="/api")
app.include_router(graph_router, prefix="/api")
app.include_router(models_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(export_router, prefix="/api")
app.include_router(ingestion_router, prefix="/api")
app.include_router(explanation_router, prefix="/api")
app.include_router(taint_router, prefix="/api")
app.include_router(scanner_router, prefix="/api")
app.include_router(scanner_router, prefix="/api/scanner")

from backend.services.alert_service import AlertService

@app.get("/api/config/threshold")
def get_threshold():
    return ACTIVE_THRESHOLD_CONFIG

@app.post("/api/config/threshold")
def update_threshold(config: ThresholdConfig):
    ACTIVE_THRESHOLD_CONFIG["min_alert_threshold"] = config.min_alert_threshold
    if config.classification_weight is not None:
        ACTIVE_THRESHOLD_CONFIG["classification_weight"] = config.classification_weight
    if config.anomaly_weight is not None:
        ACTIVE_THRESHOLD_CONFIG["anomaly_weight"] = config.anomaly_weight
    if config.graph_weight is not None:
        ACTIVE_THRESHOLD_CONFIG["graph_weight"] = config.graph_weight
    if config.behavior_weight is not None:
        ACTIVE_THRESHOLD_CONFIG["behavior_weight"] = config.behavior_weight
    if config.network_weight is not None:
        ACTIVE_THRESHOLD_CONFIG["network_weight"] = config.network_weight
    return {"status": "success", "config": ACTIVE_THRESHOLD_CONFIG}

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "database": "DuckDB Connected",
        "version": "2.0.0",
        "uptime_seconds": round(time.time() - START_TIME, 2)
    }

@app.get("/api/statistics")
def get_statistics():
    return AlertService.get_statistics()

# Serve frontend static assets if built
FRONTEND_DIST = "frontend/dist"
if os.path.exists(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="static")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8002"))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=False)
