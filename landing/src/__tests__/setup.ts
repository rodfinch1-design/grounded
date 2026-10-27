import '@testing-library/jest-dom/vitest'
import { vi } from 'vitest'

// jsdom lacks these browser APIs that GSAP, Framer Motion and the media hooks rely on.
export const mediaState = { reduced: false, mobile: false }

Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: query.includes('prefers-reduced-motion') ? mediaState.reduced : query.includes('max-width') ? mediaState.mobile : false,
    media: query,
    onchange: null,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    addListener: vi.fn(),
    removeListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

class RO { observe() {} unobserve() {} disconnect() {} }
;(globalThis as unknown as { ResizeObserver: typeof RO }).ResizeObserver = RO
class IO { observe() {} unobserve() {} disconnect() {} takeRecords() { return [] } root = null; rootMargin = ''; thresholds = [] }
;(globalThis as unknown as { IntersectionObserver: typeof IO }).IntersectionObserver = IO

HTMLMediaElement.prototype.play = vi.fn().mockResolvedValue(undefined)
HTMLMediaElement.prototype.pause = vi.fn()
HTMLMediaElement.prototype.canPlayType = vi.fn().mockReturnValue('')
