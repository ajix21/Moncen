import { EventLog } from '@/components/Analytics/EventLog'
import { eventsApi } from '@/lib/api'

export function EventsPage() {
  const clearAll = async () => {
    if (!confirm('Hapus semua event log?')) return
    await eventsApi.clear()
    window.location.reload()
  }

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-white">Event Log</h2>
        <button
          onClick={clearAll}
          className="text-xs px-3 py-1.5 text-red-400 border border-red-400/30 rounded-lg hover:bg-red-400/10 transition-colors"
        >
          Hapus Semua
        </button>
      </div>
      <EventLog />
    </div>
  )
}
