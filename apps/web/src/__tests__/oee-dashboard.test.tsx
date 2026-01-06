/**
 * OEE Dashboard Tests
 *
 * Tests for Story 2.4 Acceptance Criteria:
 * 1. OEE displays three core components: Availability, Performance, Quality
 * 2. OEE metrics computed from daily_summaries (T-1) and live_snapshots (T-15m)
 * 3. Plant-wide OEE prominently displayed with gauge/large numeric indicator
 * 4. Individual asset OEE breakdown showing each component's contribution
 * 5. OEE values update within 60 seconds (via auto-refresh)
 * 6. Visual indicators distinguish Yesterday's Analysis (T-1) and Live Pulse (T-15m)
 * 7. OEE targets shown alongside actual values for comparison
 * 8. Color-coded status indicators: Green (>=85%), Yellow (70-84%), Red (<70%)
 * 9. OEE view follows "Industrial Clarity" design - readable from 3 feet
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import * as React from 'react'

import {
  OEEGauge,
  OEEBreakdown,
  OEEStatusBadge,
  OEEStatusDot,
  AssetOEEList,
  type AssetOEEData,
  type OEEStatusType,
} from '@/components/oee'

// Mock data for tests
const mockPlantOEE = {
  overall: 78.5,
  availability: 92.1,
  performance: 88.3,
  quality: 96.5,
  target: 85.0,
  status: 'yellow' as OEEStatusType,
}

const mockAsset: AssetOEEData = {
  asset_id: '123e4567-e89b-12d3-a456-426614174000',
  name: 'Grinder 5',
  area: 'Grinding',
  oee: 82.3,
  availability: 95.0,
  performance: 90.1,
  quality: 96.2,
  target: 85.0,
  status: 'yellow',
}

const mockAssetGreen: AssetOEEData = {
  ...mockAsset,
  asset_id: '223e4567-e89b-12d3-a456-426614174001',
  name: 'Assembly Line 1',
  oee: 88.5,
  status: 'green',
}

const mockAssetRed: AssetOEEData = {
  ...mockAsset,
  asset_id: '323e4567-e89b-12d3-a456-426614174002',
  name: 'Press 3',
  oee: 65.0,
  status: 'red',
}

// ========================================
// AC #8: Color-Coded Status Indicators Tests
// ========================================
describe('AC #8: Color-Coded Status Indicators', () => {
  describe('OEEStatusBadge Component', () => {
    it('should render green status for OEE >= 85%', () => {
      render(<OEEStatusBadge status="green" />)
      const badge = screen.getByText('On Target')
      expect(badge.className).toContain('success-green')
    })

    it('should render yellow status for OEE 70-84%', () => {
      render(<OEEStatusBadge status="yellow" />)
      const badge = screen.getByText('Attention')
      expect(badge.className).toContain('warning-amber')
    })

    it('should render red status for OEE < 70%', () => {
      render(<OEEStatusBadge status="red" />)
      const badge = screen.getByText('Critical')
      // Uses standard red (red-500), NOT safety-red which is reserved for incidents
      expect(badge.className).toContain('red-')
      expect(badge.className).not.toContain('safety-red')
    })

    it('should render unknown status for null OEE', () => {
      render(<OEEStatusBadge status="unknown" />)
      const badge = screen.getByText('Unknown')
      expect(badge.className).toContain('muted')
    })

    it('should NOT use safety-red for any OEE status', () => {
      const statuses: OEEStatusType[] = ['green', 'yellow', 'red', 'unknown']

      statuses.forEach((status) => {
        const { container, unmount } = render(<OEEStatusBadge status={status} />)
        const badge = container.querySelector('span')
        expect(badge?.className).not.toContain('safety-red')
        unmount()
      })
    })

    it('should support different sizes', () => {
      const { rerender } = render(<OEEStatusBadge status="green" size="sm" />)
      let badge = screen.getByText('On Target')
      expect(badge.className).toContain('text-xs')

      rerender(<OEEStatusBadge status="green" size="md" />)
      badge = screen.getByText('On Target')
      expect(badge.className).toContain('text-sm')

      rerender(<OEEStatusBadge status="green" size="lg" />)
      badge = screen.getByText('On Target')
      expect(badge.className).toContain('text-base')
    })

    it('should hide label when showLabel=false', () => {
      render(<OEEStatusBadge status="green" showLabel={false} />)
      expect(screen.queryByText('On Target')).not.toBeInTheDocument()
    })
  })

  describe('OEEStatusDot Component', () => {
    it('should render colored dot for each status', () => {
      const { container: green } = render(<OEEStatusDot status="green" />)
      expect(green.querySelector('span')?.className).toContain('success-green')

      const { container: yellow } = render(<OEEStatusDot status="yellow" />)
      expect(yellow.querySelector('span')?.className).toContain('warning-amber')

      const { container: red } = render(<OEEStatusDot status="red" />)
      expect(red.querySelector('span')?.className).toContain('red-')
    })
  })
})

// ========================================
// AC #3: Plant-Wide OEE Gauge Tests
// ========================================
describe('AC #3: Plant-Wide OEE Prominently Displayed', () => {
  describe('OEEGauge Component', () => {
    it('should display OEE value prominently', () => {
      render(
        <OEEGauge
          value={78.5}
          target={85.0}
          status="yellow"
        />
      )
      expect(screen.getByText('78.5')).toBeInTheDocument()
      expect(screen.getByText('%')).toBeInTheDocument()
    })

    it('should display "--" when value is null', () => {
      render(
        <OEEGauge
          value={null}
          target={85.0}
          status="unknown"
        />
      )
      // Multiple '--' elements may exist (gauge and variance)
      const dashElements = screen.getAllByText('--')
      expect(dashElements.length).toBeGreaterThanOrEqual(1)
    })

    it('should display "Plant OEE" label', () => {
      render(
        <OEEGauge
          value={78.5}
          target={85.0}
          status="yellow"
        />
      )
      expect(screen.getByText('Plant OEE')).toBeInTheDocument()
    })

    it('should display target value (AC #7)', () => {
      render(
        <OEEGauge
          value={78.5}
          target={85.0}
          status="yellow"
        />
      )
      expect(screen.getByText('Target')).toBeInTheDocument()
      expect(screen.getByText('85%')).toBeInTheDocument()
    })

    it('should display variance from target (AC #7)', () => {
      render(
        <OEEGauge
          value={78.5}
          target={85.0}
          status="yellow"
        />
      )
      expect(screen.getByText('Variance')).toBeInTheDocument()
      expect(screen.getByText('-6.5%')).toBeInTheDocument()
    })

    it('should display positive variance with + sign', () => {
      render(
        <OEEGauge
          value={90.0}
          target={85.0}
          status="green"
        />
      )
      expect(screen.getByText('+5.0%')).toBeInTheDocument()
    })

    it('should indicate Yesterday data when isLive=false (AC #6)', () => {
      render(
        <OEEGauge
          value={78.5}
          target={85.0}
          status="yellow"
          isLive={false}
        />
      )
      expect(screen.getByText("Yesterday's Analysis (T-1)")).toBeInTheDocument()
    })

    it('should indicate Live data when isLive=true (AC #6)', () => {
      render(
        <OEEGauge
          value={78.5}
          target={85.0}
          status="yellow"
          isLive={true}
        />
      )
      expect(screen.getByText('Live Pulse (T-15m)')).toBeInTheDocument()
    })

    it('should use retrospective mode styling for Yesterday data (AC #6)', () => {
      const { container } = render(
        <OEEGauge
          value={78.5}
          target={85.0}
          status="yellow"
          isLive={false}
        />
      )
      const card = container.firstChild
      expect(card?.className).toContain('retrospective')
    })

    it('should use live mode styling for Live data (AC #6)', () => {
      const { container } = render(
        <OEEGauge
          value={78.5}
          target={85.0}
          status="yellow"
          isLive={true}
        />
      )
      const card = container.firstChild
      expect(card?.className).toContain('live')
    })
  })
})

// ========================================
// AC #1: Three OEE Components Tests
// ========================================
describe('AC #1: OEE Displays Three Core Components', () => {
  describe('OEEBreakdown Component', () => {
    it('should display Availability component', () => {
      render(
        <OEEBreakdown
          availability={92.1}
          performance={88.3}
          quality={96.5}
        />
      )
      expect(screen.getByText('Availability')).toBeInTheDocument()
      expect(screen.getByText('92.1%')).toBeInTheDocument()
    })

    it('should display Performance component', () => {
      render(
        <OEEBreakdown
          availability={92.1}
          performance={88.3}
          quality={96.5}
        />
      )
      // Multiple elements may exist in responsive view
      const perfElements = screen.getAllByText('Performance')
      expect(perfElements.length).toBeGreaterThanOrEqual(1)
      const valueElements = screen.getAllByText('88.3%')
      expect(valueElements.length).toBeGreaterThanOrEqual(1)
    })

    it('should display Quality component', () => {
      render(
        <OEEBreakdown
          availability={92.1}
          performance={88.3}
          quality={96.5}
        />
      )
      // Multiple elements may exist in responsive view
      const qualityElements = screen.getAllByText('Quality')
      expect(qualityElements.length).toBeGreaterThanOrEqual(1)
      const valueElements = screen.getAllByText('96.5%')
      expect(valueElements.length).toBeGreaterThanOrEqual(1)
    })

    it('should display formula reference', () => {
      render(
        <OEEBreakdown
          availability={92.1}
          performance={88.3}
          quality={96.5}
        />
      )
      expect(screen.getByText(/OEE = Availability/)).toBeInTheDocument()
    })

    it('should display "--%" for null values', () => {
      render(
        <OEEBreakdown
          availability={null}
          performance={88.3}
          quality={null}
        />
      )
      expect(screen.getAllByText('--%')).toHaveLength(2)
    })

    it('should display component descriptions', () => {
      render(
        <OEEBreakdown
          availability={92.1}
          performance={88.3}
          quality={96.5}
        />
      )
      expect(screen.getByText('Run Time / Planned Production Time')).toBeInTheDocument()
      expect(screen.getByText('Actual Output / Target Output')).toBeInTheDocument()
      expect(screen.getByText('Good Units / Total Units')).toBeInTheDocument()
    })
  })
})

// ========================================
// AC #4: Individual Asset OEE Breakdown Tests
// ========================================
describe('AC #4: Individual Asset OEE Breakdown', () => {
  describe('AssetOEEList Component', () => {
    it('should render list of assets with OEE', () => {
      const assets = [mockAsset, mockAssetGreen, mockAssetRed]
      render(<AssetOEEList assets={assets} />)

      // Multiple elements due to card+table responsive rendering
      const grinder5 = screen.getAllByText('Grinder 5')
      const assembly1 = screen.getAllByText('Assembly Line 1')
      const press3 = screen.getAllByText('Press 3')
      expect(grinder5.length).toBeGreaterThanOrEqual(1)
      expect(assembly1.length).toBeGreaterThanOrEqual(1)
      expect(press3.length).toBeGreaterThanOrEqual(1)
    })

    it('should display OEE value for each asset', () => {
      render(<AssetOEEList assets={[mockAsset]} />)
      // Multiple elements due to card+table responsive rendering
      const oeeElements = screen.getAllByText('82.3%')
      expect(oeeElements.length).toBeGreaterThanOrEqual(1)
    })

    it('should display all three OEE components per asset', () => {
      render(<AssetOEEList assets={[mockAsset]} />)

      // Multiple elements due to card+table responsive rendering
      const availElements = screen.getAllByText('95.0%')
      const perfElements = screen.getAllByText('90.1%')
      const qualElements = screen.getAllByText('96.2%')
      expect(availElements.length).toBeGreaterThanOrEqual(1) // Availability
      expect(perfElements.length).toBeGreaterThanOrEqual(1) // Performance
      expect(qualElements.length).toBeGreaterThanOrEqual(1) // Quality
    })

    it('should display asset area', () => {
      render(<AssetOEEList assets={[mockAsset]} />)
      // Multiple elements due to card+table responsive rendering
      const areaElements = screen.getAllByText('Grinding')
      expect(areaElements.length).toBeGreaterThanOrEqual(1)
    })

    it('should display target and variance (AC #7)', () => {
      render(<AssetOEEList assets={[mockAsset]} />)
      // Multiple elements due to card+table responsive rendering
      const targetElements = screen.getAllByText('85%')
      const varianceElements = screen.getAllByText('-2.7%')
      expect(targetElements.length).toBeGreaterThanOrEqual(1)
      expect(varianceElements.length).toBeGreaterThanOrEqual(1) // 82.3 - 85 = -2.7
    })

    it('should display status badge', () => {
      render(<AssetOEEList assets={[mockAsset]} />)
      // Multiple elements due to card+table responsive rendering
      const badgeElements = screen.getAllByText('Attention')
      expect(badgeElements.length).toBeGreaterThanOrEqual(1)
    })

    it('should display empty state when no assets', () => {
      render(<AssetOEEList assets={[]} />)
      expect(screen.getByText('No asset OEE data available')).toBeInTheDocument()
    })

    it('should use appropriate mode styling (AC #6)', () => {
      const { container } = render(
        <AssetOEEList assets={[mockAsset]} isLive={true} />
      )
      const card = container.querySelector('[class*="live"]')
      expect(card).toBeInTheDocument()
    })
  })
})

// ========================================
// AC #9: Glanceability Tests
// ========================================
describe('AC #9: Industrial Clarity - Readable from 3 feet', () => {
  describe('OEEGauge Glanceability', () => {
    it('should use large font for main OEE value', () => {
      render(
        <OEEGauge
          value={78.5}
          target={85.0}
          status="yellow"
        />
      )
      const valueElement = screen.getByText('78.5')
      // Should use metric-display class which is text-5xl (60px)
      expect(valueElement.className).toContain('metric-display')
    })
  })

  describe('AssetOEEList Card Glanceability', () => {
    it('should use readable font sizes for asset OEE values', () => {
      render(<AssetOEEList assets={[mockAsset]} />)
      // Multiple elements may contain '82.3%' (card view + table view)
      // Find the one with large font in the card view
      const oeeValues = screen.getAllByText('82.3%')
      const hasLargeFont = oeeValues.some(el => el.className.includes('text-4xl'))
      expect(hasLargeFont).toBe(true)
    })
  })
})

// ========================================
// Mode Styling Tests (AC #6)
// ========================================
describe('AC #6: Visual Indicators for Data Mode', () => {
  describe('Retrospective Mode (Yesterday)', () => {
    it('OEEGauge uses cool/static styling', () => {
      const { container } = render(
        <OEEGauge value={78.5} target={85.0} status="yellow" isLive={false} />
      )
      expect(container.firstChild?.className).toContain('retrospective')
    })

    it('OEEBreakdown uses retrospective card', () => {
      const { container } = render(
        <OEEBreakdown
          availability={92.1}
          performance={88.3}
          quality={96.5}
          isLive={false}
        />
      )
      expect(container.firstChild?.className).toContain('retrospective')
    })
  })

  describe('Live Mode (T-15m)', () => {
    it('OEEGauge uses vibrant/pulsing styling', () => {
      const { container } = render(
        <OEEGauge value={78.5} target={85.0} status="yellow" isLive={true} />
      )
      expect(container.firstChild?.className).toContain('live')
    })

    it('OEEBreakdown uses live card', () => {
      const { container } = render(
        <OEEBreakdown
          availability={92.1}
          performance={88.3}
          quality={96.5}
          isLive={true}
        />
      )
      expect(container.firstChild?.className).toContain('live')
    })
  })
})

// ========================================
// Accessibility Tests
// ========================================
describe('Accessibility', () => {
  it('OEEStatusBadge should have title for description', () => {
    const { container } = render(<OEEStatusBadge status="green" />)
    const badge = container.querySelector('[title]')
    expect(badge).toBeInTheDocument()
    expect(badge?.getAttribute('title')).toContain('OEE >= 85%')
  })

  it('OEEStatusDot should have title for description', () => {
    const { container } = render(<OEEStatusDot status="yellow" />)
    const dot = container.querySelector('[title]')
    expect(dot).toBeInTheDocument()
    expect(dot?.getAttribute('title')).toContain('Attention')
  })
})

// ========================================
// Edge Cases
// ========================================
describe('Edge Cases', () => {
  it('OEEGauge handles 0% OEE', () => {
    render(<OEEGauge value={0} target={85.0} status="red" />)
    expect(screen.getByText('0.0')).toBeInTheDocument()
  })

  it('OEEGauge handles 100% OEE', () => {
    render(<OEEGauge value={100} target={85.0} status="green" />)
    expect(screen.getByText('100.0')).toBeInTheDocument()
    expect(screen.getByText('+15.0%')).toBeInTheDocument()
  })

  it('OEEBreakdown handles all null values', () => {
    render(
      <OEEBreakdown
        availability={null}
        performance={null}
        quality={null}
      />
    )
    expect(screen.getAllByText('--%')).toHaveLength(3)
  })

  it('AssetOEEList handles assets with null OEE', () => {
    const assetWithNullOEE: AssetOEEData = {
      ...mockAsset,
      oee: null,
      availability: null,
      performance: null,
      quality: null,
      status: 'unknown',
    }
    render(<AssetOEEList assets={[assetWithNullOEE]} />)
    // Multiple '--' elements rendered for card view and table view
    // Just verify at least one '--' is shown for null values
    const nullValueElements = screen.getAllByText('--%')
    expect(nullValueElements.length).toBeGreaterThanOrEqual(1)
  })
})
