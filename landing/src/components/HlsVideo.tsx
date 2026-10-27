import { useEffect, useRef } from 'react'
import { prefersReducedMotion } from '../lib/motion'

/** Background video via hls.js, native HLS on Safari. Falls back to a still gradient if the stream is unavailable. */
export default function HlsVideo({ src, className = '' }: { src: string; className?: string }) {
  const ref = useRef<HTMLVideoElement>(null)
  useEffect(() => {
    const video = ref.current
    if (!video || prefersReducedMotion()) return
    let destroy = () => {}
    if (video.canPlayType('application/vnd.apple.mpegurl')) {
      video.src = src
      video.play().catch(() => {})
    } else {
      import('hls.js').then(({ default: Hls }) => {
        if (!Hls.isSupported()) return
        const hls = new Hls({ capLevelToPlayerSize: true, startLevel: 0 })
        hls.loadSource(src)
        hls.attachMedia(video)
        hls.on(Hls.Events.MANIFEST_PARSED, () => video.play().catch(() => {}))
        destroy = () => hls.destroy()
      })
    }
    return () => destroy()
  }, [src])
  return (
    <video ref={ref} muted loop playsInline autoPlay aria-hidden="true" tabIndex={-1}
      className={`h-full w-full object-cover ${className}`} />
  )
}
