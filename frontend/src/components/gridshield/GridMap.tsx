import React, { useEffect, useState, useMemo } from 'react'
import { MapContainer, TileLayer, Popup, CircleMarker, Polyline } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import { gsGetRiskRanking, type GSRankingEntry, type GSNearbyCrew } from '../../api/gridshield'
import {
  Zap, AlertTriangle, MapPin, Truck,
  ShieldAlert, TrendingUp, Users, Wind,
  Loader2, RefreshCw, Layers, X, Clock, CheckCircle2
} from 'lucide-react'
import { riskBadgeClass, MUTED } from './utils'

const DEFAULT_CENTER: [number, number] = [23.0225, 72.5714]
const DEFAULT_ZOOM = 11

const assetTypeColors = {
  transformer: '#2563eb',
  feeder: '#eab308',
  breaker: '#c5221f',
  recloser: '#7c3aed',
  switch: '#0ea5e9',
  capacitor_bank: '#8b5cf6',
}

const riskLevelColors: Record<string, string> = {
  critical: '#c5221f',
  high: '#e8710a',
  medium: '#eab308',
  low: '#0d904f',
}

const riskLevelLabels = {
  critical: 'CRITICAL',
  high: 'HIGH',
  medium: 'MEDIUM',
  low: 'LOW',
}

interface GridMapProps {
  selectedAssetId?: string
  onAssetSelect: (assetId: string) => void
  scenario?: string
}

