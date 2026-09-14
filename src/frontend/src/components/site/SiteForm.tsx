import { useState } from 'react'
import { createSite } from '../../api/client'
import { useSiteContext } from '../../context/SiteContext'
import { Button } from '../common/LoadingSkeleton'

export function SiteForm({ onClose }: { onClose: () => void }) {
  const { refreshSites } = useSiteContext()
  const [form, setForm] = useState({
    name: '', latitude: 28.6139, longitude: 77.2090, capacity_kw: 100,
    altitude: 0, surface_tilt: 28, surface_azimuth: 180,
    battery_capacity_kwh: 50, export_limit_kw: 80, hub_height_m: 80,
  })
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await createSite(form)
      await refreshSites()
      onClose()
    } catch (e: any) {
      alert('Error: ' + e.message)
    } finally {
      setLoading(false)
    }
  }

  const Input = ({ label, field, step }: { label: string; field: string; step?: string }) => (
    <div>
      <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--text-muted)' }}>{label}</label>
      <input type="number" step={step} value={(form as any)[field]} onChange={e => setForm({ ...form, [field]: Number(e.target.value) })} className="input" />
    </div>
  )

  return (
    <div className="fixed inset-0 flex items-center justify-center z-50" style={{ background: 'rgba(0,0,0,0.4)' }}>
      <div className="w-full max-w-lg rounded-xl border p-6 animate-scaleIn shadow-xl" style={{ background: 'white', borderColor: 'var(--border)' }}>
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-base font-semibold" style={{ color: 'var(--text-primary)' }}>Register New Site</h2>
          <button onClick={onClose} className="btn btn-ghost btn-icon btn-sm">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--text-muted)' }}>Site Name</label>
            <input type="text" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} className="input" placeholder="e.g. Rooftop Solar Plant" required />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Input label="Latitude" field="latitude" step="0.0001" />
            <Input label="Longitude" field="longitude" step="0.0001" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Input label="Capacity (kW)" field="capacity_kw" />
            <Input label="Altitude (m)" field="altitude" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Input label="Battery (kWh)" field="battery_capacity_kwh" />
            <Input label="Export Limit (kW)" field="export_limit_kw" />
          </div>
          <div className="flex gap-3 pt-2">
            <Button type="button" variant="secondary" onClick={onClose} className="flex-1">Cancel</Button>
            <Button type="submit" disabled={loading} className="flex-1">{loading ? 'Creating...' : 'Create Site'}</Button>
          </div>
        </form>
      </div>
    </div>
  )
}
