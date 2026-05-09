import { ALERT_LEVELS } from '@/lib/constants'

const LEVELS = [
  { key: 'NORMAL', label: 'Normal', range: '0 – 49 orang', color: '#10b981' },
  { key: 'WASPADA', label: 'Waspada', range: '50 – 199 orang', color: '#f59e0b' },
  { key: 'SIAGA', label: 'Siaga', range: '200 – 999 orang', color: '#f97316' },
  { key: 'DARURAT', label: 'Darurat', range: '≥ 1000 orang', color: '#ef4444' },
]

export function ThresholdConfig() {
  return (
    <div className="bg-navy-900 border border-navy-700 rounded-xl p-4 space-y-3">
      <h3 className="text-sm font-semibold text-white">Ambang Batas Alert</h3>
      <p className="text-xs text-slate-500">Konfigurasi level alert berdasarkan jumlah orang yang terdeteksi.</p>
      <div className="space-y-2">
        {LEVELS.map(({ key, label, range, color }) => (
          <div
            key={key}
            className="flex items-center gap-3 p-2.5 rounded-lg border"
            style={{ borderColor: `${color}30`, backgroundColor: `${color}08` }}
          >
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
            <div className="flex-1">
              <p className="text-sm font-medium text-white">{label}</p>
              <p className="text-xs text-slate-400">{range}</p>
            </div>
            <span
              className="text-[10px] font-mono px-2 py-0.5 rounded"
              style={{ backgroundColor: `${color}20`, color }}
            >
              {key}
            </span>
          </div>
        ))}
      </div>
      <p className="text-xs text-slate-600">Threshold dikonfigurasi di cv-engine/config.py · ALERT_LEVELS</p>
    </div>
  )
}
