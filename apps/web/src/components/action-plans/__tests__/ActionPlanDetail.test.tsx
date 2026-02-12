/**
 * ActionPlanDetail Component Tests (Story 16.5: Action Plans Dashboard)
 *
 * TDD tests — these MUST FAIL until the ActionPlanDetail component is implemented.
 * Tests cover detail view rendering, progress updates timeline, status changes,
 * and add-update functionality.
 *
 * @see Story 16.5 - Action Plans Dashboard
 * @see AC #3 - Detail view with updates and status changes
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'

// ---------------------------------------------------------------------------
// Mocks (BEFORE imports)
// ---------------------------------------------------------------------------

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), back: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => '/action-plans',
  useParams: () => ({}),
}))

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

interface ActionPlanUpdate {
  id: string
  action_plan_id: string
  author_id: string
  author_email: string
  update_text: string | null
  status_change: string | null
  created_at: string
}

interface ActionPlanWithUpdates {
  id: string
  title: string
  description: string | null
  asset_id: string | null
  asset_name: string | null
  category: string
  root_cause: string | null
  corrective_action: string | null
  preventive_action: string | null
  source_followup_id: string | null
  owner_id: string
  owner_email: string
  status: 'open' | 'in_progress' | 'completed' | 'verified'
  priority: 'low' | 'medium' | 'high' | 'critical'
  due_date: string | null
  completed_at: string | null
  verified_by: string | null
  verified_at: string | null
  created_at: string
  updated_at: string
  updates: ActionPlanUpdate[]
}

const createMockUpdate = (overrides: Partial<ActionPlanUpdate> = {}): ActionPlanUpdate => ({
  id: 'upd-001',
  action_plan_id: 'ap-001',
  author_id: 'user-002',
  author_email: 'engineer@company.com',
  update_text: 'Ordered replacement parts from supplier',
  status_change: null,
  created_at: '2026-02-11T10:00:00Z',
  ...overrides,
})

const createMockPlanWithUpdates = (
  overrides: Partial<ActionPlanWithUpdates> = {}
): ActionPlanWithUpdates => ({
  id: 'ap-001',
  title: 'Replace worn bearing on Grinder 5',
  description: 'Bearing shows signs of excessive wear during routine inspection',
  asset_id: 'asset-001',
  asset_name: 'Grinder 5',
  category: 'corrective',
  root_cause: 'Bearing wear due to lack of lubrication',
  corrective_action: 'Replace bearing and improve lubrication schedule',
  preventive_action: 'Monthly bearing inspection and lubrication check',
  source_followup_id: 'fu-001',
  owner_id: 'user-001',
  owner_email: 'manager@company.com',
  status: 'in_progress',
  priority: 'high',
  due_date: '2026-02-20',
  completed_at: null,
  verified_by: null,
  verified_at: null,
  created_at: '2026-02-10T08:00:00Z',
  updated_at: '2026-02-11T10:00:00Z',
  updates: [
    createMockUpdate({
      id: 'upd-002',
      update_text: 'Parts arrived, scheduling replacement',
      status_change: null,
      created_at: '2026-02-12T09:00:00Z',
    }),
    createMockUpdate({
      id: 'upd-001',
      update_text: 'Ordered replacement parts from supplier',
      status_change: 'open -> in_progress',
      created_at: '2026-02-11T10:00:00Z',
    }),
  ],
  ...overrides,
})

const createMockSession = (accessToken: string | null = 'mock-token') => ({
  data: {
    session: accessToken !== null
      ? { access_token: accessToken, user: { id: 'user-001' } }
      : null,
  },
})

// ---------------------------------------------------------------------------
// Import components AFTER mocks are set up
// ---------------------------------------------------------------------------

// These components do not exist yet — imports will fail until they're created.
import { ActionPlanDetail } from '../ActionPlanDetail'
import { UpdateTimeline } from '../UpdateTimeline'

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: ActionPlanDetail Component (Story 16.5)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockReset()
    mockGetSession.mockReset()

    mockGetSession.mockResolvedValue(createMockSession('mock-token'))

    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-02-12T12:00:00Z'))
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  // =========================================================================
  // AC3: Detail view displays plan information
  // =========================================================================
  describe('AC3: Detail view rendering', () => {
    it('16-5-action-plans-dashboard-UNIT-021: Detail view displays plan title with status badge', () => {
      // Given: A plan with status "in_progress"
      const plan = createMockPlanWithUpdates({ status: 'in_progress' })

      // When: The detail view renders
      render(<ActionPlanDetail plan={plan} open={true} onClose={vi.fn()} />)

      // Then: The title is displayed
      expect(screen.getByText('Replace worn bearing on Grinder 5')).toBeInTheDocument()

      // And: A status badge showing "In Progress" is visible
      expect(screen.getByText(/in progress/i)).toBeInTheDocument()
    })

    it('16-5-action-plans-dashboard-UNIT-022: Detail view displays full description', () => {
      // Given: A plan with a description
      const plan = createMockPlanWithUpdates({
        description: 'Bearing shows signs of excessive wear during routine inspection',
      })

      // When: The detail view renders
      render(<ActionPlanDetail plan={plan} open={true} onClose={vi.fn()} />)

      // Then: The full description is shown
      expect(
        screen.getByText('Bearing shows signs of excessive wear during routine inspection')
      ).toBeInTheDocument()
    })

    it('16-5-action-plans-dashboard-UNIT-023: Detail view displays root cause section', () => {
      // Given: A plan with a root cause
      const plan = createMockPlanWithUpdates({
        root_cause: 'Bearing wear due to lack of lubrication',
      })

      // When: The detail view renders
      render(<ActionPlanDetail plan={plan} open={true} onClose={vi.fn()} />)

      // Then: The root cause section is displayed with label and content
      expect(screen.getByText(/root cause/i)).toBeInTheDocument()
      expect(
        screen.getByText('Bearing wear due to lack of lubrication')
      ).toBeInTheDocument()
    })

    it('16-5-action-plans-dashboard-UNIT-024: Detail view displays corrective action section', () => {
      // Given: A plan with a corrective action
      const plan = createMockPlanWithUpdates({
        corrective_action: 'Replace bearing and improve lubrication schedule',
      })

      // When: The detail view renders
      render(<ActionPlanDetail plan={plan} open={true} onClose={vi.fn()} />)

      // Then: The corrective action section is displayed
      expect(screen.getByText(/corrective action/i)).toBeInTheDocument()
      expect(
        screen.getByText('Replace bearing and improve lubrication schedule')
      ).toBeInTheDocument()
    })

    it('16-5-action-plans-dashboard-UNIT-025: Detail view displays preventive action section', () => {
      // Given: A plan with a preventive action
      const plan = createMockPlanWithUpdates({
        preventive_action: 'Monthly bearing inspection and lubrication check',
      })

      // When: The detail view renders
      render(<ActionPlanDetail plan={plan} open={true} onClose={vi.fn()} />)

      // Then: The preventive action section is displayed
      expect(screen.getByText(/preventive action/i)).toBeInTheDocument()
      expect(
        screen.getByText('Monthly bearing inspection and lubrication check')
      ).toBeInTheDocument()
    })

    it('16-5-action-plans-dashboard-UNIT-026: Detail view shows asset name and owner', () => {
      // Given: A plan with an asset and owner
      const plan = createMockPlanWithUpdates({
        asset_name: 'Grinder 5',
        owner_email: 'manager@company.com',
      })

      // When: The detail view renders
      render(<ActionPlanDetail plan={plan} open={true} onClose={vi.fn()} />)

      // Then: Asset name and owner are displayed
      expect(screen.getByText('Grinder 5')).toBeInTheDocument()
      expect(screen.getByText('manager@company.com')).toBeInTheDocument()
    })

    it('16-5-action-plans-dashboard-UNIT-027: Detail view shows priority and due date', () => {
      // Given: A plan with priority and due date
      const plan = createMockPlanWithUpdates({
        priority: 'high',
        due_date: '2026-02-20',
      })

      // When: The detail view renders
      render(<ActionPlanDetail plan={plan} open={true} onClose={vi.fn()} />)

      // Then: Priority is displayed
      expect(screen.getByText(/high/i)).toBeInTheDocument()

      // And: Due date is displayed
      expect(screen.getByText(/feb.*20|2026-02-20|02\/20/i)).toBeInTheDocument()
    })

    it('16-5-action-plans-dashboard-UNIT-028: Detail view shows "View Source Follow-Up" link when source_followup_id exists', () => {
      // Given: A plan linked to a follow-up
      const plan = createMockPlanWithUpdates({
        source_followup_id: 'fu-001',
      })

      // When: The detail view renders
      render(<ActionPlanDetail plan={plan} open={true} onClose={vi.fn()} />)

      // Then: A "View Source Follow-Up" link/button is visible
      expect(
        screen.getByText(/view source follow-up|source follow-up/i)
      ).toBeInTheDocument()
    })

    it('16-5-action-plans-dashboard-UNIT-029: Detail view hides follow-up link when source_followup_id is null', () => {
      // Given: A plan with no source follow-up
      const plan = createMockPlanWithUpdates({
        source_followup_id: null,
      })

      // When: The detail view renders
      render(<ActionPlanDetail plan={plan} open={true} onClose={vi.fn()} />)

      // Then: No "View Source Follow-Up" link is visible
      expect(
        screen.queryByText(/view source follow-up|source follow-up/i)
      ).not.toBeInTheDocument()
    })

    it('16-5-action-plans-dashboard-UNIT-030: Detail view shows created_at and updated_at dates', () => {
      // Given: A plan with creation and update timestamps
      const plan = createMockPlanWithUpdates({
        created_at: '2026-02-10T08:00:00Z',
        updated_at: '2026-02-11T10:00:00Z',
      })

      // When: The detail view renders
      render(<ActionPlanDetail plan={plan} open={true} onClose={vi.fn()} />)

      // Then: Created and updated dates are shown
      expect(screen.getByText(/feb.*10|2026-02-10/i)).toBeInTheDocument()
    })
  })

  // =========================================================================
  // AC3: Progress updates timeline
  // =========================================================================
  describe('AC3: Progress updates timeline', () => {
    it('16-5-action-plans-dashboard-UNIT-031: UpdateTimeline renders updates in reverse chronological order', () => {
      // Given: A list of updates with different timestamps
      const updates = [
        createMockUpdate({
          id: 'upd-1',
          update_text: 'First update',
          created_at: '2026-02-11T10:00:00Z',
        }),
        createMockUpdate({
          id: 'upd-2',
          update_text: 'Second update',
          created_at: '2026-02-12T09:00:00Z',
        }),
      ]

      // When: The timeline renders
      render(<UpdateTimeline updates={updates} />)

      // Then: Both updates are visible
      expect(screen.getByText('First update')).toBeInTheDocument()
      expect(screen.getByText('Second update')).toBeInTheDocument()

      // And: Most recent update appears first in the DOM
      const items = screen.getAllByText(/update/i)
      const secondIdx = items.findIndex(el => el.textContent?.includes('Second update'))
      const firstIdx = items.findIndex(el => el.textContent?.includes('First update'))
      expect(secondIdx).toBeLessThan(firstIdx)
    })

    it('16-5-action-plans-dashboard-UNIT-032: UpdateTimeline shows author email for each update', () => {
      // Given: Updates from different authors
      const updates = [
        createMockUpdate({
          id: 'upd-1',
          author_email: 'engineer@company.com',
          update_text: 'Update from engineer',
        }),
        createMockUpdate({
          id: 'upd-2',
          author_email: 'supervisor@company.com',
          update_text: 'Update from supervisor',
        }),
      ]

      // When: The timeline renders
      render(<UpdateTimeline updates={updates} />)

      // Then: Both author emails are displayed
      expect(screen.getByText('engineer@company.com')).toBeInTheDocument()
      expect(screen.getByText('supervisor@company.com')).toBeInTheDocument()
    })

    it('16-5-action-plans-dashboard-UNIT-033: UpdateTimeline shows status change badge when present', () => {
      // Given: An update with a status change
      const updates = [
        createMockUpdate({
          id: 'upd-1',
          status_change: 'open -> in_progress',
          update_text: 'Started working on this',
        }),
      ]

      // When: The timeline renders
      render(<UpdateTimeline updates={updates} />)

      // Then: The status change is displayed
      expect(screen.getByText(/open.*→.*in.progress|open -> in_progress|status:.*open.*in.progress/i)).toBeInTheDocument()
    })

    it('16-5-action-plans-dashboard-UNIT-034: UpdateTimeline shows relative timestamp', () => {
      // Given: An update created 2 hours ago (now is 2026-02-12T12:00:00Z)
      const updates = [
        createMockUpdate({
          id: 'upd-1',
          created_at: '2026-02-12T10:00:00Z',
          update_text: 'Recent update',
        }),
      ]

      // When: The timeline renders
      render(<UpdateTimeline updates={updates} />)

      // Then: The relative timestamp is shown (e.g., "2h ago")
      expect(screen.getByText(/2h ago|2 hours? ago/i)).toBeInTheDocument()
    })

    it('16-5-action-plans-dashboard-UNIT-035: UpdateTimeline renders empty state when no updates exist', () => {
      // Given: No updates
      const updates: ActionPlanUpdate[] = []

      // When: The timeline renders
      render(<UpdateTimeline updates={updates} />)

      // Then: An empty/no-updates message is displayed
      expect(screen.getByText(/no updates|no progress updates/i)).toBeInTheDocument()
    })
  })

  // =========================================================================
  // AC3: Add progress update
  // =========================================================================
  describe('AC3: Add progress update', () => {
    it('16-5-action-plans-dashboard-UNIT-036: Detail view has "Add Update" form with text input', () => {
      // Given: A plan detail view is open
      const plan = createMockPlanWithUpdates()

      // When: The detail view renders
      render(<ActionPlanDetail plan={plan} open={true} onClose={vi.fn()} />)

      // Then: A text input for adding updates is visible
      expect(
        screen.getByPlaceholderText(/add.*update|progress.*update|enter.*update/i)
      ).toBeInTheDocument()

      // And: A submit button for the update is visible
      expect(
        screen.getByRole('button', { name: /add update|submit|post/i })
      ).toBeInTheDocument()
    })

    it('16-5-action-plans-dashboard-UNIT-037: Adding update calls POST /api/v1/action-plans/{id}/updates', async () => {
      // Given: A plan detail view is open
      const plan = createMockPlanWithUpdates({ id: 'ap-123' })

      mockFetch.mockResolvedValue({
        ok: true,
        status: 201,
        json: async () => createMockUpdate({
          id: 'upd-new',
          update_text: 'Bearing replacement complete',
        }),
      })

      render(<ActionPlanDetail plan={plan} open={true} onClose={vi.fn()} />)

      // When: The user types an update and submits
      const textInput = screen.getByPlaceholderText(/add.*update|progress.*update|enter.*update/i)
      fireEvent.change(textInput, { target: { value: 'Bearing replacement complete' } })

      const submitBtn = screen.getByRole('button', { name: /add update|submit|post/i })
      fireEvent.click(submitBtn)

      // Then: A POST request is made to the correct endpoint
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/action-plans/ap-123/updates'),
          expect.objectContaining({
            method: 'POST',
            headers: expect.objectContaining({
              'Authorization': 'Bearer mock-token',
              'Content-Type': 'application/json',
            }),
          })
        )
      })

      // And: The body contains the update text
      const fetchCall = mockFetch.mock.calls.find(
        (c: [string, RequestInit]) => c[0].includes('/updates') && c[1]?.method === 'POST'
      )
      const body = JSON.parse(fetchCall![1].body as string)
      expect(body.update_text).toBe('Bearing replacement complete')
    })

    it('16-5-action-plans-dashboard-UNIT-038: Add update form includes optional status change dropdown', () => {
      // Given: A plan detail view is open with status "open"
      const plan = createMockPlanWithUpdates({ status: 'open' })

      // When: The detail view renders
      render(<ActionPlanDetail plan={plan} open={true} onClose={vi.fn()} />)

      // Then: A status change dropdown is available alongside the update input
      const statusDropdown = screen.getByLabelText(/status.*change|change.*status/i) ||
        screen.getByRole('combobox', { name: /status/i })
      expect(statusDropdown).toBeInTheDocument()
    })
  })

  // =========================================================================
  // AC3: Status change actions
  // =========================================================================
  describe('AC3: Status change actions', () => {
    it('16-5-action-plans-dashboard-INT-005: "Mark In Progress" button calls PATCH with status update', async () => {
      // Given: A plan with status "open"
      const plan = createMockPlanWithUpdates({ id: 'ap-status-test', status: 'open' })

      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ ...plan, status: 'in_progress' }),
      })

      render(<ActionPlanDetail plan={plan} open={true} onClose={vi.fn()} />)

      // When: The "Mark In Progress" button is clicked
      const markInProgressBtn = screen.getByRole('button', { name: /mark in progress|start/i })
      fireEvent.click(markInProgressBtn)

      // Then: A PATCH request is made with status: 'in_progress'
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/action-plans/ap-status-test'),
          expect.objectContaining({
            method: 'PATCH',
          })
        )
      })

      const patchCall = mockFetch.mock.calls.find(
        (c: [string, RequestInit]) => c[1]?.method === 'PATCH'
      )
      const body = JSON.parse(patchCall![1].body as string)
      expect(body.status).toBe('in_progress')
    })

    it('16-5-action-plans-dashboard-INT-006: "Mark Completed" button calls PATCH with completed status', async () => {
      // Given: A plan with status "in_progress"
      const plan = createMockPlanWithUpdates({ id: 'ap-complete-test', status: 'in_progress' })

      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ ...plan, status: 'completed' }),
      })

      render(<ActionPlanDetail plan={plan} open={true} onClose={vi.fn()} />)

      // When: The "Mark Completed" button is clicked
      const markCompletedBtn = screen.getByRole('button', { name: /mark completed|complete/i })
      fireEvent.click(markCompletedBtn)

      // Then: A PATCH request is made with status: 'completed'
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/action-plans/ap-complete-test'),
          expect.objectContaining({
            method: 'PATCH',
          })
        )
      })

      const patchCall = mockFetch.mock.calls.find(
        (c: [string, RequestInit]) => c[1]?.method === 'PATCH'
      )
      const body = JSON.parse(patchCall![1].body as string)
      expect(body.status).toBe('completed')
    })

    it('Detail view shows "Verify" button for completed plans', () => {
      // Given: A plan with status "completed"
      const plan = createMockPlanWithUpdates({ status: 'completed' })

      // When: The detail view renders
      render(<ActionPlanDetail plan={plan} open={true} onClose={vi.fn()} />)

      // Then: A "Verify" button is visible
      expect(screen.getByRole('button', { name: /verify/i })).toBeInTheDocument()
    })

    it('Verify button calls POST /api/v1/action-plans/{id}/verify', async () => {
      // Given: A completed plan
      const plan = createMockPlanWithUpdates({ id: 'ap-verify', status: 'completed' })

      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ ...plan, status: 'verified' }),
      })

      render(<ActionPlanDetail plan={plan} open={true} onClose={vi.fn()} />)

      // When: The verify button is clicked
      const verifyBtn = screen.getByRole('button', { name: /verify/i })
      fireEvent.click(verifyBtn)

      // Then: A POST request is made to the verify endpoint
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/action-plans/ap-verify/verify'),
          expect.objectContaining({
            method: 'POST',
          })
        )
      })
    })

    it('Open plan shows "Mark In Progress" but not "Mark Completed" or "Verify"', () => {
      // Given: An open plan
      const plan = createMockPlanWithUpdates({ status: 'open' })

      // When: The detail view renders
      render(<ActionPlanDetail plan={plan} open={true} onClose={vi.fn()} />)

      // Then: "Mark In Progress" is visible
      expect(screen.getByRole('button', { name: /mark in progress|start/i })).toBeInTheDocument()

      // And: "Mark Completed" and "Verify" are NOT visible
      expect(screen.queryByRole('button', { name: /mark completed|complete/i })).not.toBeInTheDocument()
      expect(screen.queryByRole('button', { name: /verify/i })).not.toBeInTheDocument()
    })

    it('In-progress plan shows "Mark Completed" but not "Mark In Progress" or "Verify"', () => {
      // Given: An in-progress plan
      const plan = createMockPlanWithUpdates({ status: 'in_progress' })

      // When: The detail view renders
      render(<ActionPlanDetail plan={plan} open={true} onClose={vi.fn()} />)

      // Then: "Mark Completed" is visible
      expect(screen.getByRole('button', { name: /mark completed|complete/i })).toBeInTheDocument()

      // And: "Mark In Progress" is NOT visible
      expect(screen.queryByRole('button', { name: /mark in progress|start/i })).not.toBeInTheDocument()
    })

    it('Verified plan shows no status change buttons', () => {
      // Given: A verified plan
      const plan = createMockPlanWithUpdates({ status: 'verified' })

      // When: The detail view renders
      render(<ActionPlanDetail plan={plan} open={true} onClose={vi.fn()} />)

      // Then: No status change buttons are visible
      expect(screen.queryByRole('button', { name: /mark in progress|start/i })).not.toBeInTheDocument()
      expect(screen.queryByRole('button', { name: /mark completed|complete/i })).not.toBeInTheDocument()
      expect(screen.queryByRole('button', { name: /verify/i })).not.toBeInTheDocument()
    })
  })

  // =========================================================================
  // Dialog behavior
  // =========================================================================
  describe('Dialog behavior', () => {
    it('Detail dialog calls onClose when close button is clicked', () => {
      // Given: A detail dialog is open
      const onClose = vi.fn()
      const plan = createMockPlanWithUpdates()

      render(<ActionPlanDetail plan={plan} open={true} onClose={onClose} />)

      // When: The close button is clicked
      const closeButton = screen.getByRole('button', { name: /close|×|dismiss/i })
      fireEvent.click(closeButton)

      // Then: onClose is called
      expect(onClose).toHaveBeenCalled()
    })

    it('Detail dialog is not visible when open=false', () => {
      // Given: open prop is false
      const plan = createMockPlanWithUpdates()

      // When: The detail component renders with open=false
      render(<ActionPlanDetail plan={plan} open={false} onClose={vi.fn()} />)

      // Then: The plan title is not visible
      expect(screen.queryByText('Replace worn bearing on Grinder 5')).not.toBeInTheDocument()
    })
  })
})
