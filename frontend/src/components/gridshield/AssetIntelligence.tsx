/**
 * GridShield — Asset Intelligence Page
 * A SINGLE map UI: full-page interactive map of the selected asset (risk zone,
 * nearest crew depots, dispatch lines) with an overlay intelligence panel
 * floating over the map. No dashboard — everything lives inside the map view.
 */
import React, { useState, useEffect } from 'react'
import { ArrowLeft, Loader2, MapPin, PanelRightClose, PanelRightOpen, Truck, Clock, ShieldAlert, AlertTriangle } from 'lucide-react'
import {
  gsGetAssetIntelligence, gsGetRiskRanking, gsGetNearbyCrews, gsAssignCrew,
  type GSIntelligence, type GSRankingEntry, type GSNearbyCrew, type GSCrewAssignResult,
} from '../../api/gridshield'
import {
  riskBadgeClass, riskTextColor, priorityBadgeClass, assetTypeIcon, assetTypeLabel,
  MiniBar, pct, statusColor, RED, AMBER, GREEN, ACCENT, MUTED,
} from './utils'
import { GridMapEmbedded } from './GridMap'

interface Props { assetId: string; onBack: () => void }

const riskLevelColors: Record<string, string> = {
  critical: '#c5221f',
  high: '#e8710a',
  medium: '#eab308',
  low: '#0d904f',
}

