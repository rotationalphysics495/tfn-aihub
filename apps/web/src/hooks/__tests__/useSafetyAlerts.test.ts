/**
 * useSafetyAlerts Hook Tests (Story 10.1: Safety Alerts Auth Fix)
 *
 * TDD tests — these MUST FAIL until the auth pattern is fixed.
 * The hook currently uses `credentials: 'include'` (cookie-based auth)
 * but should use `Authorization: Bearer <token>` (JWT-based auth).
 *
 * @see Story 10.1 - Safety Alerts Auth Fix
 * @see AC #1 - Bearer Token Auth Pattern
 * @see AC #2 - Expired Session Handling
 * @see AC #3 - Acknowledge Endpoint Auth Fix
 * @see AC #4 - Consistency With Other Hooks
 */

import { renderHook, act, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

// Track call order across createClient, getSession, and fetch
const callOrder: string[] = []

const mockGetSession = vi.fn()
const mockCreateClient = vi.fn(() => ({
  auth: {
    getSession: (...args: unknown[]) => {
      callOrder.push('getSession')
      return mockGetSession(...args)
    },
  },
}))

vi.mock('@/lib/supabase/client', () => ({
  createClient: (...args: unknown[]) => {
    callOrder.push('createClient')
    return mockCreateClient(...args)
  },
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

const createMockSafetyEvent = (overrides: Record<string, unknown> = {}) => ({
  id: 'evt-1',
  asset_id: 'asset-001',
  asset_name: 'Grinder 5',
  area: 'grinding',
  event_timestamp: '2026-02-11T08:00:00Z',
  reason_code: 'SAFETY_STOP',
  severity: 'high',
  description: 'Emergency stop triggered',
  duration_minutes: 15,
  financial_impact: 2500,
  acknowledged: false,
  acknowledged_at: null,
  created_at: '2026-02-11T08:00:00Z',
  ...overrides,
})

const createMockAlertsResponse = (events: Record<string, unknown>[] = [], count?: number) => ({
  ok: true,
  status: 200,
  json: async () => ({
    events,
    count: count ?? events.length,
    last_updated: '2026-02-11T12:00:00Z',
  }),
})

const createMockAcknowledgeResponse = (success = true) => ({
  ok: true,
  status: 200,
  json: async () => ({ success }),
})

// ---------------------------------------------------------------------------
// Import hooks AFTER mocks are set up
// ---------------------------------------------------------------------------

import { useSafetyAlerts, useSafetyAlertCount } from '../useSafetyAlerts'

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: Safety Alerts Auth Fix (Story 10.1)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    callOrder.length = 0
    mockFetch.mockReset()
    mockGetSession.mockReset()

    // Default: authenticated session
    mockGetSession.mockResolvedValue(createMockSession('mock-token-abc'))
    // Default: successful empty response
    mockFetch.mockResolvedValue(createMockAlertsResponse())
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // =========================================================================
  // AC1: Bearer Token Auth Pattern
  // =========================================================================
  describe('AC1: Bearer Token Auth Pattern', () => {
    it('UNIT-001: fetchAlerts sends Bearer token in Authorization header', async () => {
      // Given: A user is authenticated with a valid Supabase session
      mockGetSession.mockResolvedValue(createMockSession('mock-token-abc'))
      mockFetch.mockResolvedValue(createMockAlertsResponse())

      // When: The useSafetyAlerts hook mounts and fetchAlerts is invoked
      const { result } = renderHook(() =>
        useSafetyAlerts({ apiUrl: MOCK_API_URL, autoFetch: true })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: The fetch call includes Authorization: Bearer mock-token-abc
      expect(mockFetch).toHaveBeenCalled()
      const [url, options] = mockFetch.mock.calls[0]
      expect(url).toBe(`${MOCK_API_URL}/api/safety/active`)
      expect(options.headers).toHaveProperty('Authorization', 'Bearer mock-token-abc')

      // And: The fetch call does NOT include credentials: 'include'
      expect(options).not.toHaveProperty('credentials')
    })

    it('UNIT-002: fetchAlerts returns safety events on successful auth', async () => {
      // Given: A user is authenticated and the API returns 2 safety events
      const evt1 = createMockSafetyEvent({ id: 'evt-1' })
      const evt2 = createMockSafetyEvent({ id: 'evt-2', asset_name: 'Mixer 3' })
      mockGetSession.mockResolvedValue(createMockSession('mock-token-abc'))
      mockFetch.mockResolvedValue(createMockAlertsResponse([evt1, evt2], 2))

      // When: fetchAlerts completes successfully
      const { result } = renderHook(() =>
        useSafetyAlerts({ apiUrl: MOCK_API_URL, autoFetch: true })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: state.alerts contains the 2 events, activeCount is 2, error is null
      expect(result.current.alerts).toHaveLength(2)
      expect(result.current.activeCount).toBe(2)
      expect(result.current.error).toBeNull()
      expect(result.current.isLoading).toBe(false)
    })

    it('UNIT-003: fetchAlerts does not use credentials include', async () => {
      // Given: A user is authenticated with a valid session
      mockGetSession.mockResolvedValue(createMockSession('mock-token-abc'))
      mockFetch.mockResolvedValue(createMockAlertsResponse())

      // When: fetchAlerts executes a fetch call
      const { result } = renderHook(() =>
        useSafetyAlerts({ apiUrl: MOCK_API_URL, autoFetch: true })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: The fetch call options do NOT contain a credentials property
      expect(mockFetch).toHaveBeenCalled()
      const [, options] = mockFetch.mock.calls[0]
      expect(options).not.toHaveProperty('credentials')
    })
  })

  // =========================================================================
  // AC2: Expired Session Handling
  // =========================================================================
  describe('AC2: Expired Session Handling', () => {
    it('UNIT-004: fetchAlerts handles null session gracefully', async () => {
      // Given: The user's session has expired (getSession returns null session)
      mockGetSession.mockResolvedValue({ data: { session: null } })

      // When: fetchAlerts is invoked
      const { result } = renderHook(() =>
        useSafetyAlerts({ apiUrl: MOCK_API_URL, autoFetch: true })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: state.error is set to auth error, isLoading is false
      expect(result.current.error).toBe('Authentication required')
      expect(result.current.isLoading).toBe(false)

      // And: global.fetch is NOT called (early return before network request)
      expect(mockFetch).not.toHaveBeenCalled()
    })

    it('UNIT-005: fetchAlerts handles missing access_token gracefully', async () => {
      // Given: Session exists but access_token is null
      mockGetSession.mockResolvedValue({
        data: { session: { access_token: null } },
      })

      // When: fetchAlerts is invoked
      const { result } = renderHook(() =>
        useSafetyAlerts({ apiUrl: MOCK_API_URL, autoFetch: true })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: state.error is set to auth error, isLoading is false
      expect(result.current.error).toBeTruthy()
      expect(result.current.error).toMatch(/[Aa]uthentication/)
      expect(result.current.isLoading).toBe(false)

      // And: global.fetch is NOT called
      expect(mockFetch).not.toHaveBeenCalled()
    })

    it('UNIT-006: No 403 error message exposed to user on expired session', async () => {
      // Given: The user's session has expired
      mockGetSession.mockResolvedValue({ data: { session: null } })

      // When: fetchAlerts is invoked
      const { result } = renderHook(() =>
        useSafetyAlerts({ apiUrl: MOCK_API_URL, autoFetch: true })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: The error message does NOT contain '403' or 'Forbidden'
      const errorMsg = result.current.error ?? ''
      expect(errorMsg).not.toMatch(/403/)
      expect(errorMsg).not.toMatch(/[Ff]orbidden/)

      // And: The error message is user-friendly
      expect(errorMsg).toMatch(/[Aa]uthentication/)
    })
  })

  // =========================================================================
  // AC3: Acknowledge Endpoint Auth Fix
  // =========================================================================
  describe('AC3: Acknowledge Endpoint Auth Fix', () => {
    it('UNIT-007: acknowledge sends Bearer token in Authorization header', async () => {
      // Given: A user is authenticated with access_token 'mock-token-xyz'
      mockGetSession.mockResolvedValue(createMockSession('mock-token-xyz'))
      mockFetch
        .mockResolvedValueOnce(createMockAlertsResponse()) // initial fetchAlerts
        .mockResolvedValueOnce(createMockAcknowledgeResponse()) // acknowledge

      const { result } = renderHook(() =>
        useSafetyAlerts({ apiUrl: MOCK_API_URL, autoFetch: true })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // When: acknowledge('evt-123') is called
      await act(async () => {
        await result.current.acknowledge('evt-123')
      })

      // Then: The POST fetch call includes Authorization: Bearer mock-token-xyz
      const acknowledgeCalls = mockFetch.mock.calls.filter(
        ([url]: [string]) => url.includes('/api/safety/acknowledge/')
      )
      expect(acknowledgeCalls).toHaveLength(1)
      const [ackUrl, ackOptions] = acknowledgeCalls[0]
      expect(ackUrl).toBe(`${MOCK_API_URL}/api/safety/acknowledge/evt-123`)
      expect(ackOptions.headers).toHaveProperty('Authorization', 'Bearer mock-token-xyz')
      expect(ackOptions.method).toBe('POST')

      // And: The credentials option is NOT present
      expect(ackOptions).not.toHaveProperty('credentials')
    })

    it('UNIT-008: acknowledge returns false on expired session', async () => {
      // Given: Initial fetch succeeds, then session expires
      mockGetSession
        .mockResolvedValueOnce(createMockSession('mock-token-abc')) // initial mount
        .mockResolvedValueOnce({ data: { session: null } }) // acknowledge attempt
      mockFetch.mockResolvedValue(createMockAlertsResponse())

      const { result } = renderHook(() =>
        useSafetyAlerts({ apiUrl: MOCK_API_URL, autoFetch: true })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Reset fetch call tracking after initial load
      mockFetch.mockClear()

      // When: acknowledge('evt-456') is called with expired session
      let ackResult: boolean = true
      await act(async () => {
        ackResult = await result.current.acknowledge('evt-456')
      })

      // Then: The function returns false
      expect(ackResult).toBe(false)

      // And: global.fetch is NOT called (no POST request made)
      expect(mockFetch).not.toHaveBeenCalled()
    })

    it('UNIT-009: acknowledge updates local state on success', async () => {
      // Given: User is authenticated and state contains alert evt-789
      const evt789 = createMockSafetyEvent({ id: 'evt-789', acknowledged: false })
      mockGetSession.mockResolvedValue(createMockSession('mock-token-abc'))
      mockFetch
        .mockResolvedValueOnce(createMockAlertsResponse([evt789], 1))
        .mockResolvedValueOnce(createMockAcknowledgeResponse(true))

      const { result } = renderHook(() =>
        useSafetyAlerts({ apiUrl: MOCK_API_URL, autoFetch: true })
      )

      await waitFor(() => {
        expect(result.current.alerts).toHaveLength(1)
      })

      // When: acknowledge('evt-789') is called and API returns success
      let ackResult: boolean = false
      await act(async () => {
        ackResult = await result.current.acknowledge('evt-789')
      })

      // Then: The function returns true
      expect(ackResult).toBe(true)

      // And: The alert with id 'evt-789' has acknowledged: true and acknowledged_at is set
      const alert = result.current.alerts.find(a => a.id === 'evt-789')
      expect(alert?.acknowledged).toBe(true)
      expect(alert?.acknowledged_at).toBeTruthy()

      // And: activeCount is decremented by 1
      expect(result.current.activeCount).toBe(0)
    })

    it('UNIT-010: acknowledge does not use credentials include', async () => {
      // Given: A user is authenticated with a valid session
      mockGetSession.mockResolvedValue(createMockSession('mock-token-abc'))
      mockFetch
        .mockResolvedValueOnce(createMockAlertsResponse())
        .mockResolvedValueOnce(createMockAcknowledgeResponse())

      const { result } = renderHook(() =>
        useSafetyAlerts({ apiUrl: MOCK_API_URL, autoFetch: true })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // When: acknowledge('evt-any') is called
      await act(async () => {
        await result.current.acknowledge('evt-any')
      })

      // Then: The POST fetch options do NOT contain a credentials property
      const acknowledgeCalls = mockFetch.mock.calls.filter(
        ([url]: [string]) => url.includes('/api/safety/acknowledge/')
      )
      expect(acknowledgeCalls).toHaveLength(1)
      const [, ackOptions] = acknowledgeCalls[0]
      expect(ackOptions).not.toHaveProperty('credentials')
    })
  })

  // =========================================================================
  // AC4: Consistency With Other Hooks
  // =========================================================================
  describe('AC4: Consistency With Other Hooks', () => {
    it('UNIT-011: fetchAlerts calls createClient and getSession before fetch', async () => {
      // Given: A user is authenticated
      mockGetSession.mockResolvedValue(createMockSession('mock-token-abc'))
      mockFetch.mockImplementation((..._args: unknown[]) => {
        callOrder.push('fetch')
        return Promise.resolve(createMockAlertsResponse())
      })

      // When: fetchAlerts is invoked
      const { result } = renderHook(() =>
        useSafetyAlerts({ apiUrl: MOCK_API_URL, autoFetch: true })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: Call order is createClient -> getSession -> fetch
      expect(callOrder).toContain('createClient')
      expect(callOrder).toContain('getSession')
      expect(callOrder).toContain('fetch')

      const createIdx = callOrder.indexOf('createClient')
      const getSessionIdx = callOrder.indexOf('getSession')
      const fetchIdx = callOrder.indexOf('fetch')
      expect(createIdx).toBeLessThan(getSessionIdx)
      expect(getSessionIdx).toBeLessThan(fetchIdx)
    })

    it('UNIT-012: acknowledge calls createClient and getSession before fetch', async () => {
      // Given: A user is authenticated
      mockGetSession.mockResolvedValue(createMockSession('mock-token-abc'))
      mockFetch.mockImplementation((..._args: unknown[]) => {
        callOrder.push('fetch')
        return Promise.resolve(createMockAlertsResponse())
      })

      const { result } = renderHook(() =>
        useSafetyAlerts({ apiUrl: MOCK_API_URL, autoFetch: true })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Reset tracking for acknowledge call
      callOrder.length = 0
      mockFetch.mockImplementation((..._args: unknown[]) => {
        callOrder.push('fetch')
        return Promise.resolve(createMockAcknowledgeResponse())
      })

      // When: acknowledge('evt-id') is invoked
      await act(async () => {
        await result.current.acknowledge('evt-id')
      })

      // Then: Call order is createClient -> getSession -> fetch
      expect(callOrder).toContain('createClient')
      expect(callOrder).toContain('getSession')
      expect(callOrder).toContain('fetch')

      const createIdx = callOrder.indexOf('createClient')
      const getSessionIdx = callOrder.indexOf('getSession')
      const fetchIdx = callOrder.indexOf('fetch')
      expect(createIdx).toBeLessThan(getSessionIdx)
      expect(getSessionIdx).toBeLessThan(fetchIdx)
    })

    it('UNIT-013: No credentials include in any fetch call from hook', async () => {
      // Given: The hook is mounted and authenticated
      mockGetSession.mockResolvedValue(createMockSession('mock-token-abc'))
      mockFetch
        .mockResolvedValueOnce(createMockAlertsResponse())
        .mockResolvedValueOnce(createMockAcknowledgeResponse())

      const { result } = renderHook(() =>
        useSafetyAlerts({ apiUrl: MOCK_API_URL, autoFetch: true })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // When: Both fetchAlerts and acknowledge have been invoked
      await act(async () => {
        await result.current.acknowledge('evt-test')
      })

      // Then: No call to global.fetch includes credentials: 'include'
      for (const call of mockFetch.mock.calls) {
        const options = call[1] ?? {}
        expect(options).not.toHaveProperty('credentials')
      }
    })

    it('UNIT-014: Public API (UseSafetyAlertsReturn) is unchanged', async () => {
      // Given: The useSafetyAlerts hook is rendered
      mockGetSession.mockResolvedValue(createMockSession('mock-token-abc'))
      mockFetch.mockResolvedValue(createMockAlertsResponse())

      // When: The hook returns its result
      const { result } = renderHook(() =>
        useSafetyAlerts({ apiUrl: MOCK_API_URL, autoFetch: false })
      )

      // Then: The return object contains exactly the expected keys
      const keys = Object.keys(result.current).sort()
      const expectedKeys = [
        'acknowledge',
        'activeCount',
        'alerts',
        'error',
        'hasActiveAlerts',
        'isLoading',
        'lastUpdated',
        'refetch',
      ].sort()
      expect(keys).toEqual(expectedKeys)

      // And: refetch is a function, acknowledge is a function
      expect(typeof result.current.refetch).toBe('function')
      expect(typeof result.current.acknowledge).toBe('function')
    })

    it('UNIT-015: useSafetyAlertCount public API is unchanged', async () => {
      // Given: The useSafetyAlertCount hook is rendered
      mockGetSession.mockResolvedValue(createMockSession('mock-token-abc'))
      mockFetch.mockResolvedValue(createMockAlertsResponse())

      // When: The hook returns its result
      const { result } = renderHook(() =>
        useSafetyAlertCount({ apiUrl: MOCK_API_URL, autoFetch: false })
      )

      // Then: The return object contains exactly: count, isLoading, refetch
      const keys = Object.keys(result.current).sort()
      expect(keys).toEqual(['count', 'isLoading', 'refetch'].sort())
    })
  })

  // =========================================================================
  // Edge Cases
  // =========================================================================
  describe('Edge Cases', () => {
    it('UNIT-016: fetchAlerts handles network error during getSession', async () => {
      // Given: getSession() throws a network error
      mockGetSession.mockRejectedValue(new Error('Network error'))

      // When: fetchAlerts is invoked
      const { result } = renderHook(() =>
        useSafetyAlerts({ apiUrl: MOCK_API_URL, autoFetch: true })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: The error is caught, state.error is set
      expect(result.current.error).toBeTruthy()
      expect(result.current.isLoading).toBe(false)

      // And: global.fetch is NOT called
      expect(mockFetch).not.toHaveBeenCalled()
    })

    it('UNIT-017: acknowledge handles network error during getSession', async () => {
      // Given: Initial fetch succeeds, then getSession throws on acknowledge
      mockGetSession
        .mockResolvedValueOnce(createMockSession('mock-token-abc'))
        .mockRejectedValueOnce(new Error('Network error'))
      mockFetch.mockResolvedValue(createMockAlertsResponse())

      const { result } = renderHook(() =>
        useSafetyAlerts({ apiUrl: MOCK_API_URL, autoFetch: true })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      mockFetch.mockClear()

      // When: acknowledge('evt-id') is invoked
      let ackResult: boolean = true
      await act(async () => {
        ackResult = await result.current.acknowledge('evt-id')
      })

      // Then: The function returns false
      expect(ackResult).toBe(false)

      // And: global.fetch is NOT called
      expect(mockFetch).not.toHaveBeenCalled()
    })

    it('UNIT-018: Polling continues to work with auth pattern', async () => {
      // Given: The hook is mounted with pollingInterval: 500 and user is authenticated
      mockGetSession.mockResolvedValue(createMockSession('mock-token-abc'))
      mockFetch.mockResolvedValue(createMockAlertsResponse())

      const { result } = renderHook(() =>
        useSafetyAlerts({ apiUrl: MOCK_API_URL, autoFetch: true, pollingInterval: 500 })
      )

      // Wait for initial fetch to complete
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Record initial fetch calls
      const initialCallCount = mockFetch.mock.calls.length

      // When: polling interval elapses (wait for the real interval to fire)
      await waitFor(
        () => {
          expect(mockFetch.mock.calls.length).toBeGreaterThan(initialCallCount)
        },
        { timeout: 3000 }
      )

      // Then: fetchAlerts is called again with proper Bearer token auth
      const latestCall = mockFetch.mock.calls[mockFetch.mock.calls.length - 1]
      const [, latestOptions] = latestCall
      expect(latestOptions.headers).toHaveProperty('Authorization', 'Bearer mock-token-abc')
      expect(latestOptions).not.toHaveProperty('credentials')
    })

    it('UNIT-019: fetchAlerts handles API 500 error with Bearer token', async () => {
      // Given: User is authenticated, but API returns 500
      mockGetSession.mockResolvedValue(createMockSession('mock-token-abc'))
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => ({ error: 'Internal Server Error' }),
      })

      // When: fetchAlerts completes
      const { result } = renderHook(() =>
        useSafetyAlerts({ apiUrl: MOCK_API_URL, autoFetch: true })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: state.error contains the error message, isLoading is false
      expect(result.current.error).toContain('500')
      expect(result.current.isLoading).toBe(false)
    })

    it('UNIT-020: Content-Type header is preserved alongside Authorization', async () => {
      // Given: User is authenticated
      mockGetSession.mockResolvedValue(createMockSession('mock-token-abc'))
      mockFetch
        .mockResolvedValueOnce(createMockAlertsResponse())
        .mockResolvedValueOnce(createMockAcknowledgeResponse())

      const { result } = renderHook(() =>
        useSafetyAlerts({ apiUrl: MOCK_API_URL, autoFetch: true })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // When: fetchAlerts makes a fetch call
      // Then: Both Content-Type and Authorization are present in the GET request
      const getCall = mockFetch.mock.calls.find(
        ([url]: [string]) => url.includes('/api/safety/active')
      )
      expect(getCall).toBeDefined()
      expect(getCall![1].headers).toHaveProperty('Content-Type', 'application/json')
      expect(getCall![1].headers).toHaveProperty('Authorization', 'Bearer mock-token-abc')

      // When: acknowledge makes a fetch call
      await act(async () => {
        await result.current.acknowledge('evt-any')
      })

      // Then: Both headers are present in the POST request
      const postCall = mockFetch.mock.calls.find(
        ([url]: [string]) => url.includes('/api/safety/acknowledge/')
      )
      expect(postCall).toBeDefined()
      expect(postCall![1].headers).toHaveProperty('Content-Type', 'application/json')
      expect(postCall![1].headers).toHaveProperty('Authorization', 'Bearer mock-token-abc')
    })
  })
})
