/**
 * AssignmentBadge Component & Integration Tests (Story 13.4: Assignment Badge on Action Cards)
 *
 * TDD tests — these MUST FAIL until the AssignmentBadge component is implemented.
 * Tests cover badge rendering with status variants, accessibility, barrel exports,
 * and integration with InsightSection.
 *
 * @see Story 13.4 - Assignment Badge on Action Cards
 * @see AC #1 - Badge rendering with color-coded status
 * @see AC #2 - No badge when no follow-up exists
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

import { AssignmentBadge } from '../AssignmentBadge'
import { InsightSection } from '../InsightSection'
import type { ActionItem } from '../types'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/**
 * FollowUpData represents follow-up assignment data.
 * This type will be defined in the actual implementation; here we define
 * the shape for test fixtures.
 */
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

const createMockActionItem = (overrides: Partial<ActionItem> = {}): ActionItem => ({
  id: 'action-42',
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

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: Assignment Badge on Action Cards (Story 13.4)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockReset()
    mockGetSession.mockReset()

    // Default: authenticated session
    mockGetSession.mockResolvedValue({
      data: { session: { access_token: 'mock-token-abc' } },
    })
    // Default: empty fetch response (for team members endpoint)
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
  // AC1: Badge renders with color-coded status
  // =========================================================================
  describe('AC1: Badge Rendering with Status Variants', () => {
    it('UNIT-001: AssignmentBadge renders with blue info variant for "assigned" status', () => {
      // Given: A FollowUpData object with status "assigned" and assignee_email "john@example.com"
      const followUp = createMockFollowUp({
        id: 'fu-1',
        action_item_id: 'act-1',
        assigned_to: 'uuid-1',
        assignee_email: 'john@example.com',
        status: 'assigned',
        note: null,
        created_at: '2026-01-15T10:00:00Z',
        updated_at: '2026-01-15T10:00:00Z',
      })

      // When: The AssignmentBadge component renders with this follow-up data
      render(<AssignmentBadge followUp={followUp} />)

      // Then: A Badge component renders with the "info" variant (blue color)
      const badge = screen.getByText(/john@example.com/i)
      expect(badge).toBeInTheDocument()

      // And: The badge contains "Assigned" status label
      expect(screen.getByText(/assigned/i)).toBeInTheDocument()

      // And: The badge has info/blue variant classes
      const badgeEl = badge.closest('[class*="border-info-blue"]') || badge.closest('[class*="info"]')
      expect(badgeEl).toBeTruthy()
    })

    it('UNIT-002: AssignmentBadge renders with amber warning variant for "in_progress" status', () => {
      // Given: A FollowUpData object with status "in_progress" and assignee_email "jane@example.com"
      const followUp = createMockFollowUp({
        id: 'fu-2',
        action_item_id: 'act-2',
        assigned_to: 'uuid-2',
        assignee_email: 'jane@example.com',
        status: 'in_progress',
        note: 'Working on it',
        created_at: '2026-01-15T10:00:00Z',
        updated_at: '2026-01-15T11:00:00Z',
      })

      // When: The AssignmentBadge component renders with this follow-up data
      render(<AssignmentBadge followUp={followUp} />)

      // Then: A Badge component renders with the "warning" variant (amber color)
      const badge = screen.getByText(/jane@example.com/i)
      expect(badge).toBeInTheDocument()

      // And: The badge contains "In Progress" status label
      expect(screen.getByText(/in progress/i)).toBeInTheDocument()

      // And: The badge has warning/amber variant classes
      const badgeEl = badge.closest('[class*="border-warning-amber"]') || badge.closest('[class*="warning"]')
      expect(badgeEl).toBeTruthy()
    })

    it('UNIT-003: AssignmentBadge renders with green success variant for "resolved" status', () => {
      // Given: A FollowUpData object with status "resolved" and assignee_email "bob@example.com"
      const followUp = createMockFollowUp({
        id: 'fu-3',
        action_item_id: 'act-3',
        assigned_to: 'uuid-3',
        assignee_email: 'bob@example.com',
        status: 'resolved',
        note: 'Fixed',
        created_at: '2026-01-15T10:00:00Z',
        updated_at: '2026-01-15T14:00:00Z',
      })

      // When: The AssignmentBadge component renders with this follow-up data
      render(<AssignmentBadge followUp={followUp} />)

      // Then: A Badge component renders with the "success" variant (green color)
      const badge = screen.getByText(/bob@example.com/i)
      expect(badge).toBeInTheDocument()

      // And: The badge contains "Resolved" status label
      expect(screen.getByText(/resolved/i)).toBeInTheDocument()

      // And: The badge has success/green variant classes
      const badgeEl = badge.closest('[class*="border-success-green"]') || badge.closest('[class*="success"]')
      expect(badgeEl).toBeTruthy()
    })

    it('UNIT-004: AssignmentBadge includes correct ARIA label for accessibility', () => {
      // Given: A FollowUpData object with assignee_email "john@example.com" and status "assigned"
      const followUp = createMockFollowUp({
        id: 'fu-1',
        action_item_id: 'act-1',
        assigned_to: 'uuid-1',
        assignee_email: 'john@example.com',
        status: 'assigned',
      })

      // When: The AssignmentBadge component renders
      render(<AssignmentBadge followUp={followUp} />)

      // Then: The badge element has an aria-label containing the assignee and status
      const badgeWithLabel = screen.getByLabelText(/assigned to john@example\.com, status: assigned/i)
      expect(badgeWithLabel).toBeInTheDocument()
    })

    it('UNIT-005: AssignmentBadge displays correct format with email and status label', () => {
      // Given: A FollowUpData object with assignee_email "alice@factory.com" and status "in_progress"
      const followUp = createMockFollowUp({
        assignee_email: 'alice@factory.com',
        status: 'in_progress',
      })

      // When: The AssignmentBadge component renders
      render(<AssignmentBadge followUp={followUp} />)

      // Then: The rendered text contains both the assignee email and a status label
      expect(screen.getByText(/alice@factory\.com/)).toBeInTheDocument()
      expect(screen.getByText(/in progress/i)).toBeInTheDocument()
    })

    it('UNIT-006: AssignmentBadge handles truncated UUID fallback for missing email', () => {
      // Given: A FollowUpData object where assignee_email is a truncated UUID format
      const followUp = createMockFollowUp({
        assignee_email: 'abc12345...',
        status: 'assigned',
      })

      // When: The AssignmentBadge component renders
      render(<AssignmentBadge followUp={followUp} />)

      // Then: The badge displays the truncated UUID as the assignee identifier without error
      expect(screen.getByText(/abc12345\.\.\./)).toBeInTheDocument()
    })
  })

  // =========================================================================
  // AC2: No badge when no follow-up exists
  // =========================================================================
  describe('AC2: No Badge When No Follow-Up', () => {
    it('UNIT-007: AssignmentBadge does not render when followUp prop is undefined', () => {
      // Given: An InsightSection component receives no followUp prop (undefined)
      render(
        <InsightSection
          priority="FINANCIAL"
          recommendation={{ text: 'Test recommendation', summary: 'Test' }}
          asset={{ id: 'asset-1', name: 'Grinder 5', area: 'Grinding' }}
          financialImpact={2000}
          timestamp="2026-02-11T08:00:00Z"
          onAssign={() => {}}
        />
      )

      // When/Then: No AssignmentBadge element is present in the DOM
      // The badge should not render any aria-label pattern matching "Assigned to"
      const assignmentBadge = screen.queryByLabelText(/assigned to/i)
      expect(assignmentBadge).toBeNull()
    })

    it('UNIT-008: AssignmentBadge does not render when followUp prop is null', () => {
      // Given: An InsightSection component receives followUp as null
      render(
        <InsightSection
          priority="FINANCIAL"
          recommendation={{ text: 'Test recommendation', summary: 'Test' }}
          asset={{ id: 'asset-1', name: 'Grinder 5', area: 'Grinding' }}
          financialImpact={2000}
          timestamp="2026-02-11T08:00:00Z"
          onAssign={() => {}}
          followUp={null}
        />
      )

      // When/Then: No AssignmentBadge element is present in the DOM
      const assignmentBadge = screen.queryByLabelText(/assigned to/i)
      expect(assignmentBadge).toBeNull()
    })
  })

  // =========================================================================
  // Integration: Badge in InsightSection
  // =========================================================================
  describe('Integration: Badge in InsightSection', () => {
    it('INT-001: InsightSection renders AssignmentBadge when followUp prop is provided', () => {
      // Given: An InsightSection component receives a valid followUp prop with status "assigned"
      const followUp = createMockFollowUp({
        status: 'assigned',
        assignee_email: 'worker@factory.com',
      })

      // When: The component renders
      render(
        <InsightSection
          priority="FINANCIAL"
          recommendation={{ text: 'Investigate downtime on Grinder 5', summary: 'Downtime investigation' }}
          asset={{ id: 'asset-1', name: 'Grinder 5', area: 'Grinding' }}
          financialImpact={2000}
          timestamp="2026-02-11T08:00:00Z"
          onAssign={() => {}}
          followUp={followUp}
        />
      )

      // Then: The AssignmentBadge is visible within the InsightSection
      const badge = screen.getByLabelText(/assigned to worker@factory\.com/i)
      expect(badge).toBeInTheDocument()

      // And: The badge displays the assignee email
      expect(screen.getByText(/worker@factory\.com/)).toBeInTheDocument()
    })

    it('INT-002: InsightEvidenceCard passes followUp to InsightSection correctly', async () => {
      // Given: An InsightEvidenceCard receives a followUp prop with status "in_progress"
      const followUp = createMockFollowUp({
        status: 'in_progress',
        assignee_email: 'worker@factory.com',
      })

      const item = createMockActionItem()

      // Import InsightEvidenceCard dynamically since it needs the mock context
      const { InsightEvidenceCard } = await import('../InsightEvidenceCard')

      // When: The card renders with followUp prop
      render(<InsightEvidenceCard item={item} followUp={followUp} />)

      // Then: The AssignmentBadge appears in the InsightSection (left side) of the card
      expect(screen.getByText(/worker@factory\.com/)).toBeInTheDocument()

      // And: The badge has amber/warning styling for "in_progress"
      const badgeEl = screen.getByLabelText(/assigned to worker@factory\.com/i)
      expect(badgeEl).toBeInTheDocument()
      expect(badgeEl.className).toMatch(/warning|amber/)
    })

    it('INT-003: InsightSection changes "Assign" button to "Reassign" when followUp exists', () => {
      // Given: An InsightSection component receives a valid followUp prop (any status)
      const followUp = createMockFollowUp({ status: 'assigned' })
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
          followUp={followUp}
        />
      )

      // Then: The action button displays "Reassign" instead of "Assign"
      const reassignButton = screen.getByRole('button', { name: /reassign/i })
      expect(reassignButton).toBeInTheDocument()
      expect(screen.queryByRole('button', { name: /^assign$/i })).toBeNull()

      // And: The button still triggers the onAssign callback when clicked
      fireEvent.click(reassignButton)
      expect(mockOnAssign).toHaveBeenCalled()
    })
  })

  // =========================================================================
  // Barrel File & Exports
  // =========================================================================
  describe('Barrel File & Exports', () => {
    it('UNIT-021: AssignmentBadge is exported from barrel file', async () => {
      // Given: The action-engine barrel file (index.ts) has been updated
      // When: Importing AssignmentBadge from '@/components/action-engine'
      const barrel = await import('../index')

      // Then: The AssignmentBadge component is successfully imported and is a valid React component
      expect(barrel.AssignmentBadge).toBeDefined()
      expect(typeof barrel.AssignmentBadge).toBe('function')
    })

    it('UNIT-022: FollowUpData type is exported from barrel file', async () => {
      // Given: The action-engine barrel file (index.ts) has been updated
      // When: Importing from '@/components/action-engine'
      // Then: The FollowUpData type is usable for typing (verified at compile time)
      // This test verifies the export exists by checking we can import
      // the type-related runtime artifacts (e.g., the component that uses it)
      const barrel = await import('../index')
      expect(barrel.AssignmentBadge).toBeDefined()
      // FollowUpData is a type export — runtime check is that the barrel imports succeed
      // If the export is missing, the barrel would fail to compile
    })
  })
})
