/**
 * GridShield API client — all /api/gs/* endpoints.
 * No auth required for GridShield endpoints (public grid ops data).
 */
import axios from 'axios'

const gs = axios.create({ baseURL: '', timeout: 15000 })

// ─── Types ────────────────────────────────────────────────────────────────────

export interface GSLocation { lat: number; lon: number }

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

// ─── ML Model Management ─────────────────────────────────────────────────────

export interface GSModelStatus {
  ml_enabled: boolean
  models_loaded: boolean
  status: 'healthy' | 'degraded' | 'no_data'
  model_version: string
  total_predictions: number
  unique_assets: number
  mean_p24: number
  mean_anomaly_score: number
  mean_confidence: number
  fallback_rate: number
  anomaly_rate_alert: boolean
  drift_alerts: Array<{ asset_id: string; drift_detected: boolean; delta: number; message: string }>
  baseline_p24: number | null
  generated_at: string
}

export interface GSModelMetrics {
  evaluated_at?: string
  models?: {
    failure_24h?: Record<string, any>
    failure_72h?: Record<string, any>
  }
}

export const gsGetModelStatus = () =>
  gs.get<GSModelStatus>('/api/gs/model/status')

export const gsGetModelMetrics = () =>
  gs.get<GSModelMetrics>('/api/gs/model/metrics')

export const gsTriggerRetrain = () =>
  gs.post<{ job_id: string; status: string; message: string }>('/api/gs/model/retrain', {})

export default gs
