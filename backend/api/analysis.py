"""
Analysis API Router for the Minimalist Black-Themed Investigation System.
Provides endpoints for Upload -> Schema Detection -> Analysis Execution -> Alerts -> Investigation -> Graph -> Export.
"""

import os
import uuid
import shutil
import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Response
from pydantic import BaseModel

from src.ingestion.auto_detector import AutoSchemaDetector
from backend.services.analysis_engine import analysis_engine, ANALYSIS_CACHE
from src.graph.graph_export import GraphExporter
from backend.services.export_service import ExportService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["Analysis"])

UPLOAD_STORAGE = "data/raw/uploads"
os.makedirs(UPLOAD_STORAGE, exist_ok=True)

# In-memory lookup for pending uploaded files
UPLOAD_REGISTRY: Dict[str, Dict[str, Any]] = {}

class AnalyzeRequest(BaseModel):
    upload_id: str
    min_alert_threshold: Optional[float] = 25.0

@router.post("/upload")
async def upload_file(
    file: Optional[UploadFile] = File(None),
    is_demo: bool = Form(False)
):
    """
    Accepts CSV, JSON, or XML file or triggers demo dataset loading.
    Returns upload_id, record count, mapped schema, and dataset layer coverage.
    """
    upload_id = f"UPL-{uuid.uuid4().hex[:8].upper()}"

    if is_demo:
        demo_path = "data/demo/demo_transactions.csv"
        if not os.path.exists(demo_path):
            from scripts.create_demo_dataset import generate_demo_csv
            generate_demo_csv()
        dest_path = demo_path
        filename = "demo_transactions.csv"
    else:
        if not file:
            raise HTTPException(status_code=400, detail="No file uploaded.")
        filename = file.filename or "uploaded_data.csv"
        clean_filename = f"{upload_id}_{os.path.basename(filename)}"
        dest_path = os.path.join(UPLOAD_STORAGE, clean_filename)
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    # Auto detect schema & coverage
    try:
        df_raw = AutoSchemaDetector.parse_file(dest_path)
        _, mapping, coverage = AutoSchemaDetector.detect_schema_and_map(df_raw)
        record_count = len(df_raw)
        file_size = os.path.getsize(dest_path)
    except Exception as e:
        logger.error("Error parsing uploaded file: %s", e)
        raise HTTPException(status_code=400, detail=f"Unable to parse file. Reason: {str(e)}")

    UPLOAD_REGISTRY[upload_id] = {
        "upload_id": upload_id,
        "filepath": dest_path,
        "filename": filename,
        "file_size": file_size,
        "record_count": record_count,
        "mapping": mapping,
        "coverage": coverage
    }

    return {
        "upload_id": upload_id,
        "filename": filename,
        "file_size_bytes": file_size,
        "record_count": record_count,
        "schema_mapping": mapping,
        "coverage": coverage,
        "message": "File recognized and schema validated. Ready for analysis."
    }

@router.post("/run")
def run_analysis(request: AnalyzeRequest):
    """Executes full analysis pipeline on an uploaded dataset."""
    upload_info = UPLOAD_REGISTRY.get(request.upload_id)
    if not upload_info:
        # Check if demo was requested
        if request.upload_id == "demo":
            demo_path = "data/demo/demo_transactions.csv"
            if not os.path.exists(demo_path):
                from scripts.create_demo_dataset import generate_demo_csv
                generate_demo_csv()
            filepath = demo_path
        else:
            raise HTTPException(status_code=404, detail=f"Upload ID '{request.upload_id}' not found.")
    else:
        filepath = upload_info["filepath"]

    analysis_res = analysis_engine.analyze_dataset(
        filepath=filepath,
        min_alert_threshold=request.min_alert_threshold or 25.0
    )
    return analysis_res

@router.get("/{analysis_id}")
def get_analysis_summary(analysis_id: str):
    """Returns analysis summary and risk distribution."""
    cache = ANALYSIS_CACHE.get(analysis_id)
    if not cache:
        raise HTTPException(status_code=404, detail=f"Analysis '{analysis_id}' not found.")
    return cache["summary"]

