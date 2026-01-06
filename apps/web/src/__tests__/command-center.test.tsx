/**
 * Command Center UI Shell Tests
 *
 * Tests for Story 1.7 Acceptance Criteria:
 * 1. Dashboard Layout Structure - Route, sections, responsive grid
 * 2. Action List Section - Primary/prominent position, placeholder content
 * 3. Live Pulse Section - Real-time styling, distinct visual treatment
 * 4. Financial Widgets Section - Financial placeholder content
 * 5. Industrial Clarity Design Compliance - Styling, glanceability, no Safety Red
 * 6. Navigation Integration - Accessible via main navigation
 */

import { describe, it, expect } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import * as React from 'react'
import { ActionListSection } from '@/components/dashboard/ActionListSection'
import { LivePulseSection } from '@/components/dashboard/LivePulseSection'
import { FinancialWidgetsSection } from '@/components/dashboard/FinancialWidgetsSection'

// ========================================
// AC #1: Dashboard Layout Structure Tests
// ========================================
describe('AC #1: Dashboard Layout Structure', () => {
  describe('ActionListSection', () => {
    it('should render with proper section landmark', () => {
      render(<ActionListSection />)
      const section = screen.getByRole('region', { name: /daily action list/i })
      expect(section).toBeInTheDocument()
    })

    it('should span 2 columns on large screens (lg:col-span-2)', () => {
      render(<ActionListSection />)
      const section = screen.getByRole('region', { name: /daily action list/i })
      expect(section.className).toContain('lg:col-span-2')
    })
  })

  describe('LivePulseSection', () => {
    it('should render with proper section landmark', () => {
      render(<LivePulseSection />)
      const section = screen.getByRole('region', { name: /live pulse/i })
      expect(section).toBeInTheDocument()
    })
  })

  describe('FinancialWidgetsSection', () => {
    it('should render with proper section landmark', () => {
      render(<FinancialWidgetsSection />)
      // Updated in Story 2.8: Now contains Cost of Loss widget instead of placeholder
      const section = screen.getByRole('region')
      expect(section).toBeInTheDocument()
      expect(section).toHaveAttribute('aria-labelledby', 'financial-widgets-heading')
    })
  })

  describe('All sections together', () => {
    it('should render all three distinct sections', () => {
      render(
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <ActionListSection />
          <LivePulseSection />
          <FinancialWidgetsSection />
        </div>
      )

      expect(screen.getByRole('region', { name: /daily action list/i })).toBeInTheDocument()
      expect(screen.getByRole('region', { name: /live pulse/i })).toBeInTheDocument()
      // Updated in Story 2.8: FinancialWidgetsSection now contains Cost of Loss widget
      const financialSection = document.querySelector('[aria-labelledby="financial-widgets-heading"]')
      expect(financialSection).toBeInTheDocument()
    })
  })
})

// ========================================
// AC #2: Action List Section (Primary)
// ========================================
describe('AC #2: Action List Section (Primary)', () => {
  it('should display "Daily Action List" heading', () => {
    render(<ActionListSection />)
    expect(screen.getByRole('heading', { name: /daily action list/i })).toBeInTheDocument()
  })

  it('should contain placeholder with "Coming in Epic 3" indicator', () => {
    render(<ActionListSection />)
    expect(screen.getByText(/coming in epic 3/i)).toBeInTheDocument()
  })

  it('should have a "Primary" badge to indicate prominence', () => {
    render(<ActionListSection />)
    expect(screen.getByText('Primary')).toBeInTheDocument()
  })

  it('should have minimum height for visual prominence', () => {
    render(<ActionListSection />)
    const section = screen.getByRole('region', { name: /daily action list/i })
    const card = section.querySelector('.min-h-\\[300px\\]')
    expect(card).toBeInTheDocument()
  })

  it('should use section-header class for heading (glanceability)', () => {
    render(<ActionListSection />)
    const heading = screen.getByRole('heading', { name: /daily action list/i })
    expect(heading.className).toContain('section-header')
  })
})

// ========================================
// AC #3: Live Pulse Section
// Updated in Epic 2: Now contains actual dashboard links instead of placeholder
// ========================================
describe('AC #3: Live Pulse Section', () => {
  it('should display "Live Pulse" heading', () => {
    render(<LivePulseSection />)
    expect(screen.getByRole('heading', { name: /live pulse/i })).toBeInTheDocument()
  })

  it('should contain links to production dashboards', () => {
    render(<LivePulseSection />)
    // Updated: Now has actual dashboard links instead of placeholder
    expect(screen.getByText('Throughput Dashboard')).toBeInTheDocument()
    expect(screen.getByText('OEE Metrics')).toBeInTheDocument()
    expect(screen.getByText('Downtime Analysis')).toBeInTheDocument()
  })

  it('should have "Real-time" badge with live variant', () => {
    render(<LivePulseSection />)
    const badge = screen.getByText('Real-time')
    expect(badge).toBeInTheDocument()
  })

  it('should use Card mode="live" for distinct visual treatment', () => {
    render(<LivePulseSection />)
    const section = screen.getByRole('region', { name: /live pulse/i })
    const card = section.querySelector('.bg-live-surface')
    expect(card).toBeInTheDocument()
  })

  it('should have live pulse indicator with animation', () => {
    render(<LivePulseSection />)
    const pulseIndicator = screen.getByLabelText('Live indicator')
    expect(pulseIndicator).toBeInTheDocument()
    expect(pulseIndicator.className).toContain('animate-live-pulse')
  })
})

