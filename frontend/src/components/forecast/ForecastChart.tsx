import { useForecast } from '../../hooks/useForecast'
import { useSiteContext } from '../../context/SiteContext'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ComposedChart, Line } from 'recharts'
import { Card, LoadingSkeleton } from '../common/LoadingSkeleton'

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload) return null
  return (
    <div className="rounded-lg border p-3 shadow-lg" style={{ background: 'white', borderColor: 'var(--border)' }}>
      <p className="text-xs font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>{label}</p>
      {payload.map((p: any, i: number) => (
        <div key={i} className="flex items-center gap-2 text-xs">
          <div className="w-2 h-2 rounded-full" style={{ background: p.color }} />
          <span style={{ color: 'var(--text-muted)' }}>{p.name}:</span>
          <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>{p.value?.toFixed(1)} kW</span>
        </div>
      ))}
    </div>
  )
}

export function ForecastChart({ horizon = 24 }: { horizon?: number }) {
  const { activeSite } = useSiteContext()
  const { data, loading, error } = useForecast(activeSite?.id || null, horizon)

  if (loading) return <Card><LoadingSkeleton rows={4} /></Card>
  if (error) return <Card><p className="text-sm" style={{ color: 'var(--red)' }}>Error loading forecast</p></Card>
  if (!data) return null

  const chartData = data.timestamps.map((ts: string, i: number) => ({
    time: new Date(ts).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
    p10: data.forecast.p10[i],
    p50: data.forecast.p50[i],
    p90: data.forecast.p90[i],
  }))

  return (
    <Card>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>Generation Forecast</h3>
          <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>{horizon}h outlook with confidence bands</p>
        </div>
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-0.5 rounded" style={{ background: 'var(--accent)' }} />
            <span style={{ color: 'var(--text-muted)' }}>P50</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded opacity-20" style={{ background: 'var(--accent)' }} />
            <span style={{ color: 'var(--text-muted)' }}>P10-P90</span>
          </div>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={260}>
        <ComposedChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
          <defs>
            <linearGradient id="gradient-band" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#6366f1" stopOpacity={0.15} />
              <stop offset="100%" stopColor="#6366f1" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
          <XAxis dataKey="time" tick={{ fontSize: 10, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} interval={Math.floor(chartData.length / 6)} />
          <YAxis tick={{ fontSize: 10, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} width={40} />
          <Tooltip content={<CustomTooltip />} />
          <Area type="monotone" dataKey="p90" stroke="none" fill="url(#gradient-band)" name="P90" />
          <Area type="monotone" dataKey="p10" stroke="none" fill="white" name="P10" />
          <Line type="monotone" dataKey="p50" stroke="#6366f1" strokeWidth={2} dot={false} name="Forecast" />
        </ComposedChart>
      </ResponsiveContainer>
    </Card>
  )
}
