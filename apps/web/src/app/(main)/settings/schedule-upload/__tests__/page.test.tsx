/**
 * Schedule Upload Page Tests (Story 12.4: Schedule Upload UI)
 *
 * TDD tests — these MUST FAIL until the page is implemented.
 *
 * @see Story 12.4 - Schedule Upload UI
 * @see AC #1 - Page renders with upload zone
 * @see AC #2 - Preview table shown after upload
 * @see AC #3 - Confirm upload and redirect
 * @see AC #4 - Disabled confirm when errors exist
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockPush = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    refresh: vi.fn(),
    replace: vi.fn(),
  }),
  useSearchParams: () => ({
    get: vi.fn().mockReturnValue(null),
  }),
  usePathname: () => '/settings/schedule-upload',
  useParams: () => ({}),
}))

// Mock the useScheduleUpload hook
const mockUploadForPreview = vi.fn()
const mockConfirmUpload = vi.fn()
const mockReset = vi.fn()

const defaultHookState = {
  isUploading: false,
  isConfirming: false,
  error: null as string | null,
  previewData: null as Record<string, unknown> | null,
  confirmResult: null as Record<string, unknown> | null,
  uploadForPreview: mockUploadForPreview,
  confirmUpload: mockConfirmUpload,
  reset: mockReset,
}

let hookState = { ...defaultHookState }

vi.mock('@/hooks/useScheduleUpload', () => ({
  useScheduleUpload: () => hookState,
}))

// ---------------------------------------------------------------------------
// Import page AFTER mocks
// ---------------------------------------------------------------------------

import ScheduleUploadPage from '../page'

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

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
    createMockPreviewRow({ row_number: 2 }),
    createMockPreviewRow({ row_number: 3 }),
  ],
  has_errors: false,
  matched_assets: ['Grinder 1', 'Grinder 2', 'Grinder 3'],
  matched_products: ['Dark Roast 12oz'],
  new_products: [],
  ...overrides,
})

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: Schedule Upload Page (Story 12.4)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    hookState = { ...defaultHookState }
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // =========================================================================
  // AC1: Page renders with upload zone
  // =========================================================================
  describe('AC1: Page renders with upload zone', () => {
    it('UNIT-004: Schedule Upload page renders at /settings/schedule-upload route', () => {
      // Given: The Schedule Upload page component is rendered
      render(<ScheduleUploadPage />)

      // Then: The page heading "Schedule Upload" is visible
      expect(screen.getByText('Schedule Upload')).toBeInTheDocument()

      // And: The ScheduleUploadZone is displayed (it renders the drop text)
      expect(screen.getByText(/drop csv or excel file here/i)).toBeInTheDocument()

      // And: The "Confirm Upload" button is NOT visible (no preview data yet)
      expect(screen.queryByRole('button', { name: /confirm upload/i })).not.toBeInTheDocument()
    })
  })

  // =========================================================================
  // AC2: Preview table shown after upload
  // =========================================================================
  describe('AC2: Preview table shown after upload', () => {
    it('INT-002: Page shows preview table after successful file upload', () => {
      // Given: The hook returns previewData after file selection
      hookState = {
        ...defaultHookState,
        previewData: createMockPreviewResponse(),
      }

      // When: The page renders with preview data
      render(<ScheduleUploadPage />)

      // Then: The SchedulePreviewTable is shown with returned rows
      expect(screen.getAllByText('Grinder 1').length).toBeGreaterThan(0)

      // And: The "Confirm Upload" button becomes visible
      expect(screen.getByRole('button', { name: /confirm upload/i })).toBeInTheDocument()
    })
  })

  // =========================================================================
  // AC3: Confirm upload and redirect
  // =========================================================================
  describe('AC3: Confirm upload and redirect', () => {
    it('UNIT-020: Confirm Upload button is enabled when preview has no errors', () => {
      // Given: previewData with has_errors: false
      hookState = {
        ...defaultHookState,
        previewData: createMockPreviewResponse({ has_errors: false }),
      }

      // When: The page renders
      render(<ScheduleUploadPage />)

      // Then: The "Confirm Upload" button is enabled
      const confirmButton = screen.getByRole('button', { name: /confirm upload/i })
      expect(confirmButton).not.toBeDisabled()

      // And: Clicking it triggers the confirmUpload function
      fireEvent.click(confirmButton)
      expect(mockConfirmUpload).toHaveBeenCalled()
    })

    it('UNIT-021: Confirm Upload button shows loading spinner during confirmation', () => {
      // Given: The page is in the confirming state
      hookState = {
        ...defaultHookState,
        previewData: createMockPreviewResponse({ has_errors: false }),
        isConfirming: true,
      }

      // When: The component renders
      render(<ScheduleUploadPage />)

      // Then: The button shows a loading spinner
      const confirmButton = screen.getByRole('button', { name: /confirm|upload/i })
      const spinner = confirmButton.querySelector('.animate-spin')
      expect(spinner).toBeTruthy()

      // And: The button is disabled
      expect(confirmButton).toBeDisabled()
    })

    it('INT-004: Page shows success message and redirects after confirm', async () => {
      // Given: The confirm result is populated
      vi.useFakeTimers()

      hookState = {
        ...defaultHookState,
        previewData: createMockPreviewResponse({ has_errors: false }),
        confirmResult: {
          rows_inserted: 3,
          products_created: 1,
          total_processed: 3,
        },
      }

      // When: The page renders with success state
      render(<ScheduleUploadPage />)

      // Then: A success message appears with the row count
      expect(screen.getByText(/successfully.*3/i)).toBeInTheDocument()

      // And: After 1.5 seconds, redirect to /morning-report
      vi.advanceTimersByTime(1500)
      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/morning-report')
      })

      vi.useRealTimers()
    })

    it('INT-005: Success message displays correct row count from API response', () => {
      // Given: The confirm API returns rows_inserted: 7, products_created: 2
      hookState = {
        ...defaultHookState,
        previewData: createMockPreviewResponse(),
        confirmResult: {
          rows_inserted: 7,
          products_created: 2,
          total_processed: 7,
        },
      }

      // When: The success state is rendered
      render(<ScheduleUploadPage />)

      // Then: The success message includes "7" rows inserted
      expect(screen.getByText(/7/)).toBeInTheDocument()
    })

    it('INT-006: Redirect timeout is cleaned up on unmount', () => {
      // Given: The page shows a success message with redirect pending
      vi.useFakeTimers()

      hookState = {
        ...defaultHookState,
        previewData: createMockPreviewResponse(),
        confirmResult: {
          rows_inserted: 3,
          products_created: 0,
          total_processed: 3,
        },
      }

      const { unmount } = render(<ScheduleUploadPage />)

      // Then: A success message should be visible before unmount
      expect(screen.getByText(/successfully.*3/i)).toBeInTheDocument()

      // When: The component unmounts before the redirect fires
      unmount()

      // Then: Advancing timers does not cause router.push to be called
      vi.advanceTimersByTime(2000)
      expect(mockPush).not.toHaveBeenCalled()

      vi.useRealTimers()
    })
  })

  // =========================================================================
  // AC4: Disabled confirm when errors exist
  // =========================================================================
  describe('AC4: Disabled confirm when errors exist', () => {
    it('UNIT-022: Confirm Upload button is disabled when preview has errors', () => {
      // Given: previewData with has_errors: true
      hookState = {
        ...defaultHookState,
        previewData: createMockPreviewResponse({
          has_errors: true,
          rows: [
            createMockPreviewRow({
              errors: [
                { row_number: 1, field: 'date', message: 'Invalid date' },
              ],
            }),
          ],
        }),
      }

      // When: The page renders
      render(<ScheduleUploadPage />)

      // Then: The "Confirm Upload" button is disabled
      const confirmButton = screen.getByRole('button', { name: /confirm upload/i })
      expect(confirmButton).toBeDisabled()
    })
  })

  // =========================================================================
  // Page-Level Integration Tests
  // =========================================================================
  describe('Page-Level Integration Tests', () => {
    it('INT-014: Page shows loading spinner during file upload', () => {
      // Given: The upload is in progress
      hookState = {
        ...defaultHookState,
        isUploading: true,
      }

      // When: The page renders
      render(<ScheduleUploadPage />)

      // Then: A loading spinner is displayed
      const spinner = document.querySelector('.animate-spin')
      expect(spinner).toBeTruthy()
    })

    it('INT-015: Page displays error state with retry option', () => {
      // Given: The file upload failed with an error
      hookState = {
        ...defaultHookState,
        error: "Something went wrong on our end.",
      }

      // When: The page renders
      render(<ScheduleUploadPage />)

      // Then: An error message is displayed
      expect(screen.getByText(/something went wrong/i)).toBeInTheDocument()

      // And: A retry option/button is available
      const retryButton = screen.getByRole('button', { name: /retry|try again/i })
      expect(retryButton).toBeInTheDocument()
    })

    it('INT-016: Page allows uploading a different file after preview', () => {
      // Given: The page is showing a preview table
      hookState = {
        ...defaultHookState,
        previewData: createMockPreviewResponse(),
      }

      // When: The user clicks "Upload Different File" button
      render(<ScheduleUploadPage />)

      const uploadDiffButton = screen.getByRole('button', {
        name: /upload different file|new file|change file/i,
      })
      fireEvent.click(uploadDiffButton)

      // Then: The reset function is called to clear preview and show upload zone
      expect(mockReset).toHaveBeenCalled()
    })
  })
})
