import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  Search,
  Filter,
  Download,
  ArrowUpDown,
  RefreshCw,
  CheckCircle2,
  Clock,
  ChevronRight,
  Flame,
  AlertTriangle,
  X,
  ExternalLink,
  Layers
} from 'lucide-react';
import { ApiService } from '../services/api';

interface AlertsPageProps {
  onSelectAlert: (alertId: string) => void;
}

export const AlertsPage: React.FC<AlertsPageProps> = ({ onSelectAlert }) => {
  const [alerts, setAlerts] = useState<any[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [selectedRiskFilter, setSelectedRiskFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [activeDrawerAlert, setActiveDrawerAlert] = useState<any | null>(null);
  const [errorMsg, setErrorMsg] = useState('');

  const fetchAlerts = async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      const params: any = { limit: 100 };
      if (selectedRiskFilter !== 'all') {
        params.risk_level = selectedRiskFilter.charAt(0).toUpperCase() + selectedRiskFilter.slice(1);
      }
      const data = await ApiService.getAlerts(params);
      setAlerts(data.alerts);
      setTotalCount(data.total);
    } catch (e) {
      console.error(e);
      setErrorMsg(e instanceof Error ? e.message : 'Failed to load alerts from the uploaded dataset.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
    const refreshInterval = window.setInterval(fetchAlerts, 10000);
    const handleWindowFocus = () => { void fetchAlerts(); };
    window.addEventListener('focus', handleWindowFocus);

    return () => {
      window.clearInterval(refreshInterval);
      window.removeEventListener('focus', handleWindowFocus);
    };
  }, [selectedRiskFilter]);

  const handleUpdateStatus = async (alertId: string, newStatus: string) => {
    try {
      await ApiService.updateAlertStatus(alertId, newStatus);
      setAlerts(prev => prev.map(a => a.alert_id === alertId ? { ...a, status: newStatus } : a));
      if (activeDrawerAlert && activeDrawerAlert.alert_id === alertId) {
        setActiveDrawerAlert({ ...activeDrawerAlert, status: newStatus });
      }
    } catch (e) {
      console.error(e);
    }
  };

  const filteredAlerts = alerts.filter(a => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      a.alert_id.toLowerCase().includes(q) ||
      a.transaction_id.toLowerCase().includes(q) ||
      a.entity_id.toLowerCase().includes(q) ||
      (a.top_reason && a.top_reason.toLowerCase().includes(q))
    );
  });

  return (
    <div className="flex h-full overflow-hidden relative">
      {/* Main Alerts Triage Table */}
      <div className="flex-1 p-6 space-y-5 overflow-y-auto min-w-0">
        {/* Header & Controls */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/80 p-4 rounded-2xl border border-slate-800 backdrop-blur-xl shadow-xl">
          <div>
            <h1 className="text-lg font-bold text-slate-100 font-mono flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-rose-400" />
              INVESTIGATION ALERTS QUEUE
            </h1>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              Prioritized leads ranked by composite risk score &bull; Total: <strong className="text-slate-200">{totalCount} Leads</strong>
            </p>
          </div>

          <div className="flex items-center gap-2 font-mono text-xs">
            <button
              onClick={() => { void fetchAlerts(); }}
              className="px-3.5 py-1.5 rounded-xl bg-cyan-500/15 hover:bg-cyan-500/25 text-cyan-300 border border-cyan-500/40 flex items-center gap-1.5 transition-colors"
              title="Refresh uploaded dataset alerts"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Refresh</span>
            </button>
            <a
              href="/api/export/alerts?format=csv"
              target="_blank"
              rel="noreferrer"
              className="px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center gap-1.5 transition-colors"
            >
              <Download className="w-3.5 h-3.5 text-cyan-400" />
              <span>Export CSV</span>
            </a>
            <a
              href="/api/export/alerts?format=json"
              target="_blank"
              rel="noreferrer"
              className="px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center gap-1.5 transition-colors"
            >
              <Download className="w-3.5 h-3.5 text-purple-400" />
              <span>Export JSON</span>
            </a>
          </div>
        </div>

        {errorMsg && (
          <div className="rounded-lg border border-rose-500/40 bg-rose-500/10 px-3 py-2 text-[10px] text-rose-200 font-mono">
            {errorMsg}
          </div>
        )}

        {/* Filter Bar & Search */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 font-mono text-xs">
          {/* Severity Filter Chips */}
          <div className="flex items-center gap-1.5 bg-slate-900/90 p-1 rounded-xl border border-slate-800 shadow-inner">
            {['all', 'critical', 'high', 'medium', 'low'].map((f) => (
              <button
                key={f}
                onClick={() => setSelectedRiskFilter(f)}
                className={`px-3 py-1 rounded-lg uppercase text-[10px] font-bold transition-all ${
                  selectedRiskFilter === f
                    ? 'bg-cyan-500 text-black shadow-md font-extrabold'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                {f}
              </button>
            ))}
          </div>

          {/* Search Bar */}
          <div className="relative w-full sm:w-72">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Filter by Alert ID, TXID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-slate-950/90 border border-slate-700 rounded-xl text-slate-200 placeholder-slate-500 text-xs focus:outline-none focus:border-cyan-400 shadow-inner"
            />
          </div>
        </div>

        {/* Alerts Grid Table */}
        <div className="rounded-2xl bg-slate-900/80 border border-slate-800 overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950/80 text-slate-400 text-[11px] uppercase tracking-wider">
                  <th className="py-3 px-4">Alert ID</th>
                  <th className="py-3 px-4">Transaction ID</th>
                  <th className="py-3 px-4">Risk Score</th>
                  <th className="py-3 px-4">Severity</th>
                  <th className="py-3 px-4">ML Prob / Anomaly</th>
                  <th className="py-3 px-4">Primary Forensic Reason</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {loading ? (
                  <tr>
                    <td colSpan={8} className="py-12 text-center text-cyan-400 animate-pulse font-bold">
                      LOADING ALERTS FROM DUCKDB ANALYTICAL STORE...
                    </td>
                  </tr>
                ) : filteredAlerts.length > 0 ? (
                  filteredAlerts.map((alert) => (
                    <tr
                      key={alert.alert_id}
                      onClick={() => setActiveDrawerAlert(alert)}
                      className={`hover:bg-slate-800/50 cursor-pointer transition-colors ${
                        activeDrawerAlert?.alert_id === alert.alert_id ? 'bg-slate-800/70 border-l-4 border-l-cyan-400' : ''
                      }`}
                    >
                      <td className="py-3.5 px-4 font-bold text-cyan-400">{alert.alert_id}</td>
                      <td className="py-3.5 px-4 text-slate-200 font-bold">{alert.transaction_id}</td>
                      <td className="py-3.5 px-4">
                        <span className="font-bold text-slate-100 text-sm">{alert.risk_score}</span>
                        <span className="text-[10px] text-slate-500"> / 100</span>
                      </td>
                      <td className="py-3.5 px-4">
                        <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                          alert.risk_level === 'Critical' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40' :
                          alert.risk_level === 'High' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40' :
                          'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40'
                        }`}>
                          {alert.risk_level}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-slate-300 text-[11px]">
                        {Math.round(alert.classification_probability * 100)}% / {Math.round(alert.anomaly_score * 100)}%
                      </td>
                      <td className="py-3.5 px-4 text-slate-300 max-w-xs truncate">{alert.top_reason}</td>
                      <td className="py-3.5 px-4">
                        <select
                          value={alert.status}
                          onClick={(e) => e.stopPropagation()}
                          onChange={(e) => handleUpdateStatus(alert.alert_id, e.target.value)}
                          className="bg-slate-950 border border-slate-700 text-slate-200 text-[10px] rounded-lg px-2 py-1 focus:outline-none"
                        >
                          <option value="New">New</option>
                          <option value="Under Investigation">Under Investigation</option>
                          <option value="Escalated">Escalated</option>
                          <option value="False Positive">False Positive</option>
                          <option value="Closed">Closed</option>
                        </select>
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectAlert(alert.alert_id);
                          }}
                          className="px-3 py-1 bg-cyan-500/15 hover:bg-cyan-500/25 text-cyan-300 border border-cyan-500/40 rounded-lg text-[11px] font-bold transition-colors"
                        >
                          Dossier
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={8} className="py-8 text-center text-slate-500">
                      No matching alerts found for current criteria.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Slide-over Preview Drawer */}
      {activeDrawerAlert && (
        <div className="w-96 border-l border-slate-800/90 bg-[#070b14]/95 backdrop-blur-2xl flex flex-col justify-between p-5 overflow-y-auto shrink-0 shadow-2xl z-30 font-mono text-xs">
          <div className="space-y-4">
            <div className="flex justify-between items-center pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-rose-400" />
                <span className="font-bold text-slate-200">{activeDrawerAlert.alert_id}</span>
              </div>
              <button
                onClick={() => setActiveDrawerAlert(null)}
                className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-slate-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-2">
              <div className="text-[10px] text-slate-500 uppercase font-bold">Target Transaction:</div>
              <div className="text-cyan-300 font-bold break-all text-sm bg-slate-950 p-2.5 rounded-xl border border-slate-800">
                {activeDrawerAlert.transaction_id}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 p-3 rounded-xl bg-slate-950 border border-slate-800">
              <div>
                <div className="text-[10px] text-slate-500">Composite Risk:</div>
                <div className="text-xl font-bold text-rose-400">{activeDrawerAlert.risk_score} / 100</div>
              </div>
              <div>
                <div className="text-[10px] text-slate-500">Severity Tier:</div>
                <div className="text-xs font-bold text-slate-200 mt-1">{activeDrawerAlert.risk_level}</div>
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="text-[10px] text-slate-500 uppercase font-bold">Primary Evidentiary Driver:</div>
              <div className="text-slate-200 bg-slate-950 p-3 rounded-xl border border-slate-800 leading-relaxed text-[11px]">
                {activeDrawerAlert.top_reason}
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-800 space-y-2">
            <button
              onClick={() => onSelectAlert(activeDrawerAlert.alert_id)}
              className="w-full py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-black font-extrabold text-xs transition-colors glow-cyan shadow-lg"
            >
              Open Full Investigation Dossier
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
