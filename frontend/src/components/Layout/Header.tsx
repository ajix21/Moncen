import { Eye } from 'lucide-react'
import { CVEnginePanel } from '@/components/Dashboard/CVEnginePanel'

export function Header() {
  return (
    <header className="h-14 bg-navy-900 border-b border-navy-700 flex items-center justify-between px-4 shrink-0 z-20">
      <div className="flex items-center gap-2">
        <Eye className="w-5 h-5 text-cv-online" />
        <span className="font-bold text-white text-sm tracking-wide">SEMAR WATCH</span>
        <span className="text-navy-700 mx-1">|</span>
        <span className="text-slate-400 text-xs font-mono">v2.0 — Split Service</span>
      </div>

      <CVEnginePanel compact />
    </header>
  )
}
