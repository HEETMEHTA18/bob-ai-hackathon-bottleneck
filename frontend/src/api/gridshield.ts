/**
 * GridShield API client — all /api/gs/* endpoints.
 * Requires authentication (Bearer token from localStorage).
 */
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || ''

const gs = axios.create({ baseURL: API_BASE, timeout: 15000 })

// Attach auth token to every GridShield request
gs.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Auto-redirect on 401
gs.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.reload()
    }
    return Promise.reject(error)
  }
)

// ─── Types ────────────────────────────────────────────────────────────────────

export interface GSLocation { lat: number; lon: number }

export interface GSHardwareConfig {
  asset_id: string
  device_type: 'dtc' | 'smart_sensor' | 'pmcu' | 'rtu' | 'custom'
  protocol: 'modbus' | 'modbus_tcp' | 'dnp3' | 'iec61850' | 'mqtt' | 'opcua' | 'http'
  connection: {
    host?: string
    port?: number
    unit_id?: number
    baud_rate?: number
    serial_port?: string
    topic?: string
    endpoint?: string
    auth?: { username: string; password: string }
  }
  registers: Array<{
    name: string
    address: number
    type: 'holding' | 'input' | 'coil' | 'discrete'
    data_type: 'uint16' | 'int16' | 'uint32' | 'int32' | 'float32' | 'float64' | 'bool'
    scale: number
    offset: number
    unit: string
    telemetry_field: 'oil_temperature' | 'load_percentage' | 'vibration' | 'current_unbalance' | 'voltage_deviation' | 'partial_discharge' | 'ambient_temperature'
  }>
  poll_interval_seconds: number
  enabled: boolean
  last_sync: string | null
  status: 'connected' | 'disconnected' | 'error' | 'configuring'
}

export interface GSHardwareReading {
  asset_id: string
  timestamp: string
  readings: Record<string, number>
  quality: 'good' | 'uncertain' | 'bad'
}

export interface GSAsset {
  id: string
  name: string
  asset_type: 'transformer' | 'feeder' | 'breaker' | 'recloser' | 'switch' | 'capacitor_bank'
  substation_id: string
  location: GSLocation
  criticality: number
  capacity_mva: number
  age_years: number
  redundancy_level: number
  status: 'healthy' | 'degraded' | 'critical' | 'offline' | 'maintenance'
  region: string
  hardware_config?: GSHardwareConfig
}

export interface GSRisk {
  asset_id: string
  risk_score: number
  risk_level: 'critical' | 'high' | 'medium' | 'low'
  failure_probability_24h: number
  failure_probability_72h: number
  health_score: number
  anomaly_score: number
  grid_impact_score: number
  weather_exposure_score: number
  criticality_score: number
  redundancy_score: number
  customers_at_risk: number
  critical_facilities_at_risk: number
  top_factors: string[]
}

export interface GSPrediction {
  asset_id: string
  failure_probability_24h: number
  failure_probability_72h: number
  health_score: number
  anomaly_score: number
  confidence: number
  top_factors: string[]
  model_version: string
}

export interface GSGridImpact {
  asset_id: string
  customers_at_risk: number
  critical_facilities_at_risk: number
  capacity_mva: number
  grid_impact_score: number
  downstream_assets: number
}

export interface GSWeather {
  asset_id: string
  temperature: number
  wind_speed: number
  precipitation: number
  humidity: number
  storm_severity: number
  heatwave_indicator: boolean
  severe_weather_indicator: boolean
  weather_exposure_score: number
}

export interface GSMaintenance {
  asset_id: string
  priority: number
  priority_level: 'immediate' | 'high' | 'medium' | 'monitor'
  recommended_action: string
  recommended_window: string
  reason: string
  estimated_duration_hours: number
  assigned_crew_id: string | null
}

