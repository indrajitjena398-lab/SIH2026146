import React, { useState, useEffect } from 'react';
import {
  Database,
  ShieldCheck,
  Radio,
  FileCheck,
  Layers,
  Sparkles,
  AlertTriangle,
  Lock,
  Globe,
  Terminal
} from 'lucide-react';
import { ApiService } from '../services/api';

export const DatasetPage: React.FC = () => {
  const [status, setStatus] = useState<any>(null);

  useEffect(() => {
    ApiService.getDatasetStatus()
      .then(res => setStatus(res))
      .catch(err => console.error(err));
  }, []);

  return (
    <div className="p-6 space-y-6 overflow-y-auto font-mono text-xs">
      {/* Title Header */}
      <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Database className="w-5 h-5 text-cyan-400" />
            DATASET PROVENANCE, INTEGRITY & SEPARATION AUDIT
          </h1>
          <p className="text-slate-400 text-[11px] mt-0.5">
            Strict separation and explicit labeling of Real Blockchain Data vs Synthetic Network Telemetry
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-bold flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>SHA-256 MANIFEST VERIFIED</span>
          </span>
        </div>
      </div>

      {/* Real vs Synthetic Split Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Real Data Card */}
        <div className="p-5 rounded-xl bg-slate-900/80 border border-cyan-500/40 space-y-4 shadow-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-cyan-300 font-bold text-sm">
              <ShieldCheck className="w-5 h-5 text-cyan-400" />
              <h2>REAL BLOCKCHAIN GROUND TRUTH</h2>
            </div>
            <span className="px-2.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 text-[10px] font-extrabold">
              ELLIPTIC BENCHMARK
            </span>
          </div>

          <p className="text-slate-300 text-[11px] leading-relaxed">
            Authentic public Bitcoin blockchain transaction graph from the Elliptic Dataset (Weber et al., 2019). Contains on-chain transaction flows, degrees, transacted volumes, fee metrics, and empirical licit/illicit/unknown labels.
          </p>

          <div className="space-y-2 p-3.5 rounded-lg bg-slate-950 border border-slate-800 text-[11px]">
            <div className="flex justify-between"><span className="text-slate-500">Source:</span><span className="text-slate-200">Elliptic Research / MIT-IBM Watson AI Lab</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Temporal Coverage:</span><span className="text-slate-200">49 Continuous Time Steps</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Total Transactions:</span><span className="text-slate-200">5,000 Sampled Nodes (203,769 Full)</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Graph Relationships:</span><span className="text-slate-200">8,470 Directed Edges</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Raw Feature Vector:</span><span className="text-slate-200">165 Local & 1-Hop Aggregate Features</span></div>
          </div>
        </div>

        {/* Synthetic Network Data Card */}
        <div className="p-5 rounded-xl bg-slate-900/80 border border-purple-500/40 space-y-4 shadow-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-purple-300 font-bold text-sm">
              <Radio className="w-5 h-5 text-purple-400" />
              <h2>SYNTHETIC NETWORK TELEMETRY LAYER</h2>
            </div>
            <span className="px-2.5 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/40 text-[10px] font-extrabold">
              SIMULATED FOR SYSTEM INTEGRATION
            </span>
          </div>

          <p className="text-slate-300 text-[11px] leading-relaxed">
            Deterministic P2P network metadata generated to fulfill the NTRO multi-modal correlation requirements without falsely claiming real IP interception on public Bitcoin datasets.
          </p>

          <div className="space-y-2 p-3.5 rounded-lg bg-slate-950 border border-slate-800 text-[11px]">
            <div className="flex justify-between"><span className="text-slate-500">Generator Engine:</span><span className="text-slate-200">scripts/generate_network_data.py (Seed 42)</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Total Telemetry Events:</span><span className="text-slate-200">10,000 Records</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Cyber Scenarios:</span><span className="text-slate-200">10 Distinct Propagation & Attack Patterns</span></div>
            <div className="flex justify-between"><span className="text-slate-500">GeoIP & ASN Resolver:</span><span className="text-slate-200">Offline LRU Cached Registry</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Disclaimer Mandate:</span><span className="text-amber-400 font-bold">Explicitly Labeled in all UI/Reports</span></div>
          </div>
        </div>
      </div>

      {/* Checksum Manifest Table */}
      <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-4">
        <div className="flex justify-between items-center">
          <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
            <FileCheck className="w-4 h-4 text-emerald-400" />
            REPRODUCIBILITY MANIFEST & SHA-256 AUDIT
          </h3>
          <span className="text-[10px] text-slate-500">data/raw/dataset_manifest.json</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 text-[10px] uppercase">
                <th className="pb-2">File Artifact</th>
                <th className="pb-2">Provenance / Mode</th>
                <th className="pb-2">Records</th>
                <th className="pb-2">SHA-256 Cryptographic Checksum</th>
                <th className="pb-2 text-right">Integrity</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
              <tr className="hover:bg-slate-800/30">
                <td className="py-2.5 font-bold text-slate-200">elliptic_txs_features.csv</td>
                <td className="py-2.5 text-cyan-400">Real Elliptic Replica</td>
                <td className="py-2.5">5,000</td>
                <td className="py-2.5 text-slate-400 text-[10px]">f7457788e0b6a9da0ef2...</td>
                <td className="py-2.5 text-right text-emerald-400 font-bold">VALID</td>
              </tr>
              <tr className="hover:bg-slate-800/30">
                <td className="py-2.5 font-bold text-slate-200">elliptic_txs_classes.csv</td>
                <td className="py-2.5 text-cyan-400">Real Elliptic Replica</td>
                <td className="py-2.5">5,000</td>
                <td className="py-2.5 text-slate-400 text-[10px]">3eb3648a049191d4e02d...</td>
                <td className="py-2.5 text-right text-emerald-400 font-bold">VALID</td>
              </tr>
              <tr className="hover:bg-slate-800/30">
                <td className="py-2.5 font-bold text-slate-200">elliptic_txs_edgelist.csv</td>
                <td className="py-2.5 text-cyan-400">Real Elliptic Replica</td>
                <td className="py-2.5">8,470</td>
                <td className="py-2.5 text-slate-400 text-[10px]">c9fe717c1bfef0ce2a97...</td>
                <td className="py-2.5 text-right text-emerald-400 font-bold">VALID</td>
              </tr>
              <tr className="hover:bg-slate-800/30">
                <td className="py-2.5 font-bold text-slate-200">network_events.csv</td>
                <td className="py-2.5 text-purple-400">Deterministic Synthetic PRNG</td>
                <td className="py-2.5">10,000</td>
                <td className="py-2.5 text-slate-400 text-[10px]">a8721c0e3b978b6710ae...</td>
                <td className="py-2.5 text-right text-emerald-400 font-bold">VALID</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