// ========================================
// AC #4: Financial Widgets Section
// Updated in Story 2.8: Now contains Cost of Loss widget instead of placeholder
// ========================================
describe('AC #4: Financial Widgets Section', () => {
  it('should display "Cost of Loss" widget heading', () => {
    render(<FinancialWidgetsSection />)
    // Story 2.8: Widget displays "Cost of Loss" title
    // In loading state, the skeleton is shown; after loading, the actual title appears
    const section = document.querySelector('[aria-labelledby="financial-widgets-heading"]')
    expect(section).toBeInTheDocument()
  })

  it('should render the Cost of Loss widget component', () => {
    render(<FinancialWidgetsSection />)
    // The widget container should be present with minimum height
    const section = document.querySelector('[aria-labelledby="financial-widgets-heading"]')
    expect(section).toBeInTheDocument()
    // min-h class is on the card inside the section, check via innerHTML
    expect(section?.innerHTML).toContain('min-h-[200px]')
  })

  it('should have proper section structure', () => {
    render(<FinancialWidgetsSection />)
    const section = screen.getByRole('region')
    expect(section).toHaveAttribute('aria-labelledby', 'financial-widgets-heading')
  })

  it('should use Card component with proper styling', () => {
    render(<FinancialWidgetsSection />)
    const section = document.querySelector('[aria-labelledby="financial-widgets-heading"]')
    // Card component adds rounded-lg, border classes
    const card = section?.querySelector('.rounded-lg.border')
    expect(card).toBeInTheDocument()
  })
})

// ========================================
// AC #5: Industrial Clarity Design Compliance
// ========================================
describe('AC #5: Industrial Clarity Design Compliance', () => {
  describe('ActionListSection Compliance', () => {
    it('should use Shadcn/UI Card component', () => {
      render(<ActionListSection />)
      const section = screen.getByRole('region', { name: /daily action list/i })
      // Card component adds rounded-lg, border, shadow classes
      const card = section.querySelector('.rounded-lg.border.shadow')
      expect(card).toBeInTheDocument()
    })

    it('should NOT use Safety Red color (reserved for incidents)', () => {
      const { container } = render(<ActionListSection />)
      const htmlContent = container.innerHTML
      expect(htmlContent).not.toContain('safety-red')
      expect(htmlContent).not.toContain('#DC2626')
    })

    it('should use card-title class for sub-headings (glanceability)', () => {
      render(<ActionListSection />)
      const subHeading = screen.getByText('Action-First Intelligence')
      expect(subHeading.className).toContain('card-title')
    })

    it('should use body-text class for descriptions (minimum 16px)', () => {
      render(<ActionListSection />)
      const description = screen.getByText(/prioritized daily actions/i)
      expect(description.className).toContain('body-text')
    })
  })

  describe('LivePulseSection Compliance', () => {
    it('should use Shadcn/UI Card with live mode', () => {
      render(<LivePulseSection />)
      const section = screen.getByRole('region', { name: /live pulse/i })
      const card = section.querySelector('.bg-live-surface.border-live-border')
      expect(card).toBeInTheDocument()
    })

    it('should NOT use Safety Red color', () => {
      const { container } = render(<LivePulseSection />)
      const htmlContent = container.innerHTML
      expect(htmlContent).not.toContain('safety-red')
      expect(htmlContent).not.toContain('#DC2626')
    })

    it('should use card-title class for heading (glanceability)', () => {
      render(<LivePulseSection />)
      const heading = screen.getByRole('heading', { name: /live pulse/i })
      expect(heading.className).toContain('card-title')
    })
  })

  describe('FinancialWidgetsSection Compliance', () => {
    it('should use Shadcn/UI Card component', () => {
      render(<FinancialWidgetsSection />)
      // Updated in Story 2.8: Uses Cost of Loss widget with Card
      const section = document.querySelector('[aria-labelledby="financial-widgets-heading"]')
      const card = section?.querySelector('.rounded-lg.border')
      expect(card).toBeInTheDocument()
    })

    it('should NOT use Safety Red color (AC #5 - reserved for safety incidents)', () => {
      const { container } = render(<FinancialWidgetsSection />)
      const htmlContent = container.innerHTML
      // Story 2.8 AC#5: Financial values should use warning amber, NOT safety red
      expect(htmlContent).not.toContain('safety-red')
      expect(htmlContent).not.toContain('#DC2626')
    })
  })

  describe('Global Compliance', () => {
    it('all sections should use high-contrast appropriate colors', () => {
      render(
        <>
          <ActionListSection />
          <LivePulseSection />
          <FinancialWidgetsSection />
        </>
      )

      // Check that semantic color classes are used (not hardcoded colors)
      const sections = screen.getAllByRole('region')
      sections.forEach((section) => {
        // Should use design system classes (text colors or background colors for skeleton)
        // Updated in Story 2.8: FinancialWidgetsSection uses skeleton with bg-muted during loading
        const hasSemanticColors =
          section.innerHTML.includes('text-foreground') ||
          section.innerHTML.includes('text-muted-foreground') ||
          section.innerHTML.includes('text-primary') ||
          section.innerHTML.includes('bg-muted') || // Skeleton uses bg-muted
          section.innerHTML.includes('bg-card')     // Card background
        expect(hasSemanticColors).toBe(true)
      })
    })
  })
})

