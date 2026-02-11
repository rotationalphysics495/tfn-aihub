/**
 * SchedulePreviewTable Component Tests (Story 12.4: Schedule Upload UI)
 *
 * TDD tests — these MUST FAIL until the component is implemented.
 *
 * @see Story 12.4 - Schedule Upload UI
 * @see AC #2 - Preview table with match indicators
 * @see AC #4 - Error rows with fix suggestions
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import { SchedulePreviewTable } from '../SchedulePreviewTable'

// ---------------------------------------------------------------------------
// Types (matching API schema from apps/api/app/schemas/schedule.py)
// ---------------------------------------------------------------------------

interface RowValidationError {
  row_number: number
  field: string
  message: string
}

interface ScheduleRowPreview {
  row_number: number
  date: string
  shift: string
  asset_name: string
  product_name: string
  scheduled_quantity: string
  asset_match_status: 'matched' | 'suggested' | 'unmatched'
  asset_id: string | null
  suggestions: string[]
  product_id: string | null
  is_new_product: boolean
  errors: RowValidationError[]
}

interface SchedulePreviewResponse {
  parsed_rows_count: number
  rows: ScheduleRowPreview[]
  has_errors: boolean
  matched_assets: string[]
  matched_products: string[]
  new_products: string[]
}

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const createMockRow = (overrides: Partial<ScheduleRowPreview> = {}): ScheduleRowPreview => ({
  row_number: 1,
  date: '2026-02-16',
  shift: 'Day',
  asset_name: 'Grinder 1',
  product_name: 'Dark Roast 12oz',
  scheduled_quantity: '500',
  asset_match_status: 'matched',
  asset_id: 'uuid-asset-1',
  suggestions: [],
  product_id: 'uuid-prod-1',
  is_new_product: false,
  errors: [],
  ...overrides,
})

const createMockPreviewResponse = (
  overrides: Partial<SchedulePreviewResponse> = {},
): SchedulePreviewResponse => {
  const rows = overrides.rows ?? [createMockRow()]
  return {
    parsed_rows_count: rows.length,
    rows,
    has_errors: rows.some((r) => r.errors.length > 0),
    matched_assets: rows
      .filter((r) => r.asset_match_status === 'matched')
      .map((r) => r.asset_name),
    matched_products: rows
      .filter((r) => !r.is_new_product && r.product_id)
      .map((r) => r.product_name),
    new_products: rows
      .filter((r) => r.is_new_product)
      .map((r) => r.product_name),
    ...overrides,
  }
}

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: Schedule Upload UI (Story 12.4)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // =========================================================================
  // AC2: Preview table with match indicators
  // =========================================================================
  describe('AC2: Preview table with match indicators', () => {
    it('UNIT-011: SchedulePreviewTable renders matched asset row with green checkmark', () => {
      // Given: previewData with a row where asset_match_status is "matched" and errors is empty
      const previewData = createMockPreviewResponse({
        rows: [
          createMockRow({
            row_number: 1,
            asset_match_status: 'matched',
            asset_id: 'uuid-1',
            errors: [],
            is_new_product: false,
          }),
        ],
      })

      // When: The component renders
      render(<SchedulePreviewTable previewData={previewData} />)

      // Then: The row displays a green checkmark icon (text-green-500)
      const rows = screen.getAllByRole('row')
      // First row is header, second row is data
      const dataRow = rows[1]
      const greenIcon = within(dataRow).getByTestId?.('status-icon') ||
        dataRow.querySelector('.text-green-500')
      expect(greenIcon).toBeTruthy()

      // And: The row data is visible in appropriate columns
      expect(screen.getByText('2026-02-16')).toBeInTheDocument()
      expect(screen.getByText('Day')).toBeInTheDocument()
      expect(screen.getByText('Grinder 1')).toBeInTheDocument()
      expect(screen.getByText('Dark Roast 12oz')).toBeInTheDocument()
      expect(screen.getByText('500')).toBeInTheDocument()
    })

    it('UNIT-012: SchedulePreviewTable renders unmatched asset row with warning and suggestions', () => {
      // Given: previewData with a row where asset_match_status is "suggested"
      const previewData = createMockPreviewResponse({
        rows: [
          createMockRow({
            row_number: 2,
            asset_name: 'Grindr 1',
            asset_match_status: 'suggested',
            asset_id: null,
            suggestions: ['Grinder 1', 'Grinder 2'],
            errors: [],
          }),
        ],
      })

      // When: The component renders
      render(<SchedulePreviewTable previewData={previewData} />)

      // Then: The row displays a warning icon
      const rows = screen.getAllByRole('row')
      const dataRow = rows[1]
      const warningIcon = dataRow.querySelector('.text-amber-500') ||
        dataRow.querySelector('.text-destructive')
      expect(warningIcon).toBeTruthy()

      // And: The suggestions are displayed
      expect(screen.getByText(/Grinder 1/)).toBeInTheDocument()
      expect(screen.getByText(/Grinder 2/)).toBeInTheDocument()
    })

    it('UNIT-013: SchedulePreviewTable renders unmatched asset row with no suggestions', () => {
      // Given: previewData with a row where asset_match_status is "unmatched"
      const previewData = createMockPreviewResponse({
        rows: [
          createMockRow({
            row_number: 3,
            asset_name: 'Unknown Machine',
            asset_match_status: 'unmatched',
            asset_id: null,
            suggestions: [],
            errors: [],
          }),
        ],
      })

      // When: The component renders
      render(<SchedulePreviewTable previewData={previewData} />)

      // Then: The row displays a red error icon
      const rows = screen.getAllByRole('row')
      const dataRow = rows[1]
      const errorIcon = dataRow.querySelector('.text-destructive')
      expect(errorIcon).toBeTruthy()

      // And: No suggestions are shown
      expect(screen.queryByText(/did you mean/i)).not.toBeInTheDocument()
    })

    it('UNIT-014: SchedulePreviewTable renders new product row with blue indicator', () => {
      // Given: previewData with a row where is_new_product is true
      const previewData = createMockPreviewResponse({
        rows: [
          createMockRow({
            row_number: 1,
            product_name: 'Blend Special',
            is_new_product: true,
            product_id: null,
            asset_match_status: 'matched',
            errors: [],
          }),
        ],
      })

      // When: The component renders
      render(<SchedulePreviewTable previewData={previewData} />)

      // Then: The product column shows a blue "(new)" indicator
      const newIndicator = screen.getByText('(new)')
      expect(newIndicator).toBeInTheDocument()
      expect(
        newIndicator.className.includes('text-blue-500') ||
          newIndicator.closest('[class*="text-blue"]') !== null ||
          newIndicator.closest('[class*="blue"]') !== null,
      ).toBe(true)

      // And: The product name is displayed
      expect(screen.getByText(/Blend Special/)).toBeInTheDocument()
    })

    it('UNIT-015: SchedulePreviewTable renders validation error row with red highlight and messages', () => {
      // Given: previewData with a row that has validation errors
      const previewData = createMockPreviewResponse({
        rows: [
          createMockRow({
            row_number: 4,
            errors: [
              {
                row_number: 4,
                field: 'scheduled_quantity',
                message: 'Scheduled quantity must be a positive integer',
              },
            ],
            asset_match_status: 'matched',
          }),
        ],
      })

      // When: The component renders
      render(<SchedulePreviewTable previewData={previewData} />)

      // Then: The row has a red background highlight
      const rows = screen.getAllByRole('row')
      const dataRow = rows[1]
      expect(dataRow.className).toMatch(/bg-destructive/)

      // And: Error messages are displayed
      expect(
        screen.getByText(/Scheduled quantity must be a positive integer/),
      ).toBeInTheDocument()
    })

    it('UNIT-016: SchedulePreviewTable displays summary stats bar', () => {
      // Given: previewData with mixed row statuses
      const previewData = createMockPreviewResponse({
        parsed_rows_count: 5,
        matched_assets: ['Grinder 1', 'Grinder 2'],
        new_products: ['New Blend 1'],
        has_errors: true,
        rows: [
          createMockRow({ row_number: 1, asset_match_status: 'matched' }),
          createMockRow({ row_number: 2, asset_match_status: 'matched' }),
          createMockRow({
            row_number: 3,
            asset_match_status: 'suggested',
            suggestions: ['Grinder 3'],
          }),
          createMockRow({
            row_number: 4,
            is_new_product: true,
            product_name: 'New Blend 1',
          }),
          createMockRow({
            row_number: 5,
            errors: [
              { row_number: 5, field: 'date', message: 'Invalid date' },
            ],
          }),
        ],
      })

      // When: The component renders
      render(<SchedulePreviewTable previewData={previewData} />)

      // Then: Summary stats are visible in the stats bar
      const statsBar = screen.getByTestId('summary-stats')
      expect(within(statsBar).getByText(/5.*total/i)).toBeInTheDocument()
      expect(within(statsBar).getByText(/2.*matched/i)).toBeInTheDocument()
      expect(within(statsBar).getByText(/1.*new/i)).toBeInTheDocument()
    })

    it('UNIT-017: SchedulePreviewTable renders all expected columns', () => {
      // Given: previewData with at least one row
      const previewData = createMockPreviewResponse({
        rows: [createMockRow()],
      })

      // When: The component renders
      render(<SchedulePreviewTable previewData={previewData} />)

      // Then: The table has all expected column headers
      const expectedHeaders = [
        'Status',
        'Row #',
        'Date',
        'Shift',
        'Asset',
        'Product',
        'Quantity',
        'Issues',
      ]

      for (const header of expectedHeaders) {
        expect(screen.getByText(header)).toBeInTheDocument()
      }
    })

    it('UNIT-018: SchedulePreviewTable renders multiple error messages per row', () => {
      // Given: previewData with a row containing multiple validation errors
      const previewData = createMockPreviewResponse({
        rows: [
          createMockRow({
            row_number: 3,
            errors: [
              { row_number: 3, field: 'date', message: 'Invalid date format' },
              { row_number: 3, field: 'scheduled_quantity', message: 'Must be positive' },
            ],
          }),
        ],
      })

      // When: The component renders
      render(<SchedulePreviewTable previewData={previewData} />)

      // Then: All error messages are displayed
      expect(screen.getByText(/Invalid date format/)).toBeInTheDocument()
      expect(screen.getByText(/Must be positive/)).toBeInTheDocument()
    })

    it('UNIT-019: SchedulePreviewTable is scrollable for large uploads', () => {
      // Given: previewData with many rows (50+)
      const rows = Array.from({ length: 55 }, (_, i) =>
        createMockRow({
          row_number: i + 1,
          asset_name: `Grinder ${i + 1}`,
          product_name: `Product ${i + 1}`,
        }),
      )
      const previewData = createMockPreviewResponse({ rows })

      // When: The component renders
      const { container } = render(
        <SchedulePreviewTable previewData={previewData} />,
      )

      // Then: The table container has overflow-y-auto and a max-height constraint
      const scrollContainer =
        container.querySelector('.overflow-y-auto') ||
        container.querySelector('[style*="overflow"]')
      expect(scrollContainer).toBeTruthy()
    })
  })

  // =========================================================================
  // AC4: Error rows with fix suggestions
  // =========================================================================
  describe('AC4: Error rows with fix suggestions', () => {
    it('UNIT-023: Error rows are visually distinct from valid rows', () => {
      // Given: previewData with a mix of valid rows and error rows
      const previewData = createMockPreviewResponse({
        rows: [
          createMockRow({ row_number: 1, errors: [] }),
          createMockRow({ row_number: 2, errors: [] }),
          createMockRow({
            row_number: 3,
            errors: [
              { row_number: 3, field: 'date', message: 'Invalid date' },
            ],
          }),
          createMockRow({
            row_number: 4,
            errors: [
              { row_number: 4, field: 'shift', message: 'Unknown shift' },
            ],
          }),
        ],
      })

      // When: The component renders
      render(<SchedulePreviewTable previewData={previewData} />)

      // Then: Rows with errors have red background highlight
      const allRows = screen.getAllByRole('row')
      // Header row + 4 data rows = 5 rows total
      const dataRows = allRows.slice(1)

      // Error rows (index 2 and 3) should have destructive background
      expect(dataRows[2].className).toMatch(/bg-destructive/)
      expect(dataRows[3].className).toMatch(/bg-destructive/)

      // Valid rows (index 0 and 1) should NOT have destructive background
      expect(dataRows[0].className).not.toMatch(/bg-destructive/)
      expect(dataRows[1].className).not.toMatch(/bg-destructive/)
    })

    it('UNIT-024: Error rows display fix suggestions for unmatched assets', () => {
      // Given: previewData with a row where asset_match_status is "suggested"
      const previewData = createMockPreviewResponse({
        rows: [
          createMockRow({
            row_number: 2,
            asset_name: 'Grindr 1',
            asset_match_status: 'suggested',
            asset_id: null,
            suggestions: ['Grinder 1', 'Grinder 2'],
          }),
        ],
      })

      // When: The component renders
      render(<SchedulePreviewTable previewData={previewData} />)

      // Then: The suggested asset names are displayed as fix suggestions
      expect(
        screen.getByText(/did you mean.*Grinder 1.*Grinder 2/i) ||
          (screen.getByText(/Grinder 1/) && screen.getByText(/Grinder 2/)),
      ).toBeTruthy()
    })

    it('UNIT-025: Error rows display specific validation error messages', () => {
      // Given: previewData with rows containing validation errors
      const previewData = createMockPreviewResponse({
        rows: [
          createMockRow({
            row_number: 3,
            errors: [
              {
                row_number: 3,
                field: 'scheduled_quantity',
                message: 'Scheduled quantity must be a positive integer',
              },
            ],
          }),
        ],
      })

      // When: The component renders
      render(<SchedulePreviewTable previewData={previewData} />)

      // Then: Each error's field name and message are displayed in the Issues column
      expect(
        screen.getByText(/scheduled_quantity.*positive integer/i) ||
          screen.getByText(/Scheduled quantity must be a positive integer/),
      ).toBeTruthy()
    })
  })
})
