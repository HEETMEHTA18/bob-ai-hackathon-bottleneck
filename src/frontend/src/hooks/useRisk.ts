import { useState, useEffect } from 'react'
import { getRisk } from '../api/client'

export function useRisk(siteId: string | null, horizon = 24) {
  const [risks, setRisks] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!siteId) return
    setLoading(true)
    getRisk(siteId, horizon)
      .then(res => { setRisks(res.data.risks); setError(null) })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [siteId, horizon])

  return { risks, loading, error }
}
