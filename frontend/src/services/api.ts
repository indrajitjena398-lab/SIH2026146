import {
  UploadResponse,
  AnalysisSummary,
  AnalysisAlert,
  TransactionDossier,
  ScannedThreatRecord,
  DatasetScanResponse
} from '../types';

const API_BASE = '/api';

export const ApiService = {
  async uploadFile(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('is_demo', 'false');

    const res = await fetch(`${API_BASE}/analysis/upload`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },

  async loadDemoDataset(): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('is_demo', 'true');

    const res = await fetch(`${API_BASE}/analysis/upload`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to load demo dataset');
    }
    return res.json();
  },

  async runAnalysis(uploadId: string): Promise<AnalysisSummary> {
    const res = await fetch(`${API_BASE}/analysis/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ upload_id: uploadId })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Analysis failed');
    }
    return res.json();
  },

  async getAnalysisSummary(analysisId: string): Promise<AnalysisSummary> {
    const res = await fetch(`${API_BASE}/analysis/${analysisId}`);
    if (!res.ok) throw new Error('Failed to fetch analysis summary');
    return res.json();
  },

  async getAnalysisAlerts(analysisId: string, riskLevel?: string, search?: string): Promise<{ total: number; alerts: AnalysisAlert[] }> {
    const query = new URLSearchParams();
    if (riskLevel && riskLevel !== 'all') query.append('risk_level', riskLevel);
    if (search) query.append('search', search);

    const res = await fetch(`${API_BASE}/analysis/${analysisId}/alerts?${query.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch alerts');
    return res.json();
  },

  async getTransactionDossier(analysisId: string, txid: string): Promise<TransactionDossier> {
    const res = await fetch(`${API_BASE}/analysis/${analysisId}/transactions/${encodeURIComponent(txid)}`);
    if (!res.ok) throw new Error('Failed to fetch transaction dossier');
    return res.json();
  },

  async getEntityGraph(analysisId: string, entityId: string, depth = 2): Promise<any> {
    const res = await fetch(`${API_BASE}/analysis/${analysisId}/graph/${encodeURIComponent(entityId)}?depth=${depth}`);
    if (!res.ok) throw new Error('Failed to fetch entity graph');
    return res.json();
  },

  async scanDataset(file?: File, useDemo = false): Promise<DatasetScanResponse> {
    const formData = new FormData();
    if (file) formData.append('file', file);
    formData.append('use_demo', useDemo ? 'true' : 'false');

    const res = await fetch(`${API_BASE}/scanner/scan`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Dataset scanning failed');
    }
    return res.json();
  },

  async scanFile(file: File): Promise<DatasetScanResponse> {
    return this.scanDataset(file, false);
  },

  // Global platform endpoints
  async getHealth(): Promise<any> {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error('Health check failed');
    return res.json();
  },

  async getStatistics(): Promise<any> {
    const res = await fetch(`${API_BASE}/statistics`);
    if (!res.ok) throw new Error('Failed to fetch statistics');
    return res.json();
  },

  async getAlerts(params: any = {}): Promise<{ total: number; alerts: any[] }> {
    const query = new URLSearchParams(params);
    const res = await fetch(`${API_BASE}/alerts?${query.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch alerts');
    return res.json();
  },

  async getAlertDetail(alertId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/alerts/${alertId}`);
    if (!res.ok) throw new Error(`Failed to fetch alert ${alertId}`);
    return res.json();
  },

  async updateAlertStatus(alertId: string, status: string): Promise<any> {
    const res = await fetch(`${API_BASE}/alerts/${alertId}/status?status=${encodeURIComponent(status)}`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error('Failed to update alert status');
    return res.json();
  },

  async getTransaction(txid: string): Promise<any> {
    const res = await fetch(`${API_BASE}/transactions/${txid}`);
    if (!res.ok) throw new Error(`Failed to fetch transaction ${txid}`);
    return res.json();
  },

  async explainTransaction(txid: string, apiKey?: string): Promise<{
    txid: string;
    alert_id?: string;
    is_attack: boolean;
    verdict: string;
    risk_level: string;
    risk_score: number;
    explanation: string;
    word_count: number;
    generated_by: string;
    transaction_details?: any;
    network_details?: any;
    reasons?: string[];
  }> {
    const url = apiKey
      ? `${API_BASE}/transactions/${encodeURIComponent(txid)}/explain?api_key=${encodeURIComponent(apiKey)}`
      : `${API_BASE}/transactions/${encodeURIComponent(txid)}/explain`;
    const res = await fetch(url);
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || `Failed to explain transaction ${txid}`);
    }
    return res.json();
  },

  async getEntity(entityId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/entities/${entityId}`);
    if (!res.ok) throw new Error(`Failed to fetch entity ${entityId}`);
    return res.json();
  },

  async getSubgraph(entityId: string, depth = 2, maxNodes = 60, types?: string): Promise<any> {
    const query = new URLSearchParams({
      entity_id: entityId,
      depth: depth.toString(),
      max_nodes: maxNodes.toString()
    });
    if (types) query.append('types', types);

    const res = await fetch(`${API_BASE}/graph/subgraph?${query.toString()}`);
    if (!res.ok) throw new Error(`Failed to fetch subgraph for ${entityId}`);
    return res.json();
  },

  async getShortestPath(source: string, target: string): Promise<any> {
    const res = await fetch(`${API_BASE}/graph/shortest_path?source=${encodeURIComponent(source)}&target=${encodeURIComponent(target)}`);
    if (!res.ok) throw new Error('Failed to compute shortest path');
    return res.json();
  },

  async getGraphEntities(): Promise<{ clusters: any[] }> {
    const res = await fetch(`${API_BASE}/graph/entities`);
    if (!res.ok) throw new Error('Failed to fetch entity clusters');
    return res.json();
  },

  async search(q: string): Promise<any[]> {
    if (!q || !q.trim()) return [];
    const res = await fetch(`${API_BASE}/search?q=${encodeURIComponent(q)}`);
    if (!res.ok) throw new Error('Search failed');
    return res.json();
  },

  async getModelMetrics(): Promise<any> {
    const res = await fetch(`${API_BASE}/models/metrics`);
    if (!res.ok) throw new Error('Failed to fetch model metrics');
    return res.json();
  },

  async predictCustom(payload: any): Promise<any> {
    const res = await fetch(`${API_BASE}/models/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('Prediction failed');
    return res.json();
  },

  async updateThreshold(config: { min_alert_threshold: number }): Promise<any> {
    const res = await fetch(`${API_BASE}/config/threshold`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    if (!res.ok) throw new Error('Failed to update threshold');
    return res.json();
  },

  async getDatasetStatus(): Promise<any> {
    const res = await fetch(`${API_BASE}/ingest/status`);
    if (!res.ok) throw new Error('Failed to fetch dataset status');
    return res.json();
  }
};
