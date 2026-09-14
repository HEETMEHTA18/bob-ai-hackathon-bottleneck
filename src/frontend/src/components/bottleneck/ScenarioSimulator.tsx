/**
 * Bottleneck — Scenario Simulator
 * Uses existing CSS design system.
 */
import React, { useState } from 'react'
import { gsSimulateScenario, type GSScenarioResult } from '../../api/bottleneck'
import { riskBadgeClass, riskTextColor, riskBarColor, RED, AMBER, GREEN, ACCENT, MUTED } from './utils'
import { CloudLightning, Thermometer, Wrench, Truck, ArrowUp, ChevronRight } from 'lucide-react'

interface Props { onSelectAsset: (id: string) => void }

const SCENARIOS = [
  {
    id: 'severe_storm', label: 'Severe Storm',
    description: 'Increases weather exposure, wind, precipitation and storm severity across all degraded assets.',
    Icon: CloudLightning, borderColor: '#1a73e8', bgColor: '#e8f0fe',
  },
  {
    id: 'heatwave', label: 'Heatwave',
    description: 'Elevates ambient temperature and thermal stress -- critical for transformers.',
    Icon: Thermometer, borderColor: RED, bgColor: '#fce8e6',
  },
  {
    id: 'asset_degradation', label: 'Asset Degradation',
    description: 'Simulates accelerated wear -- increases vibration, anomaly score, and failure probability.',
    Icon: Wrench, borderColor: AMBER, bgColor: '#fef7e0',
  },
]

export default function ScenarioSimulator({ onSelectAsset }: Props) {
  const [selected, setSelected] = useState<string | null>(null)
  const [results, setResults]   = useState<GSScenarioResult[] | null>(null)
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState<string | null>(null)

  async function run(scenario: string) {
    setSelected(scenario); setLoading(true); setError(null); setResults(null)
    try {
      const r = await gsSimulateScenario(scenario)
      setResults(r.data.results)
    } catch (e: any) { setError(e.message || 'Simulation failed') }
    finally { setLoading(false) }
  }

  return (
    <div className="animate-fadeIn">
      <div className="page-header">
        <div className="page-title">Scenario Simulator</div>
        <div className="page-subtitle">
          What-if analysis — see how conditions affect risk rankings, maintenance priorities, and crew pre-positioning.
        </div>
      </div>

      {/* Scenario cards */}
      <div className="grid-3" style={{ marginBottom: 28 }}>
        {SCENARIOS.map(s => (
          <div
            key={s.id}
            onClick={() => !loading && run(s.id)}
            className="card"
            style={{
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading && selected !== s.id ? 0.55 : 1,
              borderLeft: `4px solid ${selected === s.id ? s.borderColor : '#e0e0e0'}`,
              background: selected === s.id ? s.bgColor : 'white',
              transition: 'all 0.15s',
            }}
          >
            <div style={{ marginBottom: 10 }}><s.Icon size={32} color={s.borderColor} /></div>
            <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 6, color: '#202124' }}>{s.label}</div>
            <div className="text-sm text-muted">{s.description}</div>
          </div>
        ))}
      </div>

      {loading && (
        <div className="empty-state" style={{ padding: 32 }}>
          <div className="empty-title">Running {SCENARIOS.find(s => s.id === selected)?.label} scenario…</div>
          <div className="empty-desc">Computing risk changes across fleet</div>
        </div>
      )}

      {error && (
        <div className="card" style={{ borderLeft: `4px solid ${RED}` }}>
          <p className="text-sm" style={{ color: RED }}>{error}</p>
        </div>
      )}

      {results && results.length > 0 && (
        <div>
          <div className="page-subtitle" style={{ marginBottom: 16 }}>
            {(() => { const s = SCENARIOS.find(s => s.id === selected); return s ? <s.Icon size={16} color={s.borderColor} style={{ display: 'inline', verticalAlign: 'middle', marginRight: 6 }} /> : null })()}
            {SCENARIOS.find(s => s.id === selected)?.label} -- Impact on {results.length} assets
            <span style={{ marginLeft: 12, fontSize: 12, color: MUTED }}>Sorted by risk increase</span>
          </div>

          {results.map(r => {
            const delta = r.risk_after - r.risk_before
            const escalated = r.risk_level_after !== r.risk_level_before
            return (
              <div
                key={r.asset_id}
                className="card"
                style={{
                  cursor: 'pointer',
                  borderLeft: `4px solid ${delta > 5 ? RED : delta > 0 ? AMBER : GREEN}`,
                }}
                onClick={() => onSelectAsset(r.asset_id)}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', gap: 8, marginBottom: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                      <span style={{ fontWeight: 700, fontSize: 15, color: '#202124' }}>{r.asset_id}</span>
                      {escalated && <span className="badge badge-red"><ArrowUp className="h-3 w-3 inline-block align-middle mr-1" />ESCALATED</span>}
                      {r.crew_assigned && <span className="badge badge-default"><Truck className="h-3 w-3 inline-block align-middle mr-1" />{r.crew_assigned}</span>}
                    </div>
                    <p className="text-sm text-muted">{r.description}</p>
                  </div>

                  {/* Before → After comparison */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexShrink: 0 }}>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 12, color: MUTED, marginBottom: 4 }}>Before</div>
                      <div style={{ width: 72, background: '#e8eaed', borderRadius: 5, height: 8, overflow: 'hidden', marginBottom: 4 }}>
                        <div style={{ width: `${Math.min(100, r.risk_before)}%`, background: riskBarColor(r.risk_before), height: '100%', borderRadius: 5 }} />
                      </div>
                      <div style={{ fontWeight: 700, fontSize: 18, color: riskTextColor(r.risk_level_before) }}>{r.risk_before.toFixed(0)}</div>
                      <span className={riskBadgeClass(r.risk_level_before)} style={{ fontSize: 10 }}>{r.risk_level_before}</span>
                    </div>

                    <div style={{ fontSize: 20, color: MUTED }}><ChevronRight className="h-5 w-5" /></div>

                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 12, color: MUTED, marginBottom: 4 }}>After</div>
                      <div style={{ width: 72, background: '#e8eaed', borderRadius: 5, height: 8, overflow: 'hidden', marginBottom: 4 }}>
                        <div style={{ width: `${Math.min(100, r.risk_after)}%`, background: riskBarColor(r.risk_after), height: '100%', borderRadius: 5 }} />
                      </div>
                      <div style={{ fontWeight: 700, fontSize: 18, color: riskTextColor(r.risk_level_after) }}>{r.risk_after.toFixed(0)}</div>
                      <span className={riskBadgeClass(r.risk_level_after)} style={{ fontSize: 10 }}>{r.risk_level_after}</span>
                    </div>

                    <div style={{ fontWeight: 800, fontSize: 16, color: delta > 0 ? RED : GREEN, minWidth: 40, textAlign: 'right' }}>
                      {delta > 0 ? '+' : ''}{delta.toFixed(1)}
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
