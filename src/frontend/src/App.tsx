import { useState } from 'react'
import {
  GSCommandCenter, GSAssetIntelligence, GSMaintenance, GSCrewPlanner, GSScenarioSim, GSCopilot
} from './components/bottleneck'
import {
  Bot,
  Compass,
  Power,
  Rocket,
  ShieldAlert,
  Shuffle,
  Zap,
  type LucideIcon,
} from 'lucide-react'

// ─── Nav definition ───────────────────────────────────────────────────────────
const navItems: { id: string; label: string; icon: LucideIcon }[] = [
  { id: 'gs_dashboard',    label: 'Command Center',  icon: ShieldAlert },
  { id: 'gs_maintenance',  label: 'Maintenance',     icon: Rocket },
  { id: 'gs_crew',         label: 'Crew Planner',    icon: Compass },
  { id: 'gs_scenarios',    label: 'Scenarios',       icon: Shuffle },
  { id: 'gs_copilot',      label: 'AI Advisor',      icon: Bot },
]

// ─── Sidebar ──────────────────────────────────────────────────
function Sidebar({ page, onNav }: { page: string; onNav: (p: string) => void }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon" style={{ background: '#0284c7', color: 'white' }}>
          <Zap size={20} />
        </div>
        <div>
          <h1>Bottleneck</h1>
          <p>Grid Risk AI</p>
        </div>
      </div>

      <nav className="sidebar-nav" style={{ marginTop: 12 }}>
        <div className="sidebar-label" style={{ paddingTop: 4, letterSpacing: '0.05em', textTransform: 'uppercase', fontSize: 11, fontWeight: 700, color: 'var(--text3, #888)' }}>
          Grid Operations
        </div>
        {navItems.map(item => (
          <button
            key={item.id}
            className={`nav-item ${page === item.id || (page === 'gs_asset' && item.id === 'gs_dashboard') ? 'active' : ''}`}
            onClick={() => onNav(item.id)}
          >
            <item.icon size={18} />
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="flex-between" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div className="user-info">
            <div className="user-name" style={{ fontWeight: 600, fontSize: 13 }}>Grid Operator</div>
            <div className="user-email" style={{ fontSize: 11, color: 'var(--text3, #888)' }}>ops@gridcontrol.io</div>
          </div>
          <button className="btn btn-ghost btn-sm" onClick={() => window.location.reload()} title="Reload System">
            <Power size={16} />
          </button>
        </div>
      </div>
    </aside>
  )
}

export function App() {
  const [page, setPage] = useState<string>('gs_dashboard')
  const [gsAssetId, setGsAssetId] = useState<string | null>(null)

  function goToGsAsset(assetId: string) {
    setGsAssetId(assetId)
    setPage('gs_asset')
  }

  function backFromGsAsset() {
    setGsAssetId(null)
    setPage('gs_dashboard')
  }

  const renderPage = () => {
    switch (page) {
      case 'gs_dashboard':
        return <GSCommandCenter onSelectAsset={goToGsAsset} />
      case 'gs_asset':
        return gsAssetId ? (
          <GSAssetIntelligence assetId={gsAssetId} onBack={backFromGsAsset} />
        ) : (
          <GSCommandCenter onSelectAsset={goToGsAsset} />
        )
      case 'gs_maintenance':
        return <GSMaintenance onSelectAsset={goToGsAsset} />
      case 'gs_crew':
        return <GSCrewPlanner onSelectAsset={goToGsAsset} />
      case 'gs_scenarios':
        return <GSScenarioSim onSelectAsset={goToGsAsset} />
      case 'gs_copilot':
        return <GSCopilot />
      default:
        return <GSCommandCenter onSelectAsset={goToGsAsset} />
    }
  }

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw', overflow: 'hidden' }}>
      <Sidebar page={page} onNav={setPage} />
      <main className="main" style={{ flex: 1, overflowY: 'auto', background: 'var(--bg2, #f8fafc)', padding: '24px 32px' }}>
        <div className="main-content">
          {renderPage()}
        </div>
      </main>
    </div>
  )
}

export default App