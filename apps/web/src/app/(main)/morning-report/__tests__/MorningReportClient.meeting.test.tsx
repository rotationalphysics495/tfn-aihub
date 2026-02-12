/**
 * MorningReportClient Meeting Mode Integration Tests (Story 18.1)
 *
 * TDD tests — these MUST FAIL until meeting mode is integrated into MorningReportClient.
 * Tests cover toggle activation, URL state management, mode initialization from URL,
 * and view switching between normal and meeting modes.
 *
 * @see Story 18.1 - Meeting Mode Toggle & Talking Points View
 * @see AC #1 - Toggle switches to condensed meeting mode layout
 * @see AC #3 - Toggle back restores full report view
 * @see AC #4 - URL ?mode=meeting activates meeting mode on load
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'

// ---------------------------------------------------------------------------
// Mock state holders (declared BEFORE vi.mock calls)
// ---------------------------------------------------------------------------

const mockRouterPush = vi.fn()
const mockSearchParamsGet = vi.fn()
let mockSearchParamsToString = ''

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockRouterPush,
    refresh: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
  }),
  useSearchParams: () => ({
    get: mockSearchParamsGet,
    toString: () => mockSearchParamsToString,
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

// Mock useSafetyAlerts
const mockUseSafetyAlerts = vi.fn()
vi.mock('@/hooks/useSafetyAlerts', () => ({
  useSafetyAlerts: (...args: unknown[]) => mockUseSafetyAlerts(...args),
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

// Mock Supabase client
vi.mock('@/lib/supabase/client', () => ({
  createClient: () => ({
    auth: {
      getSession: vi.fn().mockResolvedValue({
        data: { session: { access_token: 'mock-token' } },
      }),
    },
    from: () => ({
      select: () => ({
        eq: () => ({
          order: () => Promise.resolve({ data: [], error: null }),
        }),
      }),
    }),
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

const mockFetch = vi.fn()
global.fetch = mockFetch

// ---------------------------------------------------------------------------
// Imports (AFTER mocks)
// ---------------------------------------------------------------------------

import { MorningReportClient } from '../MorningReportClient'

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

function createMockDailyActionsData(actionCount = 3) {
  const categories = ['safety', 'oee', 'financial'] as const
  const actions = Array.from({ length: actionCount }, (_, i) => ({
    action_item_id: `action-${i + 1}`,
    category: categories[i % 3],
    priority_level: i === 0 ? 'critical' : i === 1 ? 'high' : 'medium',
    priority_score: 900 - i * 100,
    recommendation_text: `Recommendation for item ${i + 1}`,
    recommendation_summary: `Summary ${i + 1}`,
    asset_id: `asset-${i + 1}`,
    asset_name: `Asset-${i + 1}`,
    asset_area: 'Production',
    evidence_type: categories[i % 3] === 'safety' ? 'safety_event' : categories[i % 3] === 'oee' ? 'oee_deviation' : 'financial_loss',
    evidence_data: {},
    evidence_source_table: 'daily_summaries',
    evidence_source_date: '2026-02-10',
    evidence_source_record_id: `rec-${i + 1}`,
    financial_impact: 2000 - i * 200,
    generated_at: '2026-02-10T06:00:00Z',
  }))

  return {
    actions,
    date: '2026-02-10',
    generated_at: '2026-02-10T06:00:00Z',
    summary: {
      total_actions: actionCount,
      safety_count: actions.filter(a => a.category === 'safety').length,
      oee_count: actions.filter(a => a.category === 'oee').length,
      financial_count: actions.filter(a => a.category === 'financial').length,
      total_financial_impact: actions.reduce((sum, a) => sum + a.financial_impact, 0),
    },
  }
}

function setupDefaultMocks() {
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
    data: createMockDailyActionsData(3),
    isLoading: false,
    error: null,
    refetch: vi.fn(),
    hasActions: true,
    summary: {
      totalActions: 3,
      safetyCount: 1,
      oeeCount: 1,
      financialCount: 1,
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
      workcenters: [],
      date: '2026-02-10',
      total_actual: 0,
      total_target: 0,
      total_attainment: 0,
    },
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  })

  mockUseScheduleAttainment.mockReturnValue({
    data: { workcenters: [], report_date: '2026-02-10', has_schedule: false },
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  })

  mockFetch.mockResolvedValue({
    ok: true,
    status: 200,
    json: async () => ({ members: [] }),
  })
}

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: Meeting Mode integration in MorningReportClient (Story 18.1)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockRouterPush.mockReset()
    mockSearchParamsGet.mockReset()
    mockSearchParamsToString = ''
    mockFetch.mockReset()
    setupDefaultMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // =========================================================================
  // AC1: Toggle activates meeting mode and updates URL
  // =========================================================================
  describe('AC1: Toggle activates meeting mode', () => {
    it('INT-001: Toggle activates meeting mode and updates URL', () => {
      // Given: MorningReportClient is rendered in normal mode (no ?mode=meeting in URL)
      mockSearchParamsGet.mockImplementation((key: string) => {
        if (key === 'mode') return null
        if (key === 'date') return null
        if (key === 'shift') return null
        return null
      })
      mockSearchParamsToString = ''

      render(<MorningReportClient />)

      // When: The user clicks the "Meeting Mode" toggle button
      const toggleButton = screen.getByRole('button', { name: /meeting mode/i })
      fireEvent.click(toggleButton)

      // Then: The MeetingModeView layout is rendered (condensed cards visible)
      expect(screen.getByText('Safety')).toBeInTheDocument()
      expect(screen.getByText("Yesterday's Performance")).toBeInTheDocument()
      expect(screen.getByText("Today's Priorities")).toBeInTheDocument()

      // And: The normal report sections are hidden
      expect(screen.queryByRole('region', { name: /action items with evidence/i })).not.toBeInTheDocument()

      // And: router.push is called with URL containing mode=meeting parameter
      expect(mockRouterPush).toHaveBeenCalled()
      const pushArg = mockRouterPush.mock.calls[0][0] as string
      expect(pushArg).toContain('mode=meeting')
    })

    it('INT-002: URL preserves existing date and shift params when toggling meeting mode', () => {
      // Given: MorningReportClient is rendered with URL params ?date=2026-02-05&shift=day
      mockSearchParamsGet.mockImplementation((key: string) => {
        if (key === 'date') return '2026-02-05'
        if (key === 'shift') return 'day'
        if (key === 'mode') return null
        return null
      })
      mockSearchParamsToString = 'date=2026-02-05&shift=day'

      render(<MorningReportClient />)

      // When: The user clicks the "Meeting Mode" toggle button
      const toggleButton = screen.getByRole('button', { name: /meeting mode/i })
      fireEvent.click(toggleButton)

      // Then: router.push is called with URL containing all three params
      expect(mockRouterPush).toHaveBeenCalled()
      const pushArg = mockRouterPush.mock.calls[mockRouterPush.mock.calls.length - 1][0] as string
      expect(pushArg).toContain('date=2026-02-05')
      expect(pushArg).toContain('shift=day')
      expect(pushArg).toContain('mode=meeting')
    })
  })

  // =========================================================================
  // AC2: Follow-up data in meeting mode
  // =========================================================================
  describe('AC2: Follow-up data integration', () => {
    it('INT-003: Meeting mode view passes follow-up data to talking point cards', () => {
      // Given: MorningReportClient is in meeting mode with 3 action items and follow-ups for 2
      mockSearchParamsGet.mockImplementation((key: string) => {
        if (key === 'mode') return 'meeting'
        return null
      })
      mockSearchParamsToString = 'mode=meeting'

      render(<MorningReportClient />)

      // When: The component mounts in meeting mode
      // Then: The 2 items with follow-ups render AssignmentBadges
      // And: The 1 item without a follow-up renders the "Assign Follow-Up" button
      // (This test will fail because MeetingModeView doesn't exist yet)
      expect(screen.getByText('Safety')).toBeInTheDocument()
      expect(screen.getByText("Yesterday's Performance")).toBeInTheDocument()
      expect(screen.getByText("Today's Priorities")).toBeInTheDocument()

      // Verify at least one "Assign Follow-Up" button exists
      const assignButtons = screen.getAllByRole('button', { name: /assign follow-up/i })
      expect(assignButtons.length).toBeGreaterThanOrEqual(1)
    })
  })

  // =========================================================================
  // AC3: Toggle back to normal mode
  // =========================================================================
  describe('AC3: Toggle back restores normal view', () => {
    it('INT-004: Toggle back to normal mode restores full report view', () => {
      // Given: MorningReportClient is rendered in meeting mode
      mockSearchParamsGet.mockImplementation((key: string) => {
        if (key === 'mode') return 'meeting'
        return null
      })
      mockSearchParamsToString = 'mode=meeting'

      render(<MorningReportClient />)

      // Verify meeting mode is active
      expect(screen.getByRole('button', { name: /meeting mode/i })).toHaveAttribute(
        'aria-pressed',
        'true'
      )

      // When: The user clicks the "Meeting Mode" toggle button again
      const toggleButton = screen.getByRole('button', { name: /meeting mode/i })
      fireEvent.click(toggleButton)

      // Then: The MeetingModeView is no longer rendered
      // And: Normal mode components are restored
      expect(screen.getByRole('region', { name: /action items with evidence/i })).toBeInTheDocument()

      // And: router.push is called with URL that does NOT contain mode=meeting
      expect(mockRouterPush).toHaveBeenCalled()
      const lastPushArg = mockRouterPush.mock.calls[mockRouterPush.mock.calls.length - 1][0] as string
      expect(lastPushArg).not.toContain('mode=meeting')
    })

    it('INT-005: Toggle back preserves date and shift params in URL', () => {
      // Given: MorningReportClient is in meeting mode with URL ?date=2026-02-05&shift=day&mode=meeting
      mockSearchParamsGet.mockImplementation((key: string) => {
        if (key === 'date') return '2026-02-05'
        if (key === 'shift') return 'day'
        if (key === 'mode') return 'meeting'
        return null
      })
      mockSearchParamsToString = 'date=2026-02-05&shift=day&mode=meeting'

      render(<MorningReportClient />)

      // When: The user clicks the toggle to switch back to normal mode
      const toggleButton = screen.getByRole('button', { name: /meeting mode/i })
      fireEvent.click(toggleButton)

      // Then: router.push is called with URL containing date and shift but NOT mode=meeting
      expect(mockRouterPush).toHaveBeenCalled()
      const lastPushArg = mockRouterPush.mock.calls[mockRouterPush.mock.calls.length - 1][0] as string
      expect(lastPushArg).toContain('date=2026-02-05')
      expect(lastPushArg).toContain('shift=day')
      expect(lastPushArg).not.toContain('mode=meeting')
    })

    it('INT-006: Normal mode data is not re-fetched on toggle back', () => {
      // Given: MorningReportClient is rendered, user toggles to meeting mode
      mockSearchParamsGet.mockImplementation((key: string) => {
        if (key === 'mode') return null
        return null
      })
      mockSearchParamsToString = ''

      render(<MorningReportClient />)

      const callCountAfterMount = mockUseDailyActions.mock.calls.length

      // When: User toggles to meeting mode
      const toggleButton = screen.getByRole('button', { name: /meeting mode/i })
      fireEvent.click(toggleButton)

      // And: Then toggles back to normal mode
      fireEvent.click(toggleButton)

      // Then: useDailyActions is NOT called with new arguments (same data reused)
      // The hook should be called during render cycles but not with different args
      const allCalls = mockUseDailyActions.mock.calls
      const uniqueArgs = new Set(allCalls.map((c: any) => JSON.stringify(c)))
      // All calls should have the same arguments (same reportDate)
      expect(uniqueArgs.size).toBeLessThanOrEqual(1)
    })
  })

  // =========================================================================
  // AC4: Meeting mode from URL on initial page load
  // =========================================================================
  describe('AC4: Meeting mode from URL', () => {
    it('INT-007: Meeting mode activates from URL on initial page load', () => {
      // Given: The URL search params include mode=meeting
      mockSearchParamsGet.mockImplementation((key: string) => {
        if (key === 'mode') return 'meeting'
        return null
      })
      mockSearchParamsToString = 'mode=meeting'

      // When: MorningReportClient mounts
      render(<MorningReportClient />)

      // Then: The MeetingModeView is rendered immediately
      expect(screen.getByText('Safety')).toBeInTheDocument()
      expect(screen.getByText("Yesterday's Performance")).toBeInTheDocument()
      expect(screen.getByText("Today's Priorities")).toBeInTheDocument()

      // And: The MeetingModeToggle shows pressed=true (aria-pressed="true")
      const toggleButton = screen.getByRole('button', { name: /meeting mode/i })
      expect(toggleButton).toHaveAttribute('aria-pressed', 'true')

      // And: Normal mode sections are not rendered
      expect(screen.queryByRole('region', { name: /action items with evidence/i })).not.toBeInTheDocument()
    })

    it('INT-008: Meeting mode does not activate for non-matching mode param values', () => {
      // Given: The URL search params include mode=presentation (not "meeting")
      mockSearchParamsGet.mockImplementation((key: string) => {
        if (key === 'mode') return 'presentation'
        return null
      })
      mockSearchParamsToString = 'mode=presentation'

      // When: MorningReportClient mounts
      render(<MorningReportClient />)

      // Then: Normal mode is rendered (MeetingModeView is NOT shown)
      expect(screen.getByRole('region', { name: /action items with evidence/i })).toBeInTheDocument()

      // And: MeetingModeToggle shows pressed=false
      const toggleButton = screen.getByRole('button', { name: /meeting mode/i })
      expect(toggleButton).toHaveAttribute('aria-pressed', 'false')
    })

    it('INT-009: Meeting mode activates from URL with combined date param', () => {
      // Given: The URL search params include date=2026-02-05&mode=meeting
      mockSearchParamsGet.mockImplementation((key: string) => {
        if (key === 'date') return '2026-02-05'
        if (key === 'mode') return 'meeting'
        return null
      })
      mockSearchParamsToString = 'date=2026-02-05&mode=meeting'

      // When: MorningReportClient mounts
      render(<MorningReportClient />)

      // Then: Meeting mode is activated
      expect(screen.getByText('Safety')).toBeInTheDocument()
      const toggleButton = screen.getByRole('button', { name: /meeting mode/i })
      expect(toggleButton).toHaveAttribute('aria-pressed', 'true')

      // And: useDailyActions is called with reportDate: '2026-02-05'
      expect(mockUseDailyActions).toHaveBeenCalled()
      const lastCall = mockUseDailyActions.mock.calls[mockUseDailyActions.mock.calls.length - 1]
      expect(lastCall[0]).toEqual(expect.objectContaining({ reportDate: '2026-02-05' }))
    })

    it('INT-010: Normal mode is default when no mode param exists', () => {
      // Given: The URL has no mode search parameter
      mockSearchParamsGet.mockImplementation((key: string) => {
        if (key === 'mode') return null
        return null
      })
      mockSearchParamsToString = ''

      // When: MorningReportClient mounts
      render(<MorningReportClient />)

      // Then: Normal mode is rendered
      expect(screen.getByRole('region', { name: /action items with evidence/i })).toBeInTheDocument()

      // And: MeetingModeToggle shows pressed=false
      const toggleButton = screen.getByRole('button', { name: /meeting mode/i })
      expect(toggleButton).toHaveAttribute('aria-pressed', 'false')

      // And: Full report sections are visible
      expect(screen.getByRole('heading', { level: 1, name: /morning report/i })).toBeInTheDocument()
    })
  })
})
