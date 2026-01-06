import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { TimeWindowToggle } from '../TimeWindowToggle'

/**
 * Tests for TimeWindowToggle Component
 *
 * Story: 2.5 - Downtime Pareto Analysis
 * AC: #7 - Time Window Toggle
 */

describe('TimeWindowToggle', () => {
  it('renders both toggle options', () => {
    const onViewChange = vi.fn()

    render(
      <TimeWindowToggle
        activeView="yesterday"
        onViewChange={onViewChange}
      />
    )

    expect(screen.getByText("Yesterday's Analysis")).toBeInTheDocument()
    expect(screen.getByText('Live Pulse')).toBeInTheDocument()
  })

  it('highlights yesterday option when active', () => {
    const onViewChange = vi.fn()

    render(
      <TimeWindowToggle
        activeView="yesterday"
        onViewChange={onViewChange}
      />
    )

    const yesterdayButton = screen.getByText("Yesterday's Analysis").closest('button')
    expect(yesterdayButton).toHaveClass('bg-card')
  })

  it('highlights live option when active', () => {
    const onViewChange = vi.fn()

    render(
      <TimeWindowToggle
        activeView="live"
        onViewChange={onViewChange}
      />
    )

    const liveButton = screen.getByText('Live Pulse').closest('button')
    expect(liveButton).toHaveClass('bg-card')
  })

  it('calls onViewChange when yesterday is clicked', () => {
    const onViewChange = vi.fn()

    render(
      <TimeWindowToggle
        activeView="live"
        onViewChange={onViewChange}
      />
    )

    const yesterdayButton = screen.getByText("Yesterday's Analysis").closest('button')
    if (yesterdayButton) {
      fireEvent.click(yesterdayButton)
      expect(onViewChange).toHaveBeenCalledWith('yesterday')
    }
  })

  it('calls onViewChange when live is clicked', () => {
    const onViewChange = vi.fn()

    render(
      <TimeWindowToggle
        activeView="yesterday"
        onViewChange={onViewChange}
      />
    )

    const liveButton = screen.getByText('Live Pulse').closest('button')
    if (liveButton) {
      fireEvent.click(liveButton)
      expect(onViewChange).toHaveBeenCalledWith('live')
    }
  })

  it('disables buttons when loading', () => {
    const onViewChange = vi.fn()

    render(
      <TimeWindowToggle
        activeView="yesterday"
        onViewChange={onViewChange}
        isLoading={true}
      />
    )

    const yesterdayButton = screen.getByText("Yesterday's Analysis").closest('button')
    const liveButton = screen.getByText('Live Pulse').closest('button')

    expect(yesterdayButton).toBeDisabled()
    expect(liveButton).toBeDisabled()
  })

  it('has proper aria attributes', () => {
    const onViewChange = vi.fn()

    render(
      <TimeWindowToggle
        activeView="yesterday"
        onViewChange={onViewChange}
      />
    )

    const yesterdayButton = screen.getByText("Yesterday's Analysis").closest('button')
    const liveButton = screen.getByText('Live Pulse').closest('button')

    expect(yesterdayButton).toHaveAttribute('aria-pressed', 'true')
    expect(liveButton).toHaveAttribute('aria-pressed', 'false')
  })
})
