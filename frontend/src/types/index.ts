export interface UploadResponse {
  upload_id: string;
  filename: string;
  file_size_bytes: number;
  record_count: number;
  schema_mapping: Record<string, string>;
  coverage: {
    blockchain_layer: { available: boolean; status: string; matched_fields: string[] };
    network_layer: { available: boolean; status: string; matched_fields: string[] };
    geoip_asn: { available: boolean; status: string; matched_fields: string[] };
  };
  message: string;
}

export interface AnalysisSummary {
  analysis_id: string;
  filename: string;
  created_at: string;
  total_transactions: number;
  total_entities: number;
  suspicious_count: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  risk_distribution: { bucket: string; count: number }[];
  coverage: any;
  alerts: AnalysisAlert[];
}

export interface AnalysisAlert {
  alert_id: string;
  analysis_id: string;
  entity_id: string;
  entity_type: string;
  transaction_id: string;
  risk_score: number;
  risk_level: 'Critical' | 'High' | 'Medium' | 'Low';
  classification_probability: number;
  anomaly_score: number;
  top_reason: string;
  timestamp: string;
  status: string;
  attack_type?: string;
  detection_layer?: string;
  input_amount?: number;
  output_amount?: number;
  input_count?: number;
  output_count?: number;
  asn?: string;
}

export interface TransactionDossier {
  analysis_id: string;
  txid: string;
  timestamp: string;
  input_amount: number;
  output_amount: number;
  fee: number;
  input_count: number;
  output_count: number;
  src_ip?: string;
  asn?: string;
  risk_score: number;
  risk_level: string;
  classification_probability: number;
  anomaly_score: number;
  top_reason: string;
  reasons: string[];
  shap_contributions: { feature: string; shap_value: number; feature_value: number }[];
  related_entities_count: {
    wallets: number;
    transactions: number;
    ips: number;
    asns: number;
    countries: number;
  };
}

export interface ScannedThreatRecord {
  row_number: number;
  txid: string;
  status: 'Attack / Suspicious' | 'Normal / Licit';
  attack_type: string;
  detection_layer: string;
  risk_score: number;
  risk_level: string;
  ml_probability: number;
  anomaly_score: number;
  why_flagged: string[];
  details: {
    amount_btc: number;
    fee_btc: number;
    input_count: number;
    output_count: number;
    src_ip: string;
    asn: string;
    country: string;
    time_step: number;
    scenario: string;
  };
  shap_contributions?: { feature: string; shap_value: number; feature_value: number }[];
}

export interface DatasetScanResponse {
  filename: string;
  file_size_bytes: number;
  total_records: number;
  attack_count: number;
  normal_count: number;
  attack_percentage: number;
  scan_duration_ms: number;
  layer_breakdown: { layer: string; count: number }[];
  attack_type_breakdown: { type: string; count: number }[];
  records: ScannedThreatRecord[];
}

export interface SearchResult {
  id: string;
  type: string;
  title: string;
  subtitle: string;
  risk_score: number;
  risk_level: string;
}

export interface Statistics {
  total_transactions: number;
  total_entities: number;
  total_edges: number;
  total_alerts: number;
  critical_alerts: number;
  high_alerts: number;
  medium_alerts: number;
  low_alerts: number;
  average_risk_score: number;
  top_risk_entities: any[];
  activity_over_time: { time_step: number; tx_count: number; alert_count: number }[];
  risk_distribution: { name: string; value: number }[];
}

export interface AlertDetail {
  alert_id: string;
  entity_id: string;
  entity_type: string;
  transaction_id: string;
  risk_score: number;
  risk_level: 'Critical' | 'High' | 'Medium' | 'Low';
  classification_probability: number;
  anomaly_score: number;
  top_reason: string;
  top_reasons: string[];
  status: string;
  timestamp: string;
  model_version: string;
  evidence: any;
  shap_contributions: { feature: string; shap_value: number; feature_value: number }[];
  transaction_details: any;
  network_details: any[];
}

export interface TransactionDetail {
  txid: string;
  time_step: number;
  timestamp: string;
  label: string;
  input_amount: number;
  output_amount: number;
  fee: number;
  input_count: number;
  output_count: number;
  prob_illicit: number;
  anomaly_score: number;
  risk_score: number;
  risk_level: string;
  reasons: string[];
  shap_contributions: { feature: string; shap_value: number; feature_value: number }[];
  network_events: any[];
}

