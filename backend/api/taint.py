"""Risk taint propagation API."""

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.services.graph_service import GraphService
from backend.services.taint import build_taint_traces, calculate_taint_propagation

router = APIRouter(prefix="/taint", tags=["Taint Propagation"])


class TaintRequest(BaseModel):
    seed_wallets: List[str] = Field(..., min_length=1)
    max_hops: int = Field(4, ge=0, le=12)
    alpha: float = Field(0.85, ge=0.0, lt=1.0)


@router.post("/propagate")
def propagate_taint(request: TaintRequest) -> Dict[str, Any]:
    graph = GraphService.get_graph()
    scores = calculate_taint_propagation(graph, request.seed_wallets, request.alpha, request.max_hops)
    if not scores:
        raise HTTPException(status_code=404, detail="No seed wallet nodes were found in the graph")
    return {"seed_wallets": request.seed_wallets, "alpha": request.alpha, "max_hops": request.max_hops, "scores": scores, "traces": build_taint_traces(graph, request.seed_wallets, scores, request.max_hops)}
