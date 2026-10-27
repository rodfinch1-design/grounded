import { render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import Loader from '../components/Loader'
import { mediaState } from './setup'

afterEach(() => { mediaState.reduced = false })

describe('Loader', () => {
  it('shows the monogram, then fades out and calls onDone after ~3s', async () => {
    const onDone = vi.fn()
    const start = Date.now()
    render(<Loader onDone={onDone} />)
    expect(screen.getByRole('status', { name: 'Loading' })).toHaveTextContent('H')
    await new Promise((r) => setTimeout(r, 2500))
    expect(screen.getByRole('status')).toBeInTheDocument()
    expect(onDone).not.toHaveBeenCalled()
    await waitFor(() => expect(screen.queryByRole('status')).not.toBeInTheDocument(), { timeout: 3000 })
    await waitFor(() => expect(onDone).toHaveBeenCalledTimes(1))
    expect(Date.now() - start).toBeGreaterThanOrEqual(3000)
  }, 10000)

  it('shortens the delay under prefers-reduced-motion', async () => {
    mediaState.reduced = true
    const onDone = vi.fn()
    render(<Loader onDone={onDone} />)
    await waitFor(() => expect(screen.queryByRole('status')).not.toBeInTheDocument(), { timeout: 2000 })
    await waitFor(() => expect(onDone).toHaveBeenCalledTimes(1))
  })
})
