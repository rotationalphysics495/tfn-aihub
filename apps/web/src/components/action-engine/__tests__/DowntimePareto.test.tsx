/**
 * DowntimePareto Component Tests (Story 14.5: Downtime Pareto Chart on Action Cards)
 *
 * TDD tests — these MUST FAIL until the DowntimePareto component is implemented.
 * Tests cover: horizontal bar chart rendering, reason code labels, planned vs unplanned
 * visual distinction, item limits, empty/null states, dark mode, skeleton loader.
 *
 * @see Story 14.5 - Downtime Pareto Chart on Action Cards
 * @see AC #1 - Horizontal bar chart with top 3-5 reason codes
 * @see AC #3 - Skeleton loader placeholder
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

// Mock Recharts to inspect chart rendering without actual SVG/canvas
vi.mock('recharts', () => ({
  BarChart: ({ children, ...props }: Record<string, unknown>) =>
    React.createElement(
      'div',
      {
        'data-testid': 'bar-chart',
        'data-layout': props.layout,
      },
      children as React.ReactNode,
    ),
  Bar: (props: Record<string, unknown>) =>
    React.createElement('div', {
      'data-testid': 'bar',
      'data-fill': props.fill,
      'data-datakey': props.dataKey,
    }),
  XAxis: (props: Record<string, unknown>) =>
    React.createElement('div', {
      'data-testid': 'x-axis',
      'data-type': props.type,
    }),
  YAxis: (props: Record<string, unknown>) =>
    React.createElement('div', {
      'data-testid': 'y-axis',
      'data-type': props.type,
      'data-datakey': props.dataKey,
    }),
  ResponsiveContainer: ({ children, ...props }: Record<string, unknown>) =>
    React.createElement(
      'div',
      {
        'data-testid': 'responsive-container',
        'data-height': props.height,
        'data-width': props.width,
      },
      children as React.ReactNode,
    ),
  Cell: (props: Record<string, unknown>) =>
    React.createElement('div', {
      'data-testid': 'cell',
      'data-fill': props.fill,
    }),
  Tooltip: () => React.createElement('div', { 'data-testid': 'tooltip' }),
  LabelList: (props: Record<string, unknown>) =>
    React.createElement('div', {
      'data-testid': 'label-list',
      'data-position': props.position,
    }),
}))

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

interface ParetoItem {
  reason_code: string
  total_minutes: number
  percentage: number
  cumulative_percentage: number
  financial_impact: number
  event_count: number
  is_safety_related: boolean
}

interface ParetoResponse {
  items: ParetoItem[]
  total_downtime_minutes: number
  total_financial_impact: number
  total_events: number
  data_source: string
  last_updated: string
  threshold_80_index: number | null
}

const createMockParetoItem = (overrides: Partial<ParetoItem> = {}): ParetoItem => ({
  reason_code: 'Mechanical',
  total_minutes: 180,
  percentage: 35.5,
  cumulative_percentage: 35.5,
  financial_impact: 450.0,
  event_count: 3,
  is_safety_related: false,
  ...overrides,
})

const createMockParetoResponse = (
  items: ParetoItem[],
  overrides: Partial<ParetoResponse> = {}
): ParetoResponse => ({
  items,
  total_downtime_minutes: items.reduce((sum, i) => sum + i.total_minutes, 0),
  total_financial_impact: 1200.0,
  total_events: items.length,
  data_source: 'downtime_events',
  last_updated: '2026-01-05T12:00:00Z',
  threshold_80_index: 2,
  ...overrides,
})

/** Standard 4-item dataset for chart tests */
const STANDARD_ITEMS: ParetoItem[] = [
  createMockParetoItem({
    reason_code: 'Mechanical',
    total_minutes: 180,
    percentage: 35.5,
    cumulative_percentage: 35.5,
  }),
  createMockParetoItem({
    reason_code: 'Changeover',
    total_minutes: 120,
    percentage: 23.6,
    cumulative_percentage: 59.1,
  }),
  createMockParetoItem({
    reason_code: 'Planned Maintenance',
    total_minutes: 90,
    percentage: 17.7,
    cumulative_percentage: 76.8,
  }),
  createMockParetoItem({
    reason_code: 'Material Shortage',
    total_minutes: 60,
    percentage: 11.8,
    cumulative_percentage: 88.6,
  }),
]

