import { useCVStore } from '@/store/cvStore'
import { formatDuration } from '@/lib/utils'
import { useCVEngine } from '@/hooks/useCVEngine'

interface CVEnginePanelProps {
  compact?: boolean
}

export function CVEnginePanel({ compact = false }: CVEnginePanelProps) {
  useCVEngine()
  const { running, streamsActive, uptimeSeconds } = useCVStore()

  if (compact) {
    return (
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div
            className={`w-2.5 h-2.5 rounded-full ${
              running ? 'bg-cv-online animate-pulse' : 'bg-cv-offline'
            }`}
          />
          <span className={`text-xs font-mono ${running ? 'text-cv-online' : 'text-cv-offline'}`}>
            {running ? `CV AKTIF — ${streamsActive} stream` : 'CV NONAKTIF'}
          </span>
        </div>
        {running && (
          <span className="text-xs text-slate-500 font-mono">{formatDuration(uptimeSeconds)}</span>
        )}
      </div>
    )
  }

  return (
    <div
      className={`rounded-xl border p-4 ${
        running
          ? 'bg-navy-900 border-cv-online/30'
          : 'bg-navy-900 border-navy-700'
      }`}
    >
      <div className="flex items-center gap-3 mb-3">
        <div
          className={`w-4 h-4 rounded-full ${
            running ? 'bg-cv-online animate-pulse' : 'bg-cv-offline'
          }`}
        />
        <div>
          <p className={`text-sm font-semibold ${running ? 'text-cv-online' : 'text-slate-400'}`}>
            Analisis Massa: {running ? 'AKTIF' : 'NONAKTIF'}
          </p>
          {running && (
            <p className="text-xs text-slate-500 font-mono">
              Aktif {formatDuration(uptimeSeconds)} — {streamsActive} stream diproses
            </p>
          )}
        </div>
      </div>

      <p className="text-xs text-slate-500 mt-2">
        {running
          ? 'CV Engine berjalan. Gunakan stop-cv.sh untuk mematikan.'
          : 'Jalankan ./start-cv.sh untuk mengaktifkan analisis kerumunan.'}
      </p>
    </div>
  )
}
