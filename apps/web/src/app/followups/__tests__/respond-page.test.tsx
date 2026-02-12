/**
 * Tests for Follow-Up Response Page (Story 15.3: Response Capture via Token Link)
 *
 * TDD tests — these MUST FAIL until the response page component is implemented.
 * Tests cover page rendering, form submission, expired/invalid token handling,
 * mobile responsiveness, and error states.
 *
 * @see Story 15.3 - Response Capture via Token Link
 * @see AC#1 - Response page renders via token link
 * @see AC#2 - Response submission creates message record
 * @see AC#3 - Expired token shows expiry message
 * @see AC#4 - Invalid token shows error
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

// Mock next/navigation with custom per-test overrides
const mockSearchParamsGet = vi.fn()
const mockParams: Record<string, string> = { id: 'uuid-followup-1' }

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    refresh: vi.fn(),
    replace: vi.fn(),
  }),
  useSearchParams: () => ({
    get: mockSearchParamsGet,
  }),
  usePathname: () => '/followups/uuid-followup-1/respond',
  useParams: () => mockParams,
}))

// Mock global fetch for API calls
const mockFetch = vi.fn()
global.fetch = mockFetch

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const VALID_TOKEN = 'valid-token-uuid'
const EXPIRED_TOKEN = 'expired-token-uuid'
const INVALID_TOKEN = 'invalid-token-uuid'
const FOLLOWUP_ID = 'uuid-followup-1'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const createMockContextResponse = (overrides: Record<string, unknown> = {}) => ({
  ok: true,
  status: 200,
  json: async () => ({
    action_summary: 'Replace bearing on Pump-101',
    asset_name: 'Pump-101',
    category: 'safety',
    assigned_by_email: 'manager@plant.com',
    assigned_by_name: 'John Manager',
    note: 'Please prioritize this week',
    report_date: '2026-02-10',
    recommendation: 'Replace worn bearing immediately to prevent failure',
    evidence_summary: 'Vibration levels exceeded threshold 3x in past week',
    financial_impact: '$15,000 estimated repair cost',
    ...overrides,
  }),
})

const createMockExpiredResponse = () => ({
  ok: false,
  status: 400,
  json: async () => ({
    error_reason: 'expired',
    detail: 'Token expired',
  }),
})

const createMockInvalidResponse = () => ({
  ok: false,
  status: 404,
  json: async () => ({
    error_reason: 'invalid',
    detail: 'Invalid link',
  }),
})

const createMockSubmitSuccessResponse = () => ({
  ok: true,
  status: 200,
  json: async () => ({
    success: true,
    message: 'Response recorded',
  }),
})

// ---------------------------------------------------------------------------
// Import component AFTER mocks
// ---------------------------------------------------------------------------

// The page component does not exist yet — this import will fail during TDD
import RespondPage from '../../followups/[id]/respond/page'

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: Follow-Up Response Page (Story 15.3)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockReset()
    mockSearchParamsGet.mockReset()

    // Default: valid token in search params
    mockSearchParamsGet.mockImplementation((key: string) => {
      if (key === 'token') return VALID_TOKEN
      return null
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // =========================================================================
  // AC1: Response page renders via token link
  // =========================================================================
  describe('AC1: Response page renders via token link', () => {
    it('E2E-001: Clicking token link loads response page with context', async () => {
      /**
       * Given: A follow-up has been assigned and a notification email sent with a valid
       *        token URL
       * When: The assignee navigates to this URL in a browser (not logged in)
       * Then: The page renders showing: (1) the action item recommendation text,
       *       (2) evidence summary, (3) financial impact if present, (4) who assigned it,
       *       (5) the manager's note, and (6) a text response textarea field with submit button
       */

      // Mock context API call
      mockFetch.mockImplementation((url: string) => {
        if (url.includes('/context')) {
          return Promise.resolve(createMockContextResponse())
        }
        return Promise.resolve({ ok: false, status: 404, json: async () => ({}) })
      })

      render(<RespondPage />)

      // Wait for context to load
      await waitFor(() => {
        expect(screen.queryByText(/loading/i)).not.toBeInTheDocument()
      })

      // (1) Action item recommendation text
      expect(screen.getByText(/Replace worn bearing immediately/i)).toBeInTheDocument()

      // (2) Evidence summary
      expect(screen.getByText(/Vibration levels exceeded threshold/i)).toBeInTheDocument()

      // (3) Financial impact
      expect(screen.getByText(/\$15,000/i)).toBeInTheDocument()

      // (4) Who assigned it
      expect(screen.getByText(/John Manager/i)).toBeInTheDocument()

      // (5) Manager's note
      expect(screen.getByText(/Please prioritize this week/i)).toBeInTheDocument()

      // (6) Textarea and submit button
      expect(screen.getByRole('textbox')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /submit/i })).toBeInTheDocument()
    })

    it('E2E-002: Response page works on mobile browser', async () => {
      /**
       * Given: A valid token link exists for a follow-up
       * When: The assignee opens the link on a mobile device (small viewport, 375x812)
       * Then: The page is responsive — context card and form are readable, textarea is usable,
       *       submit button is tappable, no horizontal scrolling required
       */

      // Mock context API call
      mockFetch.mockImplementation((url: string) => {
        if (url.includes('/context')) {
          return Promise.resolve(createMockContextResponse())
        }
        return Promise.resolve({ ok: false, status: 404, json: async () => ({}) })
      })

      // Set mobile viewport
      Object.defineProperty(window, 'innerWidth', { value: 375, writable: true })
      Object.defineProperty(window, 'innerHeight', { value: 812, writable: true })

      const { container } = render(<RespondPage />)

      await waitFor(() => {
        expect(screen.queryByText(/loading/i)).not.toBeInTheDocument()
      })

      // Page should render all key elements
      expect(screen.getByRole('textbox')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /submit/i })).toBeInTheDocument()

      // No horizontal overflow (basic check — container width within viewport)
      const rootElement = container.firstChild as HTMLElement
      if (rootElement) {
        const styles = window.getComputedStyle(rootElement)
        // Content should not overflow horizontally
        expect(rootElement.scrollWidth).toBeLessThanOrEqual(375 + 20) // small tolerance
      }
    })
  })

  // =========================================================================
  // AC2: Response submission creates message record
  // =========================================================================
  describe('AC2: Response submission', () => {
    it('E2E-003: Submitting response shows success confirmation', async () => {
      /**
       * Given: The response page is rendered with a valid token, context card is visible,
       *        and textarea is populated with "I will address this by Friday"
       * When: The user clicks the Submit button
       * Then: (1) A success confirmation is shown with message "Your response has been recorded",
       *       (2) The submit button becomes disabled to prevent double-submit,
       *       (3) The textarea is no longer editable
       */
      const user = userEvent.setup()

      // Mock context and submit API calls
      mockFetch.mockImplementation((url: string, opts?: RequestInit) => {
        if (url.includes('/context')) {
          return Promise.resolve(createMockContextResponse())
        }
        if (url.includes('/respond') && opts?.method === 'POST') {
          return Promise.resolve(createMockSubmitSuccessResponse())
        }
        return Promise.resolve({ ok: false, status: 404, json: async () => ({}) })
      })

      render(<RespondPage />)

      // Wait for context to load
      await waitFor(() => {
        expect(screen.getByRole('textbox')).toBeInTheDocument()
      })

      // Type response
      const textarea = screen.getByRole('textbox')
      await user.type(textarea, 'I will address this by Friday')

      // Click submit
      const submitButton = screen.getByRole('button', { name: /submit/i })
      await user.click(submitButton)

      // (1) Success confirmation shown
      await waitFor(() => {
        expect(screen.getByText(/your response has been recorded/i)).toBeInTheDocument()
      })

      // (2) Submit button is disabled
      expect(screen.getByRole('button', { name: /submit/i })).toBeDisabled()

      // (3) Textarea is no longer editable
      expect(screen.getByRole('textbox')).toHaveAttribute('disabled')
    })

    it('E2E-004: Double-submit is prevented on frontend', async () => {
      /**
       * Given: The user has already submitted a response and sees the success confirmation
       * When: The user attempts to click the submit button again
       * Then: The button remains disabled and no second POST request is sent
       */
      const user = userEvent.setup()

      let submitCallCount = 0

      mockFetch.mockImplementation((url: string, opts?: RequestInit) => {
        if (url.includes('/context')) {
          return Promise.resolve(createMockContextResponse())
        }
        if (url.includes('/respond') && opts?.method === 'POST') {
          submitCallCount++
          return Promise.resolve(createMockSubmitSuccessResponse())
        }
        return Promise.resolve({ ok: false, status: 404, json: async () => ({}) })
      })

      render(<RespondPage />)

      await waitFor(() => {
        expect(screen.getByRole('textbox')).toBeInTheDocument()
      })

      // Type and submit
      const textarea = screen.getByRole('textbox')
      await user.type(textarea, 'My response')
      const submitButton = screen.getByRole('button', { name: /submit/i })
      await user.click(submitButton)

      // Wait for success
      await waitFor(() => {
        expect(screen.getByText(/your response has been recorded/i)).toBeInTheDocument()
      })

      // Attempt second click (button should be disabled)
      await user.click(submitButton).catch(() => {
        // Expected — disabled button may not fire events
      })

      // Only one POST should have been made
      expect(submitCallCount).toBe(1)
    })
  })

  // =========================================================================
  // AC3: Expired token shows expiry message
  // =========================================================================
  describe('AC3: Expired token handling', () => {
    it('E2E-005: Expired token link shows expiry message with no form', async () => {
      /**
       * Given: A token link where the token has expired (>72 hours since creation)
       * When: The assignee clicks the link and navigates to the URL
       * Then: The page displays "This link has expired. Please log in to the app to respond."
       *       and no textarea or submit button is rendered
       */
      mockSearchParamsGet.mockImplementation((key: string) => {
        if (key === 'token') return EXPIRED_TOKEN
        return null
      })

      mockFetch.mockImplementation((url: string) => {
        if (url.includes('/context')) {
          return Promise.resolve(createMockExpiredResponse())
        }
        return Promise.resolve({ ok: false, status: 404, json: async () => ({}) })
      })

      render(<RespondPage />)

      await waitFor(() => {
        expect(screen.queryByText(/loading/i)).not.toBeInTheDocument()
      })

      // Should show expiry message
      expect(
        screen.getByText(/this link has expired/i)
      ).toBeInTheDocument()
      expect(
        screen.getByText(/log in to the app to respond/i)
      ).toBeInTheDocument()

      // No form elements should be rendered
      expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
      expect(screen.queryByRole('button', { name: /submit/i })).not.toBeInTheDocument()
    })

    it('E2E-006: Already-used token link shows expiry message with no form', async () => {
      /**
       * Given: A token link where the token has already been used
       * When: The assignee clicks the link again
       * Then: The page displays "This link has expired" and no form is rendered
       */
      mockSearchParamsGet.mockImplementation((key: string) => {
        if (key === 'token') return 'used-token-uuid'
        return null
      })

      mockFetch.mockImplementation((url: string) => {
        if (url.includes('/context')) {
          return Promise.resolve(createMockExpiredResponse())
        }
        return Promise.resolve({ ok: false, status: 404, json: async () => ({}) })
      })

      render(<RespondPage />)

      await waitFor(() => {
        expect(screen.queryByText(/loading/i)).not.toBeInTheDocument()
      })

      // Should show expiry message (used tokens treated same as expired)
      expect(
        screen.getByText(/this link has expired/i)
      ).toBeInTheDocument()

      // No form elements
      expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
      expect(screen.queryByRole('button', { name: /submit/i })).not.toBeInTheDocument()
    })
  })

  // =========================================================================
  // AC4: Invalid token shows error
  // =========================================================================
  describe('AC4: Invalid token handling', () => {
    it('E2E-007: Invalid token link shows error message with no form', async () => {
      /**
       * Given: A URL with a completely invalid/nonexistent token
       * When: The user navigates to this URL
       * Then: The page displays "Invalid link" (or a 404 message), no form is rendered
       */
      mockSearchParamsGet.mockImplementation((key: string) => {
        if (key === 'token') return INVALID_TOKEN
        return null
      })

      mockFetch.mockImplementation((url: string) => {
        if (url.includes('/context')) {
          return Promise.resolve(createMockInvalidResponse())
        }
        return Promise.resolve({ ok: false, status: 404, json: async () => ({}) })
      })

      render(<RespondPage />)

      await waitFor(() => {
        expect(screen.queryByText(/loading/i)).not.toBeInTheDocument()
      })

      // Should show invalid link message
      expect(screen.getByText(/invalid link/i)).toBeInTheDocument()

      // No form elements
      expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
      expect(screen.queryByRole('button', { name: /submit/i })).not.toBeInTheDocument()
    })

    it('E2E-008: Missing token parameter shows error', async () => {
      /**
       * Given: A URL without a token parameter
       * When: The user navigates to this URL
       * Then: The page displays an error message and no form is rendered
       */
      mockSearchParamsGet.mockImplementation(() => null) // No token

      render(<RespondPage />)

      await waitFor(() => {
        expect(screen.queryByText(/loading/i)).not.toBeInTheDocument()
      })

      // Should show some error message (invalid or missing token)
      const hasError = screen.queryByText(/invalid/i) || screen.queryByText(/error/i) ||
        screen.queryByText(/missing/i)
      expect(hasError).toBeTruthy()

      // No form elements
      expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
      expect(screen.queryByRole('button', { name: /submit/i })).not.toBeInTheDocument()
    })
  })
})
