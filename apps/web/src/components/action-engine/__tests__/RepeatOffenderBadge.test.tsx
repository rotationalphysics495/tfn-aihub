/**
 * RepeatOffenderBadge Component Tests (Story 14.4: Trend Indicators on Action Cards)
 *
 * TDD tests — these MUST FAIL until the RepeatOffenderBadge component is implemented.
 * Tests cover repeat offender badge rendering, "New" badge, frequency badge,
 * ordinal formatting, accessibility, and edge cases.
 *
 * @see Story 14.4 - Trend Indicators on Action Cards
 * @see AC #1 - Repeat offender badge displayed when consecutive_days >= 3
 * @see AC #4 - "New" badge shown for first-appearance items
 */

import { render, screen } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import React from 'react'

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
// Types
// ---------------------------------------------------------------------------

/**
 * TrendData represents trend indicator data for action items.
 * This type will be defined in types.ts when the feature is implemented.
 */
interface TrendData {
  consecutiveDays: number
  daysOnReport: number
  metricHistory: (number | null)[]
  weekOverWeekChange: number | null
}

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const createMockTrendData = (overrides: Partial<TrendData> = {}): TrendData => ({
  consecutiveDays: 1,
  daysOnReport: 1,
  metricHistory: [72.5, 74.1, 68.3, 71.0, 69.2, 73.8, 72.5],
  weekOverWeekChange: 0,
  ...overrides,
})

// ---------------------------------------------------------------------------
// Dynamic import helper - will fail until component exists
// ---------------------------------------------------------------------------

