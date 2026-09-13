import axios from 'axios'

const api = axios.create({
  baseURL: '',
  timeout: 30000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const res = await axios.post('/auth/refresh', { refresh_token: refreshToken })
          localStorage.setItem('access_token', res.data.access_token)
          localStorage.setItem('refresh_token', res.data.refresh_token)
          error.config.headers.Authorization = `Bearer ${res.data.access_token}`
          return api(error.config)
        } catch {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.reload()
        }
      }
    }
    return Promise.reject(error)
  }
)

export interface User {
  id: string
  email: string
  full_name: string
  company_name?: string
  role: string
}

export interface Site {
  id: string
  name: string
  site_type: string
  latitude: number
  longitude: number
  altitude?: number
  capacity_kw: number
  battery_capacity_kwh: number
  export_limit_kw: number
  is_active: boolean
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

export const signup = (data: { email: string; password: string; full_name: string; company_name?: string }) =>
  api.post<TokenResponse>('/auth/signup', data)

export const login = (data: { email: string; password: string }) =>
  api.post<TokenResponse>('/auth/login', data)

export const getMe = () => api.get<User>('/auth/me')

export const createSite = (data: Partial<Site>) => api.post<Site>('/sites/', data)
export const listSites = () => api.get<Site[]>('/sites/')
export const deleteSite = (id: string) => api.delete(`/sites/${id}`)

export const uploadCSV = (siteId: string, file: File) => {
  const form = new FormData()
  form.append('file', file)
  return api.post(`/sites/${siteId}/upload`, form)
}

export const getForecast = (siteId: string, horizon = 24) =>
  api.get(`/api/forecast/${siteId}`, { params: { horizon } })

export const getRisk = (siteId: string, horizon = 24) =>
  api.get(`/api/risk/${siteId}`, { params: { horizon } })

export const getOptimize = (siteId: string, horizon = 24) =>
  api.get(`/api/optimize/${siteId}`, { params: { horizon } })

export const getExplain = (siteId: string) =>
  api.get(`/api/explain/${siteId}`)

export const runScenario = (siteId: string, params: {
  cloud_cover_delta?: number
  wind_speed_delta?: number
  battery_soc_override?: number
}) => api.post(`/api/scenario/${siteId}`, params)

export const getDataStatus = (siteId: string) =>
  api.get(`/api/data/status/${siteId}`)

export const syncWeatherData = (siteId: string) =>
  api.post(`/api/data/sync/${siteId}`)

export const importCSV = (siteId: string, file: File) => {
  const form = new FormData()
  form.append('file', file)
  return api.post(`/api/data/import/${siteId}`, form)
}

// ─── Chat / Sessions ─────────────────────────────────────────
export interface ChatSession {
  id: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

export interface ChatResponse {
  session_id: string
  message: ChatMessage
  thinking?: string
}

export const createChatSession = (title?: string) =>
  api.post<ChatSession>('/api/chat/sessions', { title })

export const listChatSessions = () =>
  api.get<ChatSession[]>('/api/chat/sessions')

export const getChatSession = (sessionId: string) =>
  api.get<{ id: string; title: string; messages: ChatMessage[] }>(`/api/chat/sessions/${sessionId}`)

export const sendChatMessage = (sessionId: string, message: string, options?: { search?: boolean; deep_research?: boolean; reason?: boolean; site_id?: string }) =>
  api.post<ChatResponse>(`/api/chat/sessions/${sessionId}/chat`, { message, ...options })

export const deleteChatSession = (sessionId: string) =>
  api.delete(`/api/chat/sessions/${sessionId}`)

export interface AccuracySeries {
  horizon_hours: number
  MAE: number
  RMSE: number
  'MAPE_%': number
  R2: number
  'rel_%': number
}

export interface ForecastAccuracy {
  site_id: string
  capacity_kw: number
  overall: {
    MAE: number
    RMSE: number
    'MAPE_%': number
    R2: number
    'reliability_%': number
  }
  horizons: AccuracySeries[]
}

export interface AlertItem {
  id: string
  severity: 'critical' | 'warning' | 'info'
  type: string
  title: string
  detail: string
  time: string
  channels: string[]
}

export interface ModelHealth {
  model_name: string
  version: string
  algorithm: string
  mae_mw: number
  data_drift: 'LOW' | 'MEDIUM' | 'HIGH'
  model_drift: 'LOW' | 'MEDIUM' | 'HIGH'
  last_trained: string
  hours_since_training: number
  feature_version: string
  status: 'HEALTHY' | 'ATTENTION'
}

export interface WeatherInsights {
  site_id: string
  source: string
  primary_driver: string
  weather: {
    max_cloud_cover: number
    peak_temperature: number
    avg_wind_speed: number
  }
  impact: {
    'irradiance_reduction_%': number
    'temperature_derating_%': number
    'wind_boost_%': number
    'generation_reduction_kw': number
  }
  drivers: { key: string; label: string; level: string; value: string }[]
  data: {
    'quality_%': number
    records: number
    high_severity_anomalies: number
    last_updated_minutes_ago: number | null
    stale: boolean
  }
}

export const getForecastAccuracy = (siteId: string) =>
  api.get<ForecastAccuracy>(`/api/insights/${siteId}/accuracy`)

export const getModelHealth = () =>
  api.get<ModelHealth>('/api/insights/model')

export const getAlerts = () =>
  api.get<{ alerts: AlertItem[] }>('/api/alerts')

export const getWeatherInsights = (siteId: string) =>
  api.get<WeatherInsights>(`/api/insights/${siteId}/weather`)

export default api
