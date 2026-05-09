import type { AlertLevel } from '@/types'

export function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  return [h, m, s].map((v) => String(v).padStart(2, '0')).join(':')
}

export function formatTimestamp(iso: string): string {
  return new Date(iso).toLocaleString('id-ID', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    day: '2-digit',
    month: 'short',
  })
}

export function alertLevelBadgeClass(level: AlertLevel): string {
  const map: Record<AlertLevel, string> = {
    NORMAL: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    WASPADA: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    SIAGA: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    DARURAT: 'bg-red-500/20 text-red-400 border-red-500/30',
  }
  return map[level] ?? map.NORMAL
}

export function alertLevelColor(level: AlertLevel): string {
  const map: Record<AlertLevel, string> = {
    NORMAL: '#10b981',
    WASPADA: '#f59e0b',
    SIAGA: '#f97316',
    DARURAT: '#ef4444',
  }
  return map[level] ?? '#10b981'
}

export function cn(...classes: (string | undefined | false | null)[]): string {
  return classes.filter(Boolean).join(' ')
}
