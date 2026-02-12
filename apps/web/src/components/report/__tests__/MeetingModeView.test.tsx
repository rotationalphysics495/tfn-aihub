/**
 * MeetingModeView Component Tests (Story 18.1: Meeting Mode Toggle & Talking Points View)
 *
 * TDD tests — these MUST FAIL until the MeetingModeView component is implemented.
 * Tests cover section grouping, item limiting/sorting, and empty state handling.
 *
 * @see Story 18.1 - Meeting Mode Toggle & Talking Points View
 * @see AC #1 - Condensed layout with section headers and top 3-5 items
 */

import { render, screen, within } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), back: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => '/',
  useParams: () => ({}),
}))

vi.mock('@/lib/supabase/client', () => ({
  createClient: () => ({
    auth: {
      getSession: vi.fn().mockResolvedValue({
        data: { session: { access_token: 'mock-token' } },
      }),
    },
  }),
}))

const mockFetch = vi.fn()
global.fetch = mockFetch

// ---------------------------------------------------------------------------
// Imports (AFTER mocks)
// ---------------------------------------------------------------------------

import { MeetingModeView } from '../MeetingModeView'
import type { ActionItem } from '@/components/action-engine/types'

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const createMockActionItem = (overrides: Partial<ActionItem> = {}): ActionItem => ({
  id: 'action-test-1',
  priority: 'FINANCIAL',
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
    type: 'financial_loss',
    data: {
      downtimeCost: 1500,
      wasteCost: 500,
      totalLoss: 2000,
      breakdown: [],
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

/**
 * Helper to create an action item with a specific category.
 * Category maps to priority: safety → SAFETY, oee → OEE, financial → FINANCIAL
 */
function createItemForCategory(
  category: 'safety' | 'oee' | 'financial',
  id: string,
  priorityScore = 500
): ActionItem {
  const priorityMap = { safety: 'SAFETY', oee: 'OEE', financial: 'FINANCIAL' } as const
  const evidenceTypeMap = {
    safety: 'safety_event',
    oee: 'oee_deviation',
    financial: 'financial_loss',
  } as const

  const evidenceDataMap = {
    safety: {
      eventId: `evt-${id}`,
      detectedAt: '2026-02-10T06:00:00Z',
      reasonCode: 'VIBRATION_ANOMALY',
      severity: 'HIGH',
      assetName: `Asset-${id}`,
    },
    oee: {
      targetOEE: 85,
      actualOEE: 72,
      deviation: -13,
      timeframe: '2026-02-10 Day Shift',
    },
    financial: {
      downtimeCost: 1500,
      wasteCost: 500,
      totalLoss: 2000,
      breakdown: [],
    },
  }

  return createMockActionItem({
    id: `action-${category}-${id}`,
    priority: priorityMap[category],
    priorityScore,
    recommendation: {
      text: `Action for ${category} item ${id}`,
      summary: `${category} action ${id}`,
    },
    asset: {
      id: `asset-${id}`,
      name: `Asset-${id}`,
      area: 'Production',
    },
    evidence: {
      type: evidenceTypeMap[category],
      data: evidenceDataMap[category] as any,
      source: {
        table: 'daily_summaries',
        date: '2026-02-10',
        recordId: `rec-${id}`,
      },
    },
  })
}

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: Meeting Mode View (Story 18.1)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockReset()
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
  // AC1: Section grouping and headers
  // =========================================================================
  describe('AC1: Section headers and item grouping', () => {
    it('UNIT-007: MeetingModeView groups items into three section headers', () => {
      // Given: MeetingModeView is rendered with action items spanning all three categories
      const items: ActionItem[] = [
        createItemForCategory('safety', '1', 900),
        createItemForCategory('oee', '2', 600),
        createItemForCategory('financial', '3', 700),
      ]

      // When: The component mounts
      render(<MeetingModeView items={items} />)

      // Then: Three section headers are rendered
      expect(screen.getByText('Safety')).toBeInTheDocument()
      expect(screen.getByText("Yesterday's Performance")).toBeInTheDocument()
      expect(screen.getByText("Today's Priorities")).toBeInTheDocument()

      // And: Each section contains its corresponding action item card
      // Safety section should contain the safety item
      expect(screen.getByText('Action for safety item 1')).toBeInTheDocument()
      // Yesterday's Performance section should contain the oee item
      expect(screen.getByText('Action for oee item 2')).toBeInTheDocument()
      // Today's Priorities section should contain the financial item
      expect(screen.getByText('Action for financial item 3')).toBeInTheDocument()
    })

    it('UNIT-008: MeetingModeView limits display to top 3-5 items sorted by priority', () => {
      // Given: MeetingModeView is rendered with 10 action items of varying priority scores
      const items: ActionItem[] = [
        createItemForCategory('safety', '1', 1000),   // #1 - SAFETY highest
        createItemForCategory('safety', '2', 950),     // #2
        createItemForCategory('financial', '3', 900),   // #3
        createItemForCategory('financial', '4', 850),   // #4
        createItemForCategory('oee', '5', 800),         // #5 - cutoff
        createItemForCategory('oee', '6', 750),         // #6 - excluded
        createItemForCategory('safety', '7', 700),      // #7 - excluded
        createItemForCategory('financial', '8', 650),    // #8 - excluded
        createItemForCategory('oee', '9', 600),          // #9 - excluded
        createItemForCategory('financial', '10', 550),   // #10 - excluded
      ]

      // When: The component mounts
      render(<MeetingModeView items={items} />)

      // Then: Only the top 5 items are rendered as MeetingTalkingPoint cards
      expect(screen.getByText('Action for safety item 1')).toBeInTheDocument()
      expect(screen.getByText('Action for safety item 2')).toBeInTheDocument()
      expect(screen.getByText('Action for financial item 3')).toBeInTheDocument()
      expect(screen.getByText('Action for financial item 4')).toBeInTheDocument()
      expect(screen.getByText('Action for oee item 5')).toBeInTheDocument()

      // And: Items ranked 6-10 are not visible
      expect(screen.queryByText('Action for oee item 6')).not.toBeInTheDocument()
      expect(screen.queryByText('Action for safety item 7')).not.toBeInTheDocument()
      expect(screen.queryByText('Action for financial item 8')).not.toBeInTheDocument()
      expect(screen.queryByText('Action for oee item 9')).not.toBeInTheDocument()
      expect(screen.queryByText('Action for financial item 10')).not.toBeInTheDocument()
    })

    it('UNIT-009: MeetingModeView shows "No items" for empty sections', () => {
      // Given: MeetingModeView is rendered with 2 oee items and 0 safety/financial items
      const items: ActionItem[] = [
        createItemForCategory('oee', '1', 800),
        createItemForCategory('oee', '2', 700),
      ]

      // When: The component mounts
      render(<MeetingModeView items={items} />)

      // Then: The "Safety" section header is still rendered
      expect(screen.getByText('Safety')).toBeInTheDocument()

      // And: The "Today's Priorities" section header is still rendered
      expect(screen.getByText("Today's Priorities")).toBeInTheDocument()

      // And: Empty sections display "No items" text
      const noItemsElements = screen.getAllByText(/no items/i)
      expect(noItemsElements.length).toBeGreaterThanOrEqual(2)

      // And: The "Yesterday's Performance" section renders its 2 items
      expect(screen.getByText("Yesterday's Performance")).toBeInTheDocument()
      expect(screen.getByText('Action for oee item 1')).toBeInTheDocument()
      expect(screen.getByText('Action for oee item 2')).toBeInTheDocument()
    })
  })

  // =========================================================================
  // Edge cases: fewer items / empty
  // =========================================================================
  describe('Edge cases: item count boundaries', () => {
    it('UNIT-010: MeetingModeView renders correctly with fewer than 3 items', () => {
      // Given: MeetingModeView is rendered with only 1 action item
      const items: ActionItem[] = [
        createItemForCategory('safety', '1', 900),
      ]

      // When: The component mounts
      render(<MeetingModeView items={items} />)

      // Then: The single item is rendered as a MeetingTalkingPoint card
      expect(screen.getByText('Action for safety item 1')).toBeInTheDocument()

      // And: The two empty sections show "No items"
      const noItemsElements = screen.getAllByText(/no items/i)
      expect(noItemsElements.length).toBeGreaterThanOrEqual(2)

      // And: No errors are thrown (the component renders without crashing)
      expect(screen.getByText('Safety')).toBeInTheDocument()
      expect(screen.getByText("Yesterday's Performance")).toBeInTheDocument()
      expect(screen.getByText("Today's Priorities")).toBeInTheDocument()
    })

    it('UNIT-011: MeetingModeView renders correctly with 0 items', () => {
      // Given: MeetingModeView is rendered with an empty action items array
      const items: ActionItem[] = []

      // When: The component mounts
      render(<MeetingModeView items={items} />)

      // Then: All three section headers are visible
      expect(screen.getByText('Safety')).toBeInTheDocument()
      expect(screen.getByText("Yesterday's Performance")).toBeInTheDocument()
      expect(screen.getByText("Today's Priorities")).toBeInTheDocument()

      // And: Each section shows "No items" text
      const noItemsElements = screen.getAllByText(/no items/i)
      expect(noItemsElements).toHaveLength(3)

      // And: No MeetingTalkingPoint cards are rendered
      expect(screen.queryAllByRole('article')).toHaveLength(0)
    })
  })
})
