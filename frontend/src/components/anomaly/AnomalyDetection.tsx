import { useState, useEffect } from 'react'
import { useSiteContext } from '../../context/SiteContext'
import { Card, Badge, KPICard, LoadingSkeleton, Button } from '../common/LoadingSkeleton'

interface Anomaly {
  id: string
  timestamp: string
  type: 'spike' | 'drop' | 'gap' | 'zero_output' | 'negative' | 'sensor_drift'
  severity: 'high' | 'medium' | 'low'
  metric: string
  value: number
  expected: number
  description: string
  auto_fixed: boolean
}

function generateMockAnomalies(): Anomaly[] {
  return [
    { id: '1', timestamp: '2024-01-15 14:00', type: 'spike', severity: 'high', metric: 'generation_kw', value: 145, expected: 95, description: 'Generation spike +52% above capacity', auto_fixed: false },
    { id: '2', timestamp: '2024-01-15 08:30', type: 'drop', severity: 'medium', metric: 'generation_kw', value: 5, expected: 45, description: 'Sudden generation drop during peak hours', auto_fixed: true },
    { id: '3', timestamp: '2024-01-14 22:00', type: 'gap', severity: 'low', metric: 'ghi', value: 0, expected: 0, description: 'Missing weather data for 3 hours', auto_fixed: true },
    { id: '4', timestamp: '2024-01-14 11:00', type: 'zero_output', severity: 'high', metric: 'generation_kw', value: 0, expected: 85, description: 'Zero generation despite high irradiance', auto_fixed: false },
    { id: '5', timestamp: '2024-01-14 16:00', type: 'sensor_drift', severity: 'medium', metric: 'temperature', value: 42, expected: 32, description: 'Temperature sensor showing 10°C drift', auto_fixed: true },
  ]
}

const ANOMALY_CONFIG: Record<string, { icon: string; color: string; label: string }> = {
  spike: { icon: '📈', color: 'var(--red)', label: 'Value Spike' },
  drop: { icon: '📉', color: 'var(--amber)', label: 'Sudden Drop' },
  gap: { icon: '🔗', color: 'var(--text-muted)', label: 'Data Gap' },
  zero_output: { icon: '⚡', color: 'var(--red)', label: 'Zero Output' },
  negative: { icon: '➖', color: 'var(--amber)', label: 'Negative Value' },
  sensor_drift: { icon: '🌡️', color: 'var(--purple)', label: 'Sensor Drift' },
}

export function AnomalyDetectionPage() {
  const { activeSite } = useSiteContext()
  const [anomalies, setAnomalies] = useState<Anomaly[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<string>('all')

  useEffect(() => {
    setLoading(true)
    setTimeout(() => {
      setAnomalies(generateMockAnomalies())
      setLoading(false)
    }, 500)
  }, [activeSite])

  const filtered = filter === 'all' ? anomalies : anomalies.filter(a => a.severity === filter)
  const highCount = anomalies.filter(a => a.severity === 'high').length
  const medCount = anomalies.filter(a => a.severity === 'medium').length
  const lowCount = anomalies.filter(a => a.severity === 'low').length

  return (
    <div className="space-y-6 animate-fadeIn">
      <div>
        <h2 className="text-xl font-bold tracking-tight" style={{ color: 'var(--text-primary)' }}>Anomaly Detection</h2>
        <p className="text-sm mt-0.5" style={{ color: 'var(--text-muted)' }}>Real-time data quality monitoring and automatic corrections</p>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <KPICard label="Total Anomalies" value={String(anomalies.length)} icon={<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>} />
        <KPICard label="High Severity" value={String(highCount)} icon={<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/></svg>} trend="down" />
        <KPICard label="Auto-Fixed" value={String(anomalies.filter(a => a.auto_fixed).length)} icon={<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="20 6 9 17 4 12"/></svg>} />
        <KPICard label="Data Quality" value="94.2%" icon={<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>} trend="up" trendValue="+2.1%" />
      </div>

      <Card>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>Detected Anomalies</h3>
          <div className="flex gap-2">
            {['all', 'high', 'medium', 'low'].map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className="px-3 py-1 rounded-md text-xs font-medium transition-all capitalize"
                style={{
                  background: filter === f ? 'var(--accent-light)' : 'var(--bg-tertiary)',
                  color: filter === f ? 'var(--accent)' : 'var(--text-muted)',
                }}
              >
                {f} {f !== 'all' && `(${f === 'high' ? highCount : f === 'medium' ? medCount : lowCount})`}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <LoadingSkeleton rows={5} />
        ) : (
          <div className="space-y-2">
            {filtered.map(anomaly => (
              <div
                key={anomaly.id}
                className="flex items-center gap-4 p-3 rounded-lg border transition-colors hover:bg-gray-50"
                style={{ borderColor: 'var(--border)' }}
              >
                <span className="text-xl">{ANOMALY_CONFIG[anomaly.type]?.icon}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                      {ANOMALY_CONFIG[anomaly.type]?.label}
                    </p>
                    <Badge variant={anomaly.severity === 'high' ? 'red' : anomaly.severity === 'medium' ? 'amber' : 'default'}>
                      {anomaly.severity}
                    </Badge>
                    {anomaly.auto_fixed && <Badge variant="green">Auto-fixed</Badge>}
                  </div>
                  <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>{anomaly.description}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs font-medium" style={{ color: 'var(--text-muted)' }}>{anomaly.timestamp}</p>
                  <p className="text-xs mt-0.5">
                    <span style={{ color: 'var(--text-muted)' }}>Expected: </span>
                    <span className="font-medium">{anomaly.expected}</span>
                    <span style={{ color: 'var(--text-muted)' }}> | Got: </span>
                    <span className="font-medium" style={{ color: anomaly.value > anomaly.expected * 1.2 ? 'var(--red)' : 'var(--text-primary)' }}>{anomaly.value}</span>
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      <Card>
        <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>Detection Methods</h3>
        <div className="grid grid-cols-3 gap-3">
          {[
            { name: 'Statistical (Z-score)', desc: 'Detects values beyond 3σ from rolling mean', status: 'Active' },
            { name: 'IQR Method', desc: 'Interquartile range for outlier detection', status: 'Active' },
            { name: 'Isolation Forest', desc: 'ML-based multivariate anomaly detection', status: 'Ready' },
          ].map((method, i) => (
            <div key={i} className="p-3 rounded-lg" style={{ background: 'var(--bg-tertiary)' }}>
              <div className="flex items-center justify-between mb-1">
                <p className="text-xs font-semibold" style={{ color: 'var(--text-primary)' }}>{method.name}</p>
                <Badge variant="green">{method.status}</Badge>
              </div>
              <p className="text-[11px]" style={{ color: 'var(--text-muted)' }}>{method.desc}</p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
