import { useEffect, useRef } from 'react'
import { useCVStore } from '@/store/cvStore'
import { useAlertStore } from '@/store/alertStore'
import { useWebSocket } from '@/hooks/useWebSocket'
import { cvApi } from '@/lib/api'
import type { CVResult } from '@/types'

export function useCVEngine() {
  const { running, setStatus, setOffline } = useCVStore()
  const updateAlert = useAlertStore((s) => s.updateAlert)
  const prevRunningRef = useRef<boolean | null>(null)

  useEffect(() => {
    let cancelled = false

    const poll = async () => {
      try {
        const status = await cvApi.status()
        if (!cancelled) setStatus(status)
      } catch {
        if (!cancelled) setOffline()
      }
    }

    poll()
    const interval = setInterval(poll, 10_000)
    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [setStatus, setOffline])

  useEffect(() => {
    if (prevRunningRef.current === null) {
      prevRunningRef.current = running
      return
    }
    if (!running && prevRunningRef.current) {
      showToast('CV Engine mati — mode monitoring saja', 'warning')
    } else if (running && !prevRunningRef.current) {
      showToast('CV Engine aktif', 'success')
    }
    prevRunningRef.current = running
  }, [running])

  useWebSocket('/ws/cv/all', {
    enabled: running,
    onMessage: (data) => {
      const result = data as CVResult
      if (result.type === 'cv_result') {
        updateAlert(result)
      }
    },
  })

  return { running }
}

function showToast(message: string, type: 'success' | 'warning') {
  const el = document.createElement('div')
  el.textContent = message
  el.style.cssText = `
    position: fixed; bottom: 24px; right: 24px; z-index: 9999;
    padding: 12px 20px; border-radius: 8px; font-size: 14px;
    font-family: monospace; font-weight: 500;
    background: ${type === 'success' ? '#10b98133' : '#f59e0b33'};
    color: ${type === 'success' ? '#10b981' : '#f59e0b'};
    border: 1px solid ${type === 'success' ? '#10b98155' : '#f59e0b55'};
    backdrop-filter: blur(8px);
    transition: opacity 0.3s ease;
  `
  document.body.appendChild(el)
  setTimeout(() => {
    el.style.opacity = '0'
    setTimeout(() => el.remove(), 300)
  }, 3000)
}
