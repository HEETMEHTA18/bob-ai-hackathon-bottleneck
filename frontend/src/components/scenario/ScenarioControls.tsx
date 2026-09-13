import { useState } from 'react'
import { useScenario } from '../../hooks/useScenario'
import { useSiteContext } from '../../context/SiteContext'
import { Card, LoadingSkeleton, Badge, Button } from '../common/LoadingSkeleton'

export function ScenarioControls() {
  const { activeSite } = useSiteContext()
  const { result, loading, simulate } = useScenario(activeSite?.id || null)
  const [cloudDelta, setCloudDelta] = useState(0)
  const [windDelta, setWindDelta] = useState(0)
  const [batterySOC, setBatterySOC] = useState<number | ''>('')

  const handleSimulate = () => {
    simulate({
      cloud_cover_delta: cloudDelta,
      wind_speed_delta: windDelta,
      battery_soc_override: batterySOC !== '' ? batterySOC : undefined,
    })
  }

  return (
    <Card>
      <div className="mb-4">
        <h3 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>Scenario Simulator</h3>
        <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>Perturb forecast inputs and see updated recommendations</p>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-5">
        <div className="p-3 rounded-lg border" style={{ borderColor: 'var(--border)' }}>
          <label className="text-[10px] font-semibold uppercase tracking-wider block mb-2" style={{ color: 'var(--text-muted)' }}>Cloud Cover</label>
          <input
            type="range" min={-50} max={50} value={cloudDelta}
            onChange={e => setCloudDelta(Number(e.target.value))}
            className="w-full h-1.5 rounded-full appearance-none cursor-pointer accent-indigo-500"
          />
          <p className="text-center text-sm font-bold mt-2" style={{ color: cloudDelta > 0 ? 'var(--amber)' : cloudDelta < 0 ? 'var(--green)' : 'var(--text-muted)' }}>
            {cloudDelta > 0 ? '+' : ''}{cloudDelta}%
          </p>
        </div>
        <div className="p-3 rounded-lg border" style={{ borderColor: 'var(--border)' }}>
          <label className="text-[10px] font-semibold uppercase tracking-wider block mb-2" style={{ color: 'var(--text-muted)' }}>Wind Speed</label>
          <input
            type="range" min={-50} max={50} value={windDelta}
            onChange={e => setWindDelta(Number(e.target.value))}
            className="w-full h-1.5 rounded-full appearance-none cursor-pointer accent-indigo-500"
          />
          <p className="text-center text-sm font-bold mt-2" style={{ color: windDelta > 0 ? 'var(--green)' : windDelta < 0 ? 'var(--amber)' : 'var(--text-muted)' }}>
            {windDelta > 0 ? '+' : ''}{windDelta}%
          </p>
        </div>
        <div className="p-3 rounded-lg border" style={{ borderColor: 'var(--border)' }}>
          <label className="text-[10px] font-semibold uppercase tracking-wider block mb-2" style={{ color: 'var(--text-muted)' }}>Battery SOC</label>
          <input
            type="number" value={batterySOC}
            onChange={e => setBatterySOC(e.target.value ? Number(e.target.value) : '')}
            placeholder="Auto"
            className="input text-center"
          />
        </div>
      </div>

      <Button onClick={handleSimulate} disabled={loading} className="w-full">
        {loading ? 'Simulating...' : 'Run Simulation'}
      </Button>

      {result && (
        <div className="mt-4 p-4 rounded-lg border animate-fadeIn" style={{ borderColor: 'var(--border)', background: 'var(--bg-secondary)' }}>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Adjusted Generation</p>
              <p className="text-lg font-bold" style={{ color: 'var(--accent)' }}>{result.adjusted_generation_kw.toFixed(1)} kW</p>
            </div>
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Action</p>
              <p className="text-lg font-bold capitalize" style={{ color: 'var(--text-primary)' }}>{result.action.replace(/_/g, ' ')}</p>
            </div>
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Risk Level</p>
              <Badge variant={result.risk === 'HIGH' ? 'red' : result.risk === 'MEDIUM' ? 'amber' : 'green'}>{result.risk}</Badge>
            </div>
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Financial Impact</p>
              <p className="text-lg font-bold" style={{ color: result.financial_impact_inr >= 0 ? 'var(--green)' : 'var(--red)' }}>₹{result.financial_impact_inr.toFixed(0)}</p>
            </div>
          </div>
          <p className="text-xs mt-3 pt-3 border-t" style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>{result.explanation}</p>
        </div>
      )}
    </Card>
  )
}
