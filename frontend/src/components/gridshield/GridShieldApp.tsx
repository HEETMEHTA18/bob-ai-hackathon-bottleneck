/**
 * GridShield — Main Application Shell
 * 
 * This is the GridShield Command Center. The renewable forecasting pages
 * (Forecast, Optimize) are preserved for backward compatibility but
 * GridShield is now the primary UX.
 * 
 * Navigation:
 *   Command Center → Grid Map → Maintenance Planner → Crew Planner
 *   → Scenario Simulator → AI Copilot → Hardware Settings
 */
import { useState, type ReactNode } from 'react'
import { ShieldAlert, Map, Wrench, Truck, CloudLightning, Bot, Settings, ChevronLeft, ChevronRight } from 'lucide-react'
import CommandCenter from './CommandCenter'
import AssetIntelligence from './AssetIntelligence'
import MaintenancePlanner from './MaintenancePlanner'
import CrewPlanner from './CrewPlanner'
import ScenarioSimulator from './ScenarioSimulator'
import GridShieldCopilot from './Copilot'
import GridMap from './GridMap'
import SettingsPage from './Settings'

type GSPage =
  | { id: 'dashboard' }
  | { id: 'asset'; assetId: string }
  | { id: 'maintenance' }
  | { id: 'crew' }
  | { id: 'scenarios' }
  | { id: 'copilot' }
  | { id: 'map' }
  | { id: 'settings' }

const NAV_ITEMS: Array<{ id: GSPage['id']; label: string; icon: ReactNode }> = [
  { id: 'dashboard',   label: 'Command Center', icon: <ShieldAlert size={18} /> },
  { id: 'map',         label: 'Grid Map',       icon: <Map size={18} /> },
  { id: 'maintenance', label: 'Maintenance',    icon: <Wrench size={18} /> },
  { id: 'crew',        label: 'Crew Planner',   icon: <Truck size={18} /> },
  { id: 'scenarios',   label: 'Scenarios',      icon: <CloudLightning size={18} /> },
  { id: 'copilot',     label: 'AI Copilot',     icon: <Bot size={18} /> },
  { id: 'settings',    label: 'Settings',       icon: <Settings size={18} /> },
]

export default function GridShieldApp() {
  const [page, setPage] = useState<GSPage>({ id: 'dashboard' })
  const [sidebarOpen, setSidebarOpen] = useState(true)

  function nav(id: string) {
    setPage({ id } as GSPage)
  }

  function goToAsset(assetId: string) {
    setPage({ id: 'asset', assetId })
  }

  return (
    <div className="min-h-screen bg-gray-950 flex">
      {/* Sidebar */}
      <aside className={`${sidebarOpen ? 'w-56' : 'w-14'} flex-shrink-0 bg-gray-900 border-r border-gray-800 flex flex-col transition-all duration-200`}>
        {/* Logo */}
        <div className="p-4 border-b border-gray-800 flex items-center gap-3">
          <div className="w-7 h-7 bg-blue-600 rounded-md flex items-center justify-center text-sm flex-shrink-0">
            <ShieldAlert size={16} className="text-white" />
          </div>
          {sidebarOpen && (
            <div className="min-w-0">
              <p className="text-white font-bold text-sm truncate">GridShield</p>
              <p className="text-gray-500 text-xs truncate">Grid Ops AI</p>
            </div>
          )}
          <button
            className={`${sidebarOpen ? 'ml-auto' : 'mx-auto'} text-gray-500 hover:text-gray-300 text-sm`}
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            {sidebarOpen ? (
              <ChevronLeft size={16} />
            ) : (
              <ChevronRight size={16} />
            )}
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 py-4 space-y-1 px-2">
          {NAV_ITEMS.map(item => {
            const active = page.id === item.id
            return (
              <button
                key={item.id}
                onClick={() => nav(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  active
                    ? 'bg-blue-600/20 text-blue-300 border border-blue-700/50'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
                }`}
                title={!sidebarOpen ? item.label : undefined}
              >
                <span className="flex-shrink-0">{item.icon}</span>
                {sidebarOpen && <span className="truncate">{item.label}</span>}
              </button>
            )
          })}
        </nav>

        {/* Footer */}
        {sidebarOpen && (
          <div className="p-4 border-t border-gray-800">
            <p className="text-xs text-gray-600">IBM Bob Hackathon 2026</p>
            <p className="text-xs text-gray-700">U1 · Power Outage Prediction</p>
          </div>
        )}
      </aside>

      {/* Main content */}
      <main className="flex-1 min-w-0 overflow-y-auto">
        <div className="max-w-7xl mx-auto px-6 py-6">
          {page.id === 'dashboard' && (
            <CommandCenter onSelectAsset={goToAsset} />
          )}
          {page.id === 'asset' && (
            <AssetIntelligence
              assetId={page.assetId}
              onBack={() => nav('dashboard')}
            />
          )}
          {page.id === 'maintenance' && (
            <MaintenancePlanner onSelectAsset={goToAsset} />
          )}
          {page.id === 'crew' && (
            <CrewPlanner onSelectAsset={goToAsset} />
          )}
          {page.id === 'scenarios' && (
            <ScenarioSimulator onSelectAsset={goToAsset} />
          )}
          {page.id === 'copilot' && (
            <GridShieldCopilot />
          )}
          {page.id === 'map' && (
            <GridMap onAssetSelect={goToAsset} />
          )}
          {page.id === 'settings' && (
            <SettingsPage />
          )}
        </div>
      </main>
    </div>
  )
}
