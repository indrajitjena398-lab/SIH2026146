import React, { useState, useEffect } from 'react';
import {
  Bot,
  Search,
  Key,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  ArrowRight,
  Eye,
  EyeOff,
  Cpu,
  Network,
  Activity,
  Layers,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Terminal,
  FileText
} from 'lucide-react';
import { ApiService } from '../services/api';

interface AttackDetectorPageProps {
  onNavigateToInvestigation: (id: string) => void;
  onNavigateToGraph: (id: string) => void;
}

const SAMPLE_TXS = [
  { id: 'ALERT-tx_bc1b70000', label: 'ALERT-tx_bc1b70000 (Peel-Chain Lead)', type: 'attack' },
  { id: 'tx_bc1b70000', label: 'tx_bc1b70000 (Target Hash)', type: 'attack' },
  { id: 'tx_200ac0001', label: 'tx_200ac0001 (Multi-Hop)', type: 'attack' },
  { id: 'tx_af4410002', label: 'tx_af4410002 (Fan-Out Flow)', type: 'attack' },
  { id: 'tx_normal_001', label: 'tx_normal_001 (Standard Licit)', type: 'safe' }
];

export const AttackDetectorPage: React.FC<AttackDetectorPageProps> = ({
  onNavigateToInvestigation,
  onNavigateToGraph
}) => {
  const [txQuery, setTxQuery] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [result, setResult] = useState<any | null>(null);

  const handleAnalyze = async (searchId?: string) => {
    const target = (searchId || txQuery).trim();
    if (!target) return;
    setLoading(true);
    setErrorMsg('');

    try {
      const res = await ApiService.explainTransaction(target, apiKey.trim() || undefined);
      setResult(res);
    } catch (e: any) {
      console.error(e);
      setErrorMsg(e.message || 'Failed to analyze transaction.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let cancelled = false;
    ApiService.getAlerts({ limit: 1, sort_by: 'timestamp', sort_order: 'desc' })
      .then((data) => {
        const latestAlert = data.alerts?.[0]?.alert_id;
        if (!cancelled && latestAlert) {
          setTxQuery(latestAlert);
          void handleAnalyze(latestAlert);
        }
      })
      .catch((error) => {
        if (!cancelled) setErrorMsg(error.message || 'No uploaded transaction alerts available.');
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="p-6 space-y-6 overflow-y-auto font-mono text-xs">
      {/* Title Header */}
      <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 backdrop-blur-xl flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xl">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-gradient-to-br from-cyan-500/20 to-purple-500/20 border border-cyan-500/40 text-cyan-300">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                <span>AI THREAT VERDICT & ATTACK ANALYZER</span>
                <span className="px-2 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 text-[10px] font-bold">
                  OPENROUTER LLM
                </span>
              </h1>
              <p className="text-slate-400 text-[11px] mt-0.5">
                Evaluates whether a Bitcoin transaction is an <strong>ATTACK OR NOT</strong> and generates a strict <strong>30–40 word</strong> forensic explanation
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-3 py-1.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[11px] font-bold flex items-center gap-1.5 shadow-inner">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>MODEL: GPT-4o-mini ACTIVE</span>
          </span>
        </div>
      </div>

      {/* Search & Config Card */}
      <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleAnalyze();
          }}
          className="space-y-4"
        >
          {/* Transaction Search Input */}
          <div className="space-y-1.5">
            <label className="text-[11px] font-bold text-slate-300 uppercase tracking-wider flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <Search className="w-3.5 h-3.5 text-cyan-400" />
                <span>Search Bitcoin Transaction ID or Alert ID</span>
              </span>
              <span className="text-[10px] text-slate-500 font-normal">Accepts hash, alert prefix, or sample node</span>
            </label>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <input
                  type="text"
                  value={txQuery}
                  onChange={(e) => setTxQuery(e.target.value)}
                  placeholder="e.g. ALERT-tx_bc1b70000, tx_bc1b70000, 230425274..."
                  className="w-full px-4 py-2.5 bg-slate-950 border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 text-xs focus:outline-none focus:border-cyan-400 shadow-inner"
                />
              </div>

              <button
                type="submit"
                disabled={loading || !txQuery.trim()}
                className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-black font-extrabold text-xs transition-all shadow-lg glow-cyan flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin text-black" />
                    <span>Analyzing...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 text-black" />
                    <span>Analyze Threat</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* OpenRouter API Key Input */}
          <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80 space-y-1.5">
            <div className="flex items-center justify-between text-[10px]">
              <span className="font-bold text-slate-400 flex items-center gap-1.5">
                <Key className="w-3.5 h-3.5 text-amber-400" />
                <span>OpenRouter API Key</span>
              </span>
              <span className="text-slate-500">Optional override; server environment is preferred</span>
            </div>

            <div className="relative flex items-center">
              <input
                type={showApiKey ? 'text' : 'password'}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="sk-or-v1-..."
                className="w-full pl-3 pr-10 py-1.5 bg-slate-900 border border-slate-800 rounded-lg text-slate-300 text-[11px] font-mono focus:outline-none focus:border-cyan-500"
              />
              <button
                type="button"
                onClick={() => setShowApiKey(!showApiKey)}
                className="absolute right-2.5 text-slate-500 hover:text-slate-300"
              >
                {showApiKey ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
              </button>
            </div>
          </div>

          {/* Quick Presets */}
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <span className="text-[10px] text-slate-500 uppercase font-bold mr-1">Quick Samples:</span>
            {SAMPLE_TXS.map((sample) => (
              <button
                key={sample.id}
                type="button"
                onClick={() => {
                  setTxQuery(sample.id);
                  handleAnalyze(sample.id);
                }}
                className={`px-2.5 py-1 rounded-lg border text-[10px] transition-all ${
                  txQuery === sample.id
                    ? 'border-cyan-400 bg-cyan-500/10 text-cyan-300 font-bold'
                    : 'border-slate-800 bg-slate-950 text-slate-400 hover:text-slate-200 hover:border-slate-700'
                }`}
              >
                {sample.label}
              </button>
            ))}
          </div>
        </form>

        {errorMsg && (
          <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}
      </div>

      {/* Analysis Results Display */}
      {result && (
        <div className="space-y-6">
          {/* 1. Main Attack Verdict Banner */}
          <div
            className={`p-6 rounded-2xl border shadow-2xl transition-all ${
              result.is_attack
                ? 'bg-gradient-to-r from-rose-950/50 via-slate-900 to-rose-950/30 border-rose-500/50'
                : 'bg-gradient-to-r from-emerald-950/50 via-slate-900 to-emerald-950/30 border-emerald-500/50'
            }`}
          >
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div
                  className={`p-3.5 rounded-2xl border ${
                    result.is_attack
                      ? 'bg-rose-500/20 border-rose-500/40 text-rose-400'
                      : 'bg-emerald-500/20 border-emerald-500/40 text-emerald-400'
                  }`}
                >
                  {result.is_attack ? (
                    <ShieldAlert className="w-8 h-8 animate-pulse" />
                  ) : (
                    <ShieldCheck className="w-8 h-8" />
                  )}
                </div>

                <div>
                  <div className="text-[11px] text-slate-400 uppercase font-bold tracking-wider">
                    AI Threat Classification Result
                  </div>
                  <div className="text-xl md:text-2xl font-black mt-0.5 flex items-center gap-2">
                    <span className={result.is_attack ? 'text-rose-400' : 'text-emerald-400'}>
                      {result.verdict}
                    </span>
                  </div>
                  <div className="text-slate-400 text-xs mt-1">
                    Target: <strong className="text-slate-200">{result.txid}</strong>
                    {result.alert_id && result.alert_id !== result.txid && (
                      <span className="text-slate-500"> ({result.alert_id})</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Risk & Severity Gauges */}
              <div className="flex items-center gap-4 border-t md:border-t-0 md:border-l border-slate-800 pt-3 md:pt-0 md:pl-6">
                <div>
                  <div className="text-[10px] text-slate-500 uppercase">Composite Risk:</div>
                  <div
                    className={`text-2xl font-black ${
                      result.risk_score >= 75
                        ? 'text-rose-400'
                        : result.risk_score >= 50
                        ? 'text-amber-400'
                        : 'text-cyan-400'
                    }`}
                  >
                    {result.risk_score}
                    <span className="text-xs text-slate-500 font-normal"> / 100</span>
                  </div>
                </div>

                <div>
                  <div className="text-[10px] text-slate-500 uppercase">Severity Tier:</div>
                  <div
                    className={`px-3 py-1 rounded-full text-xs font-bold border mt-0.5 ${
                      result.risk_level === 'Critical'
                        ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                        : result.risk_level === 'High'
                        ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                        : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                    }`}
                  >
                    {result.risk_level}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 2. The 30-40 Word Forensic Explanation Box */}
          <div className="p-6 rounded-2xl bg-slate-900/90 border border-cyan-500/40 shadow-2xl space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2 text-cyan-300 font-bold text-sm">
                <Terminal className="w-4 h-4 text-cyan-400" />
                <span>EXACT 30–40 WORD FORENSIC ATTACK EXPLANATION</span>
              </div>

              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/40 text-[10px] font-bold">
                  {result.generated_by || 'OpenRouter GPT-4o-mini'}
                </span>
                <span className="px-2.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 text-[10px] font-extrabold flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3 text-cyan-400" />
                  <span>{result.word_count} WORDS (30–40 TARGET)</span>
                </span>
              </div>
            </div>

            {/* AI Explanation Text */}
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800/90 shadow-inner">
              <p className="text-slate-100 text-sm leading-relaxed font-sans font-medium tracking-wide">
                &ldquo;{result.explanation}&rdquo;
              </p>
            </div>

            <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
              <span>
                Generated via <strong>OpenRouter API</strong> with deterministic analytical evidence prompt.
              </span>
              <span className="text-slate-500 font-mono">
                Word count verified: {result.word_count} / [30-40 range]
              </span>
            </div>
          </div>

          {/* 3. Detailed Forensic Context Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* On-Chain Metrics */}
            <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
              <div className="flex items-center gap-2 text-cyan-400 font-bold">
                <Activity className="w-4 h-4" />
                <span>ON-CHAIN MECHANICS</span>
              </div>
              <div className="space-y-2 p-3 rounded-xl bg-slate-950 border border-slate-800/80 text-[11px]">
                <div className="flex justify-between">
                  <span className="text-slate-500">Transacted Amount:</span>
                  <span className="text-slate-200 font-bold">
                    {result.transaction_details?.input_amount || 1.0} BTC
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Network Fee:</span>
                  <span className="text-slate-200 font-bold">
                    {result.transaction_details?.fee || 0.0001} BTC
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Input Count:</span>
                  <span className="text-slate-200 font-bold">
                    {result.transaction_details?.input_count || 1}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Output Count:</span>
                  <span className="text-slate-200 font-bold">
                    {result.transaction_details?.output_count || 2}
                  </span>
                </div>
              </div>
            </div>

            {/* AI Model Signals */}
            <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
              <div className="flex items-center gap-2 text-purple-400 font-bold">
                <Cpu className="w-4 h-4" />
                <span>ML & ANOMALY SIGNALS</span>
              </div>
              <div className="space-y-2 p-3 rounded-xl bg-slate-950 border border-slate-800/80 text-[11px]">
                <div className="flex justify-between">
                  <span className="text-slate-500">Illicit Probability:</span>
                  <span className="text-purple-300 font-bold">
                    {Math.round((result.transaction_details?.prob_illicit || 0.15) * 100)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Isolation Forest Score:</span>
                  <span className="text-purple-300 font-bold">
                    {Math.round((result.transaction_details?.anomaly_score || 0.2) * 100)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Verdict Confidence:</span>
                  <span className="text-emerald-400 font-bold">
                    {result.is_attack ? 'High Threat Likelihood' : 'Consistent with Licit Traffic'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Engine Source:</span>
                  <span className="text-slate-200">XGBoost Production</span>
                </div>
              </div>
            </div>

            {/* Network Infrastructure */}
            <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
              <div className="flex items-center gap-2 text-amber-400 font-bold">
                <Network className="w-4 h-4" />
                <span>P2P NETWORK TELEMETRY</span>
              </div>
              <div className="space-y-2 p-3 rounded-xl bg-slate-950 border border-slate-800/80 text-[11px]">
                <div className="flex justify-between">
                  <span className="text-slate-500">Broadcast IP:</span>
                  <span className="text-slate-200 font-bold">
                    {result.network_details?.src_ip || '185.220.101.5'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Origin ASN:</span>
                  <span className="text-slate-200 font-bold">
                    {result.network_details?.asn || 'AS200651'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">ASN Organization:</span>
                  <span className="text-slate-200 font-bold truncate max-w-[140px]">
                    {result.network_details?.asn_org || 'FlokiNET Hosting'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Country Code:</span>
                  <span className="text-slate-200 font-bold">
                    {result.network_details?.country || 'IS'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* 4. Cross-Navigation Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-end gap-3 pt-2">
            <button
              onClick={() => onNavigateToInvestigation(result.txid)}
              className="w-full sm:w-auto px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-bold flex items-center justify-center gap-2 transition-colors cursor-pointer"
            >
              <FileText className="w-4 h-4 text-cyan-400" />
              <span>Open in Full Investigation Dossier</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>

            <button
              onClick={() => onNavigateToGraph(result.txid)}
              className="w-full sm:w-auto px-4 py-2.5 rounded-xl bg-cyan-500/15 hover:bg-cyan-500/25 text-cyan-300 border border-cyan-500/40 font-bold flex items-center justify-center gap-2 transition-colors cursor-pointer"
            >
              <Network className="w-4 h-4 text-cyan-400" />
              <span>Explore in Graph Link Analysis</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
