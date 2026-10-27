import { useMemo } from 'react'
import { useIsMobile, useReducedMotion } from '../lib/motion'

/** Subtle drifting particle layer. CSS-only, disabled on mobile and for reduced motion. */
export default function Dust({ count = 28 }: { count?: number }) {
  const reduced = useReducedMotion()
  const mobile = useIsMobile()
  const dots = useMemo(() => Array.from({ length: count }, (_, i) => ({
    left: (i * 37) % 100, size: 1 + ((i * 7) % 3), dur: 18 + ((i * 11) % 20), delay: -((i * 5) % 20), op: 0.15 + ((i * 3) % 5) / 20,
  })), [count])
  if (reduced || mobile) return null
  return (
    <div aria-hidden="true" className="pointer-events-none absolute inset-0 overflow-hidden">
      {dots.map((d, i) => (
        <span key={i} className="absolute bottom-[-10px] rounded-full bg-ink"
          style={{ left: `${d.left}%`, width: d.size, height: d.size, opacity: d.op, animation: `drift ${d.dur}s linear ${d.delay}s infinite` }} />
      ))}
    </div>
  )
}
