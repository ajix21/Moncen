import { NavLink } from 'react-router-dom'
import { LayoutDashboard, BarChart2, List, Settings } from 'lucide-react'

const NAV = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/analytics', icon: BarChart2, label: 'Analitik' },
  { to: '/events', icon: List, label: 'Event Log' },
  { to: '/settings', icon: Settings, label: 'Pengaturan' },
]

export function Sidebar() {
  return (
    <aside className="w-14 bg-navy-900 border-r border-navy-700 flex flex-col items-center py-4 gap-2 shrink-0">
      {NAV.map(({ to, icon: Icon, label }) => (
        <NavLink
          key={to}
          to={to}
          end={to === '/'}
          title={label}
          className={({ isActive }) =>
            `w-10 h-10 rounded-lg flex items-center justify-center transition-colors ${
              isActive
                ? 'bg-navy-800 text-cv-online'
                : 'text-slate-500 hover:text-slate-300 hover:bg-navy-800'
            }`
          }
        >
          <Icon className="w-5 h-5" />
        </NavLink>
      ))}
    </aside>
  )
}
