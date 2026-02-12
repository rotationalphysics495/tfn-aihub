/**
 * DateNavigation Component Unit Tests (Story 17.1: Date Picker on Morning Report)
 *
 * @see Story 17.1 - Date Picker on Morning Report
 * @see AC #1 - Date picker placement
 * @see AC #3 - Prev/next day arrows
 */

import { render, screen, fireEvent } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import { subDays, addDays, format, startOfDay } from 'date-fns'

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), back: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => '/',
  useParams: () => ({}),
}))

// ---------------------------------------------------------------------------
// Import AFTER mocks
// ---------------------------------------------------------------------------

import { DateNavigation } from '../DateNavigation'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const yesterday = startOfDay(subDays(new Date(), 1))
const twoDaysAgo = startOfDay(subDays(new Date(), 2))
const threeDaysAgo = startOfDay(subDays(new Date(), 3))

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('DateNavigation', () => {
  let onDateChange: ReturnType<typeof vi.fn>

  beforeEach(() => {
    vi.clearAllMocks()
    onDateChange = vi.fn()
  })

  it('[17-1-UNIT-001] renders the trigger button with formatted date', () => {
    render(<DateNavigation date={yesterday} onDateChange={onDateChange} />)

    const expected = format(yesterday, 'MMM d, yyyy')
    expect(screen.getByText(expected)).toBeInTheDocument()
  })

  it('[17-1-UNIT-002] renders prev and next arrow buttons', () => {
    render(<DateNavigation date={twoDaysAgo} onDateChange={onDateChange} />)

    expect(screen.getByRole('button', { name: /previous day/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /next day/i })).toBeInTheDocument()
  })

  it('[17-1-UNIT-003] calls onDateChange with previous day when prev arrow is clicked', () => {
    render(<DateNavigation date={twoDaysAgo} onDateChange={onDateChange} />)

    fireEvent.click(screen.getByRole('button', { name: /previous day/i }))

    expect(onDateChange).toHaveBeenCalledTimes(1)
    const calledDate = onDateChange.mock.calls[0][0]
    expect(startOfDay(calledDate).getTime()).toBe(threeDaysAgo.getTime())
  })

  it('[17-1-UNIT-004] calls onDateChange with next day when next arrow is clicked', () => {
    render(<DateNavigation date={threeDaysAgo} onDateChange={onDateChange} />)

    fireEvent.click(screen.getByRole('button', { name: /next day/i }))

    expect(onDateChange).toHaveBeenCalledTimes(1)
    const calledDate = onDateChange.mock.calls[0][0]
    expect(startOfDay(calledDate).getTime()).toBe(twoDaysAgo.getTime())
  })

  it('[17-1-UNIT-005] disables next arrow when date is yesterday', () => {
    render(<DateNavigation date={yesterday} onDateChange={onDateChange} />)

    const nextButton = screen.getByRole('button', { name: /next day/i })
    expect(nextButton).toBeDisabled()
  })

  it('[17-1-UNIT-006] does not disable next arrow when date is before yesterday', () => {
    render(<DateNavigation date={twoDaysAgo} onDateChange={onDateChange} />)

    const nextButton = screen.getByRole('button', { name: /next day/i })
    expect(nextButton).not.toBeDisabled()
  })

  it('[17-1-UNIT-007] does not disable prev arrow', () => {
    render(<DateNavigation date={yesterday} onDateChange={onDateChange} />)

    const prevButton = screen.getByRole('button', { name: /previous day/i })
    expect(prevButton).not.toBeDisabled()
  })

  it('[17-1-UNIT-008] does not call onDateChange when next arrow is clicked and disabled', () => {
    render(<DateNavigation date={yesterday} onDateChange={onDateChange} />)

    const nextButton = screen.getByRole('button', { name: /next day/i })
    fireEvent.click(nextButton)

    expect(onDateChange).not.toHaveBeenCalled()
  })
})
