import { useState, useEffect, useCallback } from 'react'
import {
  GSCommandCenter, GSAssetIntelligence, GSMaintenance, GSCrewPlanner, GSScenarioSim, GSCopilot
} from './components/gridshield'
import {
  signup, login, getMe, User
} from './api/client'
import {
  Bot,
  Compass,
  LayoutDashboard,
  Loader2,
  Power,
  Rocket,
  ShieldAlert,
  Shuffle,
  Sparkles,
} from 'lucide-react'
import { LandingPage } from '@/components/landing/LandingPage'

// ─── Nav definition ───────────────────────────────────────────────────────────
const navItems: { id: string; label: string; icon: any }[] = [
  { id: 'gs_dashboard',    label: 'Command Center',  icon: ShieldAlert },
  { id: 'gs_asset',        label: 'Asset Intelligence', icon: LayoutDashboard },
  { id: 'gs_maintenance',  label: 'Maintenance',     icon: Rocket },
  { id: 'gs_crew',         label: 'Crew Planner',    icon: Compass },
  { id: 'gs_scenarios',    label: 'Scenarios',       icon: Shuffle },
  { id: 'gs_copilot',      label: 'AI Advisor',      icon: Bot },
]

// ─── Auth Context ─────────────────────────────────────────────
function useAuth() {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(localStorage.getItem('access_token'))

  useEffect(() => {
    if (token) {
      getMe().then(r => setUser(r.data)).catch(() => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        setToken(null)
      })
    }
  }, [token])

  const doSignup = async (email: string, password: string, full_name: string) => {
    const r = await signup({ email, password, full_name })
    localStorage.setItem('access_token', r.data.access_token)
    localStorage.setItem('refresh_token', r.data.refresh_token)
    setUser(r.data.user)
    setToken(r.data.access_token)
  }

  const doLogin = async (email: string, password: string) => {
    const r = await login({ email, password })
    localStorage.setItem('access_token', r.data.access_token)
    localStorage.setItem('refresh_token', r.data.refresh_token)
    setUser(r.data.user)
    setToken(r.data.access_token)
  }

  const doLogout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setUser(null)
    setToken(null)
  }

  return { user, token, doSignup, doLogin, doLogout }
}

// ─── Sidebar ──────────────────────────────────────────────────
function Sidebar({ page, onNav, onLogout, user }: { page: string; onNav: (p: string) => void; onLogout: () => void; user: User }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon"><ShieldAlert size={18} /></div>
        <div>
          <h1>GridShield</h1>
          <p>Grid Ops AI</p>
        </div>
      </div>

      <nav className="sidebar-nav">
        <div className="sidebar-label" style={{paddingTop: 4}}>GridShield</div>
        {navItems.map(item => (
          <button key={item.id} className={`nav-item ${page === item.id ? 'active' : ''}`} onClick={() => onNav(item.id)}>
            <item.icon /><span>{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="flex-between">
          <div className="user-info">
            <div className="user-name">{user.full_name}</div>
            <div className="user-email">{user.email}</div>
          </div>
          <button className="btn btn-ghost btn-sm" onClick={onLogout} title="Logout">
            <Power size={16} />
          </button>
        </div>
      </div>
    </aside>
  )
}

// ─── Main App ─────────────────────────────────────────────────
export default function App() {
  const { user, doSignup, doLogin, doLogout } = useAuth()
  const [page, setPage] = useState<string>('gs_copilot')
  const [gsAssetId, setGsAssetId] = useState<string | null>(null)

  if (!user) return <LandingPage onLogin={doLogin} onSignup={doSignup} />

  function goToGsAsset(id: string) { setGsAssetId(id); setPage('gs_asset') }
  function backFromGsAsset() { setGsAssetId(null); setPage('gs_dashboard') }

  const renderPage = () => {
    switch (page) {
      case 'gs_dashboard':   return <GSCommandCenter onSelectAsset={goToGsAsset} />
      case 'gs_asset':       return gsAssetId
        ? <GSAssetIntelligence assetId={gsAssetId} onBack={backFromGsAsset} />
        : <GSCommandCenter onSelectAsset={goToGsAsset} />
      case 'gs_maintenance': return <GSMaintenance onSelectAsset={goToGsAsset} />
      case 'gs_crew':        return <GSCrewPlanner onSelectAsset={goToGsAsset} />
      case 'gs_scenarios':   return <GSScenarioSim onSelectAsset={goToGsAsset} />
      case 'gs_copilot':     return <GSCopilot />
      default:               return <GSCommandCenter onSelectAsset={goToGsAsset} />
    }
  }

  // AI Advisor needs full-height layout
  const isCopilot = page === 'gs_copilot'

  return (
    <div style={{display:'flex',height:'100vh'}}>
      <Sidebar page={page} onNav={setPage} onLogout={doLogout} user={user} />
      <main className="main">
        {isCopilot ? (
          <div style={{height:'100%',padding:0}}>
            {renderPage()}
          </div>
        ) : (
          <div className="main-content">
            {renderPage()}
          </div>
        )}
      </main>
    </div>
  )
}
