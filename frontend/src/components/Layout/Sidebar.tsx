import React from 'react';
import {
  LayoutDashboard,
  ShieldAlert,
  SearchCode,
  Network,
  Cpu,
  Database,
  Sliders,
  Radio,
  Sparkles,
  Terminal,
  Activity,
  Layers,
  Bot
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  alertCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab, alertCount }) => {
  const navItems = [
    { id: 'overview', label: 'Threat Overview', icon: LayoutDashboard, desc: 'Real-time global metrics' },
    { id: 'alerts', label: 'Alerts Center', icon: ShieldAlert, desc: 'Prioritized triage queue', badge: alertCount },
    { id: 'attack-detector', label: 'AI Attack Detector', icon: Bot, desc: 'LLM verdict & 30-40w explain' },
    { id: 'investigation', label: 'Investigation Dossier', icon: SearchCode, desc: 'Deep forensic evidence & SHAP' },
    { id: 'graph', label: 'Graph Link Analysis', icon: Network, desc: 'Interactive link & path solver' },
    { id: 'ml', label: 'ML Analytics', icon: Cpu, desc: 'Model benchmarks & ROC/PR' },
    { id: 'dataset', label: 'Dataset & Audit', icon: Database, desc: 'Real vs Synthetic provenance' },
    { id: 'system', label: 'System Operations', icon: Sliders, desc: 'Thresholds & simulation engine' }
  ];

  return (
    <aside className="w-68 border-r border-slate-800/90 bg-[#070b14]/90 backdrop-blur-xl flex flex-col justify-between py-4 select-none shrink-0 shadow-xl">
      <div className="space-y-6">
        <div className="px-3.5">
          <div className="text-[10px] uppercase font-bold tracking-widest text-slate-500 font-mono px-3 mb-2.5 flex items-center justify-between">
            <span>FORENSIC MODULES</span>
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
          </div>
          <nav className="space-y-1.5">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-mono font-medium transition-all group ${
                    isActive
                      ? 'bg-gradient-to-r from-cyan-500/15 to-purple-500/10 text-cyan-300 border border-cyan-500/40 glow-cyan shadow-lg'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 border border-transparent'
                  }`}
                >
                  <div className="flex items-center space-x-3 text-left">
                    <div className={`p-1.5 rounded-lg transition-colors ${
                      isActive ? 'bg-cyan-500/20 text-cyan-400' : 'bg-slate-900 text-slate-400 group-hover:text-slate-200'
                    }`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <div>
                      <div className={`text-xs font-bold leading-none ${isActive ? 'text-slate-100' : 'text-slate-300'}`}>
                        {item.label}
                      </div>
                      <div className="text-[10px] text-slate-500 mt-1 font-normal">{item.desc}</div>
                    </div>
                  </div>

                  {item.badge !== undefined && item.badge > 0 && (
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold font-mono ${
                      isActive ? 'bg-cyan-400 text-black shadow-md' : 'bg-rose-500/20 text-rose-400 border border-rose-500/40'
                    }`}>
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Security / System Telemetry Box */}
        <div className="px-3.5">
          <div className="text-[10px] uppercase font-bold tracking-widest text-slate-500 font-mono px-3 mb-2 flex items-center gap-1.5">
            <Activity className="w-3 h-3 text-emerald-400" />
            <span>ENGINE METRICS</span>
          </div>
          <div className="p-3.5 bg-slate-950/80 border border-slate-800/90 rounded-xl space-y-2 font-mono text-[11px] shadow-inner">
            <div className="flex justify-between items-center text-slate-400">
              <span className="text-slate-500">Storage:</span>
              <span className="text-cyan-400 font-bold">DuckDB Embedded</span>
            </div>
            <div className="flex justify-between items-center text-slate-400">
              <span className="text-slate-500">Graph Size:</span>
              <span className="text-purple-400 font-bold">15k Nodes / 27k Edges</span>
            </div>
            <div className="flex justify-between items-center text-slate-400">
              <span className="text-slate-500">Primary AI:</span>
              <span className="text-emerald-400 font-bold">XGBoost + SHAP</span>
            </div>
            <div className="flex justify-between items-center text-slate-400">
              <span className="text-slate-500">Isolation Forest:</span>
              <span className="text-amber-400 font-bold">Active (0.05)</span>
            </div>
          </div>
        </div>
      </div>

      <div className="px-4 py-2 text-[10px] text-slate-500 font-mono text-center border-t border-slate-800/80 mx-3">
        NTRO 26146 // BITCOIN DECISION SUPPORT
      </div>
    </aside>
  );
};
