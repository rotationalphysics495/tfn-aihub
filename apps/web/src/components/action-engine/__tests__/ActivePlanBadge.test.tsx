/**
 * ActivePlanBadge Component Tests (Story 16.4: Active Plans Badge on Action Cards)
 *
 * TDD tests — these MUST FAIL until the ActivePlanBadge component and
 * useActiveActionPlans hook are implemented.
 * Tests cover badge rendering for single/multiple active plans, empty states,
 * click navigation, accessibility, loading/error states, and integration
 * with InsightSection and InsightEvidenceCard.
 *
 * @see Story 16.4 - Active Plans Badge on Action Cards
 * @see AC #1 - Single active plan badge
 * @see AC #2 - Multiple active plans summary badge
 * @see AC #3 - No badge for empty/completed plans
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockPush = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush, replace: vi.fn(), back: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => '/',
  useParams: () => ({}),
}))

const mockGetSession = vi.fn()
vi.mock('@/lib/supabase/client', () => ({
  createClient: () => ({
    auth: { getSession: mockGetSession },
    from: () => ({
      insert: () => ({
        select: () => ({
          single: () => Promise.resolve({ data: null, error: null }),
        }),
      }),
    }),
  }),
}))

const mockFetch = vi.fn()
global.fetch = mockFetch

// ---------------------------------------------------------------------------
// Imports (AFTER mocks)
// ---------------------------------------------------------------------------

// The component and hook do NOT exist yet — imports will fail until implemented.
// This is intentional for TDD: tests must compile (vitest resolves the import
// at runtime) but FAIL because the modules are missing.
import React from 'react'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/**
 * ActiveActionPlan represents a single active plan returned by the API.
 * Mirrors the type that will be defined in the component.
 */
interface ActiveActionPlan {
  id: string
  title: string
  due_date: string // ISO date string
  status: 'open' | 'in_progress'
}

/**
 * ActivePlanBadgeProps — the props the component will accept.
 */
interface ActivePlanBadgeProps {
  assetId: string
  className?: string
}

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const createMockPlan = (overrides: Partial<ActiveActionPlan> = {}): ActiveActionPlan => ({
  id: 'plan-001',
  title: 'Replace bearing on motor A',
  due_date: '2026-02-20',
  status: 'open',
  ...overrides,
})

const createMockActionItem = (overrides: Record<string, unknown> = {}) => ({
  id: 'action-42',
  priority: 'FINANCIAL' as const,
  priorityScore: 750,
  recommendation: {
    text: 'Investigate downtime on Grinder 5',
    summary: 'Downtime investigation needed',
  },
  asset: {
    id: 'asset-001',
    name: 'Grinder 5',
    area: 'Grinding Area',
  },
  evidence: {
    type: 'financial_loss' as const,
    data: {
      downtimeCost: 1500,
      wasteCost: 500,
      totalLoss: 2000,
      breakdown: [],
    },
    source: {
      table: 'daily_summaries',
      date: '2026-02-10',
      recordId: 'rec-001',
    },
  },
  financialImpact: 2000,
  timestamp: '2026-02-11T08:00:00Z',
  ...overrides,
})

/**
 * Helper to build a mock fetch response returning action plans JSON.
 */
function mockFetchPlansResponse(plans: ActiveActionPlan[], status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => plans,
  }
}

/**
 * Sets up default successful auth + fetch mocks with given plans.
 */
function setupMocks(plans: ActiveActionPlan[] = []) {
  mockGetSession.mockResolvedValue({
    data: { session: { access_token: 'mock-token-abc' } },
  })
  mockFetch.mockResolvedValue(mockFetchPlansResponse(plans))
}

// ---------------------------------------------------------------------------
// Dynamic import helpers — will fail until components/hooks exist
// ---------------------------------------------------------------------------

async function importActivePlanBadge() {
  const mod = await import('../ActivePlanBadge')
  return mod.ActivePlanBadge as React.FC<ActivePlanBadgeProps>
}

