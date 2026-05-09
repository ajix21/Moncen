import { useCVStore } from '@/store/cvStore'
import { useAlertStore } from '@/store/alertStore'
import { HLSPlayer } from '@/components/VideoPlayer/HLSPlayer'
import { VideoOverlay } from '@/components/VideoPlayer/VideoOverlay'
import { alertLevelBadgeClass, formatTimestamp } from '@/lib/utils'
import type { CCTVStream } from '@/types'
import { MapPin } from 'lucide-react'

interface CCTVCardProps {
  stream: CCTVStream
}

export function CCTVCard({ stream }: CCTVCardProps) {
  const cvRunning = useCVStore((s) => s.running)
  const alert = useAlertStore((s) => s.alerts[stream.id])

  const showCV = cvRunning && !!alert
  const personCount = showCV ? alert.person_count : null
  const alertLevel = showCV ? alert.alert_level : null
  const alertColor = showCV ? alert.alert_color : '#64748b'
  const cvStatus = alert?.cv_status ?? 'offline'

  const boundingBoxes: [number, number, number, number][] =
    showCV && alert.bounding_boxes ? alert.bounding_boxes : []

  return (
    <div className="bg-navy-900 rounded-xl border border-navy-700 overflow-hidden flex flex-col">
      {/* Video + Overlay */}
      <div className="relative aspect-video bg-navy-950">
        {stream.enabled ? (
          <>
            <HLSPlayer url={stream.stream_url} className="w-full h-full" />
            <VideoOverlay
              boxes={boundingBoxes}
              frameWidth={1280}
              frameHeight={720}
              alertColor={alertColor}
              visible={showCV && cvStatus === 'analyzing' && boundingBoxes.length > 0}
            />
          </>
        ) : (
          <div className="w-full h-full flex items-center justify-center text-slate-600">
            <span className="text-xs font-mono uppercase tracking-widest">Stream Dinonaktifkan</span>
          </div>
        )}

        {/* Top-right badge */}
        <div className="absolute top-2 right-2">
          {!cvRunning ? (
            <span className="text-[10px] font-mono bg-slate-700/80 text-slate-400 px-2 py-0.5 rounded border border-slate-600/50">
              CV OFFLINE
            </span>
          ) : alertLevel ? (
            <span
              className={`text-[10px] font-mono px-2 py-0.5 rounded border ${alertLevelBadgeClass(alertLevel)}`}
            >
              {alertLevel}
            </span>
          ) : (
            <span className="text-[10px] font-mono bg-slate-700/80 text-slate-400 px-2 py-0.5 rounded border border-slate-600/50">
              {cvStatus === 'queued' ? 'ANTRIAN' : 'MENUNGGU'}
            </span>
          )}
        </div>

        {/* Person count overlay */}
        <div className="absolute bottom-2 left-2">
          {!cvRunning ? (
            <span className="text-slate-500 text-xs font-mono">
              {alert
                ? `Terakhir: ${alert.person_count} orang, ${formatTimestamp(alert.timestamp)}`
                : '--'}
            </span>
          ) : (
            <span
              className="text-2xl font-bold font-mono"
              style={{ color: alertColor, textShadow: `0 0 8px ${alertColor}55` }}
            >
              {personCount !== null ? personCount : '--'}
              {personCount !== null && (
                <span className="text-xs font-normal text-slate-400 ml-1">orang</span>
              )}
            </span>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="px-3 py-2 flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold text-white">{stream.name}</p>
          <div className="flex items-center gap-1 text-slate-500 text-xs mt-0.5">
            <MapPin className="w-3 h-3" />
            <span>{stream.location}</span>
          </div>
        </div>

        {cvRunning && cvStatus === 'queued' && (
          <span className="text-[10px] font-mono text-cv-queued bg-cv-queued/10 border border-cv-queued/30 px-2 py-0.5 rounded">
            ANTRIAN
          </span>
        )}
      </div>
    </div>
  )
}
