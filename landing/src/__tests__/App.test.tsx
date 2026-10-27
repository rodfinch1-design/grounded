import { render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import App from '../App'

describe('App', () => {
  it('mounts the full page: nav, loader, hero and all lazy sections', async () => {
    render(<App />)
    expect(screen.getByRole('status', { name: 'Loading' })).toBeInTheDocument()
    expect(screen.getByRole('navigation', { name: 'Primary' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument()
    await waitFor(() => expect(screen.getByRole('contentinfo')).toBeInTheDocument())
    for (const id of ['templates', 'method', 'pricing', 'faq']) {
      expect(document.getElementById(id)).not.toBeNull()
    }
    expect(screen.getAllByRole('heading', { level: 2 }).length).toBeGreaterThanOrEqual(5)
  })
})