function RiskCircleMarker({ entry, onClick, onMouseEnter, onMouseLeave, isSelected }: {
  entry: GSRankingEntry
  onClick: () => void
  onMouseEnter: () => void
  onMouseLeave: () => void
  isSelected: boolean
}) {
  const color = riskLevelColors[entry.risk_level]
  const assetType = entry.asset_type.toLowerCase().replace(' ', '_') as keyof typeof assetTypeColors
  const typeColor = assetTypeColors[assetType] || '#2563eb'

  return (
    <CircleMarker
      center={[entry.asset_lat, entry.asset_lon]}
      radius={isSelected ? 16 : 12}
      pathOptions={{
        fillColor: color,
        color: isSelected ? '#fff' : typeColor,
        weight: isSelected ? 3 : 2,
        fillOpacity: 0.9,
        opacity: 1,
      }}
      eventHandlers={{
        click: onClick,
        mouseover: onMouseEnter,
        mouseout: onMouseLeave,
      }}
    >
      <Popup
        offset={[0, -16]}
        className="gridshield-popup"
      >
        <div style={{ minWidth: 180, padding: 4 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
            <div style={{
              width: 10, height: 10, borderRadius: '50%',
              background: color, border: '2px solid white', boxShadow: '0 1px 3px rgba(0,0,0,0.3)'
            }} />
            <span style={{ fontWeight: 700, fontSize: 13, color: '#202124' }}>{entry.asset_name}</span>
          </div>
          <div style={{ display: 'flex', gap: 8, fontSize: 11, color: MUTED }}>
            <span>{entry.asset_id}</span>
            <span>{entry.region}</span>
          </div>
          <div style={{ marginTop: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
            <span className={riskBadgeClass(entry.risk_level)} style={{ fontSize: 10 }}>{riskLevelLabels[entry.risk_level]}</span>
            <span style={{ fontSize: 12, fontWeight: 700, color }}>{entry.risk_score.toFixed(0)}/100</span>
          </div>
          <div style={{ marginTop: 4, fontSize: 11, color: MUTED }}>
            Customers: {entry.customers_at_risk.toLocaleString()} | Critical: {entry.critical_facilities_at_risk}
          </div>
          <div style={{ marginTop: 6, display: 'flex', gap: 6 }}>
            <button
              onClick={(e) => { e.stopPropagation(); onClick(); }}
              style={{
                flex: 1, padding: '6px 10px', background: '#2563eb', color: 'white',
                border: 'none', borderRadius: 6, fontSize: 11, fontWeight: 600, cursor: 'pointer'
              }}
            >
              View Details
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); onClick(); }}
              style={{
                flex: 1, padding: '6px 10px', background: '#0d904f', color: 'white',
                border: 'none', borderRadius: 6, fontSize: 11, fontWeight: 600, cursor: 'pointer'
              }}
            >
              <Truck className="h-3 w-3 inline-block align-middle mr-1" /> Assign Crew
            </button>
          </div>
        </div>
      </Popup>
    </CircleMarker>
  )
}

function AssetMarkerLayer({ entries, selectedId, onSelect, onHover, onHoverEnd }: {
  entries: GSRankingEntry[]
  selectedId: string | undefined
  onSelect: (id: string) => void
  onHover?: (entry: GSRankingEntry) => void
  onHoverEnd?: () => void
}) {
  return (
    <>
      {entries.map(entry => (
        <RiskCircleMarker
          key={entry.asset_id}
          entry={entry}
          isSelected={selectedId === entry.asset_id}
          onClick={() => onSelect(entry.asset_id)}
          onMouseEnter={() => onHover?.(entry)}
          onMouseLeave={() => onHoverEnd?.()}
        />
      ))}
    </>
  )
}

function MapControls({ scenario, onScenarioChange, layers, onLayerToggle, filter, onFilterChange, onRefresh }: {
  scenario: string
  onScenarioChange: (s: string) => void
  layers: Record<string, boolean>
  onLayerToggle: (layer: string) => void
  filter: string
  onFilterChange: (f: string) => void
  onRefresh: () => void
}) {
  const scenarios = [
    { id: 'none', label: 'Current' },
    { id: 'severe_storm', label: 'Severe Storm' },
    { id: 'heatwave', label: 'Heatwave' },
    { id: 'asset_degradation', label: 'Asset Degradation' },
  ]

  const layerOptions = [
    { id: 'assets', label: 'Grid Assets', icon: Zap },
    { id: 'critical', label: 'Critical Only', icon: ShieldAlert },
    { id: 'weather', label: 'Weather Exposure', icon: Wind },
    { id: 'incidents', label: 'Active Incidents', icon: AlertTriangle },
    { id: 'facilities', label: 'Critical Facilities', icon: MapPin },
  ]

  return (
    <div className="card" style={{ position: 'absolute', top: 16, left: 16, zIndex: 1000, minWidth: 260, maxHeight: 'calc(100vh - 32px)', overflowY: 'auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
        <div className="card-title" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Layers className="h-4 w-4" />
          Map Controls
        </div>
        <button onClick={onRefresh} className="btn btn-ghost btn-sm" title="Refresh">
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>

      <div style={{ marginBottom: 16 }}>
        <label className="text-xs font-medium text-zinc-500 mb-1 block">Scenario</label>
        <select
          value={scenario}
          onChange={(e) => onScenarioChange(e.target.value)}
          className="select"
          style={{ width: '100%' }}
        >
          {scenarios.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}
        </select>
      </div>

      <div style={{ marginBottom: 16 }}>
        <label className="text-xs font-medium text-zinc-500 mb-1 block">Filter</label>
        <select
          value={filter}
          onChange={(e) => onFilterChange(e.target.value)}
          className="select"
          style={{ width: '100%' }}
        >
          <option value="all">All Risk Levels</option>
          <option value="critical">Critical Only</option>
          <option value="high">High & Above</option>
          <option value="medium">Medium & Above</option>
        </select>
      </div>

      <div style={{ marginBottom: 16 }}>
        <label className="text-xs font-medium text-zinc-500 mb-1 block">Layers</label>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {layerOptions.map(l => (
            <label key={l.id} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={layers[l.id]}
                onChange={() => onLayerToggle(l.id)}
                className="w-4 h-4 accent-blue-600"
              />
              <l.icon className="h-3.5 w-3.5" style={{ color: '#2563eb' }} />
              <span>{l.label}</span>
            </label>
          ))}
        </div>
      </div>

      <div style={{ paddingTop: 8, borderTop: '1px solid #e0e0e0', fontSize: 11, color: MUTED }}>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          {Object.entries(riskLevelLabels).map(([level, label]) => (
            <div key={level} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <span style={{
                width: 10, height: 10, borderRadius: '50%',
                background: riskLevelColors[level as keyof typeof riskLevelColors]
              }} />
              <span>{label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function HoverCard({ entry, onClose }: { entry: GSRankingEntry | null, onClose?: () => void }) {
  if (!entry) return null

  const color = riskLevelColors[entry.risk_level]

  return (
    <div className="card" style={{ position: 'absolute', bottom: 16, left: 16, right: 16, zIndex: 1000, maxWidth: 400, margin: '0 auto', animation: 'fadeIn 0.15s ease-out' }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <div style={{
              width: 12, height: 12, borderRadius: '50%',
              background: color, border: '2px solid white', boxShadow: '0 1px 3px rgba(0,0,0,0.2)'
            }} />
            <div>
              <div style={{ fontWeight: 700, fontSize: 14, color: '#202124', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {entry.asset_name}
              </div>
              <div style={{ fontSize: 12, color: MUTED }}>{entry.asset_id} · {entry.asset_type} · {entry.region}</div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 12, fontSize: 12, color: MUTED, flexWrap: 'wrap', marginBottom: 8 }}>
            <span><Users className="h-3 w-3 inline-block align-middle" style={{ marginRight: 4 }} /> {entry.customers_at_risk.toLocaleString()} customers</span>
            <span><ShieldAlert className="h-3 w-3 inline-block align-middle" style={{ marginRight: 4 }} /> {entry.critical_facilities_at_risk} critical</span>
            <span><TrendingUp className="h-3 w-3 inline-block align-middle" style={{ marginRight: 4 }} /> 24h: {(entry.failure_probability_24h * 100).toFixed(0)}%</span>
          </div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {entry.top_factors.slice(0, 3).map((f, i) => (
              <span key={i} className="badge badge-default" style={{ fontSize: 10 }}>{f}</span>
            ))}
          </div>
        </div>
        <div style={{ textAlign: 'right', flexShrink: 0 }}>
          <div style={{ fontSize: 28, fontWeight: 800, color, lineHeight: 1 }}>{entry.risk_score.toFixed(0)}</div>
          <span className={riskBadgeClass(entry.risk_level)} style={{ fontSize: 11 }}>{riskLevelLabels[entry.risk_level]}</span>
          {onClose && (
            <button
              onClick={onClose}
              style={{
                position: 'absolute', top: 8, right: 8, padding: 4, background: 'transparent',
                border: 'none', cursor: 'pointer', color: MUTED,
              }}
              aria-label="Close"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default function GridMap({ selectedAssetId, onAssetSelect, scenario = 'none' }: GridMapProps) {
  const [ranking, setRanking] = useState<GSRankingEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeScenario, setActiveScenario] = useState(scenario)
  const [layers, setLayers] = useState<Record<string, boolean>>({
    assets: true,
    critical: false,
    weather: false,
    incidents: false,
    facilities: false,
  })
  const [filter, setFilter] = useState<'all' | 'critical' | 'high' | 'medium'>('all')
  const [hoveredEntry, setHoveredEntry] = useState<GSRankingEntry | null>(null)

  useEffect(() => {
    loadRanking()
  }, [activeScenario])

  const loadRanking = async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await gsGetRiskRanking(activeScenario)
      setRanking(res.data.ranking)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const filteredEntries = useMemo(() => {
    let entries = ranking
    if (filter === 'critical') entries = entries.filter(e => e.risk_level === 'critical')
    else if (filter === 'high') entries = entries.filter(e => ['critical', 'high'].includes(e.risk_level))
    else if (filter === 'medium') entries = entries.filter(e => ['critical', 'high', 'medium'].includes(e.risk_level))
    return entries
  }, [ranking, filter])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full w-full bg-gray-50">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          <span className="text-zinc-500">Loading grid assets...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full w-full bg-gray-50">
        <div className="card text-center p-8" style={{ maxWidth: 320 }}>
          <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h3 className="font-semibold text-zinc-900 mb-2">Failed to load map data</h3>
          <p className="text-sm text-zinc-500 mb-4">{error}</p>
          <button className="btn btn-primary btn-sm" onClick={loadRanking}>Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="relative w-full" style={{ height: 'calc(100vh - 130px)', minHeight: '600px' }}>
      <MapContainer
        center={DEFAULT_CENTER}
        zoom={DEFAULT_ZOOM}
        scrollWheelZoom={true}
        style={{ height: '100%', width: '100%', zIndex: 0 }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <AssetMarkerLayer
          entries={filteredEntries}
          selectedId={selectedAssetId}
          onSelect={onAssetSelect}
          onHover={setHoveredEntry}
          onHoverEnd={() => setHoveredEntry(null)}
        />
      </MapContainer>

      <MapControls
        scenario={activeScenario}
        onScenarioChange={setActiveScenario}
        layers={layers}
        onLayerToggle={(l) => setLayers(prev => ({ ...prev, [l]: !prev[l] }))}
        filter={filter}
        onFilterChange={(f: string) => setFilter(f as 'all' | 'critical' | 'high' | 'medium')}
        onRefresh={loadRanking}
      />

      <HoverCard entry={hoveredEntry} />

      <div className="absolute bottom-4 right-4 z-50">
        <div className="card p-3" style={{ minWidth: 180 }}>
          <div className="text-xs font-medium text-zinc-500 mb-2">Visible Assets</div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
            <span className="text-zinc-500">Total</span>
            <span className="font-semibold">{ranking.length}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginTop: 4 }}>
            <span className="text-zinc-500">Filtered</span>
            <span className="font-semibold">{filteredEntries.length}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginTop: 4, paddingTop: 4, borderTop: '1px solid #e0e0e0' }}>
            <span className="text-zinc-500">Critical</span>
            <span className="font-semibold text-red-600">{ranking.filter(e => e.risk_level === 'critical').length}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

interface GridMapEmbeddedProps {
  riskEntry: GSRankingEntry
  nearby: GSNearbyCrew[]
  assignedCrewId?: string | null
  onAssign?: (crewId: string) => void
  onRefresh?: () => void
}

export function GridMapEmbedded({ riskEntry, nearby, assignedCrewId, onAssign, onRefresh }: GridMapEmbeddedProps) {
  const color = riskLevelColors[riskEntry.risk_level]
  const center: [number, number] = [riskEntry.asset_lat, riskEntry.asset_lon]
  const best = nearby.find(n => n.crew.crew_id === assignedCrewId) || nearby[0]

  return (
    <div className="relative w-full h-full">
      <MapContainer
        center={center}
        zoom={13}
        scrollWheelZoom={true}
        style={{ height: '100%', width: '100%', zIndex: 0 }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Crew depot markers + dispatch lines */}
        {nearby.map(n => {
          const clat = n.crew.lat ?? riskEntry.asset_lat
          const clon = n.crew.lon ?? riskEntry.asset_lon
          return (
          <React.Fragment key={n.crew.crew_id}>
            <Polyline
              positions={[[clat, clon], center]}
              pathOptions={{
                color: n.specialty_match ? '#0d904f' : '#2563eb',
                weight: assignedCrewId === n.crew.crew_id ? 4 : 2,
                dashArray: '6, 6',
                opacity: assignedCrewId === n.crew.crew_id ? 1 : 0.6,
              }}
            />
            <CircleMarker
              center={[clat, clon]}
              radius={assignedCrewId === n.crew.crew_id ? 14 : 9}
              pathOptions={{
                fillColor: assignedCrewId === n.crew.crew_id ? '#0d904f' : n.specialty_match ? '#0d904f' : '#2563eb',
                color: '#fff',
                weight: assignedCrewId === n.crew.crew_id ? 3 : 2,
                fillOpacity: 0.95,
              }}
            >
              <Popup offset={[0, -12]} className="gridshield-popup">
                <div style={{ padding: 4, minWidth: 190 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
                    <Truck className="h-3.5 w-3.5" style={{ color: '#0d904f' }} />
                    <span style={{ fontWeight: 700, fontSize: 13, color: '#202124' }}>{n.crew.name}</span>
                  </div>
                  <div style={{ fontSize: 11, color: MUTED, marginBottom: 4 }}>{n.crew.crew_id} · {n.crew.region}{n.specialty_match ? ' · Specialty MATCH' : ''}</div>
                  <div style={{ display: 'flex', gap: 10, fontSize: 11, color: MUTED, marginBottom: 6 }}>
                    <span><MapPin className="h-3 w-3 inline-block align-middle mr-1" />{n.distance_km} km</span>
                    <span><Clock className="h-3 w-3 inline-block align-middle mr-1" />ETA ~{n.eta_hours}h</span>
                  </div>
                  {assignedCrewId === n.crew.crew_id ? (
                    <div style={{ color: '#0d904f', fontWeight: 700, fontSize: 12 }}>
                      <CheckCircle2 className="h-3.5 w-3.5 inline-block align-middle mr-1" />Dispatched to asset
                    </div>
                  ) : (
                    <button
                      onClick={(e) => { e.stopPropagation(); onAssign?.(n.crew.crew_id) }}
                      style={{
                        padding: '6px 12px', background: '#0d904f', color: 'white',
                        border: 'none', borderRadius: 6, fontSize: 11, fontWeight: 600, cursor: 'pointer',
                      }}
                    >
                      <Truck className="h-3 w-3 inline-block align-middle mr-1" />Assign this crew
                    </button>
                  )}
                </div>
              </Popup>
            </CircleMarker>
          </React.Fragment>
          )
        })}

        {/* Asset risk marker + zone */}
        <CircleMarker
          center={center}
          radius={18}
          pathOptions={{
            fillColor: color,
            color: '#fff',
            weight: 4,
            fillOpacity: 0.95,
            opacity: 1,
          }}
        >
          <Popup offset={[0, -18]} className="gridshield-popup">
            <div style={{ padding: 4, minWidth: 180 }}>
              <div style={{ fontWeight: 700, fontSize: 13, color: '#202124', marginBottom: 2 }}>{riskEntry.asset_name}</div>
              <div style={{ fontSize: 11, color: MUTED, marginBottom: 4 }}>{riskEntry.asset_id} · {riskEntry.asset_type} · {riskEntry.region}</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span className={riskBadgeClass(riskEntry.risk_level)} style={{ fontSize: 10 }}>{riskLevelLabels[riskEntry.risk_level]}</span>
                <span style={{ fontSize: 12, fontWeight: 700, color }}>{riskEntry.risk_score.toFixed(0)}/100</span>
              </div>
              <div style={{ marginTop: 4, fontSize: 11, color: MUTED }}>
                {best ? `Nearest crew ${best.distance_km} km · ETA ~${best.eta_hours}h` : 'No crew nearby'}
              </div>
            </div>
          </Popup>
        </CircleMarker>
        <CircleMarker
          center={center}
          radius={90}
          pathOptions={{ color, weight: 1.5, fillColor: color, fillOpacity: 0.08, dashArray: '6, 8' }}
        />
        <CircleMarker
          center={center}
          radius={160}
          pathOptions={{ color, weight: 1, fillColor: color, fillOpacity: 0.05, dashArray: '3, 10' }}
        />
      </MapContainer>

      {/* Legend + coords overlays (kept here so the page stays map-only) */}
      <div className="card p-3" style={{ position: 'absolute', bottom: 14, left: 14, zIndex: 1000, minWidth: 200 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
          <span style={{ width: 10, height: 10, borderRadius: '50%', background: color, border: '2px solid #fff', boxShadow: '0 1px 2px rgba(0,0,0,0.3)' }} />
          <span style={{ fontSize: 11, color: MUTED }}>{riskEntry.asset_type}</span>
          <span style={{ marginLeft: 'auto', fontSize: 11, fontWeight: 700, color }}>{riskEntry.risk_score.toFixed(0)}/100</span>
        </div>
        <div style={{ fontSize: 11, color: MUTED, display: 'flex', alignItems: 'center', gap: 6 }}>
          <MapPin className="h-3 w-3" />
          {riskEntry.asset_lat.toFixed(4)}, {riskEntry.asset_lon.toFixed(4)}
          {onRefresh && (
            <button onClick={onRefresh} className="btn btn-ghost btn-sm" title="Refresh" style={{ padding: 2, marginLeft: 4 }}>
              <RefreshCw className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}