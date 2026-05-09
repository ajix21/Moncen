import { useEffect, useState } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { eventsApi } from '@/lib/api'
import { useCCTVStore } from '@/store/cctvStore'
import type { Event } from '@/types'

interface DataPoint {
  time: string
  [key: string]: number | string
}

const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#f97316']

export function CrowdChart() {
  const [data, setData] = useState<DataPoint[]>([])
  const streams = useCCTVStore((s) => s.streams)

  useEffect(() => {
    const load = async () => {
      const page = await eventsApi.list({ limit: 200 })
      const events: Event[] = page.items

      const buckets: Record<string, DataPoint> = {}
      for (const e of events) {
        const t = new Date(e.timestamp)
        const key = `${t.getHours()}:${String(t.getMinutes()).padStart(2, '0')}`
        if (!buckets[key]) buckets[key] = { time: key }
        const existing = (buckets[key][e.cctv_name] as number) ?? 0
        buckets[key][e.cctv_name] = Math.max(existing, e.person_count)
      }

      setData(Object.values(buckets).slice(-30))
    }

    load()
    const t = setInterval(load, 30_000)
    return () => clearInterval(t)
  }, [])

  const names = [...new Set(streams.map((s) => s.name))]

  return (
    <div className="bg-navy-900 border border-navy-700 rounded-xl p-4">
      <h3 className="text-sm font-semibold text-white mb-4">Tren Kerumunan (30 data terakhir)</h3>
      {data.length === 0 ? (
        <div className="h-48 flex items-center justify-center text-slate-600 text-sm font-mono">
          Belum ada data analisis
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e3a5f" />
            <XAxis dataKey="time" stroke="#475569" tick={{ fontSize: 11 }} />
            <YAxis stroke="#475569" tick={{ fontSize: 11 }} />
            <Tooltip
              contentStyle={{
                background: '#0f1729',
                border: '1px solid #1e3a5f',
                borderRadius: 8,
                fontSize: 12,
              }}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            {names.map((name, i) => (
              <Line
                key={name}
                type="monotone"
                dataKey={name}
                stroke={COLORS[i % COLORS.length]}
                strokeWidth={2}
                dot={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
