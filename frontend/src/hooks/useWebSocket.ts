import { useEffect, useRef, useCallback } from 'react'

interface UseWebSocketOptions {
  onMessage: (data: unknown) => void
  onOpen?: () => void
  onClose?: () => void
  enabled?: boolean
  reconnectDelay?: number
  maxRetries?: number
}

export function useWebSocket(url: string, options: UseWebSocketOptions) {
  const {
    onMessage,
    onOpen,
    onClose,
    enabled = true,
    reconnectDelay = 5000,
    maxRetries = 10,
  } = options

  const wsRef = useRef<WebSocket | null>(null)
  const retryCount = useRef(0)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const mountedRef = useRef(true)

  const connect = useCallback(() => {
    if (!mountedRef.current || !enabled) return

    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      retryCount.current = 0
      onOpen?.()
    }

    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        onMessage(data)
      } catch {
        // ignore parse errors
      }
    }

    ws.onclose = () => {
      onClose?.()
      if (!mountedRef.current || !enabled) return
      if (retryCount.current < maxRetries) {
        retryCount.current++
        reconnectTimer.current = setTimeout(connect, reconnectDelay)
      }
    }

    ws.onerror = () => {
      ws.close()
    }
  }, [url, enabled, onMessage, onOpen, onClose, reconnectDelay, maxRetries])

  useEffect(() => {
    mountedRef.current = true
    if (enabled) connect()

    return () => {
      mountedRef.current = false
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
      if (wsRef.current) {
        wsRef.current.onclose = null
        wsRef.current.close()
      }
    }
  }, [connect, enabled])

  const send = useCallback((data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    }
  }, [])

  return { send }
}
