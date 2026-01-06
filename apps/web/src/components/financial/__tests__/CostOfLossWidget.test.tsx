import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { CostOfLossWidget, type CostOfLossData } from '../CostOfLossWidget'

/**
 * Tests for Financial CostOfLossWidget Component
 *
 * Story: 2.8 - Cost of Loss Widget
 * AC: #1 - Cost of Loss Widget Component
 * AC: #5 - Industrial Clarity Design Compliance
 * AC: #6 - Real-Time Update Support
 */

const mockDailyData: CostOfLossData = {
  total_loss: 12500.00,
  breakdown: {
    downtime_cost: 7500.00,
    waste_cost: 3200.00,
    oee_loss_cost: 1800.00,
  },
  period: 'daily',
  last_updated: '2026-01-05T06:15:00Z',
}

const mockLiveData: CostOfLossData = {
  total_loss: 4850.50,
  breakdown: {
    downtime_cost: 2500.00,
    waste_cost: 1500.50,
    oee_loss_cost: 850.00,
  },
  period: 'live',
  last_updated: '2026-01-06T10:30:00Z',
}

describe('CostOfLossWidget', () => {
  describe('AC#1: Widget displays total financial loss', () => {
    it('displays total financial loss prominently', () => {
      render(
        <CostOfLossWidget
          period="daily"
          data={mockDailyData}
          isLoading={false}
        />
      )

      expect(screen.getByText('Total Financial Impact')).toBeInTheDocument()
      expect(screen.getByText('$12,500')).toBeInTheDocument()
    })

    it('displays values in USD currency format', () => {
      render(
        <CostOfLossWidget
          period="daily"
          data={mockDailyData}
          isLoading={false}
        />
      )

      // Total loss without decimals
      expect(screen.getByText('$12,500')).toBeInTheDocument()

      // Breakdown with decimals
      expect(screen.getByText('$7,500.00')).toBeInTheDocument()
      expect(screen.getByText('$3,200.00')).toBeInTheDocument()
      expect(screen.getByText('$1,800.00')).toBeInTheDocument()
    })

    it('displays widget title "Cost of Loss"', () => {
      render(
        <CostOfLossWidget
          period="daily"
          data={mockDailyData}
          isLoading={false}
        />
      )

      expect(screen.getByText('Cost of Loss')).toBeInTheDocument()
    })
  })

  describe('AC#1: Shows breakdown by loss category', () => {
    it('displays Downtime Cost breakdown', () => {
      render(
        <CostOfLossWidget
          period="daily"
          data={mockDailyData}
          isLoading={false}
          showBreakdown={true}
        />
      )

      expect(screen.getByText('Downtime')).toBeInTheDocument()
      expect(screen.getByText('$7,500.00')).toBeInTheDocument()
    })

    it('displays Waste/Scrap Cost breakdown', () => {
      render(
        <CostOfLossWidget
          period="daily"
          data={mockDailyData}
          isLoading={false}
          showBreakdown={true}
        />
      )

      expect(screen.getByText('Waste/Scrap')).toBeInTheDocument()
      expect(screen.getByText('$3,200.00')).toBeInTheDocument()
    })

    it('displays OEE Loss Cost breakdown', () => {
      render(
        <CostOfLossWidget
          period="daily"
          data={mockDailyData}
          isLoading={false}
          showBreakdown={true}
        />
      )

      expect(screen.getByText('OEE Loss')).toBeInTheDocument()
      expect(screen.getByText('$1,800.00')).toBeInTheDocument()
    })

    it('hides breakdown when showBreakdown is false', () => {
      render(
        <CostOfLossWidget
          period="daily"
          data={mockDailyData}
          isLoading={false}
          showBreakdown={false}
        />
      )

      expect(screen.queryByText('Downtime')).not.toBeInTheDocument()
      expect(screen.queryByText('Waste/Scrap')).not.toBeInTheDocument()
      expect(screen.queryByText('OEE Loss')).not.toBeInTheDocument()
    })
  })

  describe('AC#5: Industrial Clarity Design Compliance', () => {
    it('displays T-1 badge for daily period', () => {
      render(
        <CostOfLossWidget
          period="daily"
          data={mockDailyData}
          isLoading={false}
        />
      )

      expect(screen.getByText('T-1')).toBeInTheDocument()
    })

    it('displays Live badge for live period', () => {
      render(
        <CostOfLossWidget
          period="live"
          data={mockLiveData}
          isLoading={false}
        />
      )

      expect(screen.getByText('Live')).toBeInTheDocument()
    })

    it('shows descriptive text for daily view', () => {
      render(
        <CostOfLossWidget
          period="daily"
          data={mockDailyData}
          isLoading={false}
        />
      )

      expect(screen.getByText("Yesterday's total")).toBeInTheDocument()
    })

    it('shows descriptive text for live view', () => {
      render(
        <CostOfLossWidget
          period="live"
          data={mockLiveData}
          isLoading={false}
        />
      )

      expect(screen.getByText('Current shift accumulated')).toBeInTheDocument()
    })
  })

  describe('AC#6: Real-Time Update Support', () => {
    it('displays last_updated timestamp', () => {
      render(
        <CostOfLossWidget
          period="daily"
          data={mockDailyData}
          isLoading={false}
        />
      )

      expect(screen.getByText(/Last updated:/)).toBeInTheDocument()
    })

    it('shows auto-refresh indicator for live mode', () => {
      render(
        <CostOfLossWidget
          period="live"
          data={mockLiveData}
          isLoading={false}
          autoRefresh={true}
        />
      )

      expect(screen.getByText('Auto-refresh')).toBeInTheDocument()
    })

    it('hides auto-refresh indicator when autoRefresh is false', () => {
      render(
        <CostOfLossWidget
          period="live"
          data={mockLiveData}
          isLoading={false}
          autoRefresh={false}
        />
      )

      expect(screen.queryByText('Auto-refresh')).not.toBeInTheDocument()
    })
  })

  describe('Loading and Error States', () => {
    it('shows loading skeleton when loading', () => {
      const { container } = render(
        <CostOfLossWidget
          period="daily"
          data={null}
          isLoading={true}
        />
      )

      expect(container.querySelector('.animate-pulse')).toBeInTheDocument()
    })

    it('shows error state with message', () => {
      render(
        <CostOfLossWidget
          period="daily"
          data={null}
          isLoading={false}
          error="Failed to fetch data"
        />
      )

      expect(screen.getByText('Failed to fetch data')).toBeInTheDocument()
    })

    it('shows empty state when data is null and not loading', () => {
      render(
        <CostOfLossWidget
          period="daily"
          data={null}
          isLoading={false}
        />
      )

      expect(screen.getByText('No financial data available for this period')).toBeInTheDocument()
    })

    it('shows empty state when total_loss is 0', () => {
      const emptyData: CostOfLossData = {
        total_loss: 0,
        breakdown: { downtime_cost: 0, waste_cost: 0, oee_loss_cost: 0 },
        period: 'daily',
        last_updated: '2026-01-05T06:00:00Z',
      }

      render(
        <CostOfLossWidget
          period="daily"
          data={emptyData}
          isLoading={false}
        />
      )

      expect(screen.getByText('No financial data available for this period')).toBeInTheDocument()
    })
  })

  describe('Props and Customization', () => {
    it('accepts custom className', () => {
      const { container } = render(
        <CostOfLossWidget
          period="daily"
          data={mockDailyData}
          isLoading={false}
          className="custom-class"
        />
      )

      expect(container.firstChild).toHaveClass('custom-class')
    })

    it('uses lastUpdated prop when provided', () => {
      render(
        <CostOfLossWidget
          period="daily"
          data={mockDailyData}
          isLoading={false}
          lastUpdated="2026-01-06T12:00:00Z"
        />
      )

      // Should use the provided lastUpdated instead of data.last_updated
      expect(screen.getByText(/Jan 6/)).toBeInTheDocument()
    })
  })
})
