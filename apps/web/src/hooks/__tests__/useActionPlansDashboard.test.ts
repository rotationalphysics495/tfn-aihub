/**
 * useActionPlansDashboard Hook Tests (Story 16.5: Action Plans Dashboard)
 *
 * TDD tests — these MUST FAIL until the useActionPlansDashboard hook is implemented.
 * Tests cover data fetching with auth, client-side grouping by status,
 * and integration with the action plans API.
 *
 * @see Story 16.5 - Action Plans Dashboard
 * @see AC #1 - Dashboard displays grouped action plans
 */

import { renderHook, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'

// ---------------------------------------------------------------------------
// Mocks (BEFORE imports)
// ---------------------------------------------------------------------------

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => '/action-plans',
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

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

interface ActionPlan {
  id: string
  title: string
  description: string | null
  asset_id: string | null
  asset_name: string | null
  category: string
  root_cause: string | null
  corrective_action: string | null
  preventive_action: string | null
  source_followup_id: string | null
  owner_id: string
  owner_email: string
  status: 'open' | 'in_progress' | 'completed' | 'verified'
  priority: 'low' | 'medium' | 'high' | 'critical'
  due_date: string | null
  completed_at: string | null
  verified_by: string | null
  verified_at: string | null
  created_at: string
  updated_at: string
}

const createMockActionPlan = (overrides: Partial<ActionPlan> = {}): ActionPlan => ({
  id: 'ap-001',
  title: 'Replace worn bearing',
  description: null,
  asset_id: 'asset-001',
  asset_name: 'Grinder 5',
  category: 'corrective',
  root_cause: null,
  corrective_action: null,
  preventive_action: null,
  source_followup_id: null,
  owner_id: 'user-001',
  owner_email: 'manager@company.com',
  status: 'open',
  priority: 'high',
  due_date: '2026-02-20',
  completed_at: null,
  verified_by: null,
  verified_at: null,
  created_at: '2026-02-10T08:00:00Z',
  updated_at: '2026-02-10T08:00:00Z',
  ...overrides,
})

const createMockListResponse = (plans: ActionPlan[]) => ({
  ok: true,
  status: 200,
  json: async () => ({
    plans,
    total_count: plans.length,
    counts_by_status: plans.reduce(
      (acc, p) => {
        acc[p.status] = (acc[p.status] || 0) + 1
        return acc
      },
      {} as Record<string, number>
    ),
  }),
})

const createMockSession = (accessToken: string | null = 'mock-token') => ({
  data: {
    session: accessToken !== null
      ? { access_token: accessToken, user: { id: 'user-001' } }
      : null,
  },
})

// ---------------------------------------------------------------------------
// Import hook AFTER mocks
// ---------------------------------------------------------------------------

// The hook does not exist yet in this form — import will fail until it's created.
// The existing useActionPlans hook is for CRUD; this is a new dashboard-specific hook
// (or an extended version of useActionPlans with list/group functionality).
import { useActionPlansDashboard } from '@/hooks/useActionPlansDashboard'

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: useActionPlansDashboard Hook (Story 16.5)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockReset()
    mockGetSession.mockReset()

    mockGetSession.mockResolvedValue(createMockSession('mock-token'))
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('AC1: Data fetching', () => {
    it('16-5-action-plans-dashboard-INT-001: useActionPlansDashboard hook fetches with auth token and page_size=100', async () => {
      // Given: The session is authenticated with a valid token
      const plans = [createMockActionPlan()]
      mockFetch.mockResolvedValue(createMockListResponse(plans))

      // When: The hook is rendered
      const { result } = renderHook(() => useActionPlansDashboard())

      // Then: A fetch call is made with the auth token
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled()
      })

      const [url, options] = mockFetch.mock.calls[0]

      // And: The request includes Authorization header with Bearer token
      expect(options.headers).toHaveProperty('Authorization', 'Bearer mock-token')

      // And: The URL includes page_size=100
      expect(url).toContain('page_size=100')
    })

    it('16-5-action-plans-dashboard-INT-002: useActionPlansDashboard hook groups plans by status client-side', async () => {
      // Given: The API returns plans across multiple statuses
      const plans = [
        createMockActionPlan({ id: 'ap-1', status: 'open' }),
        createMockActionPlan({ id: 'ap-2', status: 'open' }),
        createMockActionPlan({ id: 'ap-3', status: 'in_progress' }),
        createMockActionPlan({ id: 'ap-4', status: 'completed' }),
        createMockActionPlan({ id: 'ap-5', status: 'verified' }),
        createMockActionPlan({ id: 'ap-6', status: 'verified' }),
      ]
      mockFetch.mockResolvedValue(createMockListResponse(plans))

      // When: The hook completes loading
      const { result } = renderHook(() => useActionPlansDashboard())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: Plans are grouped by status
      expect(result.current.grouped.open).toHaveLength(2)
      expect(result.current.grouped.in_progress).toHaveLength(1)
      expect(result.current.grouped.completed).toHaveLength(1)
      expect(result.current.grouped.verified).toHaveLength(2)

      // And: totalCount is correct
      expect(result.current.totalCount).toBe(6)
    })

    it('Hook returns isLoading=true initially', () => {
      // Given: A fetch that never resolves
      mockFetch.mockReturnValue(new Promise(() => {}))

      // When: The hook renders
      const { result } = renderHook(() => useActionPlansDashboard())

      // Then: isLoading is true
      expect(result.current.isLoading).toBe(true)
    })

    it('Hook returns error on API failure', async () => {
      // Given: The API returns a 500 error
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => ({ detail: 'Internal server error' }),
      })

      // When: The hook renders
      const { result } = renderHook(() => useActionPlansDashboard())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: error is set
      expect(result.current.error).toBeTruthy()
    })

    it('Hook returns error on auth failure', async () => {
      // Given: No session
      mockGetSession.mockResolvedValue(createMockSession(null))

      // When: The hook renders
      const { result } = renderHook(() => useActionPlansDashboard())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: error indicates auth failure
      expect(result.current.error).toMatch(/session|auth|log in/i)
    })

    it('Hook provides a refetch function', async () => {
      // Given: Initial fetch succeeds
      const plans = [createMockActionPlan()]
      mockFetch.mockResolvedValue(createMockListResponse(plans))

      const { result } = renderHook(() => useActionPlansDashboard())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // When: refetch is called
      expect(typeof result.current.refetch).toBe('function')

      mockFetch.mockResolvedValue(createMockListResponse([
        ...plans,
        createMockActionPlan({ id: 'ap-new' }),
      ]))

      result.current.refetch()

      // Then: A second fetch call is made
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(2)
      })
    })

    it('Hook returns empty groups when no plans exist', async () => {
      // Given: The API returns zero plans
      mockFetch.mockResolvedValue(createMockListResponse([]))

      // When: The hook renders
      const { result } = renderHook(() => useActionPlansDashboard())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: All groups are empty arrays
      expect(result.current.grouped.open).toEqual([])
      expect(result.current.grouped.in_progress).toEqual([])
      expect(result.current.grouped.completed).toEqual([])
      expect(result.current.grouped.verified).toEqual([])
      expect(result.current.totalCount).toBe(0)
    })
  })
})
