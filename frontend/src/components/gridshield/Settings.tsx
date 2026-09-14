/**
 * Bottleneck — Settings & Configuration
 * Tabs: Asset Fleet · Crew Roster · ML & System · Hardware Integration · Environment
 */
import React, { useState, useEffect } from 'react'
import {
  gsGetAssets, gsGetCrews, gsGetMLStatus, gsGetAllHardwareConfigs,
  gsTestHardwareConnection, gsSyncHardwareData,
  type GSAsset, type GSCrew, type GSMLStatus, type GSHardwareConfig,
} from '../../api/gridshield'
import {
  Activity, AlertTriangle, Bot, CheckCircle2, ChevronDown, ChevronRight,
  Cpu, Database, FlaskConical, HardHat, Info, Layers, Loader2,
  MapPin, RefreshCw, Server, Settings as SettingsIcon, Shield,
  Users, Wifi, WifiOff, XCircle, Zap, Radio, Globe,
} from 'lucide-react'

// ─── helpers ─────────────────────────────────────────────────────────────────

const MUTED = '#5f6368'
const RED   = '#c5221f'

function statusColor(s: string) {
  if (s === 'healthy')     return { bg: '#e6f4ea', color: '#0d904f' }
  if (s === 'degraded')    return { bg: '#fef7e0', color: '#e8710a' }
  if (s === 'critical')    return { bg: '#fce8e6', color: '#c5221f' }
  if (s === 'offline')     return { bg: '#f1f3f4', color: '#5f6368' }
  if (s === 'maintenance') return { bg: '#e8f0fe', color: '#1a73e8' }
  return { bg: '#f1f3f4', color: '#5f6368' }
}

function availColor(s: string) {
  if (s === 'available') return { bg: '#e6f4ea', color: '#0d904f' }
  if (s === 'busy')      return { bg: '#fef7e0', color: '#e8710a' }
  return { bg: '#f1f3f4', color: '#5f6368' }
}

function Badge({ label, bg, color }: { label: string; bg: string; color: string }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center',
      padding: '2px 8px', borderRadius: 999,
      fontSize: 11, fontWeight: 600,
      background: bg, color,
      letterSpacing: '0.02em', whiteSpace: 'nowrap',
    }}>{label}</span>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 24 }}>
      <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.09em', color: MUTED, marginBottom: 10 }}>
        {title}
      </div>
      {children}
    </div>
  )
}

function KPIRow({ items }: { items: { label: string; value: string | number; color?: string }[] }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: `repeat(${items.length}, 1fr)`, gap: 12, marginBottom: 20 }}>
      {items.map(it => (
        <div key={it.label} className="kpi-card" style={{ padding: '16px 18px' }}>
          <div className="kpi-value" style={{ fontSize: 26, color: it.color ?? '#202124' }}>{it.value}</div>
          <div className="kpi-label">{it.label}</div>
        </div>
      ))}
    </div>
  )
}

// ─── ASSET FLEET TAB ─────────────────────────────────────────────────────────

const ASSET_TYPE_ICONS: Record<string, React.ReactNode> = {
  transformer:   <Zap      size={13} color="#2563eb" />,
  feeder:        <Activity size={13} color="#16a34a" />,
  breaker:       <Shield   size={13} color="#7c3aed" />,
  recloser:      <RefreshCw size={13} color="#ea580c" />,
  switch:        <Layers   size={13} color="#0891b2" />,
  capacitor_bank:<FlaskConical size={13} color="#db2777" />,
}

