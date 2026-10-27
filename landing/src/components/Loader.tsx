import { AnimatePresence, motion } from 'framer-motion'
import { useEffect, useState } from 'react'
import { prefersReducedMotion } from '../lib/motion'

export default function Loader({ onDone }: { onDone: () => void }) {
  const [show, setShow] = useState(true)
  useEffect(() => {
    const t = setTimeout(() => setShow(false), prefersReducedMotion() ? 300 : 3000)
    return () => clearTimeout(t)
  }, [])
  return (
    <AnimatePresence onExitComplete={onDone}>
      {show && (
        <motion.div key="loader" role="status" aria-label="Loading" exit={{ opacity: 0 }} transition={{ duration: 0.7, ease: 'easeOut' }}
          className="fixed inset-0 z-[100] grid place-items-center bg-obsidian">
          <div className="text-center">
            <span className="serif-i block text-[clamp(72px,12vw,140px)] leading-none bg-clip-text text-transparent animate-shimmer bg-[length:200%_100%]"
              style={{ backgroundImage: 'linear-gradient(90deg, rgba(250,250,250,.25) 0%, #FAFAFA 45%, #D4FF4F 50%, #FAFAFA 55%, rgba(250,250,250,.25) 100%)' }}>
              H
            </span>
            <span className="eyebrow mt-4 block">Hyliox</span>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
