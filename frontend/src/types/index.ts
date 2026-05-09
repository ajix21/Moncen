export interface CCTVStream {
  id: string
  name: string
  location: string
  stream_url: string
  enabled: boolean
  created_at: string
  updated_at: string
}

export interface CCTVStreamCreate {
  name: string
  location: string
  stream_url: string
  enabled?: boolean
}

export interface CCTVStreamUpdate {
  name?: string
  location?: string
  stream_url?: string
  enabled?: boolean
}

export type AlertLevel = 'NORMAL' | 'WASPADA' | 'SIAGA' | 'DARURAT'

export interface CVResult {
  type: 'cv_result'
  cctv_id: string
  cctv_name: string
  location: string
  timestamp: string
  person_count: number
  alert_level: AlertLevel
  alert_color: string
  confidence_avg: number
  stream_status: string
  cv_status: 'analyzing' | 'queued' | 'offline'
  frame_width: number
  frame_height: number
  bounding_boxes: [number, number, number, number][]
  processing_time_ms: number
}

export interface Event {
  id: string
  cctv_id: string
  cctv_name: string
  location: string
  alert_level: AlertLevel
  alert_color: string
  person_count: number
  confidence_avg: number | null
  timestamp: string
}

export interface EventsPage {
  items: Event[]
  total: number
  page: number
  limit: number
  pages: number
}

export interface StatsSummary {
  total_streams: number
  enabled_streams: number
  total_events: number
  level_counts: {
    normal: number
    waspada: number
    siaga: number
    darurat: number
  }
  latest_events: Event[]
}

export interface CVStatus {
  running: boolean
  streams_active: number
  uptime_seconds: number
  model?: string
}

export interface CVSettings {
  cv_frame_interval: number
  max_concurrent_streams: number
  yolo_model_name: string
  rotation_interval: number
  yolo_imgsz: number
  yolo_conf: number
}

export interface CVStreamStatus {
  cctv_id: string
  cctv_name: string
  location: string
  cv_status: 'analyzing' | 'queued' | 'offline'
  last_count: number | null
  last_level: AlertLevel | null
}

export interface DashboardSummary {
  type: 'summary'
  timestamp: string
  total_streams: number
  enabled_streams: number
  latest_events: Event[]
}