export interface GSRankingEntry {
  rank: number
  asset_id: string
  asset_name: string
  asset_type: string
  region: string
  status: string
  risk_score: number
  risk_level: 'critical' | 'high' | 'medium' | 'low'
  failure_probability_24h: number
  failure_probability_72h: number
  health_score: number
  customers_at_risk: number
  critical_facilities_at_risk: number
  grid_impact_score: number
  recommended_action: string
  priority_level: string
  assigned_crew: string | null
  top_factors: string[]
  asset_lat: number
  asset_lon: number
}

export interface GSKPIs {
  critical_assets: number
  high_risk_assets: number
  customers_at_risk: number
  critical_facilities_at_risk: number
  crews_pre_positioned: number
  total_assets: number
  timestamp: string
}

export interface GSAlert {
  alert_id: string
  asset_id: string
  asset_name: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  message: string
  timestamp: string
}

export interface GSTelemetryRecord {
  asset_id: string
  timestamp: string
  oil_temperature: number
  load_percentage: number
  vibration: number
  current_unbalance: number
  voltage_deviation: number
  partial_discharge: number
  ambient_temperature: number
}

export interface GSIncident {
  incident_id: string
  asset_id: string
  timestamp: string
  description: string
  severity: 'minor' | 'moderate' | 'major' | 'critical'
}

export interface GSMaintenanceRecord {
  record_id: string
  asset_id: string
  date: string
  work_done: string
  technician: string
}

export interface GSCrew {
  crew_id: string
  name: string
  specialty: string
  region: string
  availability: 'available' | 'busy' | 'offline'
  capacity: number
  lat?: number
  lon?: number
}

export interface GSCrewAssignment {
  crew_id: string
  asset_id: string
  asset_name: string
  asset_type: string
  region: string
  risk_score: number
  risk_level: string
  crew_name: string
  crew_specialty: string
  assignment: 'Pre-position' | 'Dispatch' | 'Standby'
  priority: number
  reason: string
  eta_hours: number
}

export interface GSIntelligence {
  asset: GSAsset
  risk: GSRisk
  prediction: GSPrediction
  grid_impact: GSGridImpact
  weather: GSWeather
  maintenance_recommendation: GSMaintenance
  telemetry_24h: GSTelemetryRecord[]
  incidents: GSIncident[]
  maintenance_history: GSMaintenanceRecord[]
}

export interface GSScenarioResult {
  scenario: string
  asset_id: string
  risk_before: number
  risk_after: number
  risk_level_before: string
  risk_level_after: string
  maintenance_priority_before: number
  maintenance_priority_after: number
  crew_assigned: string | null
  description: string
}

// ─── API functions ────────────────────────────────────────────────────────────

export const gsGetAssets = (params?: { asset_type?: string; region?: string; status?: string }) =>
  gs.get<{ assets: GSAsset[]; count: number }>('/api/gs/assets', { params })

export const gsGetAsset = (assetId: string) =>
  gs.get<GSAsset>(`/api/gs/assets/${assetId}`)

export const gsGetTelemetry = (assetId: string, hours = 48) =>
  gs.get<{ asset_id: string; records: GSTelemetryRecord[]; count: number }>(
    `/api/gs/assets/${assetId}/telemetry`, { params: { hours } }
  )

export const gsGetIncidents = (assetId: string) =>
  gs.get<{ asset_id: string; incidents: GSIncident[] }>(`/api/gs/assets/${assetId}/incidents`)

export const gsGetMaintenanceHistory = (assetId: string) =>
  gs.get<{ asset_id: string; records: GSMaintenanceRecord[] }>(`/api/gs/assets/${assetId}/maintenance`)

export const gsGetWeather = (assetId?: string) =>
  gs.get('/api/gs/weather', { params: assetId ? { asset_id: assetId } : {} })

export const gsGetRiskRanking = (scenario?: string) =>
  gs.get<{ ranking: GSRankingEntry[]; total: number; scenario: string | null }>(
    '/api/gs/risk/ranking', { params: scenario ? { scenario } : {} }
  )

export const gsGetKPIs = (scenario?: string) =>
  gs.get<GSKPIs>('/api/gs/dashboard/kpis', { params: scenario ? { scenario } : {} })

