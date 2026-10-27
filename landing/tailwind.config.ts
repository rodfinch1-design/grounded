import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        obsidian: '#0A0A0A',
        lime: '#D4FF4F',
        ink: '#FAFAFA',
        'ink-2': 'rgba(250,250,250,0.64)',
        line: 'rgba(255,255,255,0.06)',
        surface: 'rgba(255,255,255,0.03)',
        glass: 'rgba(255,255,255,0.04)',
      },
      fontFamily: {
        sans: ['Geist', 'Inter', 'system-ui', 'sans-serif'],
        display: ['"Instrument Serif"', 'Georgia', 'serif'],
        mono: ['"Geist Mono"', '"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      fontSize: {
        display: ['clamp(48px, 7vw, 88px)', { lineHeight: '1.02', letterSpacing: '-0.02em' }],
        h1: ['clamp(36px, 5vw, 64px)', { lineHeight: '1.05', letterSpacing: '-0.02em' }],
        h2: ['clamp(24px, 3vw, 32px)', { lineHeight: '1.15', letterSpacing: '-0.01em' }],
        h3: ['clamp(20px, 2.5vw, 28px)', { lineHeight: '1.2' }],
        body: ['16px', { lineHeight: '1.6' }],
        mono: ['13px', { lineHeight: '1.7' }],
      },
      letterSpacing: { eyebrow: '0.4em' },
      borderRadius: { DEFAULT: '16px', card: '16px' },
      maxWidth: { content: '1280px' },
      spacing: { section: 'clamp(80px, 10vw, 160px)' },
      backdropBlur: { xl: '24px' },
      boxShadow: {
        glow: '0 0 0 1px rgba(212,255,79,0.5), 0 0 60px -10px rgba(212,255,79,0.35)',
        lift: '0 24px 48px -24px rgba(0,0,0,0.8)',
      },
      keyframes: {
        marquee: { from: { transform: 'translateX(0)' }, to: { transform: 'translateX(-50%)' } },
        shimmer: { '0%': { backgroundPosition: '-200% 0' }, '100%': { backgroundPosition: '200% 0' } },
        drift: { from: { transform: 'translateY(0)' }, to: { transform: 'translateY(-120vh)' } },
      },
      animation: {
        marquee: 'marquee 28s linear infinite',
        shimmer: 'shimmer 2.4s linear infinite',
      },
    },
  },
  plugins: [],
} satisfies Config