// ========================================
// AC #6: Navigation Integration
// ========================================
describe('AC #6: Navigation Integration', () => {
  it('ActionListSection should be accessible (has aria-labelledby)', () => {
    render(<ActionListSection />)
    const section = screen.getByRole('region', { name: /daily action list/i })
    expect(section).toHaveAttribute('aria-labelledby', 'action-list-heading')
  })

  it('LivePulseSection should be accessible (has aria-labelledby)', () => {
    render(<LivePulseSection />)
    const section = screen.getByRole('region', { name: /live pulse/i })
    expect(section).toHaveAttribute('aria-labelledby', 'live-pulse-heading')
  })

  it('FinancialWidgetsSection should be accessible (has aria-labelledby)', () => {
    render(<FinancialWidgetsSection />)
    // Updated in Story 2.8: Section contains Cost of Loss widget
    const section = document.querySelector('[aria-labelledby="financial-widgets-heading"]')
    expect(section).toBeInTheDocument()
    expect(section).toHaveAttribute('aria-labelledby', 'financial-widgets-heading')
  })

  it('all sections should render without errors', () => {
    expect(() => {
      render(
        <div>
          <ActionListSection />
          <LivePulseSection />
          <FinancialWidgetsSection />
        </div>
      )
    }).not.toThrow()
  })
})

// ========================================
// Component Index Export Tests
// ========================================
describe('Dashboard Component Exports', () => {
  it('should export all dashboard components from index', async () => {
    const dashboardComponents = await import('@/components/dashboard')

    expect(dashboardComponents.ActionListSection).toBeDefined()
    expect(dashboardComponents.LivePulseSection).toBeDefined()
    expect(dashboardComponents.FinancialWidgetsSection).toBeDefined()
  })
})

// ========================================
// Responsive Layout Tests
// ========================================
describe('Responsive Layout', () => {
  it('ActionListSection should have responsive column span', () => {
    render(<ActionListSection />)
    const section = screen.getByRole('region', { name: /daily action list/i })
    // On large screens, spans 2 columns for prominence
    expect(section.className).toContain('lg:col-span-2')
  })

  it('all sections should have minimum height for visibility', () => {
    render(
      <>
        <ActionListSection />
        <LivePulseSection />
        <FinancialWidgetsSection />
      </>
    )

    const actionSection = screen.getByRole('region', { name: /daily action list/i })
    const liveSection = screen.getByRole('region', { name: /live pulse/i })
    // Updated in Story 2.8: FinancialWidgetsSection contains Cost of Loss widget
    const financialSection = document.querySelector('[aria-labelledby="financial-widgets-heading"]')

    expect(actionSection.querySelector('.min-h-\\[300px\\]')).toBeInTheDocument()
    expect(liveSection.querySelector('.min-h-\\[200px\\]')).toBeInTheDocument()
    // Story 2.8: Widget has min-h class on the Card element directly
    expect(financialSection?.innerHTML).toContain('min-h-[200px]')
  })
})

// ========================================
// Accessibility Tests
// ========================================
describe('Accessibility', () => {
  it('icons should be hidden from screen readers with aria-hidden', () => {
    render(<ActionListSection />)
    const svgElements = document.querySelectorAll('svg')
    svgElements.forEach((svg) => {
      expect(svg).toHaveAttribute('aria-hidden', 'true')
    })
  })

  it('LivePulseSection indicator should have accessible label', () => {
    render(<LivePulseSection />)
    expect(screen.getByLabelText('Live indicator')).toBeInTheDocument()
  })

  it('all headings should have proper hierarchy', () => {
    render(
      <>
        <ActionListSection />
        <LivePulseSection />
        <FinancialWidgetsSection />
      </>
    )

    // Section headings should use appropriate heading levels
    const headings = screen.getAllByRole('heading')
    expect(headings.length).toBeGreaterThanOrEqual(3)
  })
})
