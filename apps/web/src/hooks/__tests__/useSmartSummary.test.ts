/**
 * useSmartSummary Hook Tests (Story 17.2: Smart Summary On-Demand Generation)
 *
 * Tests the autoGenerate option, generate() method for manual on-demand generation,
 * and canGenerate/hasSummary computed booleans.
 *
 * @see Story 17.2 - Smart Summary On-Demand Generation for Historical Dates
 * @see AC #1 - Historical date with no summary shows generation prompt
 * @see AC #2 - Generate button triggers API, shows loading, saves result
 * @see AC #5 - Error handling with retry
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

const createMockSmartSummary = (overrides: Record<string, unknown> = {}) => ({
  id: 'summary-001',
  date: '2026-02-10',
  summary_text: 'Production ran at 92% OEE. No safety incidents.',
  citations: [
    {
      metric_name: 'OEE',
      metric_value: '92%',
      source_table: 'daily_summaries',
    },
  ],
  model_used: 'gpt-4o',
  prompt_tokens: 500,
  completion_tokens: 200,
  generation_duration_ms: 3000,
  is_fallback: false,
  created_at: '2026-02-10T08:00:00Z',
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

function getYesterday(): string {
  const d = new Date()
  d.setDate(d.getDate() - 1)
  return d.toISOString().split('T')[0]
}

// ---------------------------------------------------------------------------
// Import hook AFTER mocks are set up
// ---------------------------------------------------------------------------

import { useSmartSummary } from '../useSmartSummary'

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: useSmartSummary Hook (Story 17.2)', () => {
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
  // Auth and Fetching
  // =========================================================================
  describe('Auth and data fetching', () => {
    it('Hook fetches with Bearer token auth on mount when autoFetch=true', async () => {
      mockFetch.mockResolvedValue(
        createMockFetchResponse(200, createMockSmartSummary())
      )

      const { result } = renderHook(() =>
        useSmartSummary({ apiUrl: MOCK_API_URL, autoFetch: true })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(mockFetch).toHaveBeenCalled()
      const [, options] = mockFetch.mock.calls[0]
      expect(options.headers).toHaveProperty('Authorization', 'Bearer mock-token-123')
    })

    it('Hook returns hasSummary=true when GET returns 200 with data', async () => {
      mockFetch.mockResolvedValue(
        createMockFetchResponse(200, createMockSmartSummary())
      )

      const { result } = renderHook(() =>
        useSmartSummary({ apiUrl: MOCK_API_URL, autoFetch: true })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.hasSummary).toBe(true)
      expect(result.current.data).toBeTruthy()
      expect(result.current.data!.summary_text).toContain('92% OEE')
    })
  })

  // =========================================================================
  // autoGenerate behavior
  // =========================================================================
  describe('autoGenerate behavior', () => {
    it('Hook auto-generates on 404 when autoGenerate is not set (default true behavior preserved)', async () => {
      const generatedSummary = createMockSmartSummary({ id: 'generated-001' })

      // First call (GET) returns 404, second call (POST generate) returns 201
      mockFetch
        .mockResolvedValueOnce(createMockFetchResponse(404, { detail: 'Not found' }))
        .mockResolvedValueOnce(createMockFetchResponse(201, generatedSummary))

      const { result } = renderHook(() =>
        useSmartSummary({ apiUrl: MOCK_API_URL, autoFetch: true })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
        expect(result.current.isGenerating).toBe(false)
      })

      // Should have made 2 fetch calls: GET (404) + POST (generate)
      expect(mockFetch).toHaveBeenCalledTimes(2)

      // Second call should be POST to /api/summaries/generate
      const [postUrl, postOptions] = mockFetch.mock.calls[1]
      expect(postUrl).toContain('/api/summaries/generate')
      expect(postOptions.method).toBe('POST')

      // Should have the generated summary
      expect(result.current.hasSummary).toBe(true)
      expect(result.current.data?.id).toBe('generated-001')
    })

    it('Hook does NOT auto-generate on 404 when autoGenerate=false — returns hasSummary=false canGenerate=true', async () => {
      // GET returns 404
      mockFetch.mockResolvedValueOnce(
        createMockFetchResponse(404, { detail: 'Not found' })
      )

      const { result } = renderHook(() =>
        useSmartSummary({
          apiUrl: MOCK_API_URL,
          autoFetch: true,
          reportDate: '2026-01-15',
          autoGenerate: false,
        })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Should have made only 1 fetch call (GET) — no POST auto-generation
      expect(mockFetch).toHaveBeenCalledTimes(1)
      const [url] = mockFetch.mock.calls[0]
      expect(url).toContain('/api/summaries/smart/2026-01-15')

      // Should indicate no summary but generation is available
      expect(result.current.hasSummary).toBe(false)
      expect(result.current.canGenerate).toBe(true)
      expect(result.current.data).toBeNull()
      expect(result.current.error).toBeNull()
    })
  })

  // =========================================================================
  // generate() method
  // =========================================================================
  describe('generate() method', () => {
    it('generate() calls POST /api/summaries/generate with correct target_date and headers', async () => {
      // Initial fetch returns 404, autoGenerate=false
      mockFetch.mockResolvedValueOnce(
        createMockFetchResponse(404, { detail: 'Not found' })
      )

      const { result } = renderHook(() =>
        useSmartSummary({
          apiUrl: MOCK_API_URL,
          autoFetch: true,
          reportDate: '2026-01-15',
          autoGenerate: false,
        })
      )

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Set up mock for generate call
      const generatedSummary = createMockSmartSummary({ id: 'manual-gen-001', date: '2026-01-15' })
      mockFetch.mockResolvedValueOnce(
        createMockFetchResponse(201, generatedSummary)
      )

      // Call generate()
      await act(async () => {
        await result.current.generate()
      })

      // Verify the POST call
      const generateCall = mockFetch.mock.calls[1] // second call after the initial GET
      const [postUrl, postOptions] = generateCall
      expect(postUrl).toBe(`${MOCK_API_URL}/api/summaries/generate`)
      expect(postOptions.method).toBe('POST')
      expect(postOptions.headers).toHaveProperty('Authorization', 'Bearer mock-token-123')

      const body = JSON.parse(postOptions.body)
      expect(body.target_date).toBe('2026-01-15')
      expect(body.regenerate).toBe(false)
    })

    it('generate() updates state with returned summary on success', async () => {
      // Initial fetch returns 404, autoGenerate=false
      mockFetch.mockResolvedValueOnce(
        createMockFetchResponse(404, { detail: 'Not found' })
      )

      const { result } = renderHook(() =>
        useSmartSummary({
          apiUrl: MOCK_API_URL,
          autoFetch: true,
          reportDate: '2026-01-15',
          autoGenerate: false,
        })
      )

      await waitFor(() => {
        expect(result.current.canGenerate).toBe(true)
      })

      // Set up successful generate response
      const generatedSummary = createMockSmartSummary({ id: 'manual-gen-001' })
      mockFetch.mockResolvedValueOnce(
        createMockFetchResponse(201, generatedSummary)
      )

      await act(async () => {
        await result.current.generate()
      })

      // State should now have the summary
      expect(result.current.hasSummary).toBe(true)
      expect(result.current.canGenerate).toBe(false)
      expect(result.current.data?.id).toBe('manual-gen-001')
      expect(result.current.isGenerating).toBe(false)
      expect(result.current.error).toBeNull()
    })

    it('generate() sets error state on failure with canGenerate remaining true for retry', async () => {
      // Initial fetch returns 404, autoGenerate=false
      mockFetch.mockResolvedValueOnce(
        createMockFetchResponse(404, { detail: 'Not found' })
      )

      const { result } = renderHook(() =>
        useSmartSummary({
          apiUrl: MOCK_API_URL,
          autoFetch: true,
          reportDate: '2026-01-15',
          autoGenerate: false,
        })
      )

      await waitFor(() => {
        expect(result.current.canGenerate).toBe(true)
      })

      // Set up failed generate response
      mockFetch.mockResolvedValueOnce(
        createMockFetchResponse(500, { detail: 'Internal server error' })
      )

      await act(async () => {
        await result.current.generate()
      })

      // Should have error but still be able to retry
      expect(result.current.error).toBeTruthy()
      expect(result.current.isGenerating).toBe(false)
      expect(result.current.hasSummary).toBe(false)
      // canGenerate should still be true (no data, not loading, not generating)
      expect(result.current.canGenerate).toBe(true)
    })

    it('generate() handles network errors gracefully', async () => {
      // Initial fetch returns 404, autoGenerate=false
      mockFetch.mockResolvedValueOnce(
        createMockFetchResponse(404, { detail: 'Not found' })
      )

      const { result } = renderHook(() =>
        useSmartSummary({
          apiUrl: MOCK_API_URL,
          autoFetch: true,
          reportDate: '2026-01-15',
          autoGenerate: false,
        })
      )

      await waitFor(() => {
        expect(result.current.canGenerate).toBe(true)
      })

      // Set up network failure
      mockFetch.mockRejectedValueOnce(new TypeError('Failed to fetch'))

      await act(async () => {
        await result.current.generate()
      })

      expect(result.current.error).toBeTruthy()
      expect(result.current.isGenerating).toBe(false)
    })

    it('generate() handles expired session', async () => {
      // Initial fetch returns 404, autoGenerate=false
      mockFetch.mockResolvedValueOnce(
        createMockFetchResponse(404, { detail: 'Not found' })
      )

      const { result } = renderHook(() =>
        useSmartSummary({
          apiUrl: MOCK_API_URL,
          autoFetch: true,
          reportDate: '2026-01-15',
          autoGenerate: false,
        })
      )

      await waitFor(() => {
        expect(result.current.canGenerate).toBe(true)
      })

      // Session expired before generate call
      mockGetSession.mockResolvedValue({ data: { session: null } })

      await act(async () => {
        await result.current.generate()
      })

      expect(result.current.error).toMatch(/session expired/i)
      expect(result.current.isGenerating).toBe(false)
    })
  })

  // =========================================================================
  // regenerate() still works
  // =========================================================================
  describe('regenerate() existing behavior', () => {
    it('regenerate() calls GET with ?regenerate=true', async () => {
      // Initial fetch returns 200 with cached summary
      mockFetch.mockResolvedValueOnce(
        createMockFetchResponse(200, createMockSmartSummary())
      )

      const { result } = renderHook(() =>
        useSmartSummary({
          apiUrl: MOCK_API_URL,
          autoFetch: true,
          reportDate: '2026-02-10',
        })
      )

      await waitFor(() => {
        expect(result.current.hasSummary).toBe(true)
      })

      // Set up regenerate response
      const regeneratedSummary = createMockSmartSummary({ id: 'regen-001' })
      mockFetch.mockResolvedValueOnce(
        createMockFetchResponse(200, regeneratedSummary)
      )

      await act(async () => {
        await result.current.regenerate()
      })

      // Second fetch call should be GET with ?regenerate=true
      const [url, options] = mockFetch.mock.calls[1]
      expect(url).toContain('/api/summaries/smart/2026-02-10?regenerate=true')
      expect(options.method).toBe('GET')
      expect(result.current.data?.id).toBe('regen-001')
    })
  })

  // =========================================================================
  // Unmount safety
  // =========================================================================
  describe('Unmount safety', () => {
    it('Hook does not update state after unmount', async () => {
      let resolvePromise: (value: unknown) => void
      const delayedFetch = new Promise((resolve) => {
        resolvePromise = resolve
      })
      mockFetch.mockReturnValue(delayedFetch)

      const { result, unmount } = renderHook(() =>
        useSmartSummary({ apiUrl: MOCK_API_URL, autoFetch: true })
      )

      expect(result.current.isLoading).toBe(true)

      unmount()

      await act(async () => {
        resolvePromise!(
          createMockFetchResponse(200, createMockSmartSummary())
        )
      })

      // No error thrown, and state didn't update after unmount
      expect(result.current.isLoading).toBe(true)
    })
  })
})
