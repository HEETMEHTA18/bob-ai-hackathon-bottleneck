import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { Site, listSites } from '../api/client'

interface SiteContextType {
  sites: Site[]
  activeSite: Site | null
  setActiveSite: (site: Site | null) => void
  refreshSites: () => Promise<void>
}

const SiteContext = createContext<SiteContextType>({
  sites: [],
  activeSite: null,
  setActiveSite: () => {},
  refreshSites: async () => {},
})

export function SiteProvider({ children }: { children: ReactNode }) {
  const [sites, setSites] = useState<Site[]>([])
  const [activeSite, setActiveSite] = useState<Site | null>(null)

  const refreshSites = async () => {
    try {
      const res = await listSites()
      setSites(res.data)
      if (!activeSite && res.data.length > 0) {
        setActiveSite(res.data[0])
      }
    } catch (e) {
      console.error('Failed to load sites:', e)
    }
  }

  useEffect(() => { refreshSites() }, [])

  return (
    <SiteContext.Provider value={{ sites, activeSite, setActiveSite, refreshSites }}>
      {children}
    </SiteContext.Provider>
  )
}

export const useSiteContext = () => useContext(SiteContext)
