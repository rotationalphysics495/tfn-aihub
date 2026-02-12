/**
 * MorningReportClient Integration Tests (Story 17.1: Date Picker on Morning Report)
 *
 * @see Story 17.1 - Date Picker on Morning Report
 * @see AC #2 - Date change reloads all data
 * @see AC #4 - URL-driven date on load
 * @see AC #5 - Empty state for missing data
 */

import { render, screen, fireEvent } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import { subDays, format, startOfDay } from 'date-fns'

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockPush = vi.fn()
const mockSearchParamsGet = vi.fn()

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush, replace: vi.fn(), back: vi.fn() }),
  useSearchParams: () => ({
    get: mockSearchParamsGet,
  }),
  usePathname: () => '/morning-report',
  useParams: () => ({}),
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

// Mock useWorkcenterSummary
const mockUseWorkcenterSummary = vi.fn()
vi.mock('@/hooks/useWorkcenterSummary', () => ({
  useWorkcenterSummary: (...args: unknown[]) => mockUseWorkcenterSummary(...args),
}))

// Mock useScheduleAttainment
const mockUseScheduleAttainment = vi.fn()
vi.mock('@/hooks/useScheduleAttainment', () => ({
  useScheduleAttainment: (...args: unknown[]) => mockUseScheduleAttainment(...args),
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

// Mock recharts
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
// Import AFTER mocks
// ---------------------------------------------------------------------------

import { MorningReportClient } from '../MorningReportClient'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const yesterday = startOfDay(subDays(new Date(), 1))
const yesterdayStr = format(yesterday, 'yyyy-MM-dd')

function setupDefaultMocks(overrides?: { dailyActionsData?: any }) {
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
    data: overrides?.dailyActionsData ?? {
      actions: [{ id: '1', title: 'Test Action', category: 'oee', priority_level: 'high', asset_name: 'Asset1', recommendation_text: 'Fix', evidence_summary: 'Data', evidence_refs: [], primary_metric_value: '80%', created_at: '2026-02-11', financial_impact_usd: 0, priority_rank: 1, description: 'Desc' }],
      generated_at: '2026-02-11T00:00:00Z',
      report_date: yesterdayStr,
      total_count: 1,
      counts_by_category: { safety: 0, oee: 1, financial: 0 },
    },
    isLoading: false,
    error: null,
    refetch: vi.fn(),
    hasActions: true,
    summary: {
      totalActions: 1,
      safetyCount: 0,
      oeeCount: 1,
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
      workcenters: [{ workcenter_name: 'Grinding', total_actual: 4200, total_target: 5000, attainment_percentage: 84.0, assets_on_target: 2, assets_missed: 2, total_assets: 4, assets: [] }],
      date: yesterdayStr,
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
      workcenters: [{ workcenter_name: 'Roasting', overall_attainment_pct: 92.5, products: [{ product_name: 'Brazilian', scheduled_quantity: 1000, actual_quantity: 950, attainment_pct: 95.0 }], variance_callouts: [] }],
      report_date: yesterdayStr,
      has_schedule: true,
    },
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  })
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('MorningReportClient', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockSearchParamsGet.mockReturnValue(null) // default: no date param
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('AC#4: URL-driven date on load', () => {
    it('[17-1-INT-001] defaults to yesterday when no date param is present', () => {
      mockSearchParamsGet.mockReturnValue(null)
      setupDefaultMocks()

      render(<MorningReportClient />)

      // useDailyActions should be called with yesterday's date
      expect(mockUseDailyActions).toHaveBeenCalledWith(
        expect.objectContaining({ reportDate: yesterdayStr })
      )
    })

    it('[17-1-INT-002] reads date from URL param when provided', () => {
      mockSearchParamsGet.mockReturnValue('2026-02-05')
      setupDefaultMocks()

      render(<MorningReportClient />)

      expect(mockUseDailyActions).toHaveBeenCalledWith(
        expect.objectContaining({ reportDate: '2026-02-05' })
      )
    })

    it('[17-1-INT-003] falls back to yesterday for invalid date strings', () => {
      mockSearchParamsGet.mockReturnValue('not-a-date')
      setupDefaultMocks()

      render(<MorningReportClient />)

      expect(mockUseDailyActions).toHaveBeenCalledWith(
        expect.objectContaining({ reportDate: yesterdayStr })
      )
    })

    it('[17-1-INT-004] falls back to yesterday for future dates', () => {
      mockSearchParamsGet.mockReturnValue('2099-01-01')
      setupDefaultMocks()

      render(<MorningReportClient />)

      expect(mockUseDailyActions).toHaveBeenCalledWith(
        expect.objectContaining({ reportDate: yesterdayStr })
      )
    })
  })

  describe('AC#2: Date change reloads all data', () => {
    it('[17-1-INT-005] passes reportDate to MorningSummarySection hooks', () => {
      mockSearchParamsGet.mockReturnValue('2026-02-05')
      setupDefaultMocks()

      render(<MorningReportClient />)

      // useDailyActions and useSmartSummary are called with reportDate
      // (MorningReportClient calls useDailyActions, and MorningSummarySection calls it too)
      const dailyActionsCalls = mockUseDailyActions.mock.calls
      const hasDateCall = dailyActionsCalls.some(
        (call: any[]) => call[0]?.reportDate === '2026-02-05'
      )
      expect(hasDateCall).toBe(true)

      const smartSummaryCalls = mockUseSmartSummary.mock.calls
      const hasSummaryDateCall = smartSummaryCalls.some(
        (call: any[]) => call[0]?.reportDate === '2026-02-05'
      )
      expect(hasSummaryDateCall).toBe(true)
    })

    it('[17-1-INT-006] passes date to WorkcenterScorecard hook', () => {
      mockSearchParamsGet.mockReturnValue('2026-02-05')
      setupDefaultMocks()

      render(<MorningReportClient />)

      const workcenterCalls = mockUseWorkcenterSummary.mock.calls
      const hasDateCall = workcenterCalls.some(
        (call: any[]) => call[0]?.date === '2026-02-05'
      )
      expect(hasDateCall).toBe(true)
    })

    it('[17-1-INT-007] passes date to ScheduleAttainment hook', () => {
      mockSearchParamsGet.mockReturnValue('2026-02-05')
      setupDefaultMocks()

      render(<MorningReportClient />)

      const scheduleCalls = mockUseScheduleAttainment.mock.calls
      const hasDateCall = scheduleCalls.some(
        (call: any[]) => call[0]?.date === '2026-02-05'
      )
      expect(hasDateCall).toBe(true)
    })
  })

  describe('AC#5: Empty state for missing data', () => {
    it('[17-1-INT-008] shows empty state when no actions exist for the selected date', () => {
      mockSearchParamsGet.mockReturnValue('2026-01-01')
      setupDefaultMocks({
        dailyActionsData: {
          actions: [],
          generated_at: '2026-01-01T00:00:00Z',
          report_date: '2026-01-01',
          total_count: 0,
          counts_by_category: { safety: 0, oee: 0, financial: 0 },
        },
      })

      render(<MorningReportClient />)

      expect(screen.getByText(/no production data available for/i)).toBeInTheDocument()
    })

    it('[17-1-INT-009] renders the page header even in empty state', () => {
      mockSearchParamsGet.mockReturnValue('2026-01-01')
      setupDefaultMocks({
        dailyActionsData: {
          actions: [],
          generated_at: '2026-01-01T00:00:00Z',
          report_date: '2026-01-01',
          total_count: 0,
          counts_by_category: { safety: 0, oee: 0, financial: 0 },
        },
      })

      render(<MorningReportClient />)

      expect(screen.getByRole('heading', { level: 1, name: 'Morning Report' })).toBeInTheDocument()
    })
  })

  describe('AC#1: Date picker placement', () => {
    it('[17-1-INT-010] renders the DateNavigation component in the summary section', () => {
      mockSearchParamsGet.mockReturnValue(null)
      setupDefaultMocks()

      render(<MorningReportClient />)

      // DateNavigation renders prev/next buttons
      expect(screen.getByRole('button', { name: /previous day/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /next day/i })).toBeInTheDocument()
    })

    it('[17-1-INT-011] displays the formatted date in the date picker trigger', () => {
      mockSearchParamsGet.mockReturnValue(null)
      setupDefaultMocks()

      render(<MorningReportClient />)

      const expectedDateText = format(yesterday, 'MMM d, yyyy')
      expect(screen.getByText(expectedDateText)).toBeInTheDocument()
    })
  })

  describe('AC#2: Dynamic badge text', () => {
    it('[17-1-INT-012] shows T-1 Data badge when viewing yesterday', () => {
      mockSearchParamsGet.mockReturnValue(null)
      setupDefaultMocks()

      render(<MorningReportClient />)

      expect(screen.getByText('T-1 Data')).toBeInTheDocument()
    })

    it('[17-1-INT-013] shows formatted date badge when viewing a different day', () => {
      mockSearchParamsGet.mockReturnValue('2026-02-05')
      setupDefaultMocks()

      render(<MorningReportClient />)

      expect(screen.getByText('Feb 5 Data')).toBeInTheDocument()
    })
  })

  describe('URL sync on date change', () => {
    it('[17-1-INT-014] calls router.push with updated date param on prev arrow click', () => {
      mockSearchParamsGet.mockReturnValue(null)
      setupDefaultMocks()

      render(<MorningReportClient />)

      const prevButton = screen.getByRole('button', { name: /previous day/i })
      fireEvent.click(prevButton)

      const expectedDate = format(subDays(yesterday, 1), 'yyyy-MM-dd')
      expect(mockPush).toHaveBeenCalledWith(
        `/morning-report?date=${expectedDate}`,
        { scroll: false }
      )
    })
  })
})
