/**
 * GridShield — Shared colour/class helpers that match the existing CSS design system.
 * Uses .badge, .btn, inline colour vars — no Tailwind dark classes.
 */

export const ACCENT = '#1a73e8'
export const GREEN  = '#0d904f'
export const AMBER  = '#e8710a'
export const RED    = '#c5221f'
export const MUTED  = '#5f6368'

/** Inline style for a coloured left-border accent strip on a card */
export function riskAccentStyle(level: string): React.CSSProperties {
  const map: Record<string, string> = {
    critical: RED, high: AMBER, medium: '#f59e0b', low: GREEN,
  }
  return { borderLeft: `4px solid ${map[level] ?? MUTED}` }
}

export function riskBadgeClass(level: string) {
  switch (level) {
    case 'critical': return 'badge badge-red'
    case 'high':     return 'badge badge-amber'
    case 'medium':   return 'badge' // amber-ish via inline
    case 'low':      return 'badge badge-green'
    default:         return 'badge badge-default'
  }
}

export function riskTextColor(level: string): string {
  switch (level) {
    case 'critical': return RED
    case 'high':     return AMBER
    case 'medium':   return '#f59e0b'
    case 'low':      return GREEN
    default:         return MUTED
  }
}

export function priorityBadgeClass(level: string) {
  switch (level) {
    case 'immediate': return 'badge badge-red'
    case 'high':      return 'badge badge-amber'
    case 'medium':    return 'badge badge-default'
    default:          return 'badge badge-default'
  }
}

export function riskBarColor(score: number): string {
  if (score >= 75) return RED
  if (score >= 50) return AMBER
  if (score >= 25) return '#f59e0b'
  return GREEN
}

export function statusColor(status: string): string {
  switch (status) {
    case 'critical':    return RED
    case 'degraded':    return AMBER
    case 'maintenance': return ACCENT
    case 'offline':     return MUTED
    default:            return GREEN
  }
}

export function assetTypeIcon(type: string): string {
  switch (type) {
    case 'transformer':    return 'TR'
    case 'feeder':         return 'FD'
    case 'breaker':        return 'BR'
    case 'recloser':       return 'RC'
    case 'switch':         return 'SW'
    case 'capacitor_bank': return 'CB'
    default:               return '??'
  }
}

export function assetTypeLabel(type: string): string {
  return type.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())
}

export function pct(v: number): string {
  return `${(v * 100).toFixed(0)}%`
}

/** Inline mini progress bar */
export function MiniBar({ value, max = 1 }: { value: number; max?: number }) {
  const w = Math.round((value / max) * 100)
  const color = riskBarColor(w)
  return (
    <div style={{ background: '#e8eaed', borderRadius: 5, height: 8, overflow: 'hidden', flex: 1 }}>
      <div style={{ width: `${w}%`, background: color, height: '100%', borderRadius: 5, transition: 'width 0.3s' }} />
    </div>
  )
}

import React from 'react'
