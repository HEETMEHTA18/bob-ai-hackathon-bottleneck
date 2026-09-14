import { useState, useEffect } from 'react'
import { getForecast } from '../api/client'

export function useForecast(siteId: string | null, horizon = 24) {
  const [data, setData] = useState<any | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!siteId) return
    setLoading(true)
    getForecast(siteId, horizon)
      .then(res => { setData(res.data); setError(null) })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [siteId, horizon])

  return { data, loading, error }
}
