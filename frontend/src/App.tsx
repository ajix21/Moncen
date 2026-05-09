import { useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Header } from '@/components/Layout/Header'
import { Sidebar } from '@/components/Layout/Sidebar'
import { useCCTVStore } from '@/store/cctvStore'
import { useCVEngine } from '@/hooks/useCVEngine'

// Pages
import { DashboardPage } from '@/pages/DashboardPage'
import { AnalyticsPage } from '@/pages/AnalyticsPage'
import { EventsPage } from '@/pages/EventsPage'
import { SettingsPage } from '@/pages/SettingsPage'

function AppInner() {
  const fetchStreams = useCCTVStore((s) => s.fetchStreams)

  useEffect(() => {
    fetchStreams()
  }, [fetchStreams])

  useCVEngine()

  return (
    <div className="flex flex-col h-screen bg-navy-950 text-white overflow-hidden">
      <Header />
      {/* min-h-0 prevents flex children from overflowing the column container */}
      <div className="flex flex-1 overflow-hidden min-h-0">
        <Sidebar />
        {/* min-w-0 prevents content wider than remaining space from pushing sidebar */}
        <main className="flex-1 overflow-y-auto min-w-0">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/events" element={<EventsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppInner />
    </BrowserRouter>
  )
}
