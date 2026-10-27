import { render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import Hero from '../sections/Hero'
import Pricing from '../sections/Pricing'
import Bento from '../sections/Bento'
import FinalCTA from '../sections/FinalCTA'
import Dust from '../components/Dust'
import { templates, tiers } from '../lib/data'
import { mediaState } from './setup'

afterEach(() => { mediaState.reduced = false; mediaState.mobile = false })

describe('Hero', () => {
  it('renders eyebrow, headline, sub and both CTAs', () => {
    render(<Hero ready />)
    expect(screen.getByText('Templates · 2026')).toBeInTheDocument()
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent("Ship a site thatdoesn't feel like AI made it.")
    expect(screen.getByText('8 premium templates. Cursor / v0 / Lovable ready.')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Browse templates →' })).toHaveAttribute('href', '#templates')
    expect(screen.getByRole('link', { name: 'See the method' })).toHaveAttribute('href', '#method')
  })

  it('renders the background video muted, looping and hidden from AT', () => {
    const { container } = render(<Hero ready />)
    const video = container.querySelector('video')!
    expect(video).toHaveAttribute('aria-hidden', 'true')
    expect(video.muted).toBe(true)
    expect(video).toHaveAttribute('loop')
    expect(video).toHaveAttribute('playsinline')
  })
})

describe('Dust layer', () => {
  it('renders on desktop and is removed on mobile or reduced motion', () => {
    const { container, unmount } = render(<Dust count={5} />)
    expect(container.querySelectorAll('span')).toHaveLength(5)
    unmount()
    mediaState.mobile = true
    expect(render(<Dust count={5} />).container.querySelectorAll('span')).toHaveLength(0)
    mediaState.mobile = false
    mediaState.reduced = true
    expect(render(<Dust count={5} />).container.querySelectorAll('span')).toHaveLength(0)
  })
})

describe('Bento', () => {
  it('renders 8 template cards with lazy thumbnails, first featured', () => {
    render(<Bento />)
    const cards = screen.getAllByRole('link')
    expect(cards).toHaveLength(8)
    expect(cards[0]).toHaveTextContent('Featured')
    expect(cards[0].className).toMatch(/shadow-glow/)
    const imgs = screen.getAllByRole('img')
    expect(imgs).toHaveLength(templates.length)
    imgs.forEach((img, i) => {
      expect(img).toHaveAttribute('alt', `${templates[i].title} template preview`)
      expect(img).toHaveAttribute('loading', i < 2 ? 'eager' : 'lazy')
    })
  })
})

describe('Pricing', () => {
  it('renders the 3 tiers with correct prices, highlights the middle, and the one-shot note', () => {
    render(<Pricing />)
    const articles = screen.getAllByRole('article')
    expect(articles).toHaveLength(3)
    expect(articles.map((a) => within(a).getByRole('heading', { level: 3 }).textContent)).toEqual(['Express', 'Standard', 'Custom'])
    expect(within(articles[0]).getByText('€297')).toBeInTheDocument()
    expect(within(articles[1]).getByText('€597')).toBeInTheDocument()
    expect(within(articles[2]).getByText('€1,499')).toBeInTheDocument()
    expect(articles[1].className).toMatch(/shadow-glow/)
    expect(articles[0].className).not.toMatch(/shadow-glow/)
    expect(screen.getByText('All prices one-shot, no subscription')).toBeInTheDocument()
  })

  it('uses lime checks for included features and muted crosses for excluded ones', () => {
    render(<Pricing />)
    const svgs = document.querySelectorAll('article svg')
    const expected = tiers.flatMap((t) => t.features.map((f) => f.included))
    expect(svgs).toHaveLength(expected.length)
    svgs.forEach((svg, i) => {
      expect(svg.getAttribute('class')).toContain(expected[i] ? 'text-lime' : 'text-ink-2')
      expect(svg).toHaveAttribute('aria-hidden', 'true')
    })
  })
})

describe('Final CTA', () => {
  it('renders headline, single lime button and the marquee strip', () => {
    render(<FinalCTA />)
    expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Ready to ship?Or still scrolling references?')
    const links = screen.getAllByRole('link')
    expect(links).toHaveLength(1)
    expect(links[0]).toHaveTextContent('Browse templates →')
    expect(screen.getByLabelText('Built with AI · Not by AI ·')).toBeInTheDocument()
  })
})
