import React, { useRef, useState, useEffect } from 'react';
import {
  TrendingUp,
  ShieldAlert,
  AlertTriangle,
  Flame,
  Activity,
  Layers,
  ArrowRight,
  Sparkles,
  Users,
  Radio,
  Globe,
  Lock,
  Upload,
  CheckCircle2,
  LoaderCircle,
  FileUp
} from 'lucide-react';
import {
  AreaChart, Area, PieChart, Pie, Cell, ResponsiveContainer, XAxis, YAxis, Tooltip
} from 'recharts';
import { Statistics } from '../types';

interface OverviewPageProps {
  stats: Statistics | null;
  onSelectEntity: (id: string, type?: string) => void;
  onNavigate: (tab: string) => void;
  onDatasetRefresh?: () => Promise<void> | void;
}

const COLORS = ['#ef4444', '#f59e0b', '#00f2fe', '#10b981'];

const allowedFormats = ['.json', '.xlsx', '.xls', '.xml', '.csv'];

const getStatusMeta = (status: string, message: string) => {
  const normalized = `${status} ${message}`.toLowerCase();

  if (normalized.includes('analysis complete')) return {
    phase: 'complete',
    label: 'Analysis Complete',
    className: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300'
  };

  if (normalized.includes('evaluating') || normalized.includes('model')) return {
    phase: 'evaluating',
    label: 'Evaluating Model...',
    className: 'border-cyan-500/40 bg-cyan-500/10 text-cyan-300'
  };

  if (normalized.includes('converting') || status === 'converting') return {
    phase: 'converting',
    label: 'Converting Data to CSV...',
    className: 'border-amber-500/40 bg-amber-500/10 text-amber-300'
  };

  return {
    phase: 'ready',
    label: 'Ready',
    className: 'border-cyan-500/40 bg-cyan-500/10 text-cyan-300'
  };
};