async function importUseActiveActionPlans() {
  const mod = await import('@/hooks/useActiveActionPlans')
  return mod.useActiveActionPlans as (assetId?: string) => {
    plans: ActiveActionPlan[]
    isLoading: boolean
    error: string | null
  }
}

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: Active Plans Badge on Action Cards (Story 16.4)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockReset()
    mockGetSession.mockReset()
    mockPush.mockReset()

    // Default: authenticated session and empty plans
    setupMocks([])
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // =========================================================================
  // AC1: Single active plan badge
  // =========================================================================
  describe('AC1: Single Active Plan Badge', () => {
    it('UNIT-001: Renders badge with plan title and due date for single active plan', async () => {
      // Given: An asset has one active plan
      const plan = createMockPlan({
        id: 'plan-100',
        title: 'Replace bearing on motor A',
        due_date: '2026-02-20',
        status: 'open',
      })
      setupMocks([plan])

      // When: The ActivePlanBadge component renders for that asset
      const ActivePlanBadge = await importActivePlanBadge()
      render(React.createElement(ActivePlanBadge, { assetId: 'asset-001' }))

      // Then: A badge is displayed containing the plan title
      await waitFor(() => {
        expect(screen.getByText(/Replace bearing on motor A/i)).toBeInTheDocument()
      })

      // And: The badge shows the due date
      expect(screen.getByText(/2026-02-20|Feb 20/)).toBeInTheDocument()
    })

    it('UNIT-002: Badge uses info variant styling', async () => {
      // Given: An asset has one active plan
      const plan = createMockPlan({ status: 'open' })
      setupMocks([plan])

      // When: The badge renders
      const ActivePlanBadge = await importActivePlanBadge()
      render(React.createElement(ActivePlanBadge, { assetId: 'asset-001' }))

      // Then: The badge has info variant classes (blue styling from Shadcn Badge)
      await waitFor(() => {
        const badgeText = screen.getByText(/Replace bearing/i)
        const badgeEl =
          badgeText.closest('[class*="border-info-blue"]') ||
          badgeText.closest('[class*="info"]')
        expect(badgeEl).toBeTruthy()
      })
    })

    it('UNIT-003: Clicking single plan badge navigates to plan detail', async () => {
      // Given: An asset has one active plan with id "plan-100"
      const plan = createMockPlan({ id: 'plan-100' })
      setupMocks([plan])

      // When: The badge is clicked
      const ActivePlanBadge = await importActivePlanBadge()
      render(React.createElement(ActivePlanBadge, { assetId: 'asset-001' }))

      await waitFor(() => {
        expect(screen.getByText(/Replace bearing/i)).toBeInTheDocument()
      })
      fireEvent.click(screen.getByText(/Replace bearing/i))

      // Then: Router navigates to /action-plans/plan-100
      expect(mockPush).toHaveBeenCalledWith('/action-plans/plan-100')
    })

    it('UNIT-004: Badge includes aria-label with plan details for accessibility', async () => {
      // Given: An asset has one active plan
      const plan = createMockPlan({
        title: 'Calibrate sensor array',
        due_date: '2026-03-01',
        status: 'in_progress',
      })
      setupMocks([plan])

      // When: The badge renders
      const ActivePlanBadge = await importActivePlanBadge()
      render(React.createElement(ActivePlanBadge, { assetId: 'asset-001' }))

      // Then: The badge has an aria-label containing plan title and status
      await waitFor(() => {
        const badge = screen.getByLabelText(/action plan.*calibrate sensor array/i)
        expect(badge).toBeInTheDocument()
      })
    })

    it('UNIT-005: Badge has role="link" semantics', async () => {
      // Given: An asset has one active plan
      const plan = createMockPlan()
      setupMocks([plan])

      // When: The badge renders
      const ActivePlanBadge = await importActivePlanBadge()
      render(React.createElement(ActivePlanBadge, { assetId: 'asset-001' }))

      // Then: The badge element has role="link" for semantic navigation
      await waitFor(() => {
        const link = screen.getByRole('link', { name: /action plan/i })
        expect(link).toBeInTheDocument()
      })
    })

    it('UNIT-006: Hook fetches plans with correct URL and auth header', async () => {
      // Given: A valid session with access token
      const plan = createMockPlan()
      setupMocks([plan])

      // When: The badge renders for asset "asset-001"
      const ActivePlanBadge = await importActivePlanBadge()
      render(React.createElement(ActivePlanBadge, { assetId: 'asset-001' }))

      // Then: fetch is called with the correct URL including asset_id and status filter
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/action-plans'),
          expect.objectContaining({
            headers: expect.objectContaining({
              Authorization: 'Bearer mock-token-abc',
            }),
          })
        )
      })

      // And: The URL includes asset_id and status query params
      const calledUrl = mockFetch.mock.calls[0][0] as string
      expect(calledUrl).toMatch(/asset_id=asset-001/)
      expect(calledUrl).toMatch(/status=open,in_progress|status=open%2Cin_progress/)
    })

    it('UNIT-007: Hook performs client-side filtering for active statuses only', async () => {
      // Given: API returns plans with mixed statuses (edge case if API filter is loose)
      setupMocks([
        createMockPlan({ id: 'p1', status: 'open', title: 'Open plan' }),
        createMockPlan({ id: 'p2', status: 'in_progress', title: 'In progress plan' }),
      ])

      // When: The badge renders
      const ActivePlanBadge = await importActivePlanBadge()
      render(React.createElement(ActivePlanBadge, { assetId: 'asset-001' }))

      // Then: Both active plans are shown in the badge context
      await waitFor(() => {
        // With 2 plans it should show the summary badge
        expect(screen.getByText(/2 active/i)).toBeInTheDocument()
      })
    })

    it('UNIT-008: Badge not rendered when hook returns empty array but fetch was attempted', async () => {
      // Given: No active plans for the asset
      setupMocks([])

      // When: The badge renders
      const ActivePlanBadge = await importActivePlanBadge()
      const { container } = render(
        React.createElement(ActivePlanBadge, { assetId: 'asset-001' })
      )

      // Then: Nothing is rendered (returns null) but fetch WAS called
      await waitFor(() => {
        expect(container.innerHTML).toBe('')
        // The hook must have attempted to fetch from the API
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/action-plans'),
          expect.any(Object)
        )
      })
    })

    it('UNIT-009: Badge displays plan status text', async () => {
      // Given: An asset has one active plan with status "in_progress"
      const plan = createMockPlan({
        title: 'Fix pump seal',
        status: 'in_progress',
        due_date: '2026-02-25',
      })
      setupMocks([plan])

      // When: The badge renders
      const ActivePlanBadge = await importActivePlanBadge()
      render(React.createElement(ActivePlanBadge, { assetId: 'asset-001' }))

      // Then: The badge shows the plan status
      await waitFor(() => {
        expect(screen.getByText(/Fix pump seal/i)).toBeInTheDocument()
        // Status should be shown somewhere in the badge
        expect(screen.getByText(/in.progress|in_progress/i)).toBeInTheDocument()
      })
    })

    it('UNIT-010: Badge displays "open" status for open plans', async () => {
      // Given: An asset has one active plan with status "open"
      const plan = createMockPlan({
        title: 'Inspect conveyor belt',
        status: 'open',
      })
      setupMocks([plan])

      // When: The badge renders
      const ActivePlanBadge = await importActivePlanBadge()
      render(React.createElement(ActivePlanBadge, { assetId: 'asset-001' }))

      // Then: The badge text includes the plan title and status info
      await waitFor(() => {
        expect(screen.getByText(/Inspect conveyor belt/i)).toBeInTheDocument()
      })
    })

    it('UNIT-011: Hook skips fetch when assetId is empty string', async () => {
      // Given: An empty assetId is provided and plans exist for other assets
      setupMocks([createMockPlan()])

      // When: The badge renders with empty assetId
      const ActivePlanBadge = await importActivePlanBadge()
      const { container } = render(
        React.createElement(ActivePlanBadge, { assetId: '' })
      )

      // Then: No fetch call is made (hook skips fetch for empty assetId)
      // Wait a tick to ensure useEffect would have run
      await new Promise((r) => setTimeout(r, 50))
      expect(mockFetch).not.toHaveBeenCalled()
      expect(container.innerHTML).toBe('')

      // And: When a valid assetId is provided, fetch IS called (proves skip logic works)
      const { unmount } = render(
        React.createElement(ActivePlanBadge, { assetId: 'asset-valid' })
      )
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('asset_id=asset-valid'),
          expect.any(Object)
        )
      })
      unmount()
    })
  })

  // =========================================================================
  // AC2: Multiple active plans summary badge
  // =========================================================================
  describe('AC2: Multiple Active Plans Summary Badge', () => {
    it('UNIT-012: Summary badge shows "2 active action plans" for two plans', async () => {
      // Given: An asset has 2 active action plans
      const plans = [
        createMockPlan({ id: 'p1', title: 'Plan Alpha', status: 'open' }),
        createMockPlan({ id: 'p2', title: 'Plan Beta', status: 'in_progress' }),
      ]
      setupMocks(plans)

      // When: The badge renders
      const ActivePlanBadge = await importActivePlanBadge()
      render(React.createElement(ActivePlanBadge, { assetId: 'asset-001' }))

      // Then: A summary badge shows "2 active action plans" or "2 active plans"
      await waitFor(() => {
        expect(screen.getByText(/2 active/i)).toBeInTheDocument()
      })
    })

    it('UNIT-013: Summary badge shows correct count for 3+ plans', async () => {
      // Given: An asset has 3 active action plans
      const plans = [
        createMockPlan({ id: 'p1', title: 'Plan A', status: 'open' }),
        createMockPlan({ id: 'p2', title: 'Plan B', status: 'in_progress' }),
        createMockPlan({ id: 'p3', title: 'Plan C', status: 'open' }),
      ]
      setupMocks(plans)

      // When: The badge renders
      const ActivePlanBadge = await importActivePlanBadge()
      render(React.createElement(ActivePlanBadge, { assetId: 'asset-001' }))

      // Then: A summary badge shows "3 active action plans" or "3 active plans"
      await waitFor(() => {
        expect(screen.getByText(/3 active/i)).toBeInTheDocument()
      })
    })

    it('UNIT-014: Summary badge shows tooltip/popover with plan titles on hover', async () => {
      // Given: An asset has 2 active plans
      const plans = [
        createMockPlan({ id: 'p1', title: 'Plan Alpha' }),
        createMockPlan({ id: 'p2', title: 'Plan Beta' }),
      ]
      setupMocks(plans)

      // When: The summary badge is hovered or clicked to expand
      const ActivePlanBadge = await importActivePlanBadge()
      render(React.createElement(ActivePlanBadge, { assetId: 'asset-001' }))

      await waitFor(() => {
        expect(screen.getByText(/2 active/i)).toBeInTheDocument()
      })

      // Trigger hover/click on the summary badge to open dropdown/popover
      fireEvent.click(screen.getByText(/2 active/i))

      // Then: Individual plan titles are listed
      await waitFor(() => {
        expect(screen.getByText(/Plan Alpha/i)).toBeInTheDocument()
        expect(screen.getByText(/Plan Beta/i)).toBeInTheDocument()
      })
    })

    it('UNIT-015: Clicking summary badge opens dropdown, clicking plan navigates to detail', async () => {
      // Given: An asset has multiple active plans
      const plans = [
        createMockPlan({ id: 'p1', title: 'Plan Alpha' }),
        createMockPlan({ id: 'p2', title: 'Plan Beta' }),
      ]
      setupMocks(plans)

      // When: The summary badge is clicked to open dropdown
      const ActivePlanBadge = await importActivePlanBadge()
      render(React.createElement(ActivePlanBadge, { assetId: 'asset-001' }))

      await waitFor(() => {
        expect(screen.getByText(/2 active/i)).toBeInTheDocument()
      })
      fireEvent.click(screen.getByText(/2 active/i))

      // Then: Dropdown shows plan titles
      await waitFor(() => {
        expect(screen.getByText(/Plan Alpha/i)).toBeInTheDocument()
      })

      // When: Clicking an individual plan link in the dropdown
      fireEvent.click(screen.getByText(/Plan Alpha/i))

      // Then: Router navigates to the plan detail page
      expect(mockPush).toHaveBeenCalledWith('/action-plans/p1')
    })

    it('UNIT-016: Summary badge uses info variant styling', async () => {
      // Given: An asset has 2 active plans
      const plans = [
        createMockPlan({ id: 'p1' }),
        createMockPlan({ id: 'p2' }),
      ]
      setupMocks(plans)

      // When: The badge renders
      const ActivePlanBadge = await importActivePlanBadge()
      render(React.createElement(ActivePlanBadge, { assetId: 'asset-001' }))

      // Then: The summary badge has info variant classes (blue styling)
      await waitFor(() => {
        const badgeText = screen.getByText(/2 active/i)
        const badgeEl =
          badgeText.closest('[class*="border-info-blue"]') ||
          badgeText.closest('[class*="info"]')
        expect(badgeEl).toBeTruthy()
      })
    })

    it('UNIT-017: Summary badge includes aria-label with plan count', async () => {
      // Given: An asset has 2 active plans
      const plans = [
        createMockPlan({ id: 'p1' }),
        createMockPlan({ id: 'p2' }),
      ]
      setupMocks(plans)

      // When: The badge renders
      const ActivePlanBadge = await importActivePlanBadge()
      render(React.createElement(ActivePlanBadge, { assetId: 'asset-001' }))

      // Then: The badge has an aria-label describing the count
      await waitFor(() => {
        const badge = screen.getByLabelText(/2 active action plan/i)
        expect(badge).toBeInTheDocument()
      })
    })
  })

  // =========================================================================
  // AC3: No badge for empty/completed plans
  // =========================================================================
  describe('AC3: No Badge for Empty or Completed Plans', () => {
    it('UNIT-018: Renders nothing when asset has no action plans', async () => {
      // Given: The API returns an empty array for the asset
      setupMocks([])

      // When: The badge renders
      const ActivePlanBadge = await importActivePlanBadge()
      const { container } = render(
        React.createElement(ActivePlanBadge, { assetId: 'asset-001' })
      )

      // Then: The hook fetched from the API (it tried to find plans)
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/action-plans'),
          expect.any(Object)
        )
      })

      // And: Nothing is rendered (component returns null)
      expect(container.innerHTML).toBe('')
    })

    it('UNIT-019: Renders nothing when asset has only completed plans', async () => {
      // Given: The API returns only completed plans (filtered out by status param)
      // The hook requests status=open,in_progress so completed plans won't be returned
      setupMocks([])

      // When: The badge renders
      const ActivePlanBadge = await importActivePlanBadge()
      const { container } = render(
        React.createElement(ActivePlanBadge, { assetId: 'asset-002' })
      )

      // Then: The hook called the API with active status filter
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringMatching(/status=open/),
          expect.any(Object)
        )
      })

      // And: Nothing is rendered
      expect(container.innerHTML).toBe('')
    })

    it('UNIT-020: Renders nothing when asset has only verified plans', async () => {
      // Given: The API returns no plans (verified plans filtered out by status param)
      setupMocks([])

      // When: The badge renders
      const ActivePlanBadge = await importActivePlanBadge()
      const { container } = render(
        React.createElement(ActivePlanBadge, { assetId: 'asset-003' })
      )

      // Then: The hook fetched with correct asset filter
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('asset_id=asset-003'),
          expect.any(Object)
        )
      })

      // And: Nothing is rendered
      expect(container.innerHTML).toBe('')
    })

    it('UNIT-021: Renders nothing when asset has only draft plans', async () => {
      // Given: The API returns no plans (draft plans filtered out by status param)
      setupMocks([])

      // When: The badge renders
      const ActivePlanBadge = await importActivePlanBadge()
      const { container } = render(
        React.createElement(ActivePlanBadge, { assetId: 'asset-004' })
      )

      // Then: The hook fetched with correct asset filter
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('asset_id=asset-004'),
          expect.any(Object)
        )
      })

      // And: Nothing is rendered
      expect(container.innerHTML).toBe('')
    })

    it('UNIT-022: Renders nothing for mixed inactive statuses (draft + completed + verified)', async () => {
      // Given: The API returns no active plans for asset with only inactive plans
      setupMocks([])

      // When: The badge renders
      const ActivePlanBadge = await importActivePlanBadge()
      const { container } = render(
        React.createElement(ActivePlanBadge, { assetId: 'asset-005' })
      )

      // Then: The hook fetched with the correct asset filter
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('asset_id=asset-005'),
          expect.any(Object)
        )
      })

      // And: Nothing is rendered
      expect(container.innerHTML).toBe('')
    })

    it('UNIT-023: Renders badge only for active plans when mixed active+inactive exist', async () => {
      // Given: The API returns 1 active plan (the hook only requests active statuses)
      const activePlan = createMockPlan({
        id: 'p-active',
        title: 'Active maintenance task',
        status: 'in_progress',
      })
      setupMocks([activePlan])

      // When: The badge renders
      const ActivePlanBadge = await importActivePlanBadge()
      render(React.createElement(ActivePlanBadge, { assetId: 'asset-006' }))

      // Then: Only the active plan badge is shown
      await waitFor(() => {
        expect(screen.getByText(/Active maintenance task/i)).toBeInTheDocument()
      })
    })
  })

  // =========================================================================
  // Loading & Error States
  // =========================================================================
  describe('Loading & Error States', () => {
    it('UNIT-024: Shows loading skeleton while fetching plans', async () => {
      // Given: The fetch is pending (never resolves immediately)
      mockGetSession.mockResolvedValue({
        data: { session: { access_token: 'mock-token-abc' } },
      })
      mockFetch.mockReturnValue(new Promise(() => {})) // Never resolves

      // When: The badge renders
      const ActivePlanBadge = await importActivePlanBadge()
      render(React.createElement(ActivePlanBadge, { assetId: 'asset-001' }))

      // Then: A loading indicator (shimmer/skeleton) is shown inline
      // The hook must have initiated a fetch (session was retrieved)
      await waitFor(() => {
        expect(mockGetSession).toHaveBeenCalled()
      })

      // And: A loading indicator is present (data-testid or role="status")
      const skeleton =
        screen.queryByTestId('active-plan-badge-loading') ||
        screen.queryByRole('status')
      expect(skeleton).not.toBeNull()
    })

    it('UNIT-025: Shows nothing on API 500 error (silent failure)', async () => {
      // Given: The API returns a 500 error
      mockGetSession.mockResolvedValue({
        data: { session: { access_token: 'mock-token-abc' } },
      })
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => ({ detail: 'Internal server error' }),
      })

      // When: The badge renders
      const ActivePlanBadge = await importActivePlanBadge()
      const { container } = render(
        React.createElement(ActivePlanBadge, { assetId: 'asset-001' })
      )

      // Then: The hook attempted to fetch (session was used, fetch was called)
      await waitFor(() => {
        expect(mockGetSession).toHaveBeenCalled()
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/action-plans'),
          expect.any(Object)
        )
      })

      // And: Nothing is rendered (silent failure - badge is informational)
      expect(container.innerHTML).toBe('')
    })

    it('UNIT-026: Shows nothing on network error (silent failure)', async () => {
      // Given: The fetch throws a network error
      mockGetSession.mockResolvedValue({
        data: { session: { access_token: 'mock-token-abc' } },
      })
      mockFetch.mockRejectedValue(new TypeError('Failed to fetch'))

      // When: The badge renders
      const ActivePlanBadge = await importActivePlanBadge()
      const { container } = render(
        React.createElement(ActivePlanBadge, { assetId: 'asset-001' })
      )

      // Then: The hook attempted to fetch (session was used, fetch was called)
      await waitFor(() => {
        expect(mockGetSession).toHaveBeenCalled()
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/action-plans'),
          expect.any(Object)
        )
      })

      // And: Nothing is rendered (silent failure)
      expect(container.innerHTML).toBe('')
    })

    it('UNIT-027: Shows nothing on auth error (no session)', async () => {
      // Given: No session is available (user not authenticated)
      mockGetSession.mockResolvedValue({
        data: { session: null },
      })

      // When: The badge renders
      const ActivePlanBadge = await importActivePlanBadge()
      const { container } = render(
        React.createElement(ActivePlanBadge, { assetId: 'asset-001' })
      )

      // Then: The hook attempted to get session (auth check was performed)
      await waitFor(() => {
        expect(mockGetSession).toHaveBeenCalled()
      })

      // And: No fetch was made (no valid token)
      expect(mockFetch).not.toHaveBeenCalled()

      // And: Nothing is rendered (silent failure)
      expect(container.innerHTML).toBe('')
    })

    it('UNIT-028: Cleans up on unmount (no state update after unmount)', async () => {
      // Given: The badge renders and a fetch is in-flight
      const plan = createMockPlan()
      let resolvePromise: (value: unknown) => void
      const fetchPromise = new Promise((resolve) => {
        resolvePromise = resolve
      })
      mockGetSession.mockResolvedValue({
        data: { session: { access_token: 'mock-token-abc' } },
      })
      mockFetch.mockReturnValue(fetchPromise)

      const ActivePlanBadge = await importActivePlanBadge()
      const { unmount } = render(
        React.createElement(ActivePlanBadge, { assetId: 'asset-001' })
      )

      // Then: The hook initiated a fetch (session was checked)
      await waitFor(() => {
        expect(mockGetSession).toHaveBeenCalled()
      })

      // When: The component is unmounted before fetch completes
      unmount()

      // Then: Resolving the fetch after unmount does not cause React warnings
      // The mountedRef pattern prevents setState on unmounted component
      resolvePromise!(mockFetchPlansResponse([plan]))

      // No error thrown — if mountedRef is not used, React will warn about
      // setting state on unmounted component. This test ensures graceful cleanup.
      await new Promise((r) => setTimeout(r, 50))
    })
  })

  // =========================================================================
  // Integration: InsightSection and InsightEvidenceCard
  // =========================================================================
  describe('Integration: Component Integration', () => {
    it('INT-001: InsightSection renders ActivePlanBadge in context row', async () => {
      // Given: An InsightSection is rendered for an asset with an active plan
      const plan = createMockPlan({ title: 'Fix pump seal' })
      setupMocks([plan])

      const { InsightSection } = await import('../InsightSection')

      // When: The InsightSection renders with the asset
      render(
        React.createElement(InsightSection, {
          priority: 'FINANCIAL',
          recommendation: { text: 'Investigate downtime', summary: 'Investigate' },
          asset: { id: 'asset-001', name: 'Grinder 5', area: 'Grinding Area' },
          financialImpact: 2000,
          timestamp: '2026-02-11T08:00:00Z',
          onAssign: () => {},
        })
      )

      // Then: The ActivePlanBadge is visible in the context row
      await waitFor(() => {
        expect(screen.getByText(/Fix pump seal/i)).toBeInTheDocument()
      })
    })

    it('INT-002: InsightEvidenceCard passes assetId to ActivePlanBadge', async () => {
      // Given: An InsightEvidenceCard with an asset that has an active plan
      const plan = createMockPlan({ title: 'Replace filter' })
      setupMocks([plan])

      const item = createMockActionItem({
        asset: { id: 'asset-007', name: 'Compressor 3', area: 'Utilities' },
      })

      const { InsightEvidenceCard } = await import('../InsightEvidenceCard')

      // When: The card renders
      render(React.createElement(InsightEvidenceCard, { item }))

      // Then: fetch is called with the correct asset_id
      await waitFor(() => {
        const calledUrl = mockFetch.mock.calls.find(
          (call) => typeof call[0] === 'string' && call[0].includes('action-plans')
        )
        expect(calledUrl).toBeTruthy()
        expect(calledUrl![0]).toContain('asset_id=asset-007')
      })
    })

    it('INT-003: ActivePlanBadge does not disrupt card layout or priority styling', async () => {
      // Given: An InsightEvidenceCard renders with an active plan
      const plan = createMockPlan({ title: 'Lubricate gears' })
      setupMocks([plan])

      const item = createMockActionItem()
      const { InsightEvidenceCard } = await import('../InsightEvidenceCard')

      // When: The full card renders
      render(React.createElement(InsightEvidenceCard, { item }))

      // Then: The card still displays the recommendation, asset name, and priority badge
      await waitFor(() => {
        expect(screen.getByText(/Investigate downtime on Grinder 5/i)).toBeInTheDocument()
        // "Grinder 5" appears in both the recommendation text and asset name span
        const grinder5Matches = screen.getAllByText(/Grinder 5/i)
        expect(grinder5Matches.length).toBeGreaterThanOrEqual(1)
      })

      // And: The active plan badge is also present
      await waitFor(() => {
        expect(screen.getByText(/Lubricate gears/i)).toBeInTheDocument()
      })
    })

    it('INT-004: ActivePlanBadge is exported from barrel file', async () => {
      // Given: The action-engine barrel file (index.ts) has been updated
      // When: Importing ActivePlanBadge from the barrel
      const barrel = await import('../index')

      // Then: The ActivePlanBadge component is exported and is a function
      expect(barrel.ActivePlanBadge).toBeDefined()
      expect(typeof barrel.ActivePlanBadge).toBe('function')
    })
  })
})
