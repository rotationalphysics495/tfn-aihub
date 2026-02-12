/**
 * ActionPlanForm Component Tests (Story 16.3: Create Action Plan from Follow-Up)
 *
 * TDD tests — these MUST FAIL until the ActionPlanForm component is implemented.
 * Tests cover form rendering, pre-fill logic, field mapping, validation,
 * submission via POST /api/v1/action-plans, and success/error states.
 *
 * @see Story 16.3 - Create Action Plan from Follow-Up
 * @see AC #1 - Pre-populated Action Plan Form from Follow-Up Response
 * @see AC #4 - Action Plan Created via POST with Required Fields
 * @see AC #5 - Follow-Up Updates Without Full Page Reload After Action Plan Creation
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'

// ---------------------------------------------------------------------------
// Mocks (BEFORE imports)
// ---------------------------------------------------------------------------

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), back: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => '/',
  useParams: () => ({}),
}))

const mockGetSession = vi.fn()

// Track Supabase query chain for asset lookup verification
const mockSupabaseFrom = vi.fn()
const mockSupabaseSelect = vi.fn()
const mockSupabaseEq = vi.fn()
const mockSupabaseSingle = vi.fn()

let mockSupabaseAssetResult: { data: { id: string } | null; error: { message: string } | null } = {
  data: { id: 'asset-uuid-123' },
  error: null,
}

vi.mock('@/lib/supabase/client', () => ({
  createClient: () => ({
    auth: { getSession: mockGetSession },
    from: (table: string) => {
      mockSupabaseFrom(table)
      return {
        select: (...args: unknown[]) => {
          mockSupabaseSelect(...args)
          return {
            eq: (col: string, val: string) => {
              mockSupabaseEq(col, val)
              return {
                single: () => {
                  mockSupabaseSingle()
                  return mockSupabaseAssetResult
                },
              }
            },
          }
        },
      }
    },
  }),
}))

const mockFetch = vi.fn()
global.fetch = mockFetch

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

interface ActionPlanPrefill {
  followUpId: string
  actionSummary: string
  assetName: string | null
  responseText: string
  category: string | null
}

const createMockPrefill = (overrides: Partial<ActionPlanPrefill> = {}): ActionPlanPrefill => ({
  followUpId: 'fu-123',
  actionSummary: 'Investigate pressure anomaly on main valve',
  assetName: 'Grinder 5',
  responseText: 'Root cause is worn bearing on pump shaft',
  category: 'safety',
  ...overrides,
})

const createMockSession = (accessToken: string | null = 'mock-token') => ({
  data: { session: accessToken !== null ? { access_token: accessToken, user: { id: 'user-123' } } : null },
})

const createMockSuccessResponse = (overrides: Record<string, unknown> = {}) => ({
  ok: true,
  status: 201,
  json: async () => ({
    id: 'ap-new',
    title: 'Action Plan: Investigate pressure anomaly on main valve',
    status: 'open',
    ...overrides,
  }),
})

const createMockErrorResponse = (status: number, detail: string = `Error ${status}`) => ({
  ok: false,
  status,
  json: async () => ({ detail }),
})

// ---------------------------------------------------------------------------
// Import component AFTER mocks are set up
// ---------------------------------------------------------------------------

// The component does not exist yet — this import will fail until it's created.
import { ActionPlanForm } from '../ActionPlanForm'

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: ActionPlanForm Component (Story 16.3)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockReset()
    mockGetSession.mockReset()
    mockSupabaseFrom.mockClear()
    mockSupabaseSelect.mockClear()
    mockSupabaseEq.mockClear()
    mockSupabaseSingle.mockClear()

    // Default: authenticated session
    mockGetSession.mockResolvedValue(createMockSession('mock-token'))

    // Default: asset lookup succeeds
    mockSupabaseAssetResult = { data: { id: 'asset-uuid-123' }, error: null }
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // =========================================================================
  // AC1: Pre-populated Action Plan Form from Follow-Up Response
  // =========================================================================
  describe('AC1: Pre-populated Action Plan Form', () => {
    it('16-3-create-action-plan-from-followup-UNIT-001: ActionPlanForm renders all required form fields', () => {
      // Given: An ActionPlanForm component is rendered with a prefill prop
      //        containing follow-up context data
      const prefill = createMockPrefill()

      // When: The dialog renders
      render(
        <ActionPlanForm
          open={true}
          onClose={vi.fn()}
          prefill={prefill}
        />
      )

      // Then: The form displays fields for:
      // - title (Input, editable)
      expect(screen.getByLabelText(/title/i)).toBeInTheDocument()

      // - description (Textarea, editable)
      expect(screen.getByLabelText(/description/i)).toBeInTheDocument()

      // - category (Select with options: corrective/preventive/improvement)
      const categorySelect = screen.getByLabelText(/category/i)
      expect(categorySelect).toBeInTheDocument()

      // - root_cause (Textarea, editable)
      expect(screen.getByLabelText(/root cause/i)).toBeInTheDocument()

      // - corrective_action (Textarea, empty)
      expect(screen.getByLabelText(/corrective action/i)).toBeInTheDocument()

      // - preventive_action (Textarea, empty)
      expect(screen.getByLabelText(/preventive action/i)).toBeInTheDocument()

      // - priority (Select with options: low/medium/high/critical)
      expect(screen.getByLabelText(/priority/i)).toBeInTheDocument()

      // - due_date (date input, empty)
      expect(screen.getByLabelText(/due date/i)).toBeInTheDocument()

      // - asset name display (read-only, showing "Grinder 5")
      expect(screen.getByText(/grinder 5/i)).toBeInTheDocument()
    })

    it('16-3-create-action-plan-from-followup-UNIT-002: ActionPlanForm pre-fills title truncated to 80 characters', () => {
      // Given: An ActionPlanForm is rendered with a prefill containing a very long
      //        action_summary exceeding 80 characters
      const longSummary =
        'Investigate the root cause of the intermittent pressure fluctuations observed on the main hydraulic valve during the morning shift'
      const prefill = createMockPrefill({ actionSummary: longSummary })

      // When: The form renders
      render(
        <ActionPlanForm
          open={true}
          onClose={vi.fn()}
          prefill={prefill}
        />
      )

      // Then: The title field value starts with "Action Plan: " followed by
      //       the action_summary text, truncated so the total length does not
      //       exceed approximately 80 characters
      const titleInput = screen.getByLabelText(/title/i) as HTMLInputElement
      expect(titleInput.value).toMatch(/^Action Plan: /)
      expect(titleInput.value.length).toBeLessThanOrEqual(80)
    })

    it('16-3-create-action-plan-from-followup-UNIT-003: ActionPlanForm maps follow-up category to action plan category correctly', () => {
      // Given: ActionPlanForm is rendered with different follow-up categories

      // Scenario 1: safety -> corrective
      const { unmount: unmount1 } = render(
        <ActionPlanForm
          open={true}
          onClose={vi.fn()}
          prefill={createMockPrefill({ category: 'safety' })}
        />
      )
      const categorySelect1 = screen.getByLabelText(/category/i) as HTMLSelectElement
      expect(categorySelect1.value).toBe('corrective')
      unmount1()

      // Scenario 2: oee -> improvement
      const { unmount: unmount2 } = render(
        <ActionPlanForm
          open={true}
          onClose={vi.fn()}
          prefill={createMockPrefill({ category: 'oee' })}
        />
      )
      const categorySelect2 = screen.getByLabelText(/category/i) as HTMLSelectElement
      expect(categorySelect2.value).toBe('improvement')
      unmount2()

      // Scenario 3: financial -> corrective
      render(
        <ActionPlanForm
          open={true}
          onClose={vi.fn()}
          prefill={createMockPrefill({ category: 'financial' })}
        />
      )
      const categorySelect3 = screen.getByLabelText(/category/i) as HTMLSelectElement
      expect(categorySelect3.value).toBe('corrective')
    })

    it('16-3-create-action-plan-from-followup-UNIT-004: ActionPlanForm maps follow-up category to priority correctly', () => {
      // Given: ActionPlanForm is rendered with different follow-up categories

      // Scenario 1: safety -> high
      const { unmount: unmount1 } = render(
        <ActionPlanForm
          open={true}
          onClose={vi.fn()}
          prefill={createMockPrefill({ category: 'safety' })}
        />
      )
      const prioritySelect1 = screen.getByLabelText(/priority/i) as HTMLSelectElement
      expect(prioritySelect1.value).toBe('high')
      unmount1()

      // Scenario 2: oee -> medium
      const { unmount: unmount2 } = render(
        <ActionPlanForm
          open={true}
          onClose={vi.fn()}
          prefill={createMockPrefill({ category: 'oee' })}
        />
      )
      const prioritySelect2 = screen.getByLabelText(/priority/i) as HTMLSelectElement
      expect(prioritySelect2.value).toBe('medium')
      unmount2()

      // Scenario 3: financial -> medium
      render(
        <ActionPlanForm
          open={true}
          onClose={vi.fn()}
          prefill={createMockPrefill({ category: 'financial' })}
        />
      )
      const prioritySelect3 = screen.getByLabelText(/priority/i) as HTMLSelectElement
      expect(prioritySelect3.value).toBe('medium')
    })

    it('16-3-create-action-plan-from-followup-UNIT-005: ActionPlanForm resolves asset_id from asset_name via Supabase lookup', async () => {
      // Given: An ActionPlanForm is rendered with prefill containing assetName='Grinder 5'
      mockSupabaseAssetResult = { data: { id: 'asset-uuid-123' }, error: null }

      const prefill = createMockPrefill({ assetName: 'Grinder 5' })

      // When: The form initializes and performs the asset lookup
      render(
        <ActionPlanForm
          open={true}
          onClose={vi.fn()}
          prefill={prefill}
        />
      )

      // Then: A Supabase query is made to the 'assets' table
      //       with .eq('name', 'Grinder 5').single()
      await waitFor(() => {
        expect(mockSupabaseFrom).toHaveBeenCalledWith('assets')
      })
      expect(mockSupabaseSelect).toHaveBeenCalledWith('id')
      expect(mockSupabaseEq).toHaveBeenCalledWith('name', 'Grinder 5')
      expect(mockSupabaseSingle).toHaveBeenCalled()
    })

    it('16-3-create-action-plan-from-followup-UNIT-006: ActionPlanForm handles asset_name not found in assets table gracefully', async () => {
      // Given: An ActionPlanForm is rendered with prefill containing
      //        assetName='Unknown Machine 99'
      mockSupabaseAssetResult = { data: null, error: { message: 'not found' } }

      const prefill = createMockPrefill({ assetName: 'Unknown Machine 99' })

      // When: The Supabase assets lookup returns no match
      // Then: The form still renders without error
      expect(() => {
        render(
          <ActionPlanForm
            open={true}
            onClose={vi.fn()}
            prefill={prefill}
          />
        )
      }).not.toThrow()

      // And: The asset name display shows "Unknown Machine 99" as read-only text
      expect(screen.getByText(/unknown machine 99/i)).toBeInTheDocument()
    })

    it('16-3-create-action-plan-from-followup-UNIT-007: All pre-filled fields in ActionPlanForm are editable by the manager', async () => {
      // Given: An ActionPlanForm is rendered with all pre-filled fields
      const prefill = createMockPrefill()

      render(
        <ActionPlanForm
          open={true}
          onClose={vi.fn()}
          prefill={prefill}
        />
      )

      // When: The manager modifies the title
      const titleInput = screen.getByLabelText(/title/i)
      fireEvent.change(titleInput, { target: { value: 'Custom Title' } })

      // Then: The title field updates
      expect((titleInput as HTMLInputElement).value).toBe('Custom Title')

      // When: The manager changes category to 'preventive'
      const categorySelect = screen.getByLabelText(/category/i)
      fireEvent.change(categorySelect, { target: { value: 'preventive' } })

      // Then: Category updates
      expect((categorySelect as HTMLSelectElement).value).toBe('preventive')

      // When: The manager changes priority to 'critical'
      const prioritySelect = screen.getByLabelText(/priority/i)
      fireEvent.change(prioritySelect, { target: { value: 'critical' } })

      // Then: Priority updates
      expect((prioritySelect as HTMLSelectElement).value).toBe('critical')

      // When: The manager edits root_cause
      const rootCauseInput = screen.getByLabelText(/root cause/i)
      fireEvent.change(rootCauseInput, { target: { value: 'Updated root cause' } })

      // Then: Root cause updates
      expect((rootCauseInput as HTMLTextAreaElement).value).toBe('Updated root cause')
    })

    it('16-3-create-action-plan-from-followup-UNIT-008: ActionPlanForm handles null asset_name in prefill', () => {
      // Given: An ActionPlanForm is rendered with prefill where assetName is null
      const prefill = createMockPrefill({ assetName: null })

      // When: The form renders
      // Then: No Supabase assets lookup is performed
      expect(() => {
        render(
          <ActionPlanForm
            open={true}
            onClose={vi.fn()}
            prefill={prefill}
          />
        )
      }).not.toThrow()

      // And: The form does not throw an error
      // And: No Supabase lookup to assets table was attempted
      expect(mockSupabaseFrom).not.toHaveBeenCalledWith('assets')
    })
  })

  // =========================================================================
  // AC1 Integration: Pre-populated form from FollowUpDetailDialog
  // =========================================================================
  describe('AC1 Integration: Pre-populated form from follow-up context', () => {
    it('16-3-create-action-plan-from-followup-INT-001: ActionPlanForm dialog renders with pre-filled data from follow-up context', async () => {
      // Given: A follow-up with status='in_progress', asset_name='Grinder 5',
      //        action_summary='Investigate pressure anomaly on main valve',
      //        category='safety', and an inbound response message body
      const prefill = createMockPrefill({
        followUpId: 'fu-int-001',
        actionSummary: 'Investigate pressure anomaly on main valve',
        assetName: 'Grinder 5',
        responseText: 'Root cause is worn bearing on pump shaft',
        category: 'safety',
      })

      mockSupabaseAssetResult = { data: { id: 'asset-uuid-123' }, error: null }

      // When: The ActionPlanForm dialog opens
      render(
        <ActionPlanForm
          open={true}
          onClose={vi.fn()}
          prefill={prefill}
        />
      )

      // Then: title is pre-filled as "Action Plan: Investigate pressure anomaly on main valve"
      //       (truncated to 80 chars)
      const titleInput = screen.getByLabelText(/title/i) as HTMLInputElement
      expect(titleInput.value).toMatch(/^Action Plan: Investigate pressure anomaly/)
      expect(titleInput.value.length).toBeLessThanOrEqual(80)

      // And: description contains the action_summary text
      const descriptionInput = screen.getByLabelText(/description/i) as HTMLTextAreaElement
      expect(descriptionInput.value).toContain('Investigate pressure anomaly on main valve')

      // And: root_cause is pre-filled with the assignee's response body
      const rootCauseInput = screen.getByLabelText(/root cause/i) as HTMLTextAreaElement
      expect(rootCauseInput.value).toBe('Root cause is worn bearing on pump shaft')

      // And: category set to "corrective" (mapped from safety)
      const categorySelect = screen.getByLabelText(/category/i) as HTMLSelectElement
      expect(categorySelect.value).toBe('corrective')

      // And: priority set to "high" (mapped from safety)
      const prioritySelect = screen.getByLabelText(/priority/i) as HTMLSelectElement
      expect(prioritySelect.value).toBe('high')

      // And: asset lookup is triggered for 'Grinder 5'
      await waitFor(() => {
        expect(mockSupabaseFrom).toHaveBeenCalledWith('assets')
        expect(mockSupabaseEq).toHaveBeenCalledWith('name', 'Grinder 5')
      })
    })

    it('16-3-create-action-plan-from-followup-INT-003: Pre-fill handles multiple inbound messages by using latest response', () => {
      // Given: A follow-up has multiple inbound response messages
      //        (the caller should pass the latest response text via prefill)
      // The responseText from the latest message body should be used
      const prefill = createMockPrefill({
        responseText: 'Final root cause confirmed: worn bearing',
      })

      // When: The ActionPlanForm renders
      render(
        <ActionPlanForm
          open={true}
          onClose={vi.fn()}
          prefill={prefill}
        />
      )

      // Then: The root_cause field is pre-filled with the latest response body
      const rootCauseInput = screen.getByLabelText(/root cause/i) as HTMLTextAreaElement
      expect(rootCauseInput.value).toBe('Final root cause confirmed: worn bearing')
    })
  })

  // =========================================================================
  // AC4: Action Plan Created via POST with Required Fields
  // =========================================================================
  describe('AC4: Form Submission via POST', () => {
    it('16-3-create-action-plan-from-followup-INT-011: Successful form submission calls POST /api/v1/action-plans with correct payload', async () => {
      // Given: An ActionPlanForm is rendered with pre-filled data
      const prefill = createMockPrefill()

      mockFetch.mockResolvedValue(createMockSuccessResponse())

      render(
        <ActionPlanForm
          open={true}
          onClose={vi.fn()}
          prefill={prefill}
        />
      )

      // Wait for async asset lookup effect to complete
      await waitFor(() => {
        expect(mockSupabaseSingle).toHaveBeenCalled()
      })

      // And: The manager has filled in due_date (required)
      const dueDateInput = screen.getByLabelText(/due date/i)
      fireEvent.change(dueDateInput, { target: { value: '2026-03-01' } })

      // When: The manager clicks the submit button
      const submitButton = screen.getByRole('button', { name: /create|submit|save/i })
      fireEvent.click(submitButton)

      // Then: A fetch POST request is sent to /api/v1/action-plans
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled()
      })

      const fetchCall = mockFetch.mock.calls.find(
        (call: [string, RequestInit]) => call[1]?.method === 'POST'
      )
      expect(fetchCall).toBeTruthy()

      const [url, options] = fetchCall!
      expect(url).toContain('/api/v1/action-plans')

      // And: Headers include authorization and content type
      expect(options.headers).toHaveProperty('Authorization', 'Bearer mock-token')
      expect(options.headers).toHaveProperty('Content-Type', 'application/json')

      // And: Body contains required fields
      const body = JSON.parse(options.body as string)
      expect(body.title).toBeTruthy()
      expect(body.category).toBe('corrective')
      expect(body.priority).toBe('high')
      expect(body.due_date).toBe('2026-03-01')
      expect(body.source_followup_id).toBe('fu-123')
      expect(body.asset_id).toBe('asset-uuid-123')
      expect(body.root_cause).toBeTruthy()

      // And: status is NOT included in the request body (set by server as 'open')
      expect(body.status).toBeUndefined()
    })

    it('16-3-create-action-plan-from-followup-UNIT-011: Form validation prevents submission without title', async () => {
      // Given: An ActionPlanForm is rendered with pre-filled data but the
      //        manager clears the title field
      const prefill = createMockPrefill()

      render(
        <ActionPlanForm
          open={true}
          onClose={vi.fn()}
          prefill={prefill}
        />
      )

      // When: The manager clears the title
      const titleInput = screen.getByLabelText(/title/i)
      fireEvent.change(titleInput, { target: { value: '' } })

      // And: The manager sets a due_date to avoid other validation
      const dueDateInput = screen.getByLabelText(/due date/i)
      fireEvent.change(dueDateInput, { target: { value: '2026-03-01' } })

      // And: The manager attempts to submit the form
      const submitButton = screen.getByRole('button', { name: /create|submit|save/i })
      fireEvent.click(submitButton)

      // Then: The form does not submit (no fetch call)
      await waitFor(() => {
        expect(mockFetch).not.toHaveBeenCalledWith(
          expect.stringContaining('/action-plans'),
          expect.objectContaining({ method: 'POST' })
        )
      })
    })

    it('16-3-create-action-plan-from-followup-UNIT-012: Form validation prevents submission without category', async () => {
      // Given: An ActionPlanForm is rendered and the category field is cleared
      const prefill = createMockPrefill()

      render(
        <ActionPlanForm
          open={true}
          onClose={vi.fn()}
          prefill={prefill}
        />
      )

      // When: The manager clears the category select
      const categorySelect = screen.getByLabelText(/category/i)
      fireEvent.change(categorySelect, { target: { value: '' } })

      // And: Sets due_date
      const dueDateInput = screen.getByLabelText(/due date/i)
      fireEvent.change(dueDateInput, { target: { value: '2026-03-01' } })

      // And: The manager attempts to submit the form
      const submitButton = screen.getByRole('button', { name: /create|submit|save/i })
      fireEvent.click(submitButton)

      // Then: The form does not submit
      await waitFor(() => {
        expect(mockFetch).not.toHaveBeenCalledWith(
          expect.stringContaining('/action-plans'),
          expect.objectContaining({ method: 'POST' })
        )
      })
    })

    it('16-3-create-action-plan-from-followup-UNIT-013: Form validation prevents submission without priority', async () => {
      // Given: An ActionPlanForm is rendered and the priority field is cleared
      const prefill = createMockPrefill()

      render(
        <ActionPlanForm
          open={true}
          onClose={vi.fn()}
          prefill={prefill}
        />
      )

      // When: The manager clears the priority select
      const prioritySelect = screen.getByLabelText(/priority/i)
      fireEvent.change(prioritySelect, { target: { value: '' } })

      // And: Sets due_date
      const dueDateInput = screen.getByLabelText(/due date/i)
      fireEvent.change(dueDateInput, { target: { value: '2026-03-01' } })

      // And: The manager attempts to submit the form
      const submitButton = screen.getByRole('button', { name: /create|submit|save/i })
      fireEvent.click(submitButton)

      // Then: The form does not submit
      await waitFor(() => {
        expect(mockFetch).not.toHaveBeenCalledWith(
          expect.stringContaining('/action-plans'),
          expect.objectContaining({ method: 'POST' })
        )
      })
    })

    it('16-3-create-action-plan-from-followup-UNIT-014: Form validation prevents submission without due_date', async () => {
      // Given: An ActionPlanForm is rendered and the due_date field is empty
      const prefill = createMockPrefill()

      render(
        <ActionPlanForm
          open={true}
          onClose={vi.fn()}
          prefill={prefill}
        />
      )

      // When: due_date is not set (empty by default)
      // And: The manager attempts to submit the form
      const submitButton = screen.getByRole('button', { name: /create|submit|save/i })
      fireEvent.click(submitButton)

      // Then: The form does not submit
      await waitFor(() => {
        expect(mockFetch).not.toHaveBeenCalledWith(
          expect.stringContaining('/action-plans'),
          expect.objectContaining({ method: 'POST' })
        )
      })
    })

    it('16-3-create-action-plan-from-followup-UNIT-015: Submit button shows loading spinner during submission', async () => {
      // Given: An ActionPlanForm is rendered with all required fields filled
      const prefill = createMockPrefill()

      // Mock fetch that returns a pending promise (never resolves during test)
      mockFetch.mockReturnValue(new Promise(() => {}))

      render(
        <ActionPlanForm
          open={true}
          onClose={vi.fn()}
          prefill={prefill}
        />
      )

      // Fill due_date
      const dueDateInput = screen.getByLabelText(/due date/i)
      fireEvent.change(dueDateInput, { target: { value: '2026-03-01' } })

      // When: The manager clicks submit and the API request is in-flight
      const submitButton = screen.getByRole('button', { name: /create|submit|save/i })
      fireEvent.click(submitButton)

      // Then: The submit button displays a loading state and is disabled
      await waitFor(() => {
        const button = screen.getByRole('button', { name: /creat|submit|sav|loading/i })
        expect(button).toBeDisabled()
      })
    })

    it('16-3-create-action-plan-from-followup-UNIT-016: Form displays error message on API failure', async () => {
      // Given: An ActionPlanForm is rendered with all required fields filled
      const prefill = createMockPrefill()

      // And: The POST endpoint returns a 500 error
      mockFetch.mockResolvedValue(createMockErrorResponse(500, 'Internal server error'))

      render(
        <ActionPlanForm
          open={true}
          onClose={vi.fn()}
          prefill={prefill}
        />
      )

      // Fill due_date
      const dueDateInput = screen.getByLabelText(/due date/i)
      fireEvent.change(dueDateInput, { target: { value: '2026-03-01' } })

      // When: The manager submits the form
      const submitButton = screen.getByRole('button', { name: /create|submit|save/i })
      fireEvent.click(submitButton)

      // Then: An error message is displayed in the form
      await waitFor(() => {
        expect(screen.getByText(/failed to create action plan|error/i)).toBeInTheDocument()
      })

      // And: The submit button is re-enabled
      const reEnabledButton = screen.getByRole('button', { name: /create|submit|save/i })
      expect(reEnabledButton).not.toBeDisabled()
    })

    it('16-3-create-action-plan-from-followup-UNIT-017: Form displays error on 401 unauthorized', async () => {
      // Given: An ActionPlanForm is rendered and the session has expired
      mockGetSession.mockResolvedValue(createMockSession(null))

      const prefill = createMockPrefill()

      render(
        <ActionPlanForm
          open={true}
          onClose={vi.fn()}
          prefill={prefill}
        />
      )

      // Fill due_date
      const dueDateInput = screen.getByLabelText(/due date/i)
      fireEvent.change(dueDateInput, { target: { value: '2026-03-01' } })

      // When: The manager submits the form
      const submitButton = screen.getByRole('button', { name: /create|submit|save/i })
      fireEvent.click(submitButton)

      // Then: An authentication error message is displayed
      await waitFor(() => {
        expect(
          screen.getByText(/session.*expired|please log in|authentication/i)
        ).toBeInTheDocument()
      })
    })

    it('16-3-create-action-plan-from-followup-UNIT-018: Form shows success state with CheckCircle2 icon after successful creation', async () => {
      // Given: An ActionPlanForm is rendered and submission succeeds
      const prefill = createMockPrefill()

      mockFetch.mockResolvedValue(createMockSuccessResponse())

      render(
        <ActionPlanForm
          open={true}
          onClose={vi.fn()}
          prefill={prefill}
        />
      )

      // Fill due_date
      const dueDateInput = screen.getByLabelText(/due date/i)
      fireEvent.change(dueDateInput, { target: { value: '2026-03-01' } })

      // When: The API returns a successful response
      const submitButton = screen.getByRole('button', { name: /create|submit|save/i })
      fireEvent.click(submitButton)

      // Then: The form transitions to a success state showing "Action Plan Created"
      await waitFor(() => {
        expect(screen.getByText(/action plan created/i)).toBeInTheDocument()
      })
    })
  })

  // =========================================================================
  // AC5: Follow-Up Updates Without Full Page Reload
  // =========================================================================
  describe('AC5: Success callback and dialog state', () => {
    it('16-3-create-action-plan-from-followup-INT-013: ActionPlanForm onSuccess callback passes created plan data back to parent', async () => {
      // Given: An ActionPlanForm is rendered with an onSuccess callback prop
      const onSuccessSpy = vi.fn()
      const prefill = createMockPrefill()

      mockFetch.mockResolvedValue(createMockSuccessResponse({
        id: 'ap-new',
        title: 'Action Plan: Fix valve',
      }))

      render(
        <ActionPlanForm
          open={true}
          onClose={vi.fn()}
          onSuccess={onSuccessSpy}
          prefill={prefill}
        />
      )

      // Fill due_date
      const dueDateInput = screen.getByLabelText(/due date/i)
      fireEvent.change(dueDateInput, { target: { value: '2026-03-01' } })

      // When: The form submission succeeds
      const submitButton = screen.getByRole('button', { name: /create|submit|save/i })
      fireEvent.click(submitButton)

      // Then: The onSuccess callback is invoked with the created plan data
      await waitFor(() => {
        expect(onSuccessSpy).toHaveBeenCalledWith(
          expect.objectContaining({
            id: 'ap-new',
            title: 'Action Plan: Fix valve',
          })
        )
      })
    })
  })

  // =========================================================================
  // Edge Cases
  // =========================================================================
  describe('Edge Cases', () => {
    it('Form handles null category in prefill by leaving selects at default', () => {
      // Given: A follow-up with null category
      const prefill = createMockPrefill({ category: null })

      // When: The form renders
      render(
        <ActionPlanForm
          open={true}
          onClose={vi.fn()}
          prefill={prefill}
        />
      )

      // Then: Category select is at default/empty, requiring manager to select
      const categorySelect = screen.getByLabelText(/category/i) as HTMLSelectElement
      expect(categorySelect.value).toBe('')
    })

    it('Form handles very long action_summary (200+ chars) with graceful truncation', () => {
      // Given: A follow-up with a very long action_summary (200+ characters)
      const longSummary = 'A'.repeat(200)
      const prefill = createMockPrefill({ actionSummary: longSummary })

      // When: The form renders
      render(
        <ActionPlanForm
          open={true}
          onClose={vi.fn()}
          prefill={prefill}
        />
      )

      // Then: Title pre-fill truncates gracefully without breaking the input field
      const titleInput = screen.getByLabelText(/title/i) as HTMLInputElement
      expect(titleInput.value.length).toBeLessThanOrEqual(80)
    })

    it('Form handles null asset_name and null category with minimal pre-fill', () => {
      // Given: A follow-up with null asset_name and null category
      const prefill = createMockPrefill({ assetName: null, category: null })

      // When: The form renders
      expect(() => {
        render(
          <ActionPlanForm
            open={true}
            onClose={vi.fn()}
            prefill={prefill}
          />
        )
      }).not.toThrow()

      // Then: Only source_followup_id and description from action_summary are pre-filled
      const descriptionInput = screen.getByLabelText(/description/i) as HTMLTextAreaElement
      expect(descriptionInput.value).toContain('Investigate pressure anomaly on main valve')
    })

    it('Empty response body in inbound message pre-fills root_cause as empty string', () => {
      // Given: A follow-up where the inbound message body is empty
      const prefill = createMockPrefill({ responseText: '' })

      // When: The form renders
      render(
        <ActionPlanForm
          open={true}
          onClose={vi.fn()}
          prefill={prefill}
        />
      )

      // Then: root_cause pre-fill is empty string, not "undefined" or "null"
      const rootCauseInput = screen.getByLabelText(/root cause/i) as HTMLTextAreaElement
      expect(rootCauseInput.value).toBe('')
      expect(rootCauseInput.value).not.toBe('undefined')
      expect(rootCauseInput.value).not.toBe('null')
    })
  })
})
