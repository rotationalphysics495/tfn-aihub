/**
 * InsightEvidenceCardList Follow-Up Integration Tests (Story 13.4: Assignment Badge on Action Cards)
 *
 * TDD tests — these MUST FAIL until the useFollowUps hook is wired into InsightEvidenceCardList.
 * Tests cover the data flow from useDailyActions + useFollowUps into ActionCardList.
 *
 * @see Story 13.4 - Assignment Badge on Action Cards
 * @see AC #1 - Badge shows on card with assignee info
 * @see AC #2 - No badge when no follow-up
 */

import { render, screen } from '@testing-library/react'
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

// Mock useDailyActions
const mockUseDailyActions = vi.fn()
vi.mock('@/hooks/useDailyActions', () => ({
  useDailyActions: () => mockUseDailyActions(),
}))

// Mock useFollowUps — this is the new hook being integrated
const mockUseFollowUps = vi.fn()
vi.mock('@/hooks/useFollowUps', () => ({
  useFollowUps: (opts: unknown) => mockUseFollowUps(opts),
}))

// ---------------------------------------------------------------------------
// Imports (AFTER mocks)
// ---------------------------------------------------------------------------

import { InsightEvidenceCardList } from '../InsightEvidenceCardList'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface FollowUpData {
  id: string
  action_item_id: string
  assigned_to: string
  assignee_email: string
  status: 'assigned' | 'in_progress' | 'resolved'
  note: string | null
  created_at: string
  updated_at: string
}

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const createMockFollowUp = (overrides: Partial<FollowUpData> = {}): FollowUpData => ({
  id: 'fu-default',
  action_item_id: 'act-default',
  assigned_to: 'uuid-default',
  assignee_email: 'default@example.com',
  status: 'assigned',
  note: null,
  created_at: '2026-01-15T10:00:00Z',
  updated_at: '2026-01-15T10:00:00Z',
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

describe('Feature: InsightEvidenceCardList Follow-Up Integration (Story 13.4)', () => {
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

    // Default: useFollowUps returns empty map
    mockUseFollowUps.mockReturnValue({
      followUps: new Map(),
      isLoading: false,
      error: null,
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('INT-008: InsightEvidenceCardList wires useFollowUps with reportDate from useDailyActions', () => {
    // Given: useDailyActions returns data with report_date "2026-01-15"
    const apiItems = [
      createMockAPIActionItem('act-1', false),
      createMockAPIActionItem('act-2', false),
    ]

    mockUseDailyActions.mockReturnValue({
      data: {
        actions: apiItems,
        generated_at: '2026-01-15T06:00:00Z',
        report_date: '2026-01-15',
        total_count: 2,
        counts_by_category: { safety: 0, oee: 0, financial: 2 },
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    })

    // And: useFollowUps returns a Map with follow-up data for "act-1"
    const followUpsMap = new Map<string, FollowUpData>()
    followUpsMap.set(
      'act-1',
      createMockFollowUp({
        action_item_id: 'act-1',
        assignee_email: 'alice@factory.com',
        status: 'assigned',
      })
    )

    mockUseFollowUps.mockReturnValue({
      followUps: followUpsMap,
      isLoading: false,
      error: null,
    })

    // When: InsightEvidenceCardList renders
    render(<InsightEvidenceCardList />)

    // Then: useFollowUps is called with reportDate "2026-01-15"
    expect(mockUseFollowUps).toHaveBeenCalledWith(
      expect.objectContaining({ reportDate: '2026-01-15' })
    )

    // And: The card for "act-1" shows the assignment badge with "alice@factory.com"
    expect(screen.getByText(/alice@factory\.com/)).toBeInTheDocument()

    // And: The card for "act-2" does NOT show an assignment badge
    // (only 1 badge total in the DOM)
    const badges = screen.queryAllByLabelText(/assigned to/i)
    expect(badges).toHaveLength(1)
  })
})
