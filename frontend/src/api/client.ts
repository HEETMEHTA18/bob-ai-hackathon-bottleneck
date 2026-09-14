import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || ''

const api = axios.create({
  baseURL: API_BASE,
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
          const res = await axios.post(`${API_BASE}/auth/refresh`, { refresh_token: refreshToken })
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

// ─── Auth ─────────────────────────────────────────────────────
export interface User {
  id: string
  email: string
  full_name: string
  company_name?: string
  role: string
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

export default api
