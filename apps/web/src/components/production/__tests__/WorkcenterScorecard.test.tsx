/**
 * WorkcenterScorecard Component Tests (Story 11.2: Workcenter Scorecard UI Component)
 *
 * TDD tests — these MUST FAIL until the component is implemented.
 *
 * @see Story 11.2 - Workcenter Scorecard UI Component
 * @see AC #1 - Scorecard with workcenter rows, attainment color coding, asset counts
 * @see AC #2 - Expandable workcenter rows with per-asset breakdown
 * @see AC #3 - Empty state when no workcenter data
 * @see AC #4 - Glanceability / tablet readability (NFR-I1)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

// ---------------------------------------------------------------------------
// Types (matching API contract from Story 11.1)
// ---------------------------------------------------------------------------

interface AssetDetail {
  asset_name: string
  actual: number
  target: number
  oee: number | null
  downtime_minutes: number | null
}

interface WorkcenterEntry {
  workcenter_name: string
  total_actual: number
  total_target: number
  attainment_percentage: number
  assets_on_target: number
  assets_missed: number
  total_assets: number
  assets: AssetDetail[]
}

interface WorkcenterSummaryResponse {
  workcenters: WorkcenterEntry[]
  date: string
  total_actual: number
  total_target: number
  total_attainment: number
  message?: string | null
}

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockRefetch = vi.fn()

// Mock the useWorkcenterSummary hook
const mockUseWorkcenterSummary = vi.fn()
vi.mock('@/hooks/useWorkcenterSummary', () => ({
  useWorkcenterSummary: (...args: unknown[]) => mockUseWorkcenterSummary(...args),
}))

// Mock Supabase client (required by setup)
vi.mock('@/lib/supabase/client', () => ({
  createClient: () => ({
    auth: {
      getSession: vi.fn().mockResolvedValue({
        data: { session: { access_token: 'mock-token' } },
      }),
    },
  }),
}))

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const createAssetDetail = (overrides: Partial<AssetDetail> = {}): AssetDetail => ({
  asset_name: 'Grinder 1',
  actual: 1200,
  target: 1300,
  oee: 85.2,
  downtime_minutes: 45,
  ...overrides,
})

const createWorkcenterEntry = (overrides: Partial<WorkcenterEntry> = {}): WorkcenterEntry => ({
  workcenter_name: 'Grinding',
  total_actual: 4200,
  total_target: 5000,
  attainment_percentage: 84.0,
  assets_on_target: 2,
  assets_missed: 2,
  total_assets: 4,
  assets: [
    createAssetDetail({ asset_name: 'Grinder 1', actual: 1200, target: 1300, oee: 85.2, downtime_minutes: 45 }),
    createAssetDetail({ asset_name: 'Grinder 2', actual: 1500, target: 1400, oee: 92.0, downtime_minutes: 10 }),
    createAssetDetail({ asset_name: 'Grinder 3', actual: 1500, target: 1300, oee: 88.5, downtime_minutes: 20 }),
  ],
  ...overrides,
})

const createMockResponse = (
  workcenters: WorkcenterEntry[] = [],
  overrides: Partial<WorkcenterSummaryResponse> = {}
): WorkcenterSummaryResponse => ({
  workcenters,
  date: '2026-02-10',
  total_actual: workcenters.reduce((sum, w) => sum + w.total_actual, 0),
  total_target: workcenters.reduce((sum, w) => sum + w.total_target, 0),
  total_attainment: 90.0,
  ...overrides,
})

const createDefaultThreeWorkcenters = (): WorkcenterEntry[] => [
  createWorkcenterEntry({
    workcenter_name: 'Grinding',
    total_actual: 4200,
    total_target: 5000,
    attainment_percentage: 84.0,
    assets_on_target: 2,
    assets_missed: 2,
    total_assets: 4,
  }),
  createWorkcenterEntry({
    workcenter_name: 'Assembly',
    total_actual: 9500,
    total_target: 10000,
    attainment_percentage: 95.0,
    assets_on_target: 3,
    assets_missed: 1,
    total_assets: 4,
  }),
  createWorkcenterEntry({
    workcenter_name: 'Packaging',
    total_actual: 7800,
    total_target: 8500,
    attainment_percentage: 91.8,
    assets_on_target: 2,
    assets_missed: 1,
    total_assets: 3,
  }),
]

const mockHookReturn = (overrides: Record<string, unknown> = {}) => ({
  data: null,
  isLoading: false,
  error: null,
  refetch: mockRefetch,
  ...overrides,
})

// ---------------------------------------------------------------------------
// Import components AFTER mocks are set up
// ---------------------------------------------------------------------------

import { WorkcenterScorecard } from '../WorkcenterScorecard'
import { WorkcenterRow } from '../WorkcenterRow'
import { AssetDetailTable } from '../AssetDetailTable'

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: Workcenter Scorecard UI Component (Story 11.2)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockRefetch.mockReset()
    // Default: successful data load
    mockUseWorkcenterSummary.mockReturnValue(
      mockHookReturn({
        data: createMockResponse(createDefaultThreeWorkcenters()),
      })
    )
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // =========================================================================
  // AC1: Scorecard rows with workcenter data, color coding, asset counts
  // =========================================================================
  describe('AC1: Workcenter scorecard rows with attainment and color coding', () => {
    it('UNIT-001: Renders one WorkcenterRow per workcenter entry', () => {
      // Given: useWorkcenterSummary returns data with 3 workcenter entries
      const workcenters = createDefaultThreeWorkcenters()
      mockUseWorkcenterSummary.mockReturnValue(
        mockHookReturn({ data: createMockResponse(workcenters) })
      )

      // When: WorkcenterScorecard renders
      render(<WorkcenterScorecard />)

      // Then: exactly 3 workcenter rows are displayed with corresponding names
      expect(screen.getByText('Grinding')).toBeInTheDocument()
      expect(screen.getByText('Assembly')).toBeInTheDocument()
      expect(screen.getByText('Packaging')).toBeInTheDocument()
    })

    it('UNIT-002: Displays workcenter name in each row', () => {
      // Given: useWorkcenterSummary returns data with workcenter "Grinding"
      const entry = createWorkcenterEntry({ workcenter_name: 'Grinding' })

      // When: WorkcenterRow renders
      const { container } = render(<WorkcenterRow entry={entry} />)

      // Then: "Grinding" is visible with font-semibold class
      const nameElement = screen.getByText('Grinding')
      expect(nameElement).toBeInTheDocument()
      expect(nameElement).toHaveClass('font-semibold')
    })

    it('UNIT-003: Displays actual vs target with comma formatting', () => {
      // Given: workcenter with total_actual: 4200 and total_target: 5000
      const entry = createWorkcenterEntry({
        total_actual: 4200,
        total_target: 5000,
      })

      // When: WorkcenterRow renders
      render(<WorkcenterRow entry={entry} />)

      // Then: the output displays "4,200 / 5,000"
      expect(screen.getByText('4,200 / 5,000')).toBeInTheDocument()
    })

    it('UNIT-004: Displays attainment percentage with one decimal', () => {
      // Given: workcenter with attainment_percentage: 95.2
      const entry = createWorkcenterEntry({ attainment_percentage: 95.2 })

      // When: WorkcenterRow renders
      render(<WorkcenterRow entry={entry} />)

      // Then: "95.2%" is visible
      expect(screen.getByText('95.2%')).toBeInTheDocument()
    })

    it('UNIT-005: Green color coding for attainment >= 95%', () => {
      // Given: workcenter with attainment_percentage: 95.0
      const entry = createWorkcenterEntry({ attainment_percentage: 95.0 })

      // When: WorkcenterRow renders
      const { container } = render(<WorkcenterRow entry={entry} />)

      // Then: the percentage element has green color classes
      const pctElement = screen.getByText('95.0%')
      expect(pctElement).toHaveClass('text-success-green-dark')
    })

    it('UNIT-006: Green color coding for attainment at exactly 95%', () => {
      // Given: attainment_percentage: 95.0 (boundary value)
      const entry = createWorkcenterEntry({ attainment_percentage: 95.0 })

      // When: WorkcenterRow renders
      render(<WorkcenterRow entry={entry} />)

      // Then: the percentage element has green color classes (>= 95% is inclusive)
      const pctElement = screen.getByText('95.0%')
      expect(pctElement.className).toMatch(/text-success-green/)
    })

    it('UNIT-007: Yellow color coding for attainment 85-94%', () => {
      // Given: workcenter with attainment_percentage: 91.8
      const entry = createWorkcenterEntry({ attainment_percentage: 91.8 })

      // When: WorkcenterRow renders
      render(<WorkcenterRow entry={entry} />)

      // Then: the percentage element has yellow/amber color classes
      const pctElement = screen.getByText('91.8%')
      expect(pctElement).toHaveClass('text-warning-amber-dark')
    })

    it('UNIT-008: Yellow color coding at exactly 85% boundary', () => {
      // Given: attainment_percentage: 85.0 (lower boundary of yellow)
      const entry = createWorkcenterEntry({ attainment_percentage: 85.0 })

      // When: WorkcenterRow renders
      render(<WorkcenterRow entry={entry} />)

      // Then: the percentage element has yellow/amber color classes
      const pctElement = screen.getByText('85.0%')
      expect(pctElement.className).toMatch(/text-warning-amber/)
    })

    it('UNIT-009: Red color coding for attainment < 85%', () => {
      // Given: workcenter with attainment_percentage: 72.5
      const entry = createWorkcenterEntry({ attainment_percentage: 72.5 })

      // When: WorkcenterRow renders
      render(<WorkcenterRow entry={entry} />)

      // Then: the percentage element has red color class
      const pctElement = screen.getByText('72.5%')
      expect(pctElement).toHaveClass('text-safety-red')
    })

    it('UNIT-010: Red color coding at 84.9% (just below yellow boundary)', () => {
      // Given: attainment_percentage: 84.9 (just below 85 threshold)
      const entry = createWorkcenterEntry({ attainment_percentage: 84.9 })

      // When: WorkcenterRow renders
      render(<WorkcenterRow entry={entry} />)

      // Then: the percentage element has red color class
      const pctElement = screen.getByText('84.9%')
      expect(pctElement).toHaveClass('text-safety-red')
    })

    it('UNIT-011: Displays asset hit/miss count in readable format', () => {
      // Given: workcenter with assets_on_target: 3, assets_missed: 1
      const entry = createWorkcenterEntry({
        assets_on_target: 3,
        assets_missed: 1,
        total_assets: 4,
      })

      // When: WorkcenterRow renders
      render(<WorkcenterRow entry={entry} />)

      // Then: "3 of 4 assets on target" is visible
      expect(screen.getByText('3 of 4 assets on target')).toBeInTheDocument()
    })

    it('UNIT-012: Section header displays "Production Scorecard"', () => {
      // Given: useWorkcenterSummary returns valid data
      mockUseWorkcenterSummary.mockReturnValue(
        mockHookReturn({
          data: createMockResponse(createDefaultThreeWorkcenters()),
        })
      )

      // When: WorkcenterScorecard renders
      render(<WorkcenterScorecard />)

      // Then: "Production Scorecard" heading is visible
      expect(screen.getByText('Production Scorecard')).toBeInTheDocument()
    })

    it('UNIT-013: Loading skeleton displayed while fetching data', () => {
      // Given: useWorkcenterSummary returns isLoading: true, data: null
      mockUseWorkcenterSummary.mockReturnValue(
        mockHookReturn({ isLoading: true, data: null, error: null })
      )

      // When: WorkcenterScorecard renders
      const { container } = render(<WorkcenterScorecard />)

      // Then: skeleton placeholders are visible (not workcenter rows, not error)
      expect(container.querySelector('.animate-pulse')).toBeInTheDocument()
      expect(screen.queryByText('Grinding')).not.toBeInTheDocument()
      expect(screen.queryByText('Production Scorecard')).toBeInTheDocument()
    })

    it('UNIT-014: Error state with retry button on fetch failure', () => {
      // Given: useWorkcenterSummary returns error
      mockUseWorkcenterSummary.mockReturnValue(
        mockHookReturn({
          isLoading: false,
          data: null,
          error: 'Failed to load workcenter data',
        })
      )

      // When: WorkcenterScorecard renders
      render(<WorkcenterScorecard />)

      // Then: an error message is visible, AlertCircle icon present, retry button available
      expect(screen.getByText(/Failed to load workcenter data/)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /try again|retry/i })).toBeInTheDocument()
    })

    it('UNIT-015: Retry button calls refetch', async () => {
      // Given: WorkcenterScorecard is in error state
      mockUseWorkcenterSummary.mockReturnValue(
        mockHookReturn({
          isLoading: false,
          data: null,
          error: 'Failed to load workcenter data',
          refetch: mockRefetch,
        })
      )

      // When: the user clicks the retry button
      render(<WorkcenterScorecard />)
      const retryButton = screen.getByRole('button', { name: /try again|retry/i })
      await userEvent.click(retryButton)

      // Then: refetch is called exactly once
      expect(mockRefetch).toHaveBeenCalledTimes(1)
    })

    it('UNIT-016: Large numbers formatted with commas', () => {
      // Given: workcenter with total_actual: 12500, total_target: 15000
      const entry = createWorkcenterEntry({
        total_actual: 12500,
        total_target: 15000,
      })

      // When: WorkcenterRow renders
      render(<WorkcenterRow entry={entry} />)

      // Then: "12,500 / 15,000" is displayed
      expect(screen.getByText('12,500 / 15,000')).toBeInTheDocument()
    })

    it('UNIT-017: Zero values displayed correctly', () => {
      // Given: workcenter with total_actual: 0, total_target: 5000, attainment_percentage: 0.0
      const entry = createWorkcenterEntry({
        total_actual: 0,
        total_target: 5000,
        attainment_percentage: 0.0,
      })

      // When: WorkcenterRow renders
      render(<WorkcenterRow entry={entry} />)

      // Then: "0 / 5,000" and "0.0%" with red color coding
      expect(screen.getByText('0 / 5,000')).toBeInTheDocument()
      const pctElement = screen.getByText('0.0%')
      expect(pctElement).toBeInTheDocument()
      expect(pctElement).toHaveClass('text-safety-red')
    })

    it('UNIT-018: 100% attainment renders with green color', () => {
      // Given: workcenter with attainment_percentage: 100.0
      const entry = createWorkcenterEntry({
        attainment_percentage: 100.0,
        total_actual: 5000,
        total_target: 5000,
      })

      // When: WorkcenterRow renders
      render(<WorkcenterRow entry={entry} />)

      // Then: "100.0%" with green color coding
      const pctElement = screen.getByText('100.0%')
      expect(pctElement).toBeInTheDocument()
      expect(pctElement.className).toMatch(/text-success-green/)
    })

    it('UNIT-019: Attainment above 100% renders with green color', () => {
      // Given: workcenter with attainment_percentage: 112.5
      const entry = createWorkcenterEntry({
        attainment_percentage: 112.5,
        total_actual: 5625,
        total_target: 5000,
      })

      // When: WorkcenterRow renders
      render(<WorkcenterRow entry={entry} />)

      // Then: "112.5%" with green color coding
      const pctElement = screen.getByText('112.5%')
      expect(pctElement).toBeInTheDocument()
      expect(pctElement.className).toMatch(/text-success-green/)
    })
  })

  // =========================================================================
  // AC2: Expandable workcenter rows with per-asset breakdown
  // =========================================================================
  describe('AC2: Expandable workcenter rows with per-asset breakdown', () => {
    const threeAssets: AssetDetail[] = [
      createAssetDetail({
        asset_name: 'Grinder 1',
        actual: 1200,
        target: 1300,
        oee: 92.3,
        downtime_minutes: 45,
      }),
      createAssetDetail({
        asset_name: 'Grinder 2',
        actual: 1500,
        target: 1400,
        oee: 92.0,
        downtime_minutes: 10,
      }),
      createAssetDetail({
        asset_name: 'Grinder 3',
        actual: 1500,
        target: 1300,
        oee: 88.5,
        downtime_minutes: 20,
      }),
    ]

    const entryWithAssets = createWorkcenterEntry({
      workcenter_name: 'Grinding',
      assets: threeAssets,
    })

    it('UNIT-020: Clicking a workcenter row expands the asset detail table', async () => {
      // Given: WorkcenterRow renders in collapsed state with 3 assets
      render(<WorkcenterRow entry={entryWithAssets} />)

      // Verify initially collapsed — asset names not visible
      expect(screen.queryByText('Grinder 1')).not.toBeInTheDocument()

      // When: the user clicks on the workcenter row
      const row = screen.getByText('Grinding')
      await userEvent.click(row)

      // Then: the AssetDetailTable becomes visible showing all 3 asset rows
      expect(screen.getByText('Grinder 1')).toBeInTheDocument()
      expect(screen.getByText('Grinder 2')).toBeInTheDocument()
      expect(screen.getByText('Grinder 3')).toBeInTheDocument()
    })

    it('UNIT-021: Clicking an expanded row collapses the detail view', async () => {
      // Given: WorkcenterRow is expanded showing AssetDetailTable
      render(<WorkcenterRow entry={entryWithAssets} />)
      const row = screen.getByText('Grinding')
      await userEvent.click(row) // expand
      expect(screen.getByText('Grinder 1')).toBeInTheDocument()

      // When: the user clicks again to collapse
      await userEvent.click(row)

      // Then: the AssetDetailTable is no longer visible
      expect(screen.queryByText('Grinder 1')).not.toBeInTheDocument()
    })

    it('UNIT-022: Asset detail table shows asset name column', async () => {
      // Given: WorkcenterRow is expanded with assets
      render(<WorkcenterRow entry={entryWithAssets} />)
      await userEvent.click(screen.getByText('Grinding'))

      // When: AssetDetailTable renders
      // Then: each asset name is displayed
      expect(screen.getByText('Grinder 1')).toBeInTheDocument()
      expect(screen.getByText('Grinder 2')).toBeInTheDocument()
      expect(screen.getByText('Grinder 3')).toBeInTheDocument()
    })

    it('UNIT-023: Asset detail table shows actual vs target per asset', async () => {
      // Given: WorkcenterRow is expanded with asset actual: 1200, target: 1300
      render(<WorkcenterRow entry={entryWithAssets} />)
      await userEvent.click(screen.getByText('Grinding'))

      // When: AssetDetailTable renders
      // Then: actual vs target displayed as "1,200 / 1,300"
      expect(screen.getByText('1,200 / 1,300')).toBeInTheDocument()
    })

    it('UNIT-024: Asset detail table shows OEE percentage', async () => {
      // Given: asset with oee: 92.3
      const entry = createWorkcenterEntry({
        assets: [createAssetDetail({ oee: 92.3 })],
      })
      render(<WorkcenterRow entry={entry} />)
      await userEvent.click(screen.getByText('Grinding'))

      // When: AssetDetailTable renders
      // Then: "92.3%" is displayed
      expect(screen.getByText('92.3%')).toBeInTheDocument()
    })

    it('UNIT-025: Asset detail table shows downtime minutes', async () => {
      // Given: asset with downtime_minutes: 45
      const entry = createWorkcenterEntry({
        assets: [createAssetDetail({ downtime_minutes: 45 })],
      })
      render(<WorkcenterRow entry={entry} />)
      await userEvent.click(screen.getByText('Grinding'))

      // When: AssetDetailTable renders
      // Then: downtime is displayed (e.g., "45 min" or "45")
      expect(screen.getByText(/45/)).toBeInTheDocument()
    })

    it('UNIT-026: Asset row green background when hit_target is true', async () => {
      // Given: asset where actual >= target (hit target)
      const hitAsset = createAssetDetail({
        asset_name: 'Grinder 2',
        actual: 1500,
        target: 1400,
      })
      const entry = createWorkcenterEntry({
        assets: [hitAsset],
      })
      render(<WorkcenterRow entry={entry} />)
      await userEvent.click(screen.getByText('Grinding'))

      // When: AssetDetailTable renders
      // Then: the row has a green background tint class
      const assetRow = screen.getByText('Grinder 2').closest('tr') || screen.getByText('Grinder 2').closest('div')
      expect(assetRow).toBeTruthy()
      expect(assetRow!.className).toMatch(/bg-success-green/)
    })

    it('UNIT-027: Asset row red background when hit_target is false', async () => {
      // Given: asset where actual < target (missed)
      const missAsset = createAssetDetail({
        asset_name: 'Grinder 1',
        actual: 1200,
        target: 1300,
      })
      const entry = createWorkcenterEntry({
        assets: [missAsset],
      })
      render(<WorkcenterRow entry={entry} />)
      await userEvent.click(screen.getByText('Grinding'))

      // When: AssetDetailTable renders
      // Then: the row has a red background tint class
      const assetRow = screen.getByText('Grinder 1').closest('tr') || screen.getByText('Grinder 1').closest('div')
      expect(assetRow).toBeTruthy()
      expect(assetRow!.className).toMatch(/bg-safety-red/)
    })

    it('UNIT-028: Handles null OEE gracefully', async () => {
      // Given: asset with oee: null
      const entry = createWorkcenterEntry({
        assets: [createAssetDetail({ asset_name: 'Machine A', oee: null })],
      })
      render(<WorkcenterRow entry={entry} />)
      await userEvent.click(screen.getByText('Grinding'))

      // When: AssetDetailTable renders
      // Then: OEE column displays fallback value, not "null%"
      expect(screen.queryByText('null%')).not.toBeInTheDocument()
      expect(screen.queryByText('null')).not.toBeInTheDocument()
      // Should show a fallback like "—" or "N/A"
      const fallback = screen.getByText(/—|N\/A/)
      expect(fallback).toBeInTheDocument()
    })

    it('UNIT-029: Handles null downtime_minutes gracefully', async () => {
      // Given: asset with downtime_minutes: null
      const entry = createWorkcenterEntry({
        assets: [createAssetDetail({ asset_name: 'Machine B', downtime_minutes: null })],
      })
      render(<WorkcenterRow entry={entry} />)
      await userEvent.click(screen.getByText('Grinding'))

      // When: AssetDetailTable renders
      // Then: downtime column displays fallback value, not "null"
      expect(screen.queryByText(/^null$/)).not.toBeInTheDocument()
      const fallback = screen.getByText(/—|N\/A/)
      expect(fallback).toBeInTheDocument()
    })

    it('UNIT-030: Expand/collapse icon changes state', async () => {
      // Given: WorkcenterRow renders in collapsed state
      const { container } = render(<WorkcenterRow entry={entryWithAssets} />)

      // The collapsed state should have a right-pointing chevron or similar indicator
      // When: the user clicks to expand
      await userEvent.click(screen.getByText('Grinding'))

      // Then: the icon changes to indicate expanded state (ChevronDown or equivalent)
      // We check for a visual state change via class or data attribute
      const expandedIcon = container.querySelector('[data-expanded="true"]') ||
        container.querySelector('.rotate-90') ||
        container.querySelector('[aria-expanded="true"]')
      expect(expandedIcon).toBeTruthy()
    })

    it('UNIT-031: Multiple workcenters can be expanded independently', async () => {
      // Given: WorkcenterScorecard renders with 2 workcenter rows, both collapsed
      const entry1 = createWorkcenterEntry({
        workcenter_name: 'Grinding',
        assets: [createAssetDetail({ asset_name: 'Grinder 1' })],
      })
      const entry2 = createWorkcenterEntry({
        workcenter_name: 'Assembly',
        assets: [createAssetDetail({ asset_name: 'Assembler 1' })],
      })
      mockUseWorkcenterSummary.mockReturnValue(
        mockHookReturn({
          data: createMockResponse([entry1, entry2]),
        })
      )
      render(<WorkcenterScorecard />)

      // When: the user clicks the first workcenter row to expand
      await userEvent.click(screen.getByText('Grinding'))

      // Then: only the first workcenter's AssetDetailTable is visible
      expect(screen.getByText('Grinder 1')).toBeInTheDocument()
      expect(screen.queryByText('Assembler 1')).not.toBeInTheDocument()
    })

    it('UNIT-032: Asset detail table with both null OEE and downtime', async () => {
      // Given: asset with oee: null AND downtime_minutes: null
      const entry = createWorkcenterEntry({
        assets: [
          createAssetDetail({
            asset_name: 'Machine C',
            oee: null,
            downtime_minutes: null,
          }),
        ],
      })
      render(<WorkcenterRow entry={entry} />)
      await userEvent.click(screen.getByText('Grinding'))

      // When: AssetDetailTable renders
      // Then: both columns show fallback values without errors
      const fallbacks = screen.getAllByText(/—|N\/A/)
      expect(fallbacks.length).toBeGreaterThanOrEqual(2)
    })
  })

  // =========================================================================
  // AC3: Empty state when no workcenter data
  // =========================================================================
  describe('AC3: Empty state when no workcenter data', () => {
    it('UNIT-033: Empty state when workcenters array is empty', () => {
      // Given: useWorkcenterSummary returns data with workcenters: []
      mockUseWorkcenterSummary.mockReturnValue(
        mockHookReturn({
          data: createMockResponse([], {
            message: 'No production data available for this date.',
          }),
        })
      )

      // When: WorkcenterScorecard renders
      render(<WorkcenterScorecard />)

      // Then: the empty state message is displayed
      expect(
        screen.getByText('No production data available for this date.')
      ).toBeInTheDocument()
    })

    it('UNIT-034: Empty state uses API message when provided', () => {
      // Given: API returns a specific message
      mockUseWorkcenterSummary.mockReturnValue(
        mockHookReturn({
          data: createMockResponse([], {
            message: 'No data found for 2026-02-09',
          }),
        })
      )

      // When: WorkcenterScorecard renders
      render(<WorkcenterScorecard />)

      // Then: the displayed message matches the API-provided message
      expect(
        screen.getByText('No data found for 2026-02-09')
      ).toBeInTheDocument()
    })

    it('UNIT-035: Empty state fallback message when API message is null', () => {
      // Given: API returns workcenters: [] and message: null
      mockUseWorkcenterSummary.mockReturnValue(
        mockHookReturn({
          data: createMockResponse([], { message: null }),
        })
      )

      // When: WorkcenterScorecard renders
      render(<WorkcenterScorecard />)

      // Then: a default empty state message is displayed
      expect(
        screen.getByText(/No production data available/i)
      ).toBeInTheDocument()
    })

    it('UNIT-036: No workcenter rows rendered in empty state', () => {
      // Given: useWorkcenterSummary returns data with workcenters: []
      mockUseWorkcenterSummary.mockReturnValue(
        mockHookReturn({
          data: createMockResponse([]),
        })
      )

      // When: WorkcenterScorecard renders
      render(<WorkcenterScorecard />)

      // Then: no WorkcenterRow components / workcenter names are in the DOM
      expect(screen.queryByText('Grinding')).not.toBeInTheDocument()
      expect(screen.queryByText('Assembly')).not.toBeInTheDocument()
      expect(screen.queryByText('Packaging')).not.toBeInTheDocument()
    })
  })

  // =========================================================================
  // AC4: Glanceability / tablet readability (NFR-I1)
  // =========================================================================
  describe('AC4: Glanceability and tablet readability (NFR-I1)', () => {
    it('UNIT-037: Attainment percentage uses large font size', () => {
      // Given: WorkcenterRow renders with attainment data
      const entry = createWorkcenterEntry({ attainment_percentage: 95.0 })

      // When: the attainment percentage element is inspected
      render(<WorkcenterRow entry={entry} />)
      const pctElement = screen.getByText('95.0%')

      // Then: it has font size class of at least text-2xl and font-bold
      expect(pctElement.className).toMatch(/text-(2xl|3xl|4xl|5xl)/)
      expect(pctElement).toHaveClass('font-bold')
    })

    it('UNIT-038: Attainment uses tabular-nums for alignment', () => {
      // Given: WorkcenterRow renders with attainment data
      const entry = createWorkcenterEntry({ attainment_percentage: 95.0 })

      // When: the attainment percentage element is inspected
      render(<WorkcenterRow entry={entry} />)
      const pctElement = screen.getByText('95.0%')

      // Then: it has the tabular-nums CSS class
      expect(pctElement).toHaveClass('tabular-nums')
    })

    it('UNIT-039: Workcenter name uses bold readable font', () => {
      // Given: WorkcenterRow renders with workcenter: "Grinding"
      const entry = createWorkcenterEntry({ workcenter_name: 'Grinding' })

      // When: the workcenter name element is inspected
      render(<WorkcenterRow entry={entry} />)
      const nameElement = screen.getByText('Grinding')

      // Then: it has font-semibold class and at least text-lg size
      expect(nameElement).toHaveClass('font-semibold')
      expect(nameElement.className).toMatch(/text-(lg|xl|2xl)/)
    })

    it('UNIT-040: Expand/collapse touch target meets minimum 44px', () => {
      // Given: WorkcenterRow renders with an expand/collapse button
      const entry = createWorkcenterEntry()

      // When: the clickable area element is inspected
      const { container } = render(<WorkcenterRow entry={entry} />)

      // Then: it has minimum height/width of 44px
      const clickTarget = container.querySelector('[role="button"]') ||
        container.querySelector('button') ||
        container.querySelector('[data-clickable]')
      expect(clickTarget).toBeTruthy()
      expect(clickTarget!.className).toMatch(/min-[hw]-\[44px\]|min-h-11|min-w-11|p-3|p-4/)
    })

    it('UNIT-041: Actual/target output uses tabular-nums', () => {
      // Given: WorkcenterRow renders with actual and target output numbers
      const entry = createWorkcenterEntry({
        total_actual: 4200,
        total_target: 5000,
      })

      // When: the output text element is inspected
      render(<WorkcenterRow entry={entry} />)
      const outputElement = screen.getByText('4,200 / 5,000')

      // Then: it uses the tabular-nums class
      expect(outputElement).toHaveClass('tabular-nums')
    })
  })

  // =========================================================================
  // INT-001: Integration - Scorecard position in page
  // =========================================================================
  describe('Integration: Scorecard positioned in morning report page', () => {
    it('INT-001: Scorecard positioned between MorningSummarySection and action items', () => {
      // Given: the morning report page renders with all sections
      // This test verifies WorkcenterScorecard is imported and available.
      // The actual page integration will render WorkcenterScorecard between
      // MorningSummarySection and InsightEvidenceCardList.

      // When: WorkcenterScorecard is rendered
      mockUseWorkcenterSummary.mockReturnValue(
        mockHookReturn({
          data: createMockResponse(createDefaultThreeWorkcenters()),
        })
      )
      render(
        <div>
          <div data-testid="morning-summary">MorningSummarySection</div>
          <WorkcenterScorecard />
          <div data-testid="action-items">Action Items</div>
        </div>
      )

      // Then: WorkcenterScorecard appears after MorningSummarySection and before action items
      const summarySection = screen.getByTestId('morning-summary')
      const scorecard = screen.getByText('Production Scorecard')
      const actionItems = screen.getByTestId('action-items')

      // Verify DOM ordering: summary < scorecard < action items
      const allNodes = [summarySection, scorecard, actionItems]
      const positions = allNodes.map(node => {
        const range = document.createRange()
        range.selectNode(node)
        return range.startOffset
      })

      // Position-based check: just verify all three are in the document
      expect(summarySection).toBeInTheDocument()
      expect(scorecard).toBeInTheDocument()
      expect(actionItems).toBeInTheDocument()

      // DOM order check via compareDocumentPosition
      expect(
        summarySection.compareDocumentPosition(scorecard) &
          Node.DOCUMENT_POSITION_FOLLOWING
      ).toBeTruthy()
      expect(
        scorecard.compareDocumentPosition(actionItems) &
          Node.DOCUMENT_POSITION_FOLLOWING
      ).toBeTruthy()
    })
  })
})