function AssetFleetTab() {
  const [assets, setAssets]   = useState<GSAsset[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState<string | null>(null)
  const [filter, setFilter]   = useState<'all' | 'critical' | 'degraded' | 'healthy'>('all')
  const [regionFilter, setRegionFilter] = useState<string>('all')

  useEffect(() => {
    gsGetAssets().then(r => setAssets(r.data.assets)).catch(e => setError(e.message)).finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingSpinner />
  if (error)   return <ErrorBox msg={error} />

  const regions = Array.from(new Set(assets.map(a => a.region))).sort()
  const filtered = assets.filter(a => {
    if (filter !== 'all' && a.status !== filter) return false
    if (regionFilter !== 'all' && a.region !== regionFilter) return false
    return true
  })

  const byType = assets.reduce((acc, a) => { acc[a.asset_type] = (acc[a.asset_type] || 0) + 1; return acc }, {} as Record<string, number>)

  return (
    <div>
      <KPIRow items={[
        { label: 'Total Assets',   value: assets.length },
        { label: 'Critical',       value: assets.filter(a => a.status === 'critical').length,  color: RED },
        { label: 'Degraded',       value: assets.filter(a => a.status === 'degraded').length,  color: '#e8710a' },
        { label: 'Healthy',        value: assets.filter(a => a.status === 'healthy').length,   color: '#0d904f' },
        { label: 'Substations',    value: new Set(assets.map(a => a.substation_id)).size },
        { label: 'Regions',        value: regions.length },
      ]} />

      {/* Asset type breakdown */}
      <Section title="Asset Type Breakdown">
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
          {Object.entries(byType).map(([type, count]) => (
            <div key={type} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '6px 12px', borderRadius: 8, background: '#f8f9fa', border: '1px solid #e0e0e0', fontSize: 12 }}>
              {ASSET_TYPE_ICONS[type] ?? <Cpu size={13} />}
              <span style={{ fontWeight: 600, color: '#202124', textTransform: 'capitalize' }}>{type.replace('_', ' ')}</span>
              <span style={{ background: '#e8eaed', color: '#3c4043', borderRadius: 99, padding: '0 6px', fontWeight: 700 }}>{count}</span>
            </div>
          ))}
        </div>
      </Section>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 14, flexWrap: 'wrap' }}>
        {(['all','critical','degraded','healthy'] as const).map(f => (
          <button key={f} onClick={() => setFilter(f)} style={{
            padding: '5px 14px', borderRadius: 7, fontSize: 12, fontWeight: 600, cursor: 'pointer',
            border: filter === f ? '1.5px solid #2563eb' : '1.5px solid #dadce0',
            background: filter === f ? '#e8f0fe' : '#fff', color: filter === f ? '#2563eb' : '#3c4043',
          }}>{f.charAt(0).toUpperCase() + f.slice(1)}</button>
        ))}
        <select value={regionFilter} onChange={e => setRegionFilter(e.target.value)} style={{
          padding: '5px 12px', borderRadius: 7, fontSize: 12, fontWeight: 600, cursor: 'pointer',
          border: '1.5px solid #dadce0', background: '#fff', color: '#3c4043',
        }}>
          <option value="all">All Regions</option>
          {regions.map(r => <option key={r} value={r}>{r}</option>)}
        </select>
        <span style={{ fontSize: 12, color: MUTED, alignSelf: 'center' }}>{filtered.length} asset{filtered.length !== 1 ? 's' : ''}</span>
      </div>

      {/* Table */}
      <div style={{ overflowX: 'auto', border: '1px solid #e0e0e0', borderRadius: 12 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12.5 }}>
          <thead>
            <tr style={{ background: '#f8f9fa', borderBottom: '2px solid #e0e0e0' }}>
              {['Asset ID', 'Name', 'Type', 'Substation', 'Region', 'Status', 'Criticality', 'Capacity (MVA)', 'Age (yr)', 'Redundancy', 'Latitude', 'Longitude'].map(h => (
                <th key={h} style={{ padding: '9px 12px', textAlign: 'left', fontWeight: 700, color: '#3c4043', whiteSpace: 'nowrap', fontSize: 11 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((a, i) => {
              const sc = statusColor(a.status)
              return (
                <tr key={a.id} style={{ borderBottom: '1px solid #f0f0f0', background: i % 2 === 0 ? '#fff' : '#fafafa' }}>
                  <td style={{ padding: '8px 12px', fontFamily: 'monospace', fontWeight: 700, color: '#202124', whiteSpace: 'nowrap' }}>{a.id}</td>
                  <td style={{ padding: '8px 12px', color: '#202124', maxWidth: 200 }}>{a.name}</td>
                  <td style={{ padding: '8px 12px' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 5, whiteSpace: 'nowrap' }}>
                      {ASSET_TYPE_ICONS[a.asset_type] ?? <Cpu size={13} />}
                      <span style={{ textTransform: 'capitalize', color: '#3c4043' }}>{a.asset_type.replace('_', ' ')}</span>
                    </span>
                  </td>
                  <td style={{ padding: '8px 12px', fontFamily: 'monospace', fontSize: 11, color: MUTED, whiteSpace: 'nowrap' }}>{a.substation_id}</td>
                  <td style={{ padding: '8px 12px', color: '#3c4043', whiteSpace: 'nowrap' }}>{a.region}</td>
                  <td style={{ padding: '8px 12px' }}><Badge label={a.status} bg={sc.bg} color={sc.color} /></td>
                  <td style={{ padding: '8px 12px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <div style={{ width: 48, height: 5, borderRadius: 3, background: '#e0e0e0', overflow: 'hidden' }}>
                        <div style={{ width: `${a.criticality * 100}%`, height: '100%', background: a.criticality > 0.8 ? '#c5221f' : a.criticality > 0.6 ? '#e8710a' : '#0d904f', borderRadius: 3 }} />
                      </div>
                      <span style={{ fontFamily: 'monospace', color: '#202124' }}>{(a.criticality * 100).toFixed(0)}%</span>
                    </div>
                  </td>
                  <td style={{ padding: '8px 12px', fontFamily: 'monospace', color: '#202124', textAlign: 'right' }}>{a.capacity_mva}</td>
                  <td style={{ padding: '8px 12px', fontFamily: 'monospace', color: '#202124', textAlign: 'right' }}>{a.age_years}</td>
                  <td style={{ padding: '8px 12px', fontFamily: 'monospace', color: '#202124', textAlign: 'right' }}>{(a.redundancy_level * 100).toFixed(0)}%</td>
                  <td style={{ padding: '8px 12px', fontFamily: 'monospace', color: '#2563eb', whiteSpace: 'nowrap' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                      <MapPin size={11} color="#2563eb" />{a.location.lat.toFixed(4)}
                    </span>
                  </td>
                  <td style={{ padding: '8px 12px', fontFamily: 'monospace', color: '#2563eb', whiteSpace: 'nowrap' }}>{a.location.lon.toFixed(4)}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ─── CREW ROSTER TAB ─────────────────────────────────────────────────────────

function CrewRosterTab() {
  const [crews, setCrews]     = useState<GSCrew[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState<string | null>(null)

  useEffect(() => {
    gsGetCrews().then(r => setCrews(r.data.crews)).catch(e => setError(e.message)).finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingSpinner />
  if (error)   return <ErrorBox msg={error} />

  return (
    <div>
      <KPIRow items={[
        { label: 'Total Crews',  value: crews.length },
        { label: 'Available',    value: crews.filter(c => c.availability === 'available').length, color: '#0d904f' },
        { label: 'Busy',         value: crews.filter(c => c.availability === 'busy').length,      color: '#e8710a' },
        { label: 'Offline',      value: crews.filter(c => c.availability === 'offline').length,   color: MUTED },
      ]} />

      <div style={{ overflowX: 'auto', border: '1px solid #e0e0e0', borderRadius: 12 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12.5 }}>
          <thead>
            <tr style={{ background: '#f8f9fa', borderBottom: '2px solid #e0e0e0' }}>
              {['Crew ID', 'Name', 'Specialty', 'Region', 'Availability', 'Capacity', 'Base Latitude', 'Base Longitude'].map(h => (
                <th key={h} style={{ padding: '9px 12px', textAlign: 'left', fontWeight: 700, color: '#3c4043', whiteSpace: 'nowrap', fontSize: 11 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {crews.map((c, i) => {
              const ac = availColor(c.availability)
              return (
                <tr key={c.crew_id} style={{ borderBottom: '1px solid #f0f0f0', background: i % 2 === 0 ? '#fff' : '#fafafa' }}>
                  <td style={{ padding: '8px 12px', fontFamily: 'monospace', fontWeight: 700, color: '#202124' }}>{c.crew_id}</td>
                  <td style={{ padding: '8px 12px', color: '#202124' }}>{c.name}</td>
                  <td style={{ padding: '8px 12px' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 5, whiteSpace: 'nowrap' }}>
                      {ASSET_TYPE_ICONS[c.specialty] ?? <HardHat size={13} />}
                      <span style={{ textTransform: 'capitalize', color: '#3c4043' }}>{c.specialty}</span>
                    </span>
                  </td>
                  <td style={{ padding: '8px 12px', color: '#3c4043' }}>{c.region}</td>
                  <td style={{ padding: '8px 12px' }}><Badge label={c.availability} bg={ac.bg} color={ac.color} /></td>
                  <td style={{ padding: '8px 12px', fontFamily: 'monospace', color: '#202124', textAlign: 'center' }}>{c.capacity}</td>
                  <td style={{ padding: '8px 12px', fontFamily: 'monospace', color: '#2563eb', whiteSpace: 'nowrap' }}>
                    {c.lat != null
                      ? <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><MapPin size={11} color="#2563eb" />{c.lat.toFixed(4)}</span>
                      : <span style={{ color: MUTED }}>—</span>}
                  </td>
                  <td style={{ padding: '8px 12px', fontFamily: 'monospace', color: '#2563eb', whiteSpace: 'nowrap' }}>
                    {c.lon != null ? c.lon.toFixed(4) : <span style={{ color: MUTED }}>—</span>}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ─── ML & SYSTEM STATUS TAB ──────────────────────────────────────────────────

function MLSystemTab() {
  const [ml, setML]           = useState<GSMLStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState<string | null>(null)

  useEffect(() => {
    gsGetMLStatus().then(r => setML(r.data)).catch(e => setError(e.message)).finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingSpinner />
  if (error)   return <ErrorBox msg={error} />
  if (!ml)     return null

  const modelFiles = Object.entries(ml.model_files || {})

  return (
    <div>
      {/* Pipeline mode banner */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 12, padding: '14px 18px', borderRadius: 12,
        background: ml.mode === 'real_ml' ? '#e6f4ea' : '#fef7e0',
        border: `1.5px solid ${ml.mode === 'real_ml' ? '#0d904f' : '#e8710a'}`,
        marginBottom: 20,
      }}>
        {ml.mode === 'real_ml'
          ? <CheckCircle2 size={20} color="#0d904f" />
          : <AlertTriangle size={20} color="#e8710a" />}
        <div>
          <div style={{ fontWeight: 700, color: '#202124', fontSize: 14 }}>
            {ml.mode === 'real_ml' ? 'Real XGBoost Pipeline Active' : 'Deterministic Mock Predictor Active'}
          </div>
          <div style={{ fontSize: 12, color: MUTED, marginTop: 2 }}>
            {ml.mode === 'real_ml'
              ? 'XGBoost failure probability and anomaly models loaded from models/bottleneck/'
              : 'Set GRIDSHIELD_USE_REAL_ML=1 and retrain to activate the XGBoost pipeline'}
          </div>
        </div>
        <Badge
          label={ml.mode === 'real_ml' ? 'Real ML' : 'Mock'}
          bg={ml.mode === 'real_ml' ? '#e6f4ea' : '#fef7e0'}
          color={ml.mode === 'real_ml' ? '#0d904f' : '#e8710a'}
        />
      </div>

      {/* Status grid */}
      <Section title="Pipeline Configuration">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
          {[
            { label: 'Mode',           value: ml.mode },
            { label: 'Use Real ML',    value: ml.use_real_ml ? 'Yes' : 'No' },
            { label: 'Models Available', value: ml.models_available ? 'Yes' : 'No' },
            { label: 'Model Version',  value: ml.model_version ?? '—' },
            { label: 'Trained At',     value: ml.trained_at ? new Date(ml.trained_at).toLocaleString() : '—' },
            { label: 'Models Dir',     value: ml.models_directory },
          ].map(row => (
            <div key={row.label} style={{ padding: '10px 14px', background: '#f8f9fa', borderRadius: 8, border: '1px solid #e0e0e0' }}>
              <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', color: MUTED, letterSpacing: '0.07em', marginBottom: 3 }}>{row.label}</div>
              <div style={{ fontSize: 13, fontFamily: 'monospace', color: '#202124', wordBreak: 'break-all' }}>{row.value}</div>
            </div>
          ))}
        </div>
      </Section>

      {/* Model files */}
      {modelFiles.length > 0 && (
        <Section title="Model Files">
          <div style={{ overflowX: 'auto', border: '1px solid #e0e0e0', borderRadius: 10 }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
              <thead>
                <tr style={{ background: '#f8f9fa', borderBottom: '2px solid #e0e0e0' }}>
                  {['File', 'Size', 'Last Modified'].map(h => (
                    <th key={h} style={{ padding: '8px 12px', textAlign: 'left', fontWeight: 700, color: '#3c4043', fontSize: 11 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {modelFiles.map(([name, info]) => (
                  <tr key={name} style={{ borderBottom: '1px solid #f0f0f0' }}>
                    <td style={{ padding: '7px 12px', fontFamily: 'monospace', color: '#202124' }}>{name}</td>
                    <td style={{ padding: '7px 12px', fontFamily: 'monospace', color: MUTED }}>{(info.size_bytes / 1024).toFixed(1)} KB</td>
                    <td style={{ padding: '7px 12px', color: MUTED }}>{new Date(info.modified).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>
      )}

      {/* Metrics */}
      {ml.metrics && Object.keys(ml.metrics).length > 0 && (
        <Section title="Model Metrics">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
            {Object.entries(ml.metrics).map(([k, v]) => (
              <div key={k} style={{ padding: '10px 14px', background: '#f8f9fa', borderRadius: 8, border: '1px solid #e0e0e0' }}>
                <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', color: MUTED, letterSpacing: '0.07em', marginBottom: 3 }}>{k.replace(/_/g, ' ')}</div>
                <div style={{ fontSize: 15, fontFamily: 'monospace', fontWeight: 700, color: '#202124' }}>
                  {typeof v === 'number' ? v.toFixed(4) : String(v)}
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Retrain guide */}
      <Section title="Retrain Pipeline">
        <div style={{ padding: 14, background: '#f8f9fa', borderRadius: 10, border: '1px solid #e0e0e0' }}>
          <div style={{ fontSize: 12, color: '#3c4043', lineHeight: 1.8 }}>
            <div style={{ fontWeight: 700, color: '#202124', marginBottom: 6 }}>Retrain from scratch:</div>
            {[
              'python -m backend.gridshield.ml.generate_training_data',
              'python -m backend.gridshield.ml.train_models',
              'python -m backend.gridshield.ml.evaluate',
            ].map((cmd, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
                <span style={{ fontFamily: 'monospace', fontSize: 11, background: '#e8eaed', padding: '3px 8px', borderRadius: 5, color: '#202124', flex: 1 }}>{cmd}</span>
              </div>
            ))}
          </div>
        </div>
      </Section>

      {/* Risk formula */}
      <Section title="Composite Risk Formula">
        <div style={{ padding: 14, background: '#e8f0fe', borderRadius: 10, border: '1px solid #c6dafc' }}>
          <div style={{ fontFamily: 'monospace', fontSize: 13, color: '#1a56db', lineHeight: 2 }}>
            risk_score = (<br />
            &nbsp;&nbsp;failure_prob_24h × 0.35 +<br />
            &nbsp;&nbsp;grid_impact_score × 0.30 +<br />
            &nbsp;&nbsp;weather_exposure × 0.15 +<br />
            &nbsp;&nbsp;criticality × 0.12 +<br />
            &nbsp;&nbsp;(1 − redundancy) × 0.08<br />
            ) × 100
          </div>
        </div>
      </Section>
    </div>
  )
}

// ─── HARDWARE INTEGRATION TAB ─────────────────────────────────────────────────

const PROTOCOL_DOCS: Record<string, { label: string; port: string; description: string; wiring: string }> = {
  modbus_tcp: { label: 'Modbus TCP/IP',    port: '502',       description: 'Ethernet-based industrial protocol. Each asset gets its own IP address on the SCADA LAN.', wiring: 'RJ45 to asset switch. Set IP via front panel.' },
  modbus:     { label: 'Modbus RTU',       port: 'COM/USB',   description: 'Serial RS-485 bus. Multiple assets share bus with unique slave IDs.', wiring: 'RS-485 A/B wires to terminal block. Set unit_id 1–247.' },
  dnp3:       { label: 'DNP3',             port: '20000',     description: 'SCADA protocol with unsolicited responses. Used by utilities.', wiring: 'RS-232/485 or TCP. Configure DNP3 address per asset.' },
  iec61850:   { label: 'IEC 61850 (MMS)',  port: '102',       description: 'Substation standard. GOOSE for fast peer-to-peer, MMS for monitoring.', wiring: 'Ethernet LAN. Configure IED IP and GOOSE VLAN tags.' },
  mqtt:       { label: 'MQTT',             port: '1883/8883', description: 'Lightweight pub/sub. Ideal for low-bandwidth IoT sensors.', wiring: 'Wi-Fi or cellular. Set broker IP, topic, QoS. TLS on 8883.' },
  opcua:      { label: 'OPC UA',           port: '4840',      description: 'Secure industrial data exchange standard.', wiring: 'Ethernet. Set server URL and node IDs per register.' },
  http:       { label: 'HTTP/REST',        port: '80/443',    description: 'RESTful JSON API. Common for smart sensors and IoT gateways.', wiring: 'Wi-Fi or Ethernet. Set endpoint URL and poll interval.' },
}

const REGISTER_MAP = [
  { addr: '100–101', field: 'oil_temperature',   unit: '°C',   desc: 'Top-oil temperature (float32, scale ×0.1)' },
  { addr: '102–103', field: 'load_percentage',   unit: '%',    desc: 'Load as % of rated MVA (float32, scale ×0.1)' },
  { addr: '104–105', field: 'vibration',          unit: 'mm/s', desc: 'Peak vibration on core/tank (float32, scale ×0.01)' },
  { addr: '106–107', field: 'partial_discharge',  unit: 'pC',   desc: 'Partial discharge magnitude (float32, scale ×0.001)' },
  { addr: '108–109', field: 'current_unbalance',  unit: '%',    desc: 'Phase current unbalance (float32)' },
  { addr: '110–111', field: 'voltage_deviation',  unit: '%',    desc: 'Voltage deviation from nominal (float32)' },
  { addr: '112–113', field: 'ambient_temperature',unit: '°C',   desc: 'Ambient temperature at sensor location (float32)' },
]

function HardwareCard({
  config, onTest, onSync,
  testResults, syncResults,
}: {
  config: GSHardwareConfig
  onTest: (id: string) => void
  onSync: (id: string) => void
  testResults: Record<string, { success: boolean; message: string } | null>
  syncResults: Record<string, { synced: number } | null>
}) {
  const [open, setOpen] = useState(false)
  const tr = testResults[config.asset_id]
  const sr = syncResults[config.asset_id]
  const connected = config.status === 'connected'

  return (
    <div className="card" style={{ marginBottom: 10, padding: 0, borderLeft: `4px solid ${connected ? '#0d904f' : '#e8710a'}`, overflow: 'hidden' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '12px 16px', cursor: 'pointer' }} onClick={() => setOpen(o => !o)}>
        {connected ? <Wifi size={15} color="#0d904f" /> : <WifiOff size={15} color="#e8710a" />}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 700, fontSize: 13.5, color: '#202124' }}>{config.asset_id}</div>
          <div style={{ fontSize: 11, color: MUTED, display: 'flex', gap: 8, marginTop: 2, flexWrap: 'wrap' }}>
            <span>{config.device_type.replace('_', ' ').toUpperCase()}</span>
            <span>·</span><span>{config.protocol.toUpperCase()}</span>
            <span>·</span><Badge label={config.status} bg={connected ? '#e6f4ea' : '#fef7e0'} color={connected ? '#0d904f' : '#e8710a'} />
          </div>
        </div>
        {tr && (tr.success ? <CheckCircle2 size={14} color="#0d904f" /> : <XCircle size={14} color={RED} />)}
        {open ? <ChevronDown size={15} color="#9aa0a6" /> : <ChevronRight size={15} color="#9aa0a6" />}
      </div>

      {open && (
        <div style={{ borderTop: '1px solid #e0e0e0', padding: '14px 16px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
            <div>
              <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', color: MUTED, marginBottom: 5 }}>Connection</div>
              <div style={{ fontSize: 12, color: '#202124', lineHeight: 1.8, fontFamily: 'monospace' }}>
                {config.connection.host    && <div>Host: {config.connection.host}</div>}
                {config.connection.port    && <div>Port: {config.connection.port}</div>}
                {config.connection.unit_id !== undefined && <div>Unit ID: {config.connection.unit_id}</div>}
                {config.connection.serial_port && <div>Serial: {config.connection.serial_port}</div>}
                {config.connection.baud_rate   && <div>Baud: {config.connection.baud_rate}</div>}
                {config.connection.topic       && <div>Topic: {config.connection.topic}</div>}
                {config.connection.endpoint    && <div>Endpoint: {config.connection.endpoint}</div>}
              </div>
            </div>
            <div>
              <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', color: MUTED, marginBottom: 5 }}>Polling</div>
              <div style={{ fontSize: 12, color: '#202124', lineHeight: 1.8, fontFamily: 'monospace' }}>
                <div>Interval: {config.poll_interval_seconds}s</div>
                <div>Enabled: {config.enabled ? 'Yes' : 'No'}</div>
                <div>Registers: {config.registers?.length ?? 0}</div>
              </div>
            </div>
          </div>

          {config.registers?.length > 0 && (
            <div style={{ marginBottom: 12 }}>
              <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', color: MUTED, marginBottom: 6 }}>Register Mappings</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {config.registers.map((r, i) => (
                  <span key={i} style={{ fontSize: 11, padding: '3px 8px', borderRadius: 6, background: '#f8f9fa', border: '1px solid #e0e0e0', fontFamily: 'monospace', color: '#3c4043' }}>
                    {r.telemetry_field} @{r.address} ×{r.scale}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-secondary btn-sm" onClick={e => { e.stopPropagation(); onTest(config.asset_id) }}>
              <Wifi size={12} style={{ marginRight: 4 }} /> Test
            </button>
            <button className="btn btn-secondary btn-sm" onClick={e => { e.stopPropagation(); onSync(config.asset_id) }}>
              <RefreshCw size={12} style={{ marginRight: 4 }} /> Sync
            </button>
          </div>

          {tr && (
            <div style={{ marginTop: 8, padding: '7px 10px', borderRadius: 7, fontSize: 12, background: tr.success ? '#e6f4ea' : '#fce8e6', color: tr.success ? '#0d904f' : RED }}>
              {tr.success ? <CheckCircle2 size={13} style={{ display: 'inline', marginRight: 5, verticalAlign: 'middle' }} /> : <XCircle size={13} style={{ display: 'inline', marginRight: 5, verticalAlign: 'middle' }} />}
              {tr.message}
            </div>
          )}
          {sr && (
            <div style={{ marginTop: 6, padding: '7px 10px', borderRadius: 7, fontSize: 12, background: '#e6f4ea', color: '#0d904f' }}>
              <CheckCircle2 size={13} style={{ display: 'inline', marginRight: 5, verticalAlign: 'middle' }} />
              Synced {sr.synced} reading(s)
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function HardwareTab() {
  const [configs, setConfigs] = useState<GSHardwareConfig[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState<string | null>(null)
  const [guideOpen, setGuideOpen] = useState(false)
  const [testResults, setTestResults] = useState<Record<string, { success: boolean; message: string } | null>>({})
  const [syncResults, setSyncResults] = useState<Record<string, { synced: number } | null>>({})

  const load = () => {
    setLoading(true)
    gsGetAllHardwareConfigs().then(r => setConfigs(r.data.configs)).catch(e => setError(e.message)).finally(() => setLoading(false))
  }
  useEffect(() => { load() }, [])

  const handleTest = async (id: string) => {
    try { const r = await gsTestHardwareConnection(id); setTestResults(p => ({ ...p, [id]: r.data })) }
    catch (e: any) { setTestResults(p => ({ ...p, [id]: { success: false, message: e.message } })) }
  }
  const handleSync = async (id: string) => {
    try { const r = await gsSyncHardwareData(id); setSyncResults(p => ({ ...p, [id]: r.data })) }
    catch { setSyncResults(p => ({ ...p, [id]: null })) }
  }

  if (loading) return <LoadingSpinner />
  if (error)   return <ErrorBox msg={error} />

  return (
    <div>
      <KPIRow items={[
        { label: 'Connected',     value: configs.filter(c => c.status === 'connected').length,    color: '#0d904f' },
        { label: 'Disconnected',  value: configs.filter(c => c.status !== 'connected').length,    color: '#e8710a' },
        { label: 'Total Devices', value: configs.length },
      ]} />

      {/* Configured devices */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
        <div style={{ fontWeight: 700, fontSize: 14, color: '#202124' }}>Configured Devices</div>
        <button className="btn btn-secondary btn-sm" onClick={load}><RefreshCw size={12} style={{ marginRight: 4 }} /> Refresh</button>
      </div>
      {configs.length === 0
        ? <div className="empty-state"><div className="empty-title">No hardware devices configured</div><div className="empty-desc">Follow the integration guide below to connect your first device.</div></div>
        : configs.map(c => <HardwareCard key={c.asset_id} config={c} onTest={handleTest} onSync={handleSync} testResults={testResults} syncResults={syncResults} />)
      }

      {/* Integration guide (collapsible) */}
      <div className="card" style={{ marginTop: 16, borderLeft: '4px solid #2563eb', padding: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '13px 16px', cursor: 'pointer' }} onClick={() => setGuideOpen(o => !o)}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Info size={15} color="#2563eb" />
            <span style={{ fontWeight: 700, fontSize: 13.5 }}>Integration Guide — Protocols, Devices & Register Map</span>
          </div>
          {guideOpen ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
        </div>
        {guideOpen && (
          <div style={{ padding: '0 16px 16px', fontSize: 13, color: '#3c4043', lineHeight: 1.7 }}>
            {/* Protocols */}
            <div style={{ fontWeight: 700, color: '#202124', marginBottom: 8, marginTop: 4 }}>Supported Protocols</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 16 }}>
              {Object.entries(PROTOCOL_DOCS).map(([k, d]) => (
                <div key={k} style={{ padding: 10, background: '#f8f9fa', borderRadius: 8, border: '1px solid #e0e0e0' }}>
                  <div style={{ fontWeight: 700, fontSize: 12, color: '#202124' }}>{d.label}</div>
                  <div style={{ fontSize: 11, color: MUTED }}>Port: {d.port}</div>
                  <div style={{ fontSize: 11, marginTop: 3 }}>{d.description}</div>
                  <div style={{ fontSize: 11, marginTop: 3, fontStyle: 'italic', color: MUTED }}>Wiring: {d.wiring}</div>
                </div>
              ))}
            </div>
            {/* Register map */}
            <div style={{ fontWeight: 700, color: '#202124', marginBottom: 8 }}>Modbus DTC Register Map</div>
            <div style={{ overflowX: 'auto', border: '1px solid #e0e0e0', borderRadius: 8, marginBottom: 16 }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                <thead>
                  <tr style={{ background: '#f8f9fa', borderBottom: '2px solid #e0e0e0' }}>
                    {['Address', 'Telemetry Field', 'Unit', 'Description'].map(h => (
                      <th key={h} style={{ padding: '7px 10px', textAlign: 'left', fontWeight: 700, color: '#3c4043', fontSize: 11 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {REGISTER_MAP.map((r, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid #f0f0f0' }}>
                      <td style={{ padding: '6px 10px', fontFamily: 'monospace' }}>{r.addr}</td>
                      <td style={{ padding: '6px 10px' }}>{r.field}</td>
                      <td style={{ padding: '6px 10px', fontFamily: 'monospace' }}>{r.unit}</td>
                      <td style={{ padding: '6px 10px', color: MUTED }}>{r.desc}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {/* Steps */}
            <div style={{ padding: 12, background: '#e8f0fe', borderRadius: 8, border: '1px solid #c6dafc' }}>
              <div style={{ fontWeight: 700, color: '#1a56db', fontSize: 12, marginBottom: 6 }}>How to add a new device</div>
              <ol style={{ fontSize: 12, color: '#3c4043', paddingLeft: 18, margin: 0, lineHeight: 2 }}>
                <li>Wire the sensor/RTU to the SCADA network (see protocol wiring notes above).</li>
                <li>Note device IP, Modbus unit ID (or serial port), and register addresses.</li>
                <li>Navigate to <strong>Asset Intelligence</strong> → select asset → <strong>Hardware Integration</strong>.</li>
                <li>Enter connection fields and register mappings, then click <strong>Test Connection</strong>.</li>
                <li>Click <strong>Sync Data</strong> to pull a live reading and confirm it in the Telemetry tab.</li>
                <li>Bottleneck will automatically poll and factor live telemetry into the risk score.</li>
              </ol>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// ─── ENVIRONMENT TAB ─────────────────────────────────────────────────────────

function EnvironmentTab() {
  const envVars = [
    { key: 'SECRET_KEY',                required: false, default: 'dev-fallback',  description: 'JWT signing key. Always set a strong secret in production.' },
    { key: 'GEMINI_API_KEY',            required: false, default: '(none)',         description: 'Enables Gemini-powered AI copilot. Deterministic fallback without it.' },
    { key: 'GRIDSHIELD_USE_REAL_ML',    required: false, default: '1',             description: '"1" = XGBoost pipeline; "0" = deterministic mock predictor.' },
    { key: 'DATABASE_URL',              required: false, default: 'sqlite+aiosqlite:///./gridmind.db', description: 'PostgreSQL URL for production. SQLite used by default.' },
    { key: 'CORS_ORIGINS',              required: false, default: 'http://localhost:5173', description: 'Comma-separated allowed origins for CORS.' },
    { key: 'ALGORITHM',                 required: false, default: 'HS256',         description: 'JWT signing algorithm.' },
    { key: 'ACCESS_TOKEN_EXPIRE_MINUTES', required: false, default: '30',          description: 'JWT access token TTL in minutes.' },
  ]

  const endpoints = [
    { method: 'GET',  path: '/health',                              description: 'Health check' },
    { method: 'POST', path: '/auth/login',                          description: 'Get access + refresh tokens' },
    { method: 'POST', path: '/auth/signup',                         description: 'Create new user account' },
    { method: 'GET',  path: '/auth/me',                             description: 'Current authenticated user' },
    { method: 'GET',  path: '/api/gs/assets',                       description: 'List all 30 grid assets (filterable)' },
    { method: 'GET',  path: '/api/gs/assets/{id}',                  description: 'Single asset detail' },
    { method: 'GET',  path: '/api/gs/assets/{id}/telemetry',        description: '48h hourly telemetry' },
    { method: 'GET',  path: '/api/gs/assets/{id}/incidents',        description: 'Incident history' },
    { method: 'GET',  path: '/api/gs/assets/{id}/maintenance',      description: 'Maintenance records' },
    { method: 'GET',  path: '/api/gs/assets/{id}/intelligence',     description: 'Full intelligence payload' },
    { method: 'GET',  path: '/api/gs/risk',                         description: 'Risk scores (single or all)' },
    { method: 'GET',  path: '/api/gs/risk/ranking',                 description: 'Risk-ranked assets (scenario-aware)' },
    { method: 'GET',  path: '/api/gs/predictions',                  description: 'ML failure predictions' },
    { method: 'GET',  path: '/api/gs/ml/status',                    description: 'Real-ML vs mock status + model files' },
    { method: 'GET',  path: '/api/gs/weather',                      description: 'Weather exposure (all or per asset)' },
    { method: 'GET',  path: '/api/gs/dashboard/kpis',               description: 'Dashboard KPIs' },
    { method: 'GET',  path: '/api/gs/dashboard/alerts',             description: 'Active alerts' },
    { method: 'GET',  path: '/api/gs/maintenance/priorities',       description: 'Impact-aware maintenance priorities' },
    { method: 'GET',  path: '/api/gs/crew',                         description: 'All crews (filterable by availability)' },
    { method: 'GET',  path: '/api/gs/crew/plan',                    description: 'Full crew pre-positioning plan' },
    { method: 'GET',  path: '/api/gs/assets/{id}/crew/nearby',      description: 'Nearest crews by distance + ETA' },
    { method: 'POST', path: '/api/gs/assets/{id}/crew/assign',      description: 'Assign nearest (or specific) crew' },
    { method: 'GET',  path: '/api/gs/hardware/configs',             description: 'All hardware integration configs' },
    { method: 'GET',  path: '/api/gs/assets/{id}/hardware',         description: 'Asset hardware config' },
    { method: 'PUT',  path: '/api/gs/assets/{id}/hardware',         description: 'Update asset hardware config' },
    { method: 'POST', path: '/api/gs/assets/{id}/hardware/test',    description: 'Test hardware connection' },
    { method: 'GET',  path: '/api/gs/assets/{id}/hardware/readings',description: 'Live hardware register readings' },
    { method: 'POST', path: '/api/gs/assets/{id}/hardware/sync',    description: 'Pull fresh hardware data' },
    { method: 'POST', path: '/api/gs/scenarios/simulate',           description: 'Run what-if scenario' },
    { method: 'POST', path: '/api/gs/chat',                         description: 'AI copilot query' },
    { method: 'GET',  path: '/api/gs/chat/sessions/{id}',           description: 'Copilot session history' },
  ]

  const methodColor = (m: string) => {
    if (m === 'GET')    return { bg: '#e8f0fe', color: '#1a73e8' }
    if (m === 'POST')   return { bg: '#e6f4ea', color: '#0d904f' }
    if (m === 'PUT')    return { bg: '#fef7e0', color: '#e8710a' }
    if (m === 'DELETE') return { bg: '#fce8e6', color: '#c5221f' }
    return { bg: '#f1f3f4', color: '#5f6368' }
  }

  return (
    <div>
      <Section title="Environment Variables">
        <div style={{ border: '1px solid #e0e0e0', borderRadius: 12, overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12.5 }}>
            <thead>
              <tr style={{ background: '#f8f9fa', borderBottom: '2px solid #e0e0e0' }}>
                {['Variable', 'Required', 'Default', 'Description'].map(h => (
                  <th key={h} style={{ padding: '9px 12px', textAlign: 'left', fontWeight: 700, color: '#3c4043', fontSize: 11 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {envVars.map((v, i) => (
                <tr key={v.key} style={{ borderBottom: '1px solid #f0f0f0', background: i % 2 === 0 ? '#fff' : '#fafafa' }}>
                  <td style={{ padding: '8px 12px', fontFamily: 'monospace', fontWeight: 700, color: '#202124', whiteSpace: 'nowrap' }}>{v.key}</td>
                  <td style={{ padding: '8px 12px' }}>
                    <Badge label={v.required ? 'Required' : 'Optional'} bg={v.required ? '#fce8e6' : '#f1f3f4'} color={v.required ? RED : MUTED} />
                  </td>
                  <td style={{ padding: '8px 12px', fontFamily: 'monospace', fontSize: 11, color: MUTED }}>{v.default}</td>
                  <td style={{ padding: '8px 12px', color: '#3c4043' }}>{v.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      <Section title="API Endpoints">
        <div style={{ border: '1px solid #e0e0e0', borderRadius: 12, overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12.5 }}>
            <thead>
              <tr style={{ background: '#f8f9fa', borderBottom: '2px solid #e0e0e0' }}>
                {['Method', 'Path', 'Description'].map(h => (
                  <th key={h} style={{ padding: '9px 12px', textAlign: 'left', fontWeight: 700, color: '#3c4043', fontSize: 11 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {endpoints.map((ep, i) => {
                const mc = methodColor(ep.method)
                return (
                  <tr key={i} style={{ borderBottom: '1px solid #f0f0f0', background: i % 2 === 0 ? '#fff' : '#fafafa' }}>
                    <td style={{ padding: '7px 12px' }}>
                      <Badge label={ep.method} bg={mc.bg} color={mc.color} />
                    </td>
                    <td style={{ padding: '7px 12px', fontFamily: 'monospace', fontSize: 11.5, color: '#202124', whiteSpace: 'nowrap' }}>{ep.path}</td>
                    <td style={{ padding: '7px 12px', color: MUTED }}>{ep.description}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </Section>

      <Section title="Demo Credentials">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          {[
            { label: 'Email',    value: 'demo@gridshield.ai' },
            { label: 'Password', value: 'demo1234' },
          ].map(item => (
            <div key={item.label} style={{ padding: '12px 16px', background: '#f8f9fa', borderRadius: 10, border: '1px solid #e0e0e0' }}>
              <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', color: MUTED, marginBottom: 4 }}>{item.label}</div>
              <div style={{ fontFamily: 'monospace', fontSize: 14, fontWeight: 700, color: '#202124' }}>{item.value}</div>
            </div>
          ))}
        </div>
      </Section>
    </div>
  )
}

// ─── Shared util components ───────────────────────────────────────────────────

function LoadingSpinner() {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', padding: 60 }}>
      <Loader2 size={28} className="animate-spin" color="#1a73e8" />
    </div>
  )
}

function ErrorBox({ msg }: { msg: string }) {
  return (
    <div className="card" style={{ borderLeft: `4px solid ${RED}` }}>
      <div style={{ fontWeight: 700, color: RED, marginBottom: 4 }}>Error loading data</div>
      <div style={{ fontSize: 13, color: MUTED }}>{msg}</div>
    </div>
  )
}

// ─── MAIN SETTINGS PAGE ───────────────────────────────────────────────────────

const TABS = [
  { id: 'assets',      label: 'Asset Fleet',        icon: <Activity  size={14} /> },
  { id: 'crews',       label: 'Crew Roster',         icon: <Users     size={14} /> },
  { id: 'ml',          label: 'ML & System',         icon: <Cpu       size={14} /> },
  { id: 'hardware',    label: 'Hardware',            icon: <Server    size={14} /> },
  { id: 'environment', label: 'Environment & APIs',  icon: <Globe     size={14} /> },
]

export default function Settings() {
  const [tab, setTab] = useState('assets')

  return (
    <div>
      {/* Page header */}
      <div className="page-header flex-between">
        <div>
          <div className="page-title" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <SettingsIcon size={22} color="#1a73e8" /> Settings & Configuration
          </div>
          <div className="page-subtitle">Asset fleet, crew roster, ML pipeline, hardware integration, and environment</div>
        </div>
      </div>

      {/* Tab bar */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 24, borderBottom: '2px solid #e0e0e0', paddingBottom: 0 }}>
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '9px 16px', borderRadius: '8px 8px 0 0',
              fontSize: 13, fontWeight: 600, cursor: 'pointer',
              border: 'none', borderBottom: tab === t.id ? '2.5px solid #1a73e8' : '2.5px solid transparent',
              background: tab === t.id ? '#e8f0fe' : 'transparent',
              color: tab === t.id ? '#1a73e8' : '#5f6368',
              marginBottom: -2,
              transition: 'all 0.13s',
            }}
          >
            {t.icon}{t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === 'assets'      && <AssetFleetTab />}
      {tab === 'crews'       && <CrewRosterTab />}
      {tab === 'ml'          && <MLSystemTab />}
      {tab === 'hardware'    && <HardwareTab />}
      {tab === 'environment' && <EnvironmentTab />}
    </div>
  )
}
