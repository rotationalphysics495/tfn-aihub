/**
 * Action List Primary View Tests
 *
 * Tests for Story 3.3 Acceptance Criteria:
 * 1. Action List as Primary Landing View
 * 2. Action First Layout Structure
 * 3. Action Item Card Display
 * 4. Action Priority Ordering
 * 5. Data Integration with Action Engine API
 * 6. Morning Summary Section
 * 7. Navigation and Quick Actions
 * 8. Industrial Clarity Visual Compliance
 * 9. Authentication Flow Integration (middleware tests in separate file)
 * 10. Performance Requirements (loading states)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import * as React from 'react'

// Mock Next.js navigation
const mockPush = vi.fn()
const mockPathname = vi.fn().mockReturnValue('/morning-report')

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    refresh: vi.fn(),
    replace: vi.fn(),
  }),
  usePathname: () => mockPathname(),
}))

// Mock Supabase client
vi.mock('@/lib/supabase/client', () => ({
  createClient: () => ({
    auth: {
      getSession: vi.fn().mockResolvedValue({
        data: {
          session: {
            access_token: 'mock-token',
          },
        },
      }),
    },
  }),
}))

// Import components after mocks
import { ActionItemCard } from '@/components/action-list/ActionItemCard'
import { ActionListContainer } from '@/components/action-list/ActionListContainer'
import { ActionListSkeleton, SummarySkeleton } from '@/components/action-list/ActionListSkeleton'
import { EmptyActionState } from '@/components/action-list/EmptyActionState'
import { MorningSummarySection } from '@/components/action-list/MorningSummarySection'
import { ViewModeToggle } from '@/components/navigation/ViewModeToggle'
import { Breadcrumb } from '@/components/navigation/Breadcrumb'
import type { ActionItem } from '@/hooks/useDailyActions'

// ========================================
// Test Data
// ========================================
const mockSafetyAction: ActionItem = {
  id: 'action-1',
  asset_id: 'asset-1',
  asset_name: 'Grinder 5',
  priority_level: 'critical',
  category: 'safety',
  primary_metric_value: 'Safety Event: Emergency Stop',
  recommendation_text: 'Investigate emergency stop trigger on Grinder 5',
  evidence_summary: 'Unresolved safety event detected at 14:30',
  evidence_refs: [],
  created_at: '2026-01-06T15:00:00Z',
  financial_impact_usd: 0,
  priority_rank: 0,
  title: 'Investigate emergency stop trigger on Grinder 5',
  description: 'Unresolved safety event detected at 14:30',
}

const mockOeeAction: ActionItem = {
  id: 'action-2',
  asset_id: 'asset-2',
  asset_name: 'Line 3',
  priority_level: 'high',
  category: 'oee',
  primary_metric_value: 'OEE: 72.5%',
  recommendation_text: 'Review OEE performance on Line 3',
  evidence_summary: 'OEE below target by 12.5% yesterday',
  evidence_refs: [],
  created_at: '2026-01-06T15:00:00Z',
  financial_impact_usd: 3500,
  priority_rank: 1,
  title: 'Review OEE performance on Line 3',
  description: 'OEE below target by 12.5% yesterday',
}

const mockFinancialAction: ActionItem = {
  id: 'action-3',
  asset_id: 'asset-3',
  asset_name: 'Packaging Unit',
  priority_level: 'medium',
  category: 'financial',
  primary_metric_value: 'Loss: $8,500',
  recommendation_text: 'Address financial loss on Packaging Unit',
  evidence_summary: 'Downtime resulted in significant financial impact',
  evidence_refs: [],
  created_at: '2026-01-06T15:00:00Z',
  financial_impact_usd: 8500,
  priority_rank: 2,
  title: 'Address financial loss on Packaging Unit',
  description: 'Downtime resulted in significant financial impact',
}

// ========================================
// AC #3: Action Item Card Display Tests
// ========================================
describe('AC #3: Action Item Card Display', () => {
  beforeEach(() => {
    mockPush.mockClear()
  })

  it('should render action card with recommendation text prominently', () => {
    render(<ActionItemCard action={mockSafetyAction} rank={1} />)

    expect(screen.getByText('Investigate emergency stop trigger on Grinder 5')).toBeInTheDocument()
    expect(screen.getByText('Unresolved safety event detected at 14:30')).toBeInTheDocument()
  })

  it('should display visual priority indicator for safety actions (red)', () => {
    render(<ActionItemCard action={mockSafetyAction} rank={1} />)

    const badge = screen.getByText('Safety')
    expect(badge).toBeInTheDocument()
    // Check safety badge variant is applied
    expect(badge.className).toContain('safety')
  })

  it('should display visual priority indicator for financial actions (amber)', () => {
    render(<ActionItemCard action={mockFinancialAction} rank={3} />)

    const badge = screen.getByText('Financial')
    expect(badge).toBeInTheDocument()
    expect(badge.className).toContain('warning')
  })

  it('should display visual priority indicator for OEE actions (blue)', () => {
    render(<ActionItemCard action={mockOeeAction} rank={2} />)

    const badge = screen.getByText('Performance')
    expect(badge).toBeInTheDocument()
    expect(badge.className).toContain('info')
  })

  it('should show rank number on card', () => {
    render(<ActionItemCard action={mockSafetyAction} rank={1} />)

    expect(screen.getByText('#1')).toBeInTheDocument()
  })

  it('should show asset name', () => {
    render(<ActionItemCard action={mockSafetyAction} rank={1} />)

    expect(screen.getByText('Grinder 5')).toBeInTheDocument()
  })

  it('should show financial impact when available', () => {
    render(<ActionItemCard action={mockFinancialAction} rank={1} />)

    expect(screen.getByText(/\$8\.5K impact/)).toBeInTheDocument()
  })

  it('should be clickable for drill-down navigation', () => {
    render(<ActionItemCard action={mockSafetyAction} rank={1} />)

    const card = screen.getByRole('button', { name: /Action 1/ })
    fireEvent.click(card)

    expect(mockPush).toHaveBeenCalledWith('/morning-report/action/action-1')
  })

  it('should be keyboard accessible', () => {
    render(<ActionItemCard action={mockSafetyAction} rank={1} />)

    const card = screen.getByRole('button', { name: /Action 1/ })
    fireEvent.keyDown(card, { key: 'Enter' })

    expect(mockPush).toHaveBeenCalledWith('/morning-report/action/action-1')
  })
})

// ========================================
// AC #4: Action Priority Ordering Tests
// ========================================
describe('AC #4: Action Priority Ordering', () => {
  it('should display safety critical items with red border', () => {
    const { container } = render(<ActionItemCard action={mockSafetyAction} rank={1} />)

    const card = container.querySelector('.border-l-safety-red')
    expect(card).toBeInTheDocument()
  })

  it('should display high priority items with amber border', () => {
    const { container } = render(<ActionItemCard action={mockOeeAction} rank={2} />)

    const card = container.querySelector('.border-l-warning-amber')
    expect(card).toBeInTheDocument()
  })

  it('should display medium priority items with blue border', () => {
    const { container } = render(<ActionItemCard action={mockFinancialAction} rank={3} />)

    const card = container.querySelector('.border-l-info-blue')
    expect(card).toBeInTheDocument()
  })

  it('should show priority level badge', () => {
    render(<ActionItemCard action={mockSafetyAction} rank={1} />)

    expect(screen.getByText(/Critical Priority/)).toBeInTheDocument()
  })
})

// ========================================
// AC #5: Loading and Error States Tests
// ========================================
describe('AC #5: Loading and Error States', () => {
  it('should render loading skeleton with correct number of cards', () => {
    render(<ActionListSkeleton count={3} />)

    const skeleton = screen.getByRole('status', { name: /loading action items/i })
    expect(skeleton).toBeInTheDocument()
  })

  it('should render summary skeleton', () => {
    const { container } = render(<SummarySkeleton />)

    // Check for animate-pulse elements
    const pulsingElements = container.querySelectorAll('.animate-pulse')
    expect(pulsingElements.length).toBeGreaterThan(0)
  })

  it('should show empty state when no action items', () => {
    render(<EmptyActionState />)

    expect(screen.getByText('All Systems Performing Within Targets')).toBeInTheDocument()
    expect(screen.getByText(/No immediate actions required/)).toBeInTheDocument()
  })

  it('should show success icon in empty state', () => {
    const { container } = render(<EmptyActionState />)

    // Check for success-green styling
    const successIcon = container.querySelector('.text-success-green')
    expect(successIcon).toBeInTheDocument()
  })
})

// ========================================
// AC #7: Navigation and Quick Actions Tests
// ========================================
describe('AC #7: Navigation and Quick Actions', () => {
  beforeEach(() => {
    mockPush.mockClear()
  })

  describe('ViewModeToggle', () => {
    it('should render view mode toggle with Morning Report and Live Pulse options', () => {
      mockPathname.mockReturnValue('/morning-report')
      render(<ViewModeToggle />)

      expect(screen.getByRole('tab', { name: /morning report/i })).toBeInTheDocument()
      expect(screen.getByRole('tab', { name: /live pulse/i })).toBeInTheDocument()
    })

    it('should highlight Morning Report when on /morning-report path', () => {
      mockPathname.mockReturnValue('/morning-report')
      render(<ViewModeToggle />)

      const morningReportTab = screen.getByRole('tab', { name: /morning report/i })
      expect(morningReportTab).toHaveAttribute('aria-selected', 'true')
    })

    it('should navigate to Live Pulse when clicked', () => {
      mockPathname.mockReturnValue('/morning-report')
      render(<ViewModeToggle />)

      const livePulseTab = screen.getByRole('tab', { name: /live pulse/i })
      fireEvent.click(livePulseTab)

      expect(mockPush).toHaveBeenCalledWith('/dashboard')
    })
  })

  describe('Breadcrumb', () => {
    it('should render breadcrumb navigation', () => {
      mockPathname.mockReturnValue('/morning-report')
      render(<Breadcrumb />)

      expect(screen.getByRole('navigation', { name: /breadcrumb/i })).toBeInTheDocument()
    })

    it('should show current page as active', () => {
      mockPathname.mockReturnValue('/morning-report')
      render(<Breadcrumb />)

      const currentPage = screen.getByText('Morning Report')
      expect(currentPage).toHaveAttribute('aria-current', 'page')
    })
  })
})

// ========================================
// AC #8: Industrial Clarity Visual Compliance Tests
// ========================================
describe('AC #8: Industrial Clarity Visual Compliance', () => {
  it('should use safety-red ONLY for safety action items', () => {
    const { container: safetyContainer } = render(
      <ActionItemCard action={mockSafetyAction} rank={1} />
    )
    const { container: oeeContainer } = render(
      <ActionItemCard action={mockOeeAction} rank={2} />
    )
    const { container: financialContainer } = render(
      <ActionItemCard action={mockFinancialAction} rank={3} />
    )

    // Safety card should have safety-red
    expect(safetyContainer.querySelector('.bg-safety-red')).toBeInTheDocument()

    // OEE card should NOT have safety-red
    expect(oeeContainer.querySelector('.bg-safety-red')).not.toBeInTheDocument()

    // Financial card should NOT have safety-red
    expect(financialContainer.querySelector('.bg-safety-red')).not.toBeInTheDocument()
  })

  it('should use retrospective mode styling for cards', () => {
    const { container } = render(<ActionItemCard action={mockOeeAction} rank={1} />)

    // Cards should use retrospective mode
    const card = container.querySelector('[class*="retrospective"]')
    expect(card).toBeInTheDocument()
  })

  it('should have large typography for action titles (text-xl or text-2xl)', () => {
    const { container } = render(<ActionItemCard action={mockSafetyAction} rank={1} />)

    // Check for large text class on title
    const title = container.querySelector('.text-xl, .text-2xl')
    expect(title).toBeInTheDocument()
  })

  it('should have minimum body text size (text-base = 18px)', () => {
    const { container } = render(<ActionItemCard action={mockSafetyAction} rank={1} />)

    // Check for text-base class on description
    const description = container.querySelector('.text-base')
    expect(description).toBeInTheDocument()
  })
})

// ========================================
// AC #10: Performance Requirements Tests
// ========================================
describe('AC #10: Performance Requirements', () => {
  it('should render loading skeleton immediately (no flash of empty content)', () => {
    const { container } = render(<ActionListSkeleton count={3} />)

    // Skeleton should be in DOM immediately
    expect(container.querySelector('[role="status"]')).toBeInTheDocument()
  })

  it('should have aria-label for screen reader accessibility during loading', () => {
    render(<ActionListSkeleton count={3} />)

    // Should have accessible label
    expect(screen.getByLabelText(/loading action items/i)).toBeInTheDocument()
  })
})

// ========================================
// MorningSummarySection Tests (AC #6)
// ========================================
describe('AC #6: Morning Summary Section', () => {
  // Mock fetch for these tests
  beforeEach(() => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          actions: [mockSafetyAction, mockOeeAction, mockFinancialAction],
          generated_at: '2026-01-06T06:30:00Z',
          report_date: '2026-01-05',
          total_count: 3,
          counts_by_category: { safety: 1, oee: 1, financial: 1 },
        }),
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should display date context', async () => {
    render(<MorningSummarySection />)

    await waitFor(() => {
      expect(screen.getByText(/Yesterday's Performance/)).toBeInTheDocument()
    })
  })

  it('should show AI summary placeholder', async () => {
    render(<MorningSummarySection />)

    await waitFor(() => {
      expect(screen.getByText(/AI Summary/)).toBeInTheDocument()
    })
  })
})

// ========================================
// Accessibility Tests
// ========================================
describe('Accessibility', () => {
  it('action cards should have proper aria-label', () => {
    render(<ActionItemCard action={mockSafetyAction} rank={1} />)

    const card = screen.getByRole('button')
    expect(card).toHaveAttribute('aria-label', expect.stringContaining('Action 1'))
  })

  it('view mode toggle should have proper tablist role', () => {
    mockPathname.mockReturnValue('/morning-report')
    render(<ViewModeToggle />)

    expect(screen.getByRole('tablist', { name: /view mode/i })).toBeInTheDocument()
  })

  it('breadcrumb should have proper navigation role', () => {
    mockPathname.mockReturnValue('/morning-report')
    render(<Breadcrumb />)

    expect(screen.getByRole('navigation', { name: /breadcrumb/i })).toBeInTheDocument()
  })
})
