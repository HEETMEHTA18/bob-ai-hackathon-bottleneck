import { useState, useEffect, useCallback, useMemo, Fragment, lazy, Suspense } from 'react'
import {
  GSCommandCenter, GSAssetIntelligence, GSMaintenance, GSCrewPlanner, GSScenarioSim
} from './components/gridshield'
import {
  signup, login, getMe, listSites, createSite,
  getForecast, getRisk, getExplain, runScenario,
  getDataStatus, syncWeatherData, importCSV,
  getForecastAccuracy, getAlerts, getModelHealth, getWeatherInsights,
  Site, User
} from './api/client'
import {
  BarChart3,
  BatteryCharging,
  Bot,
  CheckCircle2,
  Compass,
  Crosshair,
  Database,
  Factory,
  HelpCircle,
  LayoutDashboard,
  Link2,
  Loader2,
  MapPin,
  Package,
  Play,
  Plus,
  Power,
  RefreshCw,
  Rocket,
  ScanSearch,
  Settings,
  ShieldAlert,
  Shuffle,
  Sparkles,
  Thermometer,
  TrendingDown,
  TrendingUp,
  Upload,
  X,
  Zap,
  type LucideIcon,
} from 'lucide-react'
import { AIAssistantInterface } from '@/components/ui/ai-assistant-interface'
import { LandingPage } from '@/components/landing/LandingPage'
import toast from 'react-hot-toast'

