import { useId, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'

type Item = { q: string; a: string }

export default function Accordion({ items }: { items: Item[] }) {
  const [open, setOpen] = useState<number | null>(0)
  const base = useId()
  return (
    <div className="divide-y divide-line border-y border-line">
      {items.map((item, i) => {
        const isOpen = open === i
        const panelId = `${base}-panel-${i}`
        const btnId = `${base}-btn-${i}`
        return (
          <div key={i} className={`transition-[border-color,padding] duration-300 ease-out border-l-2 ${isOpen ? 'border-l-lime pl-5' : 'border-l-transparent pl-0'}`}>
            <h3>
              <button id={btnId} aria-expanded={isOpen} aria-controls={panelId} onClick={() => setOpen(isOpen ? null : i)}
                className="flex w-full items-center justify-between gap-6 py-5 text-left text-[18px] font-medium text-ink">
                <span>{item.q}</span>
                <span aria-hidden="true" className={`shrink-0 text-ink-2 transition-transform duration-300 ${isOpen ? 'rotate-45' : ''}`}>+</span>
              </button>
            </h3>
            <AnimatePresence initial={false}>
              {isOpen && (
                <motion.div id={panelId} role="region" aria-labelledby={btnId} key="panel"
                  initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }} className="overflow-hidden">
                  <p className="pb-6 pr-10 text-body text-ink-2">{item.a}</p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )
      })}
    </div>
  )
}
