import { useEffect, useState } from 'react'
import { cvApi } from '@/lib/api'
import { useCVStore } from '@/store/cvStore'
import type { CVSettings as CVSettingsType } from '@/types'
import { Info } from 'lucide-react'

const INTERVAL_OPTIONS = [3, 5, 10, 15, 30]
const STREAM_OPTIONS = [1, 2, 3, 4]
const MODEL_OPTIONS = [
  { value: 'yolov8n.pt', label: 'YOLOv8n (Ringan, rekomendasi)' },
  { value: 'yolov8s.pt', label: 'YOLOv8s (Sedang, butuh lebih RAM)' },
]

function estimateResources(interval: number, streams: number, model: string) {
  const baseRam = model.includes('yolov8s') ? 900 : 500
  const ram = baseRam + streams * 150
  const cpuLow = Math.round((100 / interval) * streams * (model.includes('yolov8s') ? 1.5 : 1))
  const cpuHigh = cpuLow + 15
  return { ram, cpuLow: Math.min(cpuLow, 85), cpuHigh: Math.min(cpuHigh, 100) }
}

export function CVSettings() {
  const cvRunning = useCVStore((s) => s.running)
  const [settings, setSettings] = useState<CVSettingsType | null>(null)
  const [dirty, setDirty] = useState<Partial<CVSettingsType>>({})
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (!cvRunning) return
    cvApi.getSettings().then(setSettings).catch(() => {})
  }, [cvRunning])

  const current = { ...settings, ...dirty } as CVSettingsType

  const update = (key: keyof CVSettingsType, value: unknown) => {
    setDirty((d) => ({ ...d, [key]: value }))
    setSaved(false)
  }

  const save = async () => {
    setSaving(true)
    try {
      const result = await cvApi.updateSettings(dirty)
      setSettings(result.settings)
      setDirty({})
      setSaved(true)
    } finally {
      setSaving(false)
    }
  }

  const estimate = settings
    ? estimateResources(
        current.cv_frame_interval ?? 5,
        current.max_concurrent_streams ?? 2,
        current.yolo_model_name ?? 'yolov8n.pt',
      )
    : null

  if (!cvRunning) {
    return (
      <div className="bg-navy-900 border border-navy-700 rounded-xl p-4">
        <h3 className="text-sm font-semibold text-white mb-2">Pengaturan CV Engine (Hemat Daya)</h3>
        <p className="text-xs text-slate-500">CV Engine tidak aktif. Jalankan ./start-cv.sh terlebih dahulu.</p>
      </div>
    )
  }

  return (
    <div className="bg-navy-900 border border-navy-700 rounded-xl p-4 space-y-4">
      <h3 className="text-sm font-semibold text-white">Pengaturan CV Engine (Hemat Daya)</h3>

      {/* Interval */}
      <div className="space-y-2">
        <label className="text-xs text-slate-400">
          Interval analisis — Proses 1 frame setiap{' '}
          <span className="text-white font-mono">{current.cv_frame_interval ?? 5}s</span>
        </label>
        <div className="flex gap-2 flex-wrap">
          {INTERVAL_OPTIONS.map((v) => (
            <button
              key={v}
              onClick={() => update('cv_frame_interval', v)}
              className={`px-3 py-1.5 rounded text-xs font-mono border transition-colors ${
                (current.cv_frame_interval ?? 5) === v
                  ? 'bg-cv-online text-navy-950 border-cv-online font-semibold'
                  : 'bg-navy-950 text-slate-400 border-navy-700 hover:border-cv-online/50'
              }`}
            >
              {v}s
            </button>
          ))}
        </div>
      </div>

      {/* Concurrent streams */}
      <div className="space-y-2">
        <label className="text-xs text-slate-400">Stream diproses bersamaan</label>
        <div className="flex gap-2">
          {STREAM_OPTIONS.map((v) => (
            <button
              key={v}
              onClick={() => update('max_concurrent_streams', v)}
              className={`px-3 py-1.5 rounded text-xs font-mono border transition-colors ${
                (current.max_concurrent_streams ?? 2) === v
                  ? 'bg-cv-online text-navy-950 border-cv-online font-semibold'
                  : 'bg-navy-950 text-slate-400 border-navy-700 hover:border-cv-online/50'
              }`}
            >
              {v}
            </button>
          ))}
        </div>
        {(current.max_concurrent_streams ?? 2) > 2 && (
          <p className="text-xs text-amber-400 flex items-center gap-1">
            <Info className="w-3 h-3" />
            Membutuhkan lebih banyak CPU dan RAM
          </p>
        )}
      </div>

      {/* Model */}
      <div className="space-y-2">
        <label className="text-xs text-slate-400">Model YOLO</label>
        <select
          value={current.yolo_model_name ?? 'yolov8n.pt'}
          onChange={(e) => update('yolo_model_name', e.target.value)}
          className="w-full bg-navy-950 border border-navy-700 rounded px-3 py-1.5 text-xs text-white focus:outline-none focus:border-cv-online/50"
        >
          {MODEL_OPTIONS.map(({ value, label }) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </div>

      {/* Auto rotation */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-slate-300">Rotasi stream otomatis</p>
          <p className="text-xs text-slate-500">
            Jika stream &gt; batas, CV bergantian memproses tiap{' '}
            {current.rotation_interval ?? 60}s
          </p>
        </div>
        <div className="w-8 h-4 bg-cv-online rounded-full relative cursor-default">
          <div className="absolute right-0.5 top-0.5 w-3 h-3 bg-white rounded-full" />
        </div>
      </div>

      {/* Resource estimate */}
      {estimate && (
        <div className="bg-navy-950 border border-navy-800 rounded-lg px-3 py-2 text-xs font-mono text-slate-400 flex gap-4">
          <span>Estimasi RAM: ~{estimate.ram} MB</span>
          <span>Estimasi CPU: {estimate.cpuLow}–{estimate.cpuHigh}%</span>
        </div>
      )}

      {/* Save */}
      <button
        onClick={save}
        disabled={saving || Object.keys(dirty).length === 0}
        className="w-full py-2 rounded-lg text-xs font-semibold bg-cv-online text-navy-950 hover:bg-cv-online/90 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        {saving ? 'Menyimpan...' : saved ? 'Tersimpan!' : 'Simpan & Terapkan'}
      </button>
    </div>
  )
}
