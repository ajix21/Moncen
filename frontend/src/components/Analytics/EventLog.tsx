import { useEffect, useState } from 'react'
import { eventsApi } from '@/lib/api'
import type { EventsPage } from '@/types'
import { alertLevelBadgeClass, formatTimestamp } from '@/lib/utils'
import { ChevronLeft, ChevronRight } from 'lucide-react'

interface EventLogProps {
  cctvId?: string
  compact?: boolean
}

export function EventLog({ cctvId, compact = false }: EventLogProps) {
  const [page, setPage] = useState<EventsPage | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const limit = compact ? 10 : 25

  useEffect(() => {
    eventsApi.list({ page: currentPage, limit, cctv_id: cctvId }).then(setPage).catch(() => {})
    const t = setInterval(() => {
      eventsApi.list({ page: currentPage, limit, cctv_id: cctvId }).then(setPage).catch(() => {})
    }, 15_000)
    return () => clearInterval(t)
  }, [currentPage, limit, cctvId])

  if (!page) {
    return (
      <div className="bg-navy-900 border border-navy-700 rounded-xl p-4 animate-pulse h-32" />
    )
  }

  return (
    <div className="bg-navy-900 border border-navy-700 rounded-xl overflow-hidden">
      {!compact && (
        <div className="px-4 py-3 border-b border-navy-700 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white">Event Log</h3>
          <span className="text-xs text-slate-500 font-mono">{page.total} total</span>
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-navy-700 text-slate-500">
              <th className="text-left px-4 py-2 font-medium">Waktu</th>
              <th className="text-left px-4 py-2 font-medium">CCTV</th>
              <th className="text-left px-4 py-2 font-medium">Level</th>
              <th className="text-right px-4 py-2 font-medium">Orang</th>
            </tr>
          </thead>
          <tbody>
            {page.items.length === 0 ? (
              <tr>
                <td colSpan={4} className="text-center py-8 text-slate-600 font-mono">
                  Belum ada event
                </td>
              </tr>
            ) : (
              page.items.map((e) => (
                <tr key={e.id} className="border-b border-navy-800 hover:bg-navy-800/40 transition-colors">
                  <td className="px-4 py-2 text-slate-400 font-mono whitespace-nowrap">
                    {formatTimestamp(e.timestamp)}
                  </td>
                  <td className="px-4 py-2 text-slate-300">{e.cctv_name}</td>
                  <td className="px-4 py-2">
                    <span
                      className={`px-2 py-0.5 rounded border text-[10px] font-mono ${alertLevelBadgeClass(e.alert_level)}`}
                    >
                      {e.alert_level}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-right font-mono text-white">{e.person_count}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {!compact && page.pages > 1 && (
        <div className="px-4 py-3 border-t border-navy-700 flex items-center justify-between">
          <span className="text-xs text-slate-500 font-mono">
            Halaman {currentPage} / {page.pages}
          </span>
          <div className="flex gap-1">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage <= 1}
              className="p-1.5 rounded text-slate-400 hover:text-white hover:bg-navy-800 disabled:opacity-30 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setCurrentPage((p) => Math.min(page.pages, p + 1))}
              disabled={currentPage >= page.pages}
              className="p-1.5 rounded text-slate-400 hover:text-white hover:bg-navy-800 disabled:opacity-30 transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
