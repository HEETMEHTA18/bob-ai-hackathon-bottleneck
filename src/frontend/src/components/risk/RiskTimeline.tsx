import { useRisk } from '../../hooks/useRisk'
import { useSiteContext } from '../../context/SiteContext'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { Card, LoadingSkeleton, Badge } from '../common/LoadingSkeleton'

const RISK_CONFIG: Record<string, string> = {
  LOW: 'var(--green)',
  MEDIUM: 'var(--amber)',
  HIGH: 'var(--red)',
}

const CustomTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.[0]) return null
  const d = payload[0].payload
  return (
    <div className="rounded-lg border p-3 shadow-lg" style={{ background: 'white', borderColor: 'var(--border)' }}>
      <p className="text-xs font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>Hour {d.hour}</p>
      <div className="flex items-center gap-2 text-xs">
        <div className="w-2 h-2 rounded-full" style={{ background: RISK_CONFIG[d.riskLabel] }} />
        <span style={{ color: 'var(--text-muted)' }}>Risk:</span>
        <span className="font-semibold" style={{ color: RISK_CONFIG[d.riskLabel] }}>{d.riskLabel}</span>
      </div>
      <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>Action: {d.action.replace(/_/g, ' ')}</p>
    </div>
  )
}

export function RiskTimeline({ horizon = 24 }: { horizon?: number }) {
  const { activeSite } = useSiteContext()
  const { risks, loading, error } = useRisk(activeSite?.id || null, horizon)

  if (loading) return <Card><LoadingSkeleton rows={3} /></Card>
  if (error) return <Card><p className="text-sm" style={{ color: 'var(--red)' }}>Error loading risk data</p></Card>
  if (!risks.length) return null

  const highCount = risks.filter(r => r.risk === 'HIGH').length
  const medCount = risks.filter(r => r.risk === 'MEDIUM').length

  const chartData = risks.map(r => ({
    hour: r.hour,
    risk: r.risk === 'HIGH' ? 3 : r.risk === 'MEDIUM' ? 2 : 1,
    riskLabel: r.risk,
    action: r.action,
  }))

  return (
    <Card>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>Risk Timeline</h3>
          <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>{horizon}h risk distribution</p>
        </div>
        <div className="flex gap-1.5">
          {highCount > 0 && <Badge variant="red">{highCount} HIGH</Badge>}
          {medCount > 0 && <Badge variant="amber">{medCount} MED</Badge>}
          <Badge variant="green">{risks.length - highCount - medCount} LOW</Badge>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={140}>
        <BarChart data={chartData} margin={{ top: 5, right: 5, left: 0, bottom: 5 }}>
          <XAxis dataKey="hour" tick={{ fontSize: 9, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
          <YAxis hide domain={[0, 4]} />
          <Tooltip content={<CustomTooltip />} cursor={false} />
          <Bar dataKey="risk" radius={[3, 3, 0, 0]} maxBarSize={18}>
            {chartData.map((entry, i) => (
              <Cell key={i} fill={RISK_CONFIG[entry.riskLabel]} fillOpacity={0.85} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </Card>
  )
}
