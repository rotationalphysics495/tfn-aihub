/**
 * ShiftTabs Component Tests (Story 17.4: Shift Breakdown API & UI)
 *
 * @see Story 17.4 - Shift Breakdown API & UI
 * @see AC #2 - Shift tab filtering on scorecard and action items
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ShiftTabs } from '../ShiftTabs'

describe('ShiftTabs', () => {
  describe('AC2: Shift tab rendering and behavior', () => {
    it('17-4-UNIT-040: renders all four tabs (All, Morning, Afternoon, Night)', () => {
      render(<ShiftTabs value="all" onValueChange={vi.fn()} />)

      expect(screen.getByRole('tab', { name: 'All' })).toBeInTheDocument()
      expect(screen.getByRole('tab', { name: 'Morning' })).toBeInTheDocument()
      expect(screen.getByRole('tab', { name: 'Afternoon' })).toBeInTheDocument()
      expect(screen.getByRole('tab', { name: 'Night' })).toBeInTheDocument()
    })

    it('17-4-UNIT-041: "All" tab is selected by default when value is "all"', () => {
      render(<ShiftTabs value="all" onValueChange={vi.fn()} />)

      const allTab = screen.getByRole('tab', { name: 'All' })
      expect(allTab).toHaveAttribute('data-state', 'active')
    })

    it('17-4-UNIT-042: clicking a tab calls onValueChange with correct value', async () => {
      const user = userEvent.setup()
      const onValueChange = vi.fn()
      render(<ShiftTabs value="all" onValueChange={onValueChange} />)

      await user.click(screen.getByRole('tab', { name: 'Afternoon' }))
      expect(onValueChange).toHaveBeenCalledWith('afternoon')
    })

    it('17-4-UNIT-043: controlled value prop works correctly', () => {
      render(<ShiftTabs value="morning" onValueChange={vi.fn()} />)

      const morningTab = screen.getByRole('tab', { name: 'Morning' })
      expect(morningTab).toHaveAttribute('data-state', 'active')

      const allTab = screen.getByRole('tab', { name: 'All' })
      expect(allTab).toHaveAttribute('data-state', 'inactive')
    })

    it('17-4-UNIT-044: renders accessible tablist with aria-label', () => {
      render(<ShiftTabs value="all" onValueChange={vi.fn()} />)

      const tablist = screen.getByRole('tablist')
      expect(tablist).toHaveAttribute('aria-label', 'Filter by shift')
    })

    it('17-4-UNIT-045: applies custom className', () => {
      const { container } = render(
        <ShiftTabs value="all" onValueChange={vi.fn()} className="mt-4" />
      )

      // The root Tabs element should have the custom class
      const root = container.firstChild as HTMLElement
      expect(root.className).toContain('mt-4')
    })
  })
})
