/**
 * EvidenceSection Pareto Integration Tests (Story 14.5: Downtime Pareto Chart on Action Cards)
 *
 * TDD tests — these MUST FAIL until the Pareto chart integration into EvidenceSection
 * is implemented. Tests cover: conditional rendering for OEE vs safety/financial evidence,
 * prop threading (assetId, reportDate), skeleton → chart transitions, and error states.
 *
 * @see Story 14.5 - Downtime Pareto Chart on Action Cards
 * @see AC #1 - Pareto chart shows for OEE-miss / downtime-related items
 * @see AC #2 - No Pareto chart for safety-only or financial-only items
 * @see AC #3 - Skeleton loader while data is loading
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import React from 'react'

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), back: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => '/',
  useParams: () => ({}),
}))

// Mock Recharts so chart components render testable DOM
vi.mock('recharts', () => ({
  BarChart: ({ children, ...props }: Record<string, unknown>) =>
    React.createElement(
      'div',
      { 'data-testid': 'bar-chart', 'data-layout': props.layout },
      children as React.ReactNode,
    ),
  Bar: (props: Record<string, unknown>) =>
    React.createElement('div', { 'data-testid': 'bar', 'data-datakey': props.dataKey }),
  XAxis: () => React.createElement('div', { 'data-testid': 'x-axis' }),
  YAxis: () => React.createElement('div', { 'data-testid': 'y-axis' }),
  ResponsiveContainer: ({ children, ...props }: Record<string, unknown>) =>
    React.createElement(
      'div',
      { 'data-testid': 'responsive-container', 'data-height': props.height },
      children as React.ReactNode,
    ),
  Cell: () => React.createElement('div', { 'data-testid': 'cell' }),
  Tooltip: () => React.createElement('div', { 'data-testid': 'tooltip' }),
  LabelList: () => React.createElement('div', { 'data-testid': 'label-list' }),
}))

// Mock the useDowntimePareto hook so we control its state
const mockUseDowntimePareto = vi.fn()
vi.mock('@/hooks/useDowntimePareto', () => ({
  useDowntimePareto: (...args: unknown[]) => mockUseDowntimePareto(...args),
}))

// Mock Supabase client (needed by EvidenceSection if it calls hooks internally)
vi.mock('@/lib/supabase/client', () => ({
  createClient: () => ({
    auth: { getSession: vi.fn().mockResolvedValue({ data: { session: null } }) },
  }),
}))

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

import type { Evidence, OEEEvidence, SafetyEvidence, FinancialEvidence } from '../types'

const createOEEEvidence = (overrides: Partial<OEEEvidence> = {}): Evidence => ({
  type: 'oee_deviation',
  data: {
    targetOEE: 85,
    actualOEE: 72,
    deviation: 13,
    timeframe: 'Last 24 hours',
    ...overrides,
  },
  source: {
    table: 'daily_summaries',
    date: '2026-01-05',
    recordId: 'rec-001',
  },
})

const createSafetyEvidence = (overrides: Partial<SafetyEvidence> = {}): Evidence => ({
  type: 'safety_event',
  data: {
    eventId: 'evt-001',
    detectedAt: '2026-01-05T14:30:00Z',
    reasonCode: 'SAFETY_STOP',
    severity: 'high',
    assetName: 'Grinder 5',
    ...overrides,
  },
  source: {
    table: 'safety_events',
    date: '2026-01-05',
    recordId: 'rec-002',
  },
})

const createFinancialEvidence = (overrides: Partial<FinancialEvidence> = {}): Evidence => ({
  type: 'financial_loss',
  data: {
    downtimeCost: 5000,
    wasteCost: 2000,
    totalLoss: 7000,
    breakdown: [{ category: 'Labor', amount: 1500 }],
    ...overrides,
  },
  source: {
    table: 'financial_summaries',
    date: '2026-01-05',
    recordId: 'rec-003',
  },
})

interface ParetoItem {
  reason_code: string
  total_minutes: number
  percentage: number
  cumulative_percentage: number
  financial_impact: number
  event_count: number
  is_safety_related: boolean
}

const createMockParetoData = (items?: ParetoItem[]) => ({
  items: items ?? [
    {
      reason_code: 'Mechanical',
      total_minutes: 180,
      percentage: 35.5,
      cumulative_percentage: 35.5,
      financial_impact: 450.0,
      event_count: 3,
      is_safety_related: false,
    },
    {
      reason_code: 'Changeover',
      total_minutes: 120,
      percentage: 23.6,
      cumulative_percentage: 59.1,
      financial_impact: 300.0,
      event_count: 2,
      is_safety_related: false,
    },
    {
      reason_code: 'Planned Maintenance',
      total_minutes: 90,
      percentage: 17.7,
      cumulative_percentage: 76.8,
      financial_impact: 225.0,
      event_count: 1,
      is_safety_related: false,
    },
    {
      reason_code: 'Material Shortage',
      total_minutes: 60,
      percentage: 11.8,
      cumulative_percentage: 88.6,
      financial_impact: 150.0,
      event_count: 1,
      is_safety_related: false,
    },
  ],
  total_downtime_minutes: 450,
  total_financial_impact: 1125.0,
  total_events: 7,
  data_source: 'downtime_events',
  last_updated: '2026-01-05T12:00:00Z',
  threshold_80_index: 2,
})

// ---------------------------------------------------------------------------
// Import component AFTER mocks are set up
// ---------------------------------------------------------------------------

import { EvidenceSection } from '../EvidenceSection'

// ---------------------------------------------------------------------------
// Helper: expand the evidence section
// ---------------------------------------------------------------------------

function expandEvidence() {
  const expandButton = screen.getByRole('button', { name: /supporting evidence/i })
  fireEvent.click(expandButton)
}

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: Downtime Pareto Chart on Action Cards (Story 14.5)', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    // Default: hook returns no data, not loading
    mockUseDowntimePareto.mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // =========================================================================
  // AC2: No Pareto chart for safety-only or financial-only items
  // =========================================================================
  describe('AC2: No Pareto Chart for Non-OEE Evidence Types', () => {
    it('UNIT-022: No Pareto chart rendered for safety evidence type', () => {
      // Given: EvidenceSection receives evidence with type='safety_event'
      const evidence = createSafetyEvidence()

      // When: The component renders and the evidence section is expanded
      render(
        React.createElement(EvidenceSection, {
          evidence,
          assetId: 'asset-001',
          reportDate: '2026-01-05',
          defaultExpanded: true,
        })
      )

      // Then: No DowntimePareto component is rendered
      expect(screen.queryByText(/Downtime Breakdown/i)).not.toBeInTheDocument()
      expect(screen.queryByTestId('bar-chart')).not.toBeInTheDocument()

      // And: useDowntimePareto is called with enabled=false
      expect(mockUseDowntimePareto).toHaveBeenCalledWith(
        expect.objectContaining({ enabled: false })
      )
    })

    it('UNIT-023: No Pareto chart rendered for financial evidence type', () => {
      // Given: EvidenceSection receives evidence with type='financial_loss'
      const evidence = createFinancialEvidence()

      // When: The component renders and the evidence section is expanded
      render(
        React.createElement(EvidenceSection, {
          evidence,
          assetId: 'asset-001',
          reportDate: '2026-01-05',
          defaultExpanded: true,
        })
      )

      // Then: No DowntimePareto component is rendered
      expect(screen.queryByText(/Downtime Breakdown/i)).not.toBeInTheDocument()
      expect(screen.queryByTestId('bar-chart')).not.toBeInTheDocument()

      // And: useDowntimePareto is called with enabled=false
      expect(mockUseDowntimePareto).toHaveBeenCalledWith(
        expect.objectContaining({ enabled: false })
      )
    })
  })

  // =========================================================================
  // AC1 Integration: EvidenceSection renders Pareto chart for OEE evidence
  // =========================================================================
  describe('AC1 Integration: EvidenceSection with Pareto Chart', () => {
    it('INT-001: EvidenceSection renders Pareto chart for OEE evidence with available data', () => {
      // Given: EvidenceSection receives OEE evidence and useDowntimePareto returns data
      const evidence = createOEEEvidence()
      mockUseDowntimePareto.mockReturnValue({
        data: createMockParetoData(),
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      })

      // When: The evidence section is expanded
      render(
        React.createElement(EvidenceSection, {
          evidence,
          assetId: 'asset-001',
          reportDate: '2026-01-05',
          defaultExpanded: true,
        })
      )

      // Then: The DowntimePareto chart component is rendered
      expect(screen.getByText(/Downtime Breakdown/i)).toBeInTheDocument()
      expect(screen.getByTestId('bar-chart')).toBeInTheDocument()
    })

    it('INT-002: InsightEvidenceCard passes assetId and reportDate to EvidenceSection', () => {
      // Given: EvidenceSection receives assetId and reportDate props
      const evidence = createOEEEvidence()

      // When: The card renders
      render(
        React.createElement(EvidenceSection, {
          evidence,
          assetId: 'asset-001',
          reportDate: '2026-01-05',
          defaultExpanded: true,
        })
      )

      // Then: useDowntimePareto receives assetId='asset-001' and reportDate='2026-01-05'
      expect(mockUseDowntimePareto).toHaveBeenCalledWith(
        expect.objectContaining({
          assetId: 'asset-001',
          reportDate: '2026-01-05',
        })
      )
    })

    it('INT-003: Pareto hook receives correct parameters from EvidenceSection', () => {
      // Given: EvidenceSection has assetId='asset-001', reportDate='2026-01-05', evidence type is 'oee_deviation'
      const evidence = createOEEEvidence()

      // When: The component mounts
      render(
        React.createElement(EvidenceSection, {
          evidence,
          assetId: 'asset-001',
          reportDate: '2026-01-05',
          defaultExpanded: true,
        })
      )

      // Then: useDowntimePareto is called with correct params including enabled=true
      expect(mockUseDowntimePareto).toHaveBeenCalledWith({
        assetId: 'asset-001',
        reportDate: '2026-01-05',
        enabled: true,
      })
    })
  })

  // =========================================================================
  // AC2 Integration: Hook disabled for missing props
  // =========================================================================
  describe('AC2 Integration: Hook Disabled for Missing Props', () => {
    it('INT-004: Hook not enabled when assetId is missing', () => {
      // Given: EvidenceSection receives OEE evidence but assetId prop is undefined
      const evidence = createOEEEvidence()

      // When: The component renders
      render(
        React.createElement(EvidenceSection, {
          evidence,
          assetId: undefined,
          reportDate: '2026-01-05',
          defaultExpanded: true,
        })
      )

      // Then: useDowntimePareto is called with enabled=false
      expect(mockUseDowntimePareto).toHaveBeenCalledWith(
        expect.objectContaining({ enabled: false })
      )

      // And: No Pareto chart is rendered
      expect(screen.queryByTestId('bar-chart')).not.toBeInTheDocument()
    })

    it('INT-005: Hook not enabled when reportDate is missing', () => {
      // Given: EvidenceSection receives OEE evidence but reportDate prop is undefined
      const evidence = createOEEEvidence()

      // When: The component renders
      render(
        React.createElement(EvidenceSection, {
          evidence,
          assetId: 'asset-001',
          reportDate: undefined,
          defaultExpanded: true,
        })
      )

      // Then: useDowntimePareto is called with enabled=false
      expect(mockUseDowntimePareto).toHaveBeenCalledWith(
        expect.objectContaining({ enabled: false })
      )

      // And: No Pareto chart is rendered
      expect(screen.queryByTestId('bar-chart')).not.toBeInTheDocument()
    })
  })

  // =========================================================================
  // AC3 Integration: Skeleton and loading states
  // =========================================================================
  describe('AC3 Integration: Skeleton and Loading States', () => {
    it('INT-006: EvidenceSection shows skeleton while Pareto data is loading', () => {
      // Given: EvidenceSection receives OEE evidence and useDowntimePareto returns loading state
      const evidence = createOEEEvidence()
      mockUseDowntimePareto.mockReturnValue({
        data: null,
        isLoading: true,
        error: null,
        refetch: vi.fn(),
      })

      // When: The evidence section is expanded
      render(
        React.createElement(EvidenceSection, {
          evidence,
          assetId: 'asset-001',
          reportDate: '2026-01-05',
          defaultExpanded: true,
        })
      )

      // Then: DowntimeParetoSkeleton is rendered in place of the chart
      const skeletonElements = document.querySelectorAll('.animate-pulse')
      // Should find skeleton pulse elements specific to the Pareto area
      expect(skeletonElements.length).toBeGreaterThan(0)

      // And: No actual chart is shown
      expect(screen.queryByTestId('bar-chart')).not.toBeInTheDocument()
    })

    it('INT-007: Skeleton transitions to chart when data loads', async () => {
      // Given: EvidenceSection initially shows skeleton while useDowntimePareto is loading
      const evidence = createOEEEvidence()

      // Start in loading state
      mockUseDowntimePareto.mockReturnValue({
        data: null,
        isLoading: true,
        error: null,
        refetch: vi.fn(),
      })

      const { rerender } = render(
        React.createElement(EvidenceSection, {
          evidence,
          assetId: 'asset-001',
          reportDate: '2026-01-05',
          defaultExpanded: true,
        })
      )

      // Verify skeleton is showing
      expect(screen.queryByTestId('bar-chart')).not.toBeInTheDocument()

      // When: The hook resolves with Pareto data
      mockUseDowntimePareto.mockReturnValue({
        data: createMockParetoData(),
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      })

      rerender(
        React.createElement(EvidenceSection, {
          evidence,
          assetId: 'asset-001',
          reportDate: '2026-01-05',
          defaultExpanded: true,
        })
      )

      // Then: The skeleton is replaced by the DowntimePareto chart
      expect(screen.getByTestId('bar-chart')).toBeInTheDocument()
      expect(screen.getByText(/Downtime Breakdown/i)).toBeInTheDocument()
    })

    it('INT-008: No chart or skeleton shown when hook returns error', () => {
      // Given: EvidenceSection receives OEE evidence and useDowntimePareto returns error
      const evidence = createOEEEvidence()
      mockUseDowntimePareto.mockReturnValue({
        data: null,
        isLoading: false,
        error: 'Network error',
        refetch: vi.fn(),
      })

      // When: The evidence section is expanded
      render(
        React.createElement(EvidenceSection, {
          evidence,
          assetId: 'asset-001',
          reportDate: '2026-01-05',
          defaultExpanded: true,
        })
      )

      // Then: Neither chart nor skeleton is rendered
      expect(screen.queryByTestId('bar-chart')).not.toBeInTheDocument()
      expect(screen.queryByText(/Downtime Breakdown/i)).not.toBeInTheDocument()

      // And: The OEE evidence content still displays normally
      expect(screen.getByText(/OEE Performance/i)).toBeInTheDocument()
    })
  })
})