export const OverviewPage: React.FC<OverviewPageProps> = ({ stats, onSelectEntity, onNavigate, onDatasetRefresh }) => {
  const chartData = stats?.activity_over_time || [];
  const timestepCount = chartData.length > 0
    ? Math.max(...chartData.map((item) => Number(item.time_step) || 0))
    : 49;
  const riskPieData = stats?.risk_distribution || [
    { name: 'Critical (>=75)', value: stats?.critical_alerts ?? 12 },
    { name: 'High (50-74)', value: stats?.high_alerts ?? 45 },
    { name: 'Medium (25-49)', value: stats?.medium_alerts ?? 161 },
    { name: 'Low (0-24)', value: stats?.low_alerts ?? 4782 }
  ];
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const statusIntervalRef = useRef<number | null>(null);
  const [isDraggingUpload, setIsDraggingUpload] = useState(false);
  const [selectedUploadFile, setSelectedUploadFile] = useState<string>('');
  const [uploadStatus, setUploadStatus] = useState({
    status: 'ready',
    message: 'Ready',
    fileName: '',
    totalRows: 0,
    flaggedTransactions: 0
  });
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  useEffect(() => {
    return () => {
      if (statusIntervalRef.current) {
        window.clearInterval(statusIntervalRef.current);
      }
    };
  }, []);

  const pollUploadStatus = async () => {
    try {
      const res = await fetch('/api/ingest/conversion-status');
      if (!res.ok) return;
      const data = await res.json();
      const nextStatus = data?.status || 'ready';
      const nextMessage = data?.message || 'Ready';
      const nextMeta = getStatusMeta(nextStatus, nextMessage);

      setUploadStatus((prev) => ({
        ...prev,
        status: nextMeta.phase,
        message: nextMeta.label,
        fileName: data?.current_file || prev.fileName,
        totalRows: Number(data?.total_rows || prev.totalRows || 0),
        flaggedTransactions: Number(data?.flagged_transactions ?? prev.flaggedTransactions ?? 0)
      }));

      if (nextMeta.phase === 'complete' || nextMeta.phase === 'ready') {
        if (statusIntervalRef.current) {
          window.clearInterval(statusIntervalRef.current);
          statusIntervalRef.current = null;
        }
        setIsUploading(false);
        if (onDatasetRefresh) {
          void onDatasetRefresh();
        }
      }
    } catch (error) {
      console.error('Upload status poll failed', error);
    }
  };

  const handleFileSelection = async (file: File | null) => {
    if (!file) return;

    const ext = `.${file.name.split('.').pop()?.toLowerCase() ?? ''}`;
    if (!allowedFormats.includes(ext)) {
      setUploadError(`Unsupported file type. Allowed: ${allowedFormats.join(', ')}`);
      return;
    }

    setUploadError(null);
    setSelectedUploadFile(file.name);
    setIsUploading(true);
    setUploadStatus({
      status: 'converting',
      message: 'Converting Data to CSV...',
      fileName: file.name,
      totalRows: 0,
      flaggedTransactions: 0
    });

    const formData = new FormData();
    formData.append('file', file);
    formData.append('dataset_type', 'transaction');
    formData.append('auto_infer', 'true');

    try {
      const response = await fetch('/api/ingest/upload-and-convert', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const detail = await response.json().catch(() => ({ detail: 'Upload failed' }));
        throw new Error(detail.detail || 'Upload failed');
      }

      const result = await response.json();
      const conversionMeta = result?.conversion_metadata || {};
      setUploadStatus({
        status: 'converting',
        message: 'Converting Data to CSV...',
        fileName: file.name,
        totalRows: Number(conversionMeta?.total_rows || 0),
        flaggedTransactions: Number(conversionMeta?.flagged_transactions || 0)
      });

      // The runtime dataset is rebuilt before the upload response returns.
      // Refresh dashboard KPIs immediately instead of waiting for polling.
      if (onDatasetRefresh) {
        await onDatasetRefresh();
      }

      if (statusIntervalRef.current) {
        window.clearInterval(statusIntervalRef.current);
      }
      statusIntervalRef.current = window.setInterval(() => { void pollUploadStatus(); }, 1000);
      await pollUploadStatus();
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : 'Upload failed');
      setIsUploading(false);
      setUploadStatus({
        status: 'ready',
        message: 'Ready',
        fileName: file.name,
        totalRows: 0,
        flaggedTransactions: 0
      });
    }
  };

  const statusMeta = getStatusMeta(uploadStatus.status, uploadStatus.message);

  return (
    <div className="p-6 space-y-6 overflow-y-auto">
      {/* Top Welcome & Mission Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900/90 via-slate-900/60 to-cyan-950/30 border border-slate-800/90 backdrop-blur-xl shadow-2xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex-1">
          <h1 className="text-2xl font-black text-slate-100 font-mono tracking-tight">
            NTRO 26146 // AI-POWERED BITCOIN TRANSACTION TRAFFIC MONITOR
          </h1>
          <p className="text-xs text-slate-400 font-mono mt-1 max-w-2xl">
            Correlating on-chain graph topologies, behavioral velocities, and P2P network telemetry to detect suspicious ransomware, mixer peel chains, and darknet transactions.
          </p>
        </div>

        <div className="flex flex-col items-stretch gap-3 min-w-[340px] font-mono">
          <div
            onClick={() => !isUploading && fileInputRef.current?.click()}
            onDragOver={(event) => {
              event.preventDefault();
              setIsDraggingUpload(true);
            }}
            onDragLeave={() => setIsDraggingUpload(false)}
            onDrop={(event) => {
              event.preventDefault();
              setIsDraggingUpload(false);
              const dropped = event.dataTransfer.files?.[0] || null;
              void handleFileSelection(dropped);
            }}
            className={`cursor-pointer rounded-xl border border-dashed px-4 py-3 transition-all ${isDraggingUpload ? 'border-cyan-400 bg-cyan-500/10' : 'border-slate-700 bg-slate-900/50 hover:border-cyan-500/60'}`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept={allowedFormats.join(',')}
              className="hidden"
              onChange={(event) => {
                const file = event.target.files?.[0] || null;
                void handleFileSelection(file);
              }}
            />
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-slate-200">
                <Upload className="w-4 h-4 text-cyan-400" />
                <span className="text-xs font-bold uppercase tracking-[0.2em]">Upload Dataset</span>
              </div>
              <FileUp className="w-4 h-4 text-slate-400" />
            </div>
          </div>

          <div className={`flex items-center gap-2 rounded-full border px-2.5 py-1.5 text-[10px] font-bold uppercase tracking-[0.18em] ${statusMeta.className}`}>
            {uploadStatus.status === 'converting' ? <LoaderCircle className="w-3.5 h-3.5 animate-spin" /> : uploadStatus.status === 'complete' ? <CheckCircle2 className="w-3.5 h-3.5" /> : <span className="w-2 h-2 rounded-full bg-current" />}
            <span>{statusMeta.label}</span>
          </div>

          <div className="grid grid-cols-3 gap-2 text-[10px] text-slate-300 font-mono">
            <div className="rounded-lg border border-slate-700 bg-slate-900/40 p-2">
              <div className="text-slate-500 uppercase tracking-[0.18em]">File</div>
              <div className="mt-1 truncate font-bold text-cyan-300">{uploadStatus.fileName || '—'}</div>
            </div>
            <div className="rounded-lg border border-slate-700 bg-slate-900/40 p-2">
              <div className="text-slate-500 uppercase tracking-[0.18em]">Rows</div>
              <div className="mt-1 font-bold text-slate-100">{uploadStatus.totalRows.toLocaleString()}</div>
            </div>
            <div className="rounded-lg border border-slate-700 bg-slate-900/40 p-2">
              <div className="text-slate-500 uppercase tracking-[0.18em]">Flagged</div>
              <div className="mt-1 font-bold text-rose-300">{uploadStatus.flaggedTransactions.toLocaleString()}</div>
            </div>
          </div>

          {uploadError && (
            <div className="rounded-lg border border-rose-500/40 bg-rose-500/10 px-3 py-2 text-[10px] text-rose-200 font-mono">
              {uploadError}
            </div>
          )}
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Total Transactions */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800/90 backdrop-blur-xl space-y-2 shadow-xl hover:border-slate-700 transition-colors">
          <div className="flex justify-between items-center text-slate-400 font-mono text-xs">
            <span className="text-[11px] uppercase tracking-wider font-bold">TOTAL TRANSACTIONS</span>
            <Layers className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-3xl font-black text-slate-100 font-mono">
            {stats ? stats.total_transactions.toLocaleString() : '5,000'}
          </div>
          <div className="text-[11px] text-slate-500 font-mono flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
            <span>{timestepCount} Timesteps (Current Dataset)</span>
          </div>
        </div>

        {/* Card 2: Heterogeneous Entities */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800/90 backdrop-blur-xl space-y-2 shadow-xl hover:border-slate-700 transition-colors">
          <div className="flex justify-between items-center text-slate-400 font-mono text-xs">
            <span className="text-[11px] uppercase tracking-wider font-bold">GRAPH ENTITIES</span>
            <Users className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-3xl font-black text-slate-100 font-mono">
            {stats ? stats.total_entities.toLocaleString() : '15,053'}
          </div>
          <div className="text-[11px] text-slate-500 font-mono flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-purple-400"></span>
            <span>Wallets, TXs, IPs, ASNs, Countries</span>
          </div>
        </div>

        {/* Card 3: Critical Threat Leads */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-rose-500/30 backdrop-blur-xl space-y-2 shadow-xl glow-rose">
          <div className="flex justify-between items-center text-rose-300 font-mono text-xs">
            <span className="text-[11px] uppercase tracking-wider font-bold">CRITICAL ALERTS</span>
            <Flame className="w-4 h-4 text-rose-400 animate-pulse" />
          </div>
          <div className="text-3xl font-black text-rose-400 font-mono">
            {stats ? stats.critical_alerts : 12}
          </div>
          <div className="text-[11px] text-rose-300/80 font-mono flex items-center gap-1.5">
            <AlertTriangle className="w-3 h-3 text-rose-400" />
            <span>Risk Score &ge; 75 / 100</span>
          </div>
        </div>

        {/* Card 4: Average Risk Score */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800/90 backdrop-blur-xl space-y-2 shadow-xl hover:border-slate-700 transition-colors">
          <div className="flex justify-between items-center text-slate-400 font-mono text-xs">
            <span className="text-[11px] uppercase tracking-wider font-bold">MEAN RISK SCORE</span>
            <Activity className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-black text-slate-100 font-mono">
            {stats ? stats.average_risk_score.toFixed(1) : '28.4'} <span className="text-sm text-slate-500 font-normal">/ 100</span>
          </div>
          <div className="text-[11px] text-emerald-400 font-mono flex items-center gap-1.5">
            <TrendingUp className="w-3 h-3" />
            <span>Fused Multi-Factor Calibrated Score</span>
          </div>
        </div>
      </div>

      {/* Visual Charts: Activity Timeline & Risk Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Activity Over Timesteps Area Chart */}
        <div className="lg:col-span-2 p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4 shadow-xl">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-sm font-bold text-slate-100 font-mono flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-cyan-400" />
                TRANSACTION TRAFFIC VELOCITY & ALERT TRENDS ({timestepCount} TIMESTEPS)
              </h3>
              <p className="text-xs text-slate-400 font-mono mt-0.5">
                Timeline progression showing transaction volume and correlated suspicious alert spikes
              </p>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
              TEMPORAL PROGRESSION
            </span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="txGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00f2fe" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#00f2fe" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="alertGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="time_step" stroke="#64748b" tick={{ fontSize: 10, fontFamily: 'monospace' }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 10, fontFamily: 'monospace' }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '11px', fontFamily: 'monospace' }}
                />
                <Area type="monotone" dataKey="tx_count" stroke="#00f2fe" strokeWidth={2} fillOpacity={1} fill="url(#txGradient)" name="Total Transactions" />
                <Area type="monotone" dataKey="alert_count" stroke="#ef4444" strokeWidth={2} fillOpacity={1} fill="url(#alertGradient)" name="Flagged Alerts" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Risk Level Distribution Pie Chart */}
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4 shadow-xl flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-100 font-mono flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-purple-400" />
              RISK SEVERITY PROFILE
            </h3>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              Breakdown across calibrated severity tiers
            </p>
          </div>

          <div className="h-44 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={riskPieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={70}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {riskPieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '11px', fontFamily: 'monospace' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-2 gap-2 text-[10px] font-mono">
            <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span><span className="text-slate-300">Critical ({stats?.critical_alerts ?? 12})</span></div>
            <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span><span className="text-slate-300">High ({stats?.high_alerts ?? 45})</span></div>
            <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-cyan-400"></span><span className="text-slate-300">Medium ({stats?.medium_alerts ?? 161})</span></div>
            <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span><span className="text-slate-300">Low ({stats?.low_alerts ?? 4782})</span></div>
          </div>
        </div>
      </div>

      {/* Top Suspicious Investigation Leads Table */}
      <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4 shadow-xl">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-sm font-bold text-slate-100 font-mono flex items-center gap-2">
              <Flame className="w-4 h-4 text-rose-400" />
              TOP SUSPICIOUS INVESTIGATION LEADS
            </h3>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              Ranked by composite multi-factor risk score (Supervised XGBoost + Isolation Forest + Graph Centrality)
            </p>
          </div>
          <button
            onClick={() => onNavigate('alerts')}
            className="text-xs font-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-bold"
          >
            <span>View All Alerts Queue</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 text-[11px] uppercase tracking-wider">
                <th className="pb-3">Alert ID</th>
                <th className="pb-3">Target Entity</th>
                <th className="pb-3">Type</th>
                <th className="pb-3">Risk Score</th>
                <th className="pb-3">Severity</th>
                <th className="pb-3">Primary Forensic Driver</th>
                <th className="pb-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {stats?.top_risk_entities && stats.top_risk_entities.length > 0 ? (
                stats.top_risk_entities.slice(0, 5).map((entity) => (
                  <tr key={entity.alert_id} className="hover:bg-slate-800/40 transition-colors group">
                    <td className="py-3 font-bold text-cyan-400">{entity.alert_id}</td>
                    <td className="py-3 text-slate-200 font-bold">{entity.entity_id}</td>
                    <td className="py-3 text-slate-400">{entity.entity_type}</td>
                    <td className="py-3">
                      <span className="font-bold text-slate-100 text-sm">{entity.risk_score}</span>
                      <span className="text-[10px] text-slate-500"> / 100</span>
                    </td>
                    <td className="py-3">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        entity.risk_level === 'Critical' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40' :
                        entity.risk_level === 'High' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40' :
                        'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40'
                      }`}>
                        {entity.risk_level}
                      </span>
                    </td>
                    <td className="py-3 text-slate-300 max-w-xs truncate">{entity.top_reason}</td>
                    <td className="py-3 text-right">
                      <button
                        onClick={() => onSelectEntity(entity.alert_id, 'Alert')}
                        className="px-3 py-1 bg-cyan-500/15 hover:bg-cyan-500/25 text-cyan-300 border border-cyan-500/40 rounded-lg text-[11px] font-bold transition-colors"
                      >
                        Investigate
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="py-4 text-center text-slate-500">Loading threat leads...</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
