/**
 * useDowntimePareto Hook Tests (Story 14.5: Downtime Pareto Chart on Action Cards)
 *
 * TDD tests — these MUST FAIL until the useDowntimePareto hook is implemented.
 * The hook fetches Pareto breakdown data from GET /api/v1/downtime/pareto
 * and returns { data, isLoading, error, refetch } matching project conventions.
 *
 * @see Story 14.5 - Downtime Pareto Chart on Action Cards
 * @see AC #1 - Horizontal bar chart with reason codes sorted by duration
 * @see AC #3 - Skeleton loader while data is loading
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

const createMockSession = (accessToken: string | null = 'mock-token-abc') => ({
  data: { session: accessToken !== null ? { access_token: accessToken } : null },
})

const createMockParetoItem = (overrides: Record<string, unknown> = {}) => ({
  reason_code: 'Mechanical',
  total_minutes: 180,
  percentage: 35.5,
  cumulative_percentage: 35.5,
  financial_impact: 450.0,
  event_count: 3,
  is_safety_related: false,
  ...overrides,
})

const createMockParetoResponse = (
  items: Record<string, unknown>[] = [],
  overrides: Record<string, unknown> = {}
) => ({
  items,
  total_downtime_minutes: items.reduce(
    (sum: number, i: Record<string, unknown>) => sum + ((i.total_minutes as number) ?? 0),
    0
  ),
  total_financial_impact: 1200.0,
  total_events: items.length,
  data_source: 'downtime_events',
  last_updated: '2026-01-05T12:00:00Z',
  threshold_80_index: 2,
  ...overrides,
})

const createMockFetchResponse = (
  body: unknown,
  status = 200,
  ok = true
) => ({
  ok,
  status,
  json: async () => body,
})

/** Standard 4-item dataset used by many tests */
const STANDARD_PARETO_ITEMS = [
  createMockParetoItem({
    reason_code: 'Mechanical',
    total_minutes: 180,
    percentage: 35.5,
    cumulative_percentage: 35.5,
  }),
  createMockParetoItem({
    reason_code: 'Changeover',
    total_minutes: 120,
    percentage: 23.6,
    cumulative_percentage: 59.1,
  }),
  createMockParetoItem({
    reason_code: 'Planned Maintenance',
    total_minutes: 90,
    percentage: 17.7,
    cumulative_percentage: 76.8,
  }),
  createMockParetoItem({
    reason_code: 'Material Shortage',
    total_minutes: 60,
    percentage: 11.8,
    cumulative_percentage: 88.6,
  }),
]

// ---------------------------------------------------------------------------
// Dynamic import helper - will fail until hook exists
// ---------------------------------------------------------------------------

