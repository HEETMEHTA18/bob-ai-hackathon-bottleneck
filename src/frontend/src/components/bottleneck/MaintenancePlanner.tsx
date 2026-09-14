/**
 * Bottleneck — Maintenance Planner Page
 * Uses existing CSS design system (.card, .badge, .btn, .select)
 */
import React, { useState, useEffect } from 'react'
import { gsGetMaintenancePriorities } from '../../api/bottleneck'
import { riskBadgeClass, riskTextColor, riskBarColor, priorityBadgeClass, assetTypeIcon, assetTypeLabel, pct, RED, AMBER, GREEN, ACCENT, MUTED } from './utils'

interface Props { onSelectAsset: (id: string) => void }

export default function MaintenancePlanner({ onSelectAsset }: Props) {
  const [priorities, setPriorities] = useState<any[]>([])
  const [loading, setLoading]       = useState(true)
  const [error, setError]           = useState<string | null>(null)
  const [filterLevel, setFilterLevel]   = useState('')
  const [filterType, setFilterType]     = useState('')
  const [filterRegion, setFilterRegion] = useState('')

  useEffect(() => { load() }, [filterLevel, filterType, filterRegion])

  async function load() {
    setLoading(true)
    try {
      const r = await gsGetMaintenancePriorities({
        priority_level: filterLevel || undefined,
        asset_type: filterType || undefined,
        region: filterRegion || undefined,
      })
      setPriorities(r.data.priorities)
    } catch (e: any) { setError(e.message) }
    finally { setLoading(false) }
  }

  return (
    <div className="animate-fadeIn">
      <div className="page-header flex-between">
        <div>
          <div className="page-title">Maintenance Planner</div>
          <div className="page-subtitle">Impact-aware prioritisation — ranked by operational consequence</div>
        </div>
        <span className="badge badge-default">{priorities.length} assets</span>
      </div>

      {/* Filters */}
      <div className="card" style={{ marginBottom: 20, padding: '16px 24px' }}>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
          <select className="select" style={{ width: 160 }} value={filterLevel} onChange={e => setFilterLevel(e.target.value)}>
            <option value="">All Priorities</option>
            <option value="immediate">Immediate</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="monitor">Monitor</option>
          </select>
          <select className="select" style={{ width: 160 }} value={filterType} onChange={e => setFilterType(e.target.value)}>
            <option value="">All Types</option>
            <option value="transformer">Transformer</option>
            <option value="breaker">Breaker</option>
            <option value="feeder">Feeder</option>
            <option value="recloser">Recloser</option>
            <option value="switch">Switch</option>
            <option value="capacitor_bank">Capacitor Bank</option>
          </select>
          <select className="select" style={{ width: 140 }} value={filterRegion} onChange={e => setFilterRegion(e.target.value)}>
            <option value="">All Regions</option>
            {['North', 'South', 'East', 'West', 'Central'].map(r => <option key={r}>{r}</option>)}
          </select>
          {(filterLevel || filterType || filterRegion) && (
            <button className="btn btn-ghost btn-sm" onClick={() => { setFilterLevel(''); setFilterType(''); setFilterRegion('') }}>
              Clear filters ×
            </button>
          )}
        </div>
      </div>

      {loading && (
        <div className="empty-state" style={{ padding: 40 }}>
          <div className="empty-title">Loading priorities…</div>
        </div>
      )}
      {error && (
        <div className="card" style={{ borderLeft: `4px solid ${RED}` }}>
          <p className="text-sm" style={{ color: RED }}>{error}</p>
        </div>
      )}

      {!loading && !error && priorities.length === 0 && (
        <div className="empty-state">
          <div className="empty-title">No results</div>
          <div className="empty-desc">No maintenance priorities match the current filters.</div>
        </div>
      )}

      {!loading && !error && priorities.map((p: any) => (
        <div
          key={p.asset_id}
          className="card"
          style={{ cursor: 'pointer', borderLeft: `4px solid ${p.priority_level === 'immediate' ? RED : p.priority_level === 'high' ? AMBER : p.priority_level === 'medium' ? '#f59e0b' : '#dadce0'}`, transition: 'box-shadow 0.15s' }}
          onClick={() => onSelectAsset(p.asset_id)}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 8, alignItems: 'center' }}>
                <span className={priorityBadgeClass(p.priority_level)}>#{p.priority} {p.priority_level.toUpperCase()}</span>
                <span className={riskBadgeClass(p.risk_level)}>{p.risk_level.toUpperCase()}</span>
                <span className="badge badge-default">{assetTypeIcon(p.asset_type)} {assetTypeLabel(p.asset_type)}</span>
                <span className="text-xs text-muted">{p.region}</span>
              </div>
              <div style={{ fontWeight: 700, fontSize: 15, color: '#202124', marginBottom: 4 }}>
                {p.asset_name} <span style={{ fontWeight: 400, color: MUTED, fontSize: 13 }}>({p.asset_id})</span>
              </div>
              <p style={{ fontSize: 13, color: '#202124', marginBottom: 4 }}>{p.recommended_action}</p>
              <p style={{ fontSize: 12, color: MUTED }}>{p.reason}</p>
            </div>
            <div style={{ textAlign: 'right', flexShrink: 0 }}>
              <div style={{ fontSize: 28, fontWeight: 800, color: riskTextColor(p.risk_level), lineHeight: 1 }}>
                {p.risk_score.toFixed(0)}<span style={{ fontSize: 13, color: MUTED }}>/100</span>
              </div>
              <div style={{ fontSize: 13, color: MUTED, marginTop: 4 }}>Risk Score</div>
              <div style={{ fontSize: 15, fontWeight: 700, marginTop: 4, color: p.failure_probability_24h >= 0.7 ? RED : p.failure_probability_24h >= 0.4 ? AMBER : '#202124' }}>
                {pct(p.failure_probability_24h)} 24h
              </div>
            </div>
          </div>

          <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid #f1f3f4', display: 'flex', gap: 16, flexWrap: 'wrap', fontSize: 12, color: MUTED }}>
            <span>⏱ {p.recommended_window}</span>
            <span>⏳ ~{p.estimated_duration_hours}h</span>
            <span>👥 {p.customers_at_risk.toLocaleString()} customers</span>
            {p.critical_facilities_at_risk > 0 && <span>🏥 {p.critical_facilities_at_risk} facilities</span>}
            {p.assigned_crew_id
              ? <span style={{ color: ACCENT, fontWeight: 600 }}>🚒 {p.assigned_crew_id}</span>
              : <span>No crew assigned</span>}
          </div>
        </div>
      ))}
    </div>
  )
}
