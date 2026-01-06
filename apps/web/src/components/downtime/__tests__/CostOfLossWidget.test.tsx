import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { CostOfLossWidget, type CostOfLossSummaryData } from '../CostOfLossWidget'

/**
 * Tests for CostOfLossWidget Component
 *
 * Story: 2.5 - Downtime Pareto Analysis
 * AC: #5 - Financial Impact Integration
 */

const mockSummaryData: CostOfLossSummaryData = {
  total_financial_loss: 3802.50,
  total_downtime_minutes: 507,
  total_downtime_hours: 8.45,
  top_reason_code: 'Mechanical Failure',
  top_reason_percentage: 35.5,
  safety_events_count: 2,
  safety_downtime_minutes: 90,
  data_source: 'daily_summaries',
  last_updated: '2026-01-05T06:00:00Z',
}

describe('CostOfLossWidget', () => {
  it('displays total financial loss prominently', () => {
    render(
      <CostOfLossWidget
        data={mockSummaryData}
        isLive={false}
        isLoading={false}
      />
    )

    expect(screen.getByText('Total Cost of Loss')).toBeInTheDocument()
    expect(screen.getByText('$3,803')).toBeInTheDocument()
  })

  it('displays total downtime in hours and minutes', () => {
    render(
      <CostOfLossWidget
        data={mockSummaryData}
        isLive={false}
        isLoading={false}
      />
    )

    expect(screen.getByText('Total Downtime')).toBeInTheDocument()
    // 8.45 hours displayed as "8.4 hrs"
    expect(screen.getByText('8.4 hrs')).toBeInTheDocument()
    expect(screen.getByText('507 minutes')).toBeInTheDocument()
  })

  it('displays top reason code with percentage', () => {
    render(
      <CostOfLossWidget
        data={mockSummaryData}
        isLive={false}
        isLoading={false}
      />
    )

    expect(screen.getByText('Top Reason')).toBeInTheDocument()
    expect(screen.getByText('Mechanical Failure')).toBeInTheDocument()
    expect(screen.getByText('35.5% of total')).toBeInTheDocument()
  })

  it('displays safety events count', () => {
    render(
      <CostOfLossWidget
        data={mockSummaryData}
        isLive={false}
        isLoading={false}
      />
    )

    expect(screen.getByText('Safety Issues')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
    expect(screen.getByText('90 min downtime')).toBeInTheDocument()
  })

  it('shows green when no safety events', () => {
    const noSafetyData: CostOfLossSummaryData = {
      ...mockSummaryData,
      safety_events_count: 0,
      safety_downtime_minutes: 0,
    }

    render(
      <CostOfLossWidget
        data={noSafetyData}
        isLive={false}
        isLoading={false}
      />
    )

    expect(screen.getByText('No safety incidents')).toBeInTheDocument()
  })

  it('shows loading skeleton when loading', () => {
    const { container } = render(
      <CostOfLossWidget
        data={null}
        isLive={false}
        isLoading={true}
      />
    )

    expect(container.querySelector('.animate-pulse')).toBeInTheDocument()
  })

  it('shows no data message when data is null', () => {
    render(
      <CostOfLossWidget
        data={null}
        isLive={false}
        isLoading={false}
      />
    )

    expect(screen.getByText('No data available')).toBeInTheDocument()
  })

  it('handles missing top reason gracefully', () => {
    const noTopReasonData: CostOfLossSummaryData = {
      ...mockSummaryData,
      top_reason_code: null,
      top_reason_percentage: null,
    }

    render(
      <CostOfLossWidget
        data={noTopReasonData}
        isLive={false}
        isLoading={false}
      />
    )

    expect(screen.getByText('Top Reason')).toBeInTheDocument()
    expect(screen.getByText('--')).toBeInTheDocument()
  })
})