export const gsGetAlerts = () =>
  gs.get<{ alerts: GSAlert[]; count: number }>('/api/gs/dashboard/alerts')

export const gsGetMaintenancePriorities = (params?: {
  priority_level?: string; asset_type?: string; region?: string
}) => gs.get<{ priorities: any[]; count: number }>('/api/gs/maintenance/priorities', { params })

export const gsGetCrews = (availability?: string) =>
  gs.get<{ crews: GSCrew[]; count: number }>('/api/gs/crew', {
    params: availability ? { availability } : {}
  })

export const gsGetCrewPlan = () =>
  gs.get<{ assignments: GSCrewAssignment[]; standby: any[]; total_assigned: number; total_standby: number }>(
    '/api/gs/crew/plan'
  )

export const gsGetAssetIntelligence = (assetId: string) =>
  gs.get<GSIntelligence>(`/api/gs/assets/${assetId}/intelligence`)

export const gsSimulateScenario = (scenario: string, assetId?: string) =>
  gs.post<{ scenario: string; results: GSScenarioResult[] }>('/api/gs/scenarios/simulate', {
    scenario, asset_id: assetId || null
  })

export const gsChat = (message: string, sessionId?: string) =>
  gs.post<{ session_id: string; response: string; timestamp: string }>('/api/gs/chat', {
    message, session_id: sessionId
  })

export interface GSMLStatus {
  mode: 'real_ml' | 'mock'
  use_real_ml: boolean
  models_available: boolean
  models_directory: string
  model_files: Record<string, { size_bytes: number; modified: string }>
  model_version?: string
  trained_at?: string
  metrics?: Record<string, any>
}

export const gsGetMLStatus = () =>
  gs.get<GSMLStatus>('/api/gs/ml/status')

export default gs

// ─── Hardware Integration API ────────────────────────────────────────────────

export const gsGetHardwareConfig = (assetId: string) =>
  gs.get<GSHardwareConfig>(`/api/gs/assets/${assetId}/hardware`)

export const gsUpdateHardwareConfig = (assetId: string, config: Partial<GSHardwareConfig>) =>
  gs.put<GSHardwareConfig>(`/api/gs/assets/${assetId}/hardware`, config)

export const gsTestHardwareConnection = (assetId: string) =>
  gs.post<{ success: boolean; message: string; readings?: GSHardwareReading }>(`/api/gs/assets/${assetId}/hardware/test`, {})

export const gsGetHardwareReadings = (assetId: string, hours = 24) =>
  gs.get<{ asset_id: string; readings: GSHardwareReading[] }>(`/api/gs/assets/${assetId}/hardware/readings`, { params: { hours } })

export const gsGetAllHardwareConfigs = () =>
  gs.get<{ configs: GSHardwareConfig[] }>('/api/gs/hardware/configs')

export const gsSyncHardwareData = (assetId: string) =>
  gs.post<{ synced: number; errors: string[] }>(`/api/gs/assets/${assetId}/hardware/sync`, {})

// ─── Crew Assignment API ─────────────────────────────────────────────────────

export interface GSNearbyCrew {
  crew: GSCrew
  distance_km: number
  eta_hours: number
  specialty_match: boolean
}

export interface GSCrewAssignResult {
  crew: GSCrew
  asset_id: string
  asset_name: string
  distance_km: number
  eta_hours: number
  assignment: 'Pre-position' | 'Dispatch' | 'Standby'
  reason: string
}

export const gsGetNearbyCrews = (assetId: string, limit = 4) =>
  gs.get<{ asset_id: string; asset_lat: number; asset_lon: number; nearby: GSNearbyCrew[] }>(
    `/api/gs/assets/${assetId}/crew/nearby`, { params: { limit } }
  )

export const gsAssignCrew = (assetId: string, crewId?: string) =>
  gs.post<GSCrewAssignResult>(`/api/gs/assets/${assetId}/crew/assign`, { crew_id: crewId || null })
