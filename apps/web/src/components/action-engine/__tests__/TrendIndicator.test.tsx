/**
 * TrendIndicator Component Tests (Story 14.4: Trend Indicators on Action Cards)
 *
 * TDD tests — these MUST FAIL until the TrendIndicator component is implemented.
 * Tests cover trend arrow direction logic, sparkline rendering, skeleton states,
 * accessibility, and metric-direction interpretation for different priority types.
 *
 * @see Story 14.4 - Trend Indicators on Action Cards
 * @see AC #2 - Trend arrow displayed based on week_over_week_change
 * @see AC #3 - 7-day sparkline chart displayed from trend_data
 * @see AC #5 - Skeleton placeholder when trend data is loading or unavailable
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

// Mock Recharts to inspect sparkline rendering without actual SVG
vi.mock('recharts', () => ({
  LineChart: ({ children, ...props }: Record<string, unknown>) =>
    React.createElement(
      'div',
      {
        'data-testid': 'sparkline-chart',
        'data-width': props.width,
        'data-height': props.height,
      },
      children as React.ReactNode,
    ),
  Line: (props: Record<string, unknown>) =>
    React.createElement('div', {
      'data-testid': 'sparkline-line',
      'data-stroke': props.stroke,
      'data-stroke-width': props.strokeWidth,
      'data-dot': String(props.dot),
      'data-animation': String(props.isAnimationActive),
    }),
}))

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

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

async function importTrendIndicator() {
  const mod = await import('../TrendIndicator')
  return mod.TrendIndicator
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
  // AC2: Trend arrow displayed based on week_over_week_change
  // =========================================================================
  describe('AC2: Trend Arrow Based on Week-over-Week Change', () => {
    it('UNIT-008: Green arrow shown when OEE metric improves (positive change)', async () => {
      // Given: An action item has priority = "OEE" and trendData with weekOverWeekChange = 3.1
      const TrendIndicator = await importTrendIndicator()
      const trendData = createMockTrendData({
        weekOverWeekChange: 3.1,
        metricHistory: [70, 71, 72, 73, 74, 75, 76],
        consecutiveDays: 2,
        daysOnReport: 3,
      })

      // When: The TrendIndicator component renders
      render(React.createElement(TrendIndicator, { trendData, priority: 'OEE' }))

      // Then: A green trend arrow (up/improving direction) is displayed with text "+3.1%"
      const percentText = screen.getByText(/\+3\.1%/i)
      expect(percentText).toBeInTheDocument()

      // And: The arrow indicator uses green color for improvement
      const arrowContainer = screen.getByTestId('trend-arrow')
      expect(arrowContainer.className).toMatch(/green|text-green/)
    })

    it('UNIT-009: Red arrow shown when OEE metric worsens (negative change)', async () => {
      // Given: An action item has priority = "OEE" and trendData with weekOverWeekChange = -4.2
      const TrendIndicator = await importTrendIndicator()
      const trendData = createMockTrendData({
        weekOverWeekChange: -4.2,
        metricHistory: [76, 75, 74, 73, 72, 71, 70],
        consecutiveDays: 1,
        daysOnReport: 1,
      })

      // When: The TrendIndicator component renders
      render(React.createElement(TrendIndicator, { trendData, priority: 'OEE' }))

      // Then: A red trend arrow (down/worsening direction) is displayed with text "-4.2%"
      const percentText = screen.getByText(/-4\.2%/i)
      expect(percentText).toBeInTheDocument()

      const arrowContainer = screen.getByTestId('trend-arrow')
      expect(arrowContainer.className).toMatch(/red|text-red/)
    })

    it('UNIT-010: Green arrow shown when FINANCIAL metric improves (negative change = loss decreased)', async () => {
      // Given: An action item has priority = "FINANCIAL" and trendData with weekOverWeekChange = -5.0
      const TrendIndicator = await importTrendIndicator()
      const trendData = createMockTrendData({
        weekOverWeekChange: -5.0,
        metricHistory: [100, 95, 90, 85, 80, 75, 70],
        consecutiveDays: 2,
        daysOnReport: 4,
      })

      // When: The TrendIndicator component renders
      render(React.createElement(TrendIndicator, { trendData, priority: 'FINANCIAL' }))

      // Then: A green trend arrow (improving direction) is displayed with text "-5.0%"
      const percentText = screen.getByText(/-5\.0%/i)
      expect(percentText).toBeInTheDocument()

      const arrowContainer = screen.getByTestId('trend-arrow')
      expect(arrowContainer.className).toMatch(/green|text-green/)
    })

    it('UNIT-011: Red arrow shown when FINANCIAL metric worsens (positive change = loss increased)', async () => {
      // Given: An action item has priority = "FINANCIAL" and trendData with weekOverWeekChange = 6.3
      const TrendIndicator = await importTrendIndicator()
      const trendData = createMockTrendData({
        weekOverWeekChange: 6.3,
        metricHistory: [70, 75, 80, 85, 90, 95, 100],
        consecutiveDays: 3,
        daysOnReport: 5,
      })

      // When: The TrendIndicator component renders
      render(React.createElement(TrendIndicator, { trendData, priority: 'FINANCIAL' }))

      // Then: A red trend arrow (worsening direction) is displayed with text "+6.3%"
      const percentText = screen.getByText(/\+6\.3%/i)
      expect(percentText).toBeInTheDocument()

      const arrowContainer = screen.getByTestId('trend-arrow')
      expect(arrowContainer.className).toMatch(/red|text-red/)
    })

    it('UNIT-012: Gray horizontal arrow shown when change is stable (< 2% absolute)', async () => {
      // Given: An action item has priority = "OEE" and trendData with weekOverWeekChange = 1.5
      const TrendIndicator = await importTrendIndicator()
      const trendData = createMockTrendData({
        weekOverWeekChange: 1.5,
        metricHistory: [72, 73, 72, 73, 72, 73, 72],
        consecutiveDays: 1,
        daysOnReport: 2,
      })

      // When: The TrendIndicator component renders
      render(React.createElement(TrendIndicator, { trendData, priority: 'OEE' }))

      // Then: A gray horizontal arrow is displayed indicating stable trend
      const arrowContainer = screen.getByTestId('trend-arrow')
      expect(arrowContainer.className).toMatch(/gray|text-gray|text-muted/)
    })

    it('UNIT-013: Gray horizontal arrow for negative stable change (> -2%)', async () => {
      // Given: An action item has priority = "FINANCIAL" and trendData with weekOverWeekChange = -1.9
      const TrendIndicator = await importTrendIndicator()
      const trendData = createMockTrendData({
        weekOverWeekChange: -1.9,
        metricHistory: [72, 72.5, 72, 72.5, 72, 72.5, 72],
        consecutiveDays: 1,
        daysOnReport: 1,
      })

      // When: The TrendIndicator component renders
      render(React.createElement(TrendIndicator, { trendData, priority: 'FINANCIAL' }))

      // Then: A gray horizontal arrow is displayed indicating stable trend
      const arrowContainer = screen.getByTestId('trend-arrow')
      expect(arrowContainer.className).toMatch(/gray|text-gray|text-muted/)
    })

    it('UNIT-014: Boundary test - exactly 2% absolute change shows directional arrow (not stable)', async () => {
      // Given: An action item has priority = "OEE" and trendData with weekOverWeekChange = 2.0
      const TrendIndicator = await importTrendIndicator()
      const trendData = createMockTrendData({
        weekOverWeekChange: 2.0,
        metricHistory: [70, 71, 72, 73, 74, 75, 76],
        consecutiveDays: 1,
        daysOnReport: 1,
      })

      // When: The TrendIndicator component renders
      render(React.createElement(TrendIndicator, { trendData, priority: 'OEE' }))

      // Then: A green arrow is displayed (2.0% is at the boundary, >= 2% is not stable)
      const arrowContainer = screen.getByTestId('trend-arrow')
      expect(arrowContainer.className).toMatch(/green|text-green/)
      expect(arrowContainer.className).not.toMatch(/gray|text-gray|text-muted/)
    })

    it('UNIT-015: Boundary test - exactly -2% absolute change shows directional arrow', async () => {
      // Given: An action item has priority = "OEE" and trendData with weekOverWeekChange = -2.0
      const TrendIndicator = await importTrendIndicator()
      const trendData = createMockTrendData({
        weekOverWeekChange: -2.0,
        metricHistory: [76, 75, 74, 73, 72, 71, 70],
        consecutiveDays: 1,
        daysOnReport: 1,
      })

      // When: The TrendIndicator component renders
      render(React.createElement(TrendIndicator, { trendData, priority: 'OEE' }))

      // Then: A red arrow is displayed (exactly 2% absolute is not < 2%, so not stable)
      const arrowContainer = screen.getByTestId('trend-arrow')
      expect(arrowContainer.className).toMatch(/red|text-red/)
      expect(arrowContainer.className).not.toMatch(/gray|text-gray|text-muted/)
    })

    it('UNIT-016: No trend arrow for SAFETY priority items', async () => {
      // Given: An action item has priority = "SAFETY" and trendData with weekOverWeekChange = -5.0
      const TrendIndicator = await importTrendIndicator()
      const trendData = createMockTrendData({
        weekOverWeekChange: -5.0,
        metricHistory: [70, 71, 72, 73, 74, 75, 76],
        consecutiveDays: 3,
        daysOnReport: 5,
      })

      // When: The TrendIndicator component renders
      render(React.createElement(TrendIndicator, { trendData, priority: 'SAFETY' }))

      // Then: No trend arrow is displayed (safety items do not show directional trend arrows)
      const arrowContainer = screen.queryByTestId('trend-arrow')
      expect(arrowContainer).toBeNull()
    })

    it('UNIT-017: Trend arrow has correct ARIA label describing direction and percentage', async () => {
      // Given: An action item has priority = "OEE" and trendData with weekOverWeekChange = -3.1
      const TrendIndicator = await importTrendIndicator()
      const trendData = createMockTrendData({
        weekOverWeekChange: -3.1,
        metricHistory: [76, 75, 74, 73, 72, 71, 70],
        consecutiveDays: 2,
        daysOnReport: 3,
      })

      // When: The TrendIndicator component renders
      render(React.createElement(TrendIndicator, { trendData, priority: 'OEE' }))

      // Then: The trend indicator has an ARIA label like "Trend: worsening, OEE down 3.1%"
      const arrowWithLabel = screen.getByLabelText(/trend.*worsening.*oee.*3\.1%/i)
      expect(arrowWithLabel).toBeInTheDocument()
    })

    it('UNIT-018: Zero week_over_week_change shows gray stable arrow', async () => {
      // Given: An action item has priority = "OEE" and trendData with weekOverWeekChange = 0
      const TrendIndicator = await importTrendIndicator()
      const trendData = createMockTrendData({
        weekOverWeekChange: 0,
        metricHistory: [72, 72, 72, 72, 72, 72, 72],
        consecutiveDays: 1,
        daysOnReport: 1,
      })

      // When: The TrendIndicator component renders
      render(React.createElement(TrendIndicator, { trendData, priority: 'OEE' }))

      // Then: A gray horizontal arrow is displayed indicating stable trend
      const arrowContainer = screen.getByTestId('trend-arrow')
      expect(arrowContainer.className).toMatch(/gray|text-gray|text-muted/)
    })

    it('UNIT-019: Null weekOverWeekChange does not render trend arrow', async () => {
      // Given: An action item has priority = "OEE" and trendData with weekOverWeekChange = null
      const TrendIndicator = await importTrendIndicator()
      const trendData = createMockTrendData({
        weekOverWeekChange: null,
        metricHistory: [72.5, 74.1, 68.3, 71.0, 69.2, 73.8, 72.5],
        consecutiveDays: 1,
        daysOnReport: 1,
      })

      // When: The TrendIndicator component renders
      render(React.createElement(TrendIndicator, { trendData, priority: 'OEE' }))

      // Then: No trend arrow is displayed (graceful handling of null)
      const arrowContainer = screen.queryByTestId('trend-arrow')
      expect(arrowContainer).toBeNull()
    })
  })

  // =========================================================================
  // AC3: 7-day sparkline chart displayed from trend_data
  // =========================================================================
  describe('AC3: 7-Day Sparkline Chart', () => {
    it('UNIT-020: Sparkline renders with 7-day metric history data', async () => {
      // Given: An action item has trendData with metricHistory = [72.5, 74.1, 68.3, 71.0, 69.2, 73.8, 72.5]
      const TrendIndicator = await importTrendIndicator()
      const trendData = createMockTrendData({
        metricHistory: [72.5, 74.1, 68.3, 71.0, 69.2, 73.8, 72.5],
        weekOverWeekChange: 0.0,
        consecutiveDays: 2,
        daysOnReport: 3,
      })

      // When: The TrendIndicator component renders
      render(React.createElement(TrendIndicator, { trendData, priority: 'OEE' }))

      // Then: A small sparkline chart (approximately 80px wide x 24px tall) is rendered
      const chart = screen.getByTestId('sparkline-chart')
      expect(chart).toBeInTheDocument()
      expect(chart.getAttribute('data-width')).toBe('80')
      expect(chart.getAttribute('data-height')).toBe('24')
    })

    it('UNIT-021: Sparkline stroke color matches trend direction (green for improving)', async () => {
      // Given: An action item has priority = "OEE" and weekOverWeekChange = 3.5 (improving)
      const TrendIndicator = await importTrendIndicator()
      const trendData = createMockTrendData({
        metricHistory: [70, 71, 72, 73, 74, 75, 76],
        weekOverWeekChange: 3.5,
        consecutiveDays: 1,
        daysOnReport: 2,
      })

      // When: The TrendIndicator component renders
      render(React.createElement(TrendIndicator, { trendData, priority: 'OEE' }))

      // Then: The sparkline line stroke color is green
      const line = screen.getByTestId('sparkline-line')
      expect(line.getAttribute('data-stroke')).toMatch(/green|#22c55e|#16a34a|#4ade80/)
    })

    it('UNIT-022: Sparkline stroke color is red for worsening trend', async () => {
      // Given: An action item has priority = "OEE" and weekOverWeekChange = -4.0 (worsening)
      const TrendIndicator = await importTrendIndicator()
      const trendData = createMockTrendData({
        metricHistory: [76, 75, 74, 73, 72, 71, 70],
        weekOverWeekChange: -4.0,
        consecutiveDays: 2,
        daysOnReport: 4,
      })

      // When: The TrendIndicator component renders
      render(React.createElement(TrendIndicator, { trendData, priority: 'OEE' }))

      // Then: The sparkline line stroke color is red
      const line = screen.getByTestId('sparkline-line')
      expect(line.getAttribute('data-stroke')).toMatch(/red|#ef4444|#dc2626|#f87171/)
    })

    it('UNIT-023: Sparkline stroke color is gray for stable trend', async () => {
      // Given: An action item has priority = "OEE" and weekOverWeekChange = 0.5 (stable)
      const TrendIndicator = await importTrendIndicator()
      const trendData = createMockTrendData({
        metricHistory: [72, 72.5, 72, 72.5, 72, 72.5, 72],
        weekOverWeekChange: 0.5,
        consecutiveDays: 1,
        daysOnReport: 1,
      })

      // When: The TrendIndicator component renders
      render(React.createElement(TrendIndicator, { trendData, priority: 'OEE' }))

      // Then: The sparkline line stroke color is gray
      const line = screen.getByTestId('sparkline-line')
      expect(line.getAttribute('data-stroke')).toMatch(/gray|#9ca3af|#6b7280|#d1d5db/)
    })

    it('UNIT-024: Sparkline handles null values in metricHistory gracefully', async () => {
      // Given: An action item has trendData with null values in metricHistory
      const TrendIndicator = await importTrendIndicator()
      const trendData = createMockTrendData({
        metricHistory: [72.5, null, 68.3, null, 69.2, 73.8, 72.5],
        weekOverWeekChange: 0.0,
        consecutiveDays: 1,
        daysOnReport: 3,
      })

      // When: The TrendIndicator component renders
      render(React.createElement(TrendIndicator, { trendData, priority: 'OEE' }))

      // Then: A sparkline is rendered connecting only the non-null data points without errors
      const chart = screen.getByTestId('sparkline-chart')
      expect(chart).toBeInTheDocument()
    })

    it('UNIT-025: Sparkline handles all-null metricHistory gracefully', async () => {
      // Given: An action item has trendData with metricHistory = [null, null, null, null, null, null, null]
      const TrendIndicator = await importTrendIndicator()
      const trendData = createMockTrendData({
        metricHistory: [null, null, null, null, null, null, null],
        weekOverWeekChange: null,
        consecutiveDays: 1,
        daysOnReport: 1,
      })

      // When: The TrendIndicator component renders
      render(React.createElement(TrendIndicator, { trendData, priority: 'OEE' }))

      // Then: No sparkline is rendered (graceful degradation) and no error is thrown
      const chart = screen.queryByTestId('sparkline-chart')
      expect(chart).toBeNull()
    })

    it('UNIT-026: Sparkline renders with empty metricHistory array', async () => {
      // Given: An action item has trendData with metricHistory = []
      const TrendIndicator = await importTrendIndicator()
      const trendData = createMockTrendData({
        metricHistory: [],
        weekOverWeekChange: 2.0,
        consecutiveDays: 1,
        daysOnReport: 1,
      })

      // When: The TrendIndicator component renders
      render(React.createElement(TrendIndicator, { trendData, priority: 'OEE' }))

      // Then: No sparkline is rendered (graceful degradation) and no error is thrown
      const chart = screen.queryByTestId('sparkline-chart')
      expect(chart).toBeNull()
    })

    it('UNIT-027: Sparkline renders without animation', async () => {
      // Given: An action item has valid trendData with metricHistory
      const TrendIndicator = await importTrendIndicator()
      const trendData = createMockTrendData({
        metricHistory: [70, 71, 72, 73, 74, 75, 76],
        weekOverWeekChange: 2.5,
        consecutiveDays: 1,
        daysOnReport: 1,
      })

      // When: The TrendIndicator component renders
      render(React.createElement(TrendIndicator, { trendData, priority: 'OEE' }))

      // Then: The Recharts LineChart renders with isAnimationActive={false} for instant display
      const line = screen.getByTestId('sparkline-line')
      expect(line.getAttribute('data-animation')).toBe('false')
    })
  })

  // =========================================================================
  // AC5: Skeleton placeholder when trend data is loading or unavailable
  // =========================================================================
  describe('AC5: Skeleton Placeholder for Loading/Unavailable Trend Data', () => {
    it('UNIT-033: Skeleton placeholder shown when isLoading is true', async () => {
      // Given: The TrendIndicator component receives isLoading = true and no trendData
      const TrendIndicator = await importTrendIndicator()

      // When: The component renders
      render(React.createElement(TrendIndicator, { isLoading: true, trendData: undefined, priority: 'OEE' }))

      // Then: A compact skeleton placeholder is displayed (animated pulse divs)
      const skeleton = screen.getByTestId('trend-indicator-skeleton')
      expect(skeleton).toBeInTheDocument()
      expect(skeleton.className).toMatch(/animate-pulse|pulse/)
    })

    it('UNIT-035: Skeleton placeholder has correct approximate dimensions', async () => {
      // Given: The TrendIndicator component receives isLoading = true
      const TrendIndicator = await importTrendIndicator()

      // When: The component renders
      render(React.createElement(TrendIndicator, { isLoading: true, trendData: undefined, priority: 'OEE' }))

      // Then: The skeleton placeholder area is approximately the same size as the actual trend indicators
      const skeleton = screen.getByTestId('trend-indicator-skeleton')
      expect(skeleton).toBeInTheDocument()
    })

    it('UNIT-036: TrendIndicator does not render when trendData is undefined and isLoading is false', async () => {
      // Given: TrendIndicator receives trendData = undefined and isLoading = false
      const TrendIndicator = await importTrendIndicator()

      // When: The component renders
      const { container } = render(
        React.createElement(TrendIndicator, { trendData: undefined, isLoading: false, priority: 'OEE' })
      )

      // Then: Nothing is rendered (no empty space, no skeleton, no indicators)
      expect(container.innerHTML).toBe('')
    })
  })

  // =========================================================================
  // Edge Cases
  // =========================================================================
  describe('Edge Cases: Trend Arrow', () => {
    it('EDGE-001: weekOverWeekChange = NaN treated as unavailable', async () => {
      // Given: trendData with weekOverWeekChange = NaN
      const TrendIndicator = await importTrendIndicator()
      const trendData = createMockTrendData({
        weekOverWeekChange: NaN,
      })

      // When: The TrendIndicator component renders
      render(React.createElement(TrendIndicator, { trendData, priority: 'OEE' }))

      // Then: No trend arrow is shown (NaN treated as unavailable)
      const arrowContainer = screen.queryByTestId('trend-arrow')
      expect(arrowContainer).toBeNull()
    })

    it('EDGE-002: weekOverWeekChange = -0 treated as stable', async () => {
      // Given: trendData with weekOverWeekChange = -0 (negative zero)
      const TrendIndicator = await importTrendIndicator()
      const trendData = createMockTrendData({
        weekOverWeekChange: -0,
      })

      // When: The TrendIndicator component renders
      render(React.createElement(TrendIndicator, { trendData, priority: 'OEE' }))

      // Then: Gray horizontal arrow displayed (stable)
      const arrowContainer = screen.getByTestId('trend-arrow')
      expect(arrowContainer.className).toMatch(/gray|text-gray|text-muted/)
    })

    it('EDGE-003: Extremely large weekOverWeekChange displays without overflow', async () => {
      // Given: Very large weekOverWeekChange value
      const TrendIndicator = await importTrendIndicator()
      const trendData = createMockTrendData({
        weekOverWeekChange: 500.0,
      })

      // When: The TrendIndicator component renders
      render(React.createElement(TrendIndicator, { trendData, priority: 'OEE' }))

      // Then: The percentage is displayed without layout overflow
      const percentText = screen.getByText(/\+500\.0%/i)
      expect(percentText).toBeInTheDocument()
    })

    it('EDGE-004: metricHistory with fewer than 7 data points still renders sparkline', async () => {
      // Given: metricHistory with only 3 data points
      const TrendIndicator = await importTrendIndicator()
      const trendData = createMockTrendData({
        metricHistory: [72.5, 74.1, 68.3],
        weekOverWeekChange: 2.5,
      })

      // When: The TrendIndicator component renders
      render(React.createElement(TrendIndicator, { trendData, priority: 'OEE' }))

      // Then: Sparkline still renders with available data
      const chart = screen.getByTestId('sparkline-chart')
      expect(chart).toBeInTheDocument()
    })

    it('EDGE-005: metricHistory with all identical values renders flat sparkline', async () => {
      // Given: metricHistory with all identical values
      const TrendIndicator = await importTrendIndicator()
      const trendData = createMockTrendData({
        metricHistory: [72, 72, 72, 72, 72, 72, 72],
        weekOverWeekChange: 0,
      })

      // When: The TrendIndicator component renders
      render(React.createElement(TrendIndicator, { trendData, priority: 'OEE' }))

      // Then: Sparkline renders (flat line)
      const chart = screen.getByTestId('sparkline-chart')
      expect(chart).toBeInTheDocument()
    })

    it('EDGE-006: Negative metricHistory values render sparkline correctly', async () => {
      // Given: metricHistory with negative values (edge case for financial data)
      const TrendIndicator = await importTrendIndicator()
      const trendData = createMockTrendData({
        metricHistory: [-10, -5, -15, -8, -12, -3, -7],
        weekOverWeekChange: -3.0,
      })

      // When: The TrendIndicator component renders
      render(React.createElement(TrendIndicator, { trendData, priority: 'FINANCIAL' }))

      // Then: Sparkline renders without errors
      const chart = screen.getByTestId('sparkline-chart')
      expect(chart).toBeInTheDocument()
    })
  })
})
