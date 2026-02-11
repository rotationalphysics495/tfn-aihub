/**
 * ScheduleUploadZone Component Tests (Story 12.4: Schedule Upload UI)
 *
 * TDD tests — these MUST FAIL until the component is implemented.
 *
 * @see Story 12.4 - Schedule Upload UI
 * @see AC #1 - Drag-and-drop zone with file picker
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ScheduleUploadZone } from '../ScheduleUploadZone'

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const createMockFile = (
  name: string,
  size: number,
  type: string,
): File => {
  const file = new File(['x'.repeat(size)], name, { type })
  Object.defineProperty(file, 'size', { value: size })
  return file
}

const createMockDataTransfer = (files: File[]) => {
  return {
    files,
    items: files.map((file) => ({
      kind: 'file',
      type: file.type,
      getAsFile: () => file,
    })),
    types: ['Files'],
  }
}

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: Schedule Upload UI (Story 12.4)', () => {
  let mockOnFileSelected: ReturnType<typeof vi.fn>

  beforeEach(() => {
    vi.clearAllMocks()
    mockOnFileSelected = vi.fn()
  })

  // =========================================================================
  // AC1: Drag-and-drop zone with file picker
  // =========================================================================
  describe('AC1: Drag-and-drop zone with file picker', () => {
    it('UNIT-001: ScheduleUploadZone renders drag-and-drop zone with instructional text', () => {
      // Given: The ScheduleUploadZone component is rendered with default props
      render(<ScheduleUploadZone onFileSelected={mockOnFileSelected} />)

      // Then: A drop zone is visible containing the instructional text
      expect(screen.getByText('Drop CSV or Excel file here')).toBeInTheDocument()

      // And: A "Browse Files" button is displayed
      expect(screen.getByRole('button', { name: /browse files/i })).toBeInTheDocument()

      // And: The accepted formats ".csv, .xlsx" text is visible
      expect(screen.getByText(/\.csv.*\.xlsx/i)).toBeInTheDocument()
    })

    it('UNIT-002: ScheduleUploadZone Browse Files button triggers hidden file input', () => {
      // Given: The ScheduleUploadZone component is rendered
      render(<ScheduleUploadZone onFileSelected={mockOnFileSelected} />)

      // When: We find the hidden file input
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
      expect(fileInput).toBeDefined()

      // Then: The file input has accept=".csv,.xlsx" attribute
      expect(fileInput.accept).toBe('.csv,.xlsx')

      // And: Clicking "Browse Files" triggers the hidden file input click
      const clickSpy = vi.spyOn(fileInput, 'click')
      fireEvent.click(screen.getByRole('button', { name: /browse files/i }))
      expect(clickSpy).toHaveBeenCalled()
    })

    it('UNIT-003: ScheduleUploadZone shows visual drag-active state on drag over', () => {
      // Given: The ScheduleUploadZone component is rendered in its default state
      const { container } = render(
        <ScheduleUploadZone onFileSelected={mockOnFileSelected} />,
      )

      const dropZone = container.firstChild as HTMLElement

      // When: A user drags a file over the drop zone
      fireEvent.dragOver(dropZone, {
        dataTransfer: createMockDataTransfer([]),
      })

      // Then: The drop zone updates to a drag-active visual state
      expect(dropZone.className).toMatch(/border-primary/)
      expect(dropZone.className).toMatch(/bg-primary/)

      // And: When the user drags out, the zone returns to default styling
      fireEvent.dragLeave(dropZone)
      expect(dropZone.className).not.toMatch(/bg-primary/)
    })

    it('UNIT-006: ScheduleUploadZone rejects invalid file types', () => {
      // Given: The ScheduleUploadZone component is rendered
      render(<ScheduleUploadZone onFileSelected={mockOnFileSelected} />)

      const dropZone = document.querySelector('[data-testid="upload-zone"]') ||
        screen.getByText('Drop CSV or Excel file here').closest('div')!

      // When: A user drops a file with an unsupported extension
      const invalidFile = createMockFile('report.pdf', 1024, 'application/pdf')
      fireEvent.drop(dropZone, {
        dataTransfer: createMockDataTransfer([invalidFile]),
      })

      // Then: The onFileSelected callback is NOT called
      expect(mockOnFileSelected).not.toHaveBeenCalled()

      // And: An error message is shown indicating the file type is not supported
      expect(screen.getByText(/not supported|invalid.*type|unsupported/i)).toBeInTheDocument()
    })

    it('UNIT-007: ScheduleUploadZone accepts .csv file via drag and drop', () => {
      // Given: The ScheduleUploadZone component is rendered
      render(<ScheduleUploadZone onFileSelected={mockOnFileSelected} />)

      const dropZone = document.querySelector('[data-testid="upload-zone"]') ||
        screen.getByText('Drop CSV or Excel file here').closest('div')!

      // When: A user drops a valid .csv file onto the drop zone
      const csvFile = createMockFile('schedule.csv', 2048, 'text/csv')
      fireEvent.drop(dropZone, {
        dataTransfer: createMockDataTransfer([csvFile]),
      })

      // Then: The onFileSelected callback is called with the dropped File object
      expect(mockOnFileSelected).toHaveBeenCalledWith(csvFile)

      // And: The file name and formatted file size are displayed in the zone
      expect(screen.getByText('schedule.csv')).toBeInTheDocument()
      expect(screen.getByText(/2.*KB/i)).toBeInTheDocument()

      // And: A "Remove" option is visible to clear the selection
      expect(screen.getByRole('button', { name: /remove/i })).toBeInTheDocument()
    })

    it('UNIT-008: ScheduleUploadZone accepts .xlsx file via drag and drop', () => {
      // Given: The ScheduleUploadZone component is rendered
      render(<ScheduleUploadZone onFileSelected={mockOnFileSelected} />)

      const dropZone = document.querySelector('[data-testid="upload-zone"]') ||
        screen.getByText('Drop CSV or Excel file here').closest('div')!

      // When: A user drops a valid .xlsx file onto the drop zone
      const xlsxFile = createMockFile(
        'schedule.xlsx',
        15360,
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      )
      fireEvent.drop(dropZone, {
        dataTransfer: createMockDataTransfer([xlsxFile]),
      })

      // Then: The onFileSelected callback is called with the dropped File object
      expect(mockOnFileSelected).toHaveBeenCalledWith(xlsxFile)

      // And: The file name and formatted file size are displayed
      expect(screen.getByText('schedule.xlsx')).toBeInTheDocument()
      expect(screen.getByText(/15.*KB/i)).toBeInTheDocument()
    })

    it('UNIT-009: ScheduleUploadZone Remove button clears selected file', () => {
      // Given: The ScheduleUploadZone component has a file already selected
      render(<ScheduleUploadZone onFileSelected={mockOnFileSelected} />)

      const dropZone = document.querySelector('[data-testid="upload-zone"]') ||
        screen.getByText('Drop CSV or Excel file here').closest('div')!

      // Select a file first
      const csvFile = createMockFile('schedule.csv', 2048, 'text/csv')
      fireEvent.drop(dropZone, {
        dataTransfer: createMockDataTransfer([csvFile]),
      })

      // Verify file is shown
      expect(screen.getByText('schedule.csv')).toBeInTheDocument()

      // When: The user clicks the "Remove" button
      fireEvent.click(screen.getByRole('button', { name: /remove/i }))

      // Then: The file info is cleared
      expect(screen.queryByText('schedule.csv')).not.toBeInTheDocument()

      // And: The drop zone returns to its initial state
      expect(screen.getByText('Drop CSV or Excel file here')).toBeInTheDocument()
    })

    it('UNIT-010: ScheduleUploadZone accepts .csv file via Browse Files button', () => {
      // Given: The ScheduleUploadZone component is rendered
      render(<ScheduleUploadZone onFileSelected={mockOnFileSelected} />)

      // When: The user selects a .csv file via the hidden file input
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
      const csvFile = createMockFile('weekly_schedule.csv', 4096, 'text/csv')

      fireEvent.change(fileInput, {
        target: { files: [csvFile] },
      })

      // Then: The onFileSelected callback is called with the selected File object
      expect(mockOnFileSelected).toHaveBeenCalledWith(csvFile)
    })
  })
})
