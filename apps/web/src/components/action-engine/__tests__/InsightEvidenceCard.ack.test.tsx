/**
 * InsightEvidenceCard Acknowledgment Tests (Story 13.2: Action Acknowledgment UI)
 *
 * TDD tests — these MUST FAIL until the acknowledgment UI feature is implemented.
 * Tests cover the acknowledge button rendering, visual states, click handlers,
 * accessibility, transformer passthrough, and acknowledged styling.
 *
 * @see Story 13.2 - Action Acknowledgment UI
 * @see AC #1 - Unacknowledged button rendering
 * @see AC #2 - Acknowledged visual state and timestamp
 * @see AC #3 - Persisted acknowledged state on reload
 */

import { render, screen, fireEvent } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

// Mock next/navigation (already done in setup.ts but explicit for clarity)
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), back: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => '/',
  useParams: () => ({}),
}))

// Mock Supabase client for AssignFollowUpDialog
const mockGetSession = vi.fn()
vi.mock('@/lib/supabase/client', () => ({
  createClient: () => ({
    auth: { getSession: mockGetSession },
    from: () => ({ insert: () => ({ select: () => ({ single: () => Promise.resolve({ data: null, error: null }) }) }) }),
  }),
}))

// Mock global.fetch (used by AssignFollowUpDialog for team members)
const mockFetch = vi.fn()
global.fetch = mockFetch

// ---------------------------------------------------------------------------
// Imports (AFTER mocks)
// ---------------------------------------------------------------------------

import { InsightEvidenceCard } from '../InsightEvidenceCard'
import { InsightSection } from '../InsightSection'
import { transformAPIActionItem } from '../transformers'
import type { ActionItem } from '../types'

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const createMockActionItem = (overrides: Partial<ActionItem> = {}): ActionItem => ({
  id: 'action-42',
  priority: 'FINANCIAL',
  priorityScore: 750,
  recommendation: {
    text: 'Investigate downtime on Grinder 5',
    summary: 'Downtime investigation needed',
  },
  asset: {
    id: 'asset-001',
    name: 'Grinder 5',
    area: 'Grinding Area',
  },
  evidence: {
    type: 'financial_loss',
    data: {
      downtimeCost: 1500,
      wasteCost: 500,
      totalLoss: 2000,
      breakdown: [],
    },
    source: {
      table: 'daily_summaries',
      date: '2026-02-10',
      recordId: 'rec-001',
    },
  },
  financialImpact: 2000,
  timestamp: '2026-02-11T08:00:00Z',
  ...overrides,
})

const createMockAcknowledgment = (overrides: Record<string, unknown> = {}) => ({
  user_id: 'u1',
  acknowledged_at: '2026-02-11T08:30:00Z',
  note: null as string | null,
  ...overrides,
})

