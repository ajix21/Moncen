import { create } from 'zustand'
import type { CVResult, AlertLevel } from '@/types'

interface StreamAlert {
  cctv_id: string
  cctv_name: string
  location: string
  person_count: number
  alert_level: AlertLevel
  alert_color: string
  timestamp: string
  cv_status: 'analyzing' | 'queued' | 'offline'
  bounding_boxes: [number, number, number, number][]
}

interface AlertStore {
  alerts: Record<string, StreamAlert>
  highestLevel: AlertLevel
  updateAlert: (result: CVResult) => void
  clearAlerts: () => void
}

const LEVEL_ORDER: AlertLevel[] = ['NORMAL', 'WASPADA', 'SIAGA', 'DARURAT']

function computeHighest(alerts: Record<string, StreamAlert>): AlertLevel {
  let highest = 0
  for (const a of Object.values(alerts)) {
    const idx = LEVEL_ORDER.indexOf(a.alert_level)
    if (idx > highest) highest = idx
  }
  return LEVEL_ORDER[highest]
}

export const useAlertStore = create<AlertStore>((set) => ({
  alerts: {},
  highestLevel: 'NORMAL',

  updateAlert: (result) =>
    set((s) => {
      const alerts = {
        ...s.alerts,
        [result.cctv_id]: {
          cctv_id: result.cctv_id,
          cctv_name: result.cctv_name,
          location: result.location,
          person_count: result.person_count,
          alert_level: result.alert_level,
          alert_color: result.alert_color,
          timestamp: result.timestamp,
          cv_status: result.cv_status,
          bounding_boxes: result.bounding_boxes,
        },
      }
      return { alerts, highestLevel: computeHighest(alerts) }
    }),

  clearAlerts: () => set({ alerts: {}, highestLevel: 'NORMAL' }),
}))
