/**
 * useMyFollowUps Hook Tests (Story 13.5: "My Assignments" Panel)
 *
 * TDD tests — these MUST FAIL until the useMyFollowUps hook is implemented.
 * Tests cover data fetching with Bearer token auth, grouping by status,
 * empty states, refetch behavior, and error handling.
 *
 * @see Story 13.5 - "My Assignments" Panel
 * @see AC #1 - Panel shows follow-ups grouped by status
 * @see AC #2 - Status group movement on refresh
 * @see AC #4 - Empty state when no open follow-ups
 */

import { renderHook, act, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'

// ---------------------------------------------------------------------------
// Mocks (BEFORE imports)
// ---------------------------------------------------------------------------

const mockGetSession = vi.fn()
vi.mock('@/lib/supabase/client', () => ({
  createClient: () => ({
    auth: { getSession: mockGetSession },
  }),
}))

const mockFetch = vi.fn()
global.fetch = mockFetch

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const MOCK_API_URL = 'http://localhost:8000'

const createMockSession = (accessToken: string | null = 'mock-token-123') => ({
  data: { session: accessToken !== null ? { access_token: accessToken } : null },
})

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

const createMockApiResponse = (
  followups: MockFollowUpItem[],
  countsByStatus?: Record<string, number>
) => {
  const counts = countsByStatus || {
    assigned: followups.filter(f => f.status === 'assigned').length,
    in_progress: followups.filter(f => f.status === 'in_progress').length,
    resolved: followups.filter(f => f.status === 'resolved').length,
  }
  return {
    ok: true,
    status: 200,
    json: async () => ({
      followups,
      total_count: followups.length,
      counts_by_status: counts,
    }),
  }
}

const createMockErrorResponse = (status: number) => ({
  ok: false,
  status,
  json: async () => ({ error: `Error ${status}` }),
})

// ---------------------------------------------------------------------------
// Import hook AFTER mocks are set up
// ---------------------------------------------------------------------------

// The hook does not exist yet — this import will fail until it's created,
// which is the expected TDD behavior.
import { useMyFollowUps } from '../useMyFollowUps'

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: useMyFollowUps Hook (Story 13.5)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockReset()
    mockGetSession.mockReset()

    // Default: authenticated session
    mockGetSession.mockResolvedValue(createMockSession('mock-token-123'))
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // =========================================================================
  // AC1: Fetch and group follow-ups on mount
  // =========================================================================
  describe('AC1: Fetch and Group Follow-Ups', () => {
    it('UNIT-003: useMyFollowUps hook fetches and groups follow-ups on mount', async () => {
      // Given: The Supabase session is authenticated and the API returns
      //        3 follow-ups (1 assigned, 1 in_progress, 1 resolved)
      const followups = [
        createMockFollowUp('fu-1', 'assigned'),
        createMockFollowUp('fu-2', 'in_progress'),
        createMockFollowUp('fu-3', 'resolved'),
      ]
      mockFetch.mockResolvedValue(createMockApiResponse(followups))

      // When: The useMyFollowUps hook is rendered
      const { result } = renderHook(() =>
        useMyFollowUps({ apiUrl: MOCK_API_URL })
      )

      // Then: isLoading is initially true
      expect(result.current.isLoading).toBe(true)

      // Wait for fetch to complete
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: grouped.assigned contains 1 item
      expect(result.current.grouped.assigned).toHaveLength(1)
      expect(result.current.grouped.assigned[0].id).toBe('fu-1')

      // And: grouped.in_progress contains 1 item
      expect(result.current.grouped.in_progress).toHaveLength(1)
      expect(result.current.grouped.in_progress[0].id).toBe('fu-2')

      // And: grouped.resolved contains 1 item
      expect(result.current.grouped.resolved).toHaveLength(1)
      expect(result.current.grouped.resolved[0].id).toBe('fu-3')

      // And: totalCount is 3, hasFollowUps is true
      expect(result.current.totalCount).toBe(3)
      expect(result.current.hasFollowUps).toBe(true)
    })

    it('UNIT-004: useMyFollowUps hook returns hasFollowUps=false when no follow-ups', async () => {
      // Given: The API returns an empty followups array
      mockFetch.mockResolvedValue(createMockApiResponse([]))

      // When: The hook is rendered
      const { result } = renderHook(() =>
        useMyFollowUps({ apiUrl: MOCK_API_URL })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: hasFollowUps is false, totalCount is 0
      expect(result.current.hasFollowUps).toBe(false)
      expect(result.current.totalCount).toBe(0)

      // And: grouped arrays are all empty
      expect(result.current.grouped.assigned).toHaveLength(0)
      expect(result.current.grouped.in_progress).toHaveLength(0)
      expect(result.current.grouped.resolved).toHaveLength(0)
    })
  })

  // =========================================================================
  // AC2: Status group movement on refetch
  // =========================================================================
  describe('AC2: Status Group Movement on Refetch', () => {
    it('UNIT-016: Follow-up moves to new status group after refetch', async () => {
      // Given: A follow-up initially has status "assigned"
      const initialFollowups = [
        createMockFollowUp('fu-move', 'assigned'),
      ]
      mockFetch.mockResolvedValueOnce(createMockApiResponse(initialFollowups))

      const { result } = renderHook(() =>
        useMyFollowUps({ apiUrl: MOCK_API_URL })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Verify initial grouping
      expect(result.current.grouped.assigned).toHaveLength(1)
      expect(result.current.grouped.in_progress).toHaveLength(0)

      // When: The follow-up's status is updated to "in_progress" on the server
      //        and refetch() is called
      const updatedFollowups = [
        createMockFollowUp('fu-move', 'in_progress'),
      ]
      mockFetch.mockResolvedValueOnce(createMockApiResponse(updatedFollowups))

      await act(async () => {
        await result.current.refetch()
      })

      // Then: The follow-up moves from grouped.assigned to grouped.in_progress
      expect(result.current.grouped.assigned).toHaveLength(0)
      expect(result.current.grouped.in_progress).toHaveLength(1)
      expect(result.current.grouped.in_progress[0].id).toBe('fu-move')
    })

    it('UNIT-021: useMyFollowUps refetch() triggers new API call', async () => {
      // Given: The hook has completed initial fetch
      const followups = [createMockFollowUp('fu-1', 'assigned')]
      mockFetch.mockResolvedValue(createMockApiResponse(followups))

      const { result } = renderHook(() =>
        useMyFollowUps({ apiUrl: MOCK_API_URL })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Initial fetch = 1 call
      const initialCallCount = mockFetch.mock.calls.length

      // When: refetch() is called
      const updatedFollowups = [
        createMockFollowUp('fu-1', 'in_progress'),
        createMockFollowUp('fu-2', 'assigned'),
      ]
      mockFetch.mockResolvedValueOnce(createMockApiResponse(updatedFollowups))

      await act(async () => {
        await result.current.refetch()
      })

      // Then: A new API call is made
      expect(mockFetch.mock.calls.length).toBeGreaterThan(initialCallCount)

      // And: Updated data is returned
      await waitFor(() => {
        expect(result.current.totalCount).toBe(2)
      })
    })
  })

  // =========================================================================
  // Story 15.4 - AC2: has_unread passthrough
  // =========================================================================
  describe('Story 15.4 - AC2: has_unread Passthrough', () => {
    it('15-4-message-thread-ui-INT-006: useMyFollowUps hook passes has_unread from API to FollowUpEntry', async () => {
      // Given: The useMyFollowUps hook fetches follow-ups from the API,
      //        and the API response includes has_unread fields
      const followupsWithUnread = [
        createMockFollowUp('fu-1', 'assigned', { has_unread: true } as Partial<MockFollowUpItem>),
        createMockFollowUp('fu-2', 'in_progress', { has_unread: false } as Partial<MockFollowUpItem>),
      ]
      mockFetch.mockResolvedValue(createMockApiResponse(followupsWithUnread))

      // When: The hook returns data to the consuming component
      const { result } = renderHook(() =>
        useMyFollowUps({ apiUrl: MOCK_API_URL })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: Each FollowUpItem in the returned array includes the has_unread boolean field
      expect(result.current.followups).toHaveLength(2)
      expect(result.current.followups[0]).toHaveProperty('has_unread', true)
      expect(result.current.followups[1]).toHaveProperty('has_unread', false)

      // And: Grouped items also carry has_unread
      expect(result.current.grouped.assigned[0]).toHaveProperty('has_unread', true)
      expect(result.current.grouped.in_progress[0]).toHaveProperty('has_unread', false)
    })
  })

  // =========================================================================
  // Error handling
  // =========================================================================
  describe('Error Handling', () => {
    it('Hook handles auth error when no session exists', async () => {
      // Given: No Supabase session
      mockGetSession.mockResolvedValue(createMockSession(null))

      // When: Hook is rendered
      const { result } = renderHook(() =>
        useMyFollowUps({ apiUrl: MOCK_API_URL })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: error state is set
      expect(result.current.error).toBeTruthy()
      expect(result.current.hasFollowUps).toBe(false)
    })

    it('Hook handles API server error gracefully', async () => {
      // Given: The API returns a 500 error
      mockFetch.mockResolvedValue(createMockErrorResponse(500))

      // When: Hook is rendered
      const { result } = renderHook(() =>
        useMyFollowUps({ apiUrl: MOCK_API_URL })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: error state is set with user-friendly message
      expect(result.current.error).toBeTruthy()
      expect(result.current.hasFollowUps).toBe(false)
    })

    it('Hook makes correct API call with Bearer token', async () => {
      // Given: Authenticated session
      mockFetch.mockResolvedValue(createMockApiResponse([]))

      // When: Hook is rendered
      const { result } = renderHook(() =>
        useMyFollowUps({ apiUrl: MOCK_API_URL })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: fetch was called with correct URL and auth header
      expect(mockFetch).toHaveBeenCalled()
      const [url, options] = mockFetch.mock.calls[0]
      expect(url).toContain(`${MOCK_API_URL}/api/v1/actions/followups`)
      expect(url).toContain('assigned_by=me')
      expect(options.headers).toHaveProperty('Authorization', 'Bearer mock-token-123')
    })
  })
})