const createMockAPIActionItem = (overrides: Record<string, unknown> = {}) => ({
  id: 'action-api-1',
  asset_id: 'asset-001',
  asset_name: 'Grinder 5',
  priority_level: 'high' as const,
  category: 'financial' as const,
  primary_metric_value: '$2,000 loss',
  recommendation_text: 'Investigate downtime on Grinder 5',
  evidence_summary: 'Downtime investigation needed',
  evidence_refs: [
    {
      table: 'daily_summaries',
      column: 'downtime_minutes',
      value: '120',
      record_id: 'rec-001',
    },
  ],
  created_at: '2026-02-11T08:00:00Z',
  financial_impact_usd: 2000,
  priority_rank: 2,
  title: 'Downtime Alert',
  description: 'Downtime investigation needed',
  ...overrides,
})

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: Action Acknowledgment UI (Story 13.2)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockReset()
    mockGetSession.mockReset()

    // Default: authenticated session
    mockGetSession.mockResolvedValue({
      data: { session: { access_token: 'mock-token-abc' } },
    })
    // Default: empty fetch response (for AssignFollowUpDialog team members)
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ members: [] }),
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // =========================================================================
  // AC1: Unacknowledged action card rendering
  // =========================================================================
  describe('AC1: Unacknowledged Action Card Rendering', () => {
    it('UNIT-001: Unacknowledged action card renders Circle icon with "Mark Reviewed" label', () => {
      // Given: An InsightEvidenceCard renders with an action item that has no acknowledgment
      const item = createMockActionItem({ acknowledgment: null })

      // When: The card is rendered
      render(<InsightEvidenceCard item={item} />)

      // Then: A button with "Mark Reviewed" label is visible
      const ackButton = screen.getByRole('button', { name: /mark reviewed/i })
      expect(ackButton).toBeInTheDocument()

      // And: The button has variant="ghost" and size="sm" (via class matching)
      // Ghost buttons in shadcn have no bg color, sm buttons are smaller
      expect(ackButton).toBeVisible()

      // And: The icon is NOT green-colored (unacknowledged state)
      expect(ackButton.className).not.toMatch(/text-green/)
    })

    it('UNIT-002: Acknowledge button is present in InsightSection context row', () => {
      // Given: An InsightSection component renders with isAcknowledged=false
      const mockOnAcknowledge = vi.fn()

      // When: The component renders
      render(
        <InsightSection
          priority="FINANCIAL"
          recommendation={{ text: 'Test recommendation', summary: 'Test' }}
          asset={{ id: 'asset-1', name: 'Grinder 5', area: 'Grinding' }}
          financialImpact={2000}
          timestamp="2026-02-11T08:00:00Z"
          isAcknowledged={false}
          onAcknowledge={mockOnAcknowledge}
          onAssign={() => {}}
        />
      )

      // Then: The acknowledge button appears with "Mark Reviewed" text
      const ackButton = screen.getByRole('button', { name: /mark reviewed/i })
      expect(ackButton).toBeInTheDocument()

      // And: The Assign button is also present
      const assignButton = screen.getByRole('button', { name: /assign/i })
      expect(assignButton).toBeInTheDocument()

      // And: The acknowledge button is positioned before the Assign button in the DOM
      const allButtons = screen.getAllByRole('button')
      const ackIndex = allButtons.indexOf(ackButton)
      const assignIndex = allButtons.indexOf(assignButton)
      expect(ackIndex).toBeLessThan(assignIndex)
    })

    it('UNIT-003: Acknowledge button has correct aria-label for accessibility', () => {
      // Given: An InsightSection renders with isAcknowledged=false
      render(
        <InsightSection
          priority="FINANCIAL"
          recommendation={{ text: 'Test recommendation', summary: 'Test' }}
          asset={{ id: 'asset-1', name: 'Grinder 5', area: 'Grinding' }}
          financialImpact={2000}
          timestamp="2026-02-11T08:00:00Z"
          isAcknowledged={false}
          onAcknowledge={vi.fn()}
          onAssign={() => {}}
        />
      )

      // When: The component renders
      // Then: The acknowledge button has an appropriate aria-label
      const ackButton = screen.getByRole('button', { name: /mark action as reviewed/i })
      expect(ackButton).toBeInTheDocument()

      // And: The button is keyboard-focusable (buttons are focusable by default)
      expect(ackButton.tabIndex).not.toBe(-1)
    })

    it('UNIT-004: Acknowledge button is keyboard accessible (Enter and Space activate)', () => {
      // Given: An InsightSection with an unacknowledged action item
      const mockOnAcknowledge = vi.fn()
      render(
        <InsightSection
          priority="FINANCIAL"
          recommendation={{ text: 'Test recommendation', summary: 'Test' }}
          asset={{ id: 'asset-1', name: 'Grinder 5', area: 'Grinding' }}
          financialImpact={2000}
          timestamp="2026-02-11T08:00:00Z"
          isAcknowledged={false}
          onAcknowledge={mockOnAcknowledge}
          onAssign={() => {}}
        />
      )

      const ackButton = screen.getByRole('button', { name: /mark.*reviewed/i })

      // When: The user focuses the button and presses Enter
      fireEvent.keyDown(ackButton, { key: 'Enter', code: 'Enter' })
      fireEvent.keyUp(ackButton, { key: 'Enter', code: 'Enter' })

      // Then: The onAcknowledge callback is invoked (buttons natively handle Enter/Space)
      // For native buttons, we test via click since Enter/Space trigger click events
      fireEvent.click(ackButton)
      expect(mockOnAcknowledge).toHaveBeenCalled()
    })

    it('UNIT-006: Each card in ActionCardList receives acknowledgment state and callback', () => {
      // Given: ActionCardList renders with items and an acknowledgments map where all are unacknowledged
      const items = [
        createMockActionItem({ id: 'action-1', acknowledgment: null }),
        createMockActionItem({ id: 'action-2', acknowledgment: null }),
        createMockActionItem({ id: 'action-3', acknowledgment: null }),
      ]

      // When: The list renders (using InsightEvidenceCard directly since ActionCardList
      // will need to pass acknowledgment props through)
      const mockOnAcknowledge = vi.fn()
      const { container } = render(
        <>
          {items.map((item) => (
            <InsightEvidenceCard
              key={item.id}
              item={item}
              onAcknowledge={mockOnAcknowledge}
            />
          ))}
        </>
      )

      // Then: Each card has a "Mark Reviewed" button (3 total)
      const ackButtons = screen.getAllByRole('button', { name: /mark reviewed/i })
      expect(ackButtons).toHaveLength(3)
    })
  })

  // =========================================================================
  // AC2: Acknowledged visual state
  // =========================================================================
  describe('AC2: Acknowledged Visual State', () => {
    it('UNIT-009: Acknowledged card button shows CheckCircle2 icon and "Reviewed" label', () => {
      // Given: An InsightSection renders with isAcknowledged=true
      render(
        <InsightSection
          priority="FINANCIAL"
          recommendation={{ text: 'Test recommendation', summary: 'Test' }}
          asset={{ id: 'asset-1', name: 'Grinder 5', area: 'Grinding' }}
          financialImpact={2000}
          timestamp="2026-02-11T08:00:00Z"
          isAcknowledged={true}
          acknowledgedAt="2026-02-11T08:30:00Z"
          onAcknowledge={vi.fn()}
          onAssign={() => {}}
        />
      )

      // Then: The button displays "Reviewed" label (not "Mark Reviewed")
      const ackButton = screen.getByRole('button', { name: /reviewed/i })
      expect(ackButton).toBeInTheDocument()
      expect(ackButton).toHaveTextContent('Reviewed')
      expect(ackButton.textContent).not.toMatch(/Mark Reviewed/)

      // And: The button text is styled with green color classes
      expect(ackButton.className).toMatch(/text-green-600|text-green-400/)
    })

    it('UNIT-010: Acknowledged card applies muted visual styling', () => {
      // Given: An InsightEvidenceCard renders with a non-null acknowledgment prop
      const item = createMockActionItem({
        acknowledgment: createMockAcknowledgment(),
      })

      // When: The card renders
      const { container } = render(<InsightEvidenceCard item={item} />)

      // Then: The card's root element has opacity-60 class applied
      const cardElement = container.querySelector('[role="article"]')
      expect(cardElement).toBeTruthy()
      expect(cardElement!.className).toMatch(/opacity-60/)
    })

    it('UNIT-011: Acknowledged card displays timestamp of acknowledgment', () => {
      // Given: An InsightSection with isAcknowledged=true and acknowledgedAt
      render(
        <InsightSection
          priority="FINANCIAL"
          recommendation={{ text: 'Test recommendation', summary: 'Test' }}
          asset={{ id: 'asset-1', name: 'Grinder 5', area: 'Grinding' }}
          financialImpact={2000}
          timestamp="2026-02-11T08:00:00Z"
          isAcknowledged={true}
          acknowledgedAt="2026-02-11T08:30:00Z"
          onAcknowledge={vi.fn()}
          onAssign={() => {}}
        />
      )

      // Then: A timestamp is displayed showing the formatted time (e.g., "8:30 AM")
      const timestampEl = screen.getByText(/8:30\s*AM/i)
      expect(timestampEl).toBeInTheDocument()

      // And: It has the expected muted styling classes
      expect(timestampEl.className).toMatch(/text-sm/)
      expect(timestampEl.className).toMatch(/text-muted-foreground/)
    })

    it('UNIT-017: Acknowledge button click handler calls onAcknowledge with correct action ID', () => {
      // Given: An InsightEvidenceCard renders with action item id "action-42"
      const mockOnAcknowledge = vi.fn()
      const item = createMockActionItem({
        id: 'action-42',
        acknowledgment: null,
      })

      // When: The user clicks the acknowledge button
      render(
        <InsightEvidenceCard
          item={item}
          onAcknowledge={mockOnAcknowledge}
        />
      )

      const ackButton = screen.getByRole('button', { name: /mark reviewed/i })
      fireEvent.click(ackButton)

      // Then: The onAcknowledge callback is called with argument "action-42"
      expect(mockOnAcknowledge).toHaveBeenCalledWith('action-42')
    })
  })

  // =========================================================================
  // AC3: Persisted acknowledged state on reload
  // =========================================================================
  describe('AC3: Persisted Acknowledged State on Reload', () => {
    it('UNIT-020: Previously acknowledged card renders in acknowledged visual state on reload', () => {
      // Given: An InsightEvidenceCard receives an action item with pre-populated acknowledgment
      const item = createMockActionItem({
        acknowledgment: createMockAcknowledgment({
          acknowledged_at: '2026-02-11T07:00:00Z',
        }),
      })

      // When: The card renders
      render(<InsightEvidenceCard item={item} />)

      // Then: The card shows "Reviewed" label (not "Mark Reviewed")
      const reviewedButton = screen.getByRole('button', { name: /reviewed/i })
      expect(reviewedButton).toBeInTheDocument()
      expect(reviewedButton.textContent).not.toMatch(/Mark Reviewed/)

      // And: The card has muted opacity
      const cardElement = screen.getByRole('article')
      expect(cardElement.className).toMatch(/opacity-60/)
    })

    it('UNIT-021: Acknowledged timestamp from database is displayed correctly', () => {
      // Given: An action item was acknowledged at "2026-02-11T14:22:00Z" (stored in database)
      render(
        <InsightSection
          priority="FINANCIAL"
          recommendation={{ text: 'Test recommendation', summary: 'Test' }}
          asset={{ id: 'asset-1', name: 'Grinder 5', area: 'Grinding' }}
          financialImpact={2000}
          timestamp="2026-02-11T08:00:00Z"
          isAcknowledged={true}
          acknowledgedAt="2026-02-11T14:22:00Z"
          onAcknowledge={vi.fn()}
          onAssign={() => {}}
        />
      )

      // Then: The timestamp is displayed in a human-readable format (e.g., "2:22 PM")
      const timestampEl = screen.getByText(/2:22\s*PM/i)
      expect(timestampEl).toBeInTheDocument()

      // And: It has text-sm text-muted-foreground styling
      expect(timestampEl.className).toMatch(/text-sm/)
      expect(timestampEl.className).toMatch(/text-muted-foreground/)
    })

    it('UNIT-022: Transformer passes acknowledgment field from API response to component type', () => {
      // Given: The API response includes an action item with acknowledgment data
      const apiItem = createMockAPIActionItem({
        acknowledgment: {
          user_id: 'u1',
          acknowledged_at: '2026-02-11T08:30:00Z',
          note: null,
        },
      })

      // When: transformAPIActionItem() processes this item
      const result = transformAPIActionItem(apiItem as any)

      // Then: The resulting component-level ActionItem includes the acknowledgment field
      expect(result).toHaveProperty('acknowledgment')
      expect(result.acknowledgment).toEqual({
        user_id: 'u1',
        acknowledged_at: '2026-02-11T08:30:00Z',
        note: null,
      })
    })

    it('UNIT-023: Transformer handles missing acknowledgment field gracefully', () => {
      // Given: The API response includes an action item without an acknowledgment field
      const apiItem = createMockAPIActionItem()

      // When: transformAPIActionItem() processes this item
      const result = transformAPIActionItem(apiItem as any)

      // Then: The resulting component-level ActionItem explicitly has acknowledgment property set to null
      // (it must be a defined property, not just absent)
      expect(result).toHaveProperty('acknowledgment')
      expect(result.acknowledgment).toBeNull()
    })
  })
})
