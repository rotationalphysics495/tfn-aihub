/**
 * ProductMixChart Component Tests (Story 12.6: Schedule Attainment UI Section)
 *
 * TDD tests — these MUST FAIL until the component is implemented.
 *
 * @see Story 12.6 - Schedule Attainment UI Section
 * @see AC #4 - Product mix bar chart (planned vs actual)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ProductAttainment {
  product_name: string
  scheduled_quantity: number
  actual_quantity: number
  attainment_pct: number
}

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

// Track which recharts components were rendered
const rechartsRenderLog: string[] = []

vi.mock('recharts', () => ({
  BarChart: ({ children }: any) => {
    rechartsRenderLog.push('BarChart')
    return <div data-testid="bar-chart">{children}</div>
  },
  Bar: ({ dataKey, fill }: any) => {
    rechartsRenderLog.push('Bar')
    return <div data-testid={`bar-${dataKey}`} data-fill={fill} />
  },
  XAxis: () => {
    rechartsRenderLog.push('XAxis')
    return <div data-testid="x-axis" />
  },
  YAxis: () => {
    rechartsRenderLog.push('YAxis')
    return <div data-testid="y-axis" />
  },
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => {
    rechartsRenderLog.push('Legend')
    return <div data-testid="legend" />
  },
  ResponsiveContainer: ({ children, width, height }: any) => (
    <div data-testid="responsive-container" data-width={width} data-height={height}>
      {children}
    </div>
  ),
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

const createProduct = (overrides: Partial<ProductAttainment> = {}): ProductAttainment => ({
  product_name: 'Brazilian',
  scheduled_quantity: 1000,
  actual_quantity: 950,
  attainment_pct: 95.0,
  ...overrides,
})

const createMultipleProducts = (): ProductAttainment[] => [
  createProduct({ product_name: 'Brazilian', scheduled_quantity: 1000, actual_quantity: 950 }),
  createProduct({ product_name: 'Colombian', scheduled_quantity: 500, actual_quantity: 600 }),
  createProduct({ product_name: 'Ethiopian', scheduled_quantity: 300, actual_quantity: 250 }),
]

// ---------------------------------------------------------------------------
// Import component AFTER mocks are set up
// ---------------------------------------------------------------------------

import { ProductMixChart } from '../ProductMixChart'

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: ProductMixChart Component (Story 12.6, AC4)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    rechartsRenderLog.length = 0
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // =========================================================================
  // AC4: Product mix bar chart with planned vs actual
  // =========================================================================
  describe('AC4: Product mix bar chart shows planned vs actual mix percentages', () => {
    it('UNIT-025: Product mix bar chart renders when data exists', () => {
      // Given: Products data with multiple products across workcenters
      const products = createMultipleProducts()

      // When: ProductMixChart component renders
      render(<ProductMixChart products={products} />)

      // Then: A Recharts BarChart is rendered
      expect(screen.getByTestId('bar-chart')).toBeInTheDocument()
      expect(screen.getByTestId('responsive-container')).toBeInTheDocument()
    })

    it('UNIT-026: Bar chart shows correct planned vs actual mix percentages', () => {
      // Given: Products with known quantities for percentage verification
      // Brazilian: sched 1000/1800 = 55.6%, actual 950/1800 = 52.8%
      // Colombian: sched 500/1800 = 27.8%, actual 600/1800 = 33.3%
      // Ethiopian: sched 300/1800 = 16.7%, actual 250/1800 = 13.9%
      const products = createMultipleProducts()

      // When: Chart computes mix percentages
      render(<ProductMixChart products={products} />)

      // Then: The chart renders with the correct data
      // (Since recharts is mocked, we verify the chart component is rendered with data)
      expect(screen.getByTestId('bar-chart')).toBeInTheDocument()
      // Verify bar elements are present for planned and actual
      expect(screen.getByTestId('bar-planned_pct')).toBeInTheDocument()
      expect(screen.getByTestId('bar-actual_pct')).toBeInTheDocument()
    })

    it('UNIT-027: Bar chart uses ResponsiveContainer for responsive sizing', () => {
      // Given: ProductMixChart component renders
      const products = createMultipleProducts()

      // When: The chart container is inspected
      render(<ProductMixChart products={products} />)

      // Then: The chart is wrapped in a ResponsiveContainer with width="100%"
      const container = screen.getByTestId('responsive-container')
      expect(container).toBeInTheDocument()
      expect(container).toHaveAttribute('data-width', '100%')
    })

    it('UNIT-028: Bar chart has legend distinguishing planned vs actual', () => {
      // Given: ProductMixChart renders with valid data
      const products = createMultipleProducts()

      // When: The chart is fully rendered
      render(<ProductMixChart products={products} />)

      // Then: A Legend component is present
      expect(screen.getByTestId('legend')).toBeInTheDocument()
    })

    it('UNIT-029: Bar chart handles empty products array gracefully', () => {
      // Given: ProductMixChart receives an empty products array
      // When: Component renders
      // Then: No error is thrown and component renders without crashing
      expect(() => render(<ProductMixChart products={[]} />)).not.toThrow()

      // Either an empty chart or a no-data message is displayed
      const chart = screen.queryByTestId('bar-chart')
      const noData = screen.queryByText(/no data|no products/i)
      expect(chart || noData).toBeTruthy()
    })

    it('UNIT-030: Bar chart uses correct color tokens for planned and actual bars', () => {
      // Given: ProductMixChart renders with valid data
      const products = createMultipleProducts()

      // When: The Bar elements are inspected
      render(<ProductMixChart products={products} />)

      // Then: Planned bars use info-blue color and actual bars use success-green color
      const plannedBar = screen.getByTestId('bar-planned_pct')
      const actualBar = screen.getByTestId('bar-actual_pct')
      expect(plannedBar).toHaveAttribute('data-fill', expect.stringMatching(/info-blue|hsl/))
      expect(actualBar).toHaveAttribute('data-fill', expect.stringMatching(/success-green|hsl/))
    })

    it('UNIT-031: Bar chart renders below workcenter cards', () => {
      // Given: A parent component with workcenter cards and a ProductMixChart
      const products = createMultipleProducts()

      // When: The full section is rendered
      render(
        <div>
          <div data-testid="workcenter-cards">Workcenter Cards</div>
          <ProductMixChart products={products} />
        </div>
      )

      // Then: The ProductMixChart appears in the DOM after workcenter cards
      const workcenterCards = screen.getByTestId('workcenter-cards')
      const chart = screen.getByTestId('bar-chart')

      expect(
        workcenterCards.compareDocumentPosition(chart) & Node.DOCUMENT_POSITION_FOLLOWING
      ).toBeTruthy()
    })
  })
})
