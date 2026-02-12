/**
 * InsightSection Trend Integration Tests (Story 14.4: Trend Indicators on Action Cards)
 *
 * TDD tests — these MUST FAIL until InsightSection is updated to accept and render trend data.
 * Tests cover integration of TrendIndicator and RepeatOffenderBadge into InsightSection,
 * InsightEvidenceCard prop passing, barrel exports, and responsive layout.
 *
 * @see Story 14.4 - Trend Indicators on Action Cards
 * @see AC #5 - Skeleton placeholder / loading state integration
 * @see AC #7 - Responsive layout on tablet viewport
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

const mockGetSession = vi.fn()
vi.mock('@/lib/supabase/client', () => ({
  createClient: () => ({
    auth: { getSession: mockGetSession },
    from: () => ({
      insert: () => ({
        select: () => ({
          single: () => Promise.resolve({ data: null, error: null }),
        }),
      }),
    }),
  }),
}))

const mockFetch = vi.fn()
global.fetch = mockFetch

// Mock Recharts for sparkline tests
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
    }),
}))

// ---------------------------------------------------------------------------
// Imports (AFTER mocks)
// ---------------------------------------------------------------------------

import { InsightSection } from '../InsightSection'
import type { ActionItem } from '../types'

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
  consecutiveDays: 3,
  daysOnReport: 5,
  metricHistory: [70, 71, 72, 73, 74, 75, 76],
  weekOverWeekChange: 3.5,
  ...overrides,
})

const createMockActionItem = (overrides: Partial<ActionItem> = {}): ActionItem => ({
  id: 'action-42',
  priority: 'OEE',
  priorityScore: 750,
  recommendation: {
    text: 'Investigate downtime on Grinder 5',
    summary: 'Downtime investigation needed',
  },
  asset: {
    id: 'asset-001',
    name: 'Grinder 5',
    area: 'Grinding Area',
  },
  evidence: {
    type: 'oee_deviation',
    data: {
      targetOEE: 85,
      actualOEE: 72,
      deviation: -13,
      timeframe: 'Yesterday (T-1)',
    },
    source: {
      table: 'daily_summaries',
      date: '2026-02-10',
      recordId: 'rec-001',
    },
  },
  financialImpact: 2000,
  timestamp: '2026-02-11T08:00:00Z',
  ...overrides,
})

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: InsightSection Trend Integration (Story 14.4)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockReset()
    mockGetSession.mockReset()

    mockGetSession.mockResolvedValue({
      data: { session: { access_token: 'mock-token-abc' } },
    })
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ members: [] }),
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // =========================================================================
  // AC5: InsightSection passes loading state to TrendIndicator
  // =========================================================================
  describe('AC5: Loading State Integration', () => {
    it('INT-001: InsightSection passes loading state to TrendIndicator', () => {
      // Given: InsightSection receives isLoading = true and trendData = undefined
      // When: The component renders
      render(
        <InsightSection
          priority="OEE"
          recommendation={{ text: 'Test recommendation', summary: 'Test' }}
          asset={{ id: 'asset-1', name: 'Grinder 5', area: 'Grinding' }}
          financialImpact={2000}
          timestamp="2026-02-11T08:00:00Z"
          onAssign={() => {}}
          isLoading={true}
          trendData={undefined}
        />
      )

      // Then: The TrendIndicator within InsightSection shows a skeleton state
      const skeleton = screen.getByTestId('trend-indicator-skeleton')
      expect(skeleton).toBeInTheDocument()
      expect(skeleton.className).toMatch(/animate-pulse|pulse/)
    })

    it('INT-004: InsightEvidenceCard renders without trend data (graceful degradation)', async () => {
      // Given: An action item has no trendData (undefined) and isLoading is false
      const item = createMockActionItem()

      // When: The InsightEvidenceCard renders
      const { InsightEvidenceCard } = await import('../InsightEvidenceCard')
      render(<InsightEvidenceCard item={item} />)

      // Then: The card renders fully with PriorityBadge, recommendation text, asset name
      expect(screen.getByText(/investigate downtime/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/view asset details for grinder 5/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/priority: oee/i)).toBeInTheDocument()

      // And: The trend indicator area is empty (no error thrown)
      expect(screen.queryByTestId('trend-arrow')).toBeNull()
      expect(screen.queryByTestId('sparkline-chart')).toBeNull()
    })
  })

  // =========================================================================
  // AC7: Responsive layout - Trend indicators render within InsightSection
  // =========================================================================
  describe('AC7: Layout Integration', () => {
    it('INT-002: Trend indicators render within InsightSection layout', () => {
      // Given: An InsightSection with trendData, priority, and all standard props
      const trendData = createMockTrendData({
        consecutiveDays: 3,
        daysOnReport: 5,
        metricHistory: [70, 71, 72, 73, 74, 75, 76],
        weekOverWeekChange: 3.5,
      })

      // When: The component renders
      render(
        <InsightSection
          priority="OEE"
          recommendation={{ text: 'Test recommendation', summary: 'Test' }}
          asset={{ id: 'asset-1', name: 'Grinder 5', area: 'Grinding' }}
          financialImpact={2000}
          timestamp="2026-02-11T08:00:00Z"
          onAssign={() => {}}
          trendData={trendData}
        />
      )

      // Then: RepeatOffenderBadge appears with the PriorityBadge
      expect(screen.getByText(/3rd day in a row/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/priority: oee/i)).toBeInTheDocument()

      // And: TrendIndicator appears with sparkline and trend arrow
      expect(screen.getByTestId('trend-arrow')).toBeInTheDocument()
      expect(screen.getByTestId('sparkline-chart')).toBeInTheDocument()
    })

    it('INT-003: InsightEvidenceCard passes trendData to InsightSection', async () => {
      // Given: An InsightEvidenceCard renders with an ActionItem that has trendData
      const trendData = createMockTrendData({
        consecutiveDays: 3,
        daysOnReport: 5,
        metricHistory: [70, 71, 72, 73, 74, 75, 76],
        weekOverWeekChange: 3.5,
      })

      const item = createMockActionItem({
        trendData,
      })

      // When: The card renders
      const { InsightEvidenceCard } = await import('../InsightEvidenceCard')
      render(<InsightEvidenceCard item={item} />)

      // Then: The InsightSection child receives the trendData prop and renders trend indicators
      expect(screen.getByText(/3rd day in a row/i)).toBeInTheDocument()
      expect(screen.getByTestId('trend-arrow')).toBeInTheDocument()
      expect(screen.getByTestId('sparkline-chart')).toBeInTheDocument()
    })

    it('INT-004: Layout does not overflow when all trend elements are present', () => {
      // Given: An InsightSection with all trend elements and long recommendation text
      const trendData = createMockTrendData({
        consecutiveDays: 5,
        daysOnReport: 6,
        weekOverWeekChange: -8.5,
      })

      const longRecommendation =
        'Investigate the extended downtime pattern on Grinder 5 in the Grinding Area which has been recurring for multiple days'

      // When: The component renders at md breakpoint
      render(
        <InsightSection
          priority="FINANCIAL"
          recommendation={{ text: longRecommendation, summary: 'Downtime investigation' }}
          asset={{ id: 'asset-1', name: 'Grinder 5', area: 'Grinding Area' }}
          financialImpact={5000}
          timestamp="2026-02-11T08:00:00Z"
          onAssign={() => {}}
          trendData={trendData}
        />
      )

      // Then: All trend elements render without error
      expect(screen.getByText(/5th day in a row/i)).toBeInTheDocument()
      expect(screen.getByTestId('trend-arrow')).toBeInTheDocument()
      expect(screen.getByTestId('sparkline-chart')).toBeInTheDocument()
      expect(screen.getByText(longRecommendation)).toBeInTheDocument()

      // And: No horizontal overflow occurs (container does not have overflow-x)
      const container = screen.getByText(longRecommendation).closest('[class*="flex-col"]')
      expect(container).toBeTruthy()
    })
  })

  // =========================================================================
  // Barrel File Exports
  // =========================================================================
  describe('Barrel File Exports', () => {
    it('INT-005: TrendIndicator and RepeatOffenderBadge exported from barrel index', async () => {
      // Given: The action-engine index.ts barrel export file
      // When: A consumer imports from the barrel
      const barrel = await import('../index')

      // Then: TrendIndicator is exported and is a valid React component
      expect((barrel as Record<string, unknown>).TrendIndicator).toBeDefined()
      expect(typeof (barrel as Record<string, unknown>).TrendIndicator).toBe('function')

      // And: RepeatOffenderBadge is exported and is a valid React component
      expect((barrel as Record<string, unknown>).RepeatOffenderBadge).toBeDefined()
      expect(typeof (barrel as Record<string, unknown>).RepeatOffenderBadge).toBe('function')
    })
  })
})
