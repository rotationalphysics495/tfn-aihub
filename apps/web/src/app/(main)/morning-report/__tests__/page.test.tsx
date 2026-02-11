/**
 * Morning Report Page Integration Tests (Story 12.6: Schedule Attainment UI Section)
 *
 * TDD test — this MUST FAIL until the ScheduleAttainment component is integrated
 * into the morning report page.
 *
 * @see Story 12.6 - Schedule Attainment UI Section
 * @see AC #1 - ScheduleAttainment positioned between WorkcenterScorecard and action items
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'

// ---------------------------------------------------------------------------
// Mocks — all hooks used by child sections
// ---------------------------------------------------------------------------

// Mock useScheduleAttainment
const mockUseScheduleAttainment = vi.fn()
vi.mock('@/hooks/useScheduleAttainment', () => ({
  useScheduleAttainment: (...args: unknown[]) => mockUseScheduleAttainment(...args),
}))

// Mock useWorkcenterSummary
const mockUseWorkcenterSummary = vi.fn()
vi.mock('@/hooks/useWorkcenterSummary', () => ({
  useWorkcenterSummary: (...args: unknown[]) => mockUseWorkcenterSummary(...args),
}))

// Mock useDailyActions
const mockUseDailyActions = vi.fn()
vi.mock('@/hooks/useDailyActions', () => ({
  useDailyActions: (...args: unknown[]) => mockUseDailyActions(...args),
}))

// Mock useSmartSummary
const mockUseSmartSummary = vi.fn()
vi.mock('@/hooks/useSmartSummary', () => ({
  useSmartSummary: (...args: unknown[]) => mockUseSmartSummary(...args),
}))

// Mock useSafetyAlerts
const mockUseSafetyAlerts = vi.fn()
vi.mock('@/hooks/useSafetyAlerts', () => ({
  useSafetyAlerts: (...args: unknown[]) => mockUseSafetyAlerts(...args),
}))

// Mock Supabase client
vi.mock('@/lib/supabase/client', () => ({
  createClient: () => ({
    auth: {
      getSession: vi.fn().mockResolvedValue({
        data: { session: { access_token: 'mock-token' } },
      }),
    },
  }),
}))

// Mock recharts to avoid canvas issues
vi.mock('recharts', () => ({
  BarChart: ({ children }: any) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => <div data-testid="bar" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
  ResponsiveContainer: ({ children }: any) => <div data-testid="responsive-container">{children}</div>,
  ComposedChart: ({ children }: any) => <div data-testid="composed-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  ReferenceLine: () => <div data-testid="reference-line" />,
  Cell: () => <div data-testid="cell" />,
}))

// ---------------------------------------------------------------------------
// Import page component AFTER mocks are set up
// ---------------------------------------------------------------------------

import MorningReportPage from '../page'

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: ScheduleAttainment integration in Morning Report page (Story 12.6)', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    // Default mock returns for all hooks
    mockUseSafetyAlerts.mockReturnValue({
      alerts: [],
      activeCount: 0,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      acknowledge: vi.fn(),
      hasActiveAlerts: false,
    })

    mockUseDailyActions.mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      hasActions: false,
      summary: {
        totalActions: 0,
        safetyCount: 0,
        oeeCount: 0,
        financialCount: 0,
      },
    })

    mockUseSmartSummary.mockReturnValue({
      data: null,
      isLoading: false,
      isGenerating: false,
      error: null,
      refetch: vi.fn(),
      regenerate: vi.fn(),
      hasSummary: false,
    })

    mockUseWorkcenterSummary.mockReturnValue({
      data: {
        workcenters: [
          {
            workcenter_name: 'Grinding',
            total_actual: 4200,
            total_target: 5000,
            attainment_percentage: 84.0,
            assets_on_target: 2,
            assets_missed: 2,
            total_assets: 4,
            assets: [],
          },
        ],
        date: '2026-02-10',
        total_actual: 4200,
        total_target: 5000,
        total_attainment: 84.0,
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    })

    mockUseScheduleAttainment.mockReturnValue({
      data: {
        workcenters: [
          {
            workcenter_name: 'Roasting',
            overall_attainment_pct: 92.5,
            products: [
              { product_name: 'Brazilian', scheduled_quantity: 1000, actual_quantity: 950, attainment_pct: 95.0 },
            ],
            variance_callouts: [],
          },
        ],
        report_date: '2026-02-10',
        has_schedule: true,
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('INT-001: ScheduleAttainment positioned between WorkcenterScorecard and action items in morning report', () => {
    // Given: The morning report page renders with all sections
    render(<MorningReportPage />)

    // When: The page loads
    // Then: The ScheduleAttainment section appears after WorkcenterScorecard
    // and before the action items section

    // Find the schedule attainment section by aria-label
    const scheduleAttainmentSection = screen.getByRole('region', {
      name: /schedule attainment/i,
    })
    expect(scheduleAttainmentSection).toBeInTheDocument()

    // Find the action items section by aria-label
    const actionItemsSection = screen.getByRole('region', {
      name: /action items with evidence/i,
    })
    expect(actionItemsSection).toBeInTheDocument()

    // Verify DOM order: ScheduleAttainment before action items
    expect(
      scheduleAttainmentSection.compareDocumentPosition(actionItemsSection) &
        Node.DOCUMENT_POSITION_FOLLOWING
    ).toBeTruthy()

    // Verify ScheduleAttainment comes after WorkcenterScorecard
    // WorkcenterScorecard renders "Production Scorecard" heading
    const productionScorecard = screen.getByText('Production Scorecard')
    expect(
      productionScorecard.compareDocumentPosition(scheduleAttainmentSection) &
        Node.DOCUMENT_POSITION_FOLLOWING
    ).toBeTruthy()
  })
})
