import { useAlertStore } from '@/store/alertStore'
import { useCVStore } from '@/store/cvStore'
import { alertLevelColor } from '@/lib/utils'
import { AlertTriangle } from 'lucide-react'

export function AlertBanner() {
  const { highestLevel, alerts } = useAlertStore()
  const cvRunning = useCVStore((s) => s.running)

  if (!cvRunning || highestLevel === 'NORMAL') return null

  const color = alertLevelColor(highestLevel)
  const affected = Object.values(alerts).filter((a) => a.alert_level === highestLevel)

  return (
    <div
      className="rounded-xl border px-4 py-3 flex items-center gap-3"
      style={{
        backgroundColor: `${color}15`,
        borderColor: `${color}40`,
      }}
    >
      <AlertTriangle className="w-5 h-5 shrink-0" style={{ color }} />
      <div>
        <p className="text-sm font-semibold" style={{ color }}>
          LEVEL {highestLevel}
        </p>
        <p className="text-xs text-slate-400">
          {affected.map((a) => `${a.cctv_name} (${a.person_count} orang)`).join(' · ')}
        </p>
      </div>
    </div>
  )
}
