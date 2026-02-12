/**
 * ActionPlanCard Component Tests (Story 16.5: Action Plans Dashboard)
 *
 * TDD tests — these MUST FAIL until the ActionPlanCard component is implemented.
 * Tests cover card rendering, priority badges, status badges, due date indicators,
 * overdue highlighting, and due-soon warnings.
 *
 * @see Story 16.5 - Action Plans Dashboard
 * @see AC #1 - Dashboard displays grouped action plans with card details
 * @see AC #2 - Overdue highlighting
 */

import { render, screen, fireEvent } from '@testing-library/react'
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

// ---------------------------------------------------------------------------
// Import component AFTER mocks are set up
// ---------------------------------------------------------------------------

// The component does not exist yet — this import will fail until it's created.
import { ActionPlanCard } from '../ActionPlanCard'

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: ActionPlanCard Component (Story 16.5)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Fix "today" to 2026-02-12 for deterministic due-date calculations
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-02-12T00:00:00Z'))
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  // =========================================================================
  // AC1: Card rendering with plan details
  // =========================================================================
  describe('AC1: ActionPlanCard renders plan details', () => {
    it('16-5-action-plans-dashboard-UNIT-002: ActionPlanCard renders title, priority badge, owner, due date, and days-until-due', () => {
      // Given: An action plan with all fields populated
      const plan = createMockActionPlan({
        title: 'Replace worn bearing on Grinder 5',
        priority: 'high',
        owner_email: 'manager@company.com',
        due_date: '2026-02-20',
        status: 'open',
      })

      // When: The ActionPlanCard renders
      render(<ActionPlanCard plan={plan} />)

      // Then: The card displays the title
      expect(screen.getByText('Replace worn bearing on Grinder 5')).toBeInTheDocument()

      // And: The card shows a priority badge for "high"
      expect(screen.getByText(/high/i)).toBeInTheDocument()

      // And: The card shows the owner email
      expect(screen.getByText('manager@company.com')).toBeInTheDocument()

      // And: The card shows the due date
      expect(screen.getByText(/feb.*20|2026-02-20|02\/20/i)).toBeInTheDocument()

      // And: The card shows days until due (8 days from 2026-02-12)
      expect(screen.getByText(/due in 8 days/i)).toBeInTheDocument()
    })

    it('16-5-action-plans-dashboard-UNIT-003: ActionPlanCard shows "Plant-wide" when asset_id is null', () => {
      // Given: An action plan with no associated asset
      const plan = createMockActionPlan({
        asset_id: null,
        asset_name: null,
      })

      // When: The ActionPlanCard renders
      render(<ActionPlanCard plan={plan} />)

      // Then: The card shows "Plant-wide" instead of an asset name
      expect(screen.getByText(/plant-wide/i)).toBeInTheDocument()
    })

    it('16-5-action-plans-dashboard-UNIT-004: ActionPlanCard renders correct status badge color per status', () => {
      // Given: Action plans with different statuses
      const statuses: Array<{ status: ActionPlan['status']; expectedClass: string }> = [
        { status: 'open', expectedClass: 'text-blue' },
        { status: 'in_progress', expectedClass: 'text-amber' },
        { status: 'completed', expectedClass: 'text-green' },
        { status: 'verified', expectedClass: 'text-emerald' },
      ]

      for (const { status, expectedClass } of statuses) {
        const plan = createMockActionPlan({ status })

        // When: The ActionPlanCard renders
        const { container, unmount } = render(<ActionPlanCard plan={plan} />)

        // Then: The status badge has the correct color class
        const statusBadge = screen.getByText(new RegExp(status.replace('_', ' '), 'i'))
        expect(statusBadge).toBeInTheDocument()

        // And: The badge contains the expected color indicator
        const badgeEl = statusBadge.closest('[class]')
        expect(badgeEl?.className).toMatch(new RegExp(expectedClass, 'i'))

        unmount()
      }
    })

    it('16-5-action-plans-dashboard-UNIT-005: ActionPlanCard renders correct priority badge colors', () => {
      // Given: Action plans with different priorities
      const priorities: Array<{ priority: ActionPlan['priority']; expectedPattern: RegExp }> = [
        { priority: 'critical', expectedPattern: /red|destructive|safety/i },
        { priority: 'high', expectedPattern: /amber|warning/i },
        { priority: 'medium', expectedPattern: /yellow/i },
        { priority: 'low', expectedPattern: /blue|info/i },
      ]

      for (const { priority, expectedPattern } of priorities) {
        const plan = createMockActionPlan({ priority })

        // When: The ActionPlanCard renders
        const { container, unmount } = render(<ActionPlanCard plan={plan} />)

        // Then: The priority badge has the correct color
        const priorityBadge = screen.getByText(new RegExp(priority, 'i'))
        expect(priorityBadge).toBeInTheDocument()

        const badgeEl = priorityBadge.closest('[class]')
        expect(badgeEl?.className).toMatch(expectedPattern)

        unmount()
      }
    })

    it('16-5-action-plans-dashboard-UNIT-002b: ActionPlanCard renders asset name when available', () => {
      // Given: An action plan with an associated asset
      const plan = createMockActionPlan({
        asset_id: 'asset-001',
        asset_name: 'Grinder 5',
      })

      // When: The ActionPlanCard renders
      render(<ActionPlanCard plan={plan} />)

      // Then: The card shows the asset name
      expect(screen.getByText('Grinder 5')).toBeInTheDocument()
    })
  })

  // =========================================================================
  // AC2: Overdue and due-soon highlighting
  // =========================================================================
  describe('AC2: Overdue highlighting', () => {
    it('16-5-action-plans-dashboard-UNIT-014: Overdue plan shows red "X days overdue" text', () => {
      // Given: An open action plan with due_date 5 days in the past
      //        (today is 2026-02-12, due_date is 2026-02-07)
      const plan = createMockActionPlan({
        status: 'open',
        due_date: '2026-02-07',
      })

      // When: The ActionPlanCard renders
      render(<ActionPlanCard plan={plan} />)

      // Then: The card shows "5 days overdue" in red
      expect(screen.getByText(/5 days overdue/i)).toBeInTheDocument()
    })

    it('16-5-action-plans-dashboard-UNIT-015: Overdue text uses text-destructive class', () => {
      // Given: An overdue action plan
      const plan = createMockActionPlan({
        status: 'in_progress',
        due_date: '2026-02-10',
      })

      // When: The ActionPlanCard renders
      const { container } = render(<ActionPlanCard plan={plan} />)

      // Then: The overdue indicator has destructive styling
      const overdueText = screen.getByText(/2 days overdue/i)
      expect(overdueText.className).toMatch(/text-destructive|text-red/i)
    })

    it('16-5-action-plans-dashboard-UNIT-016: Overdue card has red highlight or background', () => {
      // Given: An overdue action plan
      const plan = createMockActionPlan({
        status: 'open',
        due_date: '2026-02-05',
      })

      // When: The ActionPlanCard renders
      const { container } = render(<ActionPlanCard plan={plan} />)

      // Then: The card container has a destructive/red accent
      const card = container.firstElementChild
      expect(card?.className).toMatch(/destructive|border-red|bg-red/i)
    })

    it('16-5-action-plans-dashboard-UNIT-017: Completed plan is NOT marked overdue even if past due_date', () => {
      // Given: A completed plan with a due_date in the past
      const plan = createMockActionPlan({
        status: 'completed',
        due_date: '2026-02-01',
        completed_at: '2026-02-05T10:00:00Z',
      })

      // When: The ActionPlanCard renders
      render(<ActionPlanCard plan={plan} />)

      // Then: The card does NOT show overdue text
      expect(screen.queryByText(/overdue/i)).not.toBeInTheDocument()
    })

    it('16-5-action-plans-dashboard-UNIT-018: Verified plan is NOT marked overdue even if past due_date', () => {
      // Given: A verified plan with a due_date in the past
      const plan = createMockActionPlan({
        status: 'verified',
        due_date: '2026-01-15',
        verified_at: '2026-02-01T10:00:00Z',
      })

      // When: The ActionPlanCard renders
      render(<ActionPlanCard plan={plan} />)

      // Then: The card does NOT show overdue text
      expect(screen.queryByText(/overdue/i)).not.toBeInTheDocument()
    })

    it('16-5-action-plans-dashboard-UNIT-019: Overdue count is exactly correct for various day gaps', () => {
      // Given: An open plan 1 day overdue (due_date=2026-02-11, today=2026-02-12)
      const plan = createMockActionPlan({
        status: 'open',
        due_date: '2026-02-11',
      })

      // When: The ActionPlanCard renders
      render(<ActionPlanCard plan={plan} />)

      // Then: Shows "1 days overdue" (or "1 day overdue")
      expect(screen.getByText(/1 day[s]? overdue/i)).toBeInTheDocument()
    })

    it('16-5-action-plans-dashboard-UNIT-020: In-progress plan with past due_date shows overdue', () => {
      // Given: An in-progress plan with due_date in the past
      const plan = createMockActionPlan({
        status: 'in_progress',
        due_date: '2026-02-08',
      })

      // When: The ActionPlanCard renders
      render(<ActionPlanCard plan={plan} />)

      // Then: Shows "4 days overdue"
      expect(screen.getByText(/4 days overdue/i)).toBeInTheDocument()
    })

    it('16-5-action-plans-dashboard-UNIT-012: ActionPlanCard due-soon indicator shows amber text for plans due within 3 days', () => {
      // Given: An open plan due in 2 days (due_date=2026-02-14, today=2026-02-12)
      const plan = createMockActionPlan({
        status: 'open',
        due_date: '2026-02-14',
      })

      // When: The ActionPlanCard renders
      render(<ActionPlanCard plan={plan} />)

      // Then: Shows "Due in 2 days" with amber/warning styling
      const dueSoonText = screen.getByText(/due in 2 days/i)
      expect(dueSoonText).toBeInTheDocument()
      expect(dueSoonText.className).toMatch(/text-amber|text-warning|text-yellow/i)
    })

    it('16-5-action-plans-dashboard-UNIT-013: ActionPlanCard shows "Due in 1 day" (singular) when due tomorrow', () => {
      // Given: An open plan due tomorrow (due_date=2026-02-13, today=2026-02-12)
      const plan = createMockActionPlan({
        status: 'open',
        due_date: '2026-02-13',
      })

      // When: The ActionPlanCard renders
      render(<ActionPlanCard plan={plan} />)

      // Then: Shows "Due in 1 day" (singular, not "1 days")
      expect(screen.getByText(/due in 1 day$/i)).toBeInTheDocument()
      expect(screen.queryByText(/due in 1 days/i)).not.toBeInTheDocument()
    })
  })

  // =========================================================================
  // Click interaction
  // =========================================================================
  describe('Card click interaction', () => {
    it('ActionPlanCard calls onClick with plan when clicked', () => {
      // Given: An ActionPlanCard with an onClick handler
      const onClickSpy = vi.fn()
      const plan = createMockActionPlan()

      // When: The card is clicked
      render(<ActionPlanCard plan={plan} onClick={onClickSpy} />)
      const card = screen.getByText('Replace worn bearing on Grinder 5').closest('[role="button"], button, [class*="card"], [class*="Card"]')
      if (card) fireEvent.click(card)

      // Then: The onClick handler is called with the plan
      expect(onClickSpy).toHaveBeenCalledWith(plan)
    })
  })
})
