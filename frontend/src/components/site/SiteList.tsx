import { useSiteContext } from '../../context/SiteContext'

export function SiteList() {
  const { sites, activeSite } = useSiteContext()

  return (
    <div className="bg-energy-card border border-energy-border rounded-lg p-6">
      <h3 className="text-sm font-semibold text-gray-300 mb-4">Registered Sites</h3>
      {sites.length === 0 ? (
        <p className="text-gray-400 text-sm">No sites registered yet. <a href="#" className="text-energy-green underline" onClick={(e => e.preventDefault())}>Add your first site</a></p>
      ) : (
        <div className="space-y-3">
          {sites.map(site => (
            <div
              key={site.id}
              className={`flex items-center gap-3 p-3 rounded ${
                site.id === activeSite?.id ? 'bg-energy-green/10 text-energy-green' : 'text-gray-300 hover:bg-energy-dark transition'
              }`}
            >
              <span className="text-energy-green">⚡</span>
              <div>
                <p className="font-medium">{site.name}</p>
                <p className="text-xs text-gray-400">{site.capacity_kw} kW • Battery: {site.battery_capacity_kwh} kWh</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}