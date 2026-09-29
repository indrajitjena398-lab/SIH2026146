"""
Pydantic Data Schemas for the Bitcoin Investigation Platform API.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    status: str
    database: str
    models_loaded: List[str]
    dataset_records: int
    alerts_count: int
    version: str
    uptime_seconds: float

class StatisticsResponse(BaseModel):
    total_transactions: int
    total_entities: int
    suspicious_transactions: int
    critical_alerts: int
    high_alerts: int
    medium_alerts: int
    low_alerts: int
    avg_risk_score: float
    high_risk_wallets_count: int
    high_risk_ips_count: int
    risk_distribution: List[Dict[str, Any]]
    activity_over_time: List[Dict[str, Any]]
    alert_trend: List[Dict[str, Any]]
    top_suspicious_entities: List[Dict[str, Any]]

class AlertItem(BaseModel):
    alert_id: str
    entity_id: str
    entity_type: str
    transaction_id: str
    risk_score: float
    risk_level: str
    classification_probability: float
    anomaly_score: float
    top_reason: str
    status: str
    timestamp: str
    model_version: str
    patterns: List[Dict[str, Any]] = Field(default_factory=list)

class AlertDetail(AlertItem):
    top_reasons: List[str]
    evidence: Dict[str, Any]
    shap_contributions: List[Dict[str, Any]]
    transaction_details: Optional[Dict[str, Any]] = None
    network_details: Optional[List[Dict[str, Any]]] = None

class EntityDetail(BaseModel):
    entity_id: str
    entity_type: str
    label: str
    risk_score: float
    risk_level: str
    degree: int
    in_degree: int
    out_degree: int
    connected_transactions: List[str]
    associated_ips: List[str]
    associated_asns: List[str]

class TransactionDetail(BaseModel):
    txid: str
    time_step: int
    timestamp: str
    label: str
    is_illicit: int
    input_amount: float
    output_amount: float
    fee: float
    input_count: int
    output_count: int
    is_synthetic: bool
    risk_score: float
    risk_level: str
    prob_illicit: float
    anomaly_score: float
    network_events: List[Dict[str, Any]]
    shap_contributions: List[Dict[str, Any]]
    reasons: List[str]

class GraphNode(BaseModel):
    data: Dict[str, Any]

class GraphEdge(BaseModel):
    data: Dict[str, Any]

class CytoscapeGraph(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

class SearchResultItem(BaseModel):
    id: str
    type: str
    title: str
    subtitle: str
    risk_score: float
    risk_level: str

class ThresholdConfig(BaseModel):
    min_alert_threshold: float = Field(..., ge=0.0, le=100.0)
    classification_weight: Optional[float] = 0.40
    anomaly_weight: Optional[float] = 0.20
    graph_weight: Optional[float] = 0.20
    behavior_weight: Optional[float] = 0.10
    network_weight: Optional[float] = 0.10

class PredictRequest(BaseModel):
    txid: Optional[str] = "custom_tx_test"
    time_step: Optional[int] = 49
    input_amount: Optional[float] = 1.5
    output_amount: Optional[float] = 1.499
    fee: Optional[float] = 0.001
    input_count: Optional[int] = 1
    output_count: Optional[int] = 10
    src_ip: Optional[str] = "185.220.101.5"
    asn: Optional[str] = "AS200651"
    features: Optional[List[float]] = None
