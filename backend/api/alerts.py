"""
Alerts API Router.
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Path
from backend.schemas.common import AlertItem, AlertDetail
from backend.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("", response_model=Dict[str, Any])
def list_alerts(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    risk_level: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("risk_score"),
    sort_order: str = Query("desc")
):
    items, total = AlertService.get_alerts(
        limit=limit,
        offset=offset,
        risk_level=risk_level,
        entity_type=entity_type,
        min_score=min_score,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "alerts": items
    }

@router.get("/{alert_id}", response_model=AlertDetail)
def get_alert_detail(alert_id: str = Path(...)):
    detail = AlertService.get_alert_detail(alert_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found")
    return detail

@router.post("/{alert_id}/status")
def update_alert_status(alert_id: str = Path(...), status: str = Query(...)):
    success = AlertService.update_alert_status(alert_id, status)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update alert status")
    return {"status": "success", "alert_id": alert_id, "new_status": status}
