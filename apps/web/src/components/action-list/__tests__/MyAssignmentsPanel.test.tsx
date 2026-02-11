/**
 * MyAssignmentsPanel Component Tests (Story 13.5: "My Assignments" Panel)
 *
 * TDD tests — these MUST FAIL until the MyAssignmentsPanel component is implemented.
 * Tests cover status groups with color-coded badges, count badge, loading/error/empty
 * states, expand/collapse behavior, and hiding empty status groups.
 *
 * @see Story 13.5 - "My Assignments" Panel
 * @see AC #1 - Panel shows follow-ups grouped by status
 * @see AC #4 - Empty state when no open follow-ups
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'

// ---------------------------------------------------------------------------
// Mocks (BEFORE imports)
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
  }),
}))

const mockFetch = vi.fn()
global.fetch = mockFetch

// Mock the useMyFollowUps hook
const mockUseMyFollowUps = vi.fn()
vi.mock('@/hooks/useMyFollowUps', () => ({
  useMyFollowUps: () => mockUseMyFollowUps(),
}))

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

interface MockFollowUpItem {
  id: string
  action_item_id: string
  action_summary: string
  asset_name: string | null
  category: string | null
  assigned_to: string
  assigned_to_email: string
  assigned_by: string
  note: string | null
  status: 'assigned' | 'in_progress' | 'resolved'
  report_date: string
  created_at: string
  updated_at: string
}

const createMockFollowUp = (
  id: string,
  status: 'assigned' | 'in_progress' | 'resolved' = 'assigned',
  overrides: Partial<MockFollowUpItem> = {}
): MockFollowUpItem => ({
  id,
  action_item_id: `action-safety-${id}`,
  action_summary: 'Investigate pressure anomaly on main valve',
  asset_name: 'Grinder 5',
  category: 'safety',
  assigned_to: 'uuid-assignee-1',
  assigned_to_email: 'john@company.com',
  assigned_by: 'uuid-manager-1',
  note: 'Please check by EOD',
  status,
  report_date: '2026-02-11',
  created_at: '2026-02-11T08:30:00Z',
  updated_at: '2026-02-11T08:30:00Z',
  ...overrides,
})

const createMockHookReturn = (overrides: Record<string, unknown> = {}) => ({
  followups: [],
  isLoading: false,
  error: null,
  refetch: vi.fn(),
  grouped: {
    assigned: [] as MockFollowUpItem[],
    in_progress: [] as MockFollowUpItem[],
    resolved: [] as MockFollowUpItem[],
  },
  totalCount: 0,
  hasFollowUps: false,
  ...overrides,
})

// ---------------------------------------------------------------------------
// Import component AFTER mocks are set up
// ---------------------------------------------------------------------------

// The component does not exist yet — this import will fail until it's created.
import { MyAssignmentsPanel } from '../MyAssignmentsPanel'

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: MyAssignmentsPanel Component (Story 13.5)', () => {
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
  // AC1: Status groups with color-coded badges
  // =========================================================================
  describe('AC1: Status Groups with Color-Coded Badges', () => {
    it('UNIT-005: MyAssignmentsPanel renders status groups with correct color-coded badges', () => {
      // Given: The useMyFollowUps hook returns grouped follow-ups
      //        (2 assigned, 1 in_progress, 1 resolved)
      const assigned = [
        createMockFollowUp('fu-1', 'assigned'),
        createMockFollowUp('fu-2', 'assigned'),
      ]
      const inProgress = [createMockFollowUp('fu-3', 'in_progress')]
      const resolved = [createMockFollowUp('fu-4', 'resolved')]

      mockUseMyFollowUps.mockReturnValue(
        createMockHookReturn({
          followups: [...assigned, ...inProgress, ...resolved],
          grouped: {
            assigned,
            in_progress: inProgress,
            resolved,
          },
          totalCount: 4,
          hasFollowUps: true,
        })
      )

      // When: The MyAssignmentsPanel component renders
      render(<MyAssignmentsPanel />)

      // Then: Three status group sections are visible
      expect(screen.getByText(/assigned/i)).toBeInTheDocument()
      expect(screen.getByText(/in progress/i)).toBeInTheDocument()
      expect(screen.getByText(/resolved/i)).toBeInTheDocument()

      // And: The "Assigned" section has a blue/info badge variant
      const assignedBadge = screen.getByText(/assigned/i).closest('[class*="blue"], [class*="info"]')
      expect(assignedBadge).toBeTruthy()

      // And: The "In Progress" section has an amber/warning badge variant
      const progressBadge = screen.getByText(/in progress/i).closest('[class*="amber"], [class*="warning"]')
      expect(progressBadge).toBeTruthy()

      // And: The "Resolved" section has a green/success badge variant
      const resolvedBadge = screen.getByText(/resolved/i).closest('[class*="green"], [class*="success"]')
      expect(resolvedBadge).toBeTruthy()
    })

    it('UNIT-006: MyAssignmentsPanel renders count badge in header', () => {
      // Given: The useMyFollowUps hook returns 5 total follow-ups
      const followups = Array.from({ length: 5 }, (_, i) =>
        createMockFollowUp(`fu-${i}`, 'assigned')
      )

      mockUseMyFollowUps.mockReturnValue(
        createMockHookReturn({
          followups,
          grouped: {
            assigned: followups,
            in_progress: [],
            resolved: [],
          },
          totalCount: 5,
          hasFollowUps: true,
        })
      )

      // When: The MyAssignmentsPanel component renders
      render(<MyAssignmentsPanel />)

      // Then: The header shows "My Assignments" with a count badge displaying "5"
      expect(screen.getByText(/my assignments/i)).toBeInTheDocument()
      expect(screen.getByText('5')).toBeInTheDocument()
    })
  })

  // =========================================================================
  // Expand/Collapse behavior
  // =========================================================================
  describe('Expand/Collapse Behavior', () => {
    it('UNIT-010: MyAssignmentsPanel default expanded when follow-ups exist', () => {
      // Given: The useMyFollowUps hook returns hasFollowUps=true
      mockUseMyFollowUps.mockReturnValue(
        createMockHookReturn({
          followups: [createMockFollowUp('fu-1', 'assigned')],
          grouped: {
            assigned: [createMockFollowUp('fu-1', 'assigned')],
            in_progress: [],
            resolved: [],
          },
          totalCount: 1,
          hasFollowUps: true,
        })
      )

      // When: The MyAssignmentsPanel component renders initially
      render(<MyAssignmentsPanel />)

      // Then: The panel content (follow-up entries) is visible/expanded
      expect(screen.getByText(/grinder 5/i)).toBeInTheDocument()
    })

    it('UNIT-011: MyAssignmentsPanel default collapsed when no follow-ups', () => {
      // Given: The useMyFollowUps hook returns hasFollowUps=false
      mockUseMyFollowUps.mockReturnValue(createMockHookReturn())

      // When: The MyAssignmentsPanel component renders initially
      render(<MyAssignmentsPanel />)

      // Then: The panel content is collapsed (only header visible with empty state)
      expect(screen.getByText(/no open follow-ups/i)).toBeInTheDocument()
    })

    it('UNIT-012: MyAssignmentsPanel expand/collapse toggle works', () => {
      // Given: The MyAssignmentsPanel is rendered with follow-ups (expanded by default)
      mockUseMyFollowUps.mockReturnValue(
        createMockHookReturn({
          followups: [createMockFollowUp('fu-1', 'assigned')],
          grouped: {
            assigned: [createMockFollowUp('fu-1', 'assigned')],
            in_progress: [],
            resolved: [],
          },
          totalCount: 1,
          hasFollowUps: true,
        })
      )

      render(<MyAssignmentsPanel />)

      // Verify panel is expanded initially
      expect(screen.getByText(/grinder 5/i)).toBeInTheDocument()

      // When: The user clicks the expand/collapse chevron button
      const toggleButton = screen.getByRole('button', { name: /collapse|toggle|expand/i })
      fireEvent.click(toggleButton)

      // Then: The panel content collapses and is no longer visible
      expect(screen.queryByText(/grinder 5/i)).not.toBeInTheDocument()

      // When: Clicking again
      fireEvent.click(toggleButton)

      // Then: Re-expands
      expect(screen.getByText(/grinder 5/i)).toBeInTheDocument()
    })
  })

  // =========================================================================
  // Loading, error, empty states
  // =========================================================================
  describe('Loading, Error, Empty States', () => {
    it('UNIT-013: MyAssignmentsPanel renders loading skeleton state', () => {
      // Given: The useMyFollowUps hook returns isLoading=true
      mockUseMyFollowUps.mockReturnValue(
        createMockHookReturn({ isLoading: true })
      )

      // When: The MyAssignmentsPanel component renders
      render(<MyAssignmentsPanel />)

      // Then: A loading skeleton/placeholder UI is displayed
      const skeleton = document.querySelector('[class*="skeleton"], [class*="animate-pulse"]')
      expect(skeleton).toBeTruthy()
    })

    it('UNIT-014: MyAssignmentsPanel renders error state with retry button', () => {
      // Given: The useMyFollowUps hook returns an error
      const mockRefetch = vi.fn()
      mockUseMyFollowUps.mockReturnValue(
        createMockHookReturn({
          error: 'Network failure',
          refetch: mockRefetch,
        })
      )

      // When: The MyAssignmentsPanel component renders
      render(<MyAssignmentsPanel />)

      // Then: An error message is displayed
      expect(screen.getByText(/error|failed|network/i)).toBeInTheDocument()

      // And: A "Retry" button is present
      const retryButton = screen.getByRole('button', { name: /retry/i })
      expect(retryButton).toBeInTheDocument()

      // When: Clicking the retry button
      fireEvent.click(retryButton)

      // Then: The refetch function is called
      expect(mockRefetch).toHaveBeenCalled()
    })

    it('UNIT-015: MyAssignmentsPanel hides empty status groups', () => {
      // Given: The useMyFollowUps hook returns follow-ups only in "assigned" status
      const assigned = [
        createMockFollowUp('fu-1', 'assigned'),
        createMockFollowUp('fu-2', 'assigned'),
      ]

      mockUseMyFollowUps.mockReturnValue(
        createMockHookReturn({
          followups: assigned,
          grouped: {
            assigned,
            in_progress: [],
            resolved: [],
          },
          totalCount: 2,
          hasFollowUps: true,
        })
      )

      // When: The MyAssignmentsPanel component renders
      render(<MyAssignmentsPanel />)

      // Then: Only the "Assigned" status group is rendered
      expect(screen.getByText(/assigned/i)).toBeInTheDocument()

      // And: Empty groups for "In Progress" and "Resolved" are not shown
      // (We check that the status group headers for empty groups are absent)
      const allText = document.body.textContent || ''
      // We need to check more carefully — "In Progress" and "Resolved" group
      // headers should not be rendered (or should be collapsed)
      const inProgressGroups = screen.queryAllByText(/in progress/i)
      const resolvedGroups = screen.queryAllByText(/^resolved$/i)

      // Empty groups should not have visible section headers
      expect(inProgressGroups.length).toBe(0)
      expect(resolvedGroups.length).toBe(0)
    })
  })

  // =========================================================================
  // AC4: Empty state
  // =========================================================================
  describe('AC4: Empty State', () => {
    it('UNIT-032: Empty state renders exact message text', () => {
      // Given: The useMyFollowUps hook returns hasFollowUps=false
      mockUseMyFollowUps.mockReturnValue(createMockHookReturn())

      // When: The MyAssignmentsPanel component renders
      render(<MyAssignmentsPanel />)

      // Then: The exact message text is displayed
      expect(
        screen.getByText('No open follow-ups. Assign actions from the report below.')
      ).toBeInTheDocument()
    })

    it('UNIT-033: Empty state renders when API returns zero follow-ups', () => {
      // Given: The API returns a valid empty response
      mockUseMyFollowUps.mockReturnValue(
        createMockHookReturn({
          followups: [],
          grouped: {
            assigned: [],
            in_progress: [],
            resolved: [],
          },
          totalCount: 0,
          hasFollowUps: false,
        })
      )

      // When: The MyAssignmentsPanel component renders
      render(<MyAssignmentsPanel />)

      // Then: The empty state is shown; no status group headers are rendered
      expect(
        screen.getByText('No open follow-ups. Assign actions from the report below.')
      ).toBeInTheDocument()

      // And: hasFollowUps is false (verified via the empty state UI)
      expect(screen.queryByText(/assigned/i)).toBeNull()
    })
  })
})
