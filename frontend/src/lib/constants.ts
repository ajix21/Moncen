export const ALERT_LEVELS = {
  NORMAL:  { min: 0,    max: 49,    color: '#10b981' },
  WASPADA: { min: 50,   max: 199,   color: '#f59e0b' },
  SIAGA:   { min: 200,  max: 999,   color: '#f97316' },
  DARURAT: { min: 1000, max: 99999, color: '#ef4444' },
} as const
