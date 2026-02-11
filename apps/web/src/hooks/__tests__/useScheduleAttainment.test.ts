/**
 * useScheduleAttainment Hook Tests (Story 12.6: Schedule Attainment UI Section)
 *
 * TDD tests — these MUST FAIL until the hook is implemented.
 * The hook should follow the same Bearer token auth pattern as useDailyActions.ts / useWorkcenterSummary.ts.
 *
 * @see Story 12.6 - Schedule Attainment UI Section
 * @see AC #1 - Schedule attainment data fetching
 * @see AC #3 - Empty state handling (has_schedule: false)
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

const createMockProduct = (overrides: Record<string, unknown> = {}) => ({
  product_name: 'Brazilian',
  scheduled_quantity: 1000,
  actual_quantity: 950,
  attainment_pct: 95.0,
  ...overrides,
})

const createMockVariance = (overrides: Record<string, unknown> = {}) => ({
  type: 'product_swap',
  asset_name: 'Roaster 1',
  message: 'Roaster 1 ran Colombian instead of scheduled Brazilian',
  ...overrides,
})

const createMockWorkcenter = (overrides: Record<string, unknown> = {}) => ({
  workcenter_name: 'Roasting',
  overall_attainment_pct: 92.5,
  products: [
    createMockProduct({ product_name: 'Brazilian', scheduled_quantity: 1000, actual_quantity: 950, attainment_pct: 95.0 }),
    createMockProduct({ product_name: 'Colombian', scheduled_quantity: 500, actual_quantity: 400, attainment_pct: 80.0 }),
  ],
  variance_callouts: [
    createMockVariance({ type: 'product_swap', message: 'Roaster 1 ran Colombian instead of scheduled Brazilian' }),
  ],
  ...overrides,
})

const createMockAttainmentResponse = (overrides: Record<string, unknown> = {}) => ({
  workcenters: [
    createMockWorkcenter({ workcenter_name: 'Roasting' }),
    createMockWorkcenter({ workcenter_name: 'Grinding', overall_attainment_pct: 88.0 }),
  ],
  report_date: '2026-02-10',
  has_schedule: true,
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

import { useScheduleAttainment } from '../useScheduleAttainment'

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: useScheduleAttainment Hook (Story 12.6)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockReset()
    mockGetSession.mockReset()

    // Default: authenticated session
    mockGetSession.mockResolvedValue(createMockSession('mock-token-123'))
    // Default: successful response
    mockFetch.mockResolvedValue(
      createMockFetchResponse(200, createMockAttainmentResponse())
    )
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // =========================================================================
  // Auth and Fetching
  // =========================================================================
  describe('Auth and data fetching', () => {
    it('UNIT-032: Hook fetches with Bearer token authentication', async () => {
      // Given: Supabase auth returns a valid session with access_token="mock-token-123"
      mockGetSession.mockResolvedValue(createMockSession('mock-token-123'))

      // When: useScheduleAttainment hook mounts and fetches data
      const { result } = renderHook(() =>
        useScheduleAttainment({ date: '2026-02-10' })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: fetch is called with Authorization header "Bearer mock-token-123"
      expect(mockFetch).toHaveBeenCalled()
      const [, options] = mockFetch.mock.calls[0]
      expect(options.headers).toHaveProperty('Authorization', 'Bearer mock-token-123')
    })

    it('UNIT-033: Hook calls correct API endpoint with date parameter', async () => {
      // Given: useScheduleAttainment is called with date="2026-02-10"
      mockGetSession.mockResolvedValue(createMockSession('mock-token-123'))

      // When: The hook fetches data
      const { result } = renderHook(() =>
        useScheduleAttainment({ date: '2026-02-10' })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: fetch is called with URL matching /api/v1/production/schedule-attainment?date=2026-02-10
      expect(mockFetch).toHaveBeenCalled()
      const [url] = mockFetch.mock.calls[0]
      expect(url).toContain('/api/v1/production/schedule-attainment')
      expect(url).toContain('date=2026-02-10')
    })

    it('UNIT-034: Hook defaults to T-1 date when no date provided', async () => {
      // Given: useScheduleAttainment is called without a date parameter
      mockGetSession.mockResolvedValue(createMockSession('mock-token-123'))

      // When: The hook fetches data
      const { result } = renderHook(() =>
        useScheduleAttainment()
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: fetch is called with a date query parameter equal to yesterday's date
      expect(mockFetch).toHaveBeenCalled()
      const [url] = mockFetch.mock.calls[0]
      const yesterday = getYesterday()
      expect(url).toContain(`date=${yesterday}`)
    })

    it('UNIT-035: Hook returns isLoading=true initially then false after fetch completes', async () => {
      // Given: useScheduleAttainment hook is rendered
      const { result } = renderHook(() =>
        useScheduleAttainment({ date: '2026-02-10' })
      )

      // When: The hook initializes
      // Then: isLoading is initially true
      expect(result.current.isLoading).toBe(true)

      // When: The fetch resolves
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: isLoading transitions to false
      expect(result.current.isLoading).toBe(false)
    })

    it('UNIT-036: Hook returns parsed data on successful fetch', async () => {
      // Given: API returns a valid ScheduleAttainmentResponse with 2 workcenters
      const mockData = createMockAttainmentResponse()
      mockFetch.mockResolvedValue(createMockFetchResponse(200, mockData))

      // When: useScheduleAttainment hook completes fetching
      const { result } = renderHook(() =>
        useScheduleAttainment({ date: '2026-02-10' })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: data matches the API response shape with workcenters, date, has_schedule=true
      expect(result.current.data).toBeTruthy()
      expect(result.current.data!.workcenters).toHaveLength(2)
      expect(result.current.data!.workcenters[0].workcenter_name).toBe('Roasting')
      expect(result.current.data!.workcenters[1].workcenter_name).toBe('Grinding')
      expect(result.current.data!.has_schedule).toBe(true)
      expect(result.current.data!.report_date).toBe('2026-02-10')
      expect(result.current.error).toBeNull()
    })
  })

  // =========================================================================
  // Error Handling
  // =========================================================================
  describe('Error handling', () => {
    it('UNIT-037: Hook sets error on network failure', async () => {
      // Given: fetch rejects with a network error
      mockFetch.mockRejectedValue(new TypeError('Failed to fetch'))

      // When: useScheduleAttainment hook attempts to fetch
      const { result } = renderHook(() =>
        useScheduleAttainment({ date: '2026-02-10' })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: error is set to a descriptive error message, data is null
      expect(result.current.error).toBeTruthy()
      expect(result.current.data).toBeNull()
      expect(result.current.isLoading).toBe(false)
    })

    it('UNIT-038: Hook sets error on 401 unauthorized response', async () => {
      // Given: API returns 401 status
      mockFetch.mockResolvedValue(
        createMockFetchResponse(401, { detail: 'Unauthorized' })
      )

      // When: useScheduleAttainment hook processes the response
      const { result } = renderHook(() =>
        useScheduleAttainment({ date: '2026-02-10' })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: error is set to an authentication-related error message, data is null
      expect(result.current.error).toBeTruthy()
      expect(result.current.error).toMatch(/[Aa]uth|session|expired|log in/i)
      expect(result.current.data).toBeNull()
    })

    it('UNIT-039: Hook sets error on 500 server error', async () => {
      // Given: API returns 500 status
      mockFetch.mockResolvedValue(
        createMockFetchResponse(500, { detail: 'Internal Server Error' })
      )

      // When: useScheduleAttainment hook processes the response
      const { result } = renderHook(() =>
        useScheduleAttainment({ date: '2026-02-10' })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: error is set to a server error message, data is null
      expect(result.current.error).toBeTruthy()
      expect(result.current.data).toBeNull()
      expect(result.current.isLoading).toBe(false)
    })

    it('UNIT-040: Hook handles null session gracefully', async () => {
      // Given: Supabase auth getSession returns null session
      mockGetSession.mockResolvedValue({ data: { session: null } })

      // When: useScheduleAttainment hook attempts to fetch
      const { result } = renderHook(() =>
        useScheduleAttainment({ date: '2026-02-10' })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: error is set to an auth-related message, fetch is NOT called
      expect(result.current.error).toMatch(/[Aa]uthentication/)
      expect(mockFetch).not.toHaveBeenCalled()
    })
  })

  // =========================================================================
  // Refetch and Lifecycle
  // =========================================================================
  describe('Refetch and lifecycle', () => {
    it('UNIT-041: Hook refetch function triggers a new fetch', async () => {
      // Given: useScheduleAttainment hook has completed initial fetch
      const { result } = renderHook(() =>
        useScheduleAttainment({ date: '2026-02-10' })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      const initialCallCount = mockFetch.mock.calls.length

      // When: refetch() is called
      await act(async () => {
        await result.current.refetch()
      })

      // Then: fetch is called again with the same URL and auth headers
      expect(mockFetch.mock.calls.length).toBeGreaterThan(initialCallCount)
    })

    it('UNIT-042: Hook does not update state after unmount', async () => {
      // Given: useScheduleAttainment hook is rendered and a slow fetch is in progress
      let resolvePromise: (value: unknown) => void
      const delayedFetch = new Promise((resolve) => {
        resolvePromise = resolve
      })
      mockFetch.mockReturnValue(delayedFetch)

      const { result, unmount } = renderHook(() =>
        useScheduleAttainment({ date: '2026-02-10' })
      )

      // Verify loading state
      expect(result.current.isLoading).toBe(true)

      // When: The component unmounts before the fetch resolves
      unmount()

      // Then: Resolving the fetch after unmount should not cause errors
      await act(async () => {
        resolvePromise!(
          createMockFetchResponse(200, createMockAttainmentResponse())
        )
      })

      // No state update should occur (mountedRef pattern)
      expect(result.current.isLoading).toBe(true)
    })

    it('UNIT-043: Hook returns has_schedule false when API indicates no schedule', async () => {
      // Given: API returns {has_schedule: false, workcenters: [], ...}
      const emptyResponse = createMockAttainmentResponse({
        has_schedule: false,
        workcenters: [],
        message: 'No schedule data for this date',
      })
      mockFetch.mockResolvedValue(createMockFetchResponse(200, emptyResponse))

      // When: useScheduleAttainment hook completes fetching
      const { result } = renderHook(() =>
        useScheduleAttainment({ date: '2026-02-10' })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: data.has_schedule is false, data.workcenters is empty
      expect(result.current.data).toBeTruthy()
      expect(result.current.data!.has_schedule).toBe(false)
      expect(result.current.data!.workcenters).toHaveLength(0)
      expect(result.current.data!.message).toContain('No schedule data')
    })
  })
})
