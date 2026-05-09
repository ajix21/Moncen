import { create } from 'zustand'
import type { CCTVStream } from '@/types'
import { cctvApi } from '@/lib/api'

interface CCTVStore {
  streams: CCTVStream[]
  loading: boolean
  error: string | null
  fetchStreams: () => Promise<void>
  addStream: (data: Omit<CCTVStream, 'id' | 'created_at' | 'updated_at'>) => Promise<void>
  updateStream: (id: string, data: Partial<CCTVStream>) => Promise<void>
  removeStream: (id: string) => Promise<void>
  toggleStream: (id: string) => Promise<void>
}

export const useCCTVStore = create<CCTVStore>((set, get) => ({
  streams: [],
  loading: false,
  error: null,

  fetchStreams: async () => {
    set({ loading: true, error: null })
    try {
      const streams = await cctvApi.list()
      set({ streams, loading: false })
    } catch (e) {
      set({ error: String(e), loading: false })
    }
  },

  addStream: async (data) => {
    const stream = await cctvApi.create(data)
    set((s) => ({ streams: [...s.streams, stream] }))
  },

  updateStream: async (id, data) => {
    const updated = await cctvApi.update(id, data)
    set((s) => ({ streams: s.streams.map((c) => (c.id === id ? updated : c)) }))
  },

  removeStream: async (id) => {
    await cctvApi.remove(id)
    set((s) => ({ streams: s.streams.filter((c) => c.id !== id) }))
  },

  toggleStream: async (id) => {
    const updated = await cctvApi.toggle(id)
    set((s) => ({ streams: s.streams.map((c) => (c.id === id ? updated : c)) }))
  },
}))