export default function AssetIntelligence({ assetId, onBack }: Props) {
  const [entry, setEntry] = useState<GSRankingEntry | null>(null)
  const [data, setData] = useState<GSIntelligence | null>(null)
  const [nearby, setNearby] = useState<GSNearbyCrew[]>([])
  const [assigned, setAssigned] = useState<GSCrewAssignResult | null>(null)
  const [assigning, setAssigning] = useState<string | null>(null)
  const [panelOpen, setPanelOpen] = useState(true)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = async () => {
    setLoading(true); setError(null)
    try {
      const [intelRes, rankRes, crewRes] = await Promise.all([
        gsGetAssetIntelligence(assetId),
        gsGetRiskRanking(),
        gsGetNearbyCrews(assetId, 5),
      ])
      const found = rankRes.data.ranking.find(e => e.asset_id === assetId)
      if (!found) setError(`${assetId} not found in grid ranking`)
      else setEntry(found)
      setData(intelRes.data)
      setNearby(crewRes.data.nearby)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [assetId])

  const handleAssign = async (crewId: string) => {
    setAssigning(crewId)
    try {
      const res = await gsAssignCrew(assetId, crewId)
      setAssigned(res.data)
      setEntry(prev => prev ? { ...prev, assigned_crew: res.data.crew.crew_id } : prev)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setAssigning(null)
    }
  }

  const assignedCrewId = assigned?.crew.crew_id ?? entry?.assigned_crew ?? null

  return (
    <div className="animate-fadeIn" style={{ position: 'relative', height: 'calc(100vh - 16px)', width: '100%', overflow: 'hidden' }}>
      {/* Map fills the whole page */}
      {loading ? (
        <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f8f9fa' }}>
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            <span className="text-sm text-zinc-500">Loading {assetId}…</span>
          </div>
        </div>
      ) : error && !entry ? (
        <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f8f9fa' }}>
          <div className="card" style={{ borderLeft: `4px solid ${RED}`, maxWidth: 380 }}>
            <div className="card-title" style={{ color: RED }}>Map unavailable</div>
            <p className="text-sm text-muted">{error}</p>
            <button className="btn btn-secondary btn-sm" onClick={onBack}><ArrowLeft size={14} /> Back</button>
          </div>
        </div>
      ) : entry && (
        <GridMapEmbedded
          riskEntry={entry}
          nearby={nearby}
          assignedCrewId={assignedCrewId}
          onAssign={handleAssign}
          onRefresh={load}
        />
      )}

      {/* Floating top bar — back + identity + risk */}
      {entry && (
        <div style={{ position: 'absolute', top: 14, left: 14, zIndex: 1000, display: 'flex', alignItems: 'center', gap: 12, padding: '8px 14px', background: 'rgba(255,255,255,0.95)', borderRadius: 10, border: '1px solid #e0e0e0', boxShadow: '0 1px 4px rgba(0,0,0,0.08)', maxWidth: 'calc(100% - 420px)' }}>
          <button className="btn btn-secondary btn-sm" onClick={onBack}>
            <ArrowLeft size={14} /> Back
          </button>
          <div style={{ width: 12, height: 12, borderRadius: '50%', background: riskLevelColors[entry.risk_level], border: '2px solid #fff', boxShadow: '0 1px 2px rgba(0,0,0,0.25)', flexShrink: 0 }} />
          <div style={{ fontWeight: 700, fontSize: 14, color: '#202124', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{entry.asset_name}</div>
          <div style={{ fontSize: 12, color: MUTED, whiteSpace: 'nowrap' }}>{entry.asset_id} · {entry.region}</div>
          <span className={riskBadgeClass(entry.risk_level)} style={{ fontSize: 10 }}>{entry.risk_level.toUpperCase()}</span>
          <span style={{ fontSize: 13, fontWeight: 700, color: riskLevelColors[entry.risk_level] }}>{entry.risk_score.toFixed(0)}/100</span>
          <span style={{ fontSize: 11, color: MUTED, whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', gap: 4 }}>
            <MapPin className="h-3 w-3" /> {entry.asset_lat.toFixed(4)}, {entry.asset_lon.toFixed(4)}
          </span>
        </div>
      )}

      {/* Intelligence overlay panel — map stays the only screen */}
      {entry && data && panelOpen && (
        <div className="card" style={{
          position: 'absolute', top: 14, right: 14, bottom: 14, zIndex: 1000, width: 400, maxWidth: '92vw',
          display: 'flex', flexDirection: 'column', padding: 0, boxShadow: '0 4px 16px rgba(0,0,0,0.12)',
        }}>
          {/* Panel header */}
          <div style={{ padding: '14px 16px', borderBottom: '1px solid #e0e0e0', display: 'flex', alignItems: 'center', gap: 10 }}>
            <div>
              <div style={{ fontWeight: 800, fontSize: 16, color: '#202124', display: 'flex', alignItems: 'center', gap: 8 }}>
                {assetTypeIcon(data.asset.asset_type)} {assetTypeLabel(data.asset.asset_type)} Intelligence
              </div>
              <div style={{ fontSize: 12, color: MUTED, marginTop: 2 }}>
                {data.asset.name} <span style={{ display: 'inline-block', width: 6, height: 6, borderRadius: '50%', background: statusColor(data.asset.status), margin: '0 4px 1px', verticalAlign: 'middle' }} /> {data.asset.status}
              </div>
            </div>
            <button onClick={() => setPanelOpen(false)} className="btn btn-ghost btn-sm" title="Collapse panel" style={{ marginLeft: 'auto', flexShrink: 0 }}>
              <PanelRightClose className="h-4 w-4" />
            </button>
          </div>

          {/* Scrollable content */}
          <div style={{ flex: 1, minHeight: 0, overflowY: 'auto', padding: 16 }}>
            {/* Top risk strip */}
            <div style={{ display: 'flex', gap: 12, alignItems: 'stretch', marginBottom: 16 }}>
              <div style={{ flex: 1, background: riskTextColor(entry.risk_level) + '14', borderRadius: 10, padding: 12, textAlign: 'center', border: `1px solid ${riskTextColor(entry.risk_level)}33` }}>
                <div style={{ fontSize: 26, fontWeight: 800, color: riskTextColor(entry.risk_level), lineHeight: 1 }}>{entry.risk_score.toFixed(0)}</div>
                <div style={{ fontSize: 10, color: MUTED, marginTop: 2 }}>RISK SCORE</div>
                <span className={riskBadgeClass(entry.risk_level)} style={{ fontSize: 9, marginTop: 4 }}>{entry.risk_level.toUpperCase()}</span>
              </div>
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8, justifyContent: 'center' }}>
                <div style={{ fontSize: 12, display: 'flex', justifyContent: 'space-between' }}>
                  <span className="text-muted">24h failure prob</span>
                  <span style={{ fontWeight: 700, color: entry.failure_probability_24h >= 0.7 ? RED : entry.failure_probability_24h >= 0.4 ? AMBER : GREEN }}>{pct(entry.failure_probability_24h)}</span>
                </div>
                <div style={{ fontSize: 12, display: 'flex', justifyContent: 'space-between' }}>
                  <span className="text-muted">Health score</span>
                  <span style={{ fontWeight: 700, color: entry.health_score <= 50 ? RED : entry.health_score <= 70 ? AMBER : GREEN }}>{entry.health_score.toFixed(0)}/100</span>
                </div>
                <div style={{ fontSize: 12, display: 'flex', justifyContent: 'space-between' }}>
                  <span className="text-muted">Customers at risk</span>
                  <span style={{ fontWeight: 700, color: '#202124' }}>{entry.customers_at_risk.toLocaleString()}</span>
                </div>
                <div style={{ fontSize: 12, display: 'flex', justifyContent: 'space-between' }}>
                  <span className="text-muted">Critical facilities</span>
                  <span style={{ fontWeight: 700, color: '#202124' }}>{entry.critical_facilities_at_risk}</span>
                </div>
              </div>
            </div>

            {/* Recommended action */}
            <div style={{ background: riskTextColor(entry.risk_level) + '10', border: `1px solid ${riskTextColor(entry.risk_level)}30`, borderRadius: 10, padding: 10, marginBottom: 14 }}>
              <span className={priorityBadgeClass(entry.priority_level)} style={{ marginBottom: 6, display: 'inline-block' }}>{entry.priority_level.toUpperCase()} · Priority #{entry.priority_level === 'immediate' ? 1 : entry.priority_level === 'high' ? 2 : entry.priority_level === 'medium' ? 3 : 4}</span>
              <div style={{ fontWeight: 600, fontSize: 13, color: '#202124' }}>{entry.recommended_action}</div>
              {assignedCrewId && (
                <div style={{ marginTop: 6, fontSize: 12, color: ACCENT, fontWeight: 600 }}>
                  <Truck className="h-3 w-3 inline-block align-middle mr-1" /> Crew {assignedCrewId} on the way
                </div>
              )}
            </div>

            {/* Risk breakdown */}
            <SectionTitle>Risk Breakdown</SectionTitle>
            {[
              { label: 'Failure Probability', v: data.risk.failure_probability_24h },
              { label: 'Grid Impact', v: data.risk.grid_impact_score },
              { label: 'Weather Exposure', v: data.risk.weather_exposure_score },
              { label: 'Criticality', v: data.risk.criticality_score },
              { label: 'Lack of Redundancy', v: 1 - data.risk.redundancy_score },
            ].map(({ label, v }) => (
              <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                <span style={{ width: 118, fontSize: 12, color: MUTED, flexShrink: 0 }}>{label}</span>
                <MiniBar value={v} />
                <span style={{ fontSize: 12, fontWeight: 600, color: '#202124', width: 32, textAlign: 'right' }}>{(v * 100).toFixed(0)}%</span>
              </div>
            ))}

            {/* Why risky */}
            <SectionTitle>Why Risky</SectionTitle>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
              {data.risk.top_factors.slice(0, 5).map((f, i) => (
                <li key={i} style={{ display: 'flex', gap: 8, marginBottom: 6, fontSize: 12.5 }}>
                  <span style={{ color: RED, flexShrink: 0 }}>▸</span>
                  <span style={{ color: '#202124' }}>{f}</span>
                </li>
              ))}
            </ul>

            {/* Crew dispatch */}
            <SectionTitle><Truck className="h-3.5 w-3.5 inline-block align-middle mr-1" /> Crew Dispatch — Nearest First</SectionTitle>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {nearby.length === 0 && <p className="text-sm text-muted">No available crew nearby right now.</p>}
              {nearby.map((n, i) => {
                const isAssigned = assignedCrewId === n.crew.crew_id
                return (
                  <div key={n.crew.crew_id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: 10, border: isAssigned ? `2px solid ${GREEN}` : '1px solid #e0e0e0', borderRadius: 8, background: isAssigned ? '#f0fbf3' : '#fff' }}>
                    <div style={{ width: 30, height: 30, borderRadius: '50%', background: isAssigned ? GREEN : i === 0 ? '#0d904f' : '#e8f0fe', color: isAssigned || i === 0 ? '#fff' : ACCENT, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      <Truck className="h-4 w-4" />
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontWeight: 700, fontSize: 12.5, color: '#202124', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {n.crew.name}
                        {n.specialty_match && <span className="badge badge-green" style={{ marginLeft: 6, fontSize: 9 }}>MATCH</span>}
                      </div>
                      <div style={{ fontSize: 11, color: MUTED, marginTop: 2, display: 'flex', alignItems: 'center', gap: 10 }}>
                        <span><MapPin className="h-3 w-3 inline-block align-middle mr-1" />{n.distance_km} km</span>
                        <span><Clock className="h-3 w-3 inline-block align-middle mr-1" />ETA {n.eta_hours}h</span>
                        <span>{n.crew.region}</span>
                      </div>
                    </div>
                    {isAssigned ? (
                      <span className="badge badge-green" style={{ fontSize: 10 }}>ASSIGNED</span>
                    ) : (
                      <button
                        className="btn btn-primary btn-sm"
                        disabled={assigning === n.crew.crew_id || n.crew.availability !== 'available'}
                        onClick={() => handleAssign(n.crew.crew_id)}
                        style={{ flexShrink: 0 }}
                      >
                        {assigning === n.crew.crew_id ? '…' : 'Assign'}
                      </button>
                    )}
                  </div>
                )
              })}
            </div>

            {assigned && (
              <div style={{ background: '#e6f4ea', border: '1px solid #ceead6', borderRadius: 8, padding: '10px 12px', marginTop: 10 }}>
                <div style={{ fontSize: 12, color: '#0d904f', fontWeight: 700 }}><Truck className="h-3.5 w-3.5 inline-block align-middle mr-1" />{assigned.assignment} · {assigned.crew.name} ({assigned.reason.slice(0, 60)}…)</div>
              </div>
            )}

            {/* Grid impact + weather */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginTop: 4 }}>
              <div>
                <SectionTitle>Grid Impact</SectionTitle>
                {[
                  { label: 'Customers', value: data.grid_impact.customers_at_risk.toLocaleString() },
                  { label: 'Critical', value: data.grid_impact.critical_facilities_at_risk },
                  { label: 'Downstream', value: data.grid_impact.downstream_assets },
                  { label: 'Capacity', value: `${data.grid_impact.capacity_mva} MVA` },
                ].map(({ label, value }) => (
                  <div key={label} className="flex-between" style={{ marginBottom: 5, fontSize: 12 }}>
                    <span className="text-muted">{label}</span>
                    <span style={{ fontWeight: 700, color: '#202124' }}>{value}</span>
                  </div>
                ))}
              </div>
              <div>
                <SectionTitle>Weather</SectionTitle>
                {[
                  { label: 'Temp', value: `${data.weather.temperature}°C` },
                  { label: 'Wind', value: `${data.weather.wind_speed} m/s` },
                  { label: 'Storm', value: pct(data.weather.storm_severity) },
                ].map(({ label, value }) => (
                  <div key={label} className="flex-between" style={{ marginBottom: 5, fontSize: 12 }}>
                    <span className="text-muted">{label}</span>
                    <span style={{ fontWeight: 700, color: '#202124' }}>{value}</span>
                  </div>
                ))}
                <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginTop: 4 }}>
                  {data.weather.heatwave_indicator && <span className="badge badge-amber" style={{ fontSize: 9 }}>Heatwave</span>}
                  {data.weather.severe_weather_indicator && <span className="badge badge-red" style={{ fontSize: 9 }}>Severe</span>}
                </div>
              </div>
            </div>

            {/* Incidents + maintenance */}
            {data.incidents.length > 0 && (
              <>
                <SectionTitle><AlertTriangle className="h-3.5 w-3.5 inline-block align-middle mr-1" /> Recent Incidents ({data.incidents.length})</SectionTitle>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {data.incidents.slice(0, 3).map(inc => (
                    <div key={inc.incident_id} style={{ borderLeft: `3px solid ${RED}`, padding: '6px 10px', background: '#fdf2f2', borderRadius: 6 }}>
                      <p style={{ fontSize: 12, color: '#202124', margin: 0 }}>{inc.description}</p>
                      <p style={{ fontSize: 11, color: MUTED, margin: '2px 0 0' }}>{new Date(inc.timestamp).toLocaleDateString()} — {inc.severity}</p>
                    </div>
                  ))}
                </div>
              </>
            )}
            {data.maintenance_history.length > 0 && (
              <>
                <SectionTitle><ShieldAlert className="h-3.5 w-3.5 inline-block align-middle mr-1" /> Maintenance History</SectionTitle>
                {data.maintenance_history.slice(0, 3).map(m => (
                  <div key={m.record_id} style={{ borderLeft: `3px solid ${ACCENT}`, padding: '6px 10px', background: '#f5f7ff', borderRadius: 6, marginBottom: 6 }}>
                    <p style={{ fontSize: 12, color: '#202124', margin: 0 }}>{m.work_done}</p>
                    <p style={{ fontSize: 11, color: MUTED, margin: '2px 0 0' }}>{new Date(m.date).toLocaleDateString()} — {m.technician}</p>
                  </div>
                ))}
              </>
            )}
          </div>
        </div>
      )}

      {/* Collapsed → reopen button */}
      {entry && !panelOpen && (
        <button
          onClick={() => setPanelOpen(true)}
          className="btn btn-secondary"
          style={{ position: 'absolute', top: 14, right: 14, zIndex: 1000, padding: '8px 10px' }}
          title="Open Asset Intelligence panel"
        >
          <PanelRightOpen className="h-4 w-4" />
        </button>
      )}
    </div>
  )
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: 0.4, textTransform: 'uppercase', color: MUTED, margin: '14px 0 8px', display: 'flex', alignItems: 'center' }}>{children}</p>
}