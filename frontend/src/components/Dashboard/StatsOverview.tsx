import { useEffect, useState } from 'react'
import { statsApi } from '@/lib/api'
import { useAlertStore } from '@/store/alertStore'
import { useCCTVStore } from '@/store/cctvStore'
import type { StatsSummary } from '@/types'
import { Users, Video, AlertTriangle, Activity } from 'lucide-react'

export function StatsOverview() {
  const [summary, setSummary] = useState<StatsSummary | null>(null)
  const alerts = useAlertStore((s) => s.alerts)
  const streams = useCCTVStore((s) => s.streams)

  useEffect(() => {
    statsApi.summary().then(setSummary).catch(() => {})
    const t = setInterval(() => statsApi.summary().then(setSummary).catch(() => {}), 30_000)
    return () => clearInterval(t)
  }, [])

  const totalPeople = Object.values(alerts).reduce((sum, a) => sum + a.person_count, 0)
  const activeStreams = streams.filter((s) => s.enabled).length

  const stats = [
    {
      label: 'Total Orang',
      value: totalPeople,
      icon: Users,
      color: 'text-cv-online',
      bg: 'bg-cv-online/10',
    },
    {
      label: 'Stream Aktif',
      value: activeStreams,
      icon: Video,
      color: 'text-cv-queued',
      bg: 'bg-cv-queued/10',
    },
    {
      label: 'Alert Waspada+',
      value: summary
        ? (summary.level_counts.waspada ?? 0) +
          (summary.level_counts.siaga ?? 0) +
          (summary.level_counts.darurat ?? 0)
        : '--',
      icon: AlertTriangle,
      color: 'text-alert-waspada',
      bg: 'bg-alert-waspada/10',
    },
    {
      label: 'Total Event',
      value: summary?.total_events ?? '--',
      icon: Activity,
      color: 'text-slate-300',
      bg: 'bg-navy-800',
    },
  ]

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {stats.map(({ label, value, icon: Icon, color, bg }) => (
        <div key={label} className="bg-navy-900 border border-navy-700 rounded-xl p-4 flex items-center gap-3">
          <div className={`${bg} rounded-lg p-2.5`}>
            <Icon className={`w-5 h-5 ${color}`} />
          </div>
          <div>
            <p className="text-2xl font-bold text-white font-mono">{value}</p>
            <p className="text-xs text-slate-500">{label}</p>
          </div>
        </div>
      ))}
    </div>
  )
}
