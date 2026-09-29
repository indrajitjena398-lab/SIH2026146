import React, { useState, useEffect } from 'react';
import {
  Shield,
  Search,
  Terminal,
  Activity,
  Zap,
  Lock,
  Cpu,
  Layers,
  Sparkles,
  ExternalLink
} from 'lucide-react';
import { SearchResult } from '../../types';
import { ApiService } from '../../services/api';

interface NavbarProps {
  onSelectEntity: (id: string, type?: string) => void;
  activeThreshold: number;
}

export const Navbar: React.FC<NavbarProps> = ({ onSelectEntity, activeThreshold }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date().toUTCString());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date().toUTCString()), 1000);
    return () => clearInterval(timer);
  }, []);

  const handleSearch = async (val: string) => {
    setSearchQuery(val);
    if (!val || val.length < 2) {
      setSearchResults([]);
      return;
    }
    setIsSearching(true);
    try {
      const results = await ApiService.search(val);
      setSearchResults(results);
    } catch (e) {
      console.error(e);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <header className="h-16 border-b border-slate-800/90 bg-[#070b14]/95 backdrop-blur-xl px-6 flex items-center justify-between sticky top-0 z-50 shadow-2xl">
      {/* Brand & Mission Badge */}
      <div className="flex items-center space-x-3.5">
        <div className="relative">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500/20 via-slate-900 to-purple-500/20 border border-cyan-500/40 flex items-center justify-center glow-cyan">
            <Shield className="w-5 h-5 text-cyan-400" />
          </div>
          <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-emerald-500 border-2 border-[#070b14] animate-pulse"></span>
        </div>

        <div>
          <div className="flex items-center space-x-2">
            <span className="font-extrabold tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-sky-300 to-indigo-300 text-lg font-mono">
              BITCOIN SENTINEL
            </span>
            <span className="text-[9px] uppercase font-extrabold tracking-widest px-2 py-0.5 rounded-full bg-cyan-500/15 text-cyan-300 border border-cyan-500/40 font-mono shadow-sm">
              NTRO 26146
            </span>
          </div>
          <p className="text-[10px] text-slate-400 font-mono tracking-tight flex items-center gap-1.5">
            <Sparkles className="w-3 h-3 text-cyan-400" />
            <span>AI Traffic Monitoring & Blockchain Link Forensics</span>
          </p>
        </div>
      </div>

      {/* Global Intelligence Search Bar */}
      <div className="relative w-[420px]">
        <div className="relative group">
          <Search className="w-4 h-4 text-slate-400 group-focus-within:text-cyan-400 transition-colors absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search TXID, Wallet Address, IP Node, ASN, Alert ID..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            className="w-full pl-10 pr-24 py-2 text-xs bg-slate-950/90 border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400 focus:ring-2 focus:ring-cyan-500/20 font-mono transition-all shadow-inner"
          />
          {isSearching ? (
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] text-cyan-400 animate-pulse font-mono font-bold">
              SCANNING...
            </span>
          ) : (
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[9px] px-1.5 py-0.5 rounded bg-slate-800/80 border border-slate-700 text-slate-400 font-mono">
              CTRL+K
            </span>
          )}
        </div>

        {/* Live Search Dropdown */}
        {searchResults.length > 0 && (
          <div className="absolute top-full mt-2 left-0 right-0 bg-slate-900/95 border border-slate-700/90 rounded-xl shadow-2xl backdrop-blur-2xl overflow-hidden z-50 max-h-96 overflow-y-auto divide-y divide-slate-800">
            <div className="px-3.5 py-1.5 bg-slate-950/80 text-[10px] text-slate-400 font-mono font-bold uppercase tracking-wider flex justify-between">
              <span>MATCHING FORENSIC ENTITIES ({searchResults.length})</span>
              <span className="text-cyan-400">INSTANT JUMP</span>
            </div>
            {searchResults.map((item) => (
              <div
                key={item.id}
                onClick={() => {
                  onSelectEntity(item.id, item.type);
                  setSearchQuery('');
                  setSearchResults([]);
                }}
                className="px-4 py-2.5 hover:bg-slate-800/80 cursor-pointer flex items-center justify-between transition-colors group"
              >
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-mono font-bold text-slate-200 group-hover:text-cyan-300 transition-colors">
                      {item.title}
                    </span>
                    <span className="text-[9px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 font-mono">
                      {item.type}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 font-mono truncate max-w-xs mt-0.5">{item.subtitle}</p>
                </div>
                <div className="text-right">
                  <span className={`text-[11px] font-bold font-mono px-2.5 py-1 rounded-lg ${
                    item.risk_level === 'Critical' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40 glow-rose' :
                    item.risk_level === 'High' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40' :
                    'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40'
                  }`}>
                    {item.risk_score}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Right Controls: Telemetry Tickers */}
      <div className="flex items-center space-x-4">
        {/* Offline Badge */}
        <div className="hidden xl:flex items-center space-x-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-mono text-xs">
          <Lock className="w-3.5 h-3.5" />
          <span className="font-bold tracking-wider">AIR-GAPPED OFFLINE MODE</span>
        </div>

        <div className="text-right font-mono border-l border-slate-800 pl-4">
          <div className="text-xs text-slate-200 font-bold">{currentTime}</div>
          <div className="text-[10px] text-slate-400 flex items-center justify-end gap-1.5">
            <span className="text-slate-500">OPERATIONAL THRESHOLD:</span>
            <span className="text-cyan-400 font-bold">&ge;{activeThreshold}</span>
          </div>
        </div>
      </div>
    </header>
  );
};
