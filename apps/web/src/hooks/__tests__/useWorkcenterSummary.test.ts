/**
 * useWorkcenterSummary Hook Tests (Story 11.2: Workcenter Scorecard UI Component)
 *
 * TDD tests — these MUST FAIL until the hook is implemented.
 * The hook should follow the same Bearer token auth pattern as useDailyActions.ts.
 *
 * @see Story 11.2 - Workcenter Scorecard UI Component
 * @see AC #1 - Scorecard data fetching
 * @see AC #3 - Empty state handling
 */

import { renderHook, act, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockGetSession = vi.fn()
const mockCreateClient = vi.fn(() => ({
  auth: {
    getSession: mockGetSession,
  },
}))

vi.mock('@/lib/supabase/client', () => ({
  createClient: () => mockCreateClient(),
}))

// Mock global.fetch
const mockFetch = vi.fn()
global.fetch = mockFetch

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const MOCK_API_URL = 'http://localhost:8000'

const createMockSession = (accessToken: string | null = 'mock-token-123') => ({
  data: { session: accessToken !== null ? { access_token: accessToken } : null },
})

const createMockWorkcenterResponse = (overrides: Record<string, unknown> = {}) => ({
  workcenters: [
    {
      workcenter_name: 'Grinding',
      total_actual: 4200,
      total_target: 5000,
      attainment_percentage: 84.0,
      assets_on_target: 2,
      assets_missed: 2,
      total_assets: 4,
      assets: [
        {
          asset_name: 'Grinder 1',
          actual: 1200,
          target: 1300,
          oee: 85.2,
          downtime_minutes: 45,
        },
      ],
    },
  ],
  date: '2026-02-10',
  total_actual: 4200,
  total_target: 5000,
  total_attainment: 84.0,
  ...overrides,
})

const createMockFetchResponse = (
  status: number,
  body: unknown,
  ok?: boolean
) => ({
  ok: ok ?? (status >= 200 && status < 300),
  status,
  json: async () => body,
})

/**
 * Helper: compute yesterday's date in YYYY-MM-DD format
 */
function getYesterday(): string {
  const d = new Date()
  d.setDate(d.getDate() - 1)
  return d.toISOString().split('T')[0]
}

// ---------------------------------------------------------------------------
// Import hook AFTER mocks are set up
// ---------------------------------------------------------------------------

import { useWorkcenterSummary } from '../useWorkcenterSummary'

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: useWorkcenterSummary Hook (Story 11.2)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockReset()
    mockGetSession.mockReset()

    // Default: authenticated session
    mockGetSession.mockResolvedValue(createMockSession('mock-token-123'))
    // Default: successful response
    mockFetch.mockResolvedValue(
      createMockFetchResponse(200, createMockWorkcenterResponse())
    )
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // =========================================================================
  // Auth and Fetching
  // =========================================================================
  describe('Auth and data fetching', () => {
    it('UNIT-042: Hook fetches with Bearer token auth', async () => {
      // Given: Supabase session exists with access_token "mock-token-123"
      mockGetSession.mockResolvedValue(createMockSession('mock-token-123'))

      // When: useWorkcenterSummary hook mounts and autoFetches
      const { result } = renderHook(() =>
        useWorkcenterSummary({ apiUrl: MOCK_API_URL, autoFetch: true })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: fetch is called with Authorization header "Bearer mock-token-123"
      expect(mockFetch).toHaveBeenCalled()
      const [, options] = mockFetch.mock.calls[0]
      expect(options.headers).toHaveProperty('Authorization', 'Bearer mock-token-123')
    })

    it('UNIT-043: Hook defaults date to T-1 (yesterday)', async () => {
      // Given: no date parameter is provided
      mockGetSession.mockResolvedValue(createMockSession('mock-token-123'))

      // When: the hook makes the API call
      const { result } = renderHook(() =>
        useWorkcenterSummary({ apiUrl: MOCK_API_URL, autoFetch: true })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: the URL includes date parameter set to yesterday's date
      expect(mockFetch).toHaveBeenCalled()
      const [url] = mockFetch.mock.calls[0]
      const yesterday = getYesterday()
      expect(url).toContain(`date=${yesterday}`)
    })

    it('UNIT-044: Hook returns data on successful fetch', async () => {
      // Given: API returns 200 with valid WorkcenterSummaryResponse
      const mockData = createMockWorkcenterResponse()
      mockFetch.mockResolvedValue(createMockFetchResponse(200, mockData))

      // When: useWorkcenterSummary hook completes fetching
      const { result } = renderHook(() =>
        useWorkcenterSummary({ apiUrl: MOCK_API_URL, autoFetch: true })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: hook returns data with workcenters array, isLoading: false, error: null
      expect(result.current.data).toBeTruthy()
      expect(result.current.data!.workcenters).toHaveLength(1)
      expect(result.current.data!.workcenters[0].workcenter_name).toBe('Grinding')
      expect(result.current.isLoading).toBe(false)
      expect(result.current.error).toBeNull()
    })

    it('UNIT-045: Hook handles null session (no auth)', async () => {
      // Given: Supabase getSession returns null session
      mockGetSession.mockResolvedValue({ data: { session: null } })

      // When: useWorkcenterSummary hook attempts to fetch
      const { result } = renderHook(() =>
        useWorkcenterSummary({ apiUrl: MOCK_API_URL, autoFetch: true })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: hook returns error "Authentication required" and does NOT call fetch
      expect(result.current.error).toMatch(/[Aa]uthentication/)
      expect(mockFetch).not.toHaveBeenCalled()
    })
  })

  // =========================================================================
  // Error Handling
  // =========================================================================
  describe('Error handling', () => {
    it('UNIT-046: Hook handles 404 response as empty state', async () => {
      // Given: API returns 404
      mockFetch.mockResolvedValue(createMockFetchResponse(404, { detail: 'Not found' }))

      // When: useWorkcenterSummary hook processes the response
      const { result } = renderHook(() =>
        useWorkcenterSummary({ apiUrl: MOCK_API_URL, autoFetch: true })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: hook returns data with empty workcenters array (not error)
      expect(result.current.error).toBeNull()
      expect(result.current.data).toBeTruthy()
      expect(result.current.data!.workcenters).toHaveLength(0)
    })

    it('UNIT-047: Hook handles 401 unauthorized response', async () => {
      // Given: API returns 401 Unauthorized
      mockFetch.mockResolvedValue(
        createMockFetchResponse(401, { detail: 'Unauthorized' })
      )

      // When: useWorkcenterSummary hook processes the response
      const { result } = renderHook(() =>
        useWorkcenterSummary({ apiUrl: MOCK_API_URL, autoFetch: true })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: hook returns appropriate authentication error message
      expect(result.current.error).toBeTruthy()
      expect(result.current.error).toMatch(/[Aa]uth|session|expired|log in/i)
    })

    it('UNIT-048: Hook handles 500 server error response', async () => {
      // Given: API returns 500 Internal Server Error
      mockFetch.mockResolvedValue(
        createMockFetchResponse(500, { detail: 'Internal Server Error' })
      )

      // When: useWorkcenterSummary hook processes the response
      const { result } = renderHook(() =>
        useWorkcenterSummary({ apiUrl: MOCK_API_URL, autoFetch: true })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: hook returns error state with server error message
      expect(result.current.error).toBeTruthy()
      expect(result.current.isLoading).toBe(false)
    })

    it('UNIT-049: Hook handles network failure', async () => {
      // Given: fetch throws a network error
      mockFetch.mockRejectedValue(new TypeError('Failed to fetch'))

      // When: useWorkcenterSummary hook processes the error
      const { result } = renderHook(() =>
        useWorkcenterSummary({ apiUrl: MOCK_API_URL, autoFetch: true })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: hook returns error state with appropriate network error message
      expect(result.current.error).toBeTruthy()
      expect(result.current.isLoading).toBe(false)
    })
  })

  // =========================================================================
  // Refetch and Lifecycle
  // =========================================================================
  describe('Refetch and lifecycle', () => {
    it('UNIT-050: Hook refetch function triggers new fetch', async () => {
      // Given: useWorkcenterSummary has completed initial fetch
      const { result } = renderHook(() =>
        useWorkcenterSummary({ apiUrl: MOCK_API_URL, autoFetch: true })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      const initialCallCount = mockFetch.mock.calls.length

      // When: refetch function is called
      await act(async () => {
        await result.current.refetch()
      })

      // Then: a new fetch call is made to the API endpoint
      expect(mockFetch.mock.calls.length).toBeGreaterThan(initialCallCount)
    })

    it('UNIT-051: Hook does not update state after unmount', async () => {
      // Given: useWorkcenterSummary hook is mounted and fetch is in-flight
      let resolvePromise: (value: unknown) => void
      const delayedFetch = new Promise((resolve) => {
        resolvePromise = resolve
      })
      mockFetch.mockReturnValue(delayedFetch)

      const { result, unmount } = renderHook(() =>
        useWorkcenterSummary({ apiUrl: MOCK_API_URL, autoFetch: true })
      )

      // Verify loading state
      expect(result.current.isLoading).toBe(true)

      // When: the component unmounts before fetch completes
      unmount()

      // Then: resolving the fetch after unmount should not cause errors
      // (mountedRef pattern prevents state updates after unmount)
      await act(async () => {
        resolvePromise!(
          createMockFetchResponse(200, createMockWorkcenterResponse())
        )
      })

      // No assertion needed here — if the hook tries to setState after unmount,
      // React will warn. The test passes if no warning/error is thrown.
      // We can also verify the result didn't update:
      expect(result.current.isLoading).toBe(true) // still true — no update happened
    })
  })
})
