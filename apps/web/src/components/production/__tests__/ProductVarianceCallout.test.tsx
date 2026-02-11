/**
 * ProductVarianceCallout Component Tests (Story 12.6: Schedule Attainment UI Section)
 *
 * TDD tests — these MUST FAIL until the component is implemented.
 *
 * @see Story 12.6 - Schedule Attainment UI Section
 * @see AC #2 - Product swap and variance highlighting
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'

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

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

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

const createVarianceCallout = (overrides: Partial<VarianceCallout> = {}): VarianceCallout => ({
  type: 'product_swap',
  asset_name: 'Roaster 1',
  message: 'Roaster 1 ran Colombian instead of scheduled Brazilian',
  ...overrides,
})

// ---------------------------------------------------------------------------
// Import component AFTER mocks are set up
// ---------------------------------------------------------------------------

import { ProductVarianceCallout } from '../ProductVarianceCallout'

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: ProductVarianceCallout Component (Story 12.6, AC2)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // =========================================================================
  // AC2: Product swap and variance highlighting
  // =========================================================================
  describe('AC2: Product swap and variance callout rendering', () => {
    it('UNIT-014: Product swap callout renders with amber/orange styling', () => {
      // Given: A VarianceCallout with type="product_swap"
      const variance = createVarianceCallout({
        type: 'product_swap',
        asset_name: 'Roaster 1',
        message: 'Roaster 1 ran Colombian instead of scheduled Brazilian',
      })

      // When: ProductVarianceCallout component renders
      const { container } = render(<ProductVarianceCallout variance={variance} />)

      // Then: The callout has amber/orange background and amber left border
      const callout = container.firstElementChild as HTMLElement
      expect(callout).toBeTruthy()
      expect(callout.className).toMatch(/bg-warning-amber/)
      expect(callout.className).toMatch(/border-l-4/)
      expect(callout.className).toMatch(/border-warning-amber/)

      // And the message text is visible
      expect(screen.getByText('Roaster 1 ran Colombian instead of scheduled Brazilian')).toBeInTheDocument()
    })

    it('UNIT-015: Product swap callout uses swap icon indicator', () => {
      // Given: A VarianceCallout with type="product_swap"
      const variance = createVarianceCallout({ type: 'product_swap' })

      // When: ProductVarianceCallout component renders
      const { container } = render(<ProductVarianceCallout variance={variance} />)

      // Then: An ArrowRightLeft icon (or equivalent swap indicator) is rendered
      // Lucide icons render as SVG elements
      const svgIcon = container.querySelector('svg')
      expect(svgIcon).toBeInTheDocument()
    })

    it('UNIT-016: Underproduction callout renders with appropriate warning styling', () => {
      // Given: A VarianceCallout with type="underproduction"
      const variance = createVarianceCallout({
        type: 'underproduction',
        asset_name: 'Grinder 2',
        message: 'Grinder 2 produced 200 fewer units of Ethiopian',
      })

      // When: ProductVarianceCallout component renders
      const { container } = render(<ProductVarianceCallout variance={variance} />)

      // Then: The callout renders with amber warning styling and the message is visible
      const callout = container.firstElementChild as HTMLElement
      expect(callout).toBeTruthy()
      expect(callout.className).toMatch(/bg-warning-amber|border-warning-amber/)
      expect(screen.getByText('Grinder 2 produced 200 fewer units of Ethiopian')).toBeInTheDocument()

      // And an AlertTriangle icon is present
      const svgIcon = container.querySelector('svg')
      expect(svgIcon).toBeInTheDocument()
    })

    it('UNIT-017: Unscheduled production callout renders with info-blue styling', () => {
      // Given: A VarianceCallout with type="unscheduled"
      const variance = createVarianceCallout({
        type: 'unscheduled',
        asset_name: 'Roaster 2',
        message: 'Roaster 2 ran Decaf — not on schedule',
      })

      // When: ProductVarianceCallout component renders
      const { container } = render(<ProductVarianceCallout variance={variance} />)

      // Then: The callout renders with info-blue background and info-blue text
      const callout = container.firstElementChild as HTMLElement
      expect(callout).toBeTruthy()
      expect(callout.className).toMatch(/bg-info-blue/)
      expect(callout.className).toMatch(/text-info-blue/)
      expect(screen.getByText('Roaster 2 ran Decaf — not on schedule')).toBeInTheDocument()
    })

    it('UNIT-018: Multiple variance callouts render in order within a workcenter', () => {
      // Given: A workcenter has 3 variance callouts: one swap, one underproduction, one unscheduled
      const variances: VarianceCallout[] = [
        createVarianceCallout({
          type: 'product_swap',
          message: 'Roaster 1 ran Colombian instead of scheduled Brazilian',
        }),
        createVarianceCallout({
          type: 'underproduction',
          message: 'Grinder 2 produced 200 fewer units of Ethiopian',
        }),
        createVarianceCallout({
          type: 'unscheduled',
          message: 'Roaster 2 ran Decaf — not on schedule',
        }),
      ]

      // When: All three callouts are rendered
      const { container } = render(
        <div>
          {variances.map((v, i) => (
            <ProductVarianceCallout key={i} variance={v} />
          ))}
        </div>
      )

      // Then: All three callout messages are visible in order
      const msg1 = screen.getByText('Roaster 1 ran Colombian instead of scheduled Brazilian')
      const msg2 = screen.getByText('Grinder 2 produced 200 fewer units of Ethiopian')
      const msg3 = screen.getByText('Roaster 2 ran Decaf — not on schedule')

      expect(msg1).toBeInTheDocument()
      expect(msg2).toBeInTheDocument()
      expect(msg3).toBeInTheDocument()

      // Verify DOM order
      expect(
        msg1.compareDocumentPosition(msg2) & Node.DOCUMENT_POSITION_FOLLOWING
      ).toBeTruthy()
      expect(
        msg2.compareDocumentPosition(msg3) & Node.DOCUMENT_POSITION_FOLLOWING
      ).toBeTruthy()
    })

    it('UNIT-019: Swap callout message text contains swap description', () => {
      // Given: ProductVarianceCallout receives a swap message
      const variance = createVarianceCallout({
        type: 'product_swap',
        message: 'Ran Colombian instead of scheduled Brazilian',
      })

      // When: Component renders
      render(<ProductVarianceCallout variance={variance} />)

      // Then: The exact text is visible in the document
      expect(screen.getByText('Ran Colombian instead of scheduled Brazilian')).toBeInTheDocument()
    })
  })
})
