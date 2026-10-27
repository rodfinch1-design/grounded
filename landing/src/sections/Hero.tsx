import { motion } from 'framer-motion'
import Button from '../components/Button'
import Dust from '../components/Dust'
import Eyebrow from '../components/Eyebrow'
import HlsVideo from '../components/HlsVideo'
import { useReducedMotion } from '../lib/motion'

// Public test stream; replace with your own HLS manifest.
const HLS_SRC = 'https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8'

export default function Hero({ ready }: { ready: boolean }) {
  const reduced = useReducedMotion()
  const item = (i: number) => ({
    initial: reduced ? false : { opacity: 0, y: 24 },
    animate: ready ? { opacity: 1, y: 0 } : undefined,
    transition: { duration: 0.8, delay: 0.1 + i * 0.12, ease: [0.16, 1, 0.3, 1] as const },
  })
  return (
    <section id="top" className="relative flex min-h-[100svh] items-center overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(212,255,79,0.10),transparent_60%)]">
        <HlsVideo src={HLS_SRC} />
      </div>
      <div className="absolute inset-0 bg-black/50" />
      <div className="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-obsidian to-transparent" />
      <Dust />
      <div className="container-x relative z-10 py-32 text-center">
        <motion.div {...item(0)}><Eyebrow>Templates · 2026</Eyebrow></motion.div>
        <motion.h1 {...item(1)} className="mx-auto mt-6 max-w-5xl text-h1">
          Ship a site that<br />
          <span className="serif-i font-normal text-display">doesn't feel like AI made it.</span>
        </motion.h1>
        <motion.p {...item(2)} className="mx-auto mt-6 max-w-xl text-[18px] text-ink-2">
          8 premium templates. Cursor / v0 / Lovable ready.
        </motion.p>
        <motion.div {...item(3)} className="mt-10 flex flex-wrap items-center justify-center gap-3">
          <Button href="#templates">Browse templates →</Button>
          <Button href="#method" variant="ghost">See the method</Button>
        </motion.div>
      </div>
    </section>
  )
}
