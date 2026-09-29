"""Export & forensic dossier API router."""

import hashlib
import io
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Response
from backend.services.alert_service import AlertService
from backend.services.export_service import ExportService

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

router = APIRouter(prefix="/export", tags=["Export"])


def _forensic_checksum(dossier: Dict[str, Any]) -> str:
    shap = dossier.get("shap_contributions", [])
    payload = {
        "transaction_hash": dossier.get("transaction_id", dossier.get("entity_id", "")),
        "timestamp": dossier.get("timestamp", ""),
        "risk_score": dossier.get("risk_score", 0),
        "shap_features": shap,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


@router.get("/stix/{alert_id}")
def export_alert_stix(alert_id: str):
    """Export an alert as a compact STIX 2.1 threat-intelligence bundle."""
    dossier = AlertService.get_alert_detail(alert_id)
    if not dossier:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found")
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    transaction_id = dossier.get("transaction_id", dossier.get("entity_id", alert_id))
    identity_id = f"identity--{uuid.uuid5(uuid.NAMESPACE_URL, 'bitcoin-sentinel') }"
    indicator_id = f"indicator--{uuid.uuid5(uuid.NAMESPACE_URL, f'bitcoin-sentinel:{alert_id}') }"
    observable_id = f"observed-data--{uuid.uuid5(uuid.NAMESPACE_URL, f'bitcoin-sentinel:observable:{transaction_id}') }"
    bundle = {
        "type": "bundle",
        "id": f"bundle--{uuid.uuid4()}",
        "objects": [
            {"type": "identity", "spec_version": "2.1", "id": identity_id, "created": now, "modified": now, "name": "Bitcoin Sentinel", "identity_class": "organization"},
            {"type": "indicator", "spec_version": "2.1", "id": indicator_id, "created": now, "modified": now, "name": f"Bitcoin transaction alert {alert_id}", "pattern": f"[file:hashes.'SHA-256' = '{transaction_id}']", "pattern_type": "stix", "valid_from": now, "confidence": int(float(dossier.get('risk_score', 0)))},
            {"type": "observed-data", "spec_version": "2.1", "id": observable_id, "created": now, "modified": now, "first_observed": str(dossier.get("timestamp", now)), "last_observed": str(dossier.get("timestamp", now)), "number_observed": 1, "object_refs": [indicator_id], "x_transaction_id": transaction_id, "x_risk_score": dossier.get("risk_score", 0), "x_forensic_checksum": _forensic_checksum(dossier)},
        ],
    }
    return Response(content=json.dumps(bundle, indent=2), media_type="application/stix+json", headers={"Content-Disposition": f"attachment; filename={alert_id}.stix.json"})


@router.get("/pdf/{alert_id}")
def export_alert_pdf(alert_id: str):
    """Generate a court-ready PDF dossier with a deterministic evidence checksum."""
    dossier = AlertService.get_alert_detail(alert_id)
    if not dossier:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found")
    checksum = _forensic_checksum(dossier)
    output = io.BytesIO()
    document = canvas.Canvas(output, pagesize=letter)
    width, height = letter
    y = height - 54
    document.setTitle(f"Bitcoin Sentinel Forensic Report {alert_id}")
    document.setFont("Helvetica-Bold", 16)
    document.drawString(48, y, "Bitcoin Sentinel Forensic Report")
    y -= 28
    document.setFont("Helvetica", 10)
    fields = [
        ("Alert ID", alert_id),
        ("Transaction ID", dossier.get("transaction_id", "")),
        ("Risk score", f"{dossier.get('risk_score', 0)} / 100"),
        ("Risk level", str(dossier.get("risk_level", ""))),
        ("Timestamp", str(dossier.get("timestamp", ""))),
        ("Evidence SHA-256", checksum),
    ]
    for label, value in fields:
        document.setFont("Helvetica-Bold", 10)
        document.drawString(48, y, f"{label}:")
        document.setFont("Helvetica", 10)
        document.drawString(155, y, str(value)[:100])
        y -= 18
    y -= 8
    document.setFont("Helvetica-Bold", 11)
    document.drawString(48, y, "Forensic reasons")
    y -= 18
    document.setFont("Helvetica", 9)
    reasons = dossier.get("top_reasons", [dossier.get("top_reason", "No reason recorded")])
    for reason in reasons:
        document.drawString(60, y, f"- {str(reason)[:110]}")
        y -= 15
    document.setFont("Helvetica-Oblique", 8)
    document.drawString(48, 38, "Decision support only. Verify source records and chain of custody before legal use.")
    document.save()
    return Response(content=output.getvalue(), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=forensic_{alert_id}.pdf"})

@router.get("/alerts")
def export_alerts(
    format: str = Query("json", pattern="^(json|csv|html)$"),
    risk_level: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None)
):
    alerts, _ = AlertService.get_alerts(limit=500, risk_level=risk_level, min_score=min_score)

    if format == "csv":
        csv_content = ExportService.export_alerts_csv(alerts)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=alerts_export.csv"}
        )
    elif format == "json":
        json_content = ExportService.export_alerts_json(alerts)
        return Response(
            content=json_content,
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=alerts_export.json"}
        )
    elif format == "html":
        if alerts:
            first_id = alerts[0]["alert_id"]
            dossier = AlertService.get_alert_detail(first_id)
            html_content = ExportService.export_alert_dossier_html(dossier)
        else:
            html_content = "<html><body><h1>No Alerts Found</h1></body></html>"
        return Response(
            content=html_content,
            media_type="text/html",
            headers={"Content-Disposition": "attachment; filename=investigation_dossier.html"}
        )

@router.get("/dossier/{alert_id}")
def export_single_dossier(alert_id: str):
    dossier = AlertService.get_alert_detail(alert_id)
    if not dossier:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found")
    
    html_content = ExportService.export_alert_dossier_html(dossier)
    return Response(
        content=html_content,
        media_type="text/html",
        headers={"Content-Disposition": f"attachment; filename=dossier_{alert_id}.html"}
    )
