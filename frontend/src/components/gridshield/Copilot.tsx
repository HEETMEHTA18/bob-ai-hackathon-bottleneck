/**
 * GridShield — AI Advisor
 * ChatGPT-style interface with chat history sidebar, collapse, and clean layout.
 */
import { useState, useRef, useEffect, useCallback } from 'react'
import { gsChat } from '../../api/gridshield'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {
  Send, Bot, User, Loader2, Plus, MessageSquare, PanelLeftClose,
  PanelLeftOpen, Trash2, Clock,
} from 'lucide-react'

/* ─── Chat history persistence ─────────────────────────────────────────────── */

interface ChatMsg { role: 'user' | 'assistant'; content: string }
interface ChatSession {
  id: string
  title: string
  messages: ChatMsg[]
  createdAt: number
}

const STORAGE_KEY = 'gridshield_chat_history'
const MAX_SESSIONS = 50

function loadSessions(): ChatSession[] {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
  } catch { return [] }
}
function saveSessions(sessions: ChatSession[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions.slice(0, MAX_SESSIONS)))
}
function makeTitle(msg: string): string {
  return msg.length > 40 ? msg.slice(0, 40) + '...' : msg
}

/* ─── Suggested questions ──────────────────────────────────────────────────── */

const SUGGESTIONS = [
  { q: 'Why is TR-1042 critical?', desc: 'Deep-dive into the highest-risk asset' },
  { q: 'Will there be a power outage?', desc: 'Outage risk assessment with customer impact' },
  { q: 'What are the top 5 risk assets?', desc: 'Ranked summary of critical equipment' },
  { q: 'Compare TR-1042 and BR-2201', desc: 'Side-by-side asset comparison' },
  { q: 'How does the storm affect North?', desc: 'Weather exposure for a specific region' },
  { q: 'What happens if a severe storm hits?', desc: 'What-if scenario simulation' },
]

/* ─── Component ────────────────────────────────────────────────────────────── */

