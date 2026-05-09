import { CrowdChart } from '@/components/Analytics/CrowdChart'
import { EventLog } from '@/components/Analytics/EventLog'

export function AnalyticsPage() {
  return (
    <div className="p-4 space-y-4">
      <h2 className="text-base font-semibold text-white">Analitik Kerumunan</h2>
      <CrowdChart />
      <EventLog compact />
    </div>
  )
}
