import React, { useState, useEffect } from 'react';
import {
  Sliders,
  CheckCircle2,
  Server,
  Database,
  Cpu,
  Globe,
  Play,
  Flame,
  Shield,
  Activity
} from 'lucide-react';
import { ApiService } from '../services/api';

interface SystemStatusPageProps {
  activeThreshold: number;
  onUpdateThreshold: (val: number) => void;
}

export const SystemStatusPage: React.FC<SystemStatusPageProps> = ({ activeThreshold, onUpdateThreshold }) => {
  const [health, setHealth] = useState<any>(null);
  const [tempThreshold, setTempThreshold] = useState<number>(activeThreshold);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Simulation Playground State
  const [simTxid, setSimTxid] = useState('sim_tx_001');
  const [simAmount, setSimAmount] = useState(5.0);
  const [simFee, setSimFee] = useState(0.005);
  const [simInCount, setSimInCount] = useState(1);
  const [simOutCount, setSimOutCount] = useState(12);
  const [simAsn, setSimAsn] = useState('AS200651');
  const [simResult, setSimResult] = useState<any>(null);
  const [simLoading, setSimLoading] = useState(false);

  useEffect(() => {
    ApiService.getHealth()
      .then(res => setHealth(res))
      .catch(err => console.error(err));
  }, []);

  const handleSaveThreshold = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await ApiService.updateThreshold({ min_alert_threshold: tempThreshold });
      onUpdateThreshold(tempThreshold);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (e) {
      console.error(e);
    }
  };

  const handleRunSim = async (e: React.FormEvent) => {
    e.preventDefault();
    setSimLoading(true);
    try {
      const res = await ApiService.predictCustom({
        txid: simTxid,
        input_amount: simAmount,
        output_amount: simAmount * 0.99,
        fee: simFee,
        input_count: simInCount,
        output_count: simOutCount,
        asn: simAsn
      });
      setSimResult(res);
    } catch (e) {
      console.error(e);
    } finally {
      setSimLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6 overflow-y-auto">
      {/* Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/80 p-4 rounded-xl border border-slate-800">
        <div>
          <h1 className="text-lg font-bold text-slate-100 font-mono flex items-center gap-2">
            <Sliders className="w-5 h-5 text-cyan-400" />
            SYSTEM STATUS & OPERATIONS CONSOLE
          </h1>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Engine uptime, DuckDB embedded storage, Model registry, and Live Simulation Playground
          </p>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="text-emerald-400 font-bold">SYSTEM OPERATIONAL &bull; UPTIME: {health?.uptime_seconds || 0}s</span>
        </div>
      </div>

      {/* Component Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 font-mono text-xs">
        {/* Database Status */}
        <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-cyan-400 font-bold">
            <Database className="w-4 h-4" />
            <h3>DUCKDB ANALYTICAL STORE</h3>
          </div>
          <div className="space-y-1.5 text-slate-300">
            <div className="flex justify-between"><span className="text-slate-500">Database Path:</span><span>data/bitcoin.duckdb</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Storage Engine:</span><span>DuckDB v1.1 Embedded</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Transactions:</span><span>5,000 Records</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Graph Entities:</span><span>15,053 Nodes</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Graph Edges:</span><span>27,882 Relationships</span></div>
          </div>
        </div>

        {/* ML Model Registry */}
        <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-purple-400 font-bold">
            <Cpu className="w-4 h-4" />
            <h3>ML MODEL REGISTRY</h3>
          </div>
          <div className="space-y-1.5 text-slate-300">
            <div className="flex justify-between"><span className="text-slate-500">Active Classifier:</span><span className="text-cyan-400 font-bold">XGBoost Classifier</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Anomaly Detector:</span><span>Isolation Forest (Contam 0.05)</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Explainability:</span><span>TreeSHAP Local Engine</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Temporal Split:</span><span>Strict TS 1-34/35-41/42-49</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Feature Count:</span><span>190 Engineered Feats</span></div>
          </div>
        </div>

        {/* GeoIP Engine */}
        <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-emerald-400 font-bold">
            <Globe className="w-4 h-4" />
            <h3>GEOIP & ASN ENRICHMENT</h3>
          </div>
          <div className="space-y-1.5 text-slate-300">
            <div className="flex justify-between"><span className="text-slate-500">Resolver Mode:</span><span className="text-emerald-400 font-bold">Local Offline Registry</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Memory Cache:</span><span>LRU Cache (32k Max)</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Private IP Support:</span><span>RFC 1918 Filter</span></div>
            <div className="flex justify-between"><span className="text-slate-500">IPv4 & IPv6:</span><span>Supported</span></div>
            <div className="flex justify-between"><span className="text-slate-500">External Network:</span><span className="text-slate-400">Zero Cloud Egress</span></div>
          </div>
        </div>
      </div>

      {/* Threshold Configuration & Simulation Playground */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Operational Threshold Config */}
        <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-4 font-mono text-xs">
          <div className="flex justify-between items-center">
            <h3 className="text-sm font-bold text-slate-200">OPERATIONAL ALERT THRESHOLD TUNING</h3>
            {saveSuccess && <span className="text-emerald-400 font-bold flex items-center gap-1"><CheckCircle2 className="w-3.5 h-3.5" /> Saved</span>}
          </div>
          <p className="text-slate-400 text-[11px]">
            Adjust the minimum composite risk score required to trigger an alert lead for investigator triage.
          </p>

          <form onSubmit={handleSaveThreshold} className="space-y-4 pt-2">
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-slate-300">Minimum Alert Risk Score:</span>
                <span className="text-cyan-400 font-bold text-sm">{tempThreshold} / 100</span>
              </div>
              <input
                type="range"
                min="10"
                max="80"
                step="5"
                value={tempThreshold}
                onChange={(e) => setTempThreshold(Number(e.target.value))}
                className="w-full accent-cyan-400"
              />
            </div>

            <div className="p-3 rounded bg-slate-950 border border-slate-800 space-y-1 text-[11px] text-slate-400">
              <div className="flex justify-between"><span>Active Operating Tier:</span><strong className="text-slate-200">{tempThreshold >= 75 ? 'Critical Only' : (tempThreshold >= 50 ? 'High & Critical' : 'Medium, High & Critical')}</strong></div>
              <div className="flex justify-between"><span>Classification Weight:</span><span>40%</span></div>
              <div className="flex justify-between"><span>Anomaly Score Weight:</span><span>20%</span></div>
              <div className="flex justify-between"><span>Graph Topology Weight:</span><span>20%</span></div>
              <div className="flex justify-between"><span>Network Telemetry Weight:</span><span>20%</span></div>
            </div>

            <button
              type="submit"
              className="w-full py-2 rounded bg-cyan-500 hover:bg-cyan-400 text-black font-bold font-mono transition-colors"
            >
              Update Operational Threshold
            </button>
          </form>
        </div>

        {/* Real-Time Prediction Simulation Playground */}
        <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-4 font-mono text-xs">
          <div className="flex justify-between items-center">
            <h3 className="text-sm font-bold text-slate-200">REAL-TIME INFERENCE SIMULATION</h3>
            <span className="text-[10px] text-purple-400 font-bold">XGBOOST + SHAP LIVE</span>
          </div>

          <form onSubmit={handleRunSim} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[10px] text-slate-400 block mb-1">Transacted BTC Amount</label>
                <input
                  type="number"
                  step="0.1"
                  value={simAmount}
                  onChange={(e) => setSimAmount(Number(e.target.value))}
                  className="w-full px-2.5 py-1 text-xs bg-slate-950 border border-slate-700 rounded text-slate-200"
                />
              </div>
              <div>
                <label className="text-[10px] text-slate-400 block mb-1">Transaction Fee (BTC)</label>
                <input
                  type="number"
                  step="0.0001"
                  value={simFee}
                  onChange={(e) => setSimFee(Number(e.target.value))}
                  className="w-full px-2.5 py-1 text-xs bg-slate-950 border border-slate-700 rounded text-slate-200"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[10px] text-slate-400 block mb-1">Fan-In (Inputs)</label>
                <input
                  type="number"
                  value={simInCount}
                  onChange={(e) => setSimInCount(Number(e.target.value))}
                  className="w-full px-2.5 py-1 text-xs bg-slate-950 border border-slate-700 rounded text-slate-200"
                />
              </div>
              <div>
                <label className="text-[10px] text-slate-400 block mb-1">Fan-Out (Outputs / Peel Chain)</label>
                <input
                  type="number"
                  value={simOutCount}
                  onChange={(e) => setSimOutCount(Number(e.target.value))}
                  className="w-full px-2.5 py-1 text-xs bg-slate-950 border border-slate-700 rounded text-slate-200"
                />
              </div>
            </div>

            <div>
              <label className="text-[10px] text-slate-400 block mb-1">Network Route ASN</label>
              <select
                value={simAsn}
                onChange={(e) => setSimAsn(e.target.value)}
                className="w-full px-2.5 py-1 text-xs bg-slate-950 border border-slate-700 rounded text-slate-200"
              >
                <option value="AS200651">AS200651 (Tor Exit Node Network — High Risk)</option>
                <option value="AS60531">AS60531 (Flokinet Bulletproof Hosting — High Risk)</option>
                <option value="AS15169">AS15169 (Google Cloud — Standard)</option>
                <option value="AS24940">AS24940 (Hetzner Datacenter — Standard)</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={simLoading}
              className="w-full py-2 rounded bg-purple-600 hover:bg-purple-500 text-white font-bold transition-colors flex items-center justify-center gap-2"
            >
              <Play className="w-3.5 h-3.5" />
              <span>{simLoading ? 'Executing Inference...' : 'Simulate & Calculate Risk Score'}</span>
            </button>
          </form>

          {/* Simulation Output Card */}
          {simResult && (
            <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800 space-y-2 mt-2">
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Computed Risk Score:</span>
                <span className={`text-sm font-bold px-2 py-0.5 rounded ${
                  simResult.risk_level === 'Critical' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40' :
                  simResult.risk_level === 'High' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40' :
                  'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40'
                }`}>
                  {simResult.risk_score} / 100 ({simResult.risk_level})
                </span>
              </div>
              <div className="text-[11px] text-slate-400 space-y-1">
                <div>ML Probability: <strong className="text-slate-200">{Math.round(simResult.classification_probability * 100)}%</strong> | Anomaly Score: <strong className="text-slate-200">{Math.round(simResult.anomaly_score * 100)}%</strong></div>
                <div className="text-rose-400 font-bold mt-1">Generated Forensic Rationale:</div>
                <ul className="list-disc pl-4 space-y-0.5 text-[10px] text-slate-300">
                  {simResult.reasons.map((r: string, i: number) => <li key={i}>{r}</li>)}
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
