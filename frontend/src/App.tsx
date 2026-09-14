import { useState, useEffect } from 'react'
import {
  GSCommandCenter, GSAssetIntelligence, GSMaintenance, GSCrewPlanner,
  GSScenarioSim, GSCopilot, GSSettings,
} from './components/gridshield'
import { signup, login, getMe, User } from './api/client'
import {
  AlertTriangle,
  Bot,
  ChevronRight,
  LayoutDashboard,
  LogOut,
  Cpu,
  Users,
  Zap,
  FlaskConical,
  Activity,
  Settings,
} from 'lucide-react'
import { LandingPage } from '@/components/landing/LandingPage'

// ─── Nav definition ────────────────────────────────────────────────────────────
interface NavItem { id: string; label: string; icon: React.ElementType; badge?: string }

const navItems: NavItem[] = [
  { id: 'gs_dashboard',   label: 'Command Center',     icon: LayoutDashboard },
  { id: 'gs_asset',       label: 'Asset Intelligence', icon: Activity },
  { id: 'gs_maintenance', label: 'Maintenance',        icon: AlertTriangle },
  { id: 'gs_crew',        label: 'Crew Planner',       icon: Users },
  { id: 'gs_scenarios',   label: 'Scenarios',          icon: FlaskConical },
  { id: 'gs_copilot',     label: 'AI Advisor',         icon: Bot },
  { id: 'gs_settings',    label: 'Settings',           icon: Settings },
]

// ─── Auth hook ────────────────────────────────────────────────
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
function Sidebar({
  page,
  onNav,
  onLogout,
  user,
}: {
  page: string
  onNav: (p: string) => void
  onLogout: () => void
  user: User
}) {
  const initials = (user.full_name || user.email)
    .split(' ')
    .map((w: string) => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)

  return (
    <aside className="bn-sidebar">
      {/* ── Logo ──────────────────────────────────────────── */}
      <div className="bn-sidebar-logo">
        <div className="bn-logo-icon">
          <Zap size={17} strokeWidth={2.5} />
        </div>
        <div className="bn-logo-text">
          <span className="bn-logo-title">Bottleneck</span>
          <span className="bn-logo-sub">Power Outage Prediction</span>
        </div>
      </div>

      {/* ── Section label ─────────────────────────────────── */}
      <div className="bn-nav-section-label">Navigation</div>

      {/* ── Nav items ─────────────────────────────────────── */}
      <nav className="bn-nav">
        {navItems.map(item => {
          const active = page === item.id
          return (
            <button
              key={item.id}
              className={`bn-nav-item${active ? ' bn-nav-item--active' : ''}`}
              onClick={() => onNav(item.id)}
            >
              <span className="bn-nav-icon">
                <item.icon size={16} strokeWidth={active ? 2.2 : 1.8} />
              </span>
              <span className="bn-nav-label">{item.label}</span>
              {active && <ChevronRight size={13} className="bn-nav-chevron" />}
            </button>
          )
        })}
      </nav>

      {/* ── Divider ───────────────────────────────────────── */}
      <div className="bn-sidebar-divider" />

      {/* ── Track badge ───────────────────────────────────── */}
      <div className="bn-track-badge">
        <Cpu size={12} />
        <span>IBM Bob Hackathon 2026 · Track U1</span>
      </div>

      {/* ── Footer / user ─────────────────────────────────── */}
      <div className="bn-sidebar-footer">
        <div className="bn-user-avatar">{initials}</div>
        <div className="bn-user-info">
          <span className="bn-user-name">{user.full_name || 'User'}</span>
          <span className="bn-user-email">{user.email}</span>
        </div>
        <button className="bn-logout-btn" onClick={onLogout} title="Sign out">
          <LogOut size={15} strokeWidth={1.8} />
        </button>
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
      case 'gs_settings':    return <GSSettings />
      default:               return <GSCommandCenter onSelectAsset={goToGsAsset} />
    }
  }

  const isCopilot = page === 'gs_copilot'

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      <Sidebar page={page} onNav={setPage} onLogout={doLogout} user={user} />
      <main className="main">
        {isCopilot ? (
          <div style={{ height: '100%', padding: 0 }}>
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
