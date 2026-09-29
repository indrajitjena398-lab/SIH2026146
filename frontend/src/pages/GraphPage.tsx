import React, { useEffect, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
import {
  Network,
  Search,
  ZoomIn,
  ZoomOut,
  Maximize2,
  RefreshCw,
  Sliders,
  Filter,
  Eye,
  ArrowRight,
  ShieldAlert,
  Route,
  Sparkles,
  Layers,
  Play,
  Pause
} from 'lucide-react';
import { ApiService } from '../services/api';

interface GraphPageProps {
  initialEntityId?: string | null;
  onSelectEntity: (id: string, type?: string) => void;
}

export const GraphPage: React.FC<GraphPageProps> = ({ initialEntityId, onSelectEntity }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);

  const [centerId, setCenterId] = useState<string>(initialEntityId || 'tx_bc1b70000');
  const [depth, setDepth] = useState<number>(2);
  const [layoutName, setLayoutName] = useState<string>('cose');
  const [selectedNodeData, setSelectedNodeData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  // Shortest path solver
  const [pathSource, setPathSource] = useState('');
  const [pathTarget, setPathTarget] = useState('');
  const [pathResult, setPathResult] = useState<string[] | null>(null);
  const [viewMode, setViewMode] = useState<'raw' | 'super'>('raw');
  const [timelineStep, setTimelineStep] = useState(49);
  const [isPlaying, setIsPlaying] = useState(false);
  const [clusterCount, setClusterCount] = useState(0);

  // Entity Type Filter state
  const [activeTypes, setActiveTypes] = useState<{ [key: string]: boolean }>({
    Transaction: true,
    Wallet: true,
    IP: true,
    ASN: true,
    Country: true
  });

  const loadGraphData = async (targetId: string) => {
    if (!targetId || !containerRef.current) return;
    setLoading(true);
    setErrorMsg('');
    try {
      const typeFilterStr = Object.keys(activeTypes).filter(k => activeTypes[k]).join(',');
      const graphData = await ApiService.getSubgraph(targetId, depth, 75, typeFilterStr);

      if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
        setErrorMsg(`No graph relationships found for '${targetId}'.`);
        setLoading(false);
        return;
      }

      if (cyRef.current) {
        cyRef.current.destroy();
      }

      const cy = cytoscape({
        container: containerRef.current,
        elements: [...graphData.nodes, ...graphData.edges],
        style: [
          {
            selector: 'node',
            style: {
              'label': 'data(label)',
              'font-size': '9px',
              'font-family': 'monospace',
              'font-weight': 'bold',
              'color': '#f8fafc',
              'text-valign': 'bottom',
              'text-margin-y': 5,
              'background-color': '#38bdf8',
              'width': 28,
              'height': 28,
              'border-width': 2,
              'border-color': '#0f172a'
            }
          },
          // Node Shape & Colors by Entity Type
          {
            selector: 'node[entity_type = "Transaction"]',
            style: {
              'shape': 'round-rectangle',
              'background-color': '#a855f7',
              'border-color': '#7e22ce'
            }
          },
          {
            selector: 'node[entity_type = "Wallet"]',
            style: {
              'shape': 'ellipse',
              'background-color': '#38bdf8',
              'border-color': '#0284c7'
            }
          },
          {
            selector: 'node[entity_type = "IP"]',
            style: {
              'shape': 'diamond',
              'background-color': '#f59e0b',
              'border-color': '#d97706'
            }
          },
          {
            selector: 'node[entity_type = "ASN"]',
            style: {
              'shape': 'hexagon',
              'background-color': '#10b981',
              'border-color': '#059669'
            }
          },
          {
            selector: 'node[entity_type = "Country"]',
            style: {
              'shape': 'octagon',
              'background-color': '#64748b',
              'border-color': '#475569'
            }
          },
          // High Risk Node Glow
          {
            selector: 'node[risk_score >= 75]',
            style: {
              'background-color': '#ef4444',
              'border-color': '#ff4d4d',
              'border-width': 3,
              'width': 34,
              'height': 34
            }
          },
          {
            selector: 'node[?is_center]',
            style: {
              'border-color': '#00f2fe',
              'border-width': 4,
              'width': 40,
              'height': 40
            }
          },
          // Edges styling
          {
            selector: 'edge',
            style: {
              'width': 1.8,
              'line-color': '#334155',
              'target-arrow-color': '#64748b',
              'target-arrow-shape': 'triangle',
              'curve-style': 'bezier',
              'label': 'data(relation)',
              'font-size': '7px',
              'font-family': 'monospace',
              'color': '#64748b',
              'text-rotation': 'autorotate'
            }
          },
          {
            selector: 'node:selected',
            style: {
              'border-color': '#00f2fe',
              'border-width': 4
            }
          },
          {
            selector: '.highlighted',
            style: {
              'line-color': '#00f2fe',
              'target-arrow-color': '#00f2fe',
              'width': 3.5,
              'border-color': '#00f2fe'
            }
          }
        ],
        layout: {
          name: layoutName,
          animate: false,
          padding: 40
        } as any
      });

      cy.on('tap', 'node', (evt) => {
        const node = evt.target;
        setSelectedNodeData(node.data());
      });

      cy.on('dbltap', 'node', (evt) => {
        const node = evt.target;
        const targetEntity = node.data('full_label') || node.data('id');
        setCenterId(targetEntity);
      });

      cy.on('tap', (evt) => {
        if (evt.target === cy) {
          setSelectedNodeData(null);
        }
      });

      cyRef.current = cy;
    } catch (e: any) {
      console.error(e);
      setErrorMsg(e.message || 'Failed to render link analysis graph.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadGraphData(centerId);
  }, [centerId, depth, layoutName]);

  useEffect(() => {
    if (!isPlaying) return;
    const timer = window.setInterval(() => {
      setTimelineStep((step) => step >= 49 ? 1 : step + 1);
    }, 900);
    return () => window.clearInterval(timer);
  }, [isPlaying]);

  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;
    cy.batch(() => {
      cy.nodes().forEach((node) => {
        const nodeStep = Number(node.data('time_step') || 1);
        node.style('display', node.data('entity_type') === 'Transaction' && nodeStep > timelineStep ? 'none' : 'element');
      });
      cy.edges().forEach((edge) => {
        const source = cy.getElementById(edge.data('source'));
        const target = cy.getElementById(edge.data('target'));
        edge.style('display', source.visible() && target.visible() ? 'element' : 'none');
      });
    });
  }, [timelineStep]);

  const handleViewMode = async (mode: 'raw' | 'super') => {
    setViewMode(mode);
    if (mode === 'raw') {
      setClusterCount(0);
      await loadGraphData(centerId);
      return;
    }
    try {
      const response = await ApiService.getGraphEntities();
      setClusterCount(response.clusters.length);
      const clusterByTransaction = new Map<string, any>();
      response.clusters.forEach((cluster) => cluster.transaction_ids.forEach((txid: string) => clusterByTransaction.set(txid, cluster)));
      cyRef.current?.batch(() => {
        cyRef.current?.nodes().forEach((node) => {
          const cluster = clusterByTransaction.get(node.data('full_label'));
          if (node.data('entity_type') === 'Wallet') {
            node.style('display', 'none');
          } else if (cluster) {
            node.data('label', `Entity ${cluster.cluster_id}`);
            node.data('entity_type', 'EntityCluster');
          }
        });
        cyRef.current?.edges().forEach((edge) => {
          edge.style('display', 'none');
        });
      });
    } catch (error: any) {
      setErrorMsg(error.message || 'Failed to load entity clusters.');
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadGraphData(centerId);
  };

  const handleSolvePath = async () => {
    if (!pathSource || !pathTarget) return;
    try {
      const res = await ApiService.getShortestPath(pathSource, pathTarget);
      if (res && res.path && res.path.length > 0) {
        setPathResult(res.path);
        if (cyRef.current) {
          cyRef.current.elements().removeClass('highlighted');
          res.path.forEach((id: string) => {
            const el = cyRef.current?.$(`node[id = "${id}"]`);
            el?.addClass('highlighted');
          });
        }
      } else {
        setPathResult([]);
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="flex h-full overflow-hidden relative">
      {/* Main Graph Viewport */}
      <div className="flex-1 flex flex-col min-w-0 bg-[#060911] relative">
        {/* Controls Toolbar */}
        <div className="h-14 border-b border-slate-800 bg-[#080d18]/90 backdrop-blur-xl px-5 flex items-center justify-between z-20 shadow-md">
          <form onSubmit={handleSearch} className="flex items-center gap-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Center node on Entity ID / TXID..."
                value={centerId}
                onChange={(e) => setCenterId(e.target.value)}
                className="pl-8 pr-3 py-1 text-xs bg-slate-950 border border-slate-700 rounded-lg text-slate-200 font-mono w-64 focus:outline-none focus:border-cyan-400 shadow-inner"
              />
            </div>
            <button
              type="submit"
              className="px-3 py-1 bg-cyan-500 hover:bg-cyan-400 text-black text-xs font-mono font-bold rounded-lg transition-colors glow-cyan-sm"
            >
              Focus
            </button>
          </form>

          {/* Layout & Hop Controls */}
          <div className="flex items-center gap-3 font-mono text-xs text-slate-300">
            <div className="flex items-center gap-1.5">
              <span className="text-slate-500 text-[10px]">LAYOUT:</span>
              <select
                value={layoutName}
                onChange={(e) => setLayoutName(e.target.value)}
                className="bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1 text-xs text-slate-200"
              >
                <option value="cose">Force-Directed (CoSE)</option>
                <option value="concentric">Concentric Circles</option>
                <option value="circle">Circular Ring</option>
                <option value="breadthfirst">Flow Hierarchy Tree</option>
              </select>
            </div>

            <div className="flex items-center gap-1.5">
              <span className="text-slate-500 text-[10px]">DEPTH:</span>
              <select
                value={depth}
                onChange={(e) => setDepth(Number(e.target.value))}
                className="bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1 text-xs text-slate-200"
              >
                <option value={1}>1 Hop Neighborhood</option>
                <option value={2}>2 Hops Expansion</option>
                <option value={3}>3 Hops Deep Trace</option>
              </select>
            </div>

            <div className="flex items-center gap-1 border-l border-slate-800 pl-3">
              <button
                onClick={() => cyRef.current?.zoom(cyRef.current.zoom() * 1.25)}
                className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300"
                title="Zoom In"
              >
                <ZoomIn className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => cyRef.current?.zoom(cyRef.current.zoom() * 0.8)}
                className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300"
                title="Zoom Out"
              >
                <ZoomOut className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => cyRef.current?.fit()}
                className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300"
                title="Fit to Screen"
              >
                <Maximize2 className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

        <div className="absolute top-[4.25rem] left-5 z-20 flex items-center gap-1 rounded-lg border border-slate-800 bg-slate-950/90 p-1 font-mono text-[10px] shadow-xl">
          <button onClick={() => void handleViewMode('raw')} className={`rounded px-2.5 py-1.5 ${viewMode === 'raw' ? 'bg-cyan-500 text-black font-bold' : 'text-slate-400 hover:text-slate-100'}`}>Raw Node View</button>
          <button onClick={() => void handleViewMode('super')} className={`rounded px-2.5 py-1.5 ${viewMode === 'super' ? 'bg-purple-500 text-white font-bold' : 'text-slate-400 hover:text-slate-100'}`}>Entity Super-Node View</button>
          {viewMode === 'super' && <span className="px-2 text-purple-300">{clusterCount} clusters</span>}
        </div>
        </div>

        {/* Cytoscape Canvas */}
        <div ref={containerRef} className="flex-1 w-full h-full relative z-10" />

        {loading && (
          <div className="absolute inset-0 bg-[#060911]/70 backdrop-blur-sm flex items-center justify-center z-30 font-mono text-cyan-400 animate-pulse text-xs tracking-wider font-bold">
            COMPUTING GRAPH TOPOLOGY & EXPANDING NEIGHBORS...
          </div>
        )}

        {errorMsg && !loading && (
          <div className="absolute top-20 left-1/2 -translate-x-1/2 z-30 max-w-xl px-4 py-3 rounded-lg bg-rose-950/90 border border-rose-500/50 text-rose-300 font-mono text-xs shadow-xl">
            {errorMsg}
          </div>
        )}

        {/* Canvas Legend */}
        <div className="absolute bottom-4 left-4 p-3.5 bg-slate-950/90 border border-slate-800/90 rounded-xl font-mono text-[11px] space-y-1.5 z-20 backdrop-blur-md shadow-2xl pointer-events-none">
          <div className="text-[10px] text-slate-500 uppercase font-extrabold tracking-wider mb-1.5 flex items-center gap-1.5">
            <Sparkles className="w-3 h-3 text-cyan-400" />
            <span>HETEROGENEOUS ENTITIES</span>
          </div>
          <div className="flex items-center gap-2"><span className="w-3 h-3 rounded bg-purple-500"></span><span>Transaction Node</span></div>
          <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-sky-400"></span><span>Wallet Address</span></div>
          <div className="flex items-center gap-2"><span className="w-3 h-3 rotate-45 bg-amber-500"></span><span>IP Node</span></div>
          <div className="flex items-center gap-2"><span className="w-3 h-3 rounded bg-emerald-500"></span><span>Autonomous System (ASN)</span></div>
          <div className="flex items-center gap-2"><span className="w-3 h-3 rounded bg-rose-500 border border-rose-300"></span><span className="text-rose-400 font-bold">High Risk Node (&ge;75)</span></div>
        </div>

        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-20 flex items-center gap-3 rounded-xl border border-slate-800 bg-slate-950/95 px-4 py-2.5 font-mono text-[10px] shadow-2xl">
          <button onClick={() => setIsPlaying((playing) => !playing)} className="rounded-md bg-cyan-500/20 p-1.5 text-cyan-300 hover:bg-cyan-500/30" title={isPlaying ? 'Pause timeline' : 'Play timeline'}>
            {isPlaying ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
          </button>
          <span className="text-slate-400">T_{timelineStep}</span>
          <input type="range" min="1" max="49" value={timelineStep} onChange={(event) => { setIsPlaying(false); setTimelineStep(Number(event.target.value)); }} className="w-40 accent-cyan-400" aria-label="Dataset timeline timestep" />
          <span className="text-slate-500">T_49</span>
        </div>
      </div>

      {/* Right Sidebar: Node Inspector & Flow Solver */}
      <div className="w-84 border-l border-slate-800/90 bg-[#070b14]/95 backdrop-blur-xl flex flex-col justify-between p-4 overflow-y-auto shrink-0 z-20 shadow-2xl">
        <div className="space-y-5 font-mono text-xs">
          {/* Node Inspector */}
          <div>
            <div className="text-[10px] uppercase font-extrabold tracking-widest text-slate-500 mb-2.5 flex items-center gap-1.5">
              <Eye className="w-3.5 h-3.5 text-cyan-400" />
              <span>NODE FORENSIC INSPECTOR</span>
            </div>

            {selectedNodeData ? (
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3 shadow-inner">
                <div className="flex justify-between items-center">
                  <span className="text-[10px] text-slate-500">Entity Classification:</span>
                  <span className="px-2 py-0.5 rounded-full bg-slate-800 text-slate-200 text-[10px] font-bold">
                    {selectedNodeData.entity_type}
                  </span>
                </div>
                <div>
                  <div className="text-[10px] text-slate-500">Entity Identifier:</div>
                  <div className="text-cyan-300 font-bold break-all mt-0.5">{selectedNodeData.full_label || selectedNodeData.id}</div>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[10px] text-slate-500">Risk Assessment:</span>
                  <span className={`px-2.5 py-0.5 rounded-full font-bold ${
                    selectedNodeData.risk_score >= 75 ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40 glow-rose' :
                    selectedNodeData.risk_score >= 50 ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40' :
                    'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40'
                  }`}>
                    {selectedNodeData.risk_score} / 100
                  </span>
                </div>

                <div className="pt-2.5 border-t border-slate-800 space-y-2">
                  <button
                    onClick={() => onSelectEntity(selectedNodeData.full_label || selectedNodeData.id, selectedNodeData.entity_type)}
                    className="w-full py-2 rounded-lg bg-gradient-to-r from-cyan-500 to-sky-400 hover:from-cyan-400 hover:to-sky-300 text-black font-extrabold text-[11px] transition-all glow-cyan-sm"
                  >
                    Open Full Investigation Dossier
                  </button>
                  <button
                    onClick={() => { setCenterId(selectedNodeData.full_label || selectedNodeData.id); }}
                    className="w-full py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] transition-colors"
                  >
                    Center Node & Expand Neighbors
                  </button>
                </div>
              </div>
            ) : (
              <div className="p-5 rounded-xl bg-slate-950/60 border border-slate-800 text-center text-slate-500 text-[11px] leading-relaxed">
                Click any node on the canvas to inspect forensic properties, or double-click to expand its neighbor subgraph.
              </div>
            )}
          </div>

          {/* Shortest Path Solver */}
          <div className="pt-4 border-t border-slate-800">
            <div className="text-[10px] uppercase font-extrabold tracking-widest text-slate-500 mb-2.5 flex items-center gap-1.5">
              <Route className="w-3.5 h-3.5 text-purple-400" />
              <span>TRANSACTION FLOW PATH FINDER</span>
            </div>

            <div className="space-y-2">
              <input
                type="text"
                placeholder="Source Entity ID..."
                value={pathSource}
                onChange={(e) => setPathSource(e.target.value)}
                className="w-full px-3 py-1.5 text-[11px] bg-slate-950 border border-slate-700 rounded-lg text-slate-200 placeholder-slate-500 font-mono shadow-inner"
              />
              <input
                type="text"
                placeholder="Target Entity ID..."
                value={pathTarget}
                onChange={(e) => setPathTarget(e.target.value)}
                className="w-full px-3 py-1.5 text-[11px] bg-slate-950 border border-slate-700 rounded-lg text-slate-200 placeholder-slate-500 font-mono shadow-inner"
              />
              <button
                onClick={handleSolvePath}
                className="w-full py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-bold text-[11px] transition-colors glow-purple"
              >
                Solve Shortest Flow Path
              </button>

              {pathResult && (
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-[10px] space-y-1.5 mt-2">
                  {pathResult.length > 0 ? (
                    <>
                      <div className="text-emerald-400 font-bold">Path Found ({pathResult.length} Nodes):</div>
                      <div className="text-slate-300 break-all leading-relaxed">{pathResult.join(' → ')}</div>
                    </>
                  ) : (
                    <div className="text-rose-400">No reachable path found between entities.</div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
