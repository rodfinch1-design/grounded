import { useEffect, useState } from 'react'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)
export { gsap, ScrollTrigger }

const RM_QUERY = '(prefers-reduced-motion: reduce)'
const MOBILE_QUERY = '(max-width: 767px)'

export function prefersReducedMotion(): boolean {
  return typeof window !== 'undefined' && window.matchMedia(RM_QUERY).matches
}

function useMedia(query: string): boolean {
  const [match, setMatch] = useState(() => typeof window !== 'undefined' && window.matchMedia(query).matches)
  useEffect(() => {
    const mq = window.matchMedia(query)
    const on = () => setMatch(mq.matches)
    on()
    mq.addEventListener('change', on)
    return () => mq.removeEventListener('change', on)
  }, [query])
  return match
}

export const useReducedMotion = () => useMedia(RM_QUERY)
export const useIsMobile = () => useMedia(MOBILE_QUERY)
