/**
 * ScheduleAttainment Component Tests (Story 12.6: Schedule Attainment UI Section)
 *
 * TDD tests — these MUST FAIL until the component is implemented.
 *
 * @see Story 12.6 - Schedule Attainment UI Section
 * @see AC #1 - Schedule attainment section with workcenter data, attainment %, variance callouts
 * @see AC #3 - Empty state with upload link when no schedule data
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

// ---------------------------------------------------------------------------
// Types (matching API contract from Story 12.5)
// ---------------------------------------------------------------------------

interface VarianceCallout {
  type: 'product_swap' | 'underproduction' | 'unscheduled'
  asset_name: string
  message: string
  scheduled_product?: string
  actual_product?: string
  quantity_gap?: number
}

interface ProductAttainment {
  product_name: string
  scheduled_quantity: number
  actual_quantity: number
  attainment_pct: number
}

interface WorkcenterAttainment {
  workcenter_name: string
  overall_attainment_pct: number
  products: ProductAttainment[]
  variance_callouts: VarianceCallout[]
}

interface ScheduleAttainmentResponse {
  workcenters: WorkcenterAttainment[]
  report_date: string
  has_schedule: boolean
  message?: string
}

interface UseScheduleAttainmentReturn {
  data: ScheduleAttainmentResponse | null
  isLoading: boolean
  error: string | null
  refetch: () => void
}

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockRefetch = vi.fn()
const mockUseScheduleAttainment = vi.fn()

vi.mock('@/hooks/useScheduleAttainment', () => ({
  useScheduleAttainment: (...args: unknown[]) => mockUseScheduleAttainment(...args),
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

// Mock recharts to avoid canvas issues in tests
vi.mock('recharts', () => ({
  BarChart: ({ children }: any) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => <div data-testid="bar" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
  ResponsiveContainer: ({ children }: any) => <div data-testid="responsive-container">{children}</div>,
}))

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const createProduct = (overrides: Partial<ProductAttainment> = {}): ProductAttainment => ({
  product_name: 'Brazilian',
  scheduled_quantity: 1000,
  actual_quantity: 950,
  attainment_pct: 95.0,
  ...overrides,
})

const createVariance = (overrides: Partial<VarianceCallout> = {}): VarianceCallout => ({
  type: 'product_swap',
  asset_name: 'Roaster 1',
  message: 'Roaster 1 ran Colombian instead of scheduled Brazilian',
  ...overrides,
})

const createWorkcenter = (overrides: Partial<WorkcenterAttainment> = {}): WorkcenterAttainment => ({
  workcenter_name: 'Roasting',
  overall_attainment_pct: 92.5,
  products: [
    createProduct({ product_name: 'Brazilian', scheduled_quantity: 1000, actual_quantity: 950, attainment_pct: 95.0 }),
    createProduct({ product_name: 'Colombian', scheduled_quantity: 500, actual_quantity: 400, attainment_pct: 80.0 }),
  ],
  variance_callouts: [],
  ...overrides,
})

const createMockResponse = (
  workcenters: WorkcenterAttainment[] = [],
  overrides: Partial<ScheduleAttainmentResponse> = {}
): ScheduleAttainmentResponse => ({
  workcenters,
  report_date: '2026-02-10',
  has_schedule: true,
  ...overrides,
})

const createDefaultTwoWorkcenters = (): WorkcenterAttainment[] => [
  createWorkcenter({
    workcenter_name: 'Roasting',
    overall_attainment_pct: 92.5,
    products: [
      createProduct({ product_name: 'Brazilian', scheduled_quantity: 1000, actual_quantity: 950, attainment_pct: 95.0 }),
      createProduct({ product_name: 'Colombian', scheduled_quantity: 500, actual_quantity: 400, attainment_pct: 80.0 }),
    ],
  }),
  createWorkcenter({
    workcenter_name: 'Grinding',
    overall_attainment_pct: 88.0,
    products: [
      createProduct({ product_name: 'Ethiopian', scheduled_quantity: 800, actual_quantity: 700, attainment_pct: 87.5 }),
    ],
  }),
]

const mockHookReturn = (overrides: Partial<UseScheduleAttainmentReturn> = {}): UseScheduleAttainmentReturn => ({
  data: null,
  isLoading: false,
  error: null,
  refetch: mockRefetch,
  ...overrides,
})

// ---------------------------------------------------------------------------
// Import components AFTER mocks are set up
// ---------------------------------------------------------------------------

import { ScheduleAttainment } from '../ScheduleAttainment'

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: Schedule Attainment UI Section (Story 12.6)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockRefetch.mockReset()
    // Default: successful data load
    mockUseScheduleAttainment.mockReturnValue(
      mockHookReturn({
        data: createMockResponse(createDefaultTwoWorkcenters()),
      })
    )
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // =========================================================================
  // AC1: Schedule attainment section with workcenter data
  // =========================================================================
  describe('AC1: Schedule attainment section renders with workcenter data', () => {
    it('UNIT-001: Section renders with correct heading when data exists', () => {
      // Given: useScheduleAttainment returns data with has_data=true and two workcenters
      const workcenters = createDefaultTwoWorkcenters()
      mockUseScheduleAttainment.mockReturnValue(
        mockHookReturn({ data: createMockResponse(workcenters) })
      )

      // When: ScheduleAttainment component renders
      render(<ScheduleAttainment />)

      // Then: A section element with aria-label="Schedule attainment" is present,
      // containing an h2 heading with text "Schedule Attainment"
      const section = screen.getByRole('region', { name: /schedule attainment/i })
      expect(section).toBeInTheDocument()

      const heading = within(section).getByRole('heading', { level: 2 })
      expect(heading).toHaveTextContent('Schedule Attainment')
    })

    it('UNIT-002: Each workcenter renders as a Card with mode retrospective', () => {
      // Given: useScheduleAttainment returns data with 3 workcenters
      const workcenters = [
        createWorkcenter({ workcenter_name: 'Roasting' }),
        createWorkcenter({ workcenter_name: 'Grinding' }),
        createWorkcenter({ workcenter_name: 'Packaging' }),
      ]
      mockUseScheduleAttainment.mockReturnValue(
        mockHookReturn({ data: createMockResponse(workcenters) })
      )

      // When: ScheduleAttainment component renders
      const { container } = render(<ScheduleAttainment />)

      // Then: Three Card components render, each with mode="retrospective"
      expect(screen.getByText('Roasting')).toBeInTheDocument()
      expect(screen.getByText('Grinding')).toBeInTheDocument()
      expect(screen.getByText('Packaging')).toBeInTheDocument()

      // Cards should have retrospective styling classes
      const cards = container.querySelectorAll('[class*="retrospective"]')
      expect(cards.length).toBeGreaterThanOrEqual(3)
    })

    it('UNIT-003: Per-product rows show product name, scheduled qty, actual qty, attainment %', () => {
      // Given: useScheduleAttainment returns a workcenter with specific product data
      const workcenter = createWorkcenter({
        workcenter_name: 'Roasting',
        products: [
          createProduct({ product_name: 'Brazilian', scheduled_quantity: 1000, actual_quantity: 950, attainment_pct: 95.0 }),
          createProduct({ product_name: 'Colombian', scheduled_quantity: 500, actual_quantity: 400, attainment_pct: 80.0 }),
        ],
      })
      mockUseScheduleAttainment.mockReturnValue(
        mockHookReturn({ data: createMockResponse([workcenter]) })
      )

      // When: ScheduleAttainment component renders
      render(<ScheduleAttainment />)

      // Then: Product rows display formatted values
      expect(screen.getByText('Brazilian')).toBeInTheDocument()
      expect(screen.getByText('1,000')).toBeInTheDocument()
      expect(screen.getByText('950')).toBeInTheDocument()
      expect(screen.getByText('95.0%')).toBeInTheDocument()

      expect(screen.getByText('Colombian')).toBeInTheDocument()
      expect(screen.getByText('500')).toBeInTheDocument()
      expect(screen.getByText('400')).toBeInTheDocument()
      expect(screen.getByText('80.0%')).toBeInTheDocument()
    })

    it('UNIT-004: Overall workcenter attainment percentage is displayed', () => {
      // Given: useScheduleAttainment returns a workcenter with overall_attainment_pct of 87.5
      const workcenter = createWorkcenter({
        workcenter_name: 'Roasting',
        overall_attainment_pct: 87.5,
      })
      mockUseScheduleAttainment.mockReturnValue(
        mockHookReturn({ data: createMockResponse([workcenter]) })
      )

      // When: ScheduleAttainment component renders
      render(<ScheduleAttainment />)

      // Then: The workcenter card shows "87.5%" as the overall attainment
      expect(screen.getByText('87.5%')).toBeInTheDocument()
    })

    it('UNIT-005: Attainment percentage color-coded green for >=95%', () => {
      // Given: A product has attainment_pct of 98.0
      const workcenter = createWorkcenter({
        products: [createProduct({ product_name: 'HiProd', attainment_pct: 98.0 })],
      })
      mockUseScheduleAttainment.mockReturnValue(
        mockHookReturn({ data: createMockResponse([workcenter]) })
      )

      // When: ScheduleAttainment renders the product row
      render(<ScheduleAttainment />)

      // Then: The attainment percentage text has success-green color class
      const pctElement = screen.getByText('98.0%')
      expect(pctElement.className).toMatch(/text-success-green/)
    })

    it('UNIT-006: Attainment percentage color-coded amber for 80-94%', () => {
      // Given: A product has attainment_pct of 88.0
      const workcenter = createWorkcenter({
        products: [createProduct({ product_name: 'MidProd', attainment_pct: 88.0 })],
      })
      mockUseScheduleAttainment.mockReturnValue(
        mockHookReturn({ data: createMockResponse([workcenter]) })
      )

      // When: ScheduleAttainment renders the product row
      render(<ScheduleAttainment />)

      // Then: The attainment percentage text has warning-amber color class
      const pctElement = screen.getByText('88.0%')
      expect(pctElement.className).toMatch(/text-warning-amber/)
    })

    it('UNIT-007: Attainment percentage color-coded red for <80%', () => {
      // Given: A product has attainment_pct of 72.0
      const workcenter = createWorkcenter({
        products: [createProduct({ product_name: 'LowProd', attainment_pct: 72.0 })],
      })
      mockUseScheduleAttainment.mockReturnValue(
        mockHookReturn({ data: createMockResponse([workcenter]) })
      )

      // When: ScheduleAttainment renders the product row
      render(<ScheduleAttainment />)

      // Then: The attainment percentage text has safety-red color class
      const pctElement = screen.getByText('72.0%')
      expect(pctElement).toHaveClass('text-safety-red')
    })

    it('UNIT-008: Variance callouts rendered within workcenter cards', () => {
      // Given: useScheduleAttainment returns a workcenter with 2 variance callouts
      const workcenter = createWorkcenter({
        workcenter_name: 'Roasting',
        variance_callouts: [
          createVariance({
            type: 'product_swap',
            message: 'Roaster 1 ran Colombian instead of scheduled Brazilian',
          }),
          createVariance({
            type: 'underproduction',
            asset_name: 'Grinder 2',
            message: 'Grinder 2 produced 200 fewer units of Ethiopian',
          }),
        ],
      })
      mockUseScheduleAttainment.mockReturnValue(
        mockHookReturn({ data: createMockResponse([workcenter]) })
      )

      // When: ScheduleAttainment renders
      render(<ScheduleAttainment />)

      // Then: Both variance callout messages are visible
      expect(screen.getByText('Roaster 1 ran Colombian instead of scheduled Brazilian')).toBeInTheDocument()
      expect(screen.getByText('Grinder 2 produced 200 fewer units of Ethiopian')).toBeInTheDocument()
    })

    it('UNIT-009: Loading skeleton displayed while data is fetching', () => {
      // Given: useScheduleAttainment returns isLoading=true, data=null
      mockUseScheduleAttainment.mockReturnValue(
        mockHookReturn({ isLoading: true, data: null, error: null })
      )

      // When: ScheduleAttainment component renders
      const { container } = render(<ScheduleAttainment />)

      // Then: Animated skeleton placeholders are visible, no workcenter cards or data rows
      expect(container.querySelector('.animate-pulse')).toBeInTheDocument()
      expect(screen.queryByText('Roasting')).not.toBeInTheDocument()
      expect(screen.queryByText('Grinding')).not.toBeInTheDocument()
    })

    it('UNIT-010: Error state displays error message and retry button', () => {
      // Given: useScheduleAttainment returns error, data=null
      mockUseScheduleAttainment.mockReturnValue(
        mockHookReturn({
          isLoading: false,
          data: null,
          error: 'Failed to load schedule attainment data',
        })
      )

      // When: ScheduleAttainment component renders
      render(<ScheduleAttainment />)

      // Then: The error message text is visible and a retry button is present
      expect(screen.getByText(/Failed to load schedule attainment data/)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /try again|retry/i })).toBeInTheDocument()
    })

    it('UNIT-011: Retry button triggers refetch on click', async () => {
      // Given: ScheduleAttainment is in error state with a visible retry button
      mockUseScheduleAttainment.mockReturnValue(
        mockHookReturn({
          isLoading: false,
          data: null,
          error: 'Failed to load schedule attainment data',
          refetch: mockRefetch,
        })
      )

      // When: User clicks the retry button
      render(<ScheduleAttainment />)
      const retryButton = screen.getByRole('button', { name: /try again|retry/i })
      await userEvent.click(retryButton)

      // Then: The refetch function is called exactly once
      expect(mockRefetch).toHaveBeenCalledTimes(1)
    })

    it('UNIT-012: Workcenter with empty products array renders only variance callouts', () => {
      // Given: useScheduleAttainment returns a workcenter with products=[] and variances
      const workcenter = createWorkcenter({
        workcenter_name: 'Roasting',
        products: [],
        variance_callouts: [
          createVariance({
            type: 'unscheduled',
            message: 'Unscheduled production on Roaster 1',
          }),
        ],
      })
      mockUseScheduleAttainment.mockReturnValue(
        mockHookReturn({ data: createMockResponse([workcenter]) })
      )

      // When: ScheduleAttainment renders
      render(<ScheduleAttainment />)

      // Then: No product rows shown but variance callout is rendered
      expect(screen.queryByText('Brazilian')).not.toBeInTheDocument()
      expect(screen.getByText('Unscheduled production on Roaster 1')).toBeInTheDocument()
    })

    it('UNIT-013: Section renders with className prop applied', () => {
      // Given: ScheduleAttainment component receives className="custom-class"
      mockUseScheduleAttainment.mockReturnValue(
        mockHookReturn({
          data: createMockResponse(createDefaultTwoWorkcenters()),
        })
      )

      // When: Component renders
      const { container } = render(<ScheduleAttainment className="custom-class" />)

      // Then: The custom-class is applied to the section's root element
      const section = container.querySelector('section')
      expect(section).toBeInTheDocument()
      expect(section).toHaveClass('custom-class')
    })
  })

  // =========================================================================
  // AC3: Empty state with upload link when no schedule data
  // =========================================================================
  describe('AC3: Empty state when no schedule data exists', () => {
    const emptyStateHookReturn = () =>
      mockHookReturn({
        data: createMockResponse([], {
          has_schedule: false,
          message: 'No schedule data for this date',
          workcenters: [],
        }),
      })

    it('UNIT-020: Empty state renders when has_data is false', () => {
      // Given: useScheduleAttainment returns data with has_schedule=false
      mockUseScheduleAttainment.mockReturnValue(emptyStateHookReturn())

      // When: ScheduleAttainment component renders
      render(<ScheduleAttainment />)

      // Then: A prompt is displayed and no workcenter cards are shown
      expect(screen.getByText(/No schedule uploaded for this date/i)).toBeInTheDocument()
      expect(screen.queryByText('Roasting')).not.toBeInTheDocument()
      expect(screen.queryByText('Grinding')).not.toBeInTheDocument()
    })

    it('UNIT-021: Empty state contains link to schedule upload page', () => {
      // Given: useScheduleAttainment returns has_schedule=false
      mockUseScheduleAttainment.mockReturnValue(emptyStateHookReturn())

      // When: ScheduleAttainment renders the empty state
      render(<ScheduleAttainment />)

      // Then: A link with text "Upload schedule" and href to /settings/schedule-upload
      const link = screen.getByRole('link', { name: /upload schedule/i })
      expect(link).toBeInTheDocument()
      expect(link).toHaveAttribute('href', '/settings/schedule-upload')
    })

    it('UNIT-022: Empty state link uses Next.js Link for client-side navigation', () => {
      // Given: ScheduleAttainment renders the empty state
      mockUseScheduleAttainment.mockReturnValue(emptyStateHookReturn())

      // When: The link element is inspected
      render(<ScheduleAttainment />)

      // Then: The link is rendered as an anchor tag with correct href
      // (Next.js Link renders as <a>)
      const link = screen.getByRole('link', { name: /upload schedule/i })
      expect(link.tagName).toBe('A')
      expect(link).toHaveAttribute('href', '/settings/schedule-upload')
    })

    it('UNIT-023: Section heading still displays in empty state', () => {
      // Given: useScheduleAttainment returns has_schedule=false
      mockUseScheduleAttainment.mockReturnValue(emptyStateHookReturn())

      // When: ScheduleAttainment renders
      render(<ScheduleAttainment />)

      // Then: The "Schedule Attainment" section heading is still visible
      const heading = screen.getByRole('heading', { level: 2 })
      expect(heading).toHaveTextContent('Schedule Attainment')
    })

    it('UNIT-024: No bar chart rendered in empty state', () => {
      // Given: useScheduleAttainment returns has_schedule=false
      mockUseScheduleAttainment.mockReturnValue(emptyStateHookReturn())

      // When: ScheduleAttainment renders
      render(<ScheduleAttainment />)

      // Then: The section heading is rendered (verifies component renders something)
      const heading = screen.getByRole('heading', { level: 2 })
      expect(heading).toHaveTextContent('Schedule Attainment')

      // And no Recharts BarChart or ProductMixChart component is rendered
      expect(screen.queryByTestId('bar-chart')).not.toBeInTheDocument()
      expect(screen.queryByTestId('responsive-container')).not.toBeInTheDocument()
    })
  })
})
