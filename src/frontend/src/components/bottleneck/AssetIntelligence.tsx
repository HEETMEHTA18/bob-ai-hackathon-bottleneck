/**
 * Bottleneck — Asset Intelligence Page
 * Full detail for one asset. Uses existing CSS design system.
 */
import React, { useState, useEffect } from 'react'
import { gsGetAssetIntelligence, type GSIntelligence } from '../../api/bottleneck'
import { riskBadgeClass, riskTextColor, riskBarColor, riskAccentStyle, priorityBadgeClass, assetTypeIcon, assetTypeLabel, pct, statusColor, RED, AMBER, GREEN, ACCENT, MUTED, MiniBar } from './utils'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { ArrowLeft } from 'lucide-react'

interface Props { assetId: string; onBack: () => void }

export default function AssetIntelligence({ assetId, onBack }: Props) {
  const [data, setData]       = useState<GSIntelligence | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState<string | null>(null)

  useEffect(() => {
    setLoading(true); setError(null)
    gsGetAssetIntelligence(assetId)
      .then(r => setData(r.data))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [assetId])

  if (loading) return (
    <div className="empty-state">
      <div className="empty-icon"><span style={{ fontSize: 28 }}>{assetTypeIcon('transformer')}</span></div>
      <div className="empty-title">Loading {assetId}…</div>
    </div>
  )
  if (error || !data) return (
    <div>
      <button className="btn btn-secondary btn-sm" style={{ marginBottom: 16 }} onClick={onBack}>
        <ArrowLeft size={14} /> Back
      </button>
      <div className="card" style={{ borderLeft: `4px solid ${RED}` }}>
        <div className="card-title" style={{ color: RED }}>Error loading {assetId}</div>
        <p className="text-sm text-muted">{error}</p>
      </div>
    </div>
  )

  const { asset, risk, prediction, grid_impact, weather, maintenance_recommendation: maint, telemetry_24h, incidents, maintenance_history } = data

  const chartData = telemetry_24h.slice(-24).map(t => ({
    time: new Date(t.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    'Oil Temp (°C)': t.oil_temperature,
    'Load %': t.load_percentage,
    'Vibration': +(t.vibration * 10).toFixed(1),
  }))

  return (
    <div className="animate-fadeIn">
      {/* Back + header */}
      <div style={{ marginBottom: 20 }}>
        <button className="btn btn-secondary btn-sm" style={{ marginBottom: 14 }} onClick={onBack}>
          <ArrowLeft size={14} /> Back to Command Center
        </button>
        <div className="page-header flex-between" style={{ marginBottom: 0 }}>
          <div>
            <div className="page-title">
              {assetTypeIcon(asset.asset_type)} {asset.name}
            </div>
            <div className="page-subtitle">
              {asset.id} · {assetTypeLabel(asset.asset_type)} · {asset.region} Region · {asset.age_years} yrs old
              <span style={{ marginLeft: 10 }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: statusColor(asset.status), display: 'inline-block', marginRight: 5, verticalAlign: 'middle' }} />
                {asset.status}
              </span>
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: 36, fontWeight: 800, color: riskTextColor(risk.risk_level), lineHeight: 1 }}>
              {risk.risk_score.toFixed(0)}<span style={{ fontSize: 16, color: MUTED }}>/100</span>
            </div>
            <span className={riskBadgeClass(risk.risk_level)} style={{ marginTop: 6, display: 'inline-block' }}>
              {risk.risk_level.toUpperCase()} RISK
            </span>
          </div>
        </div>
      </div>

      {/* 4 headline metrics */}
      <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(4,1fr)', marginBottom: 24 }}>
        <MetricCard label="24h Failure Prob" value={pct(risk.failure_probability_24h)} color={risk.failure_probability_24h >= 0.7 ? RED : risk.failure_probability_24h >= 0.4 ? AMBER : GREEN} />
        <MetricCard label="72h Failure Prob" value={pct(risk.failure_probability_72h)} color={risk.failure_probability_72h >= 0.8 ? RED : risk.failure_probability_72h >= 0.5 ? AMBER : GREEN} />
        <MetricCard label="Health Score" value={`${risk.health_score.toFixed(0)}/100`} color={risk.health_score <= 50 ? RED : risk.health_score <= 70 ? AMBER : GREEN} />
        <MetricCard label="Anomaly Score" value={risk.anomaly_score.toFixed(2)} color={risk.anomaly_score >= 0.7 ? RED : risk.anomaly_score >= 0.4 ? AMBER : GREEN} />
      </div>

      <div className="grid-2" style={{ gridTemplateColumns: '1fr 2fr', alignItems: 'start' }}>
        {/* Left column */}
        <div>
          {/* Risk breakdown */}
          <div className="card">
            <div className="card-title">Risk Breakdown</div>
            {[
              { label: 'Failure Probability', v: risk.failure_probability_24h },
              { label: 'Grid Impact', v: risk.grid_impact_score },
              { label: 'Weather Exposure', v: risk.weather_exposure_score },
              { label: 'Criticality', v: risk.criticality_score },
              { label: 'Lack of Redundancy', v: 1 - risk.redundancy_score },
            ].map(({ label, v }) => (
              <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                <span style={{ width: 130, fontSize: 13, color: MUTED, flexShrink: 0 }}>{label}</span>
                <MiniBar value={v} />
                <span style={{ fontSize: 13, fontWeight: 600, color: '#202124', width: 34, textAlign: 'right' }}>{(v * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>

          {/* Why risky */}
          <div className="card">
            <div className="card-title">Why Risky</div>
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {risk.top_factors.map((f, i) => (
                <li key={i} style={{ display: 'flex', gap: 8, marginBottom: 8, fontSize: 13 }}>
                  <span style={{ color: RED, flexShrink: 0, marginTop: 2 }}>▸</span>
                  <span style={{ color: '#202124' }}>{f}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Recommended action */}
          <div className="card" style={riskAccentStyle(risk.risk_level)}>
            <div className="card-title">Recommended Action</div>
            <span className={priorityBadgeClass(maint.priority_level)} style={{ marginBottom: 10, display: 'inline-block' }}>
              {maint.priority_level.toUpperCase()} — Priority #{maint.priority}
            </span>
            <p style={{ fontWeight: 600, color: '#202124', marginBottom: 6, fontSize: 14 }}>{maint.recommended_action}</p>
            <p className="text-xs text-muted" style={{ marginBottom: 4 }}>Window: {maint.recommended_window}</p>
            <p className="text-xs text-muted" style={{ marginBottom: 4 }}>Duration: ~{maint.estimated_duration_hours}h</p>
            <p className="text-xs text-muted" style={{ marginBottom: maint.assigned_crew_id ? 8 : 0 }}>Reason: {maint.reason}</p>
            {maint.assigned_crew_id && (
              <div style={{ background: '#e8f0fe', borderRadius: 8, padding: '8px 12px', fontSize: 13, color: ACCENT, fontWeight: 600 }}>
                🚒 Assigned: {maint.assigned_crew_id}
              </div>
            )}
          </div>
        </div>

        {/* Right column */}
        <div>
          {/* Telemetry chart */}
          <div className="card">
            <div className="card-title">Telemetry — Last 24 Hours</div>
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={chartData} margin={{ top: 4, right: 10, left: -10, bottom: 4 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f3f4" />
                  <XAxis dataKey="time" tick={{ fontSize: 11, fill: MUTED }} interval="preserveStartEnd" />
                  <YAxis tick={{ fontSize: 11, fill: MUTED }} />
                  <Tooltip contentStyle={{ border: '1px solid #e0e0e0', borderRadius: 8, fontSize: 12 }} />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Line type="monotone" dataKey="Oil Temp (°C)" stroke={RED} dot={false} strokeWidth={2} />
                  <Line type="monotone" dataKey="Load %" stroke={AMBER} dot={false} strokeWidth={2} />
                  <Line type="monotone" dataKey="Vibration" stroke="#7c3aed" dot={false} strokeWidth={1.5} />
                </LineChart>
              </ResponsiveContainer>
            ) : <p className="text-sm text-muted">No telemetry data</p>}
          </div>

          {/* Grid Impact + Weather */}
          <div className="grid-2">
            <div className="card">
              <div className="card-title">Grid Impact</div>
              {[
                { label: 'Customers at Risk', value: grid_impact.customers_at_risk.toLocaleString() },
                { label: 'Critical Facilities', value: grid_impact.critical_facilities_at_risk },
                { label: 'Downstream Assets', value: grid_impact.downstream_assets },
                { label: 'Capacity', value: `${grid_impact.capacity_mva} MVA` },
              ].map(({ label, value }) => (
                <div key={label} className="flex-between" style={{ marginBottom: 8, fontSize: 13 }}>
                  <span className="text-muted">{label}</span>
                  <span style={{ fontWeight: 700, color: '#202124' }}>{value}</span>
                </div>
              ))}
              <div style={{ marginTop: 8 }}>
                <div style={{ fontSize: 12, color: MUTED, marginBottom: 4 }}>Impact Score</div>
                <MiniBar value={grid_impact.grid_impact_score} />
              </div>
            </div>

            <div className="card">
              <div className="card-title">Weather Exposure</div>
              {[
                { label: 'Temperature', value: `${weather.temperature}°C`, hi: weather.temperature >= 42 },
                { label: 'Wind Speed', value: `${weather.wind_speed} m/s`, hi: false },
                { label: 'Storm Severity', value: pct(weather.storm_severity), hi: weather.storm_severity >= 0.6 },
              ].map(({ label, value, hi }) => (
                <div key={label} className="flex-between" style={{ marginBottom: 8, fontSize: 13 }}>
                  <span className="text-muted">{label}</span>
                  <span style={{ fontWeight: 700, color: hi ? RED : '#202124' }}>{value}</span>
                </div>
              ))}
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', margin: '8px 0' }}>
                {weather.heatwave_indicator && <span className="badge badge-amber">🔥 Heatwave</span>}
                {weather.severe_weather_indicator && <span className="badge badge-red">⛈ Severe</span>}
              </div>
              <div style={{ fontSize: 12, color: MUTED, marginBottom: 4 }}>Exposure Score</div>
              <MiniBar value={weather.weather_exposure_score} />
            </div>
          </div>

          {/* Incidents */}
          {incidents.length > 0 && (
            <div className="card">
              <div className="card-title">Recent Incidents ({incidents.length})</div>
              <div style={{ maxHeight: 160, overflowY: 'auto' }}>
                {incidents.map(inc => (
                  <div key={inc.incident_id} className="anomaly-row" style={{ ...riskAccentStyle(inc.severity), paddingLeft: 12, marginBottom: 6 }}>
                    <div style={{ flex: 1 }}>
                      <p style={{ fontSize: 13, color: '#202124' }}>{inc.description}</p>
                      <p style={{ fontSize: 12, color: MUTED, marginTop: 2 }}>{new Date(inc.timestamp).toLocaleDateString()} — {inc.severity}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Maintenance history */}
          {maintenance_history.length > 0 && (
            <div className="card">
              <div className="card-title">Maintenance History</div>
              {maintenance_history.map(m => (
                <div key={m.record_id} className="anomaly-row" style={{ borderLeft: `4px solid ${ACCENT}`, paddingLeft: 12, marginBottom: 6 }}>
                  <div style={{ flex: 1 }}>
                    <p style={{ fontSize: 13, color: '#202124' }}>{m.work_done}</p>
                    <p style={{ fontSize: 12, color: MUTED, marginTop: 2 }}>{new Date(m.date).toLocaleDateString()} — {m.technician}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function MetricCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="kpi-card" style={{ textAlign: 'center' }}>
      <div className="kpi-value" style={{ color, fontSize: 24 }}>{value}</div>
      <div className="kpi-label" style={{ marginTop: 8 }}>{label}</div>
    </div>
  )
}
