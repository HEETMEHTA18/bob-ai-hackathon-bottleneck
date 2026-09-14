import { useExplain } from '../../hooks/useExplain'
import { useSiteContext } from '../../context/SiteContext'
import { Card, Badge, LoadingSkeleton } from '../common/LoadingSkeleton'

const ACTION_CONFIG: Record<string, { icon: string; color: string; label: string }> = {
  charge_battery: { icon: '⚡', color: 'var(--green)', label: 'Charge Battery' },
  discharge_battery: { icon: '🔋', color: 'var(--amber)', label: 'Discharge Battery' },
  curtail: { icon: '✂️', color: 'var(--red)', label: 'Curtail Generation' },
  activate_backup: { icon: '🚨', color: 'var(--red)', label: 'Activate Backup' },
  hold: { icon: '✅', color: 'var(--cyan)', label: 'Hold Position' },
}

export function RecommendationCard() {
  const { activeSite } = useSiteContext()
  const { data, loading, error } = useExplain(activeSite?.id || null)

  if (loading) return <Card><LoadingSkeleton rows={2} /></Card>
  if (error) return <Card><p className="text-sm" style={{ color: 'var(--red)' }}>Error loading recommendation</p></Card>
  if (!data) return null

  const config = ACTION_CONFIG[data.action] || ACTION_CONFIG.hold

  return (
    <Card>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>Current Recommendation</h3>
        <Badge variant={data.risk === 'HIGH' ? 'red' : data.risk === 'MEDIUM' ? 'amber' : 'green'}>
          {data.risk} RISK
        </Badge>
      </div>

      <div className="flex items-start gap-4">
        <div className="w-12 h-12 rounded-xl flex items-center justify-center text-xl flex-shrink-0" style={{ background: `${config.color}10` }}>
          {config.icon}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-base font-bold" style={{ color: config.color }}>{config.label}</p>
          <p className="text-sm mt-2 leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{data.explanation}</p>

          <div className="flex gap-8 mt-4 pt-4 border-t" style={{ borderColor: 'var(--border)' }}>
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Financial Impact</p>
              <p className="text-lg font-bold mt-0.5" style={{ color: data.financial_impact_inr >= 0 ? 'var(--green)' : 'var(--red)' }}>
                ₹{data.financial_impact_inr.toFixed(0)}
              </p>
            </div>
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>CO₂ Impact</p>
              <p className="text-lg font-bold mt-0.5" style={{ color: data.co2_impact_tonnes >= 0 ? 'var(--green)' : 'var(--red)' }}>
                {data.co2_impact_tonnes.toFixed(3)} t
              </p>
            </div>
          </div>
        </div>
      </div>
    </Card>
  )
}