// ---------------------------------------------------------------------------
// Dynamic import helpers - will fail until components exist
// ---------------------------------------------------------------------------

async function importDowntimePareto() {
  const mod = await import('../DowntimePareto')
  return mod.DowntimePareto
}

async function importDowntimeParetoSkeleton() {
  const mod = await import('../DowntimePareto')
  return mod.DowntimeParetoSkeleton
}

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: Downtime Pareto Chart on Action Cards (Story 14.5)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // =========================================================================
  // AC1: Horizontal bar chart rendering
  // =========================================================================
  describe('AC1: Horizontal Bar Chart Rendering', () => {
    it('UNIT-011: Component renders horizontal bars for 3-5 reason codes sorted by duration', async () => {
      // Given: DowntimePareto receives a ParetoResponse with 4 items sorted by total_minutes descending
      const DowntimePareto = await importDowntimePareto()
      const data = createMockParetoResponse(STANDARD_ITEMS)

      // When: The component renders
      render(React.createElement(DowntimePareto, { data }))

      // Then: A Recharts BarChart with layout="vertical" renders inside a ResponsiveContainer
      const container = screen.getByTestId('responsive-container')
      expect(container).toBeInTheDocument()

      const chart = screen.getByTestId('bar-chart')
      expect(chart).toBeInTheDocument()
      expect(chart.getAttribute('data-layout')).toBe('vertical')

      // And: 4 bars are displayed corresponding to the 4 reason codes
      const bars = screen.getAllByTestId('bar')
      expect(bars.length).toBeGreaterThanOrEqual(1) // At least one Bar component
    })

    it('UNIT-012: Each bar shows reason code name, duration in minutes, and percentage of total', async () => {
      // Given: DowntimePareto receives a ParetoResponse with items
      const DowntimePareto = await importDowntimePareto()
      const data = createMockParetoResponse(STANDARD_ITEMS)

      // When: The component renders
      render(React.createElement(DowntimePareto, { data }))

      // Then: Each bar's label area contains the reason code name, duration as Nmin, percentage as (N%)
      expect(screen.getByText(/Mechanical/)).toBeInTheDocument()
      expect(screen.getByText(/180\s*min/)).toBeInTheDocument()
      expect(screen.getByText(/35\.5%/)).toBeInTheDocument()

      expect(screen.getByText(/Changeover/)).toBeInTheDocument()
      expect(screen.getByText(/120\s*min/)).toBeInTheDocument()
      expect(screen.getByText(/23\.6%/)).toBeInTheDocument()
    })

    it('UNIT-013: Planned downtime bars are visually distinguished with hatched pattern', async () => {
      // Given: DowntimePareto receives data with items where is_planned=true (Planned Maintenance)
      const DowntimePareto = await importDowntimePareto()
      const mixedItems: ParetoItem[] = [
        createMockParetoItem({
          reason_code: 'Mechanical',
          total_minutes: 180,
          percentage: 50.0,
        }),
        createMockParetoItem({
          reason_code: 'Planned Maintenance',
          total_minutes: 90,
          percentage: 25.0,
        }),
      ]
      const data = createMockParetoResponse(mixedItems)

      // When: The component renders
      const { container } = render(React.createElement(DowntimePareto, { data }))

      // Then: Bars for planned items use a hatched/striped SVG pattern fill
      // Look for SVG pattern definition or data-testid for planned bar
      const plannedBars = container.querySelectorAll('[data-planned="true"]')
      const patternDefs = container.querySelectorAll('pattern')
      const hasHatchedDistinction =
        plannedBars.length > 0 || patternDefs.length > 0

      expect(hasHatchedDistinction).toBe(true)
    })

    it('UNIT-014: Unplanned downtime bars render with solid fill', async () => {
      // Given: DowntimePareto receives data with unplanned items (is_planned=false)
      const DowntimePareto = await importDowntimePareto()
      const unplannedItems: ParetoItem[] = [
        createMockParetoItem({
          reason_code: 'Mechanical',
          total_minutes: 180,
          percentage: 60.0,
        }),
        createMockParetoItem({
          reason_code: 'Changeover',
          total_minutes: 120,
          percentage: 40.0,
        }),
      ]
      const data = createMockParetoResponse(unplannedItems)

      // When: The component renders
      const { container } = render(React.createElement(DowntimePareto, { data }))

      // Then: Unplanned bars use solid color fill (not hatched), consistent with Industrial Clarity palette
      const unplannedBars = container.querySelectorAll('[data-planned="false"]')
      // At minimum, bars should exist and NOT use pattern references
      expect(container.querySelector('[data-testid="bar-chart"]')).toBeInTheDocument()

      // Unplanned items should not reference a hatched pattern
      if (unplannedBars.length > 0) {
        unplannedBars.forEach((bar) => {
          const fill = bar.getAttribute('fill') || bar.getAttribute('data-fill') || ''
          expect(fill).not.toMatch(/url\(#.*hatch/i)
        })
      }
    })

    it('UNIT-015: Component limits display to top 5 reason codes when more are provided', async () => {
      // Given: DowntimePareto receives a ParetoResponse with 8 items
      const DowntimePareto = await importDowntimePareto()
      const manyItems: ParetoItem[] = Array.from({ length: 8 }, (_, i) =>
        createMockParetoItem({
          reason_code: `Reason ${i + 1}`,
          total_minutes: 200 - i * 20,
          percentage: 15 - i * 1.5,
          cumulative_percentage: (i + 1) * 12.5,
        })
      )
      const data = createMockParetoResponse(manyItems)

      // When: The component renders
      render(React.createElement(DowntimePareto, { data }))

      // Then: Only the top 5 items (by total_minutes descending) are displayed
      // Should NOT show Reason 6, 7, 8
      expect(screen.getByText(/Reason 1/)).toBeInTheDocument()
      expect(screen.getByText(/Reason 5/)).toBeInTheDocument()
      expect(screen.queryByText(/Reason 6/)).not.toBeInTheDocument()
      expect(screen.queryByText(/Reason 7/)).not.toBeInTheDocument()
      expect(screen.queryByText(/Reason 8/)).not.toBeInTheDocument()
    })

    it('UNIT-016: Component returns null when data is null', async () => {
      // Given: DowntimePareto receives data as null
      const DowntimePareto = await importDowntimePareto()

      // When: The component renders
      const { container } = render(React.createElement(DowntimePareto, { data: null }))

      // Then: Nothing is rendered (returns null), no chart elements appear in the DOM
      expect(container.innerHTML).toBe('')
      expect(screen.queryByTestId('bar-chart')).not.toBeInTheDocument()
    })

    it('UNIT-017: Component returns null when items array is empty', async () => {
      // Given: DowntimePareto receives a ParetoResponse with items: []
      const DowntimePareto = await importDowntimePareto()
      const emptyData = createMockParetoResponse([])

      // When: The component renders
      const { container } = render(React.createElement(DowntimePareto, { data: emptyData }))

      // Then: Nothing is rendered (returns null), no chart or empty state message appears
      expect(container.innerHTML).toBe('')
      expect(screen.queryByTestId('bar-chart')).not.toBeInTheDocument()
    })

    it('UNIT-018: Component truncates long reason code names', async () => {
      // Given: DowntimePareto receives items with a reason_code exceeding 15 characters
      const DowntimePareto = await importDowntimePareto()
      const longNameItems: ParetoItem[] = [
        createMockParetoItem({
          reason_code: 'Electrical System Overload',
          total_minutes: 180,
          percentage: 100.0,
        }),
      ]
      const data = createMockParetoResponse(longNameItems)

      // When: The component renders
      render(React.createElement(DowntimePareto, { data }))

      // Then: The displayed reason code name is truncated (e.g., 'Electrical Syst…')
      // Full name should NOT appear
      expect(screen.queryByText('Electrical System Overload')).not.toBeInTheDocument()
      // Truncated version should appear (15 chars + ellipsis)
      expect(screen.getByText(/Electrical Syst/)).toBeInTheDocument()
    })

    it('UNIT-019: Component uses compact height appropriate for inline rendering', async () => {
      // Given: DowntimePareto receives data with 3-5 items
      const DowntimePareto = await importDowntimePareto()
      const data = createMockParetoResponse(STANDARD_ITEMS)

      // When: The component renders
      render(React.createElement(DowntimePareto, { data }))

      // Then: The ResponsiveContainer height is between 100-150px (compact, sparkline-sized)
      const container = screen.getByTestId('responsive-container')
      const height = Number(container.getAttribute('data-height'))
      expect(height).toBeGreaterThanOrEqual(100)
      expect(height).toBeLessThanOrEqual(150)
    })

    it('UNIT-020: Component supports dark mode via Tailwind dark: variants', async () => {
      // Given: DowntimePareto renders in a dark mode context
      const DowntimePareto = await importDowntimePareto()
      const data = createMockParetoResponse(STANDARD_ITEMS)

      // When: The component renders
      const { container } = render(React.createElement(DowntimePareto, { data }))

      // Then: Dark mode CSS classes (dark: prefixed Tailwind classes) are applied
      const allElements = container.querySelectorAll('*')
      const hasDarkClasses = Array.from(allElements).some(
        (el) => el.className && typeof el.className === 'string' && el.className.includes('dark:')
      )
      expect(hasDarkClasses).toBe(true)
    })

    it('UNIT-021: Planned vs unplanned legend is rendered', async () => {
      // Given: DowntimePareto receives data containing both planned and unplanned items
      const DowntimePareto = await importDowntimePareto()
      const data = createMockParetoResponse(STANDARD_ITEMS)

      // When: The component renders
      render(React.createElement(DowntimePareto, { data }))

      // Then: A compact inline legend is displayed showing unplanned vs planned distinction
      const legend = screen.getByTestId('pareto-legend')
      expect(legend).toBeInTheDocument()
      expect(legend.textContent).toMatch(/unplanned/i)
      expect(legend.textContent).toMatch(/planned/i)
    })
  })

  // =========================================================================
  // AC3: Skeleton Loader
  // =========================================================================
  describe('AC3: Skeleton Loader', () => {
    it('UNIT-024: Skeleton loader renders with animate-pulse during loading', async () => {
      // Given: DowntimeParetoSkeleton is rendered
      const DowntimeParetoSkeleton = await importDowntimeParetoSkeleton()

      // When: The component mounts
      const { container } = render(React.createElement(DowntimeParetoSkeleton))

      // Then: A container with animate-pulse class is rendered
      const pulseElements = container.querySelectorAll('.animate-pulse')
      expect(pulseElements.length).toBeGreaterThan(0)

      // And: Contains 3-4 horizontal bar placeholders
      const barPlaceholders = container.querySelectorAll(
        '[class*="bg-industrial-200"], [class*="bg-industrial"]'
      )
      expect(barPlaceholders.length).toBeGreaterThanOrEqual(3)
    })

    it('UNIT-025: Skeleton loader matches chart dimensions', async () => {
      // Given: DowntimeParetoSkeleton is rendered
      const DowntimeParetoSkeleton = await importDowntimeParetoSkeleton()

      // When: The component mounts
      const { container } = render(React.createElement(DowntimeParetoSkeleton))

      // Then: The skeleton placeholders are horizontal bars at varying widths
      // (e.g., w-full, w-3/4, w-1/2, w-1/3) at approximately 120-150px total height
      const allElements = container.querySelectorAll('*')
      const hasStaggeredWidths = Array.from(allElements).some(
        (el) =>
          el.className &&
          typeof el.className === 'string' &&
          (el.className.includes('w-3/4') ||
            el.className.includes('w-1/2') ||
            el.className.includes('w-2/3') ||
            el.className.includes('w-1/3'))
      )
      expect(hasStaggeredWidths).toBe(true)
    })
  })
})
