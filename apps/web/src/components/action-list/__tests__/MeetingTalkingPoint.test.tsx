/**
 * MeetingTalkingPoint Component Tests (Story 18.1: Meeting Mode Toggle & Talking Points View)
 *
 * TDD tests — these MUST FAIL until the MeetingTalkingPoint component is implemented.
 * Tests cover card rendering, evidence hiding, priority border colors, assignment badge,
 * and prominent Assign Follow-Up button.
 *
 * @see Story 18.1 - Meeting Mode Toggle & Talking Points View
 * @see AC #1 - Condensed layout with headline, asset, priority
 * @see AC #2 - Assign Follow-Up button prominent; assignment badges visible
 */

import { render, screen, fireEvent } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), back: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => '/',
  useParams: () => ({}),
}))

vi.mock('@/lib/supabase/client', () => ({
  createClient: () => ({
    auth: {
      getSession: vi.fn().mockResolvedValue({
        data: { session: { access_token: 'mock-token' } },
      }),
    },
  }),
}))

const mockFetch = vi.fn()
global.fetch = mockFetch

// ---------------------------------------------------------------------------
// Imports (AFTER mocks)
// ---------------------------------------------------------------------------

import { MeetingTalkingPoint } from '../MeetingTalkingPoint'
import type { ActionItem, FollowUpData } from '@/components/action-engine/types'

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const createMockActionItem = (overrides: Partial<ActionItem> = {}): ActionItem => ({
  id: 'action-test-1',
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

const createMockFollowUp = (overrides: Partial<FollowUpData> = {}): FollowUpData => ({
  id: 'fu-default',
  action_item_id: 'act-default',
  assigned_to: 'uuid-default',
  assignee_email: 'default@example.com',
  status: 'assigned',
  note: null,
  created_at: '2026-01-15T10:00:00Z',
  updated_at: '2026-01-15T10:00:00Z',
  ...overrides,
})

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: Meeting Talking Point Card (Story 18.1)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockReset()
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
  // AC1: Condensed card with headline, asset, priority
  // =========================================================================
  describe('AC1: Card rendering with headline, asset, priority', () => {
    it('UNIT-005: MeetingTalkingPoint renders large card with headline, asset, and priority', () => {
      // Given: A MeetingTalkingPoint component is rendered with a transformed ActionItem
      const item = createMockActionItem({
        priority: 'SAFETY',
        recommendation: {
          text: 'Replace worn bearing on Grinder-04',
          summary: 'Replace bearing',
        },
        asset: {
          id: 'a1',
          name: 'Grinder-04',
          area: 'Grinding',
        },
      })

      // When: The component mounts
      render(<MeetingTalkingPoint item={item} />)

      // Then: The headline "Replace worn bearing on Grinder-04" is displayed at 24px+ size
      const headline = screen.getByText('Replace worn bearing on Grinder-04')
      expect(headline).toBeInTheDocument()
      expect(headline.className).toMatch(/text-xl|text-2xl/)

      // And: "Grinder-04" asset name is visible
      expect(screen.getByText('Grinder-04')).toBeInTheDocument()

      // And: A PriorityBadge with SAFETY level is rendered
      const priorityBadge = screen.getByText('SAFETY')
      expect(priorityBadge).toBeInTheDocument()

      // And: The card has a 4px left border with the safety priority color
      const card = screen.getByRole('article')
      expect(card).toBeInTheDocument()
      expect(card.className).toMatch(/border-l-4|border-l/)
      expect(card.className).toMatch(/border-l-\[#DC2626\]/)

      // And: The card has role="article" and appropriate ARIA labels
      expect(card).toHaveAttribute('role', 'article')
    })

    it('UNIT-006: MeetingTalkingPoint hides evidence detail sections', () => {
      // Given: A MeetingTalkingPoint component is rendered with a complete ActionItem with evidence
      const item = createMockActionItem({
        recommendation: {
          text: 'Check OEE deviation on Line 3',
          summary: 'OEE check',
        },
        evidence: {
          type: 'oee_deviation',
          data: {
            targetOEE: 85,
            actualOEE: 72,
            deviation: -13,
            timeframe: '2026-02-10 Day Shift',
          },
          source: {
            table: 'daily_summaries',
            date: '2026-02-10',
            recordId: 'rec-002',
          },
        },
      })

      // When: The component mounts
      render(<MeetingTalkingPoint item={item} />)

      // Then: The card itself renders (headline is visible — prerequisite check)
      expect(screen.getByText('Check OEE deviation on Line 3')).toBeInTheDocument()

      // And: No EvidenceSection content is rendered
      expect(screen.queryByText(/target.*oee/i)).not.toBeInTheDocument()
      expect(screen.queryByText(/actual.*oee/i)).not.toBeInTheDocument()
      expect(screen.queryByText('85')).not.toBeInTheDocument()
      expect(screen.queryByText('72')).not.toBeInTheDocument()

      // And: No metrics row is visible (check for evidence-specific deviation value, not headline text)
      expect(screen.queryByText('-13')).not.toBeInTheDocument()
      expect(screen.queryByText(/2026-02-10 Day Shift/)).not.toBeInTheDocument()

      // And: No drill-down chevron is present
      expect(screen.queryByTestId('chevron')).not.toBeInTheDocument()
      expect(screen.queryByLabelText(/expand/i)).not.toBeInTheDocument()

      // And: No evidence source references are shown
      expect(screen.queryByText(/daily_summaries/i)).not.toBeInTheDocument()
      expect(screen.queryByText(/rec-002/)).not.toBeInTheDocument()
    })

    it('UNIT-012: MeetingTalkingPoint applies correct priority border color', () => {
      // Given: Three MeetingTalkingPoint cards rendered with priorities SAFETY, FINANCIAL, and OEE
      const safetyItem = createMockActionItem({ id: 'safety-1', priority: 'SAFETY' })
      const financialItem = createMockActionItem({ id: 'financial-1', priority: 'FINANCIAL' })
      const oeeItem = createMockActionItem({ id: 'oee-1', priority: 'OEE' })

      // When: The components mount
      const { unmount: unmount1 } = render(<MeetingTalkingPoint item={safetyItem} />)
      const safetyCard = screen.getByRole('article')
      // Safety card: border-l-[#DC2626] (safety red)
      expect(safetyCard.className).toMatch(/border-l-\[#DC2626\]/)
      unmount1()

      const { unmount: unmount2 } = render(<MeetingTalkingPoint item={financialItem} />)
      const financialCard = screen.getByRole('article')
      // Financial card: border-l-[#F59E0B] (amber)
      expect(financialCard.className).toMatch(/border-l-\[#F59E0B\]/)
      unmount2()

      render(<MeetingTalkingPoint item={oeeItem} />)
      const oeeCard = screen.getByRole('article')
      // OEE card: border-l-[#EAB308] (yellow)
      expect(oeeCard.className).toMatch(/border-l-\[#EAB308\]/)
    })
  })

  // =========================================================================
  // AC2: Assign Follow-Up button and assignment badges
  // =========================================================================
  describe('AC2: Assign Follow-Up button and assignment badges', () => {
    it('UNIT-013: MeetingTalkingPoint shows prominent Assign Follow-Up button', () => {
      // Given: A MeetingTalkingPoint is rendered with an action item that has no follow-up
      const item = createMockActionItem()

      // When: The component mounts
      render(<MeetingTalkingPoint item={item} />)

      // Then: A Button with text "Assign Follow-Up" is visible in the DOM
      const assignButton = screen.getByRole('button', { name: /assign follow-up/i })
      expect(assignButton).toBeInTheDocument()

      // And: The button is not hidden in a dropdown or overflow menu
      // (verify it's not within a collapsed, popover, or dropdown container)
      const closestDropdown = assignButton.closest('[role="menu"]')
      expect(closestDropdown).toBeNull()
      const closestPopover = assignButton.closest('[data-state="closed"]')
      expect(closestPopover).toBeNull()

      // And: The button is directly visible (not in a hidden container)
      expect(assignButton).toBeVisible()
    })

    it('UNIT-014: MeetingTalkingPoint displays assignment badge when follow-up exists', () => {
      // Given: A MeetingTalkingPoint is rendered with an action item and a matching FollowUpData
      const item = createMockActionItem({ id: 'action-with-followup' })
      const followUp = createMockFollowUp({
        action_item_id: 'action-with-followup',
        assignee_email: 'john.doe@factory.com',
        status: 'assigned',
      })

      // When: The component mounts
      render(<MeetingTalkingPoint item={item} followUp={followUp} />)

      // Then: An AssignmentBadge is visible showing the assignee information
      const badge = screen.getByLabelText(/assigned to john\.doe@factory\.com/i)
      expect(badge).toBeInTheDocument()

      // And: The badge shows the assignee email
      expect(screen.getByText(/john\.doe@factory\.com/)).toBeInTheDocument()

      // And: The badge has the correct status variant styling for "assigned"
      expect(screen.getByText(/assigned/i)).toBeInTheDocument()
    })

    it('UNIT-015: MeetingTalkingPoint Assign Follow-Up button opens assignment dialog', () => {
      // Given: A MeetingTalkingPoint is rendered with an action item and an onAssign callback
      const item = createMockActionItem()
      const onAssign = vi.fn()

      // When: The user clicks the "Assign Follow-Up" button
      render(<MeetingTalkingPoint item={item} onAssign={onAssign} />)
      const assignButton = screen.getByRole('button', { name: /assign follow-up/i })
      fireEvent.click(assignButton)

      // Then: The AssignFollowUpDialog is opened (dialog becomes visible in the DOM)
      const dialog = screen.getByRole('dialog')
      expect(dialog).toBeInTheDocument()
    })

    it('UNIT-016: MeetingTalkingPoint shows assignment badge with in_progress status', () => {
      // Given: A MeetingTalkingPoint is rendered with a FollowUpData record with status "in_progress"
      const item = createMockActionItem()
      const followUp = createMockFollowUp({
        assignee_email: 'jane@factory.com',
        status: 'in_progress',
      })

      // When: The component mounts
      render(<MeetingTalkingPoint item={item} followUp={followUp} />)

      // Then: The AssignmentBadge displays the "in_progress" status variant
      const badge = screen.getByLabelText(/assigned to jane@factory\.com/i)
      expect(badge).toBeInTheDocument()
      expect(screen.getByText(/in progress/i)).toBeInTheDocument()

      // And: Has distinct visual styling from "assigned" (warning variant)
      const badgeEl = badge.closest('[class*="warning"]') || badge
      expect(badgeEl.className).toMatch(/warning|amber/)
    })
  })
})
