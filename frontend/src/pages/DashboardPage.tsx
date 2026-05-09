import { CCTVGrid } from '@/components/Dashboard/CCTVGrid'
import { StatsOverview } from '@/components/Dashboard/StatsOverview'
import { AlertBanner } from '@/components/Dashboard/AlertBanner'
import { CVEnginePanel } from '@/components/Dashboard/CVEnginePanel'

export function DashboardPage() {
  return (
    <div className="p-4 space-y-4">
      <StatsOverview />
      <AlertBanner />
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-2">
          <CCTVGrid />
        </div>
        <div>
          <CVEnginePanel />
        </div>
      </div>
    </div>
  )
}
