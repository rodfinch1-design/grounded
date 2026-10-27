import { motion } from 'framer-motion'
import type { ComponentProps } from 'react'

type Props = ComponentProps<typeof motion.a> & { variant?: 'primary' | 'ghost' }

const base = 'inline-flex items-center justify-center gap-2 rounded-full px-6 py-3 text-[15px] font-medium transition-colors duration-200'
const styles = {
  primary: 'bg-lime text-obsidian hover:bg-[#E2FF7A]',
  ghost: 'border border-white/15 text-ink hover:border-white/40 hover:bg-white/[0.04]',
}

export default function Button({ variant = 'primary', className = '', children, ...rest }: Props) {
  return (
    <motion.a whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} transition={{ type: 'spring', stiffness: 400, damping: 25 }}
      className={`${base} ${styles[variant]} ${className}`} {...rest}>
      {children}
    </motion.a>
  )
}
