/**
 * All Items Reviewed Banner & Integration Tests (Story 13.2: Action Acknowledgment UI)
 *
 * TDD tests — these MUST FAIL until the "All items reviewed" banner and
 * acknowledgment integration are implemented in InsightEvidenceCardList.
 *
 * @see Story 13.2 - Action Acknowledgment UI
 * @see AC #4 - "All items reviewed" summary
 * @see AC #3 - Integration with acknowledged/unacknowledged mix
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
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

const mockGetSession = vi.fn()
vi.mock('@/lib/supabase/client', () => ({
  createClient: () => ({
    auth: { getSession: mockGetSession },
    from: () => ({ insert: () => ({ select: () => ({ single: () => Promise.resolve({ data: null, error: null }) }) }) }),
  }),
}))

const mockFetch = vi.fn()
global.fetch = mockFetch

// Mock useDailyActions for the InsightEvidenceCardList integration tests
const mockUseDailyActions = vi.fn()
vi.mock('@/hooks/useDailyActions', () => ({
  useDailyActions: () => mockUseDailyActions(),
}))

// ---------------------------------------------------------------------------
// Imports (AFTER mocks)
// ---------------------------------------------------------------------------

import { InsightEvidenceCardList } from '../InsightEvidenceCardList'
import { ActionCardList } from '../ActionCardList'
import type { ActionItem } from '../types'

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const createMockActionItem = (
  id: string,
  overrides: Partial<ActionItem> = {}
): ActionItem => ({
  id,
  priority: 'FINANCIAL',
  priorityScore: 750,
  recommendation: {
    text: `Recommendation for ${id}`,
    summary: `Summary for ${id}`,
  },
  asset: {
    id: `asset-${id}`,
    name: `Asset ${id}`,
    area: 'Area A',
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
      recordId: `rec-${id}`,
    },
  },
  financialImpact: 2000,
  timestamp: '2026-02-11T08:00:00Z',
  ...overrides,
})

const createMockAcknowledgment = (overrides: Record<string, unknown> = {}) => ({
  user_id: 'u1',
  acknowledged_at: '2026-02-11T08:30:00Z',
  note: null as string | null,
  ...overrides,
})

const createMockAPIActionItem = (id: string, acknowledged: boolean = false) => ({
  id,
  asset_id: `asset-${id}`,
  asset_name: `Asset ${id}`,
  priority_level: 'high' as const,
  category: 'financial' as const,
  primary_metric_value: '$2,000 loss',
  recommendation_text: `Recommendation for ${id}`,
  evidence_summary: `Summary for ${id}`,
  evidence_refs: [
    {
      table: 'daily_summaries',
      column: 'downtime_minutes',
      value: '120',
      record_id: `rec-${id}`,
    },
  ],
  created_at: '2026-02-11T08:00:00Z',
  financial_impact_usd: 2000,
  priority_rank: 2,
  title: `Action ${id}`,
  description: `Description for ${id}`,
  acknowledgment: acknowledged
    ? { user_id: 'u1', acknowledged_at: '2026-02-11T08:30:00Z', note: null }
    : null,
})

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: All Items Reviewed Banner (Story 13.2)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockReset()
    mockGetSession.mockReset()

    // Default: authenticated session
    mockGetSession.mockResolvedValue({
      data: { session: { access_token: 'mock-token-abc' } },
    })
    // Default: empty fetch (for team members endpoint)
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
  // AC4: "All items reviewed" banner
  // =========================================================================
  describe('AC4: "All Items Reviewed" Banner', () => {
    it('UNIT-024: "All items reviewed" banner renders when all items are acknowledged', () => {
      // Given: InsightEvidenceCardList has 5 action items and all 5 are acknowledged
      const items = Array.from({ length: 5 }, (_, i) =>
        createMockActionItem(`action-${i + 1}`, {
          acknowledgment: createMockAcknowledgment(),
        })
      )

      mockUseDailyActions.mockReturnValue({
        data: {
          actions: items.map((_, i) => createMockAPIActionItem(`action-${i + 1}`, true)),
          generated_at: '2026-02-11T06:00:00Z',
          report_date: '2026-02-11',
          total_count: 5,
          counts_by_category: { safety: 0, oee: 0, financial: 5 },
        },
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      })

      // When: The list renders
      render(<InsightEvidenceCardList />)

      // Then: A success banner is visible with "All items reviewed" text
      const banner = screen.getByText(/all items reviewed/i)
      expect(banner).toBeInTheDocument()

      // And: The count shows "5/5 reviewed"
      const count = screen.getByText(/5\/5 reviewed/i)
      expect(count).toBeInTheDocument()
    })

    it('UNIT-025: "All items reviewed" banner has correct green styling', () => {
      // Given: All items are acknowledged and the banner renders
      const items = Array.from({ length: 3 }, (_, i) =>
        createMockActionItem(`action-${i + 1}`, {
          acknowledgment: createMockAcknowledgment(),
        })
      )

      mockUseDailyActions.mockReturnValue({
        data: {
          actions: items.map((_, i) => createMockAPIActionItem(`action-${i + 1}`, true)),
          generated_at: '2026-02-11T06:00:00Z',
          report_date: '2026-02-11',
          total_count: 3,
          counts_by_category: { safety: 0, oee: 0, financial: 3 },
        },
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      })

      // When: The banner renders
      const { container } = render(<InsightEvidenceCardList />)

      // Then: The banner has the correct green styling classes
      const bannerEl = screen.getByText(/all items reviewed/i).closest('div')
      expect(bannerEl).toBeTruthy()
      const bannerClasses = bannerEl!.className
      expect(bannerClasses).toMatch(/bg-green-50/)
      expect(bannerClasses).toMatch(/border-green-200/)
    })

    it('UNIT-026: Banner does NOT render when some items are unacknowledged', () => {
      // Given: InsightEvidenceCardList has 5 items but only 3 are acknowledged
      const apiItems = [
        createMockAPIActionItem('action-1', true),
        createMockAPIActionItem('action-2', true),
        createMockAPIActionItem('action-3', true),
        createMockAPIActionItem('action-4', false),
        createMockAPIActionItem('action-5', false),
      ]

      mockUseDailyActions.mockReturnValue({
        data: {
          actions: apiItems,
          generated_at: '2026-02-11T06:00:00Z',
          report_date: '2026-02-11',
          total_count: 5,
          counts_by_category: { safety: 0, oee: 0, financial: 5 },
        },
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      })

      // When: The list renders
      render(<InsightEvidenceCardList />)

      // Then: The acknowledgment UI is present (Mark Reviewed buttons for unacknowledged items)
      const markReviewedButtons = screen.getAllByRole('button', { name: /mark reviewed/i })
      expect(markReviewedButtons).toHaveLength(2) // 2 unacknowledged items

      // And: Acknowledged items show "Reviewed" buttons
      const reviewedButtons = screen.getAllByRole('button', { name: /^reviewed$/i })
      expect(reviewedButtons).toHaveLength(3) // 3 acknowledged items

      // And: The "All items reviewed" banner is NOT present
      const banner = screen.queryByText(/all items reviewed/i)
      expect(banner).toBeNull()
    })

    it('UNIT-027: Banner does NOT render when there are zero action items', () => {
      // Given: InsightEvidenceCardList has 0 action items
      mockUseDailyActions.mockReturnValue({
        data: {
          actions: [],
          generated_at: '2026-02-11T06:00:00Z',
          report_date: '2026-02-11',
          total_count: 0,
          counts_by_category: { safety: 0, oee: 0, financial: 0 },
        },
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      })

      // When: The list renders
      render(<InsightEvidenceCardList />)

      // Then: The "All items reviewed" banner is NOT present (even though 0/0 is technically "all")
      const banner = screen.queryByText(/all items reviewed/i)
      expect(banner).toBeNull()

      // And: No acknowledge buttons are rendered
      const ackButtons = screen.queryAllByRole('button', { name: /mark reviewed|reviewed/i })
      // Filter out any Refresh button or other buttons
      const acknowledgeButtons = ackButtons.filter(
        (btn) => btn.textContent?.match(/reviewed/i)
      )
      expect(acknowledgeButtons).toHaveLength(0)

      // And: The empty state is shown instead
      const emptyState = screen.getByText(/all systems operating normally/i)
      expect(emptyState).toBeInTheDocument()

      // And: There is no review count indicator (e.g., "0/0 reviewed" should not appear)
      const reviewCount = screen.queryByText(/\d+\/\d+ reviewed/i)
      expect(reviewCount).toBeNull()

      // Verify the component integrates with acknowledgment tracking
      // by checking that the data-testid attribute exists on the list container
      // (will be added when useActionAcknowledgment is integrated)
      const { container } = render(<InsightEvidenceCardList />)
      const listWithTracking = container.querySelector('[data-acknowledgment-tracking]')
      expect(listWithTracking).toBeTruthy()
    })

    it('UNIT-028: Banner appears dynamically when last item is acknowledged', async () => {
      // Given: InsightEvidenceCardList has 3 items, 2 acknowledged, 1 not
      const apiItems = [
        createMockAPIActionItem('action-1', true),
        createMockAPIActionItem('action-2', true),
        createMockAPIActionItem('action-3', false),
      ]

      mockUseDailyActions.mockReturnValue({
        data: {
          actions: apiItems,
          generated_at: '2026-02-11T06:00:00Z',
          report_date: '2026-02-11',
          total_count: 3,
          counts_by_category: { safety: 0, oee: 0, financial: 3 },
        },
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      })

      // Mock the acknowledge API
      mockFetch.mockImplementation(async (url: string) => {
        if (url.includes('/acknowledge')) {
          return {
            ok: true,
            status: 200,
            json: async () => ({
              id: 'ack-3',
              action_item_id: 'action-3',
              user_id: 'u1',
              acknowledged_at: new Date().toISOString(),
              note: null,
              report_date: '2026-02-11',
            }),
          }
        }
        return { ok: true, status: 200, json: async () => ({ members: [] }) }
      })

      render(<InsightEvidenceCardList />)

      // When: The user clicks acknowledge on the last unacknowledged item
      const markReviewedButtons = screen.getAllByRole('button', { name: /mark reviewed/i })
      expect(markReviewedButtons).toHaveLength(1) // Only one unacknowledged

      fireEvent.click(markReviewedButtons[0])

      // Then: The banner appears after the optimistic update
      await waitFor(() => {
        const banner = screen.getByText(/all items reviewed/i)
        expect(banner).toBeInTheDocument()
      })

      // And: The count shows "3/3 reviewed"
      const count = screen.getByText(/3\/3 reviewed/i)
      expect(count).toBeInTheDocument()
    })

    it('UNIT-029: Banner shows correct count after acknowledging items incrementally', async () => {
      // Given: 4 total items, 0 initially acknowledged
      const apiItems = [
        createMockAPIActionItem('action-1', false),
        createMockAPIActionItem('action-2', false),
        createMockAPIActionItem('action-3', false),
        createMockAPIActionItem('action-4', false),
      ]

      mockUseDailyActions.mockReturnValue({
        data: {
          actions: apiItems,
          generated_at: '2026-02-11T06:00:00Z',
          report_date: '2026-02-11',
          total_count: 4,
          counts_by_category: { safety: 0, oee: 0, financial: 4 },
        },
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      })

      mockFetch.mockImplementation(async (url: string) => {
        if (url.includes('/acknowledge')) {
          const actionId = url.split('/actions/')[1]?.split('/')[0]
          return {
            ok: true,
            status: 200,
            json: async () => ({
              id: `ack-${actionId}`,
              action_item_id: actionId,
              user_id: 'u1',
              acknowledged_at: new Date().toISOString(),
              note: null,
              report_date: '2026-02-11',
            }),
          }
        }
        return { ok: true, status: 200, json: async () => ({ members: [] }) }
      })

      render(<InsightEvidenceCardList />)

      // When: Items are acknowledged one by one
      const markButtons = screen.getAllByRole('button', { name: /mark reviewed/i })
      expect(markButtons).toHaveLength(4)

      // Acknowledge first 3 — banner should NOT appear
      for (let i = 0; i < 3; i++) {
        const buttons = screen.getAllByRole('button', { name: /mark reviewed/i })
        fireEvent.click(buttons[0])
        // Banner should not appear yet
        await waitFor(() => {
          const banner = screen.queryByText(/all items reviewed/i)
          expect(banner).toBeNull()
        })
      }

      // Acknowledge the 4th (last) — banner SHOULD appear
      const lastButton = screen.getByRole('button', { name: /mark reviewed/i })
      fireEvent.click(lastButton)

      // Then: The banner appears with "4/4 reviewed"
      await waitFor(() => {
        const banner = screen.getByText(/all items reviewed/i)
        expect(banner).toBeInTheDocument()
      })

      const count = screen.getByText(/4\/4 reviewed/i)
      expect(count).toBeInTheDocument()
    })
  })

  // =========================================================================
  // Integration Tests
  // =========================================================================
  describe('Integration: Mixed Acknowledged/Unacknowledged State', () => {
    it('INT-001: InsightEvidenceCardList loads and displays mix of acknowledged and unacknowledged items', () => {
      // Given: useDailyActions returns 4 action items — 2 acknowledged, 2 unacknowledged
      const apiItems = [
        createMockAPIActionItem('action-1', true),
        createMockAPIActionItem('action-2', true),
        createMockAPIActionItem('action-3', false),
        createMockAPIActionItem('action-4', false),
      ]

      mockUseDailyActions.mockReturnValue({
        data: {
          actions: apiItems,
          generated_at: '2026-02-11T06:00:00Z',
          report_date: '2026-02-11',
          total_count: 4,
          counts_by_category: { safety: 0, oee: 0, financial: 4 },
        },
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      })

      // When: InsightEvidenceCardList mounts and renders
      render(<InsightEvidenceCardList />)

      // Then: 2 cards display in acknowledged state (with "Reviewed" buttons)
      const reviewedButtons = screen.getAllByRole('button', { name: /^reviewed$/i })
      expect(reviewedButtons).toHaveLength(2)

      // And: 2 cards display in unacknowledged state (with "Mark Reviewed" buttons)
      const markReviewedButtons = screen.getAllByRole('button', { name: /mark reviewed/i })
      expect(markReviewedButtons).toHaveLength(2)

      // And: The "All items reviewed" banner is NOT shown
      const banner = screen.queryByText(/all items reviewed/i)
      expect(banner).toBeNull()
    })

    it('INT-002: Full flow - acknowledge all items and see banner', async () => {
      // Given: InsightEvidenceCardList renders with 2 unacknowledged action items
      const apiItems = [
        createMockAPIActionItem('action-1', false),
        createMockAPIActionItem('action-2', false),
      ]

      mockUseDailyActions.mockReturnValue({
        data: {
          actions: apiItems,
          generated_at: '2026-02-11T06:00:00Z',
          report_date: '2026-02-11',
          total_count: 2,
          counts_by_category: { safety: 0, oee: 0, financial: 2 },
        },
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      })

      mockFetch.mockImplementation(async (url: string) => {
        if (url.includes('/acknowledge')) {
          const actionId = url.split('/actions/')[1]?.split('/')[0]
          return {
            ok: true,
            status: 200,
            json: async () => ({
              id: `ack-${actionId}`,
              action_item_id: actionId,
              user_id: 'u1',
              acknowledged_at: new Date().toISOString(),
              note: null,
              report_date: '2026-02-11',
            }),
          }
        }
        return { ok: true, status: 200, json: async () => ({ members: [] }) }
      })

      render(<InsightEvidenceCardList />)

      // Initially, no banner
      expect(screen.queryByText(/all items reviewed/i)).toBeNull()

      // When: The user clicks acknowledge on the first card
      const buttons1 = screen.getAllByRole('button', { name: /mark reviewed/i })
      expect(buttons1).toHaveLength(2)
      fireEvent.click(buttons1[0])

      // First card transitions to acknowledged state
      await waitFor(() => {
        const reviewed = screen.getAllByRole('button', { name: /^reviewed$/i })
        expect(reviewed).toHaveLength(1)
      })

      // Still no banner (1/2)
      expect(screen.queryByText(/all items reviewed/i)).toBeNull()

      // When: The user clicks acknowledge on the second card
      const buttons2 = screen.getAllByRole('button', { name: /mark reviewed/i })
      expect(buttons2).toHaveLength(1)
      fireEvent.click(buttons2[0])

      // Then: Both cards transition to acknowledged visual state
      await waitFor(() => {
        const reviewed = screen.getAllByRole('button', { name: /^reviewed$/i })
        expect(reviewed).toHaveLength(2)
      })

      // And: The "All items reviewed" banner appears with "2/2 reviewed"
      await waitFor(() => {
        const banner = screen.getByText(/all items reviewed/i)
        expect(banner).toBeInTheDocument()
      })

      const count = screen.getByText(/2\/2 reviewed/i)
      expect(count).toBeInTheDocument()
    })
  })
})
