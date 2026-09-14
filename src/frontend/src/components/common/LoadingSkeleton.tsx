import { ReactNode } from 'react'

export function LoadingSkeleton({ rows = 3, className = '' }: { rows?: number; className?: string }) {
  return (
    <div className={`space-y-3 ${className}`}>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="skeleton h-4 rounded" style={{ width: `${85 - i * 15}%` }} />
      ))}
    </div>
  )
}

export function EmptyState({ icon, title, description, action }: { icon: ReactNode; title: string; description: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center animate-fadeIn">
      <div className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4" style={{ background: 'var(--bg-tertiary)', color: 'var(--text-muted)' }}>
        {icon}
      </div>
      <h3 className="text-base font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>{title}</h3>
      <p className="text-sm max-w-sm" style={{ color: 'var(--text-muted)' }}>{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}

export function Card({ children, className = '', padding = true }: { children: ReactNode; className?: string; padding?: boolean }) {
  return (
    <div className={`card ${padding ? 'p-5' : ''} ${className}`}>
      {children}
    </div>
  )
}

export function Badge({ variant, children, className = '' }: { variant: 'green' | 'amber' | 'red' | 'default' | 'accent'; children: ReactNode; className?: string }) {
  return (
    <span className={`badge badge-${variant} ${className}`}>
      {children}
    </span>
  )
}

export function KPICard({ label, value, subtext, icon, trend, trendValue }: {
  label: string; value: string; subtext?: string; icon: ReactNode; trend?: 'up' | 'down' | 'neutral'; trendValue?: string
}) {
  return (
    <div className="card p-4 transition-all hover:shadow-md">
      <div className="flex items-start justify-between mb-3">
        <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: 'var(--accent-light)', color: 'var(--accent)' }}>
          {icon}
        </div>
        {trend && (
          <span className="inline-flex items-center gap-0.5 text-xs font-semibold" style={{ color: trend === 'up' ? 'var(--green)' : trend === 'down' ? 'var(--red)' : 'var(--text-muted)' }}>
            {trend === 'up' ? (
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="18 15 12 9 6 15"/></svg>
            ) : trend === 'down' ? (
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="6 9 12 15 18 9"/></svg>
            ) : null}
            {trendValue}
          </span>
        )}
      </div>
      <p className="text-xl font-bold tracking-tight" style={{ color: 'var(--text-primary)' }}>{value}</p>
      <p className="text-[11px] font-medium mt-0.5" style={{ color: 'var(--text-muted)' }}>{label}</p>
      {subtext && <p className="text-[10px] mt-0.5" style={{ color: 'var(--text-muted)' }}>{subtext}</p>}
    </div>
  )
}

export function Button({ variant = 'primary', size = 'md', children, className = '', ...props }: {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  children: ReactNode
  className?: string
} & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button className={`btn btn-${variant} btn-${size} ${className}`} {...props}>
      {children}
    </button>
  )
}

export function Tabs({ tabs, active, onChange }: { tabs: { id: string; label: string }[]; active: string; onChange: (id: string) => void }) {
  return (
    <div className="inline-flex p-1 rounded-lg" style={{ background: 'var(--bg-tertiary)' }}>
      {tabs.map(tab => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className="px-3 py-1.5 rounded-md text-sm font-medium transition-all"
          style={{
            background: active === tab.id ? 'white' : 'transparent',
            color: active === tab.id ? 'var(--text-primary)' : 'var(--text-muted)',
            boxShadow: active === tab.id ? 'var(--shadow-sm)' : 'none',
          }}
        >
          {tab.label}
        </button>
      ))}
    </div>
  )
}
