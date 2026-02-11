/**
 * useFollowUps Hook Tests (Story 13.4: Assignment Badge on Action Cards)
 *
 * TDD tests — these MUST FAIL until the useFollowUps hook is implemented.
 * Tests cover data fetching, follow-up grouping/selection logic, email resolution,
 * loading/error states, and Supabase query verification.
 *
 * @see Story 13.4 - Assignment Badge on Action Cards
 * @see AC #2 - No badge when no follow-up
 * @see AC #3 - Most recent active follow-up selection
 */

import { renderHook, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

// Track Supabase query chain for verification
const mockSupabaseSelect = vi.fn()
const mockSupabaseEq = vi.fn()
const mockSupabaseOrder = vi.fn()
const mockSupabaseFrom = vi.fn()

const mockGetSession = vi.fn()

vi.mock('@/lib/supabase/client', () => ({
  createClient: () => ({
    auth: { getSession: mockGetSession },
    from: (table: string) => {
      mockSupabaseFrom(table)
      return {
        select: (...args: unknown[]) => {
          mockSupabaseSelect(...args)
          return {
            eq: (col: string, val: string) => {
              mockSupabaseEq(col, val)
              return {
                order: (col2: string, opts: Record<string, unknown>) => {
                  mockSupabaseOrder(col2, opts)
                  return mockSupabaseQueryResult
                },
              }
            },
          }
        },
      }
    },
  }),
}))

// Default mock result that can be overridden per test
let mockSupabaseQueryResult: { data: unknown[] | null; error: { message: string } | null } = {
  data: [],
  error: null,
}

// Mock global.fetch for team members API
const mockFetch = vi.fn()
global.fetch = mockFetch

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

interface MockFollowUpRow {
  id: string
  action_item_id: string
  assigned_to: string
  status: 'assigned' | 'in_progress' | 'resolved'
  note: string | null
  created_at: string
  updated_at: string
}

const createMockFollowUpRow = (overrides: Partial<MockFollowUpRow> = {}): MockFollowUpRow => ({
  id: 'fu-default',
  action_item_id: 'act-default',
  assigned_to: 'uuid-default',
  status: 'assigned',
  note: null,
  created_at: '2026-01-15T10:00:00Z',
  updated_at: '2026-01-15T10:00:00Z',
  ...overrides,
})

const createMockTeamMembersResponse = (
  members: Array<{ user_id: string; email: string; role?: string }>
) => ({
  ok: true,
  status: 200,
  json: async () => ({ members }),
})

const createMockTeamMembersErrorResponse = (status: number = 500) => ({
  ok: false,
  status,
  json: async () => ({ error: `Error ${status}` }),
})

// ---------------------------------------------------------------------------
// Import hook AFTER mocks
// ---------------------------------------------------------------------------

import { useFollowUps } from '../useFollowUps'

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: useFollowUps Hook (Story 13.4)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockReset()
    mockGetSession.mockReset()
    mockSupabaseFrom.mockClear()
    mockSupabaseSelect.mockClear()
    mockSupabaseEq.mockClear()
    mockSupabaseOrder.mockClear()

    // Default: authenticated session
    mockGetSession.mockResolvedValue({
      data: { session: { access_token: 'mock-token-abc' } },
    })

    // Default: empty follow-ups, empty team members
    mockSupabaseQueryResult = { data: [], error: null }
    mockFetch.mockResolvedValue(createMockTeamMembersResponse([]))
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // =========================================================================
  // AC2: Empty state for no follow-ups
  // =========================================================================
  describe('AC2: Empty State', () => {
    it('UNIT-009: useFollowUps returns empty Map for action items without follow-ups', async () => {
      // Given: The action_followups table returns an empty result set
      mockSupabaseQueryResult = { data: [], error: null }

      // When: The useFollowUps hook resolves
      const { result } = renderHook(() => useFollowUps({ reportDate: '2026-01-15' }))

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: The returned followUps Map is empty (size === 0)
      expect(result.current.followUps.size).toBe(0)

      // And: isLoading is false and error is null
      expect(result.current.isLoading).toBe(false)
      expect(result.current.error).toBeNull()
    })
  })

  // =========================================================================
  // AC3: Most recent active follow-up selection
  // =========================================================================
  describe('AC3: Follow-Up Selection Logic', () => {
    it('UNIT-010: useFollowUps selects most recent non-resolved follow-up when multiple exist', async () => {
      // Given: 3 follow-ups for the same action_item_id with different statuses
      mockSupabaseQueryResult = {
        data: [
          // Already sorted by created_at DESC from Supabase
          createMockFollowUpRow({
            id: 'fu-3',
            action_item_id: 'act-1',
            assigned_to: 'uuid-3',
            status: 'in_progress',
            created_at: '2026-01-15T14:00:00Z',
          }),
          createMockFollowUpRow({
            id: 'fu-2',
            action_item_id: 'act-1',
            assigned_to: 'uuid-2',
            status: 'assigned',
            created_at: '2026-01-15T12:00:00Z',
          }),
          createMockFollowUpRow({
            id: 'fu-1',
            action_item_id: 'act-1',
            assigned_to: 'uuid-1',
            status: 'resolved',
            created_at: '2026-01-15T08:00:00Z',
          }),
        ],
        error: null,
      }

      mockFetch.mockResolvedValue(
        createMockTeamMembersResponse([
          { user_id: 'uuid-3', email: 'latest@factory.com' },
          { user_id: 'uuid-2', email: 'middle@factory.com' },
          { user_id: 'uuid-1', email: 'oldest@factory.com' },
        ])
      )

      // When: The useFollowUps hook processes the data
      const { result } = renderHook(() => useFollowUps({ reportDate: '2026-01-15' }))

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: The returned Map contains the "in_progress" follow-up (most recent active)
      const followUp = result.current.followUps.get('act-1')
      expect(followUp).toBeDefined()
      expect(followUp!.status).toBe('in_progress')
      expect(followUp!.id).toBe('fu-3')
    })

    it('UNIT-011: useFollowUps selects most recent resolved follow-up when all are resolved', async () => {
      // Given: 2 follow-ups for the same action_item_id, both resolved
      mockSupabaseQueryResult = {
        data: [
          createMockFollowUpRow({
            id: 'fu-2',
            action_item_id: 'act-1',
            assigned_to: 'uuid-2',
            status: 'resolved',
            created_at: '2026-01-15T14:00:00Z',
          }),
          createMockFollowUpRow({
            id: 'fu-1',
            action_item_id: 'act-1',
            assigned_to: 'uuid-1',
            status: 'resolved',
            created_at: '2026-01-15T08:00:00Z',
          }),
        ],
        error: null,
      }

      mockFetch.mockResolvedValue(
        createMockTeamMembersResponse([
          { user_id: 'uuid-2', email: 'newer@factory.com' },
          { user_id: 'uuid-1', email: 'older@factory.com' },
        ])
      )

      // When: The useFollowUps hook processes the data
      const { result } = renderHook(() => useFollowUps({ reportDate: '2026-01-15' }))

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: The returned Map contains the most recently created resolved follow-up
      const followUp = result.current.followUps.get('act-1')
      expect(followUp).toBeDefined()
      expect(followUp!.id).toBe('fu-2')
      expect(followUp!.status).toBe('resolved')
    })

    it('UNIT-012: useFollowUps prefers active over resolved even if resolved is newer', async () => {
      // Given: 2 follow-ups: one "assigned" (older), one "resolved" (newer)
      mockSupabaseQueryResult = {
        data: [
          createMockFollowUpRow({
            id: 'fu-2',
            action_item_id: 'act-1',
            assigned_to: 'uuid-2',
            status: 'resolved',
            created_at: '2026-01-15T12:00:00Z',
          }),
          createMockFollowUpRow({
            id: 'fu-1',
            action_item_id: 'act-1',
            assigned_to: 'uuid-1',
            status: 'assigned',
            created_at: '2026-01-15T08:00:00Z',
          }),
        ],
        error: null,
      }

      mockFetch.mockResolvedValue(
        createMockTeamMembersResponse([
          { user_id: 'uuid-1', email: 'active@factory.com' },
          { user_id: 'uuid-2', email: 'resolved@factory.com' },
        ])
      )

      // When: The useFollowUps hook processes the data
      const { result } = renderHook(() => useFollowUps({ reportDate: '2026-01-15' }))

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: The "assigned" follow-up is selected (active preferred over resolved)
      const followUp = result.current.followUps.get('act-1')
      expect(followUp).toBeDefined()
      expect(followUp!.status).toBe('assigned')
      expect(followUp!.id).toBe('fu-1')
    })

    it('UNIT-013: useFollowUps handles single follow-up per action item correctly', async () => {
      // Given: Exactly one follow-up for an action_item_id
      mockSupabaseQueryResult = {
        data: [
          createMockFollowUpRow({
            id: 'fu-1',
            action_item_id: 'act-1',
            assigned_to: 'uuid-1',
            status: 'assigned',
          }),
        ],
        error: null,
      }

      mockFetch.mockResolvedValue(
        createMockTeamMembersResponse([{ user_id: 'uuid-1', email: 'solo@factory.com' }])
      )

      // When: The useFollowUps hook processes the data
      const { result } = renderHook(() => useFollowUps({ reportDate: '2026-01-15' }))

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: The returned Map contains that single follow-up
      const followUp = result.current.followUps.get('act-1')
      expect(followUp).toBeDefined()
      expect(followUp!.id).toBe('fu-1')
      expect(followUp!.status).toBe('assigned')
    })

    it('UNIT-014: useFollowUps groups follow-ups correctly across different action items', async () => {
      // Given: Follow-ups for 3 different action_item_ids
      mockSupabaseQueryResult = {
        data: [
          // act-1: two follow-ups (one active, one resolved)
          createMockFollowUpRow({
            id: 'fu-1a',
            action_item_id: 'act-1',
            assigned_to: 'uuid-1',
            status: 'assigned',
            created_at: '2026-01-15T12:00:00Z',
          }),
          createMockFollowUpRow({
            id: 'fu-1b',
            action_item_id: 'act-1',
            assigned_to: 'uuid-2',
            status: 'resolved',
            created_at: '2026-01-15T08:00:00Z',
          }),
          // act-2: two follow-ups (both resolved)
          createMockFollowUpRow({
            id: 'fu-2a',
            action_item_id: 'act-2',
            assigned_to: 'uuid-3',
            status: 'resolved',
            created_at: '2026-01-15T14:00:00Z',
          }),
          createMockFollowUpRow({
            id: 'fu-2b',
            action_item_id: 'act-2',
            assigned_to: 'uuid-4',
            status: 'resolved',
            created_at: '2026-01-15T10:00:00Z',
          }),
          // act-3: single follow-up
          createMockFollowUpRow({
            id: 'fu-3',
            action_item_id: 'act-3',
            assigned_to: 'uuid-5',
            status: 'assigned',
            created_at: '2026-01-15T09:00:00Z',
          }),
        ],
        error: null,
      }

      mockFetch.mockResolvedValue(
        createMockTeamMembersResponse([
          { user_id: 'uuid-1', email: 'user1@factory.com' },
          { user_id: 'uuid-2', email: 'user2@factory.com' },
          { user_id: 'uuid-3', email: 'user3@factory.com' },
          { user_id: 'uuid-4', email: 'user4@factory.com' },
          { user_id: 'uuid-5', email: 'user5@factory.com' },
        ])
      )

      // When: The useFollowUps hook processes the data
      const { result } = renderHook(() => useFollowUps({ reportDate: '2026-01-15' }))

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: The returned Map has exactly 3 entries
      expect(result.current.followUps.size).toBe(3)

      // And: act-1 has the active follow-up (assigned, not resolved)
      const fu1 = result.current.followUps.get('act-1')
      expect(fu1).toBeDefined()
      expect(fu1!.status).toBe('assigned')

      // And: act-2 has the most recent resolved follow-up
      const fu2 = result.current.followUps.get('act-2')
      expect(fu2).toBeDefined()
      expect(fu2!.id).toBe('fu-2a')

      // And: act-3 has its single follow-up
      const fu3 = result.current.followUps.get('act-3')
      expect(fu3).toBeDefined()
      expect(fu3!.id).toBe('fu-3')
    })
  })

  // =========================================================================
  // Data Fetching & Query Verification
  // =========================================================================
  describe('Hook Data Fetching & Integration', () => {
    it('UNIT-015: useFollowUps fetches follow-ups filtered by reportDate', async () => {
      // Given: A reportDate of "2026-01-15" is provided
      mockSupabaseQueryResult = { data: [], error: null }

      // When: The hook initializes and fetches data
      const { result } = renderHook(() => useFollowUps({ reportDate: '2026-01-15' }))

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: The Supabase query targets the action_followups table
      expect(mockSupabaseFrom).toHaveBeenCalledWith('action_followups')

      // And: The query includes .eq('report_date', '2026-01-15')
      expect(mockSupabaseEq).toHaveBeenCalledWith('report_date', '2026-01-15')

      // And: The query includes .order('created_at', { ascending: false })
      expect(mockSupabaseOrder).toHaveBeenCalledWith('created_at', { ascending: false })
    })

    it('UNIT-016: useFollowUps resolves assigned_to UUIDs to emails via team members API', async () => {
      // Given: Follow-ups contain assigned_to UUID "uuid-abc"
      mockSupabaseQueryResult = {
        data: [
          createMockFollowUpRow({
            id: 'fu-1',
            action_item_id: 'act-1',
            assigned_to: 'uuid-abc',
            status: 'assigned',
          }),
        ],
        error: null,
      }

      // And: The team members API returns a matching member
      mockFetch.mockResolvedValue(
        createMockTeamMembersResponse([
          { user_id: 'uuid-abc', email: 'alice@factory.com' },
        ])
      )

      // When: The hook processes the data
      const { result } = renderHook(() => useFollowUps({ reportDate: '2026-01-15' }))

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: The returned FollowUpData has assignee_email set to "alice@factory.com"
      const followUp = result.current.followUps.get('act-1')
      expect(followUp).toBeDefined()
      expect(followUp!.assignee_email).toBe('alice@factory.com')
    })

    it('UNIT-017: useFollowUps falls back to truncated UUID when team member email not found', async () => {
      // Given: Follow-ups contain an unresolvable UUID
      mockSupabaseQueryResult = {
        data: [
          createMockFollowUpRow({
            id: 'fu-1',
            action_item_id: 'act-1',
            assigned_to: 'abcdef12-3456-7890-abcd-ef1234567890',
            status: 'assigned',
          }),
        ],
        error: null,
      }

      // And: Team members API does not include this user
      mockFetch.mockResolvedValue(
        createMockTeamMembersResponse([
          { user_id: 'other-uuid', email: 'other@factory.com' },
        ])
      )

      // When: The hook processes the data
      const { result } = renderHook(() => useFollowUps({ reportDate: '2026-01-15' }))

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: The assignee_email falls back to a truncated UUID format
      const followUp = result.current.followUps.get('act-1')
      expect(followUp).toBeDefined()
      expect(followUp!.assignee_email).toMatch(/^abcdef12/)
      expect(followUp!.assignee_email).toMatch(/\.\.\./)
    })

    it('UNIT-018: useFollowUps returns loading state during fetch', () => {
      // Given: The hook is initialized with a valid reportDate
      // Mock a pending promise (never resolves during test)
      mockSupabaseQueryResult = new Promise(() => {}) as any

      // When: The hook is rendered (fetch is in-flight)
      const { result } = renderHook(() => useFollowUps({ reportDate: '2026-01-15' }))

      // Then: The hook returns loading state
      expect(result.current.isLoading).toBe(true)
      expect(result.current.followUps.size).toBe(0)
      expect(result.current.error).toBeNull()
    })

    it('UNIT-019: useFollowUps handles Supabase query error gracefully', async () => {
      // Given: The Supabase query returns an error
      mockSupabaseQueryResult = {
        data: null,
        error: { message: 'Permission denied' },
      }

      // When: The hook processes the error
      const { result } = renderHook(() => useFollowUps({ reportDate: '2026-01-15' }))

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: The hook returns error state
      expect(result.current.followUps.size).toBe(0)
      expect(result.current.error).toBeTruthy()
      expect(result.current.error).toMatch(/permission denied/i)
    })

    it('UNIT-020: useFollowUps handles team members API failure gracefully', async () => {
      // Given: The Supabase query succeeds with follow-ups
      mockSupabaseQueryResult = {
        data: [
          createMockFollowUpRow({
            id: 'fu-1',
            action_item_id: 'act-1',
            assigned_to: 'abcdef12-3456-7890-abcd-ef1234567890',
            status: 'assigned',
          }),
        ],
        error: null,
      }

      // And: The team members API fails
      mockFetch.mockResolvedValue(createMockTeamMembersErrorResponse(500))

      // When: The hook processes the data
      const { result } = renderHook(() => useFollowUps({ reportDate: '2026-01-15' }))

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: The hook still returns follow-ups (does not fail entirely)
      expect(result.current.followUps.size).toBe(1)

      // And: The assignee_email falls back to truncated UUID
      const followUp = result.current.followUps.get('act-1')
      expect(followUp).toBeDefined()
      expect(followUp!.assignee_email).toMatch(/abcdef12/)
      expect(followUp!.assignee_email).toMatch(/\.\.\./)

      // And: No error is set (team member failure is a soft failure)
      expect(result.current.error).toBeNull()
    })
  })
})
