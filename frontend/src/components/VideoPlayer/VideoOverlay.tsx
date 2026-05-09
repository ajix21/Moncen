import { useEffect, useRef } from 'react'

interface BoundingBox {
  x1: number
  y1: number
  x2: number
  y2: number
}

interface VideoOverlayProps {
  boxes: [number, number, number, number][]
  frameWidth: number
  frameHeight: number
  alertColor: string
  visible: boolean
}

export function VideoOverlay({ boxes, frameWidth, frameHeight, alertColor, visible }: VideoOverlayProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    ctx.clearRect(0, 0, canvas.width, canvas.height)
    if (!visible || boxes.length === 0) return

    const scaleX = canvas.width / (frameWidth || 1)
    const scaleY = canvas.height / (frameHeight || 1)

    ctx.strokeStyle = alertColor
    ctx.lineWidth = 1.5
    ctx.shadowColor = alertColor
    ctx.shadowBlur = 4

    for (const [x1, y1, x2, y2] of boxes) {
      const rx = x1 * scaleX
      const ry = y1 * scaleY
      const rw = (x2 - x1) * scaleX
      const rh = (y2 - y1) * scaleY
      ctx.strokeRect(rx, ry, rw, rh)
    }
  }, [boxes, frameWidth, frameHeight, alertColor, visible])

  if (!visible) return null

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 w-full h-full pointer-events-none"
      style={{ mixBlendMode: 'screen' }}
    />
  )
}
