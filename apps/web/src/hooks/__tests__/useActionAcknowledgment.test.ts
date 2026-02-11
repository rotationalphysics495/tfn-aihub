/**
 * useActionAcknowledgment Hook Tests (Story 13.2: Action Acknowledgment UI)
 *
 * TDD tests — these MUST FAIL until the useActionAcknowledgment hook is implemented.
 * Tests cover optimistic state management, API calls with Bearer token auth,
 * rollback on failure, deduplication, and initial state from fetched data.
 *
 * @see Story 13.2 - Action Acknowledgment UI
 * @see AC #1 - Unacknowledged initial state
 * @see AC #2 - Optimistic acknowledge with rollback
 * @see AC #3 - Persisted acknowledged state from database
 */

import { renderHook, act, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockGetSession = vi.fn()
vi.mock('@/lib/supabase/client', () => ({
  createClient: () => ({
    auth: { getSession: mockGetSession },
  }),
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

interface MockActionItem {
  id: string
  acknowledgment: {
    user_id: string
    acknowledged_at: string
    note: string | null
  } | null
}

const createMockActionItem = (
  id: string,
  acknowledgment: MockActionItem['acknowledgment'] = null
): MockActionItem => ({
  id,
  acknowledgment,
})

const createMockAcknowledgeResponse = (actionId: string) => ({
  ok: true,
  status: 200,
  json: async () => ({
    id: `ack-${actionId}`,
    action_item_id: actionId,
    user_id: 'u1',
    acknowledged_at: new Date().toISOString(),
    note: null,
    report_date: '2026-02-11',
  }),
})

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
import { useActionAcknowledgment } from '../useActionAcknowledgment'

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: useActionAcknowledgment Hook (Story 13.2)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockReset()
    mockGetSession.mockReset()

    // Default: authenticated session
    mockGetSession.mockResolvedValue(createMockSession('mock-token-123'))
    // Default: successful acknowledge response
    mockFetch.mockImplementation(async (_url: string) => {
      const actionId = _url.split('/actions/')[1]?.split('/')[0] || 'unknown'
      return createMockAcknowledgeResponse(actionId)
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // =========================================================================
  // AC1: Initial State
  // =========================================================================
  describe('AC1: Initial State', () => {
    it('UNIT-005: Hook initializes all items as unacknowledged when no prior acknowledgments exist', () => {
      // Given: The hook receives a list of action items where all have acknowledgment: null
      const items = [
        createMockActionItem('action-1'),
        createMockActionItem('action-2'),
        createMockActionItem('action-3'),
      ]

      // When: The hook initializes
      const { result } = renderHook(() =>
        useActionAcknowledgment({ items, apiUrl: MOCK_API_URL })
      )

      // Then: isAcknowledged returns false for every item
      expect(result.current.isAcknowledged('action-1')).toBe(false)
      expect(result.current.isAcknowledged('action-2')).toBe(false)
      expect(result.current.isAcknowledged('action-3')).toBe(false)

      // And: acknowledgedCount is 0 and totalCount equals the number of items
      expect(result.current.acknowledgedCount).toBe(0)
      expect(result.current.totalCount).toBe(3)
    })
  })

  // =========================================================================
  // AC2: Optimistic Acknowledge
  // =========================================================================
  describe('AC2: Optimistic Acknowledge', () => {
    it('UNIT-007: Clicking acknowledge triggers optimistic UI update immediately', async () => {
      // Given: The hook is initialized with unacknowledged items
      let resolveApi: () => void
      const apiPromise = new Promise<void>((resolve) => {
        resolveApi = resolve
      })
      mockFetch.mockImplementation(async () => {
        await apiPromise
        return createMockAcknowledgeResponse('action-1')
      })

      const items = [createMockActionItem('action-1')]
      const { result } = renderHook(() =>
        useActionAcknowledgment({ items, apiUrl: MOCK_API_URL })
      )

      // When: acknowledge is called (API has NOT resolved yet)
      act(() => {
        result.current.acknowledge('action-1')
      })

      // Then: isAcknowledged returns true IMMEDIATELY (before API resolves)
      expect(result.current.isAcknowledged('action-1')).toBe(true)

      // And: getAcknowledgment returns an object with acknowledged_at timestamp
      const ack = result.current.getAcknowledgment('action-1')
      expect(ack).toBeTruthy()
      expect(ack!.acknowledged_at).toBeTruthy()

      // And: acknowledgedCount increments by 1
      expect(result.current.acknowledgedCount).toBe(1)

      // Clean up: resolve the API call
      resolveApi!()
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled()
      })
    })

    it('UNIT-008: Acknowledge calls POST API with correct endpoint and Bearer token', async () => {
      // Given: The hook has a valid Supabase session with access_token "mock-token-123"
      const items = [createMockActionItem('action-42')]
      const { result } = renderHook(() =>
        useActionAcknowledgment({ items, apiUrl: MOCK_API_URL })
      )

      // When: acknowledge("action-42") is called
      await act(async () => {
        await result.current.acknowledge('action-42')
      })

      // Then: fetch is called with correct URL, method, and headers
      expect(mockFetch).toHaveBeenCalled()
      const [url, options] = mockFetch.mock.calls[0]
      expect(url).toBe(`${MOCK_API_URL}/api/v1/actions/action-42/acknowledge`)
      expect(options.method).toBe('POST')
      expect(options.headers).toHaveProperty('Authorization', 'Bearer mock-token-123')
      expect(options.headers).toHaveProperty('Content-Type', 'application/json')
    })

    it('UNIT-012: Optimistic update rolls back on API failure', async () => {
      // Given: The hook has an unacknowledged item "action-1" and the API will return 500
      mockFetch.mockResolvedValue(createMockErrorResponse(500))

      const items = [createMockActionItem('action-1')]
      const { result } = renderHook(() =>
        useActionAcknowledgment({ items, apiUrl: MOCK_API_URL })
      )

      // When: acknowledge("action-1") is called and the API fails
      await act(async () => {
        await result.current.acknowledge('action-1')
      })

      // Then: The optimistic state is rolled back
      await waitFor(() => {
        expect(result.current.isAcknowledged('action-1')).toBe(false)
      })

      // And: acknowledgedCount returns to original value
      expect(result.current.acknowledgedCount).toBe(0)
    })

    it('UNIT-013: Error toast is shown when acknowledgment API fails', async () => {
      // Given: The hook has an unacknowledged item and the API returns an error
      mockFetch.mockResolvedValue(createMockErrorResponse(500))

      const mockOnError = vi.fn()
      const items = [createMockActionItem('action-1')]
      const { result } = renderHook(() =>
        useActionAcknowledgment({ items, apiUrl: MOCK_API_URL, onError: mockOnError })
      )

      // When: acknowledge is called and the API fails
      await act(async () => {
        await result.current.acknowledge('action-1')
      })

      // Then: The onError callback (or toast) is triggered with an error message
      await waitFor(() => {
        expect(mockOnError).toHaveBeenCalledWith(
          expect.stringMatching(/fail|error|unable/i)
        )
      })
    })

    it('UNIT-014: Clicking an already-acknowledged button does not send duplicate API call', async () => {
      // Given: The hook has item "action-1" already in acknowledged state
      const items = [
        createMockActionItem('action-1', {
          user_id: 'u1',
          acknowledged_at: '2026-02-11T08:30:00Z',
          note: null,
        }),
      ]
      const { result } = renderHook(() =>
        useActionAcknowledgment({ items, apiUrl: MOCK_API_URL })
      )

      // When: acknowledge("action-1") is called again
      await act(async () => {
        await result.current.acknowledge('action-1')
      })

      // Then: No API call is made (fetch call count does not increase)
      expect(mockFetch).not.toHaveBeenCalled()
    })

    it('UNIT-015: Rapid successive clicks on acknowledge button are debounced', async () => {
      // Given: The hook has an unacknowledged item with an in-flight request
      let resolveApi: () => void
      const apiPromise = new Promise<void>((resolve) => {
        resolveApi = resolve
      })
      mockFetch.mockImplementation(async () => {
        await apiPromise
        return createMockAcknowledgeResponse('action-1')
      })

      const items = [createMockActionItem('action-1')]
      const { result } = renderHook(() =>
        useActionAcknowledgment({ items, apiUrl: MOCK_API_URL })
      )

      // When: acknowledge("action-1") is called twice before the first completes
      act(() => {
        result.current.acknowledge('action-1')
      })
      act(() => {
        result.current.acknowledge('action-1')
      })

      // Then: Only one API call is made (not two)
      expect(mockFetch).toHaveBeenCalledTimes(1)

      // Clean up
      resolveApi!()
      await waitFor(() => {
        expect(result.current.isAcknowledged('action-1')).toBe(true)
      })
    })

    it('UNIT-016: Multiple items can be acknowledged in quick succession without stale closure issues', async () => {
      // Given: The hook has 3 unacknowledged items
      const items = [
        createMockActionItem('action-1'),
        createMockActionItem('action-2'),
        createMockActionItem('action-3'),
      ]
      const { result } = renderHook(() =>
        useActionAcknowledgment({ items, apiUrl: MOCK_API_URL })
      )

      // When: All three are acknowledged in rapid succession
      await act(async () => {
        result.current.acknowledge('action-1')
        result.current.acknowledge('action-2')
        result.current.acknowledge('action-3')
      })

      // Then: All three items are marked as acknowledged (no stale state overwrites)
      await waitFor(() => {
        expect(result.current.isAcknowledged('action-1')).toBe(true)
        expect(result.current.isAcknowledged('action-2')).toBe(true)
        expect(result.current.isAcknowledged('action-3')).toBe(true)
      })

      // And: acknowledgedCount equals 3
      expect(result.current.acknowledgedCount).toBe(3)

      // And: all 3 API calls are made
      expect(mockFetch).toHaveBeenCalledTimes(3)
    })

    it('UNIT-018: Acknowledgment request includes optional note in body', async () => {
      // Given: The hook is initialized
      const items = [createMockActionItem('action-1')]
      const { result } = renderHook(() =>
        useActionAcknowledgment({ items, apiUrl: MOCK_API_URL })
      )

      // When: acknowledge is called without a note
      await act(async () => {
        await result.current.acknowledge('action-1')
      })

      // Then: The POST body is valid JSON
      const [, options] = mockFetch.mock.calls[0]
      const body = JSON.parse(options.body)
      expect(body).toBeDefined()

      // And: When a note is provided, it should be included
      mockFetch.mockClear()
      const items2 = [createMockActionItem('action-2')]
      const { result: result2 } = renderHook(() =>
        useActionAcknowledgment({ items: items2, apiUrl: MOCK_API_URL })
      )

      await act(async () => {
        await result2.current.acknowledge('action-2', { note: 'Reviewed and addressed' })
      })

      const [, options2] = mockFetch.mock.calls[0]
      const body2 = JSON.parse(options2.body)
      expect(body2.note).toBe('Reviewed and addressed')
    })
  })

  // =========================================================================
  // AC3: Initial State from Database
  // =========================================================================
  describe('AC3: Initial State from Database', () => {
    it('UNIT-019: Hook initializes acknowledged state from action items data', () => {
      // Given: useDailyActions returns action items where some have non-null acknowledgment fields
      const items = [
        createMockActionItem('action-1', {
          user_id: 'u1',
          acknowledged_at: '2026-02-11T07:00:00Z',
          note: null,
        }),
        createMockActionItem('action-2', {
          user_id: 'u1',
          acknowledged_at: '2026-02-11T07:15:00Z',
          note: null,
        }),
        createMockActionItem('action-3'),
        createMockActionItem('action-4'),
        createMockActionItem('action-5'),
      ]

      // When: useActionAcknowledgment initializes from this data
      const { result } = renderHook(() =>
        useActionAcknowledgment({ items, apiUrl: MOCK_API_URL })
      )

      // Then: isAcknowledged returns true for the 2 acknowledged items
      expect(result.current.isAcknowledged('action-1')).toBe(true)
      expect(result.current.isAcknowledged('action-2')).toBe(true)

      // And: isAcknowledged returns false for the 3 unacknowledged items
      expect(result.current.isAcknowledged('action-3')).toBe(false)
      expect(result.current.isAcknowledged('action-4')).toBe(false)
      expect(result.current.isAcknowledged('action-5')).toBe(false)

      // And: acknowledgedCount is 2, totalCount is 5
      expect(result.current.acknowledgedCount).toBe(2)
      expect(result.current.totalCount).toBe(5)
    })
  })
})