async function importUseDowntimePareto() {
  const mod = await import('../useDowntimePareto')
  return mod.useDowntimePareto
}

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: Downtime Pareto Chart on Action Cards (Story 14.5)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockReset()
    mockGetSession.mockReset()

    // Default: authenticated session
    mockGetSession.mockResolvedValue(createMockSession('mock-token-abc'))
    // Default: successful response with standard items
    mockFetch.mockResolvedValue(
      createMockFetchResponse(createMockParetoResponse(STANDARD_PARETO_ITEMS))
    )
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // =========================================================================
  // AC1: Pareto data fetching hook
  // =========================================================================
  describe('AC1: useDowntimePareto Hook — Data Fetching', () => {
    it('UNIT-001: Hook returns loading state on initial mount', async () => {
      // Given: The useDowntimePareto hook is called with valid assetId, reportDate, enabled=true
      const useDowntimePareto = await importUseDowntimePareto()
      // Use a never-resolving fetch to capture the loading state
      mockFetch.mockImplementation(() => new Promise(() => {}))

      // When: The hook mounts and the fetch has not yet resolved
      const { result } = renderHook(() =>
        useDowntimePareto({
          assetId: 'asset-001',
          reportDate: '2026-01-05',
          enabled: true,
        })
      )

      // Then: isLoading is true, data is null, error is null
      expect(result.current.isLoading).toBe(true)
      expect(result.current.data).toBeNull()
      expect(result.current.error).toBeNull()
    })

    it('UNIT-002: Hook fetches Pareto data with correct URL and auth header', async () => {
      // Given: Supabase session returns access_token: 'mock-token-abc'
      const useDowntimePareto = await importUseDowntimePareto()
      mockGetSession.mockResolvedValue(createMockSession('mock-token-abc'))

      // When: The hook triggers its fetch with assetId='asset-001' and reportDate='2026-01-05'
      const { result } = renderHook(() =>
        useDowntimePareto({
          assetId: 'asset-001',
          reportDate: '2026-01-05',
          enabled: true,
        })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: fetch is called with correct URL and headers
      expect(mockFetch).toHaveBeenCalled()
      const [url, options] = mockFetch.mock.calls[0]
      expect(url).toContain('/api/v1/downtime/pareto')
      expect(url).toContain('asset_id=asset-001')
      expect(url).toContain('start_date=2026-01-05')
      expect(options.headers).toHaveProperty('Authorization', 'Bearer mock-token-abc')
      expect(options.headers).toHaveProperty('Content-Type', 'application/json')
    })

    it('UNIT-003: Hook sets data on successful API response', async () => {
      // Given: The API returns a valid ParetoResponse with 4 items sorted by total_minutes descending
      const useDowntimePareto = await importUseDowntimePareto()
      const responseData = createMockParetoResponse(STANDARD_PARETO_ITEMS)
      mockFetch.mockResolvedValue(createMockFetchResponse(responseData))

      // When: The fetch resolves successfully
      const { result } = renderHook(() =>
        useDowntimePareto({
          assetId: 'asset-001',
          reportDate: '2026-01-05',
          enabled: true,
        })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: data contains the parsed response with all 4 ParetoItem entries
      expect(result.current.data).not.toBeNull()
      expect(result.current.data!.items).toHaveLength(4)
      expect(result.current.data!.items[0].reason_code).toBe('Mechanical')
      expect(result.current.data!.items[0].total_minutes).toBe(180)
      expect(result.current.data!.items[0].percentage).toBe(35.5)
      expect(result.current.error).toBeNull()
      expect(result.current.isLoading).toBe(false)
    })

    it('UNIT-004: Hook handles network error gracefully', async () => {
      // Given: The useDowntimePareto hook is called with valid params
      const useDowntimePareto = await importUseDowntimePareto()
      // When: The fetch rejects with a network error
      mockFetch.mockRejectedValue(new Error('Network request failed'))

      const { result } = renderHook(() =>
        useDowntimePareto({
          assetId: 'asset-001',
          reportDate: '2026-01-05',
          enabled: true,
        })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: error is set to a descriptive error message, data is null, isLoading is false
      expect(result.current.error).toBeTruthy()
      expect(result.current.data).toBeNull()
      expect(result.current.isLoading).toBe(false)
    })

    it('UNIT-005: Hook handles 401 auth error', async () => {
      // Given: The Supabase session is valid but the API returns HTTP 401
      const useDowntimePareto = await importUseDowntimePareto()
      mockFetch.mockResolvedValue(
        createMockFetchResponse({ error: 'Unauthorized' }, 401, false)
      )

      // When: The fetch resolves with status 401
      const { result } = renderHook(() =>
        useDowntimePareto({
          assetId: 'asset-001',
          reportDate: '2026-01-05',
          enabled: true,
        })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: error is set to an authentication error message, data is null, isLoading is false
      expect(result.current.error).toBeTruthy()
      expect(result.current.error).toMatch(/[Aa]uth|session|expired|401|[Uu]nauthorized/i)
      expect(result.current.data).toBeNull()
      expect(result.current.isLoading).toBe(false)
    })

    it('UNIT-006: Hook handles empty items array', async () => {
      // Given: The API returns a valid ParetoResponse with items: [] and total_downtime_minutes: 0
      const useDowntimePareto = await importUseDowntimePareto()
      const emptyResponse = createMockParetoResponse([], {
        total_downtime_minutes: 0,
        total_financial_impact: 0,
        total_events: 0,
      })
      mockFetch.mockResolvedValue(createMockFetchResponse(emptyResponse))

      // When: The fetch resolves successfully
      const { result } = renderHook(() =>
        useDowntimePareto({
          assetId: 'asset-001',
          reportDate: '2026-01-05',
          enabled: true,
        })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: data is set with the empty response, data.items has length 0
      expect(result.current.data).not.toBeNull()
      expect(result.current.data!.items).toHaveLength(0)
      expect(result.current.isLoading).toBe(false)
      expect(result.current.error).toBeNull()
    })

    it('UNIT-007: Hook does not fetch when enabled is false', async () => {
      // Given: The useDowntimePareto hook is called with enabled=false
      const useDowntimePareto = await importUseDowntimePareto()

      // When: The hook mounts
      const { result } = renderHook(() =>
        useDowntimePareto({
          assetId: 'asset-001',
          reportDate: '2026-01-05',
          enabled: false,
        })
      )

      // Then: fetch is never called, isLoading is false, data is null
      expect(mockFetch).not.toHaveBeenCalled()
      expect(result.current.isLoading).toBe(false)
      expect(result.current.data).toBeNull()
    })

    it('UNIT-008: Hook refetch triggers a new API call', async () => {
      // Given: The hook has completed its initial fetch and returned data
      const useDowntimePareto = await importUseDowntimePareto()
      const firstResponse = createMockParetoResponse(STANDARD_PARETO_ITEMS, {
        last_updated: '2026-01-05T12:00:00Z',
      })
      const secondResponse = createMockParetoResponse(STANDARD_PARETO_ITEMS, {
        last_updated: '2026-01-05T13:00:00Z',
      })

      mockFetch
        .mockResolvedValueOnce(createMockFetchResponse(firstResponse))
        .mockResolvedValueOnce(createMockFetchResponse(secondResponse))

      const { result } = renderHook(() =>
        useDowntimePareto({
          assetId: 'asset-001',
          reportDate: '2026-01-05',
          enabled: true,
        })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.data!.last_updated).toBe('2026-01-05T12:00:00Z')

      // When: refetch() is called
      await act(async () => {
        await result.current.refetch()
      })

      // Then: A new fetch is made and data is updated with the new response
      expect(mockFetch).toHaveBeenCalledTimes(2)
      expect(result.current.data!.last_updated).toBe('2026-01-05T13:00:00Z')
      expect(result.current.isLoading).toBe(false)
    })

    it('UNIT-009: Hook prevents state updates after unmount', async () => {
      // Given: The hook is called and a fetch is in progress
      const useDowntimePareto = await importUseDowntimePareto()
      let resolvePromise: (value: unknown) => void
      const slowFetch = new Promise((resolve) => {
        resolvePromise = resolve
      })
      mockFetch.mockImplementation(() => slowFetch)

      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      const { result, unmount } = renderHook(() =>
        useDowntimePareto({
          assetId: 'asset-001',
          reportDate: '2026-01-05',
          enabled: true,
        })
      )

      // When: The component unmounts before the fetch resolves
      expect(result.current.isLoading).toBe(true)
      unmount()

      // Resolve the fetch after unmount
      resolvePromise!(createMockFetchResponse(createMockParetoResponse(STANDARD_PARETO_ITEMS)))

      // Then: No React state update warnings occur (mountedRef pattern prevents setState)
      await new Promise((r) => setTimeout(r, 50))

      const stateUpdateWarnings = consoleErrorSpy.mock.calls.filter(
        (args) => args.some((arg: unknown) =>
          typeof arg === 'string' && arg.includes('unmounted')
        )
      )
      expect(stateUpdateWarnings).toHaveLength(0)

      consoleErrorSpy.mockRestore()
    })

    it('UNIT-010: Hook handles missing Supabase session', async () => {
      // Given: Supabase getSession returns { data: { session: null } }
      const useDowntimePareto = await importUseDowntimePareto()
      mockGetSession.mockResolvedValue({ data: { session: null } })

      // When: The hook attempts to fetch
      const { result } = renderHook(() =>
        useDowntimePareto({
          assetId: 'asset-001',
          reportDate: '2026-01-05',
          enabled: true,
        })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: error is set to an authentication error, fetch is not called, isLoading is false
      expect(result.current.error).toBeTruthy()
      expect(result.current.error).toMatch(/[Aa]uth|session|expired/i)
      expect(mockFetch).not.toHaveBeenCalled()
      expect(result.current.isLoading).toBe(false)
    })
  })
})
