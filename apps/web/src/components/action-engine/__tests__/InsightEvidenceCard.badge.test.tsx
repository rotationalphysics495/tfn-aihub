/**
 * InsightEvidenceCard Badge Integration Tests (Story 13.4: Assignment Badge on Action Cards)
 *
 * TDD tests — these MUST FAIL until the follow-up badge integration is implemented.
 * Tests cover: "Assign"/"Reassign" button behavior, card rendering with/without follow-ups,
 * and ActionCardList follow-up prop passing.
 *
 * @see Story 13.4 - Assignment Badge on Action Cards
 * @see AC #2 - No badge when no follow-up (existing behavior preserved)
 * @see AC #3 - Most recent active follow-up displayed
 */

import { render, screen, fireEvent } from '@testing-library/react'
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

// ---------------------------------------------------------------------------
// Imports (AFTER mocks)
// ---------------------------------------------------------------------------

import { InsightEvidenceCard } from '../InsightEvidenceCard'
import { InsightSection } from '../InsightSection'
import { ActionCardList } from '../ActionCardList'
import type { ActionItem } from '../types'

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

const createMockActionItem = (
  id: string = 'action-42',
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

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: InsightEvidenceCard Badge Integration (Story 13.4)', () => {
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
  // AC2: Existing behavior preserved when no follow-up
  // =========================================================================
  describe('AC2: Existing Behavior Without Follow-Up', () => {
    it('INT-004: "Assign" button remains visible and labeled "Assign" when no follow-up exists', () => {
      // Given: An InsightSection component with an onAssign callback but no followUp prop
      const mockOnAssign = vi.fn()

      // When: The component renders
      render(
        <InsightSection
          priority="FINANCIAL"
          recommendation={{ text: 'Test recommendation', summary: 'Test' }}
          asset={{ id: 'asset-1', name: 'Grinder 5', area: 'Grinding' }}
          financialImpact={2000}
          timestamp="2026-02-11T08:00:00Z"
          onAssign={mockOnAssign}
        />
      )

      // Then: The "Assign" button is visible with the text "Assign"
      const assignButton = screen.getByRole('button', { name: /assign/i })
      expect(assignButton).toBeInTheDocument()
      expect(assignButton).toHaveTextContent('Assign')

      // And: It is NOT labeled "Reassign"
      expect(assignButton.textContent).not.toMatch(/reassign/i)

      // And: Clicking it invokes the onAssign callback
      fireEvent.click(assignButton)
      expect(mockOnAssign).toHaveBeenCalled()
    })

    it('INT-005: Card renders identically to pre-story behavior when no follow-up exists', () => {
      // Given: An InsightEvidenceCard component with a standard ActionItem and no followUp prop
      const item = createMockActionItem('action-standard')

      // When: The card renders
      render(<InsightEvidenceCard item={item} />)

      // Then: The card layout renders correctly
      // Priority badge is visible
      expect(screen.getByLabelText(/Priority: FINANCIAL/i)).toBeInTheDocument()

      // Recommendation text is visible
      expect(screen.getByText(/Recommendation for action-standard/)).toBeInTheDocument()

      // Financial impact is displayed
      expect(screen.getByText(/\$2K loss/)).toBeInTheDocument()

      // Asset name is visible
      expect(screen.getByText(/Asset action-standard/)).toBeInTheDocument()

      // "Assign" button is present (not "Reassign")
      const assignButton = screen.getByRole('button', { name: /assign/i })
      expect(assignButton).toBeInTheDocument()
      expect(assignButton.textContent).not.toMatch(/reassign/i)

      // No assignment badge is present
      const badge = screen.queryByLabelText(/assigned to/i)
      expect(badge).toBeNull()
    })

    it('INT-006: ActionCardList passes undefined followUp to cards not in the followUps Map', () => {
      // Given: Two action items, only one has a follow-up
      const items = [
        createMockActionItem('act-1'),
        createMockActionItem('act-2'),
      ]

      const followUpsMap = new Map<string, FollowUpData>()
      followUpsMap.set(
        'act-1',
        createMockFollowUp({
          action_item_id: 'act-1',
          assignee_email: 'assigned@factory.com',
          status: 'assigned',
        })
      )

      // When: The list renders with the followUps Map
      render(
        <ActionCardList
          items={items}
          followUps={followUpsMap}
        />
      )

      // Then: The card for "act-1" shows the assignment badge
      expect(screen.getByText(/assigned@factory\.com/)).toBeInTheDocument()

      // And: The card for "act-2" does NOT show an assignment badge
      // Count total assignment badges - should be exactly 1
      const badges = screen.getAllByLabelText(/assigned to/i)
      expect(badges).toHaveLength(1)
    })
  })

  // =========================================================================
  // AC3: Most recent active follow-up badge display
  // =========================================================================
  describe('AC3: Follow-Up Badge Display', () => {
    it('INT-007: Card displays most recent active follow-up badge when reassigned', () => {
      // Given: An InsightEvidenceCard receives a followUp reflecting the most recent active follow-up
      const followUp = createMockFollowUp({
        status: 'in_progress',
        assignee_email: 'latest-worker@factory.com',
      })

      const item = createMockActionItem('action-reassigned')

      // When: The card renders with the follow-up
      render(<InsightEvidenceCard item={item} followUp={followUp} />)

      // Then: The badge shows the most recent assignee's email
      expect(screen.getByText(/latest-worker@factory\.com/)).toBeInTheDocument()

      // And: "In Progress" status with amber styling
      expect(screen.getByText(/in progress/i)).toBeInTheDocument()

      // And: The badge has the correct aria label
      const badge = screen.getByLabelText(/assigned to latest-worker@factory\.com/i)
      expect(badge).toBeInTheDocument()
    })
  })
})
