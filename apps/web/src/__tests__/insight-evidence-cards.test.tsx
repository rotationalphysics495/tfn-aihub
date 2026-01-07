/**
 * Insight + Evidence Cards Tests
 *
 * Tests for Story 3.4 Acceptance Criteria:
 * 1. Insight + Evidence Card Component
 * 2. Recommendation/Insight Display (Left Side)
 * 3. Evidence Display (Right Side)
 * 4. Visual Hierarchy and Priority Styling
 * 5. Data Source Integration
 * 6. Interactivity
 * 7. Performance and Accessibility
 *
 * @see Story 3.4 - Insight + Evidence Cards
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import * as React from 'react'

// Mock Next.js navigation
const mockPush = vi.fn()

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    refresh: vi.fn(),
    replace: vi.fn(),
  }),
  usePathname: () => '/morning-report',
}))

// Mock Supabase client
vi.mock('@/lib/supabase/client', () => ({
  createClient: () => ({
    auth: {
      getSession: vi.fn().mockResolvedValue({
        data: {
          session: {
            access_token: 'mock-token',
          },
        },
      }),
    },
  }),
}))

// Import components after mocks
import { PriorityBadge, getPriorityBorderColor, getPriorityAccentBg } from '@/components/action-engine/PriorityBadge'
import { InsightSection } from '@/components/action-engine/InsightSection'
import { EvidenceSection } from '@/components/action-engine/EvidenceSection'
import { InsightEvidenceCard, InsightEvidenceCardSkeleton } from '@/components/action-engine/InsightEvidenceCard'
import { ActionCardList } from '@/components/action-engine/ActionCardList'
import type { ActionItem, SafetyEvidence, OEEEvidence, FinancialEvidence } from '@/components/action-engine/types'

// ========================================
// Test Data
// ========================================

const mockSafetyEvidence: SafetyEvidence = {
  eventId: 'SE-001',
  detectedAt: '2026-01-05T14:30:00Z',
  reasonCode: 'Emergency Stop Triggered',
  severity: 'high',
  assetName: 'Grinder 5',
}

const mockOEEEvidence: OEEEvidence = {
  targetOEE: 85,
  actualOEE: 72.5,
  deviation: -12.5, // actualOEE - targetOEE = 72.5 - 85 = -12.5
  timeframe: 'Yesterday (T-1)',
}

const mockFinancialEvidence: FinancialEvidence = {
  downtimeCost: 5500,
  wasteCost: 3000,
  totalLoss: 8500,
  breakdown: [
    { category: 'Labor', amount: 2000 },
    { category: 'Materials', amount: 1000 },
  ],
}

const mockSafetyAction: ActionItem = {
  id: 'action-1',
  priority: 'SAFETY',
  priorityScore: 1500,
  recommendation: {
    text: 'Investigate emergency stop trigger on Grinder 5',
    summary: 'Safety event detected on Grinder 5',
  },
  asset: {
    id: 'asset-1',
    name: 'Grinder 5',
    area: 'Machine Shop',
  },
  evidence: {
    type: 'safety_event',
    data: mockSafetyEvidence,
    source: {
      table: 'safety_events',
      date: '2026-01-05',
      recordId: 'SE-001',
    },
  },
  financialImpact: 0,
  timestamp: '2026-01-06T06:30:00Z',
}

const mockOEEAction: ActionItem = {
  id: 'action-2',
  priority: 'OEE',
  priorityScore: 850,
  recommendation: {
    text: 'Review OEE performance on Line 3',
    summary: 'OEE below target by 12.5%',
  },
  asset: {
    id: 'asset-2',
    name: 'Line 3',
    area: 'Assembly',
  },
  evidence: {
    type: 'oee_deviation',
    data: mockOEEEvidence,
    source: {
      table: 'daily_summaries',
      date: '2026-01-05',
      recordId: 'DS-001',
    },
  },
  financialImpact: 3500,
  timestamp: '2026-01-06T06:30:00Z',
}

const mockFinancialAction: ActionItem = {
  id: 'action-3',
  priority: 'FINANCIAL',
  priorityScore: 950,
  recommendation: {
    text: 'Address financial loss on Packaging Unit',
    summary: 'Significant downtime cost identified',
  },
  asset: {
    id: 'asset-3',
    name: 'Packaging Unit',
    area: 'Packaging',
  },
  evidence: {
    type: 'financial_loss',
    data: mockFinancialEvidence,
    source: {
      table: 'cost_centers',
      date: '2026-01-05',
      recordId: 'CC-001',
    },
  },
  financialImpact: 8500,
  timestamp: '2026-01-06T06:30:00Z',
}

// ========================================
// AC #4: PriorityBadge Tests
// ========================================
describe('AC #4: PriorityBadge Component', () => {
  it('should render SAFETY badge with correct styling (Safety Red #DC2626)', () => {
    const { container } = render(<PriorityBadge priority="SAFETY" />)

    expect(screen.getByText('SAFETY')).toBeInTheDocument()
    const badge = container.querySelector('.bg-\\[\\#DC2626\\]')
    expect(badge).toBeInTheDocument()
  })

  it('should render FINANCIAL badge with correct styling (Amber #F59E0B)', () => {
    const { container } = render(<PriorityBadge priority="FINANCIAL" />)

    expect(screen.getByText('FINANCIAL')).toBeInTheDocument()
    const badge = container.querySelector('.bg-\\[\\#F59E0B\\]')
    expect(badge).toBeInTheDocument()
  })

  it('should render OEE badge with correct styling (Yellow #EAB308)', () => {
    const { container } = render(<PriorityBadge priority="OEE" />)

    expect(screen.getByText('OEE')).toBeInTheDocument()
    const badge = container.querySelector('.bg-\\[\\#EAB308\\]')
    expect(badge).toBeInTheDocument()
  })

  it('should have minimum 16px text for glanceability', () => {
    const { container } = render(<PriorityBadge priority="SAFETY" />)

    // text-base = 16px minimum
    const badge = container.querySelector('.text-base')
    expect(badge).toBeInTheDocument()
  })

  it('should have proper aria-label for accessibility', () => {
    render(<PriorityBadge priority="SAFETY" />)

    expect(screen.getByRole('status', { name: /priority: safety/i })).toBeInTheDocument()
  })
})

describe('AC #4: getPriorityBorderColor utility', () => {
  it('should return correct border color for SAFETY', () => {
    expect(getPriorityBorderColor('SAFETY')).toContain('#DC2626')
  })

  it('should return correct border color for FINANCIAL', () => {
    expect(getPriorityBorderColor('FINANCIAL')).toContain('#F59E0B')
  })

  it('should return correct border color for OEE', () => {
    expect(getPriorityBorderColor('OEE')).toContain('#EAB308')
  })
})

// ========================================
// AC #2: InsightSection Tests
// ========================================
describe('AC #2: InsightSection Component', () => {
  beforeEach(() => {
    mockPush.mockClear()
  })

  it('should display recommendation text prominently', () => {
    render(
      <InsightSection
        priority="SAFETY"
        recommendation={mockSafetyAction.recommendation}
        asset={mockSafetyAction.asset}
        financialImpact={0}
        timestamp={mockSafetyAction.timestamp}
      />
    )

    expect(screen.getByText('Investigate emergency stop trigger on Grinder 5')).toBeInTheDocument()
  })

  it('should display priority badge', () => {
    render(
      <InsightSection
        priority="SAFETY"
        recommendation={mockSafetyAction.recommendation}
        asset={mockSafetyAction.asset}
        financialImpact={0}
        timestamp={mockSafetyAction.timestamp}
      />
    )

    expect(screen.getByText('SAFETY')).toBeInTheDocument()
  })

  it('should display financial impact when applicable', () => {
    render(
      <InsightSection
        priority="FINANCIAL"
        recommendation={mockFinancialAction.recommendation}
        asset={mockFinancialAction.asset}
        financialImpact={8500}
        timestamp={mockFinancialAction.timestamp}
      />
    )

    // $8500 rounds to $9K with our formatting (Math.round(8500/1000) = 9)
    // Using aria-label to verify the combined financial impact display
    expect(screen.getByLabelText(/financial impact: \$9K/i)).toBeInTheDocument()
  })

  it('should display asset name', () => {
    render(
      <InsightSection
        priority="SAFETY"
        recommendation={mockSafetyAction.recommendation}
        asset={mockSafetyAction.asset}
        financialImpact={0}
        timestamp={mockSafetyAction.timestamp}
      />
    )

    expect(screen.getByText('Grinder 5')).toBeInTheDocument()
  })

  it('should display timestamp', () => {
    render(
      <InsightSection
        priority="SAFETY"
        recommendation={mockSafetyAction.recommendation}
        asset={mockSafetyAction.asset}
        financialImpact={0}
        timestamp={mockSafetyAction.timestamp}
      />
    )

    // Should display formatted time
    expect(screen.getByText(/Generated at/)).toBeInTheDocument()
  })

  it('should navigate to asset detail view when asset name is clicked (AC #6)', () => {
    render(
      <InsightSection
        priority="SAFETY"
        recommendation={mockSafetyAction.recommendation}
        asset={mockSafetyAction.asset}
        financialImpact={0}
        timestamp={mockSafetyAction.timestamp}
      />
    )

    const assetButton = screen.getByRole('button', { name: /view asset details/i })
    fireEvent.click(assetButton)

    expect(mockPush).toHaveBeenCalledWith('/assets/asset-1')
  })
})

// ========================================
// AC #3: EvidenceSection Tests
// ========================================
describe('AC #3: EvidenceSection Component', () => {
  it('should display safety evidence details', () => {
    render(
      <EvidenceSection
        evidence={{
          type: 'safety_event',
          data: mockSafetyEvidence,
          source: { table: 'safety_events', date: '2026-01-05', recordId: 'SE-001' },
        }}
        defaultExpanded={true}
      />
    )

    expect(screen.getByText('Safety Event Details')).toBeInTheDocument()
    expect(screen.getByText('Emergency Stop Triggered')).toBeInTheDocument()
    expect(screen.getByText('Grinder 5')).toBeInTheDocument()
  })

  it('should display OEE evidence with target vs actual comparison', () => {
    render(
      <EvidenceSection
        evidence={{
          type: 'oee_deviation',
          data: mockOEEEvidence,
          source: { table: 'daily_summaries', date: '2026-01-05', recordId: 'DS-001' },
        }}
        defaultExpanded={true}
      />
    )

    expect(screen.getByText('OEE Performance')).toBeInTheDocument()
    expect(screen.getByText('85%')).toBeInTheDocument() // Target
    expect(screen.getByText('72.5%')).toBeInTheDocument() // Actual
    expect(screen.getByText('-12.5%')).toBeInTheDocument() // Deviation
  })

  it('should display financial evidence with cost breakdown', () => {
    render(
      <EvidenceSection
        evidence={{
          type: 'financial_loss',
          data: mockFinancialEvidence,
          source: { table: 'cost_centers', date: '2026-01-05', recordId: 'CC-001' },
        }}
        defaultExpanded={true}
      />
    )

    expect(screen.getByText('Financial Impact')).toBeInTheDocument()
    // Verify cost breakdown is displayed (values formatted as $X.YK)
    expect(screen.getByText('Downtime Cost:')).toBeInTheDocument()
    expect(screen.getByText('Waste Cost:')).toBeInTheDocument()
    expect(screen.getByText('Total Loss:')).toBeInTheDocument()
    // Check that total loss amount is displayed
    expect(screen.getByText(/\$8\.5K/)).toBeInTheDocument()
  })

  it('should display source citation for NFR1 compliance (AC #5)', () => {
    render(
      <EvidenceSection
        evidence={{
          type: 'safety_event',
          data: mockSafetyEvidence,
          source: { table: 'safety_events', date: '2026-01-05', recordId: 'SE-001' },
        }}
        defaultExpanded={true}
      />
    )

    expect(screen.getByText(/Source: safety_events/)).toBeInTheDocument()
    expect(screen.getByText(/2026-01-05/)).toBeInTheDocument()
    expect(screen.getByText(/Record ID: SE-001/)).toBeInTheDocument()
  })

  it('should have expand/collapse functionality (AC #6)', () => {
    render(
      <EvidenceSection
        evidence={{
          type: 'safety_event',
          data: mockSafetyEvidence,
          source: { table: 'safety_events', date: '2026-01-05', recordId: 'SE-001' },
        }}
        defaultExpanded={false}
      />
    )

    const expandButton = screen.getByRole('button', { name: /supporting evidence/i })
    expect(expandButton).toHaveAttribute('aria-expanded', 'false')

    fireEvent.click(expandButton)
    expect(expandButton).toHaveAttribute('aria-expanded', 'true')
  })

  it('should include View Details link for drill-down', () => {
    render(
      <EvidenceSection
        evidence={{
          type: 'safety_event',
          data: mockSafetyEvidence,
          source: { table: 'safety_events', date: '2026-01-05', recordId: 'SE-001' },
        }}
        defaultExpanded={true}
      />
    )

    expect(screen.getByRole('link', { name: /view details/i })).toBeInTheDocument()
  })
})

// ========================================
// AC #1: InsightEvidenceCard Tests
// ========================================
describe('AC #1: InsightEvidenceCard Component', () => {
  it('should render two-column layout (insight left, evidence right)', () => {
    const { container } = render(<InsightEvidenceCard item={mockSafetyAction} />)

    // Should have grid with 2 columns on md+
    const grid = container.querySelector('.grid-cols-1.md\\:grid-cols-2')
    expect(grid).toBeInTheDocument()
  })

  it('should apply 4px left border with priority color (AC #4)', () => {
    const { container } = render(<InsightEvidenceCard item={mockSafetyAction} />)

    const card = container.querySelector('.border-l-4')
    expect(card).toBeInTheDocument()
  })

  it('should apply Safety Red border for SAFETY priority', () => {
    const { container } = render(<InsightEvidenceCard item={mockSafetyAction} />)

    const card = container.querySelector('.border-l-\\[\\#DC2626\\]')
    expect(card).toBeInTheDocument()
  })

  it('should apply Amber border for FINANCIAL priority', () => {
    const { container } = render(<InsightEvidenceCard item={mockFinancialAction} />)

    const card = container.querySelector('.border-l-\\[\\#F59E0B\\]')
    expect(card).toBeInTheDocument()
  })

  it('should apply Yellow border for OEE priority', () => {
    const { container } = render(<InsightEvidenceCard item={mockOEEAction} />)

    const card = container.querySelector('.border-l-\\[\\#EAB308\\]')
    expect(card).toBeInTheDocument()
  })

  it('should have proper ARIA role and label (AC #7)', () => {
    render(<InsightEvidenceCard item={mockSafetyAction} />)

    expect(screen.getByRole('article', { name: /safety priority action/i })).toBeInTheDocument()
  })

  it('should use retrospective mode styling', () => {
    const { container } = render(<InsightEvidenceCard item={mockSafetyAction} />)

    // Card should have retrospective mode styling
    const card = container.querySelector('[class*="retrospective"]')
    expect(card).toBeInTheDocument()
  })
})

describe('InsightEvidenceCardSkeleton', () => {
  it('should render loading skeleton', () => {
    const { container } = render(<InsightEvidenceCardSkeleton />)

    // Should have animate-pulse for loading state
    const skeleton = container.querySelector('.animate-pulse')
    expect(skeleton).toBeInTheDocument()
  })

  it('should render immediately (AC #7 - Performance)', () => {
    const { container } = render(<InsightEvidenceCardSkeleton />)

    // Skeleton should be in DOM immediately
    expect(container.querySelector('.grid')).toBeInTheDocument()
  })
})

// ========================================
// AC #4, #5: ActionCardList Tests
// ========================================
describe('AC #4, #5: ActionCardList Component', () => {
  it('should sort cards by priority: Safety > Financial > OEE (AC #4)', () => {
    const items = [mockOEEAction, mockSafetyAction, mockFinancialAction]
    render(<ActionCardList items={items} />)

    const cards = screen.getAllByRole('article')

    // First card should be Safety
    expect(cards[0]).toHaveAttribute('aria-label', expect.stringContaining('SAFETY'))
    // Second should be Financial (higher score than OEE)
    expect(cards[1]).toHaveAttribute('aria-label', expect.stringContaining('FINANCIAL'))
    // Third should be OEE
    expect(cards[2]).toHaveAttribute('aria-label', expect.stringContaining('OEE'))
  })

  it('should display loading skeleton when loading', () => {
    const { container } = render(<ActionCardList items={[]} isLoading={true} />)

    expect(screen.getByRole('status', { name: /loading action items/i })).toBeInTheDocument()
  })

  it('should display error state with retry option', () => {
    const mockRetry = vi.fn()
    render(
      <ActionCardList
        items={[]}
        error="Network error occurred"
        onRefetch={mockRetry}
      />
    )

    expect(screen.getByText('Unable to Load Action Items')).toBeInTheDocument()
    expect(screen.getByText('Network error occurred')).toBeInTheDocument()

    const retryButton = screen.getByRole('button', { name: /try again/i })
    fireEvent.click(retryButton)
    expect(mockRetry).toHaveBeenCalled()
  })

  it('should display empty state when no action items', () => {
    render(<ActionCardList items={[]} />)

    expect(screen.getByText('All Systems Operating Normally')).toBeInTheDocument()
    expect(screen.getByText(/no immediate actions required/i)).toBeInTheDocument()
  })

  it('should have accessible list structure', () => {
    render(<ActionCardList items={[mockSafetyAction]} />)

    expect(screen.getByRole('list', { name: /action items/i })).toBeInTheDocument()
    expect(screen.getByRole('listitem')).toBeInTheDocument()
  })
})

// ========================================
// AC #7: Accessibility Tests
// ========================================
describe('AC #7: Accessibility', () => {
  it('should have WCAG compliant focus states', () => {
    const { container } = render(<InsightEvidenceCard item={mockSafetyAction} />)

    // Card should have focus-within styling
    const card = container.querySelector('[class*="focus-within"]')
    expect(card).toBeInTheDocument()
  })

  it('should be keyboard navigable', () => {
    render(
      <InsightSection
        priority="SAFETY"
        recommendation={mockSafetyAction.recommendation}
        asset={mockSafetyAction.asset}
        financialImpact={0}
        timestamp={mockSafetyAction.timestamp}
      />
    )

    const assetButton = screen.getByRole('button', { name: /view asset details/i })

    // Tab to button and press Enter
    assetButton.focus()
    expect(document.activeElement).toBe(assetButton)
  })

  it('evidence section should be keyboard accessible', () => {
    render(
      <EvidenceSection
        evidence={{
          type: 'safety_event',
          data: mockSafetyEvidence,
          source: { table: 'safety_events', date: '2026-01-05', recordId: 'SE-001' },
        }}
        defaultExpanded={false}
      />
    )

    const expandButton = screen.getByRole('button', { name: /supporting evidence/i })

    // Should be focusable and have proper ARIA
    expandButton.focus()
    expect(document.activeElement).toBe(expandButton)
    expect(expandButton).toHaveAttribute('aria-expanded', 'false')
    expect(expandButton).toHaveAttribute('aria-controls', 'evidence-content')
  })
})

// ========================================
// AC #8: Industrial Clarity Compliance Tests
// ========================================
describe('AC #8: Industrial Clarity Visual Compliance', () => {
  it('should use Safety Red ONLY for safety priority items', () => {
    const { container: safetyContainer } = render(
      <InsightEvidenceCard item={mockSafetyAction} />
    )
    const { container: oeeContainer } = render(
      <InsightEvidenceCard item={mockOEEAction} />
    )
    const { container: financialContainer } = render(
      <InsightEvidenceCard item={mockFinancialAction} />
    )

    // Safety card should have Safety Red border
    expect(safetyContainer.querySelector('.border-l-\\[\\#DC2626\\]')).toBeInTheDocument()

    // OEE card should NOT have Safety Red
    expect(oeeContainer.querySelector('.border-l-\\[\\#DC2626\\]')).not.toBeInTheDocument()

    // Financial card should NOT have Safety Red
    expect(financialContainer.querySelector('.border-l-\\[\\#DC2626\\]')).not.toBeInTheDocument()
  })

  it('should have large typography for recommendations (text-xl or text-2xl)', () => {
    const { container } = render(
      <InsightSection
        priority="SAFETY"
        recommendation={mockSafetyAction.recommendation}
        asset={mockSafetyAction.asset}
        financialImpact={0}
        timestamp={mockSafetyAction.timestamp}
      />
    )

    // Should have text-xl or text-2xl for title
    const title = container.querySelector('.text-xl, .text-2xl')
    expect(title).toBeInTheDocument()
  })

  it('should use retrospective mode for cards', () => {
    const { container } = render(<InsightEvidenceCard item={mockSafetyAction} />)

    // Should use retrospective mode
    const card = container.querySelector('[class*="retrospective"]')
    expect(card).toBeInTheDocument()
  })
})

// ========================================
// Performance Tests
// ========================================
describe('Performance Requirements', () => {
  it('should render skeleton immediately (no flash of content)', () => {
    const { container } = render(<InsightEvidenceCardSkeleton />)

    // Skeleton should be in DOM immediately
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument()
  })

  it('should render list of cards efficiently', () => {
    const items = Array(10).fill(null).map((_, i) => ({
      ...mockSafetyAction,
      id: `action-${i}`,
    }))

    const { container } = render(<ActionCardList items={items} />)

    // All cards should be rendered
    expect(container.querySelectorAll('[role="listitem"]')).toHaveLength(10)
  })
})
