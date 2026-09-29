"""
Graph & Link Analysis API Router.
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Path
from backend.services.graph_service import GraphService
from backend.services.entity_cluster import get_entity_clusters
from backend.schemas.common import CytoscapeGraph

router = APIRouter(prefix="/graph", tags=["Graph"])

@router.get("/entities")
def get_graph_entities():
    """Return common-input ownership clusters as graph super-nodes."""
    return {"clusters": get_entity_clusters(GraphService.get_graph())}

@router.get("/subgraph", response_model=CytoscapeGraph)
def get_subgraph(
    entity_id: str = Query(..., description="Target node identifier"),
    depth: int = Query(2, ge=1, le=4),
    max_nodes: int = Query(60, ge=5, le=200),
    types: Optional[str] = Query(None, description="Comma-separated entity type filter, e.g. 'Transaction,Wallet,IP'")
):
    filter_list = [t.strip() for t in types.split(",")] if types else None
    result = GraphService.get_subgraph(
        entity_id=entity_id,
        depth=depth,
        max_nodes=max_nodes,
        filter_types=filter_list
    )
    if "error" in result and not result["nodes"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@router.get("/shortest_path")
def get_shortest_path(
    source: str = Query(..., description="Source entity ID"),
    target: str = Query(..., description="Target entity ID")
):
    result = GraphService.get_shortest_path(source_id=source, target_id=target)
    return result