@router.get("/{analysis_id}/alerts")
def get_analysis_alerts(
    analysis_id: str,
    risk_level: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Returns paginated and filtered alerts for an analysis run."""
    cache = ANALYSIS_CACHE.get(analysis_id)
    if not cache:
        raise HTTPException(status_code=404, detail=f"Analysis '{analysis_id}' not found.")

    all_alerts = cache["summary"]["alerts"]
    filtered = all_alerts

    if risk_level and risk_level.lower() != "all":
        filtered = [a for a in filtered if a["risk_level"].lower() == risk_level.lower()]

    if search:
        s = search.lower()
        filtered = [a for a in filtered if s in a["transaction_id"].lower() or s in a["top_reason"].lower() or s in a["alert_id"].lower()]

    total = len(filtered)
    paged = filtered[offset:offset+limit]

    return {
        "analysis_id": analysis_id,
        "total": total,
        "limit": limit,
        "offset": offset,
        "alerts": paged
    }

@router.get("/{analysis_id}/transactions/{txid}")
def get_transaction_dossier(analysis_id: str, txid: str):
    """Returns detailed forensic dossier for a transaction."""
    cache = ANALYSIS_CACHE.get(analysis_id)
    if not cache:
        raise HTTPException(status_code=404, detail=f"Analysis '{analysis_id}' not found.")

    tx_data = cache["transactions"].get(txid)
    if not tx_data:
        raise HTTPException(status_code=404, detail=f"Transaction '{txid}' not found in analysis {analysis_id}.")

    # Count related entities in graph
    G = cache["graph"]
    tx_node = f"tx_{txid}"
    related_counts = {"wallets": 0, "transactions": 0, "ips": 0, "asns": 0, "countries": 0}
    if tx_node in G:
        nbrs = set(G.successors(tx_node)).union(set(G.predecessors(tx_node)))
        for n in nbrs:
            if n.startswith("wallet_"):
                related_counts["wallets"] += 1
            elif n.startswith("tx_"):
                related_counts["transactions"] += 1
            elif n.startswith("ip_"):
                related_counts["ips"] += 1
            elif n.startswith("asn_"):
                related_counts["asns"] += 1
            elif n.startswith("country_"):
                related_counts["countries"] += 1

    tx_data["related_entities_count"] = related_counts
    return tx_data

@router.get("/{analysis_id}/graph/{entity_id}")
def get_entity_graph(
    analysis_id: str,
    entity_id: str,
    depth: int = Query(2, ge=1, le=3),
    max_nodes: int = Query(60, ge=5, le=150)
):
    """Returns Cytoscape subgraph for link analysis."""
    cache = ANALYSIS_CACHE.get(analysis_id)
    if not cache:
        raise HTTPException(status_code=404, detail=f"Analysis '{analysis_id}' not found.")

    G = cache["graph"]
    result = GraphExporter.get_ego_subgraph(G, center_node=entity_id, depth=depth, max_nodes=max_nodes)
    return result

@router.get("/{analysis_id}/export")
def export_analysis_results(
    analysis_id: str,
    format: str = Query("json", pattern="^(json|csv|html)$")
):
    """Exports full analysis report as CSV, JSON, or standalone dark HTML dossier."""
    cache = ANALYSIS_CACHE.get(analysis_id)
    if not cache:
        raise HTTPException(status_code=404, detail=f"Analysis '{analysis_id}' not found.")

    alerts = cache["summary"]["alerts"]

    if format == "csv":
        csv_str = ExportService.export_alerts_csv(alerts)
        return Response(
            content=csv_str,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=investigation_{analysis_id}.csv"}
        )
    elif format == "json":
        json_str = ExportService.export_alerts_json(cache["summary"])
        return Response(
            content=json_str,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=investigation_{analysis_id}.json"}
        )
    elif format == "html":
        # Render top alert as dossier
        if alerts:
            first_tx = alerts[0]["transaction_id"]
            dossier_data = cache["transactions"].get(first_tx, {})
            dossier_data["alert_id"] = alerts[0]["alert_id"]
            dossier_data["top_reasons"] = dossier_data.get("reasons", [])
            dossier_data["transaction_details"] = dossier_data
            html_str = ExportService.export_alert_dossier_html(dossier_data)
        else:
            html_str = "<html><body><h1>No Alerts</h1></body></html>"

        return Response(
            content=html_str,
            media_type="text/html",
            headers={"Content-Disposition": f"attachment; filename=investigation_report_{analysis_id}.html"}
        )
