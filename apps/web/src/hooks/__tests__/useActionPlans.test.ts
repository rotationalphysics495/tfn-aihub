/**
 * useActionPlans Hook Tests (Story 16.3: Create Action Plan from Follow-Up)
 *
 * TDD tests — these MUST FAIL until the useActionPlans hook is implemented.
 * Tests cover createActionPlan() API call construction, getLinkedActionPlan()
 * querying by source_followup_id, and error/auth handling.
 *
 * @see Story 16.3 - Create Action Plan from Follow-Up
 * @see AC #2 - Linked Action Plan Visible on Follow-Up Detail
 * @see AC #4 - Action Plan Created via POST with Required Fields
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

const createMockSession = (accessToken: string | null = 'mock-token-abc') => ({
  data: {
    session: accessToken !== null
      ? { access_token: accessToken, user: { id: 'user-uuid-owner' } }
      : null,
  },
})

interface CreateActionPlanPayload {
  title: string
  description: string
  category: string
  priority: string
  due_date: string
  root_cause: string
  source_followup_id: string
  asset_id: string | null
  corrective_action?: string
  preventive_action?: string
}

const createMockPayload = (
  overrides: Partial<CreateActionPlanPayload> = {}
): CreateActionPlanPayload => ({
  title: 'Action Plan: Fix valve leak',
  description: 'Investigate pressure anomaly on main valve. Root cause is worn bearing.',
  category: 'corrective',
  priority: 'high',
  due_date: '2026-03-01',
  root_cause: 'Worn bearing on pump shaft',
  source_followup_id: 'fu-123',
  asset_id: 'asset-uuid-123',
  ...overrides,
})

const createMockCreateResponse = (overrides: Record<string, unknown> = {}) => ({
  ok: true,
  status: 201,
  json: async () => ({
    id: 'ap-new-uuid',
    title: 'Action Plan: Fix valve leak',
    status: 'open',
    category: 'corrective',
    priority: 'high',
    source_followup_id: 'fu-123',
    ...overrides,
  }),
})

const createMockLinkedPlanResponse = (
  plans: Record<string, unknown>[] = []
) => ({
  ok: true,
  status: 200,
  json: async () => ({
    items: plans,
    total_count: plans.length,
  }),
})

const createMockErrorResponse = (status: number, detail: string = `Error ${status}`) => ({
  ok: false,
  status,
  json: async () => ({ detail }),
})

// ---------------------------------------------------------------------------
// Import hook AFTER mocks are set up
// ---------------------------------------------------------------------------

// The hook does not exist yet — this import will fail until it's created.
import { useActionPlans } from '../useActionPlans'

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: useActionPlans Hook (Story 16.3)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockReset()
    mockGetSession.mockReset()

    // Default: authenticated session
    mockGetSession.mockResolvedValue(createMockSession('mock-token-abc'))
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // =========================================================================
  // AC4: createActionPlan API call
  // =========================================================================
  describe('AC4: createActionPlan constructs correct API call', () => {
    it('16-3-create-action-plan-from-followup-UNIT-019: createActionPlan hook function constructs correct API call', async () => {
      // Given: The useActionPlans hook is initialized with a valid session
      mockFetch.mockResolvedValue(createMockCreateResponse())

      const { result } = renderHook(() =>
        useActionPlans({ apiUrl: MOCK_API_URL })
      )

      const payload = createMockPayload()

      // When: createActionPlan() is called with a CreateActionPlanRequest payload
      await act(async () => {
        await result.current.createActionPlan(payload)
      })

      // Then: fetch is called with method='POST'
      expect(mockFetch).toHaveBeenCalled()
      const postCall = mockFetch.mock.calls.find(
        (call: [string, RequestInit]) => call[1]?.method === 'POST'
      )
      expect(postCall).toBeTruthy()

      const [url, options] = postCall!

      // And: URL is ${apiUrl}/api/v1/action-plans
      expect(url).toBe(`${MOCK_API_URL}/api/v1/action-plans`)

      // And: Headers include Authorization and Content-Type
      expect(options.headers).toHaveProperty('Authorization', 'Bearer mock-token-abc')
      expect(options.headers).toHaveProperty('Content-Type', 'application/json')

      // And: The body is JSON-stringified payload
      const body = JSON.parse(options.body as string)
      expect(body.title).toBe('Action Plan: Fix valve leak')
      expect(body.category).toBe('corrective')
      expect(body.priority).toBe('high')
      expect(body.due_date).toBe('2026-03-01')
      expect(body.source_followup_id).toBe('fu-123')
      expect(body.asset_id).toBe('asset-uuid-123')
      expect(body.root_cause).toBe('Worn bearing on pump shaft')

      // And: status and owner_id fields are NOT included in body
      expect(body.status).toBeUndefined()
      expect(body.owner_id).toBeUndefined()
    })
  })

  // =========================================================================
  // AC2: getLinkedActionPlan queries by source_followup_id
  // =========================================================================
  describe('AC2: getLinkedActionPlan queries by source_followup_id', () => {
    it('16-3-create-action-plan-from-followup-UNIT-009: getLinkedActionPlan queries action_plans by source_followup_id', async () => {
      // Given: The useActionPlans hook is initialized
      const mockPlan = {
        id: 'ap-456',
        title: 'Action Plan: Fix valve leak',
        status: 'open',
        source_followup_id: 'fu-123',
      }

      mockFetch.mockResolvedValue(createMockLinkedPlanResponse([mockPlan]))

      const { result } = renderHook(() =>
        useActionPlans({ apiUrl: MOCK_API_URL })
      )

      // When: getLinkedActionPlan('fu-123') is called
      let linkedPlan: Record<string, unknown> | null = null
      await act(async () => {
        linkedPlan = await result.current.getLinkedActionPlan('fu-123')
      })

      // Then: A fetch request is made to GET /api/v1/action-plans with
      //       query parameter source_followup_id=fu-123
      expect(mockFetch).toHaveBeenCalled()
      const getCall = mockFetch.mock.calls.find(
        (call: [string, RequestInit]) =>
          (call[0] as string).includes('/api/v1/action-plans') &&
          (call[0] as string).includes('source_followup_id=fu-123')
      )
      expect(getCall).toBeTruthy()

      // And: The first matching result is returned
      expect(linkedPlan).toBeTruthy()
      expect(linkedPlan!.id).toBe('ap-456')
      expect(linkedPlan!.title).toBe('Action Plan: Fix valve leak')
    })

    it('16-3-create-action-plan-from-followup-UNIT-010: getLinkedActionPlan returns null when no linked plan exists', async () => {
      // Given: The useActionPlans hook is initialized
      // And: No action plan has source_followup_id='fu-no-plan'
      mockFetch.mockResolvedValue(createMockLinkedPlanResponse([]))

      const { result } = renderHook(() =>
        useActionPlans({ apiUrl: MOCK_API_URL })
      )

      // When: getLinkedActionPlan('fu-no-plan') is called
      let linkedPlan: Record<string, unknown> | null = null
      await act(async () => {
        linkedPlan = await result.current.getLinkedActionPlan('fu-no-plan')
      })

      // Then: The function returns null
      expect(linkedPlan).toBeNull()
    })
  })

  // =========================================================================
  // Error Handling
  // =========================================================================
  describe('Error Handling', () => {
    it('createActionPlan handles auth error when no session exists', async () => {
      // Given: No Supabase session
      mockGetSession.mockResolvedValue(createMockSession(null))

      const { result } = renderHook(() =>
        useActionPlans({ apiUrl: MOCK_API_URL })
      )

      // When: createActionPlan is called
      // Then: An error is returned or thrown
      let error: unknown = null
      await act(async () => {
        try {
          await result.current.createActionPlan(createMockPayload())
        } catch (e) {
          error = e
        }
      })

      // Either throws or returns error state
      const hasError = error !== null || result.current.error !== null
      expect(hasError).toBe(true)
    })

    it('getLinkedActionPlan handles API failure gracefully', async () => {
      // Given: API returns error
      mockFetch.mockResolvedValue(createMockErrorResponse(500))

      const { result } = renderHook(() =>
        useActionPlans({ apiUrl: MOCK_API_URL })
      )

      // When: getLinkedActionPlan is called
      let linkedPlan: unknown = 'not-called'
      await act(async () => {
        linkedPlan = await result.current.getLinkedActionPlan('fu-123')
      })

      // Then: Returns null (fails open, not closed)
      expect(linkedPlan).toBeNull()
    })
  })
})
