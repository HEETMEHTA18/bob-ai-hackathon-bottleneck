/**
 * GridShield — Command Center Dashboard
 * Uses the existing CSS design system: .card, .kpi-card, .badge, .btn, etc.
 */
import React, { useState, useEffect } from 'react'
import { gsGetKPIs, gsGetRiskRanking, gsGetAlerts, gsGetMLStatus, type GSKPIs, type GSRankingEntry, type GSAlert, type GSMLStatus } from '../../api/gridshield'
import { riskBadgeClass, riskTextColor, riskBarColor, riskAccentStyle, priorityBadgeClass, assetTypeIcon, assetTypeLabel, pct, statusColor, RED, AMBER, GREEN, ACCENT, MUTED } from './utils'
import { AlertTriangle, Activity, Users, Zap, Shield, TrendingUp } from 'lucide-react'

interface CommandCenterProps {
  onSelectAsset: (id: string) => void
}

export default function CommandCenter({ onSelectAsset }: CommandCenterProps) {
  const [kpis, setKpis]       = useState<GSKPIs | null>(null)
  const [ranking, setRanking] = useState<GSRankingEntry[]>([])
  const [alerts, setAlerts]   = useState<GSAlert[]>([])
  const [mlStatus, setMlStatus] = useState<GSMLStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState<string | null>(null)
  const [filter, setFilter]   = useState<string>('all')

  useEffect(() => {
    load()
    const id = setInterval(load, 60_000)
    return () => clearInterval(id)
  }, [])

  async function load() {
    try {
      setLoading(true)
      const [k, r, a, ml] = await Promise.all([gsGetKPIs(), gsGetRiskRanking(), gsGetAlerts(), gsGetMLStatus()])
      setKpis(k.data); setRanking(r.data.ranking); setAlerts(a.data.alerts); setMlStatus(ml.data)
    } catch (e: any) { setError(e.message) }
    finally { setLoading(false) }
  }

  const filtered = filter === 'all' ? ranking : ranking.filter(r => r.risk_level === filter)

  if (loading) return (
    <div className="empty-state">
      <div className="empty-icon"><Activity size={28} /></div>
      <div className="empty-title">Loading grid status…</div>
      <div className="empty-desc">Fetching asset telemetry and risk data</div>
    </div>
  )
  if (error) return (
    <div className="card" style={{ borderLeft: `4px solid ${RED}` }}>
      <div className="card-title" style={{ color: RED }}>Failed to load GridShield data</div>
      <p className="text-sm text-muted">{error}</p>
      <button className="btn btn-primary btn-sm" style={{ marginTop: 12 }} onClick={load}>Retry</button>
    </div>
  )

  return (
    <div className="animate-fadeIn">
      {/* Header */}
      <div className="page-header flex-between">
        <div>
          <div className="page-title">GridShield Command Center</div>
          <div className="page-subtitle">
            Power Outage Prediction &amp; Grid Equipment Failure Advisor
            {kpis && <span style={{ marginLeft: 12, fontSize: 13, color: MUTED }}>
              Last updated {new Date(kpis.timestamp).toLocaleTimeString()}
            </span>}
          </div>
        </div>
        <div className="flex gap-2 items-center">
          {mlStatus && (
            <span className="badge" style={{
              background: mlStatus.mode === 'real_ml' ? '#dcfce7' : '#fef3c7',
              color: mlStatus.mode === 'real_ml' ? '#166534' : '#92400e',
              fontSize: 11,
              padding: '4px 8px',
            }}>
              {mlStatus.mode === 'real_ml' ? 'ML: XGBoost' : 'ML: Mock'}
              {mlStatus.model_version && <span style={{ marginLeft: 4, opacity: 0.7 }}>({mlStatus.model_version})</span>}
            </span>
          )}
          <span className="badge badge-green"><span className="status-dot" />LIVE</span>
        </div>
      </div>

      {/* KPI Cards */}
      {kpis && (
        <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(5,1fr)' }}>
          <KpiCard icon={<Shield size={20} />} value={kpis.critical_assets} label="Critical Assets" color={RED} bg="#fce8e6" />
          <KpiCard icon={<AlertTriangle size={20} />} value={kpis.high_risk_assets} label="High Risk Assets" color={AMBER} bg="#fef7e0" />
          <KpiCard icon={<Users size={20} />} value={kpis.customers_at_risk.toLocaleString()} label="Customers at Risk" color={ACCENT} bg="#e8f0fe" />
          <KpiCard icon={<Zap size={20} />} value={kpis.critical_facilities_at_risk} label="Critical Facilities" color="#7c3aed" bg="#ede9fe" />
          <KpiCard icon={<TrendingUp size={20} />} value={kpis.crews_pre_positioned} label="Crews Positioned" color={GREEN} bg="#e6f4ea" />
        </div>
      )}

      {/* Alerts */}
      {alerts.length > 0 && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="card-title"><AlertTriangle size={16} style={{ marginRight: 8, color: RED }} />Active Alerts</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 160, overflowY: 'auto' }}>
            {alerts.slice(0, 6).map(a => (
              <div
                key={a.alert_id}
                onClick={() => onSelectAsset(a.asset_id)}
                className="anomaly-row"
                style={{ cursor: 'pointer', ...riskAccentStyle(a.severity), paddingLeft: 14 }}
              >
                <div style={{ flex: 1, minWidth: 0 }}>
                  <p className="text-sm font-bold" style={{ color: riskTextColor(a.severity) }}>{a.message}</p>
                  <p className="text-xs text-muted" style={{ marginTop: 2 }}>{new Date(a.timestamp).toLocaleTimeString()}</p>
                </div>
                <span className={riskBadgeClass(a.severity)}>{a.severity.toUpperCase()}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Risk Ranking */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {/* Table header row */}
        <div style={{ padding: '18px 24px 14px', borderBottom: '1px solid #e0e0e0', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
          <div className="card-title" style={{ margin: 0 }}>
            Risk Ranking — {filtered.length} assets
          </div>
          <div className="tabs">
            {['all', 'critical', 'high', 'medium', 'low'].map(f => (
              <button key={f} className={`tab ${filter === f ? 'active' : ''}`} onClick={() => setFilter(f)}>
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ background: '#f8f9fa', borderBottom: '1.5px solid #e0e0e0' }}>
                {['#', 'Asset', 'Type', 'Risk Score', '24h Prob', 'Customers', 'Action', 'Crew'].map(h => (
                  <th key={h} style={{ padding: '10px 16px', textAlign: 'left', fontWeight: 600, color: MUTED, fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.06em', whiteSpace: 'nowrap' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((e, i) => (
                <tr
                  key={e.asset_id}
                  onClick={() => onSelectAsset(e.asset_id)}
                  style={{ borderBottom: '1px solid #f1f3f4', cursor: 'pointer', transition: 'background 0.12s' }}
                  onMouseEnter={ev => (ev.currentTarget.style.background = '#f8f9fa')}
                  onMouseLeave={ev => (ev.currentTarget.style.background = '')}
                >
                  <td style={{ padding: '12px 16px', color: MUTED, fontWeight: 500, fontFamily: 'monospace' }}>{e.rank}</td>
                  <td style={{ padding: '12px 16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ width: 8, height: 8, borderRadius: '50%', background: statusColor(e.status), flexShrink: 0, display: 'inline-block' }} />
                      <div>
                        <div style={{ fontWeight: 600, color: '#202124', fontSize: 13 }}>{e.asset_name}</div>
                        <div style={{ color: MUTED, fontSize: 12 }}>{e.asset_id} · {e.region}</div>
                      </div>
                    </div>
                  </td>
                  <td style={{ padding: '12px 16px', color: MUTED }}>{assetTypeIcon(e.asset_type)} {assetTypeLabel(e.asset_type)}</td>
                  <td style={{ padding: '12px 16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div style={{ width: 60, background: '#e8eaed', borderRadius: 5, height: 7, overflow: 'hidden' }}>
                        <div style={{ width: `${Math.min(100, e.risk_score)}%`, background: riskBarColor(e.risk_score), height: '100%', borderRadius: 5 }} />
                      </div>
                      <span style={{ fontWeight: 700, color: riskTextColor(e.risk_level), fontSize: 13, minWidth: 26 }}>{e.risk_score.toFixed(0)}</span>
                      <span className={riskBadgeClass(e.risk_level)} style={{ fontSize: 11 }}>{e.risk_level.toUpperCase()}</span>
                    </div>
                  </td>
                  <td style={{ padding: '12px 16px', fontWeight: 700, color: e.failure_probability_24h >= 0.7 ? RED : e.failure_probability_24h >= 0.4 ? AMBER : '#202124' }}>
                    {pct(e.failure_probability_24h)}
                  </td>
                  <td style={{ padding: '12px 16px', color: '#202124' }}>{e.customers_at_risk.toLocaleString()}</td>
                  <td style={{ padding: '12px 16px' }}>
                    <span className={priorityBadgeClass(e.priority_level)} style={{ fontSize: 11 }}>{e.priority_level.toUpperCase()}</span>
                  </td>
                  <td style={{ padding: '12px 16px', color: MUTED, fontSize: 12 }}>{e.assigned_crew || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

function KpiCard({ icon, value, label, color, bg }: { icon: React.ReactNode; value: string | number; label: string; color: string; bg: string }) {
  return (
    <div className="kpi-card">
      <div className="kpi-icon" style={{ background: bg, color }}>{icon}</div>
      <div className="kpi-value" style={{ color }}>{value}</div>
      <div className="kpi-label">{label}</div>
    </div>
  )
}
