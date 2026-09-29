import React, { useState, useEffect } from 'react';
import {
  SearchCode,
  ShieldAlert,
  Flame,
  Globe,
  Radio,
  FileText,
  Download,
  Share2,
  ArrowRight,
  Clock,
  Layers,
  Activity,
  Cpu,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Network,
  Terminal,
  FileCheck
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell
} from 'recharts';
import { AlertDetail, TransactionDetail } from '../types';
import { ApiService } from '../services/api';

interface InvestigationPageProps {
  selectedAlertId: string | null;
  onNavigateToGraph: (entityId: string) => void;
}

export const InvestigationPage: React.FC<InvestigationPageProps> = ({ selectedAlertId, onNavigateToGraph }) => {
  const [queryInput, setQueryInput] = useState(selectedAlertId || '');
  const [dossier, setDossier] = useState<AlertDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [explanation, setExplanation] = useState<Awaited<ReturnType<typeof ApiService.explainTransaction>> | null>(null);
  const [explanationLoading, setExplanationLoading] = useState(false);

  const loadDossier = async (id: string) => {
    if (!id || !id.trim()) return;
    setLoading(true);
    setErrorMsg('');
    const cleanId = id.trim();
    const upperId = cleanId.toUpperCase();
    try {
      if (upperId.startsWith('ALT-') || upperId.startsWith('ALERT-')) {
        let data: any = null;
        try {
          data = await ApiService.getAlertDetail(cleanId);
        } catch {
          const candidateTx = cleanId.replace(/^(ALT-|ALERT-)/i, '');
          data = await ApiService.getAlertDetail(candidateTx);
        }
        setDossier(data);
        if (data?.transaction_id || data?.entity_id) {
          const targetTx = data.transaction_id || data.entity_id;
          setExplanationLoading(true);
          try {
            setExplanation(await ApiService.explainTransaction(targetTx));
          } catch {
            setExplanation(null);
          } finally {
            setExplanationLoading(false);
          }
        }
      } else {
        let tx: any = null;
        try {
          tx = await ApiService.getTransaction(cleanId);
        } catch (err) {
          const alertData = await ApiService.getAlertDetail(cleanId);
          if (alertData) {
            setDossier(alertData);
            if (alertData.transaction_id) {
              setExplanationLoading(true);
              try {
                setExplanation(await ApiService.explainTransaction(alertData.transaction_id));
              } catch {
                setExplanation(null);
              } finally {
                setExplanationLoading(false);
              }
            }
            return;
          }
          throw err;
        }

        setExplanation(null);
        setDossier({
          alert_id: cleanId.startsWith('ALERT-') ? cleanId : `ALT-${cleanId.slice(-6).toUpperCase()}`,
          entity_id: tx.txid,
          entity_type: 'Transaction',
          transaction_id: tx.txid,
          risk_score: tx.risk_score,
          risk_level: tx.risk_level as any,
          classification_probability: tx.prob_illicit,
          anomaly_score: tx.anomaly_score,
          top_reason: tx.reasons[0] || 'Investigative query lead',
          top_reasons: tx.reasons,
          status: 'Under Investigation',
          timestamp: tx.timestamp,
          model_version: 'v1.0-xgboost',
          evidence: { graph: { in_degree: tx.input_count, out_degree: tx.output_count, neighbor_illicit_ratio: 0.25 } },
          shap_contributions: tx.shap_contributions,
          transaction_details: tx,
          network_details: tx.network_events
        });
        setExplanationLoading(true);
        try {
          setExplanation(await ApiService.explainTransaction(tx.txid));
        } catch {
          setExplanation(null);
        } finally {
          setExplanationLoading(false);
        }
      }
    } catch (e: any) {
      console.error(e);
      setErrorMsg(e.message || 'Entity or Alert ID not found in database.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedAlertId) {
      setQueryInput(selectedAlertId);
      loadDossier(selectedAlertId);
    } else {
      ApiService.getAlerts({ limit: 1 }).then(res => {
        if (res.alerts.length > 0) {
          const firstId = res.alerts[0].alert_id;
          setQueryInput(firstId);
          loadDossier(firstId);
        }
      });
    }
  }, [selectedAlertId]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadDossier(queryInput);
  };

  return (
    <div className="p-6 space-y-6 overflow-y-auto">
      {/* Top Search & Actions Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/80 backdrop-blur-xl p-4 rounded-2xl border border-slate-800 shadow-xl">
        <form onSubmit={handleSearch} className="flex-1 flex items-center gap-2 max-w-xl">
          <div className="relative flex-1">
            <SearchCode className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Enter Alert ID (e.g. ALT-857B94DE) or TXID..."
              value={queryInput}
              onChange={(e) => setQueryInput(e.target.value)}
              className="w-full pl-10 pr-4 py-2 text-xs bg-slate-950/90 border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 font-mono focus:outline-none focus:border-cyan-400 shadow-inner"
            />
          </div>
          <button
            type="submit"
            className="px-5 py-2 bg-gradient-to-r from-cyan-500 to-sky-400 hover:from-cyan-400 hover:to-sky-300 text-black text-xs font-mono font-bold rounded-xl transition-all glow-cyan shadow-lg"
          >
            Investigate
          </button>
        </form>

        {dossier && (
          <div className="flex items-center gap-2 font-mono text-xs">
            <a
              href={`/api/export/dossier/${dossier.alert_id}`}
              target="_blank"
              rel="noreferrer"
              className="px-4 py-2 rounded-xl bg-rose-500/15 hover:bg-rose-500/25 text-rose-300 border border-rose-500/40 font-bold flex items-center gap-2 transition-colors shadow-sm"
            >
              <Download className="w-4 h-4" />
              <span>Export Dossier (HTML)</span>
            </a>
            <button
              onClick={() => onNavigateToGraph(dossier.transaction_id)}
              className="px-4 py-2 rounded-xl bg-purple-500/15 hover:bg-purple-500/25 text-purple-300 border border-purple-500/40 font-bold flex items-center gap-2 transition-colors shadow-sm"
            >
              <Globe className="w-4 h-4" />
              <span>Explore Graph Canvas</span>
            </button>
          </div>
        )}
      </div>

      {loading && (
        <div className="p-16 text-center text-cyan-400 font-mono animate-pulse flex flex-col items-center justify-center gap-3">
          <Activity className="w-8 h-8 animate-spin" />
          <div className="text-sm font-bold tracking-wider">COMPUTING FORENSIC SHAP ATTRIBUTIONS & CORRELATING TOPOLOGY...</div>
        </div>
      )}

      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-500/15 border border-rose-500/40 text-rose-400 font-mono text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {dossier && !loading && (
        <div className="space-y-6">
          {explanationLoading && (
            <div className="p-5 rounded-2xl bg-slate-900/90 border border-cyan-500/30 text-cyan-300 font-mono text-xs animate-pulse">
              Generating transaction verdict and plain-English explanation...
            </div>
          )}

          {explanation && (
            <div className={`p-6 rounded-2xl border shadow-xl ${explanation.is_attack ? 'bg-rose-950/30 border-rose-500/40' : 'bg-emerald-950/30 border-emerald-500/40'}`}>
              <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-widest text-slate-400">
                    {explanation.is_attack ? <ShieldAlert className="w-4 h-4 text-rose-400" /> : <CheckCircle className="w-4 h-4 text-emerald-400" />}
                    Transaction verdict
                  </div>
                  <h3 className={`mt-2 text-xl font-black font-mono ${explanation.is_attack ? 'text-rose-300' : 'text-emerald-300'}`}>
                    {explanation.verdict}
                  </h3>
                  <p className="mt-3 max-w-4xl text-sm leading-7 text-slate-200">{explanation.explanation}</p>
                </div>
                <span className="shrink-0 px-3 py-1 rounded-full border border-slate-700 bg-slate-950/70 text-[10px] font-mono text-slate-400">
                  {explanation.word_count} words
                </span>
              </div>
            </div>
          )}

          {/* Main Case Header Dossier Card */}
          <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800/90 backdrop-blur-xl shadow-2xl space-y-6">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 border-b border-slate-800/90 pb-6">
              <div>
                <div className="flex items-center gap-2.5 mb-2">
                  <span className="text-[10px] uppercase font-extrabold tracking-widest text-slate-400 font-mono px-2 py-0.5 rounded bg-slate-800/80 border border-slate-700">
                    INVESTIGATION DOSSIER
                  </span>
                  <span className="text-sm font-bold text-cyan-400 font-mono">{dossier.alert_id}</span>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold font-mono bg-purple-500/20 text-purple-300 border border-purple-500/40">
                    STATUS: {dossier.status.toUpperCase()}
                  </span>
                </div>
                <h2 className="text-2xl font-black text-slate-100 font-mono tracking-tight flex items-center gap-3">
                  <span>TARGET TXID:</span>
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-sky-300 to-purple-300">
                    {dossier.transaction_id}
                  </span>
                </h2>
                <div className="text-xs text-slate-400 font-mono mt-1.5 flex flex-wrap items-center gap-4">
                  <span className="flex items-center gap-1"><Clock className="w-3.5 h-3.5 text-slate-500" /> {dossier.timestamp}</span>
                  <span>&bull;</span>
                  <span>Model: <strong className="text-slate-300">{dossier.model_version}</strong></span>
                  <span>&bull;</span>
                  <span>Decision Support: <strong className="text-amber-400 font-bold">Investigation Lead</strong></span>
                </div>
              </div>

              {/* Composite Score Meter */}
              <div className="flex items-center gap-5 bg-slate-950/90 p-4 rounded-2xl border border-slate-800 shadow-inner">
                <div className="text-right font-mono">
                  <div className="text-[10px] text-slate-400 uppercase tracking-widest font-bold">COMPOSITE RISK</div>
                  <div className="text-xs font-bold text-slate-200 mt-0.5">{dossier.risk_level.toUpperCase()} SEVERITY</div>
                  <div className="text-[10px] text-slate-500">Calibrated (0-100)</div>
                </div>
                <div className={`text-4xl font-black font-mono px-5 py-2.5 rounded-xl shadow-lg ${
                  dossier.risk_level === 'Critical' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/50 glow-rose' :
                  dossier.risk_level === 'High' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/50 glow-amber' :
                  'bg-cyan-500/20 text-cyan-400 border border-cyan-500/50 glow-cyan'
                }`}>
                  {dossier.risk_score}
                </div>
              </div>
            </div>

            {/* Multi-Modal Score Components Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 font-mono">
              <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800/90 space-y-1">
                <div className="text-[10px] text-slate-400 uppercase">ML CLASSIFICATION (40%)</div>
                <div className="text-2xl font-bold text-rose-400">{Math.round(dossier.classification_probability * 100)}%</div>
                <div className="text-[10px] text-slate-500">Supervised XGBoost</div>
              </div>

              <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800/90 space-y-1">
                <div className="text-[10px] text-slate-400 uppercase">ANOMALY SCORE (20%)</div>
                <div className="text-2xl font-bold text-amber-400">{Math.round(dossier.anomaly_score * 100)}%</div>
                <div className="text-[10px] text-slate-500">Isolation Forest Outlier</div>
              </div>

              <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800/90 space-y-1">
                <div className="text-[10px] text-slate-400 uppercase">GRAPH RISK (20%)</div>
                <div className="text-2xl font-bold text-purple-400">
                  {Math.round((dossier.evidence?.graph?.neighbor_illicit_ratio || 0.3) * 100)}%
                </div>
                <div className="text-[10px] text-slate-500">PageRank & Illicit Neighbors</div>
              </div>

              <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800/90 space-y-1">
                <div className="text-[10px] text-slate-400 uppercase">NETWORK RISK (20%)</div>
                <div className="text-2xl font-bold text-cyan-400">
                  {dossier.evidence?.network?.has_high_risk_asn ? '85%' : '20%'}
                </div>
                <div className="text-[10px] text-slate-500">ASN & Connection Burst</div>
              </div>
            </div>
          </div>

          {/* Section: Forensic Evidence & Decision Reasoning */}
          <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4 shadow-xl">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-100 font-mono flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-rose-400" />
                FORENSIC EVIDENCE & DECISION RATIONALES
              </h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                MULTI-MODAL SYNTHESIS
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono">
              The AI platform synthesized the following evidentiary drivers for this investigation lead:
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 font-mono text-xs">
              {dossier.top_reasons.map((reason, idx) => (
                <div key={idx} className="p-3.5 rounded-xl bg-slate-950/90 border border-slate-800 flex items-start gap-3 shadow-inner">
                  <span className="w-6 h-6 rounded-full bg-rose-500/20 text-rose-400 flex items-center justify-center shrink-0 text-xs font-bold border border-rose-500/40">
                    {idx + 1}
                  </span>
                  <span className="text-slate-200 leading-relaxed text-xs">{reason}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Explainable AI: TreeSHAP Feature Attribution Waterfall */}
          <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4 shadow-xl">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-sm font-bold text-slate-100 font-mono flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-cyan-400" />
                  SHAP LOCAL FEATURE ATTRIBUTION (EXPLAINABLE AI)
                </h3>
                <p className="text-xs text-slate-400 font-mono mt-0.5">
                  Exact TreeSHAP marginal push towards Illicit (+) vs Licit (-) prediction
                </p>
              </div>
              <span className="text-[10px] font-mono px-2.5 py-1 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 font-bold">
                XGBOOST TREESHAP
              </span>
            </div>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={dossier.shap_contributions}
                  layout="vertical"
                  margin={{ top: 10, right: 30, left: 140, bottom: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                  <XAxis type="number" stroke="#64748b" tick={{ fontSize: 10, fontFamily: 'monospace' }} />
                  <YAxis type="category" dataKey="feature" stroke="#64748b" tick={{ fontSize: 10, fontFamily: 'monospace' }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '11px', fontFamily: 'monospace' }}
                  />
                  <Bar dataKey="shap_value" name="SHAP Contribution">
                    {dossier.shap_contributions?.map((entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={entry.shap_value >= 0 ? '#ef4444' : '#10b981'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Transaction Metadata & Network Telemetry Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Blockchain On-Chain Mechanics */}
            <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3 font-mono text-xs shadow-xl">
              <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                <Layers className="w-4 h-4 text-purple-400" />
                BLOCKCHAIN ON-CHAIN MECHANICS
              </h3>
              <div className="divide-y divide-slate-800/80">
                <div className="py-2.5 flex justify-between"><span className="text-slate-400">Time Step / Epoch:</span><span className="text-slate-200 font-bold">TS {dossier.transaction_details?.time_step || 1}</span></div>
                <div className="py-2.5 flex justify-between"><span className="text-slate-400">Input Transacted Volume:</span><span className="text-cyan-300 font-bold">{dossier.transaction_details?.input_amount || 1.0} BTC</span></div>
                <div className="py-2.5 flex justify-between"><span className="text-slate-400">Output Transacted Volume:</span><span className="text-cyan-300 font-bold">{dossier.transaction_details?.output_amount || 1.0} BTC</span></div>
                <div className="py-2.5 flex justify-between"><span className="text-slate-400">Transaction Fee:</span><span className="text-amber-400 font-bold">{dossier.transaction_details?.fee || 0.0001} BTC</span></div>
                <div className="py-2.5 flex justify-between"><span className="text-slate-400">Fan-In (Inputs):</span><span className="text-slate-200">{dossier.transaction_details?.input_count || 1} Wallets</span></div>
                <div className="py-2.5 flex justify-between"><span className="text-slate-400">Fan-Out (Peel Outputs):</span><span className="text-slate-200">{dossier.transaction_details?.output_count || 2} Wallets</span></div>
              </div>
            </div>

            {/* Correlated P2P Network Telemetry */}
            <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3 font-mono text-xs flex flex-col justify-between shadow-xl">
              <div>
                <div className="flex justify-between items-center mb-1">
                  <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                    <Radio className="w-4 h-4 text-cyan-400" />
                    P2P NETWORK TELEMETRY
                  </h3>
                  <span className="text-[10px] text-slate-500 font-bold">SYNTHETIC LAYER</span>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-[11px] mt-2">
                    <thead>
                      <tr className="border-b border-slate-800 text-slate-400">
                        <th className="pb-1.5">Source IP</th>
                        <th className="pb-1.5">Country</th>
                        <th className="pb-1.5">ASN</th>
                        <th className="pb-1.5">Scenario</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {dossier.network_details && dossier.network_details.length > 0 ? (
                        dossier.network_details.slice(0, 5).map((n: any, i: number) => (
                          <tr key={i} className="hover:bg-slate-800/30">
                            <td className="py-1.5 text-cyan-400 font-semibold">{n.src_ip}</td>
                            <td className="py-1.5">{n.geo_country}</td>
                            <td className="py-1.5 font-bold text-slate-300">{n.asn}</td>
                            <td className="py-1.5 text-slate-400">{n.scenario}</td>
                          </tr>
                        ))
                      ) : (
                        <tr><td colSpan={4} className="py-2 text-slate-500">No network events recorded.</td></tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 text-[10px] text-slate-500">
                Disclaimer: Synthetic network-layer metadata generated for system integration and demonstration.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
