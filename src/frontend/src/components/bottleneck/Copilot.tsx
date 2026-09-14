/**
 * Bottleneck — AI Copilot Chat
 * Uses existing CSS design system and .prose markdown styles.
 */
import React, { useState, useRef, useEffect } from 'react'
import { gsChat } from '../../api/bottleneck'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { ACCENT, MUTED, RED } from './utils'

const SUGGESTIONS = [
  'Why is TR-1042 critical?',
  'What action is needed for TR-1042?',
  'What are the top 5 highest risk assets?',
  'How does the storm affect North region?',
  'Which crew is assigned to the most critical asset?',
  'What happens if a severe heatwave hits?',
]

export default function BottleneckCopilot() {
  const [messages, setMessages] = useState<{ role: 'user' | 'assistant'; content: string }[]>([{
    role: 'assistant',
    content: "### Bottleneck AI — Grid Operations Advisor\n\nI'm grounded in live backend data. Ask me about any asset, risk, maintenance plan, or crew assignment.\n\nI never invent sensor values or statistics — all answers are based on actual telemetry and predictions.",
  }])
  const [input, setInput]       = useState('')
  const [loading, setLoading]   = useState(false)
  const [sessionId, setSessionId] = useState<string | undefined>()
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function send(text: string) {
    if (!text.trim() || loading) return
    const msg = text.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: msg }])
    setLoading(true)
    try {
      const r = await gsChat(msg, sessionId)
      setSessionId(r.data.session_id)
      setMessages(prev => [...prev, { role: 'assistant', content: r.data.response }])
    } catch (e: any) {
      setMessages(prev => [...prev, { role: 'assistant', content: `**Error:** ${e.message}. Check that the backend is running on port 8000.` }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 140px)', minHeight: 500 }}>
      <div style={{ marginBottom: 16 }}>
        <div className="page-title">Bottleneck AI Copilot</div>
        <div className="page-subtitle">Grounded Grid Operations Advisor — all answers backed by backend data</div>
      </div>

      {/* Suggested questions */}
      {messages.length <= 1 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
          {SUGGESTIONS.map(q => (
            <button key={q} className="btn btn-secondary btn-sm" onClick={() => send(q)}>{q}</button>
          ))}
        </div>
      )}

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 16, paddingRight: 4 }}>
        {messages.map((msg, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
            <div style={{
              maxWidth: '75%',
              borderRadius: 12,
              padding: '12px 16px',
              fontSize: 14,
              lineHeight: 1.6,
              background: msg.role === 'user' ? ACCENT : 'white',
              color: msg.role === 'user' ? 'white' : '#202124',
              border: msg.role === 'user' ? 'none' : '1px solid #e0e0e0',
              boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
            }}>
              {msg.role === 'assistant' ? (
                <div className="prose">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                </div>
              ) : (
                <p>{msg.content}</p>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
            <div style={{ background: 'white', border: '1px solid #e0e0e0', borderRadius: 12, padding: '12px 16px', fontSize: 14, color: MUTED, display: 'flex', alignItems: 'center', gap: 8 }}>
              <span>Analysing grid data</span>
              <span style={{ display: 'flex', gap: 4 }}>
                {[0, 1, 2].map(i => (
                  <span key={i} style={{ width: 6, height: 6, borderRadius: '50%', background: ACCENT, display: 'inline-block', animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite` }} />
                ))}
              </span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div style={{ marginTop: 16, display: 'flex', gap: 10 }}>
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send(input)}
          placeholder="Ask about any asset, risk, maintenance, or crew…"
          disabled={loading}
          className="input"
          style={{ flex: 1 }}
        />
        <button
          onClick={() => send(input)}
          disabled={loading || !input.trim()}
          className="btn btn-primary"
          style={{ opacity: loading || !input.trim() ? 0.5 : 1 }}
        >
          Send
        </button>
      </div>

      <style>{`@keyframes bounce { 0%,80%,100% { transform: scale(0.6); } 40% { transform: scale(1); } }`}</style>
    </div>
  )
}
