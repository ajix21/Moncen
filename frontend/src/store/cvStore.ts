import { create } from 'zustand'
import type { CVStatus } from '@/types'

interface CVStore {
  running: boolean
  streamsActive: number
  uptimeSeconds: number
  model: string
  lastChecked: Date | null
  setStatus: (status: CVStatus) => void
  setOffline: () => void
}

export const useCVStore = create<CVStore>((set) => ({
  running: false,
  streamsActive: 0,
  uptimeSeconds: 0,
  model: 'yolov8n',
  lastChecked: null,

  setStatus: (status) =>
    set({
      running: status.running,
      streamsActive: status.streams_active,
      uptimeSeconds: status.uptime_seconds,
      model: status.model ?? 'yolov8n',
      lastChecked: new Date(),
    }),

  setOffline: () =>
    set({
      running: false,
      streamsActive: 0,
      uptimeSeconds: 0,
      lastChecked: new Date(),
    }),
}))
