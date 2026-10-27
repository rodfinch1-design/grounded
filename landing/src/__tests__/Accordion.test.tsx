import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import Accordion from '../components/Accordion'
import { faqs } from '../lib/data'

describe('Accordion', () => {
  it('renders all 8 FAQ questions as buttons with aria-expanded', () => {
    render(<Accordion items={faqs} />)
    const buttons = screen.getAllByRole('button')
    expect(buttons).toHaveLength(8)
    buttons.forEach((b) => expect(b).toHaveAttribute('aria-expanded'))
  })

  it('opens the first item by default and wires aria-controls to a region', () => {
    render(<Accordion items={faqs} />)
    const first = screen.getByRole('button', { name: faqs[0].q })
    expect(first).toHaveAttribute('aria-expanded', 'true')
    const region = screen.getByRole('region', { name: faqs[0].q })
    expect(region).toHaveTextContent(faqs[0].a)
    expect(first.getAttribute('aria-controls')).toBe(region.id)
  })

  it('switches the open item on click and closes on second click', async () => {
    const user = userEvent.setup()
    render(<Accordion items={faqs} />)
    const second = screen.getByRole('button', { name: faqs[1].q })
    await user.click(second)
    expect(second).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByRole('button', { name: faqs[0].q })).toHaveAttribute('aria-expanded', 'false')
    await user.click(second)
    expect(second).toHaveAttribute('aria-expanded', 'false')
  })

  it('is keyboard operable', async () => {
    const user = userEvent.setup()
    render(<Accordion items={faqs} />)
    const third = screen.getByRole('button', { name: faqs[2].q })
    third.focus()
    await user.keyboard('{Enter}')
    expect(third).toHaveAttribute('aria-expanded', 'true')
  })

  it('marks the open item with the lime left border', async () => {
    const user = userEvent.setup()
    render(<Accordion items={faqs} />)
    const third = screen.getByRole('button', { name: faqs[2].q })
    await user.click(third)
    expect(third.closest('div')).toHaveClass('border-l-lime')
  })
})
