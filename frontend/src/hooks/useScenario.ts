import { useState } from 'react'
import { runScenario } from '../api/client'

export function useScenario(siteId: string | null) {
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const simulate = async (params: {
    cloud_cover_delta?: number
    wind_speed_delta?: number
    battery_soc_override?: number
  }) => {
    if (!siteId) return
    setLoading(true)
    try {
      const res = await runScenario(siteId, params)
      setResult(res.data)
      setError(null)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return { result, loading, error, simulate }
}