// ─── Nav definition ───────────────────────────────────────────────────────────
const navItems: { id: string; label: string; icon: LucideIcon }[] = [
  { id: 'gs_dashboard',    label: 'Command Center',  icon: ShieldAlert },
  { id: 'dashboard',       label: 'Dashboard',       icon: LayoutDashboard },
  { id: 'forecast',        label: 'Forecast',        icon: TrendingUp },
  { id: 'risk',            label: 'Risk Analysis',   icon: Shuffle },
  { id: 'optimize',        label: 'Optimize',        icon: Zap },
  { id: 'insights',        label: 'Insights',        icon: Sparkles },
  { id: 'anomalies',       label: 'Anomalies',       icon: ScanSearch },
  { id: 'data',            label: 'Data Sources',    icon: Database },
  { id: 'gs_maintenance',  label: 'Maintenance',     icon: Rocket },
  { id: 'gs_crew',         label: 'Crew Planner',    icon: Compass },
  { id: 'gs_scenarios',    label: 'Scenarios',       icon: Shuffle },
  { id: 'gs_copilot',      label: 'AI Advisor',      icon: Bot },
  { id: 'settings',        label: 'Settings',        icon: Settings },
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
  const [sites, setSites] = useState<Site[]>([])
  const [activeSite, setActiveSite] = useState<Site | null>(null)

  const refreshSites = useCallback(() => {
    listSites().then(r => {
      setSites(r.data)
      if (r.data.length > 0 && !activeSite) {
        setActiveSite(r.data[0])
        ;(window as any).__GRIDSHIELD_SITE__ = r.data[0]
        window.dispatchEvent(new Event('siteChanged'))
      }
    }).catch(() => {})
  }, [])

  useEffect(() => { refreshSites() }, [refreshSites])

  useEffect(() => {
    const handler = () => refreshSites()
    window.addEventListener('siteCreated', handler)
    return () => window.removeEventListener('siteCreated', handler)
  }, [refreshSites])

  useEffect(() => {
    ;(window as any).__GRIDSHIELD_SITE__ = activeSite
  }, [activeSite])

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon"><ShieldAlert size={18} /></div>
        <div>
          <h1>GridShield</h1>
          <p>Grid Ops AI</p>
        </div>
      </div>

      <div className="sidebar-section">
        <div className="sidebar-label">Renewables Site</div>
        <select className="select" value={activeSite?.id || ''} onChange={e => {
          const s = sites.find(s => s.id === e.target.value) || null
          setActiveSite(s)
          ;(window as any).__GRIDSHIELD_SITE__ = s
          window.dispatchEvent(new Event('siteChanged'))
        }}>
          {sites.length === 0 && <option value="">No sites yet</option>}
          {sites.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>
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

// ─── Dashboard ────────────────────────────────────────────────
function Dashboard({ site }: { site: Site }) {
  const [forecast, setForecast] = useState<any>(null)
  const [risk, setRisk] = useState<any>(null)

  useEffect(() => {
    if (!site) return
    getForecast(site.id, 24).then(r => setForecast(r.data)).catch(() => {})
    getRisk(site.id, 24).then(r => setRisk(r.data)).catch(() => {})
  }, [site])

  return (
    <div className="animate-fadeIn">
      <div className="page-header flex-between">
        <div>
          <div className="page-title">{site.name}</div>
          <div className="page-subtitle">Lat {site.latitude.toFixed(4)}, Lon {site.longitude.toFixed(4)} · {site.site_type}</div>
        </div>
        <span className="badge badge-green"><span className="status-dot" style={{marginRight:6}} />Online</span>
      </div>

      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-icon" style={{background:'var(--accent-light)',color:'var(--accent)'}}><Zap /></div>
          <div className="kpi-value">{site.capacity_kw} <span style={{fontSize:12,fontWeight:500}}>kW</span></div>
          <div className="kpi-label">Installed Capacity</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon" style={{background:'var(--green-light)',color:'var(--green)'}}><BatteryCharging /></div>
          <div className="kpi-value">{site.battery_capacity_kwh} <span style={{fontSize:12,fontWeight:500}}>kWh</span></div>
          <div className="kpi-label">Battery Storage</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon" style={{background:'var(--amber-light)',color:'var(--amber)'}}><Upload /></div>
          <div className="kpi-value">{site.export_limit_kw} <span style={{fontSize:12,fontWeight:500}}>kW</span></div>
          <div className="kpi-label">Export Limit</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon" style={{background:'#f0f9ff',color:'#0284c7'}}><MapPin /></div>
          <div className="kpi-value">{site.altitude || 0} <span style={{fontSize:12,fontWeight:500}}>m</span></div>
          <div className="kpi-label">Altitude</div>
        </div>
      </div>

      <div className="grid-2" style={{gridTemplateColumns: '3fr 2fr'}}>
        {/* Mini Forecast Chart */}
        <div className="card">
          <div className="card-title">24-Hour Generation Forecast</div>
          {forecast ? (
            <div>
              <div style={{display:'flex',gap:2,alignItems:'flex-end',height:140}}>
                {forecast.forecast.p50.map((v:number, i:number) => {
                  const maxVal = Math.max(...forecast.forecast.p90, 1)
                  return (
                    <div key={i} style={{flex:1,display:'flex',flexDirection:'column',alignItems:'center'}}>
                      <div style={{width:'100%',background:'var(--accent-light)',borderRadius:3,height:((forecast.forecast.p90[i]-forecast.forecast.p10[i])/maxVal)*120,position:'relative'}}>
                        <div style={{position:'absolute',bottom:0,width:'100%',background:'var(--accent)',borderRadius:3,height:Math.max(2,(v/maxVal)*120),opacity:0.85}}></div>
                      </div>
                      {i%4===0 && <span className="text-xs text-muted" style={{marginTop:4}}>{String(i).padStart(2,'0')}:00</span>}
                    </div>
                  )
                })}
              </div>
              <div className="flex-center gap-4 mt-3" style={{justifyContent:'center'}}>
                <div className="flex-center gap-2"><div style={{width:12,height:4,background:'var(--accent)',borderRadius:2}}></div><span className="text-xs text-muted">Forecast</span></div>
                <div className="flex-center gap-2"><div style={{width:12,height:12,background:'var(--accent-light)',borderRadius:2}}></div><span className="text-xs text-muted">P10-P90 Range</span></div>
              </div>
            </div>
          ) : <div className="text-sm text-muted">Loading forecast...</div>}
        </div>

        {/* Risk Summary */}
        <div className="card">
          <div className="card-title">Risk Summary (24h)</div>
          {risk ? (
            <div>
              {(() => {
                const high = risk.risks.filter((r:any) => r.risk === 'HIGH').length
                const med = risk.risks.filter((r:any) => r.risk === 'MEDIUM').length
                const low = risk.risks.length - high - med
                return (
                  <div className="grid-3 mb-4">
                    <div style={{padding:12,border:'1px solid var(--border)',borderRadius:8,textAlign:'center'}}>
                      <div style={{fontSize:28,fontWeight:800,color:'var(--red)'}}>{high}</div>
                      <div className="text-xs text-muted">High Risk</div>
                    </div>
                    <div style={{padding:12,border:'1px solid var(--border)',borderRadius:8,textAlign:'center'}}>
                      <div style={{fontSize:28,fontWeight:800,color:'var(--amber)'}}>{med}</div>
                      <div className="text-xs text-muted">Medium</div>
                    </div>
                    <div style={{padding:12,border:'1px solid var(--border)',borderRadius:8,textAlign:'center'}}>
                      <div style={{fontSize:28,fontWeight:800,color:'var(--green)'}}>{low}</div>
                      <div className="text-xs text-muted">Low Risk</div>
                    </div>
                  </div>
                )
              })()}
              <div style={{display:'flex',gap:2,height:40,alignItems:'flex-end'}}>
                {risk.risks.map((r:any, i:number) => (
                  <div key={i} style={{flex:1}}>
                    <div className={`risk-bar ${r.risk==='HIGH'?'risk-high':r.risk==='MEDIUM'?'risk-medium':'risk-low'}`}
                         style={{height: r.risk==='HIGH'?40:r.risk==='MEDIUM'?24:12}}></div>
                  </div>
                ))}
              </div>
            </div>
          ) : <div className="text-sm text-muted">Loading risk data...</div>}
        </div>
      </div>
    </div>
  )
}
function ForecastPage({ site }: { site: Site }) {
  const [horizon, setHorizon] = useState(24)
  const [data, setData] = useState<any>(null)

  useEffect(() => {
    if (!site) return
    setData(null)
    getForecast(site.id, horizon).then(r => setData(r.data)).catch(() => {})
  }, [site, horizon])

  return (
    <div className="animate-fadeIn">
      <div className="page-header flex-between">
        <div>
          <div className="page-title">Generation Forecast</div>
          <div className="page-subtitle">Solar irradiance and generation prediction with uncertainty quantification</div>
        </div>
        <div className="tabs">
          {[24, 48, 72].map(h => (
            <button key={h} className={`tab ${horizon === h ? 'active' : ''}`} onClick={() => setHorizon(h)}>
              {h}h
            </button>
          ))}
        </div>
      </div>

      {data ? (
        <>
          <div className="card">
            <div className="card-title">Power Output Forecast (kW)</div>
            <div style={{display:'flex',gap:2,alignItems:'flex-end',height:200}}>
              {data.forecast.p50.map((v:number, i:number) => {
                const maxVal = Math.max(...data.forecast.p90, 1)
                const p10 = data.forecast.p10[i]
                const p90 = data.forecast.p90[i]
                return (
                  <div key={i} style={{flex:1,display:'flex',flexDirection:'column',alignItems:'center'}}>
                    <div style={{width:'100%',background:'var(--accent-light)',borderRadius:4,height:((p90-p10)/maxVal)*180,position:'relative'}}>
                      <div style={{position:'absolute',bottom:0,width:'100%',background:'var(--accent)',borderRadius:4,height:Math.max(3,(v/maxVal)*180),opacity:0.85}}></div>
                    </div>
                    {i%6===0 && <span className="text-xs text-muted" style={{marginTop:4}}>{String(i).padStart(2,'0')}:00</span>}
                  </div>
                )
              })}
            </div>
            <div className="flex-center gap-6 mt-3" style={{justifyContent:'center'}}>
              <div className="flex-center gap-2"><div style={{width:16,height:6,background:'var(--accent)',borderRadius:3}}></div><span className="text-xs text-muted">P50 (Median)</span></div>
              <div className="flex-center gap-2"><div style={{width:16,height:12,background:'var(--accent-light)',borderRadius:3}}></div><span className="text-xs text-muted">P10-P90 (80% CI)</span></div>
            </div>
          </div>

          <div className="grid-3">
            <div className="card" style={{textAlign:'center'}}>
              <div className="text-xs text-muted mb-2">Total Generation</div>
              <div className="kpi-value" style={{fontSize:24}}>{data.forecast.p50.reduce((a:number,b:number)=>a+b,0).toFixed(1)}</div>
              <div className="text-xs text-muted">kWh over {horizon}h</div>
            </div>
            <div className="card" style={{textAlign:'center'}}>
              <div className="text-xs text-muted mb-2">Peak Output</div>
              <div className="kpi-value" style={{fontSize:24,color:'var(--accent)'}}>{Math.max(...data.forecast.p50).toFixed(1)}</div>
              <div className="text-xs text-muted">kW</div>
            </div>
            <div className="card" style={{textAlign:'center'}}>
              <div className="text-xs text-muted mb-2">Uncertainty Width</div>
              <div className="kpi-value" style={{fontSize:24,color:'var(--amber)'}}>{((data.forecast.p90.reduce((a:number,b:number)=>a+b,0) - data.forecast.p10.reduce((a:number,b:number)=>a+b,0)) / (data.forecast.p50.reduce((a:number,b:number)=>a+b,0) || 1) * 100).toFixed(0)}%</div>
              <div className="text-xs text-muted">Avg P10-P90 spread</div>
            </div>
          </div>
        </>
      ) : (
        <div className="card"><div className="empty-state"><div className="empty-icon"><BarChart3 /></div><div className="empty-title">Loading forecast data...</div></div></div>
      )}
    </div>
  )
}

// ─── Risk Page ────────────────────────────────────────────────
function RiskPage({ site }: { site: Site }) {
  const [data, setData] = useState<any>(null)
  const [horizon, setHorizon] = useState(24)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!site) return
    setLoading(true)
    getRisk(site.id, horizon).then(r => {
      setData(r.data)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [site, horizon])

  if (loading) {
    return (
      <div className="animate-fadeIn">
        <div className="page-header">
          <div className="page-title">Risk Analysis</div>
          <div className="page-subtitle">Curtailment, deficit, and battery risk assessment</div>
        </div>
        <div className="card"><div className="empty-state"><div className="empty-icon"><Loader2 className="animate-spin" /></div><div className="empty-title">Analyzing risks...</div></div></div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="animate-fadeIn">
        <div className="page-header">
          <div className="page-title">Risk Analysis</div>
          <div className="page-subtitle">Curtailment, deficit, and battery risk assessment</div>
        </div>
        <div className="card"><div className="empty-state"><div className="empty-icon"><ShieldAlert /></div><div className="empty-title">No risk data available</div><div className="empty-desc">Sync weather data first to enable risk analysis.</div></div></div>
      </div>
    )
  }

  const risks = data.risks || []
  const highRisks = risks.filter((r: any) => r.risk === 'HIGH')
  const medRisks = risks.filter((r: any) => r.risk === 'MEDIUM')
  const lowRisks = risks.filter((r: any) => r.risk === 'LOW')
  const peakGen = Math.max(...risks.map((r: any) => r.generation_kw))
  const totalEnergy = risks.reduce((sum: number, r: any) => sum + r.generation_kw, 0)
  const margin = site.export_limit_kw - peakGen
  const isCurtailmentRisk = highRisks.length > 0

  // Financial impact
  const GRID_TARIFF = 7.5
  const potentialLoss = highRisks.reduce((sum: number, r: any) => sum + r.generation_kw * GRID_TARIFF, 0)

  return (
    <div className="animate-fadeIn">
      <div className="page-header flex-between">
        <div>
          <div className="page-title">Risk Analysis</div>
          <div className="page-subtitle">Curtailment, deficit, and battery risk for {site.name}</div>
        </div>
        <div className="tabs">
          {[24, 48, 72].map(h => (
            <button key={h} className={`tab ${horizon === h ? 'active' : ''}`} onClick={() => setHorizon(h)}>{h}h</button>
          ))}
        </div>
      </div>

      {/* Risk KPIs */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-icon" style={{background: isCurtailmentRisk ? '#fce8e6' : '#e6f4ea', color: isCurtailmentRisk ? '#c5221f' : '#0d904f'}}>
            <ShieldAlert />
          </div>
          <div className="kpi-value" style={{color: isCurtailmentRisk ? '#c5221f' : '#0d904f'}}>
            {isCurtailmentRisk ? 'AT RISK' : 'CLEAR'}
          </div>
          <div className="kpi-label">Curtailment Status</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon" style={{background:'#fce8e6',color:'#c5221f'}}><TrendingUp /></div>
          <div className="kpi-value" style={{color:'#c5221f'}}>{highRisks.length}</div>
          <div className="kpi-label">High Risk Hours</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon" style={{background:'#e8f0fe',color:'#1a73e8'}}><Zap /></div>
          <div className="kpi-value">{peakGen.toFixed(1)} <span style={{fontSize:14,fontWeight:500}}>kW</span></div>
          <div className="kpi-label">Peak Generation</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon" style={{background: margin >= 0 ? '#e6f4ea' : '#fce8e6', color: margin >= 0 ? '#0d904f' : '#c5221f'}}><BatteryCharging /></div>
          <div className="kpi-value" style={{color: margin >= 0 ? '#0d904f' : '#c5221f'}}>{margin.toFixed(1)} <span style={{fontSize:14,fontWeight:500}}>kW</span></div>
          <div className="kpi-label">Margin to Limit</div>
        </div>
      </div>

      {/* Risk Summary Bar */}
      <div className="card">
        <div className="flex-between mb-4">
          <div className="card-title" style={{marginBottom:0}}>Risk Distribution</div>
          <div style={{display:'flex',gap:10}}>
            <span className="badge badge-red">{highRisks.length} HIGH</span>
            <span className="badge badge-amber">{medRisks.length} MEDIUM</span>
            <span className="badge badge-green">{lowRisks.length} LOW</span>
          </div>
        </div>
        <div style={{display:'flex',height:32,borderRadius:8,overflow:'hidden',gap:2}}>
          {highRisks.length > 0 && <div style={{flex:highRisks.length,background:'#c5221f',borderRadius:6,display:'flex',alignItems:'center',justifyContent:'center',color:'white',fontSize:12,fontWeight:700}}>{highRisks.length}</div>}
          {medRisks.length > 0 && <div style={{flex:medRisks.length,background:'#e8710a',borderRadius:6,display:'flex',alignItems:'center',justifyContent:'center',color:'white',fontSize:12,fontWeight:700}}>{medRisks.length}</div>}
          {lowRisks.length > 0 && <div style={{flex:lowRisks.length,background:'#0d904f',borderRadius:6,display:'flex',alignItems:'center',justifyContent:'center',color:'white',fontSize:12,fontWeight:700}}>{lowRisks.length}</div>}
        </div>
        <div style={{display:'flex',justifyContent:'space-between',marginTop:8}}>
          <span style={{fontSize:12,color:'#5f6368'}}>Export limit: {site.export_limit_kw} kW</span>
          <span style={{fontSize:12,color:'#5f6368'}}>Total energy: {totalEnergy.toFixed(1)} kWh over {horizon}h</span>
        </div>
      </div>

      {/* Hourly Risk Chart */}
      <div className="card">
        <div className="card-title">Hourly Risk Timeline</div>
        <div style={{display:'flex',gap:2,alignItems:'flex-end',height:180,padding:'0 4px'}}>
          {risks.map((r: any, i: number) => {
            const maxGen = Math.max(...risks.map((x: any) => x.generation_kw), 1)
            const height = (r.generation_kw / maxGen) * 160
            const color = r.risk === 'HIGH' ? '#c5221f' : r.risk === 'MEDIUM' ? '#e8710a' : '#0d904f'
            return (
              <div key={i} style={{flex:1,display:'flex',flexDirection:'column',alignItems:'center',gap:4}}>
                <div style={{fontSize:10,color:'#5f6368',fontWeight:500}}>{r.generation_kw.toFixed(0)}</div>
                <div style={{width:'100%',height:height,background:color,borderRadius:'4px 4px 0 0',minHeight:2,transition:'height 0.3s'}}></div>
                {i % (horizon <= 24 ? 3 : horizon <= 48 ? 6 : 12) === 0 && (
                  <span style={{fontSize:10,color:'#9aa0a6'}}>{String(i % 24).padStart(2,'0')}:00</span>
                )}
              </div>
            )
          })}
        </div>
        <div style={{display:'flex',justifyContent:'center',gap:20,marginTop:12}}>
          <div style={{display:'flex',alignItems:'center',gap:6}}><div style={{width:12,height:12,borderRadius:3,background:'#0d904f'}}></div><span style={{fontSize:12,color:'#5f6368'}}>LOW</span></div>
          <div style={{display:'flex',alignItems:'center',gap:6}}><div style={{width:12,height:12,borderRadius:3,background:'#e8710a'}}></div><span style={{fontSize:12,color:'#5f6368'}}>MEDIUM</span></div>
          <div style={{display:'flex',alignItems:'center',gap:6}}><div style={{width:12,height:12,borderRadius:3,background:'#c5221f'}}></div><span style={{fontSize:12,color:'#5f6368'}}>HIGH</span></div>
        </div>
      </div>

      {/* Detailed Hourly Table */}
      <div className="card">
        <div className="card-title">Hourly Risk Detail</div>
        <div style={{maxHeight:400,overflowY:'auto'}}>
          <table style={{width:'100%',borderCollapse:'collapse',fontSize:13}}>
            <thead>
              <tr style={{borderBottom:'2px solid #e0e0e0'}}>
                <th style={{padding:'10px 12px',textAlign:'left',fontWeight:600,color:'#5f6368',fontSize:12}}>Hour</th>
                <th style={{padding:'10px 12px',textAlign:'left',fontWeight:600,color:'#5f6368',fontSize:12}}>Generation</th>
                <th style={{padding:'10px 12px',textAlign:'left',fontWeight:600,color:'#5f6368',fontSize:12}}>Risk Level</th>
                <th style={{padding:'10px 12px',textAlign:'left',fontWeight:600,color:'#5f6368',fontSize:12}}>Action</th>
                <th style={{padding:'10px 12px',textAlign:'left',fontWeight:600,color:'#5f6368',fontSize:12}}>Status</th>
              </tr>
            </thead>
            <tbody>
              {risks.map((r: any, i: number) => (
                <tr key={i} style={{borderBottom:'1px solid #f1f3f4',background: r.risk === 'HIGH' ? '#fce8e608' : 'transparent'}}>
                  <td style={{padding:'10px 12px',fontWeight:600,color:'#202124'}}>{String(i).padStart(2,'0')}:00</td>
                  <td style={{padding:'10px 12px',fontWeight:600,color:'#202124'}}>{r.generation_kw.toFixed(1)} kW</td>
                  <td style={{padding:'10px 12px'}}>
                    <span className={`badge ${r.risk === 'HIGH' ? 'badge-red' : r.risk === 'MEDIUM' ? 'badge-amber' : 'badge-green'}`}>
                      {r.risk}
                    </span>
                  </td>
                  <td style={{padding:'10px 12px',color:'#5f6368',textTransform:'capitalize'}}>{r.action.replace(/_/g, ' ')}</td>
                  <td style={{padding:'10px 12px'}}>
                    <div style={{height:6,borderRadius:3,background:'#f1f3f4',width:80}}>
                      <div style={{height:'100%',borderRadius:3,background:r.risk === 'HIGH' ? '#c5221f' : r.risk === 'MEDIUM' ? '#e8710a' : '#0d904f',width:`${(r.generation_kw / site.export_limit_kw) * 100}%`}}></div>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Risk Mitigation */}
      <div className="grid-2">
        <div className="card">
          <div className="card-title">Financial Impact</div>
          <div style={{padding:20,background: isCurtailmentRisk ? '#fce8e6' : '#e6f4ea',borderRadius:12,marginBottom:16}}>
            <div style={{fontSize:12,color:'#5f6368',marginBottom:4}}>{isCurtailmentRisk ? 'Potential curtailment loss' : 'No curtailment risk'}</div>
            <div style={{fontSize:28,fontWeight:800,color: isCurtailmentRisk ? '#c5221f' : '#0d904f'}}>
              ₹{potentialLoss.toFixed(0)}<span style={{fontSize:14,fontWeight:500}}>/day</span>
            </div>
          </div>
          <div className="flex-between" style={{padding:'10px 0',borderBottom:'1px solid #f1f3f4'}}>
            <span style={{fontSize:13,color:'#5f6368'}}>Export limit</span>
            <span style={{fontSize:13,fontWeight:600}}>{site.export_limit_kw} kW</span>
          </div>
          <div className="flex-between" style={{padding:'10px 0',borderBottom:'1px solid #f1f3f4'}}>
            <span style={{fontSize:13,color:'#5f6368'}}>Peak generation</span>
            <span style={{fontSize:13,fontWeight:600}}>{peakGen.toFixed(1)} kW</span>
          </div>
          <div className="flex-between" style={{padding:'10px 0'}}>
            <span style={{fontSize:13,color:'#5f6368'}}>Margin</span>
            <span style={{fontSize:13,fontWeight:600,color: margin >= 0 ? '#0d904f' : '#c5221f'}}>{margin.toFixed(1)} kW</span>
          </div>
        </div>

        <div className="card">
          <div className="card-title">Risk Mitigation</div>
          {isCurtailmentRisk ? (
            <div>
              <div style={{padding:14,background:'#fef7e0',borderRadius:10,marginBottom:12,borderLeft:'4px solid #e8710a'}}>
                <div style={{fontSize:13,fontWeight:700,color:'#e8710a',marginBottom:4}}>⚡ Battery Charging Recommended</div>
                <div style={{fontSize:12,color:'#5f6368'}}>Charge battery during {highRisks.length} high-risk hours to absorb excess generation.</div>
              </div>
              <div style={{padding:14,background:'#e8f0fe',borderRadius:10,marginBottom:12,borderLeft:'4px solid #1a73e8'}}>
                <div style={{fontSize:13,fontWeight:700,color:'#1a73e8',marginBottom:4}}>📊 Export Scheduling</div>
                <div style={{fontSize:12,color:'#5f6368'}}>Shift export to low-risk hours when generation is within grid limits.</div>
              </div>
              <div style={{padding:14,background:'#f3e8ff',borderRadius:10,borderLeft:'4px solid #8b5cf6'}}>
                <div style={{fontSize:13,fontWeight:700,color:'#8b5cf6',marginBottom:4}}>🔧 Demand Response</div>
                <div style={{fontSize:12,color:'#5f6368'}}>Increase on-site consumption during peak generation hours.</div>
              </div>
            </div>
          ) : (
            <div>
              <div style={{padding:14,background:'#e6f4ea',borderRadius:10,marginBottom:12,borderLeft:'4px solid #0d904f'}}>
                <div style={{fontSize:13,fontWeight:700,color:'#0d904f',marginBottom:4}}>✅ No Curtailment Risk</div>
                <div style={{fontSize:12,color:'#5f6368'}}>Generation stays within grid export limits. All energy can be exported or self-consumed.</div>
              </div>
              <div style={{padding:14,background:'#e8f0fe',borderRadius:10,borderLeft:'4px solid #1a73e8'}}>
                <div style={{fontSize:13,fontWeight:700,color:'#1a73e8',marginBottom:4}}>📈 Capacity Expansion Opportunity</div>
                <div style={{fontSize:12,color:'#5f6368'}}>You have {margin.toFixed(1)} kW margin. Consider adding {Math.floor(margin)} kW more capacity.</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ─── Optimize Page ────────────────────────────────────────────
function OptimizePage({ site }: { site: Site }) {
  const [cloud, setCloud] = useState(0)
  const [wind, setWind] = useState(0)
  const [soc, setSoc] = useState('')
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const simulate = () => {
    setLoading(true)
    runScenario(site.id, {
      cloud_cover_delta: cloud,
      wind_speed_delta: wind,
      battery_soc_override: soc ? Number(soc) : undefined,
    }).then(r => setResult(r.data)).finally(() => setLoading(false))
  }

  return (
    <div className="animate-fadeIn">
      <div className="page-header">
        <div className="page-title">Optimize & Simulate</div>
        <div className="page-subtitle">Run what-if scenarios with adjustable weather and battery parameters</div>
      </div>

      <div className="grid-2">
        {/* Controls */}
        <div className="card">
          <div className="card-title">Scenario Parameters</div>
          <div style={{marginBottom:20}}>
            <div className="flex-between mb-2">
              <span className="text-xs text-muted">Cloud Cover Change</span>
              <span className="text-sm font-bold" style={{color: cloud > 0 ? 'var(--amber)' : cloud < 0 ? 'var(--green)' : 'var(--text3)'}}>
                {cloud > 0 ? '+' : ''}{cloud}%
              </span>
            </div>
            <input type="range" min={-50} max={50} value={cloud} onChange={e => setCloud(Number(e.target.value))} style={{width:'100%',accentColor:'var(--accent)'}} />
            <div className="flex-between text-xs text-muted"><span>Clearer</span><span>Cloudier</span></div>
          </div>
          <div style={{marginBottom:20}}>
            <div className="flex-between mb-2">
              <span className="text-xs text-muted">Wind Speed Change</span>
              <span className="text-sm font-bold" style={{color: wind > 0 ? 'var(--green)' : wind < 0 ? 'var(--amber)' : 'var(--text3)'}}>
                {wind > 0 ? '+' : ''}{wind}%
              </span>
            </div>
            <input type="range" min={-50} max={50} value={wind} onChange={e => setWind(Number(e.target.value))} style={{width:'100%',accentColor:'var(--accent)'}} />
            <div className="flex-between text-xs text-muted"><span>Calm</span><span>Strong</span></div>
          </div>
          <div style={{marginBottom:20}}>
            <div className="text-xs text-muted mb-2">Battery SOC Override (%)</div>
            <input className="input" type="number" value={soc} onChange={e => setSoc(e.target.value)} placeholder="Auto (50%)" min={0} max={100} />
          </div>
          <button className="btn btn-primary w-full" onClick={simulate} disabled={loading}>
            {loading ? <><Loader2 className="animate-spin" size={14} /> Simulating...</> : <><Play size={14} /> Run Simulation</>}
          </button>
        </div>

        {/* Results */}
        <div className="card">
          <div className="card-title">Simulation Result</div>
          {result ? (
            <div>
              <div style={{padding:20,background:'var(--bg3)',borderRadius:12,marginBottom:16}}>
                <div className="grid-2 mb-3">
                  <div>
                    <div className="text-xs text-muted mb-1">Adjusted Generation</div>
                    <div className="kpi-value" style={{fontSize:24}}>{result.adjusted_generation_kw.toFixed(1)} <span style={{fontSize:12}}>kW</span></div>
                  </div>
                  <div>
                    <div className="text-xs text-muted mb-1">Recommended Action</div>
                    <div className="kpi-value" style={{fontSize:16,textTransform:'capitalize',color: result.action.includes('charge')?'var(--green)':result.action.includes('curtail')?'var(--red)':'var(--accent)'}}>
                      {result.action.replace(/_/g,' ')}
                    </div>
                  </div>
                </div>
              </div>
              <div className="text-sm" style={{color:'var(--text2)',lineHeight:1.7,marginBottom:16}}>{result.explanation}</div>
              <div className="grid-2">
                <div style={{padding:12,border:'1px solid var(--border)',borderRadius:8}}>
                  <div className="text-xs text-muted">Financial Impact</div>
                  <div className="kpi-value" style={{fontSize:20,color: result.financial_impact_inr >= 0 ? 'var(--green)' : 'var(--red)'}}>
                    ₹{result.financial_impact_inr.toFixed(0)}
                  </div>
                </div>
                <div style={{padding:12,border:'1px solid var(--border)',borderRadius:8}}>
                  <div className="text-xs text-muted">CO₂ Impact</div>
                  <div className="kpi-value" style={{fontSize:20,color: result.co2_impact_tonnes >= 0 ? 'var(--green)' : 'var(--red)'}}>
                    {result.co2_impact_tonnes >= 0 ? '+' : ''}{result.co2_impact_tonnes.toFixed(3)} t
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="empty-state">
              <div className="empty-icon"><Zap /></div>
              <div className="empty-title">No simulation yet</div>
              <div className="empty-desc">Adjust parameters on the left and click "Run Simulation" to see results.</div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ─── Anomalies Page ───────────────────────────────────────────
function AnomaliesPage() {
  const anomalies = [
    { id: '1', type: 'Spike', severity: 'high', desc: 'Generation +52% above rated capacity for 3 consecutive readings', time: '14:00', auto: false },
    { id: '2', type: 'Drop', severity: 'medium', desc: 'Sudden generation drop from 85kW to 12kW during peak irradiance', time: '08:30', auto: true },
    { id: '3', type: 'Gap', severity: 'low', desc: 'Missing weather data from Open-Meteo for 3 hours (API timeout)', time: '22:00', auto: true },
    { id: '4', type: 'Zero Output', severity: 'high', desc: 'Zero generation despite 800W/m² irradiance — possible inverter fault', time: '11:00', auto: false },
    { id: '5', type: 'Sensor Drift', severity: 'medium', desc: 'Temperature sensor reading 10°C above ambient average', time: '16:00', auto: true },
    { id: '6', type: 'Calibration', severity: 'low', desc: 'Irradiance sensor deviating 8% from satellite reference', time: '13:30', auto: true },
  ]
  const icons: Record<string, any> = {
    Spike: TrendingUp, Drop: TrendingDown, Gap: Link2,
    'Zero Output': Power, 'Sensor Drift': Thermometer, Calibration: Crosshair,
  }

  return (
    <div className="animate-fadeIn">
      <div className="page-header">
        <div className="page-title">Anomaly Detection</div>
        <div className="page-subtitle">Real-time data quality monitoring and automatic correction</div>
      </div>

      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-icon" style={{background:'var(--accent-light)',color:'var(--accent)'}}><ScanSearch /></div>
          <div className="kpi-value">{anomalies.length}</div>
          <div className="kpi-label">Total Anomalies</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon" style={{background:'var(--red-light)',color:'var(--red)'}}><ShieldAlert /></div>
          <div className="kpi-value" style={{color:'var(--red)'}}>{anomalies.filter(a => a.severity === 'high').length}</div>
          <div className="kpi-label">High Severity</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon" style={{background:'var(--green-light)',color:'var(--green)'}}><CheckCircle2 /></div>
          <div className="kpi-value" style={{color:'var(--green)'}}>{anomalies.filter(a => a.auto).length}</div>
          <div className="kpi-label">Auto-Fixed</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon" style={{background:'#f0f9ff',color:'#0284c7'}}><BarChart3 /></div>
          <div className="kpi-value">94.2%</div>
          <div className="kpi-label">Data Quality Score</div>
        </div>
      </div>

      <div className="card">
        <div className="card-title">Detected Anomalies</div>
        {anomalies.map(a => {
          const Icon = icons[a.type] || HelpCircle
          return (
            <div key={a.id} className="anomaly-row">
              <div style={{width:36,textAlign:'center',color:'var(--accent)'}}><Icon size={20} /></div>
              <div style={{flex:1}}>
                <div className="flex-center gap-2">
                  <span className="text-sm font-medium">{a.type}</span>
                  <span className={`badge badge-${a.severity === 'high' ? 'red' : a.severity === 'medium' ? 'amber' : 'default'}`}>{a.severity}</span>
                  {a.auto && <span className="badge badge-green">Auto-fixed</span>}
                </div>
                <div className="text-xs text-muted mt-2">{a.desc}</div>
              </div>
              <div className="text-xs text-muted">{a.time}</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ─── Data Sources Page ────────────────────────────────────────
function DataPage({ site }: { site: Site }) {
  const [dataStatus, setDataStatus] = useState<any>(null)
  const [weatherInsights, setWeatherInsights] = useState<any>(null)
  const [modelHealth, setModelHealth] = useState<any>(null)
  const [syncing, setSyncing] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!site) return
    setLoading(true)
    Promise.all([
      getDataStatus(site.id).catch(() => ({ data: null })),
      getWeatherInsights(site.id).catch(() => ({ data: null })),
      getModelHealth().catch(() => ({ data: null })),
    ]).then(([ds, wi, mh]) => {
      setDataStatus(ds.data)
      setWeatherInsights(wi.data)
      setModelHealth(mh.data)
      setLoading(false)
    })
  }, [site])

  const handleSync = async () => {
    if (!site) return
    setSyncing(true)
    try {
      await syncWeatherData(site.id)
      const ds = await getDataStatus(site.id)
      setDataStatus(ds.data)
      toast.success('Weather data synced')
    } catch (e) {
      toast.error('Sync failed')
    } finally {
      setSyncing(false)
    }
  }

  if (loading) {
    return (
      <div className="animate-fadeIn">
        <div className="page-header">
          <div className="page-title">Data Sources</div>
          <div className="page-subtitle">Connected feeds, datasets, and model registry</div>
        </div>
        <div className="card"><div className="empty-state"><div className="empty-icon"><Loader2 className="animate-spin" /></div><div className="empty-title">Loading data sources...</div></div></div>
      </div>
    )
  }

  const totalRecords = dataStatus?.weather_records || 0
  const latestTs = dataStatus?.latest_timestamp
  const oldestTs = dataStatus?.oldest_timestamp
  const dataQuality = weatherInsights?.data?.['quality_%'] || 0
  const isStale = weatherInsights?.data?.stale || false
  const lastUpdatedMin = weatherInsights?.data?.last_updated_minutes_ago
  const weatherSource = weatherInsights?.source || 'unknown'
  const modelStatus = modelHealth?.status || 'UNKNOWN'
  const modelVersion = modelHealth?.version || '—'
  const modelDrift = modelHealth?.data_drift || '—'

  const sources = [
    {
      name: 'Open-Meteo API',
      type: 'Live Forecast',
      status: weatherSource === 'open-meteo' ? 'connected' : 'fallback',
      icon: RefreshCw,
      color: '#0d904f',
      fields: ['GHI (shortwave_radiation)', 'DNI (direct_normal_irradiance)', 'DHI (global_tilted_irradiance)', 'Temperature', 'Wind Speed/Direction', 'Cloud Cover', 'Humidity', 'Pressure'],
      detail: weatherSource === 'open-meteo' ? 'Live API connected — real-time forecast data' : 'Using physics baseline — API unavailable',
      refreshRate: '1 hour (forecast) / Daily (archive)',
    },
    {
      name: 'Weather Database',
      type: 'Historical Store',
      status: totalRecords > 0 ? 'active' : 'empty',
      icon: Database,
      color: '#1a73e8',
      fields: ['Hourly timestamps', 'All irradiance components', 'Temperature & wind', 'Cloud cover & humidity'],
      detail: totalRecords > 0
        ? `${totalRecords.toLocaleString()} records · ${oldestTs ? new Date(oldestTs).toLocaleDateString() : '—'} to ${latestTs ? new Date(latestTs).toLocaleDateString() : '—'}`
        : 'No weather data synced yet',
      refreshRate: 'On-demand sync',
    },
    {
      name: 'SURGE ML Models',
      type: 'Forecasting Engine',
      status: modelStatus === 'HEALTHY' ? 'ready' : 'warning',
      icon: Zap,
      color: '#8b5cf6',
      fields: ['XGBoost (solar)', 'LightGBM (wind)', 'Quantile regression (P10/P50/P90)', 'Physics-informed features'],
      detail: `Version ${modelVersion} · Drift: ${modelDrift} · ${modelStatus}`,
      refreshRate: 'Retrained on demand',
    },
    {
      name: 'CSV Import',
      type: 'Manual Upload',
      status: 'available',
      icon: Upload,
      color: '#e8710a',
      fields: ['Custom weather data', 'Generation logs', 'Sensor readings'],
      detail: 'Upload CSV files to supplement API data (max 10MB)',
      refreshRate: 'Manual',
    },
  ]

  return (
    <div className="animate-fadeIn">
      <div className="page-header flex-between">
        <div>
          <div className="page-title">Data Sources</div>
          <div className="page-subtitle">Connected feeds, datasets, and model registry for {site.name}</div>
        </div>
        <button className="btn btn-primary" onClick={handleSync} disabled={syncing}>
          {syncing ? <><Loader2 size={14} className="animate-spin" /> Syncing...</> : <><RefreshCw size={14} /> Sync Weather</>}
        </button>
      </div>

      {/* KPI Row */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-icon" style={{background:'#e8f0fe',color:'#1a73e8'}}><Database /></div>
          <div className="kpi-value">{totalRecords.toLocaleString()}</div>
          <div className="kpi-label">Weather Records</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon" style={{background:'#e6f4ea',color:'#0d904f'}}><CheckCircle2 /></div>
          <div className="kpi-value" style={{color: dataQuality >= 90 ? '#0d904f' : '#e8710a'}}>{dataQuality}%</div>
          <div className="kpi-label">Data Quality</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon" style={{background: isStale ? '#fce8e6' : '#e6f4ea', color: isStale ? '#c5221f' : '#0d904f'}}><RefreshCw /></div>
          <div className="kpi-value" style={{color: isStale ? '#c5221f' : '#0d904f', fontSize: isStale ? 20 : 30}}>
            {isStale ? `${lastUpdatedMin}m ago` : 'Live'}
          </div>
          <div className="kpi-label">{isStale ? 'Data Stale' : 'Data Fresh'}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon" style={{background:'#f3e8ff',color:'#8b5cf6'}}><Zap /></div>
          <div className="kpi-value" style={{color: modelStatus === 'HEALTHY' ? '#0d904f' : '#e8710a'}}>{modelStatus}</div>
          <div className="kpi-label">Model Status</div>
        </div>
      </div>

      {/* Data Source Cards */}
      {sources.map((s, i) => {
        const Icon = s.icon
        const statusColor = s.status === 'connected' || s.status === 'active' || s.status === 'ready' ? '#0d904f' : s.status === 'fallback' || s.status === 'warning' ? '#e8710a' : '#5f6368'
        return (
          <div key={i} className="card" style={{marginBottom: 16}}>
            <div className="flex-between" style={{alignItems: 'flex-start'}}>
              <div style={{display:'flex',gap:14,alignItems:'flex-start',flex:1}}>
                <div style={{width:44,height:44,borderRadius:12,background:s.color+'18',color:s.color,display:'flex',alignItems:'center',justifyContent:'center',flexShrink:0}}>
                  <Icon size={22} />
                </div>
                <div style={{flex:1}}>
                  <div style={{display:'flex',alignItems:'center',gap:10,marginBottom:4}}>
                    <span style={{fontSize:15,fontWeight:700,color:'#202124'}}>{s.name}</span>
                    <span className={`badge ${s.status === 'connected' || s.status === 'active' || s.status === 'ready' ? 'badge-green' : s.status === 'fallback' || s.status === 'warning' ? 'badge-amber' : 'badge-default'}`}>{s.status}</span>
                    <span className="badge badge-default">{s.type}</span>
                  </div>
                  <div style={{fontSize:13,color:'#5f6368',marginBottom:10}}>{s.detail}</div>
                  <div style={{display:'flex',flexWrap:'wrap',gap:6}}>
                    {s.fields.map((f, j) => (
                      <span key={j} style={{fontSize:12,padding:'3px 10px',background:'#f1f3f4',borderRadius:6,color:'#3c4043',fontWeight:500}}>{f}</span>
                    ))}
                  </div>
                  <div style={{fontSize:12,color:'#9aa0a6',marginTop:8}}>Refresh: {s.refreshRate}</div>
                </div>
              </div>
            </div>
          </div>
        )
      })}

      {/* Lambda Architecture */}
      <div className="card">
        <div className="card-title">Lambda Architecture Pipeline</div>
        <div style={{display:'flex',gap:8,overflowX:'auto',paddingBottom:8,justifyContent:'center',flexWrap:'wrap'}}>
          {[
            { label: 'Open-Meteo API', sub: 'Live + Archive', color: '#1a73e8', icon: '🌐' },
            { label: 'CSV Import', sub: 'Manual upload', color: '#e8710a', icon: '📄' },
            { label: 'Speed Layer', sub: 'Real-time processing', color: '#0d904f', icon: '⚡' },
            { label: 'Batch Layer', sub: 'Historical analysis', color: '#8b5cf6', icon: '📦' },
            { label: 'SQLite DB', sub: 'Unified storage', color: '#5f6368', icon: '🗄️' },
            { label: 'SURGE Models', sub: 'XGBoost + Quantile', color: '#c5221f', icon: '🤖' },
            { label: 'Dashboard', sub: 'Real-time views', color: '#0284c7', icon: '📊' },
          ].map((step, i) => (
            <div key={i} style={{display:'flex',alignItems:'center',gap:8}}>
              <div style={{padding:'14px 18px',border:`1.5px solid ${step.color}30`,borderRadius:12,minWidth:140,textAlign:'center',background:step.color+'08'}}>
                <div style={{fontSize:22,marginBottom:6}}>{step.icon}</div>
                <div style={{fontSize:13,fontWeight:700,color:'#202124'}}>{step.label}</div>
                <div style={{fontSize:11,color:'#5f6368',marginTop:2}}>{step.sub}</div>
              </div>
              {i < 6 && <span style={{color:'#dadce0',fontSize:22,flexShrink:0}}>→</span>}
            </div>
          ))}
        </div>
      </div>

      {/* Data Freshness Timeline */}
      {latestTs && (
        <div className="card">
          <div className="card-title">Data Freshness</div>
          <div className="grid-2">
            <div style={{padding:16,border:'1px solid #e0e0e0',borderRadius:10}}>
              <div style={{fontSize:12,color:'#5f6368',fontWeight:600,marginBottom:4}}>Oldest Record</div>
              <div style={{fontSize:14,fontWeight:600,color:'#202124'}}>{oldestTs ? new Date(oldestTs).toLocaleString() : '—'}</div>
            </div>
            <div style={{padding:16,border:'1px solid #e0e0e0',borderRadius:10}}>
              <div style={{fontSize:12,color:'#5f6368',fontWeight:600,marginBottom:4}}>Latest Record</div>
              <div style={{fontSize:14,fontWeight:600,color:'#202124'}}>{latestTs ? new Date(latestTs).toLocaleString() : '—'}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ─── Insights Page ─────────────────────────────────────────────
function InsightsPage({ site }: { site: Site }) {
  const [accuracy, setAccuracy] = useState<any>(null)
  const [alerts, setAlerts] = useState<any[]>([])
  const [model, setModel] = useState<any>(null)
  const [weather, setWeather] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    ;(async () => {
      try {
        const [acc, alr, mdl, wth] = await Promise.all([
          getForecastAccuracy(site.id),
          getAlerts(),
          getModelHealth(),
          getWeatherInsights(site.id),
        ])
        if (cancelled) return
        setAccuracy(acc.data)
        setAlerts(alr.data.alerts || [])
        setModel(mdl.data)
        setWeather(wth.data)
      } catch (e) {
        if (!cancelled) toast('Failed to load insights', { icon: <ShieldAlert className="h-4 w-4 text-red-600" /> })
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => { cancelled = true }
  }, [site.id])

  if (loading) {
    return (
      <div className="empty-state">
        <div className="empty-icon"><Loader2 size={30} className="animate-spin" /></div>
        <div className="empty-title">Analyzing your site…</div>
        <div className="empty-desc">Computing forecast accuracy, model health, and weather intelligence.</div>
      </div>
    )
  }

  const reliability = accuracy?.overall?.['reliability_%'] ?? 0

  const severityStyle: Record<string, { badge: string; color: string; bg: string }> = {
    critical: { badge: 'badge-red', color: 'var(--red)', bg: 'var(--red-light)' },
    warning: { badge: 'badge-amber', color: 'var(--amber)', bg: 'var(--amber-light)' },
    info: { badge: 'badge-default', color: 'var(--accent)', bg: 'var(--accent-light)' },
  }

  return (
    <div className="animate-fadeIn">
      <div className="page-header">
        <div className="page-title">Forecast Intelligence</div>
        <div className="page-subtitle">Accuracy report, model health, alerts, and weather drivers for {site.name}</div>
      </div>

      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-icon" style={{background:'var(--green-light)',color:'var(--green)'}}><CheckCircle2 /></div>
          <div className="kpi-value" style={{color:'var(--green)'}}>{reliability.toFixed(1)}%</div>
          <div className="kpi-label">Forecast Reliability</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon" style={{background:'var(--accent-light)',color:'var(--accent)'}}><TrendingUp /></div>
          <div className="kpi-value">{accuracy?.overall?.MAE ?? 0} kW</div>
          <div className="kpi-label">Mean Abs. Error</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon" style={{background:'#f0f9ff',color:'#0284c7'}}><ScanSearch /></div>
          <div className="kpi-value">{accuracy?.overall?.R2 ?? 0}</div>
          <div className="kpi-label">R² Score</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon" style={{background:'var(--amber-light)',color:'var(--amber)'}}><ShieldAlert /></div>
          <div className="kpi-value" style={{color: model?.status === 'HEALTHY' ? 'var(--green)' : 'var(--amber)'}}>{model?.status ?? '—'}</div>
          <div className="kpi-label">Model Status</div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-title">Accuracy by Horizon</div>
          <div className="text-xs text-muted mb-3">MAE vs forecast horizon — expected error grows with lead time.</div>
          <div className="chart-bars" style={{display:'flex',flexDirection:'column',gap:12}}>
            {(accuracy?.horizons || []).map((h: any) => {
              const rel = Math.min(h['rel_%'] ?? 0, 100)
              return (
                <div key={h.horizon_hours}>
                  <div className="flex-between mb-1">
                    <span className="text-xs font-medium">{h.horizon_hours}h horizon</span>
                    <span className="text-xs text-muted">MAE {h.MAE} kW · {h['rel_%']}%</span>
                  </div>
                  <div className="px-track" style={{height:10,background:'var(--bg3)',borderRadius:5,overflow:'hidden'}}>
                    <div style={{width:`${rel}%`,height:'100%',background:'var(--accent)',borderRadius:5}} />
                  </div>
                </div>
              )
            })}
          </div>
          <div className="divider" />
          <div className="flex-between">
            <div className="text-xs text-muted">MAPE</div>
            <div className="text-xs font-medium">{accuracy?.overall?.['MAPE_%'] ?? 0}%</div>
          </div>
          <div className="flex-between mt-2">
            <div className="text-xs text-muted">RMSE</div>
            <div className="text-xs font-medium">{accuracy?.overall?.RMSE ?? 0} kW</div>
          </div>
          <div className="flex-between mt-2">
            <div className="text-xs text-muted">Model</div>
            <div className="text-xs font-medium">{model?.version ?? 'v2.4'} · {model?.algorithm ?? 'Ensemble'}</div>
          </div>
        </div>

        <div className="card">
          <div className="card-title">Alerts</div>
          <div className="text-xs text-muted mb-3">Actionable notifications from risk & weather intelligence.</div>
          {alerts.length === 0 && (
            <div className="empty-state" style={{padding:'40px 16px'}}>
              <div className="empty-icon" style={{width:48,height:48}}><CheckCircle2 /></div>
              <div className="empty-title" style={{fontSize:15}}>No active alerts</div>
            </div>
          )}
          {alerts.map((a: any) => {
            const s = severityStyle[a.severity] || severityStyle.info
            return (
              <div key={a.id} className="anomaly-row">
                <div style={{width:36,textAlign:'center',color:s.color}}><ShieldAlert size={20} /></div>
                <div style={{flex:1}}>
                  <div className="flex-center gap-2">
                    <span className="text-sm font-medium" style={{color:s.color}}>{a.title}</span>
                    <span className={`badge ${s.badge}`}>{a.severity}</span>
                  </div>
                  <div className="text-xs text-muted mt-2">{a.detail}</div>
                  {a.channels?.length > 0 && (
                    <div className="mt-2 flex gap-2">
                      {a.channels.map((c: string) => <span key={c} className="badge badge-default">{c}</span>)}
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-title">Weather Drivers</div>
          <div className="text-xs text-muted mb-3">Source: <span className="font-medium">{weather?.source === 'open-meteo' ? 'Open-Meteo live' : 'Physics baseline'}</span></div>
          <div className="flex flex-col gap-2">
            {(weather?.drivers || []).map((d: any) => (
              <div key={d.key} className="flex-between anomaly-row" style={{padding:'10px 14px'}}>
                <div>
                  <div className="text-sm font-medium">{d.label}</div>
                  <div className="text-xs text-muted">{d.value}</div>
                </div>
                <span className={`badge ${d.level === 'HIGH' ? 'badge-red' : d.level === 'MEDIUM' ? 'badge-amber' : 'badge-green'}`}>{d.level}</span>
              </div>
            ))}
          </div>
          <div className="divider" />
          <div className="flex-between">
            <div className="text-xs text-muted">Generation impact</div>
            <div className="text-xs font-medium" style={{color:'var(--amber)'}}>-{weather?.impact?.['generation_reduction_kw'] ?? 0} kW</div>
          </div>
        </div>

        <div className="card">
          <div className="card-title">Model Health</div>
          <div className="text-xs text-muted mb-3">MLOps status for the active forecasting model.</div>
          <div className="flex-center gap-4 mb-4">
            <div className="flex-center" style={{width:88,height:88,borderRadius:'50%',border:`6px solid ${model?.status === 'HEALTHY' ? 'var(--green)' : 'var(--amber)'}`,flexDirection:'column'}}>
              <div className="kpi-value">{model?.data_drift ?? '—'}</div>
              <div className="text-xs text-muted">Data Drift</div>
            </div>
            <div className="flex-1" style={{display:'flex',flexDirection:'column',gap:8}}>
              <div className="flex-between"><span className="text-xs text-muted">Version</span><span className="text-xs font-medium">{model?.version}</span></div>
              <div className="flex-between"><span className="text-xs text-muted">Model Drift</span><span className="text-xs font-medium">{model?.model_drift}</span></div>
              <div className="flex-between"><span className="text-xs text-muted">Last trained</span><span className="text-xs font-medium">{model && Number(model.hours_since_training) < 72 ? `${Math.round(model.hours_since_training)}h ago` : '> 3 days ago'}</span></div>
              <div className="flex-between"><span className="text-xs text-muted">Features</span><span className="text-xs font-medium">{model?.feature_version}</span></div>
            </div>
          </div>
          <div className="flex-between anomaly-row" style={{padding:'10px 14px'}}>
            <div>
              <div className="text-sm font-medium">Data Quality</div>
              <div className="text-xs text-muted">{weather?.data?.records ?? 0} records · {weather?.data?.high_severity_anomalies ?? 0} severe anomalies</div>
            </div>
            <span className={`badge ${(weather?.data?.['quality_%'] ?? 100) >= 90 ? 'badge-green' : 'badge-amber'}`}>{weather?.data?.['quality_%'] ?? 100}%</span>
          </div>
          {weather?.data?.stale && (
            <div className="badge badge-red mt-3">Data stale — last update {weather.data.last_updated_minutes_ago} min ago</div>
          )}
        </div>
      </div>
    </div>
  )
}

// ─── Settings Page ────────────────────────────────────────────
function SettingsPage({ onSiteCreated }: { onSiteCreated: () => void }) {
  const [showForm, setShowForm] = useState(false)
  const [sites, setSites] = useState<Site[]>([])
  const [form, setForm] = useState({ name: '', latitude: 28.6139, longitude: 77.2090, capacity_kw: 100, battery_capacity_kwh: 50, export_limit_kw: 80 })

  useEffect(() => {
    listSites().then(r => setSites(r.data)).catch(() => {})
  }, [])

  const handleCreate = async () => {
    try {
      await createSite(form)
      const r = await listSites()
      setSites(r.data)
      setShowForm(false)
      onSiteCreated()
    } catch (e: any) {
      const detail = e?.response?.data?.detail
      const msg = typeof detail === "string" ? detail : Array.isArray(detail) ? detail.map((d: any) => d.msg || String(d)).join(", ") : e.message || "Failed"
      alert(msg)
    }
  }

  return (
    <div className="animate-fadeIn">
      <div className="page-header">
        <div className="page-title">Settings</div>
        <div className="page-subtitle">Manage sites, data sources, and system configuration</div>
      </div>

      <div className="card">
        <div className="flex-between mb-4">
          <div className="card-title" style={{marginBottom:0}}>Registered Sites</div>
          <button className="btn btn-primary btn-sm" onClick={() => setShowForm(true)}><Plus size={14} /> New Site</button>
        </div>
        {sites.length === 0 ? (
          <div className="empty-state" style={{padding:40}}>
            <div className="empty-icon"><Factory /></div>
            <div className="empty-title">No sites registered</div>
            <div className="empty-desc mb-4">Add your first solar or wind installation to get started.</div>
            <button className="btn btn-primary" onClick={() => setShowForm(true)}><Plus size={14} /> Add Site</button>
          </div>
        ) : (
          sites.map(s => (
            <div key={s.id} className="anomaly-row">
              <div style={{width:40,height:40,borderRadius:10,background:'var(--accent-light)',color:'var(--accent)',display:'flex',alignItems:'center',justifyContent:'center',fontWeight:700,fontSize:16}}>
                {s.name[0]}
              </div>
              <div style={{flex:1}}>
                <div className="text-sm font-medium">{s.name}</div>
                <div className="text-xs text-muted">{s.capacity_kw} kW · {s.battery_capacity_kwh} kWh battery · Lat {s.latitude.toFixed(2)}</div>
              </div>
              <span className="badge badge-green">Active</span>
            </div>
          ))
        )}
      </div>

      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal animate-fadeIn" onClick={e => e.stopPropagation()}>
            <div className="flex-between mb-4">
              <div className="text-sm font-bold">Register New Site</div>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowForm(false)}><X size={14} /></button>
            </div>
            <div className="mb-3">
              <div className="text-xs text-muted mb-2">Site Name</div>
              <input className="input" value={form.name} onChange={e => setForm({...form, name: e.target.value})} placeholder="e.g. Rooftop Solar Plant" />
            </div>
            <div className="grid-2 mb-3">
              <div>
                <div className="text-xs text-muted mb-2">Latitude</div>
                <input className="input" type="number" step="0.0001" value={form.latitude} onChange={e => setForm({...form, latitude: Number(e.target.value)})} />
              </div>
              <div>
                <div className="text-xs text-muted mb-2">Longitude</div>
                <input className="input" type="number" step="0.0001" value={form.longitude} onChange={e => setForm({...form, longitude: Number(e.target.value)})} />
              </div>
            </div>
            <div className="grid-3 mb-4">
              <div>
                <div className="text-xs text-muted mb-2">Capacity (kW)</div>
                <input className="input" type="number" value={form.capacity_kw} onChange={e => setForm({...form, capacity_kw: Number(e.target.value)})} />
              </div>
              <div>
                <div className="text-xs text-muted mb-2">Battery (kWh)</div>
                <input className="input" type="number" value={form.battery_capacity_kwh} onChange={e => setForm({...form, battery_capacity_kwh: Number(e.target.value)})} />
              </div>
              <div>
                <div className="text-xs text-muted mb-2">Export Limit (kW)</div>
                <input className="input" type="number" value={form.export_limit_kw} onChange={e => setForm({...form, export_limit_kw: Number(e.target.value)})} />
              </div>
            </div>
            <div className="flex-center gap-3">
              <button className="btn btn-secondary" style={{flex:1}} onClick={() => setShowForm(false)}>Cancel</button>
              <button className="btn btn-primary" style={{flex:1}} onClick={handleCreate}>Create Site</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ─── Main App ─────────────────────────────────────────────────
export default function App() {
  const { user, doSignup, doLogin, doLogout } = useAuth()
  const [page, setPage] = useState<string>('gs_dashboard')
  const [siteVersion, setSiteVersion] = useState(0)
  const [activeSite, setActiveSite] = useState<Site | null>(null)
  const [gsAssetId, setGsAssetId] = useState<string | null>(null)

  useEffect(() => {
    const handler = () => setSiteVersion(v => v + 1)
    window.addEventListener('siteCreated', handler)
    window.addEventListener('siteChanged', handler)
    return () => {
      window.removeEventListener('siteCreated', handler)
      window.removeEventListener('siteChanged', handler)
    }
  }, [])

  // Listen for site changes from sidebar
  useEffect(() => {
    const handler = (e: any) => {
      const site = (window as any).__GRIDSHIELD_SITE__
      setActiveSite(site || null)
    }
    window.addEventListener('siteChanged', handler)
    window.addEventListener('siteCreated', handler)
    // Initial load
    const timer = setTimeout(() => {
      const site = (window as any).__GRIDSHIELD_SITE__
      setActiveSite(site || null)
    }, 500)
    return () => {
      window.removeEventListener('siteChanged', handler)
      window.removeEventListener('siteCreated', handler)
      clearTimeout(timer)
    }
  }, [])

  if (!user) return <LandingPage onLogin={doLogin} onSignup={doSignup} />

  const site = activeSite || (window as any).__GRIDSHIELD_SITE__
  const noSite = !site

  function goToGsAsset(id: string) { setGsAssetId(id); setPage('gs_asset') }
  function backFromGsAsset() { setGsAssetId(null); setPage('gs_dashboard') }

  const renderPage = () => {
    // GridShield pages — no site required
    switch (page) {
      case 'gs_dashboard':   return <GSCommandCenter onSelectAsset={goToGsAsset} />
      case 'gs_asset':       return gsAssetId
        ? <GSAssetIntelligence assetId={gsAssetId} onBack={backFromGsAsset} />
        : <GSCommandCenter onSelectAsset={goToGsAsset} />
      case 'gs_maintenance': return <GSMaintenance onSelectAsset={goToGsAsset} />
      case 'gs_crew':        return <GSCrewPlanner onSelectAsset={goToGsAsset} />
      case 'gs_scenarios':   return <GSScenarioSim onSelectAsset={goToGsAsset} />
      case 'gs_copilot':     return <div style={{height:'calc(100vh - 64px)',display:'flex',flexDirection:'column'}}><AIAssistantInterface /></div>
    }

    // Site-specific pages — require a site
    if (noSite && !['settings', 'data', 'anomalies'].includes(page)) {
      return (
        <div className="empty-state">
          <div className="empty-icon"><Factory /></div>
          <div className="empty-title">No Site Selected</div>
          <div className="empty-desc mb-4">Create a site in Settings, or select one from the sidebar dropdown.</div>
          <button className="btn btn-primary" onClick={() => setPage('settings')}>Go to Settings</button>
        </div>
      )
    }

    switch (page) {
      case 'dashboard': return <Dashboard site={site} />
      case 'forecast': return <ForecastPage site={site} />
      case 'risk': return <RiskPage site={site} />
      case 'optimize': return <OptimizePage site={site} />
      case 'insights': return <InsightsPage site={site} />
      case 'anomalies': return <AnomaliesPage />
      case 'data': return <DataPage site={site} />
      case 'settings': return <SettingsPage onSiteCreated={() => setSiteVersion(v => v + 1)} />
      default: return <Dashboard site={site} />
    }
  }

  return (
    <div style={{display:'flex',height:'100vh'}}>
      <Sidebar page={page} onNav={setPage} onLogout={doLogout} user={user} />
      <main className="main">
        <div className="main-content" key={siteVersion}>
          {renderPage()}
        </div>
      </main>
    </div>
  )
}