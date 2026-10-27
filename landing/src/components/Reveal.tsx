import { useLayoutEffect, useRef, type ReactNode } from 'react'
import { gsap, prefersReducedMotion } from '../lib/motion'

type Props = { children: ReactNode; className?: string; stagger?: string; delay?: number; y?: number }

/** Scroll-triggered reveal. Pass `stagger` as a child selector to animate children in sequence. */
export default function Reveal({ children, className = '', stagger, delay = 0, y = 32 }: Props) {
  const ref = useRef<HTMLDivElement>(null)
  useLayoutEffect(() => {
    const el = ref.current
    if (!el || prefersReducedMotion()) return
    const targets = stagger ? el.querySelectorAll(stagger) : el
    const ctx = gsap.context(() => {
      gsap.fromTo(targets, { opacity: 0, y }, {
        opacity: 1, y: 0, duration: 0.9, ease: 'power3.out', delay, stagger: stagger ? 0.08 : 0,
        scrollTrigger: { trigger: el, start: 'top 85%', once: true },
      })
    }, el)
    return () => ctx.revert()
  }, [stagger, delay, y])
  return <div ref={ref} className={className}>{children}</div>
}
