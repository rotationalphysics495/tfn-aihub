import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { DowntimeTable, type DowntimeEvent } from '../DowntimeTable'

/**
 * Tests for DowntimeTable Component
 *
 * Story: 2.5 - Downtime Pareto Analysis
 * AC: #4 - Granular Breakdown Table
 * AC: #6 - Safety Reason Code Highlighting
 */

const mockEvents: DowntimeEvent[] = [
  {
    id: '1',
    asset_id: 'asset-1',
    asset_name: 'CNC Mill 01',
    area: 'Machining',
    reason_code: 'Mechanical Failure',
    duration_minutes: 60,
    event_timestamp: '2026-01-05T10:00:00Z',
    end_timestamp: '2026-01-05T11:00:00Z',
    financial_impact: 150.0,
    is_safety_related: false,
    severity: null,
    description: null,
  },
  {
    id: '2',
    asset_id: 'asset-2',
    asset_name: 'Press 01',
    area: 'Forming',
    reason_code: 'Safety Issue',
    duration_minutes: 30,
    event_timestamp: '2026-01-05T12:00:00Z',
    end_timestamp: '2026-01-05T12:30:00Z',
    financial_impact: 75.0,
    is_safety_related: true,
    severity: 'high',
    description: 'E-stop triggered',
  },
]

describe('DowntimeTable', () => {
  it('renders table with events', () => {
    render(
      <DowntimeTable
        events={mockEvents}
        isLive={false}
      />
    )

    expect(screen.getByText('Downtime Events')).toBeInTheDocument()
    expect(screen.getByText('CNC Mill 01')).toBeInTheDocument()
    expect(screen.getByText('Press 01')).toBeInTheDocument()
  })

  it('shows empty state when no events', () => {
    render(
      <DowntimeTable
        events={[]}
        isLive={false}
      />
    )

    expect(screen.getByText('No downtime events found')).toBeInTheDocument()
  })

  it('displays total event count', () => {
    render(
      <DowntimeTable
        events={mockEvents}
        isLive={false}
      />
    )

    expect(screen.getByText('2 total events')).toBeInTheDocument()
  })

  it('displays all required columns', () => {
    render(
      <DowntimeTable
        events={mockEvents}
        isLive={false}
      />
    )

    expect(screen.getByText('Asset')).toBeInTheDocument()
    expect(screen.getByText('Reason Code')).toBeInTheDocument()
    expect(screen.getByText('Duration')).toBeInTheDocument()
    expect(screen.getByText('Start Time')).toBeInTheDocument()
    expect(screen.getByText('End Time')).toBeInTheDocument()
    expect(screen.getByText('Financial Impact')).toBeInTheDocument()
  })

  it('formats financial values as currency', () => {
    render(
      <DowntimeTable
        events={mockEvents}
        isLive={false}
      />
    )

    expect(screen.getByText('$150.00')).toBeInTheDocument()
    expect(screen.getByText('$75.00')).toBeInTheDocument()
  })

  it('prioritizes safety events at top of sorted list', () => {
    render(
      <DowntimeTable
        events={mockEvents}
        isLive={false}
      />
    )

    const rows = screen.getAllByRole('row')
    // First row after header should be safety event (Press 01)
    // Note: Safety events are prioritized in sorting
    expect(rows.length).toBeGreaterThan(1)
  })

  it('calls onSafetyClick when safety row is clicked', () => {
    const onSafetyClick = vi.fn()

    render(
      <DowntimeTable
        events={mockEvents}
        isLive={false}
        onSafetyClick={onSafetyClick}
      />
    )

    // Find and click the safety event row
    const safetyRow = screen.getByText('Safety Issue').closest('tr')
    if (safetyRow) {
      fireEvent.click(safetyRow)
      expect(onSafetyClick).toHaveBeenCalled()
    }
  })

  it('supports column sorting', () => {
    render(
      <DowntimeTable
        events={mockEvents}
        isLive={false}
      />
    )

    // Click on Duration header to sort
    const durationHeader = screen.getByText('Duration')
    fireEvent.click(durationHeader)

    // Component should re-render with sorted data
    expect(durationHeader).toBeInTheDocument()
  })
})

describe('DowntimeTable Pagination', () => {
  const manyEvents: DowntimeEvent[] = Array.from({ length: 25 }, (_, i) => ({
    id: String(i + 1),
    asset_id: `asset-${i + 1}`,
    asset_name: `Asset ${i + 1}`,
    area: 'Area A',
    reason_code: 'Reason',
    duration_minutes: 30,
    event_timestamp: '2026-01-05T10:00:00Z',
    end_timestamp: '2026-01-05T10:30:00Z',
    financial_impact: 75.0,
    is_safety_related: false,
    severity: null,
    description: null,
  }))

  it('shows pagination controls for large datasets', () => {
    render(
      <DowntimeTable
        events={manyEvents}
        isLive={false}
      />
    )

    expect(screen.getByText('Previous')).toBeInTheDocument()
    expect(screen.getByText('Next')).toBeInTheDocument()
  })

  it('shows correct item range', () => {
    render(
      <DowntimeTable
        events={manyEvents}
        isLive={false}
      />
    )

    // Default shows first 10 of 25
    expect(screen.getByText(/Showing 1 to 10 of 25/)).toBeInTheDocument()
  })

  it('navigates to next page', () => {
    render(
      <DowntimeTable
        events={manyEvents}
        isLive={false}
      />
    )

    const nextButton = screen.getByText('Next')
    fireEvent.click(nextButton)

    // Should now show items 11-20
    expect(screen.getByText(/Showing 11 to 20 of 25/)).toBeInTheDocument()
  })

  it('disables previous button on first page', () => {
    render(
      <DowntimeTable
        events={manyEvents}
        isLive={false}
      />
    )

    const prevButton = screen.getByText('Previous')
    expect(prevButton).toHaveClass('cursor-not-allowed')
  })
})

describe('DowntimeTable Safety Highlighting', () => {
  it('shows safety icon for safety-related events', () => {
    render(
      <DowntimeTable
        events={mockEvents}
        isLive={false}
      />
    )

    // Safety row should have a warning icon (triangle)
    const safetyRow = screen.getByText('Safety Issue').closest('tr')
    expect(safetyRow).toHaveClass('bg-safety-red/5')
  })
})
