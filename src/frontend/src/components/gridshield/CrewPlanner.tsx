/**
 * GridShield — Crew Planner Page
 * Uses existing CSS design system.
 */
import React, { useState, useEffect } from 'react'
import { gsGetCrewPlan, gsGetCrews, type GSCrewAssignment, type GSCrew } from '../../api/gridshield'
import { riskBadgeClass, riskTextColor, assetTypeIcon, RED, AMBER, GREEN, ACCENT, MUTED } from './utils'

interface Props { onSelectAsset: (id: string) => void }

export default function CrewPlanner({ onSelectAsset }: Props) {
  const [assignments, setAssignments] = useState<GSCrewAssignment[]>([])
  const [standby, setStandby]         = useState<any[]>([])
  const [allCrews, setAllCrews]       = useState<GSCrew[]>([])
  const [loading, setLoading]         = useState(true)
  const [error, setError]             = useState<string | null>(null)
  const [tab, setTab]                 = useState<'assignments' | 'all'>('assignments')

  useEffect(() => {
    Promise.all([gsGetCrewPlan(), gsGetCrews()])
      .then(([plan, crews]) => {
        setAssignments(plan.data.assignments)
        setStandby(plan.data.standby)
        setAllCrews(crews.data.crews)
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="empty-state"><div className="empty-title">Loading crew plan…</div></div>
  if (error)   return <div className="card" style={{ borderLeft: `4px solid ${RED}` }}><p className="text-sm" style={{ color: RED }}>{error}</p></div>

  const dispatched    = assignments.filter(a => a.assignment === 'Dispatch').length
  const prepositioned = assignments.filter(a => a.assignment === 'Pre-position').length
  const onStandby     = standby.filter((s: any) => s.status === 'standby' || s.availability === 'available').length

  return (
    <div className="animate-fadeIn">
      <div className="page-header flex-between">
        <div>
          <div className="page-title">Crew Pre-Positioning Planner</div>
          <div className="page-subtitle">{assignments.length} crews deployed · {onStandby} on standby</div>
        </div>
      </div>

      {/* Summary */}
      <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(3,1fr)', marginBottom: 24 }}>
        <div className="kpi-card">
          <div className="kpi-icon" style={{ background: '#fce8e6', color: RED }}>🚒</div>
          <div className="kpi-value" style={{ color: RED }}>{dispatched}</div>
          <div className="kpi-label">Dispatched</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon" style={{ background: '#fef7e0', color: AMBER }}>📍</div>
          <div className="kpi-value" style={{ color: AMBER }}>{prepositioned}</div>
          <div className="kpi-label">Pre-Positioned</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon" style={{ background: '#e8f0fe', color: ACCENT }}>⏳</div>
          <div className="kpi-value" style={{ color: ACCENT }}>{onStandby}</div>
          <div className="kpi-label">On Standby</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs" style={{ marginBottom: 20 }}>
        <button className={`tab ${tab === 'assignments' ? 'active' : ''}`} onClick={() => setTab('assignments')}>
          Active Assignments ({assignments.length})
        </button>
        <button className={`tab ${tab === 'all' ? 'active' : ''}`} onClick={() => setTab('all')}>
          All Crews ({allCrews.length})
        </button>
      </div>

      {tab === 'assignments' && (
        <div>
          {assignments.length === 0 && (
            <div className="empty-state"><div className="empty-title">No active assignments</div></div>
          )}

          {assignments.map(a => (
            <div key={`${a.crew_id}-${a.asset_id}`} className="card" style={{
              borderLeft: `4px solid ${a.assignment === 'Dispatch' ? RED : a.assignment === 'Pre-position' ? AMBER : ACCENT}`
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', gap: 8, marginBottom: 10, flexWrap: 'wrap', alignItems: 'center' }}>
                    <span className={`badge ${a.assignment === 'Dispatch' ? 'badge-red' : a.assignment === 'Pre-position' ? 'badge-amber' : 'badge-default'}`}>
                      {a.assignment.toUpperCase()}
                    </span>
                    <span className={riskBadgeClass(a.risk_level)}>{a.risk_level.toUpperCase()}</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: 14, color: '#202124' }}>🚒 {a.crew_name || a.crew_id}</div>
                      <div style={{ fontSize: 12, color: MUTED }}>{a.crew_specialty} specialist · {a.region}</div>
                    </div>
                    <div style={{ color: MUTED, fontSize: 18 }}>→</div>
                    <div style={{ cursor: 'pointer' }} onClick={() => onSelectAsset(a.asset_id)}>
                      <div style={{ fontWeight: 600, fontSize: 14, color: ACCENT }}>{assetTypeIcon(a.asset_type)} {a.asset_name || a.asset_id}</div>
                      <div style={{ fontSize: 12, color: MUTED }}>{a.asset_id} · Risk {a.risk_score?.toFixed(0)}/100</div>
                    </div>
                  </div>
                  {a.reason && <p style={{ fontSize: 12, color: MUTED, marginTop: 8 }}>{a.reason}</p>}
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontWeight: 700, color: AMBER, fontSize: 15 }}>ETA {a.eta_hours}h</div>
                  <div style={{ fontSize: 12, color: MUTED }}>Priority #{a.priority}</div>
                </div>
              </div>
            </div>
          ))}

          {/* Standby */}
          {standby.length > 0 && (
            <div style={{ marginTop: 24 }}>
              <div className="page-subtitle" style={{ marginBottom: 12 }}>Standby / Unassigned</div>
              <div className="grid-3">
                {standby.map((s: any) => (
                  <div key={s.crew_id} className="source-card">
                    <div style={{ fontWeight: 600, fontSize: 13, color: '#202124' }}>{s.crew_name || s.crew_id}</div>
                    <div style={{ fontSize: 12, color: MUTED, marginTop: 2 }}>{s.specialty} · {s.region}</div>
                    <span className={`badge ${s.availability === 'available' ? 'badge-green' : s.availability === 'busy' ? 'badge-amber' : 'badge-default'}`} style={{ marginTop: 8, display: 'inline-block' }}>
                      {s.availability || s.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {tab === 'all' && (
        <div className="grid-2">
          {allCrews.map(c => {
            const assigned = assignments.find(a => a.crew_id === c.crew_id)
            return (
              <div key={c.crew_id} className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 14, color: '#202124' }}>🚒 {c.name}</div>
                    <div style={{ fontSize: 12, color: MUTED, marginTop: 2 }}>{c.crew_id} · {c.specialty} · {c.region}</div>
                  </div>
                  <span className={`badge ${c.availability === 'available' ? 'badge-green' : c.availability === 'busy' ? 'badge-amber' : 'badge-default'}`}>
                    {c.availability}
                  </span>
                </div>
                {assigned && (
                  <div style={{ marginTop: 10, background: '#e8f0fe', borderRadius: 8, padding: '8px 12px', fontSize: 13, color: ACCENT }}>
                    {assigned.assignment}: {assigned.asset_name || assigned.asset_id}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