async function importRepeatOffenderBadge() {
  const mod = await import('../RepeatOffenderBadge')
  return mod.RepeatOffenderBadge
}

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: Trend Indicators on Action Cards (Story 14.4)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // =========================================================================
  // AC1: Repeat offender badge displayed when consecutive_days >= 3
  // =========================================================================
  describe('AC1: Repeat Offender Badge for Consecutive Days >= 3', () => {
    it('UNIT-001: Repeat offender badge renders with warning variant when consecutive_days >= 3', async () => {
      // Given: An action item has trendData with consecutiveDays = 3 and daysOnReport = 5
      const RepeatOffenderBadge = await importRepeatOffenderBadge()
      const trendData = createMockTrendData({
        consecutiveDays: 3,
        daysOnReport: 5,
        metricHistory: [70, 71, 72, 73, 74, 75, 76],
        weekOverWeekChange: -2.5,
      })

      // When: The RepeatOffenderBadge component renders
      render(React.createElement(RepeatOffenderBadge, { trendData }))

      // Then: A Badge with variant="warning" is displayed containing text "3rd day in a row"
      const badge = screen.getByText(/3rd day in a row/i)
      expect(badge).toBeInTheDocument()

      // And: The badge uses warning variant (amber styling)
      const badgeEl = badge.closest('[class*="warning"]') || badge.closest('[class*="border-warning-amber"]')
      expect(badgeEl).toBeTruthy()
    })

    it('UNIT-002: Repeat offender badge shows correct ordinal suffix for higher consecutive counts', async () => {
      // Given: An action item has trendData with consecutiveDays = 5
      const RepeatOffenderBadge = await importRepeatOffenderBadge()
      const trendData = createMockTrendData({
        consecutiveDays: 5,
        daysOnReport: 6,
        metricHistory: [70, 71, 72, 73, 74, 75, 76],
        weekOverWeekChange: -1.0,
      })

      // When: The RepeatOffenderBadge component renders
      render(React.createElement(RepeatOffenderBadge, { trendData }))

      // Then: A Badge with variant="warning" is displayed containing text "5th day in a row"
      const badge = screen.getByText(/5th day in a row/i)
      expect(badge).toBeInTheDocument()

      const badgeEl = badge.closest('[class*="warning"]') || badge.closest('[class*="border-warning-amber"]')
      expect(badgeEl).toBeTruthy()
    })

    it('UNIT-003: Repeat offender badge shows correct ordinal for 4th consecutive day', async () => {
      // Given: An action item has trendData with consecutiveDays = 4
      const RepeatOffenderBadge = await importRepeatOffenderBadge()
      const trendData = createMockTrendData({
        consecutiveDays: 4,
        daysOnReport: 4,
        metricHistory: [70, 71, 72, 73, 74, 75, 76],
        weekOverWeekChange: 3.0,
      })

      // When: The RepeatOffenderBadge component renders
      render(React.createElement(RepeatOffenderBadge, { trendData }))

      // Then: A Badge with variant="warning" is displayed containing text "4th day in a row"
      const badge = screen.getByText(/4th day in a row/i)
      expect(badge).toBeInTheDocument()

      const badgeEl = badge.closest('[class*="warning"]') || badge.closest('[class*="border-warning-amber"]')
      expect(badgeEl).toBeTruthy()
    })

    it('UNIT-004: Frequency badge shown when days_on_report >= 3 but consecutive_days < 3', async () => {
      // Given: An action item has trendData with daysOnReport = 4 and consecutiveDays = 1
      const RepeatOffenderBadge = await importRepeatOffenderBadge()
      const trendData = createMockTrendData({
        consecutiveDays: 1,
        daysOnReport: 4,
        metricHistory: [70, 71, 72, 73, 74, 75, 76],
        weekOverWeekChange: -2.0,
      })

      // When: The RepeatOffenderBadge component renders
      render(React.createElement(RepeatOffenderBadge, { trendData }))

      // Then: A Badge with variant="warning" is displayed containing text "4 of 7 days"
      const badge = screen.getByText(/4 of 7 days/i)
      expect(badge).toBeInTheDocument()

      const badgeEl = badge.closest('[class*="warning"]') || badge.closest('[class*="border-warning-amber"]')
      expect(badgeEl).toBeTruthy()
    })

    it('UNIT-005: Second day badge shown with outline variant when consecutive_days = 2', async () => {
      // Given: An action item has trendData with consecutiveDays = 2 and daysOnReport = 2
      const RepeatOffenderBadge = await importRepeatOffenderBadge()
      const trendData = createMockTrendData({
        consecutiveDays: 2,
        daysOnReport: 2,
        metricHistory: [72, 73, 72, 73, 72, 73, 72],
        weekOverWeekChange: 1.5,
      })

      // When: The RepeatOffenderBadge component renders
      render(React.createElement(RepeatOffenderBadge, { trendData }))

      // Then: A Badge with variant="outline" is displayed containing text "2nd day"
      const badge = screen.getByText(/2nd day/i)
      expect(badge).toBeInTheDocument()

      // And: The badge uses the outline variant (not warning)
      const badgeEl = badge.closest('div')
      expect(badgeEl).toBeTruthy()
      // Outline variant should NOT have warning/amber classes
      expect(badgeEl!.className).not.toMatch(/warning|amber/)
    })

    it('UNIT-006: Repeat offender badge has correct ARIA label for accessibility', async () => {
      // Given: An action item has trendData with consecutiveDays = 3
      const RepeatOffenderBadge = await importRepeatOffenderBadge()
      const trendData = createMockTrendData({
        consecutiveDays: 3,
        daysOnReport: 5,
        metricHistory: [70, 71, 72, 73, 74, 75, 76],
        weekOverWeekChange: -3.0,
      })

      // When: The RepeatOffenderBadge component renders
      render(React.createElement(RepeatOffenderBadge, { trendData }))

      // Then: The badge element has an appropriate aria-label describing the repeat status
      const badge = screen.getByLabelText(/repeat issue: 3rd day in a row/i)
      expect(badge).toBeInTheDocument()
    })

    it('UNIT-007: Consecutive_days >= 3 takes precedence over days_on_report >= 3', async () => {
      // Given: An action item has trendData with consecutiveDays = 3 AND daysOnReport = 5
      const RepeatOffenderBadge = await importRepeatOffenderBadge()
      const trendData = createMockTrendData({
        consecutiveDays: 3,
        daysOnReport: 5,
        metricHistory: [70, 71, 72, 73, 74, 75, 76],
        weekOverWeekChange: -1.0,
      })

      // When: The RepeatOffenderBadge component renders
      render(React.createElement(RepeatOffenderBadge, { trendData }))

      // Then: The "3rd day in a row" badge is shown (not "5 of 7 days")
      expect(screen.getByText(/3rd day in a row/i)).toBeInTheDocument()
      expect(screen.queryByText(/5 of 7 days/i)).toBeNull()
    })
  })

  // =========================================================================
  // AC4: "New" badge shown for first-appearance items
  // =========================================================================
  describe('AC4: "New" Badge for First-Appearance Items', () => {
    it('UNIT-028: "New" badge shown when days_on_report = 1 and consecutive_days = 1', async () => {
      // Given: An action item has trendData with daysOnReport = 1 and consecutiveDays = 1
      const RepeatOffenderBadge = await importRepeatOffenderBadge()
      const trendData = createMockTrendData({
        consecutiveDays: 1,
        daysOnReport: 1,
        metricHistory: [72.5],
        weekOverWeekChange: null,
      })

      // When: The RepeatOffenderBadge component renders
      render(React.createElement(RepeatOffenderBadge, { trendData }))

      // Then: A Badge with variant="info" is displayed containing text "New"
      const badge = screen.getByText(/^new$/i)
      expect(badge).toBeInTheDocument()

      const badgeEl = badge.closest('[class*="info"]') || badge.closest('[class*="border-info-blue"]')
      expect(badgeEl).toBeTruthy()
    })

    it('UNIT-029: "New" badge has info variant styling (blue background)', async () => {
      // Given: An action item has trendData with daysOnReport = 1 and consecutiveDays = 1
      const RepeatOffenderBadge = await importRepeatOffenderBadge()
      const trendData = createMockTrendData({
        consecutiveDays: 1,
        daysOnReport: 1,
        metricHistory: [72.5],
        weekOverWeekChange: null,
      })

      // When: The RepeatOffenderBadge component renders
      render(React.createElement(RepeatOffenderBadge, { trendData }))

      // Then: The Badge uses the "info" variant which applies blue background styling
      const badge = screen.getByText(/^new$/i)
      const badgeEl = badge.closest('[class*="info-blue"]') || badge.closest('[class*="info"]')
      expect(badgeEl).toBeTruthy()
    })

    it('UNIT-030: "New" badge has appropriate ARIA label', async () => {
      // Given: An action item has trendData with daysOnReport = 1 and consecutiveDays = 1
      const RepeatOffenderBadge = await importRepeatOffenderBadge()
      const trendData = createMockTrendData({
        consecutiveDays: 1,
        daysOnReport: 1,
        metricHistory: [72.5],
        weekOverWeekChange: null,
      })

      // When: The RepeatOffenderBadge component renders
      render(React.createElement(RepeatOffenderBadge, { trendData }))

      // Then: The badge has an ARIA label like "New issue"
      const badge = screen.getByLabelText(/new issue/i)
      expect(badge).toBeInTheDocument()
    })

    it('UNIT-031: No badge rendered when trendData is undefined', async () => {
      // Given: An action item has no trendData (trendData is undefined)
      const RepeatOffenderBadge = await importRepeatOffenderBadge()

      // When: The RepeatOffenderBadge component renders
      const { container } = render(React.createElement(RepeatOffenderBadge, { trendData: undefined }))

      // Then: No badge is rendered (returns null)
      expect(container.innerHTML).toBe('')
    })

    it('UNIT-032: No badge rendered when trendData is null', async () => {
      // Given: An action item has trendData = null
      const RepeatOffenderBadge = await importRepeatOffenderBadge()

      // When: The RepeatOffenderBadge component renders
      const { container } = render(React.createElement(RepeatOffenderBadge, { trendData: null }))

      // Then: No badge is rendered (returns null)
      expect(container.innerHTML).toBe('')
    })
  })

  // =========================================================================
  // Edge Cases
  // =========================================================================
  describe('Edge Cases', () => {
    it('EDGE-001: consecutiveDays = 0 renders nothing', async () => {
      // Given: Invalid/unexpected data with consecutiveDays = 0
      const RepeatOffenderBadge = await importRepeatOffenderBadge()
      const trendData = createMockTrendData({
        consecutiveDays: 0,
        daysOnReport: 0,
      })

      // When: The RepeatOffenderBadge component renders
      const { container } = render(React.createElement(RepeatOffenderBadge, { trendData }))

      // Then: No badge is rendered (graceful handling)
      expect(container.innerHTML).toBe('')
    })

    it('EDGE-002: Very large consecutiveDays shows correct ordinal', async () => {
      // Given: A very large consecutiveDays value
      const RepeatOffenderBadge = await importRepeatOffenderBadge()
      const trendData = createMockTrendData({
        consecutiveDays: 30,
        daysOnReport: 30,
      })

      // When: The RepeatOffenderBadge component renders
      render(React.createElement(RepeatOffenderBadge, { trendData }))

      // Then: The ordinal suffix is correct ("30th day in a row")
      expect(screen.getByText(/30th day in a row/i)).toBeInTheDocument()
    })

    it('EDGE-003: consecutiveDays negative value renders nothing', async () => {
      // Given: Negative consecutiveDays (invalid data from API)
      const RepeatOffenderBadge = await importRepeatOffenderBadge()
      const trendData = createMockTrendData({
        consecutiveDays: -1,
        daysOnReport: 3,
      })

      // When: The RepeatOffenderBadge component renders
      const { container } = render(React.createElement(RepeatOffenderBadge, { trendData }))

      // Then: No badge is rendered (graceful handling of invalid data)
      expect(container.innerHTML).toBe('')
    })
  })
})
