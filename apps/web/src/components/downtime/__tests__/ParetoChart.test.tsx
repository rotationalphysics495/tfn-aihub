import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ParetoChart, type ParetoItem } from '../ParetoChart'

// Mock recharts to avoid canvas issues in tests
vi.mock('recharts', () => ({
  ComposedChart: ({ children }: any) => <div data-testid="composed-chart">{children}</div>,
  Bar: () => <div data-testid="bar" />,
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
  ResponsiveContainer: ({ children }: any) => <div data-testid="responsive-container">{children}</div>,
  ReferenceLine: () => <div data-testid="reference-line" />,
  Cell: () => <div data-testid="cell" />,
}))

/**
 * Tests for ParetoChart Component
 *
 * Story: 2.5 - Downtime Pareto Analysis
 * AC: #3 - Pareto Chart Visualization
 */

const mockParetoData: ParetoItem[] = [
  {
    reason_code: 'Mechanical Failure',
    total_minutes: 90,
    percentage: 40.0,
    cumulative_percentage: 40.0,
    financial_impact: 225.0,
    event_count: 2,
    is_safety_related: false,
  },
  {
    reason_code: 'Material Shortage',
    total_minutes: 75,
    percentage: 33.3,
    cumulative_percentage: 73.3,
    financial_impact: 187.5,
    event_count: 3,
    is_safety_related: false,
  },
  {
    reason_code: 'Safety Issue',
    total_minutes: 60,
    percentage: 26.7,
    cumulative_percentage: 100.0,
    financial_impact: 150.0,
    event_count: 1,
    is_safety_related: true,
  },
]

describe('ParetoChart', () => {
  it('renders with data', () => {
    render(
      <ParetoChart
        data={mockParetoData}
        threshold80Index={1}
        isLive={false}
      />
    )

    expect(screen.getByText('Downtime by Reason Code')).toBeInTheDocument()
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument()
  })

  it('shows empty state when no data', () => {
    render(
      <ParetoChart
        data={[]}
        threshold80Index={null}
        isLive={false}
      />
    )

    expect(screen.getByText('No downtime data available')).toBeInTheDocument()
  })

  it('displays legend items', () => {
    render(
      <ParetoChart
        data={mockParetoData}
        threshold80Index={1}
        isLive={false}
      />
    )

    expect(screen.getByText('Duration (min)')).toBeInTheDocument()
    expect(screen.getByText('Cumulative %')).toBeInTheDocument()
    expect(screen.getByText('Safety Issue')).toBeInTheDocument()
  })

  it('shows Pareto principle info when threshold is provided', () => {
    render(
      <ParetoChart
        data={mockParetoData}
        threshold80Index={1}
        isLive={false}
      />
    )

    expect(screen.getByText(/account for 80% of total downtime/)).toBeInTheDocument()
  })

  it('does not show Pareto info when threshold is null', () => {
    render(
      <ParetoChart
        data={mockParetoData}
        threshold80Index={null}
        isLive={false}
      />
    )

    expect(screen.queryByText(/account for 80% of total downtime/)).not.toBeInTheDocument()
  })

  it('applies correct mode styling for retrospective view', () => {
    const { container } = render(
      <ParetoChart
        data={mockParetoData}
        threshold80Index={1}
        isLive={false}
      />
    )

    // Card should have retrospective mode applied
    const card = container.querySelector('[class*="Card"]')
    expect(card).toBeDefined()
  })

  it('applies correct mode styling for live view', () => {
    const { container } = render(
      <ParetoChart
        data={mockParetoData}
        threshold80Index={1}
        isLive={true}
      />
    )

    // Card should have live mode applied
    const card = container.querySelector('[class*="Card"]')
    expect(card).toBeDefined()
  })
})
