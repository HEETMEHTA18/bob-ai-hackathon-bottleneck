import { useState } from 'react'
import { Card, Badge, Button } from '../common/LoadingSkeleton'

const DATA_SOURCES = [
  {
    id: 'kaggle-solar',
    name: 'Kaggle Solar Power Generation',
    type: 'Historical',
    description: 'Plant-1 and Plant-2 generation data with weather sensors',
    rows: '34,000+',
    format: 'CSV',
    url: 'https://www.kaggle.com/datasets/anikannal/solar-power-generation-data',
    status: 'downloaded',
    features: ['Generation (kW)', 'Irradiance (GHI/DNI/DHI)', 'Temperature', 'Humidity'],
  },
  {
    id: 'kaggle-wind',
    name: 'Kaggle Wind Turbine SCADA',
    type: 'Historical',
    description: 'Turbine SCADA data with wind speed, direction, power output',
    rows: '50,000+',
    format: 'CSV',
    url: 'https://www.kaggle.com/datasets/berkerzen/wind-turbine-scada-dataset',
    status: 'downloaded',
    features: ['Wind Speed', 'Wind Direction', 'Power (kW)', 'Temperature'],
  },
  {
    id: 'open-meteo',
    name: 'Open-Meteo API',
    type: 'Live + Historical',
    description: 'Free weather API with GHI, DNI, DHI, temperature, wind',
    rows: 'Unlimited',
    format: 'JSON',
    url: 'https://open-meteo.com',
    status: 'connected',
    features: ['GHI', 'DNI', 'DHI', 'Temperature', 'Wind Speed/Direction', 'Cloud Cover'],
  },
  {
    id: 'huggingface-timeseries',
    name: 'HuggingFace Time Series',
    type: 'Foundation Models',
    description: 'Pre-trained time-series models (Chronos, Lag-Llama)',
    rows: 'N/A',
    format: 'Model',
    url: 'https://huggingface.co/collections/tag/time-series-forecasting',
    status: 'ready',
    features: ['Zero-shot forecasting', 'Probabilistic predictions', 'Transfer learning'],
  },
  {
    id: 'huggingface-solar',
    name: 'HuggingFace Solar Dataset',
    type: 'Historical',
    description: 'Community solar generation datasets',
    rows: 'Various',
    format: 'CSV/Parquet',
    url: 'https://huggingface.co/datasets?search=solar+generation',
    status: 'available',
    features: ['Multi-site solar data', 'Various granularities', 'Global coverage'],
  },
  {
    id: 'opennem',
    name: 'OpenNEM Australia',
    type: 'Historical',
    description: 'Australian NEM wind and solar generation data',
    rows: '100,000+',
    format: 'CSV',
    url: 'https://opennem.org.au',
    status: 'available',
    features: ['5-min interval data', 'Wind + Solar', 'Regional breakdown'],
  },
]

export function DataSourcesPage() {
  const [sources, setSources] = useState(DATA_SOURCES)

  return (
    <div className="space-y-6 animate-fadeIn">
      <div>
        <h2 className="text-xl font-bold tracking-tight" style={{ color: 'var(--text-primary)' }}>Data Sources</h2>
        <p className="text-sm mt-0.5" style={{ color: 'var(--text-muted)' }}>Connected data feeds and downloadable datasets</p>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="card p-4">
          <p className="text-[11px] font-semibold uppercase tracking-wider mb-1" style={{ color: 'var(--text-muted)' }}>Total Sources</p>
          <p className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>{sources.length}</p>
        </div>
        <div className="card p-4">
          <p className="text-[11px] font-semibold uppercase tracking-wider mb-1" style={{ color: 'var(--text-muted)' }}>Connected</p>
          <p className="text-2xl font-bold" style={{ color: 'var(--green)' }}>{sources.filter(s => s.status === 'connected' || s.status === 'downloaded').length}</p>
        </div>
        <div className="card p-4">
          <p className="text-[11px] font-semibold uppercase tracking-wider mb-1" style={{ color: 'var(--text-muted)' }}>Data Points</p>
          <p className="text-2xl font-bold" style={{ color: 'var(--accent)' }}>200K+</p>
        </div>
      </div>

      <div className="space-y-3">
        {sources.map(source => (
          <Card key={source.id}>
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{source.name}</h3>
                  <Badge variant={source.status === 'connected' ? 'green' : source.status === 'downloaded' ? 'accent' : 'default'}>
                    {source.status}
                  </Badge>
                  <Badge variant="default">{source.type}</Badge>
                </div>
                <p className="text-xs mb-2" style={{ color: 'var(--text-muted)' }}>{source.description}</p>
                <div className="flex flex-wrap gap-1.5">
                  {source.features.map((f, i) => (
                    <span key={i} className="px-2 py-0.5 rounded text-[10px] font-medium" style={{ background: 'var(--bg-tertiary)', color: 'var(--text-secondary)' }}>
                      {f}
                    </span>
                  ))}
                </div>
              </div>
              <div className="flex items-center gap-3 ml-4">
                <div className="text-right">
                  <p className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>{source.rows}</p>
                  <p className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{source.format}</p>
                </div>
                <a
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-secondary btn-sm"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
                  Open
                </a>
              </div>
            </div>
          </Card>
        ))}
      </div>

      <Card>
        <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>Lambda Architecture Data Flow</h3>
        <div className="flex items-center gap-3 overflow-x-auto pb-2">
          {[
            { label: 'Data Sources', sub: 'Kaggle, Open-Meteo, HuggingFace', color: 'var(--accent)' },
            { label: 'Batch Layer', sub: 'Historical processing, feature eng.', color: 'var(--green)' },
            { label: 'Speed Layer', sub: 'Real-time forecast updates', color: 'var(--amber)' },
            { label: 'Serving Layer', sub: 'Merged view for API', color: 'var(--purple)' },
            { label: 'Dashboard', sub: 'Visualization & decisions', color: 'var(--cyan)' },
          ].map((step, i) => (
            <div key={i} className="flex items-center gap-3">
              <div className="p-3 rounded-lg border min-w-[140px]" style={{ borderColor: 'var(--border)', background: 'white' }}>
                <div className="w-6 h-6 rounded flex items-center justify-center text-white text-xs font-bold mb-2" style={{ background: step.color }}>
                  {i + 1}
                </div>
                <p className="text-xs font-semibold" style={{ color: 'var(--text-primary)' }}>{step.label}</p>
                <p className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{step.sub}</p>
              </div>
              {i < 4 && (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="flex-shrink-0">
                  <polyline points="9 18 15 12 9 6"/>
                </svg>
              )}
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
