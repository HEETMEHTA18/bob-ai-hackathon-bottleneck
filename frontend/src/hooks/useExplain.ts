import { useState, useEffect } from 'react'
import { getExplain } from '../api/client'

export function useExplain(siteId: string | null) {
  const [data, setData] = useState<any | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!siteId) return
    setLoading(true)
    getExplain(siteId)
      .then(res => { setData(res.data); setError(null) })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [siteId])

  return { data, loading, error }
}
