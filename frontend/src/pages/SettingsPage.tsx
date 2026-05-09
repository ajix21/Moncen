import { CCTVManager } from '@/components/Settings/CCTVManager'
import { ThresholdConfig } from '@/components/Settings/ThresholdConfig'
import { CVSettings } from '@/components/Settings/CVSettings'

export function SettingsPage() {
  return (
    <div className="p-4 space-y-4">
      <h2 className="text-base font-semibold text-white">Pengaturan</h2>
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <div className="space-y-4">
          <CCTVManager />
          <ThresholdConfig />
        </div>
        <div>
          <CVSettings />
        </div>
      </div>
    </div>
  )
}
