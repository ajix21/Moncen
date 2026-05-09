import { useEffect, useRef, useState } from 'react'
import Hls from 'hls.js'

interface HLSPlayerProps {
  url: string
  className?: string
  onReady?: () => void
}

export function HLSPlayer({ url, className = '', onReady }: HLSPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const hlsRef = useRef<Hls | null>(null)
  const [status, setStatus] = useState<'loading' | 'playing' | 'error'>('loading')
  const retryCount = useRef(0)
  const MAX_RETRIES = 10

  useEffect(() => {
    const video = videoRef.current
    if (!video || !url) return

    retryCount.current = 0
    setStatus('loading')

    const attach = () => {
      if (hlsRef.current) {
        hlsRef.current.destroy()
        hlsRef.current = null
      }

      if (Hls.isSupported()) {
        const hls = new Hls({
          lowLatencyMode: true,
          enableWorker: true,
          backBufferLength: 30,
        })
        hlsRef.current = hls

        video.muted = true
        hls.loadSource(url)
        hls.attachMedia(video)

        hls.on(Hls.Events.MANIFEST_PARSED, () => {
          video.play().catch(() => {})
          setStatus('playing')
          onReady?.()
        })

        hls.on(Hls.Events.ERROR, (_e, data) => {
          if (data.fatal) {
            if (retryCount.current < MAX_RETRIES) {
              retryCount.current++
              setTimeout(attach, 5000)
            } else {
              setStatus('error')
            }
          }
        })
      } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
        video.muted = true
        video.src = url
        video.addEventListener('loadedmetadata', () => {
          video.play().catch(() => {})
          setStatus('playing')
          onReady?.()
        })
        video.addEventListener('error', () => {
          if (retryCount.current < MAX_RETRIES) {
            retryCount.current++
            setTimeout(attach, 5000)
          } else {
            setStatus('error')
          }
        })
      }
    }

    attach()

    return () => {
      if (hlsRef.current) {
        hlsRef.current.destroy()
        hlsRef.current = null
      }
    }
  }, [url])

  return (
    <div className={`relative bg-navy-950 ${className}`}>
      <video
        ref={videoRef}
        className="w-full h-full object-cover"
        muted
        playsInline
        autoPlay
      />

      {status === 'loading' && (
        <div className="absolute inset-0 flex items-center justify-center bg-navy-950/80">
          <div className="flex flex-col items-center gap-2">
            <div className="w-8 h-8 border-2 border-cv-online border-t-transparent rounded-full animate-spin" />
            <span className="text-xs text-slate-400 font-mono">Menghubungkan stream...</span>
          </div>
        </div>
      )}

      {status === 'error' && (
        <div className="absolute inset-0 flex items-center justify-center bg-navy-950">
          <div className="flex flex-col items-center gap-2 text-slate-500">
            <div className="w-12 h-12 rounded-full border-2 border-slate-700 flex items-center justify-center">
              <span className="text-xl">!</span>
            </div>
            <span className="text-xs font-mono uppercase tracking-widest">STREAM OFFLINE</span>
          </div>
        </div>
      )}
    </div>
  )
}
