import { useLayoutEffect, useRef } from 'react'
import Eyebrow from '../components/Eyebrow'
import Reveal from '../components/Reveal'
import Thumb from '../components/Thumb'
import { steps } from '../lib/data'
import { gsap, ScrollTrigger, prefersReducedMotion } from '../lib/motion'

export default function HowItWorks() {
  const root = useRef<HTMLDivElement>(null)

  // Desktop: pin the section header while the three steps scroll past it.
  useLayoutEffect(() => {
    const el = root.current
    if (!el || prefersReducedMotion()) return
    const mm = gsap.matchMedia()
    mm.add('(min-width: 1024px)', () => {
      ScrollTrigger.create({ trigger: el, start: 'top 96px', end: 'bottom bottom', pin: el.querySelector('[data-pin]'), pinSpacing: false })
    })
    return () => mm.revert()
  }, [])

  return (
    <section id="method" className="section border-t border-line">
      <div ref={root} className="container-x lg:grid lg:grid-cols-12 lg:gap-6">
        <div className="lg:col-span-4">
          <div data-pin className="mb-14 lg:mb-0">
            <Eyebrow>The method</Eyebrow>
            <h2 className="mt-4 text-h1">Three steps. <span className="serif-i font-normal">No séance.</span></h2>
            <p className="mt-4 max-w-sm text-ink-2">The templates are built so an AI editor has the vocabulary to extend them without inventing a second design system.</p>
          </div>
        </div>
        <ol className="space-y-24 lg:col-span-8 lg:space-y-40">
          {steps.map((s, i) => {
            const flip = i % 2 === 1
            return (
              <li key={s.n}>
                <Reveal className={`grid items-center gap-8 md:grid-cols-2 ${flip ? 'md:[&>*:first-child]:order-2' : ''}`}>
                  <div>
                    <span className="font-mono text-mono text-lime">{s.n}</span>
                    <h3 className="mt-3 text-h2 font-medium">{s.title}</h3>
                    <p className="mt-4 text-ink-2">{s.body}</p>
                  </div>
                  <div className="glass p-3"><Thumb hue={s.hue} label={`Step ${s.n}`} /></div>
                </Reveal>
              </li>
            )
          })}
        </ol>
      </div>
    </section>
  )
}
