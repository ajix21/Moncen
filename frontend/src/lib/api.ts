import type {
  CCTVStream,
  CCTVStreamCreate,
  CCTVStreamUpdate,
  EventsPage,
  StatsSummary,
  CVStatus,
  CVSettings,
  CVStreamStatus,
} from '@/types'

const BASE = ''

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`HTTP ${res.status}: ${text}`)
  }
  return res.json() as Promise<T>
}

// ── CCTV ──────────────────────────────────────────────────────────────────────

export const cctvApi = {
  list: () => request<CCTVStream[]>('/api/cctvs'),
  create: (data: CCTVStreamCreate) =>
    request<CCTVStream>('/api/cctvs', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: string, data: CCTVStreamUpdate) =>
    request<CCTVStream>(`/api/cctvs/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  remove: (id: string) => fetch(`/api/cctvs/${id}`, { method: 'DELETE' }),
  toggle: (id: string) => request<CCTVStream>(`/api/cctvs/${id}/toggle`, { method: 'PATCH' }),
}

// ── Events ────────────────────────────────────────────────────────────────────

export const eventsApi = {
  list: (params?: { page?: number; limit?: number; cctv_id?: string; level?: string }) => {
    const qs = new URLSearchParams()
    if (params?.page) qs.set('page', String(params.page))
    if (params?.limit) qs.set('limit', String(params.limit))
    if (params?.cctv_id) qs.set('cctv_id', params.cctv_id)
    if (params?.level) qs.set('level', params.level)
    return request<EventsPage>(`/api/events?${qs}`)
  },
  clear: () => fetch('/api/events', { method: 'DELETE' }),
}

// ── Stats ─────────────────────────────────────────────────────────────────────

export const statsApi = {
  summary: () => request<StatsSummary>('/api/stats/summary'),
}

// ── CV Engine ─────────────────────────────────────────────────────────────────

export const cvApi = {
  status: () => request<CVStatus>('/api/cv/status'),
  streams: () =>
    request<{ streams: CVStreamStatus[] }>('/cv/streams').then((d) => d.streams),
  startStream: (id: string) =>
    request<{ status: string }>(`/cv/streams/${id}/start`, { method: 'POST' }),
  stopStream: (id: string) =>
    request<{ status: string }>(`/cv/streams/${id}/stop`, { method: 'POST' }),
  getSettings: () => request<CVSettings>('/cv/settings'),
  updateSettings: (data: Partial<CVSettings>) =>
    request<{ status: string; settings: CVSettings }>('/cv/settings', {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  snapshotUrl: (cctvId: string) => `/cv/snapshot/${cctvId}`,
}