export default function GridShieldCopilot() {
  const [sessions, setSessions] = useState<ChatSession[]>(loadSessions)
  const [activeId, setActiveId] = useState<string | null>(null)
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const active = sessions.find(s => s.id === activeId) || null
  const messages: ChatMsg[] = active?.messages || []

  const persist = useCallback((next: ChatSession[]) => {
    setSessions(next)
    saveSessions(next)
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  useEffect(() => {
    if (!loading) inputRef.current?.focus()
  }, [loading])

  /* ── Session management ────────────────────────────────────────────── */

  function newChat() {
    setActiveId(null)
    setInput('')
    inputRef.current?.focus()
  }

  function selectSession(id: string) {
    setActiveId(id)
    setInput('')
  }

  function deleteSession(id: string) {
    const next = sessions.filter(s => s.id !== id)
    persist(next)
    if (activeId === id) setActiveId(null)
  }

  /* ── Send message ──────────────────────────────────────────────────── */

  async function send(text: string) {
    if (!text.trim() || loading) return
    const msg = text.trim()
    setInput('')

    let sessionId: string
    let currentMessages: ChatMsg[]

    if (active) {
      sessionId = active.id
      currentMessages = [...active.messages, { role: 'user', content: msg }]
      const next = sessions.map(s => s.id === active.id
        ? { ...s, messages: currentMessages, title: s.messages.length === 0 ? makeTitle(msg) : s.title }
        : s)
      persist(next)
    } else {
      const newId = Date.now().toString(36) + Math.random().toString(36).slice(2, 6)
      sessionId = newId
      currentMessages = [{ role: 'user', content: msg }]
      const session: ChatSession = {
        id: newId, title: makeTitle(msg), messages: currentMessages, createdAt: Date.now(),
      }
      persist([session, ...sessions])
      setActiveId(newId)
    }

    setLoading(true)
    try {
      const r = await gsChat(msg, sessionId)
      const assistantMsg: ChatMsg = { role: 'assistant', content: r.data.response }
      const updatedMessages = [...currentMessages, assistantMsg]
      const next = loadSessions().map(s =>
        s.id === sessionId ? { ...s, messages: updatedMessages } : s
      )
      persist(next)
    } catch {
      const errorMsg: ChatMsg = { role: 'assistant', content: '**Error:** Unable to connect to the server. Please try again later.' }
      const next = loadSessions().map(s =>
        s.id === sessionId ? { ...s, messages: [...s.messages, errorMsg] } : s
      )
      persist(next)
    } finally {
      setLoading(false)
    }
  }

  /* ── Render ────────────────────────────────────────────────────────── */

  return (
    <div style={{ display: 'flex', height: '100%', overflow: 'hidden', borderRadius: 12, border: '1px solid #e5e7eb', background: '#ffffff' }}>

      {/* ── Sidebar ──────────────────────────────────────────────────── */}
      <div style={{
        width: sidebarOpen ? 260 : 0, minWidth: sidebarOpen ? 260 : 0,
        transition: 'all 0.2s ease', overflow: 'hidden',
        background: '#f9fafb', borderRight: sidebarOpen ? '1px solid #e5e7eb' : 'none',
        display: 'flex', flexDirection: 'column',
      }}>
        <div style={{ padding: '12px 12px 8px', display: 'flex', flexDirection: 'column', gap: 8 }}>
          <button
            onClick={newChat}
            style={{
              width: '100%', padding: '10px 12px', borderRadius: 8, fontSize: 13, fontWeight: 500,
              background: '#ffffff', border: '1px solid #d1d5db', color: '#374151',
              cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8,
              transition: 'all 0.15s',
            }}
            onMouseEnter={e => { e.currentTarget.style.background = '#f3f4f6' }}
            onMouseLeave={e => { e.currentTarget.style.background = '#ffffff' }}
          >
            <Plus size={15} /> New Chat
          </button>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '0 8px 8px' }}>
          {sessions.length === 0 && (
            <div style={{ padding: '24px 12px', textAlign: 'center', color: '#9ca3af', fontSize: 12 }}>
              No previous chats
            </div>
          )}
          {sessions.map(s => (
            <div
              key={s.id}
              onClick={() => selectSession(s.id)}
              style={{
                padding: '8px 10px', borderRadius: 8, cursor: 'pointer', marginBottom: 2,
                background: s.id === activeId ? '#e0e7ff' : 'transparent',
                display: 'flex', alignItems: 'center', gap: 8,
                transition: 'background 0.1s',
              }}
              onMouseEnter={e => { if (s.id !== activeId) e.currentTarget.style.background = '#f3f4f6' }}
              onMouseLeave={e => { if (s.id !== activeId) e.currentTarget.style.background = 'transparent' }}
            >
              <MessageSquare size={14} color={s.id === activeId ? '#4338ca' : '#9ca3af'} style={{ flexShrink: 0 }} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{
                  fontSize: 13, fontWeight: s.id === activeId ? 500 : 400,
                  color: s.id === activeId ? '#1e1b4b' : '#374151',
                  overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                }}>
                  {s.title}
                </div>
                <div style={{ fontSize: 11, color: '#9ca3af', display: 'flex', alignItems: 'center', gap: 4, marginTop: 2 }}>
                  <Clock size={10} />
                  {new Date(s.createdAt).toLocaleDateString()}
                </div>
              </div>
              <button
                onClick={e => { e.stopPropagation(); deleteSession(s.id) }}
                style={{
                  padding: 4, borderRadius: 4, border: 'none', background: 'transparent',
                  color: '#9ca3af', cursor: 'pointer', opacity: 0.5, transition: 'opacity 0.15s',
                }}
                onMouseEnter={e => { e.currentTarget.style.opacity = '1'; e.currentTarget.style.color = '#ef4444' }}
                onMouseLeave={e => { e.currentTarget.style.opacity = '0.5'; e.currentTarget.style.color = '#9ca3af' }}
              >
                <Trash2 size={13} />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* ── Main chat area ───────────────────────────────────────────── */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>

        {/* Top bar */}
        <div style={{
          padding: '10px 16px', borderBottom: '1px solid #e5e7eb',
          display: 'flex', alignItems: 'center', gap: 10, background: '#ffffff',
        }}>
          <button
            onClick={() => setSidebarOpen(o => !o)}
            style={{
              padding: 6, borderRadius: 6, border: 'none', background: 'transparent',
              color: '#6b7280', cursor: 'pointer', display: 'flex', alignItems: 'center',
            }}
            title={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
          >
            {sidebarOpen ? <PanelLeftClose size={18} /> : <PanelLeftOpen size={18} />}
          </button>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{
              width: 28, height: 28, borderRadius: 7, background: '#e0e7ff',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Bot size={15} color="#4338ca" />
            </div>
            <div>
              <div style={{ fontWeight: 600, fontSize: 14, color: '#111827', lineHeight: 1.2 }}>Bottleneck AI</div>
              <div style={{ fontSize: 11, color: '#6b7280' }}>Power Outage Prediction Advisor</div>
            </div>
          </div>
          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#22c55e', display: 'inline-block' }} />
            <span style={{ fontSize: 11, color: '#6b7280' }}>Online</span>
          </div>
        </div>

        {/* Messages or empty state */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '0' }}>
          {messages.length === 0 ? (
            /* ── Empty state: suggested questions ────────────────────── */
            <div style={{
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
              height: '100%', padding: 40, maxWidth: 680, margin: '0 auto',
            }}>
              <div style={{
                width: 52, height: 52, borderRadius: 14, background: '#e0e7ff',
                display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 16,
              }}>
                <Bot size={28} color="#4338ca" />
              </div>
              <div style={{ fontSize: 22, fontWeight: 700, color: '#111827', marginBottom: 6 }}>
                Bottleneck AI
              </div>
              <div style={{ fontSize: 14, color: '#6b7280', textAlign: 'center', marginBottom: 32, lineHeight: 1.6, maxWidth: 480 }}>
                Grid operations intelligence grounded in live telemetry. Ask about any asset, risk, maintenance plan, or crew assignment.
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, width: '100%' }}>
                {SUGGESTIONS.map(({ q, desc }) => (
                  <button
                    key={q}
                    onClick={() => send(q)}
                    disabled={loading}
                    style={{
                      padding: '12px 14px', borderRadius: 10, fontSize: 13, textAlign: 'left',
                      background: '#f9fafb', border: '1px solid #e5e7eb', color: '#374151',
                      cursor: loading ? 'not-allowed' : 'pointer', transition: 'all 0.15s',
                    }}
                    onMouseEnter={e => { e.currentTarget.style.background = '#f3f4f6'; e.currentTarget.style.borderColor = '#d1d5db' }}
                    onMouseLeave={e => { e.currentTarget.style.background = '#f9fafb'; e.currentTarget.style.borderColor = '#e5e7eb' }}
                  >
                    <div style={{ fontWeight: 500, marginBottom: 2 }}>{q}</div>
                    <div style={{ fontSize: 11, color: '#9ca3af' }}>{desc}</div>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            /* ── Messages ────────────────────────────────────────────── */
            <div style={{ maxWidth: 780, margin: '0 auto', padding: '20px 24px' }}>
              {messages.map((msg, i) => (
                <div key={i} style={{
                  display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  marginBottom: 20,
                }}>
                  {msg.role === 'assistant' && (
                    <div style={{
                      width: 32, height: 32, borderRadius: 8, background: '#e0e7ff',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      flexShrink: 0, marginRight: 12, marginTop: 2,
                    }}>
                      <Bot size={16} color="#4338ca" />
                    </div>
                  )}
                  <div style={{
                    maxWidth: '80%', padding: '12px 16px', borderRadius: msg.role === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
                    fontSize: 14, lineHeight: 1.65,
                    background: msg.role === 'user' ? '#4338ca' : '#f3f4f6',
                    color: msg.role === 'user' ? '#ffffff' : '#1f2937',
                  }}>
                    {msg.role === 'assistant' ? (
                      <div className="prose" style={{ fontSize: 14 }}>
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                      </div>
                    ) : (
                      <span>{msg.content}</span>
                    )}
                  </div>
                  {msg.role === 'user' && (
                    <div style={{
                      width: 32, height: 32, borderRadius: 8, background: '#4338ca',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      flexShrink: 0, marginLeft: 12, marginTop: 2,
                    }}>
                      <User size={16} color="#ffffff" />
                    </div>
                  )}
                </div>
              ))}

              {loading && (
                <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: 20 }}>
                  <div style={{
                    width: 32, height: 32, borderRadius: 8, background: '#e0e7ff',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    flexShrink: 0, marginRight: 12,
                  }}>
                    <Bot size={16} color="#4338ca" />
                  </div>
                  <div style={{
                    background: '#f3f4f6', borderRadius: '16px 16px 16px 4px',
                    padding: '12px 16px', fontSize: 13, color: '#6b7280',
                    display: 'flex', alignItems: 'center', gap: 8,
                  }}>
                    <Loader2 size={14} className="animate-spin" />
                    <span>Analyzing grid data...</span>
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        {/* Input bar */}
        <div style={{ borderTop: '1px solid #e5e7eb', padding: '12px 16px', background: '#ffffff' }}>
          <div style={{ maxWidth: 780, margin: '0 auto', display: 'flex', gap: 10, alignItems: 'flex-end' }}>
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send(input)}
              placeholder="Ask about any asset, risk, maintenance, or crew..."
              disabled={loading}
              style={{
                flex: 1, padding: '12px 16px', borderRadius: 12,
                border: '1px solid #d1d5db', fontSize: 14, color: '#111827',
                outline: 'none', background: '#ffffff', resize: 'none',
              }}
              onFocus={e => { e.currentTarget.style.borderColor = '#4338ca'; e.currentTarget.style.boxShadow = '0 0 0 3px rgba(67,56,202,0.1)' }}
              onBlur={e => { e.currentTarget.style.borderColor = '#d1d5db'; e.currentTarget.style.boxShadow = 'none' }}
            />
            <button
              onClick={() => send(input)}
              disabled={loading || !input.trim()}
              style={{
                width: 42, height: 42, borderRadius: 10,
                background: loading || !input.trim() ? '#e5e7eb' : '#4338ca',
                color: loading || !input.trim() ? '#9ca3af' : '#ffffff',
                border: 'none', cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                transition: 'all 0.15s', flexShrink: 0,
              }}
            >
              <Send size={17} />
            </button>
          </div>
          <div style={{ maxWidth: 780, margin: '6px auto 0', fontSize: 11, color: '#9ca3af', textAlign: 'center' }}>
            Bottleneck AI — Power outage prediction · Data grounded in live backend telemetry
          </div>
        </div>
      </div>
    </div>
  )
}
