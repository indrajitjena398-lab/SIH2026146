import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Layout/Navbar';
import { Sidebar } from './components/Layout/Sidebar';
import { OverviewPage } from './pages/OverviewPage';
import { AlertsPage } from './pages/AlertsPage';
import { AttackDetectorPage } from './pages/AttackDetectorPage';
import { InvestigationPage } from './pages/InvestigationPage';
import { GraphPage } from './pages/GraphPage';
import { MLAnalyticsPage } from './pages/MLAnalyticsPage';
import { DatasetPage } from './pages/DatasetPage';
import { SystemStatusPage } from './pages/SystemStatusPage';
import { Statistics } from './types';
import { ApiService } from './services/api';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [stats, setStats] = useState<Statistics | null>(null);
  const [selectedEntityId, setSelectedEntityId] = useState<string | null>(null);
  const [activeThreshold, setActiveThreshold] = useState<number>(30);

  const fetchStats = async () => {
    try {
      const s = await ApiService.getStatistics();
      setStats(s);
    } catch (e) {
      console.error('Failed to load statistics:', e);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleSelectEntity = (id: string, type?: string) => {
    setSelectedEntityId(id);
    if (type === 'Alert' || id.startsWith('ALT-') || id.startsWith('ALERT-') || type === 'Transaction' || /^\d+$/.test(id)) {
      setActiveTab('investigation');
    } else {
      setActiveTab('graph');
    }
  };

  const handleSelectAlert = (alertId: string) => {
    setSelectedEntityId(alertId);
    setActiveTab('investigation');
  };

  const handleNavigateToGraph = (entityId: string) => {
    setSelectedEntityId(entityId);
    setActiveTab('graph');
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#060911] text-slate-100 selection:bg-cyan-500 selection:text-black">
      {/* Top Cyber Intelligence Navbar */}
      <Navbar onSelectEntity={handleSelectEntity} activeThreshold={activeThreshold} />

      {/* Main Forensic Investigation Layout */}
      <div className="flex flex-1 min-h-0">
        {/* Left Navigation Sidebar */}
        <Sidebar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          alertCount={stats ? (stats.critical_alerts + stats.high_alerts) : 0}
        />

        {/* Dynamic Investigation Workspace Pages */}
        <main className="flex-1 min-w-0 bg-[#060911]/95 overflow-hidden flex flex-col">
          {activeTab === 'overview' && (
            <OverviewPage
              stats={stats}
              onSelectEntity={handleSelectEntity}
              onNavigate={(tab) => setActiveTab(tab)}
              onDatasetRefresh={fetchStats}
            />
          )}

          {activeTab === 'alerts' && (
            <AlertsPage onSelectAlert={handleSelectAlert} />
          )}

          {activeTab === 'attack-detector' && (
            <AttackDetectorPage
              onNavigateToInvestigation={handleSelectAlert}
              onNavigateToGraph={handleNavigateToGraph}
            />
          )}

          {activeTab === 'investigation' && (
            <InvestigationPage
              selectedAlertId={selectedEntityId}
              onNavigateToGraph={handleNavigateToGraph}
            />
          )}

          {activeTab === 'graph' && (
            <GraphPage
              initialEntityId={selectedEntityId}
              onSelectEntity={handleSelectEntity}
            />
          )}

          {activeTab === 'ml' && (
            <MLAnalyticsPage />
          )}

          {activeTab === 'dataset' && (
            <DatasetPage />
          )}

          {activeTab === 'system' && (
            <SystemStatusPage
              activeThreshold={activeThreshold}
              onUpdateThreshold={(val) => setActiveThreshold(val)}
            />
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
