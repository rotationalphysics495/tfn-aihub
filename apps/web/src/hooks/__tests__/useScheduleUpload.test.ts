/**
 * useScheduleUpload Hook Tests (Story 12.4: Schedule Upload UI)
 *
 * TDD tests — these MUST FAIL until the hook is implemented.
 * Follows the useSafetyAlerts / useDailyActions auth pattern.
 *
 * @see Story 12.4 - Schedule Upload UI
 * @see AC #1 - File upload to preview endpoint
 * @see AC #2 - Preview data returned
 * @see AC #3 - Confirm upload
 */

import { renderHook, act, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockGetSession = vi.fn()

vi.mock('@/lib/supabase/client', () => ({
  createClient: () => ({
    auth: {
      getSession: mockGetSession,
    },
  }),
}))

// Mock global.fetch
const mockFetch = vi.fn()
global.fetch = mockFetch

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const MOCK_API_URL = 'http://localhost:8000'

const createMockSession = (accessToken: string | null = 'mock-token') => ({
  data: { session: accessToken !== null ? { access_token: accessToken } : null },
})

const createMockFile = (name: string, size: number, type: string): File => {
  const file = new File(['x'.repeat(size)], name, { type })
  Object.defineProperty(file, 'size', { value: size })
  return file
}

const createMockPreviewRow = (overrides: Record<string, unknown> = {}) => ({
  row_number: 1,
  date: '2026-02-16',
  shift: 'Day',
  asset_name: 'Grinder 1',
  product_name: 'Dark Roast 12oz',
  scheduled_quantity: '500',
  asset_match_status: 'matched',
  asset_id: 'uuid-asset-1',
  suggestions: [],
  product_id: 'uuid-prod-1',
  is_new_product: false,
  errors: [],
  ...overrides,
})

const createMockPreviewResponse = (overrides: Record<string, unknown> = {}) => ({
  parsed_rows_count: 3,
  rows: [
    createMockPreviewRow({ row_number: 1 }),
    createMockPreviewRow({
      row_number: 2,
      asset_match_status: 'suggested',
      asset_id: null,
      suggestions: ['Grinder 2'],
    }),
    createMockPreviewRow({
      row_number: 3,
      errors: [{ row_number: 3, field: 'date', message: 'Invalid date format' }],
    }),
  ],
  has_errors: true,
  matched_assets: ['Grinder 1'],
  matched_products: ['Dark Roast 12oz'],
  new_products: [],
  ...overrides,
})

const createMockConfirmResponse = (overrides: Record<string, unknown> = {}) => ({
  rows_inserted: 3,
  products_created: 1,
  total_processed: 3,
  ...overrides,
})

// ---------------------------------------------------------------------------
// Import hook AFTER mocks are set up
// ---------------------------------------------------------------------------

import { useScheduleUpload } from '../useScheduleUpload'

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: Schedule Upload UI (Story 12.4)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockReset()
    mockGetSession.mockReset()

    // Default: authenticated session
    mockGetSession.mockResolvedValue(createMockSession('mock-token'))
    // Default: successful preview response
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => createMockPreviewResponse(),
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // =========================================================================
  // AC2: File upload and preview
  // =========================================================================
  describe('AC2: File upload and preview', () => {
    it('INT-001: useScheduleUpload hook uploads file and returns preview data', async () => {
      // Given: The hook is initialized with a mock API URL and valid session
      const previewResponse = createMockPreviewResponse()
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => previewResponse,
      })

      const { result } = renderHook(() =>
        useScheduleUpload({ apiUrl: MOCK_API_URL }),
      )

      // When: uploadForPreview(file) is called
      const file = createMockFile('schedule.csv', 2048, 'text/csv')

      await act(async () => {
        await result.current.uploadForPreview(file)
      })

      // Then: A POST request is made to /api/v1/schedule/upload with FormData
      expect(mockFetch).toHaveBeenCalled()
      const [url, options] = mockFetch.mock.calls[0]
      expect(url).toBe(`${MOCK_API_URL}/api/v1/schedule/upload`)
      expect(options.method).toBe('POST')

      // And: Authorization header includes Bearer token
      expect(options.headers).toHaveProperty('Authorization', 'Bearer mock-token')

      // And: Content-Type is NOT manually set (browser sets multipart boundary)
      expect(options.headers?.['Content-Type']).toBeUndefined()

      // And: Body is FormData containing the file
      expect(options.body).toBeInstanceOf(FormData)

      // And: previewData is populated with the response
      expect(result.current.previewData).toEqual(previewResponse)

      // And: isUploading is false after completion
      expect(result.current.isUploading).toBe(false)
    })
  })

  // =========================================================================
  // AC3: Confirm upload
  // =========================================================================
  describe('AC3: Confirm upload', () => {
    it('INT-003: useScheduleUpload hook confirms upload and returns success response', async () => {
      // Given: The hook has previewData loaded with no errors
      const previewData = createMockPreviewResponse({
        has_errors: false,
        rows: [
          createMockPreviewRow({
            row_number: 1,
            asset_match_status: 'matched',
            asset_id: 'uuid-1',
            errors: [],
          }),
        ],
      })

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => previewData,
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => createMockConfirmResponse(),
        })

      const { result } = renderHook(() =>
        useScheduleUpload({ apiUrl: MOCK_API_URL }),
      )

      // Upload first to populate previewData
      const file = createMockFile('schedule.csv', 2048, 'text/csv')
      await act(async () => {
        await result.current.uploadForPreview(file)
      })

      // When: confirmUpload() is called
      await act(async () => {
        await result.current.confirmUpload()
      })

      // Then: A POST request is made to confirm endpoint
      const confirmCall = mockFetch.mock.calls.find(
        ([u]: [string]) => u.includes('/upload/confirm'),
      )
      expect(confirmCall).toBeDefined()
      const [confirmUrl, confirmOptions] = confirmCall!
      expect(confirmUrl).toBe(`${MOCK_API_URL}/api/v1/schedule/upload/confirm`)
      expect(confirmOptions.method).toBe('POST')
      expect(confirmOptions.headers).toHaveProperty('Authorization', 'Bearer mock-token')
      expect(confirmOptions.headers).toHaveProperty('Content-Type', 'application/json')

      // And: confirmResult state is populated
      expect(result.current.confirmResult).toEqual({
        rows_inserted: 3,
        products_created: 1,
        total_processed: 3,
      })

      // And: isConfirming is false after completion
      expect(result.current.isConfirming).toBe(false)
    })
  })

  // =========================================================================
  // Additional Hook Tests (Cross-cutting)
  // =========================================================================
  describe('Auth and Error Handling', () => {
    it('INT-007: useScheduleUpload returns auth error when no session exists', async () => {
      // Given: Supabase getSession returns null session
      mockGetSession.mockResolvedValue({ data: { session: null } })

      const { result } = renderHook(() =>
        useScheduleUpload({ apiUrl: MOCK_API_URL }),
      )

      // When: uploadForPreview(file) is called
      const file = createMockFile('schedule.csv', 2048, 'text/csv')
      await act(async () => {
        await result.current.uploadForPreview(file)
      })

      // Then: error state is set to auth error message
      expect(result.current.error).toMatch(/session.*expired|log in/i)

      // And: isUploading returns to false
      expect(result.current.isUploading).toBe(false)

      // And: no fetch request is made
      expect(mockFetch).not.toHaveBeenCalled()
    })

    it('INT-008: useScheduleUpload handles network error gracefully', async () => {
      // Given: A valid session exists
      mockGetSession.mockResolvedValue(createMockSession('mock-token'))

      // And: fetch throws a network error
      mockFetch.mockRejectedValue(new TypeError('Failed to fetch'))

      const { result } = renderHook(() =>
        useScheduleUpload({ apiUrl: MOCK_API_URL }),
      )

      // When: uploadForPreview(file) is called
      const file = createMockFile('schedule.csv', 2048, 'text/csv')
      await act(async () => {
        await result.current.uploadForPreview(file)
      })

      // Then: error state is set to a network/server error message
      expect(result.current.error).toBeTruthy()

      // And: isUploading returns to false
      expect(result.current.isUploading).toBe(false)

      // And: previewData remains null
      expect(result.current.previewData).toBeNull()
    })

    it('INT-009: useScheduleUpload handles 401 response', async () => {
      // Given: A valid session exists
      mockGetSession.mockResolvedValue(createMockSession('mock-token'))

      // And: API returns 401
      mockFetch.mockResolvedValue({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Unauthorized' }),
      })

      const { result } = renderHook(() =>
        useScheduleUpload({ apiUrl: MOCK_API_URL }),
      )

      // When: uploadForPreview(file) is called
      const file = createMockFile('schedule.csv', 2048, 'text/csv')
      await act(async () => {
        await result.current.uploadForPreview(file)
      })

      // Then: error state is set to auth error message
      expect(result.current.error).toMatch(/session|auth|log in/i)

      // And: isUploading returns to false
      expect(result.current.isUploading).toBe(false)
    })

    it('INT-010: useScheduleUpload handles 500 server error response', async () => {
      // Given: A valid session exists
      mockGetSession.mockResolvedValue(createMockSession('mock-token'))

      // And: API returns 500
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => ({ detail: 'Internal Server Error' }),
      })

      const { result } = renderHook(() =>
        useScheduleUpload({ apiUrl: MOCK_API_URL }),
      )

      // When: uploadForPreview(file) is called
      const file = createMockFile('schedule.csv', 2048, 'text/csv')
      await act(async () => {
        await result.current.uploadForPreview(file)
      })

      // Then: error state is set to server error message
      expect(result.current.error).toBeTruthy()

      // And: isUploading returns to false
      expect(result.current.isUploading).toBe(false)
    })

    it('INT-011: useScheduleUpload mountedRef prevents state updates after unmount', async () => {
      // Given: The hook is rendered and uploadForPreview is called
      mockGetSession.mockResolvedValue(createMockSession('mock-token'))

      // Delay the fetch to allow unmounting before resolution
      let resolveFetch!: (value: unknown) => void
      mockFetch.mockReturnValue(
        new Promise((resolve) => {
          resolveFetch = resolve
        }),
      )

      const { result, unmount } = renderHook(() =>
        useScheduleUpload({ apiUrl: MOCK_API_URL }),
      )

      const file = createMockFile('schedule.csv', 2048, 'text/csv')

      // Start the upload — isUploading should transition to true
      await act(async () => {
        result.current.uploadForPreview(file)
      })

      // Then: isUploading should be true while waiting for response
      expect(result.current.isUploading).toBe(true)

      // When: The component unmounts before the fetch resolves
      unmount()

      // Then: Resolving the fetch after unmount should not cause errors
      await act(async () => {
        resolveFetch({
          ok: true,
          status: 200,
          json: async () => createMockPreviewResponse(),
        })
      })

      // No React warning about setState on unmounted component
    })

    it('INT-012: useScheduleUpload confirmUpload filters and maps rows correctly', async () => {
      // Given: The hook has previewData with mixed rows
      const mixedPreviewData = createMockPreviewResponse({
        has_errors: true,
        rows: [
          // Row 1: matched, no errors (should be included)
          createMockPreviewRow({
            row_number: 1,
            asset_match_status: 'matched',
            asset_id: 'uuid-asset-1',
            product_name: 'Dark Roast',
            date: '2026-02-16',
            shift: 'Day',
            scheduled_quantity: '500',
            errors: [],
          }),
          // Row 2: suggested (should be excluded)
          createMockPreviewRow({
            row_number: 2,
            asset_match_status: 'suggested',
            asset_id: null,
            suggestions: ['Grinder 1'],
            errors: [],
          }),
          // Row 3: has errors (should be excluded)
          createMockPreviewRow({
            row_number: 3,
            asset_match_status: 'matched',
            asset_id: 'uuid-asset-2',
            errors: [{ row_number: 3, field: 'date', message: 'Invalid' }],
          }),
        ],
      })

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => mixedPreviewData,
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => createMockConfirmResponse({ rows_inserted: 1 }),
        })

      const { result } = renderHook(() =>
        useScheduleUpload({ apiUrl: MOCK_API_URL }),
      )

      // Upload to populate previewData
      const file = createMockFile('schedule.csv', 2048, 'text/csv')
      await act(async () => {
        await result.current.uploadForPreview(file)
      })

      // When: confirmUpload() is called
      await act(async () => {
        await result.current.confirmUpload()
      })

      // Then: Only the matched row with no errors is included in the POST body
      const confirmCall = mockFetch.mock.calls.find(
        ([u]: [string]) => u.includes('/upload/confirm'),
      )
      expect(confirmCall).toBeDefined()
      const body = JSON.parse(confirmCall![1].body)

      // Only 1 row should be in the confirm request (the matched, error-free one)
      expect(body.rows).toHaveLength(1)

      // And: Row is mapped to ScheduleConfirmRow format
      expect(body.rows[0]).toEqual({
        asset_id: 'uuid-asset-1',
        product_name: 'Dark Roast',
        scheduled_date: '2026-02-16',
        shift: 'Day',
        scheduled_quantity: 500,
      })
    })

    it('INT-013: useScheduleUpload handles confirm API error', async () => {
      // Given: The hook has previewData loaded
      const previewData = createMockPreviewResponse({
        has_errors: false,
        rows: [
          createMockPreviewRow({ errors: [], asset_match_status: 'matched' }),
        ],
      })

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => previewData,
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 422,
          json: async () => ({ detail: 'Unprocessable Entity' }),
        })

      const { result } = renderHook(() =>
        useScheduleUpload({ apiUrl: MOCK_API_URL }),
      )

      // Upload to populate previewData
      const file = createMockFile('schedule.csv', 2048, 'text/csv')
      await act(async () => {
        await result.current.uploadForPreview(file)
      })

      // When: confirmUpload() is called and API returns 422
      await act(async () => {
        await result.current.confirmUpload()
      })

      // Then: error state is set
      expect(result.current.error).toBeTruthy()

      // And: isConfirming returns to false
      expect(result.current.isConfirming).toBe(false)

      // And: previewData is preserved (not cleared)
      expect(result.current.previewData).not.toBeNull()
    })
  })
})
