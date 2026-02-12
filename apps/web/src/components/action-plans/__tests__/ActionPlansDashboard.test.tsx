/**
 * Action Plans Dashboard Page Tests (Story 16.5: Action Plans Dashboard)
 *
 * TDD tests — these MUST FAIL until the dashboard page and components are implemented.
 * Tests cover dashboard rendering, grouped sections, loading/error/empty states,
 * and filter persistence in URL params.
 *
 * @see Story 16.5 - Action Plans Dashboard
 * @see AC #1 - Dashboard displays grouped action plans
 * @see AC #4 - Filter persistence in URL params
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'

// ---------------------------------------------------------------------------
// Mocks (BEFORE imports)
// ---------------------------------------------------------------------------

const mockPush = vi.fn()
const mockReplace = vi.fn()
let mockSearchParams = new URLSearchParams()

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush, replace: mockReplace, back: vi.fn(), refresh: vi.fn() }),
  useSearchParams: () => mockSearchParams,
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

interface ActionPlan {
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
}

const createMockActionPlan = (overrides: Partial<ActionPlan> = {}): ActionPlan => ({
  id: 'ap-001',
  title: 'Replace worn bearing on Grinder 5',
  description: 'Bearing shows signs of excessive wear',
  asset_id: 'asset-001',
  asset_name: 'Grinder 5',
  category: 'corrective',
  root_cause: 'Bearing wear due to lack of lubrication',
  corrective_action: 'Replace bearing and improve lubrication schedule',
  preventive_action: 'Monthly bearing inspection',
  source_followup_id: null,
  owner_id: 'user-001',
  owner_email: 'manager@company.com',
  status: 'open',
  priority: 'high',
  due_date: '2026-02-20',
  completed_at: null,
  verified_by: null,
  verified_at: null,
  created_at: '2026-02-10T08:00:00Z',
  updated_at: '2026-02-10T08:00:00Z',
  ...overrides,
})

const createMockListResponse = (
  plans: ActionPlan[],
  overrides: Record<string, unknown> = {}
) => {
  const countsByStatus = plans.reduce(
    (acc, p) => {
      acc[p.status] = (acc[p.status] || 0) + 1
      return acc
    },
    {} as Record<string, number>
  )
  return {
    ok: true,
    status: 200,
    json: async () => ({
      plans,
      total_count: plans.length,
      counts_by_status: countsByStatus,
      ...overrides,
    }),
  }
}

const createMockErrorResponse = (status: number, detail: string = `Error ${status}`) => ({
  ok: false,
  status,
  json: async () => ({ detail }),
})

const createMockSession = (accessToken: string | null = 'mock-token') => ({
  data: {
    session: accessToken !== null
      ? { access_token: accessToken, user: { id: 'user-001' } }
      : null,
  },
})

// Sample plans across different statuses
const samplePlans: ActionPlan[] = [
  createMockActionPlan({ id: 'ap-open-1', title: 'Fix valve alignment', status: 'open', priority: 'high' }),
  createMockActionPlan({ id: 'ap-open-2', title: 'Calibrate sensor A3', status: 'open', priority: 'medium' }),
  createMockActionPlan({ id: 'ap-open-3', title: 'Replace filter housing', status: 'open', priority: 'critical' }),
  createMockActionPlan({ id: 'ap-ip-1', title: 'Overhaul motor windings', status: 'in_progress', priority: 'high' }),
  createMockActionPlan({ id: 'ap-ip-2', title: 'Rebuild hydraulic pump', status: 'in_progress', priority: 'medium' }),
  createMockActionPlan({ id: 'ap-comp-1', title: 'Replace bearing assembly', status: 'completed', priority: 'low' }),
  createMockActionPlan({ id: 'ap-ver-1', title: 'Update safety guard', status: 'verified', priority: 'high' }),
  createMockActionPlan({ id: 'ap-ver-2', title: 'Inspect cooling system', status: 'verified', priority: 'medium' }),
]

// ---------------------------------------------------------------------------
// Import page component AFTER mocks are set up
// ---------------------------------------------------------------------------

// The page does not exist yet — this import will fail until it's created.
import ActionPlansDashboardPage from '@/app/action-plans/page'

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: Action Plans Dashboard Page (Story 16.5)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockReset()
    mockGetSession.mockReset()
    mockPush.mockClear()
    mockReplace.mockClear()
    mockSearchParams = new URLSearchParams()

    // Default: authenticated session
    mockGetSession.mockResolvedValue(createMockSession('mock-token'))

    // Default: return sample plans
    mockFetch.mockResolvedValue(createMockListResponse(samplePlans))

    // Fix "today" for deterministic calculations
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-02-12T00:00:00Z'))
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  // =========================================================================
  // AC1: Dashboard renders grouped sections
  // =========================================================================
  describe('AC1: Dashboard rendering', () => {
    it('16-5-action-plans-dashboard-UNIT-001: Dashboard page renders grouped sections with correct status headers', async () => {
      // Given: The API returns plans across all 4 status groups
      // When: The dashboard page renders
      render(<ActionPlansDashboardPage />)

      // Then: Wait for plans to load and verify section headers exist
      await waitFor(() => {
        expect(screen.getByText(/open\s*\(3\)/i)).toBeInTheDocument()
      })

      // And: All four status group headers are displayed
      expect(screen.getByText(/open\s*\(3\)/i)).toBeInTheDocument()
      expect(screen.getByText(/in progress\s*\(2\)/i)).toBeInTheDocument()
      expect(screen.getByText(/completed\s*\(1\)/i)).toBeInTheDocument()
      expect(screen.getByText(/verified\s*\(2\)/i)).toBeInTheDocument()
    })

    it('16-5-action-plans-dashboard-UNIT-006: Dashboard page header shows "Action Plans" title with total active count badge', async () => {
      // Given: The API returns plans with a total count
      // When: The dashboard page renders
      render(<ActionPlansDashboardPage />)

      // Then: The page header shows "Action Plans" title
      await waitFor(() => {
        expect(screen.getByText(/action plans/i)).toBeInTheDocument()
      })

      // And: A count badge shows the total number of active plans
      //      (active = open + in_progress = 3 + 2 = 5)
      expect(screen.getByText('5')).toBeInTheDocument()
    })

    it('16-5-action-plans-dashboard-UNIT-007: Dashboard renders loading skeleton cards while fetching', () => {
      // Given: The API request has not yet resolved
      mockFetch.mockReturnValue(new Promise(() => {})) // never resolves

      // When: The dashboard renders
      const { container } = render(<ActionPlansDashboardPage />)

      // Then: Skeleton loading elements are visible
      const skeletons = container.querySelectorAll('[class*="animate-pulse"], [class*="skeleton"]')
      expect(skeletons.length).toBeGreaterThan(0)
    })

    it('16-5-action-plans-dashboard-UNIT-008: Dashboard renders empty state when no plans exist', async () => {
      // Given: The API returns zero plans
      mockFetch.mockResolvedValue(createMockListResponse([]))

      // When: The dashboard renders
      render(<ActionPlansDashboardPage />)

      // Then: An empty state message is displayed
      await waitFor(() => {
        expect(
          screen.getByText(/no action plans found|create action plans from follow-up/i)
        ).toBeInTheDocument()
      })
    })

    it('16-5-action-plans-dashboard-UNIT-009: Dashboard renders error state with retry button on API failure', async () => {
      // Given: The API returns a 500 error
      mockFetch.mockResolvedValue(createMockErrorResponse(500, 'Internal server error'))

      // When: The dashboard renders
      render(<ActionPlansDashboardPage />)

      // Then: An error message is displayed
      await waitFor(() => {
        expect(screen.getByText(/error|failed to load/i)).toBeInTheDocument()
      })

      // And: A retry button is available
      expect(screen.getByRole('button', { name: /retry|try again/i })).toBeInTheDocument()
    })

    it('16-5-action-plans-dashboard-UNIT-010: Dashboard handles auth error when session is expired', async () => {
      // Given: The session has expired (no access token)
      mockGetSession.mockResolvedValue(createMockSession(null))

      // When: The dashboard renders
      render(<ActionPlansDashboardPage />)

      // Then: An authentication error message is displayed
      await waitFor(() => {
        expect(
          screen.getByText(/session.*expired|please log in|authentication/i)
        ).toBeInTheDocument()
      })
    })

    it('16-5-action-plans-dashboard-UNIT-011: Dashboard groups plans correctly when some status groups are empty', async () => {
      // Given: The API returns plans only in open and in_progress statuses
      const partialPlans = [
        createMockActionPlan({ id: 'ap-1', status: 'open', title: 'Plan A' }),
        createMockActionPlan({ id: 'ap-2', status: 'in_progress', title: 'Plan B' }),
      ]
      mockFetch.mockResolvedValue(createMockListResponse(partialPlans))

      // When: The dashboard renders
      render(<ActionPlansDashboardPage />)

      // Then: Only populated sections are shown (or empty sections are gracefully handled)
      await waitFor(() => {
        expect(screen.getByText('Plan A')).toBeInTheDocument()
        expect(screen.getByText('Plan B')).toBeInTheDocument()
      })

      // And: The Open section shows count 1
      expect(screen.getByText(/open\s*\(1\)/i)).toBeInTheDocument()

      // And: The In Progress section shows count 1
      expect(screen.getByText(/in progress\s*\(1\)/i)).toBeInTheDocument()
    })

    it('Retry button re-fetches plans on click', async () => {
      // Given: The first fetch fails
      mockFetch.mockResolvedValueOnce(createMockErrorResponse(500))

      render(<ActionPlansDashboardPage />)

      await waitFor(() => {
        expect(screen.getByText(/error|failed/i)).toBeInTheDocument()
      })

      // When: The retry button is clicked and the second fetch succeeds
      mockFetch.mockResolvedValueOnce(createMockListResponse(samplePlans))

      const retryButton = screen.getByRole('button', { name: /retry|try again/i })
      fireEvent.click(retryButton)

      // Then: The plans are displayed
      await waitFor(() => {
        expect(screen.getByText('Fix valve alignment')).toBeInTheDocument()
      })
    })
  })

  // =========================================================================
  // AC4: Filter persistence in URL params
  // =========================================================================
  describe('AC4: Filter persistence in URL params', () => {
    it('16-5-action-plans-dashboard-UNIT-039: Status filter dropdown changes displayed plans', async () => {
      // Given: The dashboard is rendered with all plans
      render(<ActionPlansDashboardPage />)

      await waitFor(() => {
        expect(screen.getByText('Fix valve alignment')).toBeInTheDocument()
      })

      // When: The status filter is changed to "open"
      const statusFilter = screen.getByLabelText(/status/i) || screen.getByRole('combobox', { name: /status/i })
      fireEvent.change(statusFilter, { target: { value: 'open' } })

      // Then: The URL is updated with status=open
      await waitFor(() => {
        expect(mockReplace).toHaveBeenCalledWith(
          expect.stringContaining('status=open')
        )
      })
    })

    it('16-5-action-plans-dashboard-UNIT-040: Priority filter updates URL params', async () => {
      // Given: The dashboard is rendered
      render(<ActionPlansDashboardPage />)

      await waitFor(() => {
        expect(screen.getByText('Fix valve alignment')).toBeInTheDocument()
      })

      // When: The priority filter is changed to "high"
      const priorityFilter = screen.getByLabelText(/priority/i) || screen.getByRole('combobox', { name: /priority/i })
      fireEvent.change(priorityFilter, { target: { value: 'high' } })

      // Then: The URL is updated with priority=high
      await waitFor(() => {
        expect(mockReplace).toHaveBeenCalledWith(
          expect.stringContaining('priority=high')
        )
      })
    })

    it('16-5-action-plans-dashboard-UNIT-041: Setting filter to "all" removes param from URL', async () => {
      // Given: The dashboard has a status filter applied
      mockSearchParams = new URLSearchParams('status=open')

      render(<ActionPlansDashboardPage />)

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled()
      })

      // When: The status filter is changed back to "all"
      const statusFilter = screen.getByLabelText(/status/i) || screen.getByRole('combobox', { name: /status/i })
      fireEvent.change(statusFilter, { target: { value: 'all' } })

      // Then: The URL does not contain status param
      await waitFor(() => {
        expect(mockReplace).toHaveBeenCalledWith(
          expect.not.stringContaining('status=')
        )
      })
    })

    it('16-5-action-plans-dashboard-UNIT-042: Multiple filters can be applied simultaneously', async () => {
      // Given: The dashboard is rendered
      render(<ActionPlansDashboardPage />)

      await waitFor(() => {
        expect(screen.getByText('Fix valve alignment')).toBeInTheDocument()
      })

      // When: Both status and priority filters are applied
      const statusFilter = screen.getByLabelText(/status/i) || screen.getByRole('combobox', { name: /status/i })
      fireEvent.change(statusFilter, { target: { value: 'open' } })

      const priorityFilter = screen.getByLabelText(/priority/i) || screen.getByRole('combobox', { name: /priority/i })
      fireEvent.change(priorityFilter, { target: { value: 'high' } })

      // Then: The URL contains both filter params
      await waitFor(() => {
        expect(mockReplace).toHaveBeenCalledWith(
          expect.stringMatching(/status=open.*priority=high|priority=high.*status=open/)
        )
      })
    })

    it('16-5-action-plans-dashboard-UNIT-043: Dashboard reads initial filter state from URL params on mount', async () => {
      // Given: The URL contains filter params
      mockSearchParams = new URLSearchParams('status=in_progress&priority=critical')

      // When: The dashboard renders
      render(<ActionPlansDashboardPage />)

      // Then: The fetch call includes the filter params from URL
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled()
      })

      const fetchCall = mockFetch.mock.calls[0]
      const url = fetchCall[0] as string
      expect(url).toContain('status=in_progress')
      expect(url).toContain('priority=critical')
    })

    it('16-5-action-plans-dashboard-UNIT-044: Owner filter updates URL params', async () => {
      // Given: The dashboard is rendered
      render(<ActionPlansDashboardPage />)

      await waitFor(() => {
        expect(screen.getByText('Fix valve alignment')).toBeInTheDocument()
      })

      // When: The owner filter is applied
      const ownerFilter = screen.getByLabelText(/owner/i) || screen.getByRole('combobox', { name: /owner/i })
      fireEvent.change(ownerFilter, { target: { value: 'user-001' } })

      // Then: The URL is updated with owner_id param
      await waitFor(() => {
        expect(mockReplace).toHaveBeenCalledWith(
          expect.stringContaining('owner_id=user-001')
        )
      })
    })

    it('16-5-action-plans-dashboard-INT-007: Filter changes trigger new API fetch', async () => {
      // Given: The dashboard is rendered with initial data
      render(<ActionPlansDashboardPage />)

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(1)
      })

      // When: A filter is changed
      const statusFilter = screen.getByLabelText(/status/i) || screen.getByRole('combobox', { name: /status/i })
      fireEvent.change(statusFilter, { target: { value: 'open' } })

      // Then: A new fetch call is made with the filter param
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(2)
      })

      const latestCall = mockFetch.mock.calls[1]
      expect(latestCall[0]).toContain('status=open')
    })

    it('16-5-action-plans-dashboard-INT-008: Filtered results update the grouped display', async () => {
      // Given: Initial load shows all plans
      render(<ActionPlansDashboardPage />)

      await waitFor(() => {
        expect(screen.getByText('Fix valve alignment')).toBeInTheDocument()
      })

      // When: Status filter is set to "completed" and API returns only completed plans
      const completedPlan = createMockActionPlan({ id: 'ap-filtered', title: 'Filtered completed plan', status: 'completed' })
      mockFetch.mockResolvedValueOnce(createMockListResponse([completedPlan]))

      const statusFilter = screen.getByLabelText(/status/i) || screen.getByRole('combobox', { name: /status/i })
      fireEvent.change(statusFilter, { target: { value: 'completed' } })

      // Then: Only the filtered plan is shown
      await waitFor(() => {
        expect(screen.getByText('Filtered completed plan')).toBeInTheDocument()
      })
    })

    it('16-5-action-plans-dashboard-INT-009: Browser back/forward preserves filter state', async () => {
      // Given: The URL has filter params from browser history
      mockSearchParams = new URLSearchParams('priority=high')

      // When: The dashboard mounts
      render(<ActionPlansDashboardPage />)

      // Then: The API fetch includes the priority filter
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled()
      })

      const fetchUrl = mockFetch.mock.calls[0][0] as string
      expect(fetchUrl).toContain('priority=high')
    })

    it('16-5-action-plans-dashboard-INT-010: Asset filter syncs to URL and triggers re-fetch', async () => {
      // Given: The dashboard is rendered
      render(<ActionPlansDashboardPage />)

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled()
      })

      // When: An asset filter is applied
      const assetFilter = screen.getByLabelText(/asset/i) || screen.getByRole('combobox', { name: /asset/i })
      fireEvent.change(assetFilter, { target: { value: 'asset-001' } })

      // Then: The URL is updated with asset_id
      await waitFor(() => {
        expect(mockReplace).toHaveBeenCalledWith(
          expect.stringContaining('asset_id=asset-001')
        )
      })
    })
  })
})
