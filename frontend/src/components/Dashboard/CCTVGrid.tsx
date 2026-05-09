import { useCCTVStore } from '@/store/cctvStore'
import { CCTVCard } from './CCTVCard'
import { VideoIcon } from 'lucide-react'

export function CCTVGrid() {
  const { streams, loading } = useCCTVStore()
  const enabled = streams.filter((s) => s.enabled)

  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-2 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-navy-900 rounded-xl border border-navy-700 aspect-video animate-pulse" />
        ))}
      </div>
    )
  }

  if (enabled.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-slate-600 gap-3">
        <VideoIcon className="w-12 h-12" />
        <p className="text-sm font-mono">Tidak ada stream aktif</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-2 gap-4">
      {enabled.map((s) => (
        <CCTVCard key={s.id} stream={s} />
      ))}
    </div>
  )
}
