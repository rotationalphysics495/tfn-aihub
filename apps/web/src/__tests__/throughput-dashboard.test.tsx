/**
 * Throughput Dashboard Tests
 *
 * Tests for Story 2.3 Acceptance Criteria:
 * 1. Dashboard Route and Navigation
 * 2. Actual vs Target Visualization
 * 3. Status Indicators (on_target, behind, critical)
 * 4. Data Freshness Indicator
 * 5. Real-time Data Binding (covered by integration tests)
 * 6. Responsive Layout
 * 7. Empty State Handling
 * 8. Asset Filtering
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import * as React from 'react'

import {
  StatusBadge,
  ThroughputCard,
  ThroughputGrid,
  EmptyState,
  FilterBar,
  DataFreshnessIndicator,
  type ThroughputCardData,
  type ThroughputStatus,
} from '@/components/production'

// Mock data for tests
const mockAsset: ThroughputCardData = {
  id: '123e4567-e89b-12d3-a456-426614174000',
  name: 'Grinder 5',
  area: 'Grinding',
  actual_output: 90,
  target_output: 100,
  variance: -10,
  percentage: 90,
  status: 'behind' as ThroughputStatus,
  snapshot_timestamp: new Date().toISOString(),
}

const mockAssetOnTarget: ThroughputCardData = {
  ...mockAsset,
  id: '223e4567-e89b-12d3-a456-426614174001',
  name: 'Assembly Line 1',
  actual_output: 100,
  target_output: 100,
  variance: 0,
  percentage: 100,
  status: 'on_target' as ThroughputStatus,
}

const mockAssetCritical: ThroughputCardData = {
  ...mockAsset,
  id: '323e4567-e89b-12d3-a456-426614174002',
  name: 'Press 3',
  actual_output: 70,
  target_output: 100,
  variance: -30,
  percentage: 70,
  status: 'critical' as ThroughputStatus,
}

// ========================================
// AC #3: Status Indicators Tests
// ========================================
describe('AC #3: Status Indicators', () => {
  describe('StatusBadge Component', () => {
    it('should render on_target status with success styling', () => {
      render(<StatusBadge status="on_target" />)
      const badge = screen.getByRole('status')
      expect(badge).toHaveTextContent('On Target')
      expect(badge).toHaveAttribute('aria-label', 'Production status: On Target')
      // Check for success green classes
      expect(badge.className).toContain('success-green')
    })

    it('should render behind status with warning styling', () => {
      render(<StatusBadge status="behind" />)
      const badge = screen.getByRole('status')
      expect(badge).toHaveTextContent('Behind')
      // Check for warning amber classes
      expect(badge.className).toContain('warning-amber')
    })

    it('should render critical status with amber-dark styling', () => {
      render(<StatusBadge status="critical" />)
      const badge = screen.getByRole('status')
      expect(badge).toHaveTextContent('Critical')
      // Check for amber-dark classes (NOT safety-red)
      expect(badge.className).toContain('warning-amber')
      expect(badge.className).not.toContain('safety-red')
    })

    it('should NOT use safety-red for any production status', () => {
      const statuses: ThroughputStatus[] = ['on_target', 'behind', 'critical']

      statuses.forEach((status) => {
        const { container } = render(<StatusBadge status={status} />)
        const badge = container.querySelector('[role="status"]')
        expect(badge?.className).not.toContain('safety-red')
      })
    })

    it('should support different sizes', () => {
      const { rerender } = render(<StatusBadge status="on_target" size="sm" />)
      let badge = screen.getByRole('status')
      expect(badge.className).toContain('text-xs')

      rerender(<StatusBadge status="on_target" size="md" />)
      badge = screen.getByRole('status')
      expect(badge.className).toContain('text-sm')

      rerender(<StatusBadge status="on_target" size="lg" />)
      badge = screen.getByRole('status')
      expect(badge.className).toContain('text-base')
    })
  })
})

// ========================================
// AC #2: Actual vs Target Visualization Tests
// ========================================
describe('AC #2: Actual vs Target Visualization', () => {
  describe('ThroughputCard Component', () => {
    it('should display asset name', () => {
      render(<ThroughputCard data={mockAsset} />)
      expect(screen.getByText('Grinder 5')).toBeInTheDocument()
    })

    it('should display asset area', () => {
      render(<ThroughputCard data={mockAsset} />)
      expect(screen.getByText('Grinding')).toBeInTheDocument()
    })

    it('should display actual output', () => {
      render(<ThroughputCard data={mockAsset} />)
      expect(screen.getByText('90')).toBeInTheDocument()
      expect(screen.getByText('Actual')).toBeInTheDocument()
    })

    it('should display target output', () => {
      render(<ThroughputCard data={mockAsset} />)
      expect(screen.getByText('100')).toBeInTheDocument()
      expect(screen.getByText('Target')).toBeInTheDocument()
    })

    it('should display variance with correct sign', () => {
      render(<ThroughputCard data={mockAsset} />)
      expect(screen.getByText('-10')).toBeInTheDocument()
    })

    it('should display positive variance with plus sign', () => {
      const positiveAsset = { ...mockAsset, variance: 10 }
      render(<ThroughputCard data={positiveAsset} />)
      expect(screen.getByText('+10')).toBeInTheDocument()
    })

    it('should display percentage of target', () => {
      render(<ThroughputCard data={mockAsset} />)
      expect(screen.getByText('90.0%')).toBeInTheDocument()
    })

    it('should display status badge', () => {
      render(<ThroughputCard data={mockAsset} />)
      expect(screen.getByRole('status')).toBeInTheDocument()
    })

    it('should display progress bar', () => {
      render(<ThroughputCard data={mockAsset} />)
      const progressBar = screen.getByRole('progressbar')
      expect(progressBar).toBeInTheDocument()
      expect(progressBar).toHaveAttribute('aria-valuenow', '90')
    })

    it('should use live mode card variant', () => {
      const { container } = render(<ThroughputCard data={mockAsset} />)
      const card = container.firstChild
      expect(card?.className).toContain('live')
    })

    it('should format large numbers with K suffix', () => {
      const largeOutputAsset = {
        ...mockAsset,
        actual_output: 15000,
        target_output: 20000,
      }
      render(<ThroughputCard data={largeOutputAsset} />)
      expect(screen.getByText('15.0K')).toBeInTheDocument()
      expect(screen.getByText('20.0K')).toBeInTheDocument()
    })
  })
})

// ========================================
// AC #6: Responsive Layout Tests
// ========================================
describe('AC #6: Responsive Layout', () => {
  describe('ThroughputGrid Component', () => {
    it('should render grid with correct responsive classes', () => {
      const assets = [mockAsset, mockAssetOnTarget, mockAssetCritical]
      const { container } = render(<ThroughputGrid assets={assets} />)

      const grid = container.firstChild
      expect(grid?.className).toContain('grid-cols-1')
      expect(grid?.className).toContain('md:grid-cols-2')
      expect(grid?.className).toContain('lg:grid-cols-3')
    })

    it('should render all assets', () => {
      const assets = [mockAsset, mockAssetOnTarget, mockAssetCritical]
      render(<ThroughputGrid assets={assets} />)

      expect(screen.getByText('Grinder 5')).toBeInTheDocument()
      expect(screen.getByText('Assembly Line 1')).toBeInTheDocument()
      expect(screen.getByText('Press 3')).toBeInTheDocument()
    })

    it('should return null for empty assets array', () => {
      const { container } = render(<ThroughputGrid assets={[]} />)
      expect(container.firstChild).toBeNull()
    })

    it('should have appropriate gap for touch targets', () => {
      const assets = [mockAsset]
      const { container } = render(<ThroughputGrid assets={assets} />)

      const grid = container.firstChild
      expect(grid?.className).toContain('gap-4')
      expect(grid?.className).toContain('md:gap-6')
    })
  })
})

// ========================================
// AC #7: Empty State Handling Tests
// ========================================
describe('AC #7: Empty State Handling', () => {
  describe('EmptyState Component', () => {
    it('should display meaningful empty message', () => {
      render(<EmptyState />)
      expect(screen.getByText('No Throughput Data Available')).toBeInTheDocument()
    })

    it('should display waiting for data message', () => {
      render(<EmptyState />)
      expect(screen.getByText(/Waiting for Live Pulse data/)).toBeInTheDocument()
    })

    it('should display live indicator', () => {
      render(<EmptyState />)
      expect(screen.getByText(/Monitoring for incoming data/)).toBeInTheDocument()
    })

    it('should use live mode card', () => {
      const { container } = render(<EmptyState />)
      const card = container.querySelector('[class*="live"]')
      expect(card).toBeInTheDocument()
    })

    it('should not break or show errors', () => {
      expect(() => render(<EmptyState />)).not.toThrow()
    })
  })
})

// ========================================
// AC #4: Data Freshness Indicator Tests
// ========================================
describe('AC #4: Data Freshness Indicator', () => {
  describe('DataFreshnessIndicator Component', () => {
    const mockRefresh = vi.fn()

    beforeEach(() => {
      mockRefresh.mockClear()
    })

    it('should display last updated timestamp', () => {
      const recentTime = new Date().toISOString()
      render(
        <DataFreshnessIndicator
          lastUpdated={recentTime}
          onRefresh={mockRefresh}
        />
      )
      expect(screen.getByText(/Last updated:/)).toBeInTheDocument()
    })

    it('should show "Just now" for recent data', () => {
      const recentTime = new Date().toISOString()
      render(
        <DataFreshnessIndicator
          lastUpdated={recentTime}
          onRefresh={mockRefresh}
        />
      )
      // Use regex to handle text split across elements
      expect(screen.getByText(/Just now/)).toBeInTheDocument()
    })

    it('should show green indicator for fresh data', () => {
      const recentTime = new Date().toISOString()
      const { container } = render(
        <DataFreshnessIndicator
          lastUpdated={recentTime}
          onRefresh={mockRefresh}
        />
      )
      const indicator = container.querySelector('[aria-label="Data is fresh"]')
      expect(indicator).toBeInTheDocument()
      expect(indicator?.className).toContain('success-green')
    })

    it('should show warning for stale data (>60 seconds)', () => {
      const staleTime = new Date(Date.now() - 120000).toISOString()
      const { container } = render(
        <DataFreshnessIndicator
          lastUpdated={staleTime}
          onRefresh={mockRefresh}
        />
      )
      const indicator = container.querySelector('[aria-label="Data may be stale"]')
      expect(indicator).toBeInTheDocument()
      expect(screen.getByText(/Data may be stale/)).toBeInTheDocument()
    })

    it('should have refresh button', () => {
      const recentTime = new Date().toISOString()
      render(
        <DataFreshnessIndicator
          lastUpdated={recentTime}
          onRefresh={mockRefresh}
        />
      )
      const refreshButton = screen.getByRole('button', { name: /refresh/i })
      expect(refreshButton).toBeInTheDocument()
    })

    it('should call onRefresh when refresh button clicked', () => {
      const recentTime = new Date().toISOString()
      render(
        <DataFreshnessIndicator
          lastUpdated={recentTime}
          onRefresh={mockRefresh}
        />
      )
      const refreshButton = screen.getByRole('button', { name: /refresh/i })
      fireEvent.click(refreshButton)
      expect(mockRefresh).toHaveBeenCalledTimes(1)
    })

    it('should disable refresh button when refreshing', () => {
      const recentTime = new Date().toISOString()
      render(
        <DataFreshnessIndicator
          lastUpdated={recentTime}
          onRefresh={mockRefresh}
          isRefreshing={true}
        />
      )
      const refreshButton = screen.getByRole('button', { name: /refresh/i })
      expect(refreshButton).toBeDisabled()
    })

    it('should show "No data available" when lastUpdated is null', () => {
      render(
        <DataFreshnessIndicator
          lastUpdated={null}
          onRefresh={mockRefresh}
        />
      )
      expect(screen.getByText('No data available')).toBeInTheDocument()
    })
  })
})

// ========================================
// AC #8: Asset Filtering Tests
// ========================================
describe('AC #8: Asset Filtering', () => {
  describe('FilterBar Component', () => {
    const mockOnAreaChange = vi.fn()
    const mockOnStatusChange = vi.fn()
    const defaultCounts = {
      total: 10,
      on_target: 5,
      behind: 3,
      critical: 2,
    }
    const areas = ['Grinding', 'Assembly', 'Pressing']

    beforeEach(() => {
      mockOnAreaChange.mockClear()
      mockOnStatusChange.mockClear()
    })

    it('should render area filter dropdown', () => {
      render(
        <FilterBar
          areas={areas}
          selectedArea={null}
          selectedStatus={null}
          onAreaChange={mockOnAreaChange}
          onStatusChange={mockOnStatusChange}
          counts={defaultCounts}
        />
      )
      expect(screen.getByLabelText(/area/i)).toBeInTheDocument()
    })

    it('should render status filter tabs', () => {
      render(
        <FilterBar
          areas={areas}
          selectedArea={null}
          selectedStatus={null}
          onAreaChange={mockOnAreaChange}
          onStatusChange={mockOnStatusChange}
          counts={defaultCounts}
        />
      )
      expect(screen.getByRole('tab', { name: /all/i })).toBeInTheDocument()
      expect(screen.getByRole('tab', { name: /on target/i })).toBeInTheDocument()
      expect(screen.getByRole('tab', { name: /behind/i })).toBeInTheDocument()
      expect(screen.getByRole('tab', { name: /critical/i })).toBeInTheDocument()
    })

    it('should display counts for each status', () => {
      render(
        <FilterBar
          areas={areas}
          selectedArea={null}
          selectedStatus={null}
          onAreaChange={mockOnAreaChange}
          onStatusChange={mockOnStatusChange}
          counts={defaultCounts}
        />
      )
      expect(screen.getByText('10')).toBeInTheDocument() // Total
      expect(screen.getByText('5')).toBeInTheDocument()  // On target
      expect(screen.getByText('3')).toBeInTheDocument()  // Behind
      expect(screen.getByText('2')).toBeInTheDocument()  // Critical
    })

    it('should call onAreaChange when area selected', () => {
      render(
        <FilterBar
          areas={areas}
          selectedArea={null}
          selectedStatus={null}
          onAreaChange={mockOnAreaChange}
          onStatusChange={mockOnStatusChange}
          counts={defaultCounts}
        />
      )
      const select = screen.getByLabelText(/area/i)
      fireEvent.change(select, { target: { value: 'Grinding' } })
      expect(mockOnAreaChange).toHaveBeenCalledWith('Grinding')
    })

    it('should call onStatusChange when status tab clicked', () => {
      render(
        <FilterBar
          areas={areas}
          selectedArea={null}
          selectedStatus={null}
          onAreaChange={mockOnAreaChange}
          onStatusChange={mockOnStatusChange}
          counts={defaultCounts}
        />
      )
      const behindTab = screen.getByRole('tab', { name: /behind/i })
      fireEvent.click(behindTab)
      expect(mockOnStatusChange).toHaveBeenCalledWith('behind')
    })

    it('should show "All Areas" option in dropdown', () => {
      render(
        <FilterBar
          areas={areas}
          selectedArea={null}
          selectedStatus={null}
          onAreaChange={mockOnAreaChange}
          onStatusChange={mockOnStatusChange}
          counts={defaultCounts}
        />
      )
      const select = screen.getByLabelText(/area/i)
      expect(select).toContainHTML('All Areas')
    })

    it('should highlight selected status tab', () => {
      render(
        <FilterBar
          areas={areas}
          selectedArea={null}
          selectedStatus="behind"
          onAreaChange={mockOnAreaChange}
          onStatusChange={mockOnStatusChange}
          counts={defaultCounts}
        />
      )
      const behindTab = screen.getByRole('tab', { name: /behind/i })
      expect(behindTab).toHaveAttribute('aria-selected', 'true')
    })
  })
})

// ========================================
// Glanceability Tests (AC #6 - Typography)
// ========================================
describe('Glanceability - Typography for Factory Floor', () => {
  it('ThroughputCard percentage should use large font', () => {
    render(<ThroughputCard data={mockAsset} />)
    const percentage = screen.getByText('90.0%')
    // Should have text-5xl (60px) for glanceability
    expect(percentage.className).toContain('text-5xl')
  })

  it('ThroughputCard should have readable metric values', () => {
    render(<ThroughputCard data={mockAsset} />)
    const actualValue = screen.getByText('90')
    // Metric values should be at least text-2xl
    expect(actualValue.className).toContain('text-2xl')
  })
})

// ========================================
// Accessibility Tests
// ========================================
describe('Accessibility', () => {
  it('StatusBadge should have role="status"', () => {
    render(<StatusBadge status="on_target" />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('StatusBadge should have aria-label', () => {
    render(<StatusBadge status="behind" />)
    const badge = screen.getByRole('status')
    expect(badge).toHaveAttribute('aria-label')
  })

  it('Progress bar should have correct aria attributes', () => {
    render(<ThroughputCard data={mockAsset} />)
    const progressBar = screen.getByRole('progressbar')
    expect(progressBar).toHaveAttribute('aria-valuenow')
    expect(progressBar).toHaveAttribute('aria-valuemin', '0')
    expect(progressBar).toHaveAttribute('aria-valuemax', '100')
    expect(progressBar).toHaveAttribute('aria-label')
  })

  it('FilterBar status tabs should have tablist role', () => {
    render(
      <FilterBar
        areas={[]}
        selectedArea={null}
        selectedStatus={null}
        onAreaChange={() => {}}
        onStatusChange={() => {}}
        counts={{ total: 0, on_target: 0, behind: 0, critical: 0 }}
      />
    )
    expect(screen.getByRole('tablist')).toBeInTheDocument()
  })

  it('Refresh button should have aria-label', () => {
    render(
      <DataFreshnessIndicator
        lastUpdated={new Date().toISOString()}
        onRefresh={() => {}}
      />
    )
    const button = screen.getByRole('button')
    expect(button).toHaveAttribute('aria-label')
  })
})
