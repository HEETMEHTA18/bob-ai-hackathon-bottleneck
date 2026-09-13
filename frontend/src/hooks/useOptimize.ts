import { useState, useEffect } from 'react'
import { getOptimize } from '../api/client'

export function useOptimize(siteId: string | null, horizon = 24) {
  const [schedule, setSchedule] = useState<any[]>([])
  const [totalFinancial, setTotalFinancial] = useState(0)
  const [totalCO2, setTotalCO2] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!siteId) return
    setLoading(true)
    getOptimize(siteId, horizon)
      .then(res => {
        setSchedule(res.data.schedule)
        setTotalFinancial(res.data.total_financial_impact_inr)
        setTotalCO2(res.data.total_co2_impact_tonnes)
        setError(null)
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [siteId, horizon])

  return { schedule, totalFinancial, totalCO2, loading, error }
}
