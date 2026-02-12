/**
 * useFollowUpMessages Hook Tests (Story 15.4: Message Thread UI)
 *
 * TDD tests — these MUST FAIL until the useFollowUpMessages hook is implemented.
 * Tests cover fetching messages from API with auth token, typed response,
 * loading state transitions, and markViewed functionality.
 *
 * @see Story 15.4 - Message Thread UI
 * @see AC #1 - Chronological message thread display
 * @see AC #2 - Unread indicator / markViewed
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

interface MockFollowUpMessage {
  id: string
  direction: 'outbound' | 'inbound'
  message_type: 'assignment' | 'response' | 'status_update' | 'escalation'
  sender_email: string
  subject: string | null
  body: string
  sent_at: string
}

const createMockMessage = (overrides: Partial<MockFollowUpMessage> = {}): MockFollowUpMessage => ({
  id: 'msg-default',
  direction: 'outbound',
  message_type: 'assignment',
  sender_email: 'manager@plant.com',
  subject: 'Follow-up: Replace bearing',
  body: 'Please inspect the bearing on Pump-101',
  sent_at: '2026-02-10T08:00:00Z',
  ...overrides,
})

const createMockMessagesResponse = (
  messages: MockFollowUpMessage[],
  overrides: Record<string, unknown> = {}
) => ({
  ok: true,
  status: 200,
  json: async () => ({
    followup_id: 'fu-123',
    action_summary: 'Replace bearing',
    assignee_name: 'John Smith',
    assignee_email: 'john@plant.com',
    status: 'in_progress',
    messages,
    has_unread: false,
    last_viewed_at: '2026-02-10T12:00:00Z',
    ...overrides,
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

// The hook does not exist yet — this import will fail until it's created.
import { useFollowUpMessages } from '../useFollowUpMessages'

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: useFollowUpMessages Hook (Story 15.4)', () => {
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
  // AC1: Fetch messages from API
  // =========================================================================
  describe('AC1: Fetch Messages from API', () => {
    it('15-4-message-thread-ui-INT-002: useFollowUpMessages hook fetches messages from API with auth token', async () => {
      // Given: A Supabase session exists with a valid access token,
      //        and useFollowUpMessages is called with followUpId="fu-123"
      const messages = [
        createMockMessage({
          id: 'msg-1',
          direction: 'outbound',
          message_type: 'assignment',
          sent_at: '2026-02-10T08:00:00Z',
        }),
        createMockMessage({
          id: 'msg-2',
          direction: 'inbound',
          message_type: 'response',
          sender_email: 'assignee@plant.com',
          body: 'Bearing replaced',
          sent_at: '2026-02-10T14:30:00Z',
        }),
      ]
      mockFetch.mockResolvedValue(createMockMessagesResponse(messages))

      // When: The hook initializes and fetches data
      const { result } = renderHook(() =>
        useFollowUpMessages({ followUpId: 'fu-123', apiUrl: MOCK_API_URL })
      )

      // Then: Loading transitions from true to false
      expect(result.current.isLoading).toBe(true)

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // And: A GET request is made to /api/v1/followups/fu-123/messages
      //      with Authorization: Bearer {token}
      expect(mockFetch).toHaveBeenCalled()
      const [url, options] = mockFetch.mock.calls[0]
      expect(url).toContain(`${MOCK_API_URL}/api/v1/followups/fu-123/messages`)
      expect(options.headers).toHaveProperty('Authorization', 'Bearer mock-token-123')

      // And: The hook returns the typed messages array
      expect(result.current.messages).toHaveLength(2)
      expect(result.current.messages[0].id).toBe('msg-1')
      expect(result.current.messages[0].direction).toBe('outbound')
      expect(result.current.messages[1].id).toBe('msg-2')
      expect(result.current.messages[1].direction).toBe('inbound')

      // And: The hook returns wrapper context fields
      expect(result.current.assignee_name).toBe('John Smith')
      expect(result.current.has_unread).toBe(false)
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
        useFollowUpMessages({ followUpId: 'fu-123', apiUrl: MOCK_API_URL })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: error state is set
      expect(result.current.error).toBeTruthy()
    })

    it('Hook handles 401 API error', async () => {
      // Given: API returns 401
      mockFetch.mockResolvedValue(createMockErrorResponse(401))

      // When: Hook is rendered
      const { result } = renderHook(() =>
        useFollowUpMessages({ followUpId: 'fu-123', apiUrl: MOCK_API_URL })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: error state is set
      expect(result.current.error).toBeTruthy()
    })

    it('Hook handles 500 API error', async () => {
      // Given: API returns 500
      mockFetch.mockResolvedValue(createMockErrorResponse(500))

      // When: Hook is rendered
      const { result } = renderHook(() =>
        useFollowUpMessages({ followUpId: 'fu-123', apiUrl: MOCK_API_URL })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Then: error state is set
      expect(result.current.error).toBeTruthy()
    })
  })

  // =========================================================================
  // markViewed functionality
  // =========================================================================
  describe('markViewed Functionality', () => {
    it('markViewed sends PATCH request to viewed endpoint', async () => {
      // Given: Hook loaded successfully
      const messages = [createMockMessage()]
      mockFetch.mockResolvedValueOnce(createMockMessagesResponse(messages))

      const { result } = renderHook(() =>
        useFollowUpMessages({ followUpId: 'fu-123', apiUrl: MOCK_API_URL })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // When: markViewed is called
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ success: true, last_viewed_at: '2026-02-11T12:00:00Z' }),
      })

      await act(async () => {
        await result.current.markViewed()
      })

      // Then: A PATCH request was made to the viewed endpoint
      const patchCall = mockFetch.mock.calls.find(
        (call: [string, RequestInit]) =>
          call[0].includes('/api/v1/followups/fu-123/viewed') &&
          call[1]?.method === 'PATCH'
      )
      expect(patchCall).toBeTruthy()
    })
  })
})
