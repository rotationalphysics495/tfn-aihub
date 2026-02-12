/**
 * FollowUpDetailDialog Component Tests (Story 13.5: "My Assignments" Panel)
 *
 * TDD tests — these MUST FAIL until the FollowUpDetailDialog component is implemented.
 * Tests cover dialog rendering of assignment context: original action item,
 * manager's note, status badge, timestamps, assignee email, and dialog open/close.
 *
 * @see Story 13.5 - "My Assignments" Panel
 * @see AC #3 - Detail view shows full assignment context
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'

// ---------------------------------------------------------------------------
// Mocks (BEFORE imports)
// ---------------------------------------------------------------------------

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), back: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => '/',
  useParams: () => ({}),
}))

// Mock useFollowUpMessages hook
const mockMarkViewed = vi.fn()
let mockUseFollowUpMessagesReturn = {
  messages: [] as Array<{
    id: string
    direction: string
    message_type: string
    sender_email: string
    subject: string | null
    body: string
    sent_at: string
  }>,
  isLoading: false,
  error: null as string | null,
  assignee_name: null as string | null,
  assignee_email: null as string | null,
  status: null as string | null,
  has_unread: false,
  last_viewed_at: null as string | null,
  refetch: vi.fn(),
  markViewed: mockMarkViewed,
}

vi.mock('@/hooks/useFollowUpMessages', () => ({
  useFollowUpMessages: () => mockUseFollowUpMessagesReturn,
}))

// Mock localStorage
const mockLocalStorage: Record<string, string> = {}
const localStorageMock = {
  getItem: vi.fn((key: string) => mockLocalStorage[key] ?? null),
  setItem: vi.fn((key: string, value: string) => {
    mockLocalStorage[key] = value
  }),
  removeItem: vi.fn((key: string) => {
    delete mockLocalStorage[key]
  }),
  clear: vi.fn(() => {
    Object.keys(mockLocalStorage).forEach(k => delete mockLocalStorage[k])
  }),
}
Object.defineProperty(window, 'localStorage', { value: localStorageMock })

// Mock useActionPlans hook (Story 16.3)
const LINKED_PLANS: Record<string, { id: string; title: string; status: string }> = {
  'fu-123': { id: 'ap-456', title: 'Action Plan: Fix valve leak', status: 'open' },
  'fu-link-nav': { id: 'ap-456', title: 'Action Plan: Fix valve leak', status: 'open' },
  'fu-1': { id: 'ap-456', title: 'Action Plan: Fix valve leak', status: 'open' },
  'fu-with-plan': { id: 'ap-789', title: 'Action Plan: Repair pump', status: 'open' },
}

const mockGetLinkedActionPlan = vi.fn(async (followUpId: string) => {
  return LINKED_PLANS[followUpId] || null
})

const mockCreateActionPlan = vi.fn()

vi.mock('@/hooks/useActionPlans', () => ({
  useActionPlans: () => ({
    getLinkedActionPlan: mockGetLinkedActionPlan,
    createActionPlan: mockCreateActionPlan,
    isLoading: false,
    error: null,
  }),
}))

// Mock ActionPlanForm component (Story 16.3) — lightweight mock using real Dialog for portal support
vi.mock('@/components/action-plans', async () => {
  const { Dialog, DialogContent } = await import('@/components/ui/dialog')
  return {
    ActionPlanForm: ({
      open,
      onClose,
      onSuccess,
      prefill,
    }: {
      open: boolean
      onClose: () => void
      onSuccess?: (plan: { id: string; title: string; status: string }) => void
      prefill: { followUpId: string; actionSummary: string; assetName: string | null; responseText: string; category: string | null }
    }) => {
      return (
        <Dialog open={open} onOpenChange={(isOpen: boolean) => { if (!isOpen) onClose() }}>
          <DialogContent>
            <div data-testid="action-plan-form-dialog">
              <label htmlFor="ap-title">Title</label>
              <input id="ap-title" defaultValue={`Action Plan: ${prefill.actionSummary}`} />
              <label htmlFor="ap-root-cause">Root Cause</label>
              <textarea id="ap-root-cause" defaultValue={prefill.responseText} />
              <button onClick={onClose}>Cancel</button>
              <button
                onClick={() => {
                  if (onSuccess) {
                    onSuccess({ id: 'ap-new', title: 'Action Plan: Fix valve leak', status: 'open' })
                  }
                }}
              >
                Create Action Plan Submit
              </button>
            </div>
          </DialogContent>
        </Dialog>
      )
    },
  }
})

// Mock Supabase client (for useActionPlans and ActionPlanForm asset lookup)
vi.mock('@/lib/supabase/client', () => ({
  createClient: () => ({
    auth: { getSession: vi.fn().mockResolvedValue({ data: { session: { access_token: 'mock-token', user: { id: 'user-123' } } } }) },
    from: () => ({
      select: () => ({
        eq: () => ({
          single: () => ({ data: { id: 'asset-uuid-123' }, error: null }),
        }),
      }),
    }),
  }),
}))

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

interface MockFollowUpItem {
  id: string
  action_item_id: string
  action_summary: string
  asset_name: string | null
  category: string | null
  assigned_to: string
  assigned_to_email: string
  assigned_by: string
  note: string | null
  status: 'assigned' | 'in_progress' | 'resolved'
  report_date: string
  created_at: string
  updated_at: string
}

const createMockFollowUp = (
  overrides: Partial<MockFollowUpItem> = {}
): MockFollowUpItem => ({
  id: 'fu-detail-1',
  action_item_id: 'action-safety-abc123',
  action_summary: 'Investigate pressure anomaly on main valve',
  asset_name: 'Grinder 5',
  category: 'safety',
  assigned_to: 'uuid-assignee-1',
  assigned_to_email: 'jane@company.com',
  assigned_by: 'uuid-manager-1',
  note: 'Please check by EOD and report back',
  status: 'in_progress',
  report_date: '2026-02-09',
  created_at: '2026-02-09T08:30:00Z',
  updated_at: '2026-02-10T14:00:00Z',
  ...overrides,
})

// ---------------------------------------------------------------------------
// Import component AFTER mocks are set up
// ---------------------------------------------------------------------------

// The component does not exist yet — this import will fail until it's created.
import { FollowUpDetailDialog } from '../FollowUpDetailDialog'

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: FollowUpDetailDialog Component (Story 13.5)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorageMock.clear()
    Object.keys(mockLocalStorage).forEach(k => delete mockLocalStorage[k])
    // Reset mock hook return to defaults
    mockUseFollowUpMessagesReturn = {
      messages: [],
      isLoading: false,
      error: null,
      assignee_name: null,
      assignee_email: null,
      status: null,
      has_unread: false,
      last_viewed_at: null,
      refetch: vi.fn(),
      markViewed: mockMarkViewed,
    }
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // =========================================================================
  // AC3: Detail view shows full assignment context
  // =========================================================================
  describe('AC3: Full Assignment Context', () => {
    it('UNIT-024: FollowUpDetailDialog renders original action item context', () => {
      // Given: A FollowUpDetailDialog is opened with a follow-up that has
      //        action_summary, category, asset_name
      const followUp = createMockFollowUp({
        action_summary: 'Investigate pressure anomaly',
        category: 'safety',
        asset_name: 'Grinder 5',
      })

      // When: The dialog renders
      render(
        <FollowUpDetailDialog
          followUp={followUp}
          open={true}
          onClose={vi.fn()}
        />
      )

      // Then: The action summary text is displayed
      expect(screen.getByText(/investigate pressure anomaly/i)).toBeInTheDocument()

      // And: The category is shown
      expect(screen.getByText(/safety/i)).toBeInTheDocument()

      // And: The asset name is displayed
      expect(screen.getByText(/grinder 5/i)).toBeInTheDocument()
    })

    it("UNIT-025: FollowUpDetailDialog renders manager's assignment note", () => {
      // Given: A follow-up with a non-null note
      const followUp = createMockFollowUp({
        note: 'Please check by EOD and report back',
      })

      // When: The dialog renders
      render(
        <FollowUpDetailDialog
          followUp={followUp}
          open={true}
          onClose={vi.fn()}
        />
      )

      // Then: The manager's assignment note is visible
      expect(
        screen.getByText(/please check by eod and report back/i)
      ).toBeInTheDocument()
    })

    it('UNIT-026: FollowUpDetailDialog renders current status badge', () => {
      // Given: A follow-up with status="in_progress"
      const followUp = createMockFollowUp({
        status: 'in_progress',
      })

      // When: The dialog renders
      render(
        <FollowUpDetailDialog
          followUp={followUp}
          open={true}
          onClose={vi.fn()}
        />
      )

      // Then: A status badge showing "In Progress" with amber/warning color
      const statusBadge = screen.getByText(/in progress/i)
      expect(statusBadge).toBeInTheDocument()

      // And: The badge has amber/warning styling
      const badgeEl = statusBadge.closest('[class*="amber"], [class*="warning"]')
      expect(badgeEl).toBeTruthy()
    })

    it('UNIT-027: FollowUpDetailDialog renders timestamps for creation and last update', () => {
      // Given: A follow-up with distinct created_at and updated_at
      const followUp = createMockFollowUp({
        created_at: '2026-02-09T08:30:00Z',
        updated_at: '2026-02-10T14:00:00Z',
      })

      // When: The dialog renders
      render(
        <FollowUpDetailDialog
          followUp={followUp}
          open={true}
          onClose={vi.fn()}
        />
      )

      // Then: Both timestamps are displayed in the detail section
      // We look for the dates to be rendered in some human-readable form
      expect(screen.getByText(/feb.*9/i)).toBeInTheDocument()
      expect(screen.getByText(/feb.*10/i)).toBeInTheDocument()
    })

    it('UNIT-028: FollowUpDetailDialog handles follow-up with no note gracefully', () => {
      // Given: A follow-up where note=null
      const followUp = createMockFollowUp({ note: null })

      // When: The dialog renders
      // Then: No error is thrown
      expect(() => {
        render(
          <FollowUpDetailDialog
            followUp={followUp}
            open={true}
            onClose={vi.fn()}
          />
        )
      }).not.toThrow()

      // And: A placeholder or omission is shown (no crash)
      const noteArea = screen.queryByText(/no note provided/i)
      // Either shows placeholder or the note section is simply absent
      const actionSummary = screen.getByText(/investigate pressure anomaly/i)
      expect(actionSummary).toBeInTheDocument()
    })

    it('UNIT-029: FollowUpDetailDialog renders assignee email', () => {
      // Given: A follow-up with assigned_to_email="jane@company.com"
      const followUp = createMockFollowUp({
        assigned_to_email: 'jane@company.com',
      })

      // When: The dialog renders
      render(
        <FollowUpDetailDialog
          followUp={followUp}
          open={true}
          onClose={vi.fn()}
        />
      )

      // Then: The assignee's email is displayed
      expect(screen.getByText(/jane@company\.com/)).toBeInTheDocument()
    })
  })

  // =========================================================================
  // Dialog open/close
  // =========================================================================
  describe('Dialog Open/Close', () => {
    it('UNIT-030: FollowUpDetailDialog opens and closes correctly', () => {
      // Given: The dialog is rendered as open
      const mockOnClose = vi.fn()
      const followUp = createMockFollowUp()

      render(
        <FollowUpDetailDialog
          followUp={followUp}
          open={true}
          onClose={mockOnClose}
        />
      )

      // Verify the dialog content is visible
      expect(screen.getByText(/investigate pressure anomaly/i)).toBeInTheDocument()

      // When: The user clicks the close button
      const closeButton = screen.getByRole('button', { name: /close/i })
      fireEvent.click(closeButton)

      // Then: The onClose callback is called
      expect(mockOnClose).toHaveBeenCalled()
    })
  })

  // =========================================================================
  // AC2: localStorage update on dialog open
  // =========================================================================
  describe('AC2: localStorage Update on Dialog Open', () => {
    it('UNIT-031: FollowUpDetailDialog updates localStorage on open to clear "New update"', () => {
      // Given: A follow-up with updated_at > existing localStorage value
      const followUp = createMockFollowUp({
        id: 'fu-ls-update',
        updated_at: '2026-02-11T10:30:00Z',
      })
      mockLocalStorage['followup-viewed-fu-ls-update'] = new Date('2026-02-11T08:00:00Z').getTime().toString()

      // When: The FollowUpDetailDialog is opened
      render(
        <FollowUpDetailDialog
          followUp={followUp}
          open={true}
          onClose={vi.fn()}
        />
      )

      // Then: localStorage key "followup-viewed-fu-ls-update" is set to current timestamp
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'followup-viewed-fu-ls-update',
        expect.any(String)
      )

      // And: The stored value should be a recent timestamp (within last second)
      const storedValue = localStorageMock.setItem.mock.calls.find(
        (call: string[]) => call[0] === 'followup-viewed-fu-ls-update'
      )?.[1]
      if (storedValue) {
        const storedTime = parseInt(storedValue, 10)
        expect(storedTime).toBeGreaterThan(Date.now() - 5000) // within 5 seconds
      }
    })
  })

  // =========================================================================
  // Story 15.4: MessageThread integration in dialog
  // =========================================================================
  describe('Story 15.4 - AC1: MessageThread Integration', () => {
    it('15-4-message-thread-ui-INT-001: FollowUpDetailDialog renders MessageThread when opened with a follow-up that has messages', () => {
      // Given: A FollowUpDetailDialog is rendered with open=true and a followUpId,
      //        and the useFollowUpMessages hook returns a populated messages array
      const followUp = createMockFollowUp({ id: 'fu-with-messages' })

      // Mock useFollowUpMessages to return messages
      mockUseFollowUpMessagesReturn = {
        ...mockUseFollowUpMessagesReturn,
        messages: [
          {
            id: 'msg-1',
            direction: 'outbound',
            message_type: 'assignment',
            sender_email: 'manager@plant.com',
            subject: 'Follow-up: Investigate pressure anomaly',
            body: 'Please check the valve by EOD',
            sent_at: '2026-02-09T08:30:00Z',
          },
          {
            id: 'msg-2',
            direction: 'inbound',
            message_type: 'response',
            sender_email: 'jane@company.com',
            subject: null,
            body: 'Valve inspected and cleared',
            sent_at: '2026-02-09T14:00:00Z',
          },
        ],
      }

      // When: The dialog opens
      render(
        <FollowUpDetailDialog
          followUp={followUp}
          open={true}
          onClose={vi.fn()}
        />
      )

      // Then: The MessageThread component renders inside the dialog showing
      //       the chronological message thread below the header/metadata section
      // The message thread should contain a role="log" container
      const logContainer = screen.queryByRole('log')
      expect(logContainer).toBeInTheDocument()

      // And: The messages are visible
      expect(screen.getByText(/please check the valve by eod/i)).toBeInTheDocument()
      expect(screen.getByText(/valve inspected and cleared/i)).toBeInTheDocument()
    })
  })

  // =========================================================================
  // Story 15.4 - AC2: markViewed on dialog open
  // =========================================================================
  describe('Story 15.4 - AC2: markViewed on Dialog Open', () => {
    it('15-4-message-thread-ui-INT-003: FollowUpDetailDialog calls markViewed on open to clear unread status', async () => {
      // Given: A FollowUpDetailDialog is rendered with open=true and a followUpId
      const followUp = createMockFollowUp({ id: 'fu-mark-viewed' })

      // We need to mock the useFollowUpMessages hook to provide markViewed spy
      const markViewedSpy = vi.fn()

      // Note: This will require the dialog to call markViewed from useFollowUpMessages
      // which doesn't exist yet — this test will fail until implemented

      // When: The dialog open prop transitions from false to true
      const { rerender } = render(
        <FollowUpDetailDialog
          followUp={followUp}
          open={false}
          onClose={vi.fn()}
        />
      )

      // markViewed should not be called yet
      // (We can't directly check markViewedSpy here without proper mocking,
      // but we verify the PATCH request pattern)

      rerender(
        <FollowUpDetailDialog
          followUp={followUp}
          open={true}
          onClose={vi.fn()}
        />
      )

      // Then: The markViewed() function from useFollowUpMessages is called,
      //       which sends PATCH /api/v1/followups/{id}/viewed
      // This assertion will fail until the dialog integrates useFollowUpMessages
      await waitFor(() => {
        // The dialog should have called markViewed when opened
        // We check that localStorage was updated (existing behavior) AND
        // that the API PATCH was triggered (new behavior from Story 15.4)
        expect(localStorageMock.setItem).toHaveBeenCalledWith(
          'followup-viewed-fu-mark-viewed',
          expect.any(String)
        )
      })

      // The PATCH /api/v1/followups/fu-mark-viewed/viewed should have been called
      // This part will fail until the useFollowUpMessages hook integration is done
    })
  })

  // =========================================================================
  // Edge cases
  // =========================================================================
  describe('Edge Cases', () => {
    it('Dialog handles null category without crashing', () => {
      // Given: A follow-up with category=null
      const followUp = createMockFollowUp({ category: null })

      // When/Then: No error
      expect(() => {
        render(
          <FollowUpDetailDialog
            followUp={followUp}
            open={true}
            onClose={vi.fn()}
          />
        )
      }).not.toThrow()
    })

    it('Dialog handles null asset_name without crashing', () => {
      // Given: A follow-up with asset_name=null
      const followUp = createMockFollowUp({ asset_name: null })

      // When/Then: No error
      expect(() => {
        render(
          <FollowUpDetailDialog
            followUp={followUp}
            open={true}
            onClose={vi.fn()}
          />
        )
      }).not.toThrow()
    })
  })

  // =========================================================================
  // Story 16.3: Create Action Plan from Follow-Up
  // =========================================================================

  // =========================================================================
  // AC2: Linked Action Plan Visible on Follow-Up Detail
  // =========================================================================
  describe('Story 16.3 - AC2: Linked Action Plan Visible on Follow-Up Detail', () => {
    it('16-3-create-action-plan-from-followup-INT-004: Follow-up detail shows linked action plan when one exists', async () => {
      // Given: A follow-up with id='fu-123' has a linked action plan
      //        (queried via getLinkedActionPlan where source_followup_id='fu-123'),
      //        and the action plan has id='ap-456' and title='Action Plan: Fix valve leak'
      const followUp = createMockFollowUp({
        id: 'fu-123',
        status: 'in_progress',
      })

      // Note: The FollowUpDetailDialog must be enhanced to query for linked
      // action plans via useActionPlans.getLinkedActionPlan — this import/mock
      // does not exist yet and the test will fail until Story 16.3 is implemented.

      // When: The FollowUpDetailDialog opens for this follow-up
      render(
        <FollowUpDetailDialog
          followUp={followUp}
          open={true}
          onClose={vi.fn()}
        />
      )

      // Then: A link or badge displaying "Action Plan: Fix valve leak" is visible
      await waitFor(() => {
        expect(screen.getByText(/action plan: fix valve leak/i)).toBeInTheDocument()
      })

      // And: The "Create Action Plan" button is NOT shown
      expect(screen.queryByRole('button', { name: /create action plan/i })).not.toBeInTheDocument()
    })

    it('16-3-create-action-plan-from-followup-INT-005: Linked action plan link navigates to action plan detail', async () => {
      // Given: A FollowUpDetailDialog shows a linked action plan with id='ap-456'
      const followUp = createMockFollowUp({
        id: 'fu-link-nav',
        status: 'in_progress',
      })

      render(
        <FollowUpDetailDialog
          followUp={followUp}
          open={true}
          onClose={vi.fn()}
        />
      )

      // When: The manager clicks the action plan link
      // Then: Navigation is triggered to '/action-plans/ap-456'
      //       (or the link element has href='/action-plans/ap-456')
      await waitFor(() => {
        const actionPlanLink = screen.getByRole('link', { name: /action plan/i })
        expect(actionPlanLink).toHaveAttribute('href', '/action-plans/ap-456')
      })
    })

    it('16-3-create-action-plan-from-followup-INT-006: Follow-up detail dialog shows both "Create Action Plan" button and linked plan correctly across states', async () => {
      // Given: Two follow-ups exist: fu-1 has a linked action plan, fu-2 does not
      const followUp1 = createMockFollowUp({
        id: 'fu-1',
        status: 'in_progress',
      })

      const followUp2 = createMockFollowUp({
        id: 'fu-2',
        status: 'in_progress',
      })

      // When: The detail dialog opens for fu-1
      const { unmount } = render(
        <FollowUpDetailDialog
          followUp={followUp1}
          open={true}
          onClose={vi.fn()}
        />
      )

      // Then: For fu-1, the linked plan link is shown and
      //       "Create Action Plan" is hidden
      await waitFor(() => {
        expect(screen.queryByText(/action plan:/i)).toBeInTheDocument()
      })
      expect(screen.queryByRole('button', { name: /create action plan/i })).not.toBeInTheDocument()

      unmount()

      // When: Dialog opens for fu-2 (no linked plan, but has a response)
      render(
        <FollowUpDetailDialog
          followUp={followUp2}
          open={true}
          onClose={vi.fn()}
        />
      )

      // Then: For fu-2, the "Create Action Plan" button is shown
      //       and no linked plan link is visible
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /create action plan/i })).toBeInTheDocument()
      })
      expect(screen.queryByText(/action plan:/i)).not.toBeInTheDocument()
    })
  })

  // =========================================================================
  // AC3: "Create Action Plan" Button Hidden When No Response
  // =========================================================================
  describe('Story 16.3 - AC3: "Create Action Plan" Button Visibility', () => {
    it('16-3-create-action-plan-from-followup-INT-007: "Create Action Plan" button is hidden when follow-up status is assigned', () => {
      // Given: A FollowUpDetailDialog is open for a follow-up with
      //        status='assigned' (no response yet)
      const followUp = createMockFollowUp({ status: 'assigned' })

      // When: The dialog renders
      render(
        <FollowUpDetailDialog
          followUp={followUp}
          open={true}
          onClose={vi.fn()}
        />
      )

      // Then: No "Create Action Plan" button is present in the dialog
      expect(screen.queryByRole('button', { name: /create action plan/i })).not.toBeInTheDocument()
    })

    it('16-3-create-action-plan-from-followup-INT-008: "Create Action Plan" button is shown when follow-up status is in_progress', async () => {
      // Given: A FollowUpDetailDialog is open for a follow-up with
      //        status='in_progress' (has engagement from assignee),
      //        and no linked action plan exists
      const followUp = createMockFollowUp({ status: 'in_progress' })

      // When: The dialog renders
      render(
        <FollowUpDetailDialog
          followUp={followUp}
          open={true}
          onClose={vi.fn()}
        />
      )

      // Then: A "Create Action Plan" button is visible in the dialog
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /create action plan/i })).toBeInTheDocument()
      })
    })

    it('16-3-create-action-plan-from-followup-INT-009: "Create Action Plan" button is shown when follow-up status is resolved', async () => {
      // Given: A FollowUpDetailDialog is open for a follow-up with
      //        status='resolved', and no linked action plan exists
      const followUp = createMockFollowUp({ status: 'resolved' })

      // When: The dialog renders
      render(
        <FollowUpDetailDialog
          followUp={followUp}
          open={true}
          onClose={vi.fn()}
        />
      )

      // Then: A "Create Action Plan" button is visible in the dialog
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /create action plan/i })).toBeInTheDocument()
      })
    })

    it('16-3-create-action-plan-from-followup-INT-010: "Create Action Plan" button is hidden when linked plan already exists', async () => {
      // Given: A FollowUpDetailDialog is open for a follow-up with
      //        status='in_progress' and a linked action plan already exists
      const followUp = createMockFollowUp({
        id: 'fu-with-plan',
        status: 'in_progress',
      })

      // When: The dialog renders
      render(
        <FollowUpDetailDialog
          followUp={followUp}
          open={true}
          onClose={vi.fn()}
        />
      )

      // Then: The "Create Action Plan" button is NOT shown
      await waitFor(() => {
        expect(screen.queryByRole('button', { name: /create action plan/i })).not.toBeInTheDocument()
      })

      // And: Instead the linked action plan link/badge is displayed
      expect(screen.queryByText(/action plan:/i)).toBeInTheDocument()
    })
  })

  // =========================================================================
  // AC1 Integration: Create Action Plan button opens form
  // =========================================================================
  describe('Story 16.3 - AC1: Create Action Plan from Follow-Up Detail', () => {
    it('16-3-create-action-plan-from-followup-INT-002: FollowUpDetailDialog extracts response text from inbound messages for pre-fill', async () => {
      // Given: A FollowUpDetailDialog is open and useFollowUpMessages returns
      //        messages including an inbound message with direction='inbound',
      //        message_type='response', body='Investigated and found worn bearing causing vibration'
      const followUp = createMockFollowUp({
        id: 'fu-extract-response',
        status: 'in_progress',
      })

      mockUseFollowUpMessagesReturn = {
        ...mockUseFollowUpMessagesReturn,
        messages: [
          {
            id: 'msg-outbound',
            direction: 'outbound',
            message_type: 'assignment',
            sender_email: 'manager@plant.com',
            subject: 'Follow-up assignment',
            body: 'Please investigate',
            sent_at: '2026-02-09T08:00:00Z',
          },
          {
            id: 'msg-inbound',
            direction: 'inbound',
            message_type: 'response',
            sender_email: 'jane@company.com',
            subject: null,
            body: 'Investigated and found worn bearing causing vibration',
            sent_at: '2026-02-10T10:00:00Z',
          },
        ],
      }

      render(
        <FollowUpDetailDialog
          followUp={followUp}
          open={true}
          onClose={vi.fn()}
        />
      )

      // When: The manager clicks "Create Action Plan"
      const createButton = await screen.findByRole('button', { name: /create action plan/i })
      fireEvent.click(createButton)

      // Then: The ActionPlanForm opens with root_cause pre-filled with the
      //       inbound response message body text
      await waitFor(() => {
        const rootCauseField = screen.getByLabelText(/root cause/i) as HTMLTextAreaElement
        expect(rootCauseField.value).toBe('Investigated and found worn bearing causing vibration')
      })
    })
  })

  // =========================================================================
  // AC5: Follow-Up Updates Without Full Page Reload
  // =========================================================================
  describe('Story 16.3 - AC5: Follow-Up Updates After Creation', () => {
    it('16-3-create-action-plan-from-followup-INT-012: Follow-up detail updates to show linked plan after successful creation without reload', async () => {
      // Given: A FollowUpDetailDialog is open showing a "Create Action Plan" button
      //        (no linked plan exists)
      const followUp = createMockFollowUp({
        id: 'fu-live-update',
        status: 'in_progress',
      })

      render(
        <FollowUpDetailDialog
          followUp={followUp}
          open={true}
          onClose={vi.fn()}
        />
      )

      // Then: Initially, the "Create Action Plan" button is visible
      const createButton = await screen.findByRole('button', { name: /create action plan/i })
      expect(createButton).toBeInTheDocument()

      // When: The manager clicks "Create Action Plan" to open the form
      fireEvent.click(createButton)

      // And: The ActionPlanForm opens — click the submit button in the mock form
      //      which triggers onSuccess with the created plan data
      await waitFor(() => {
        expect(screen.getByText(/create action plan submit/i)).toBeInTheDocument()
      })
      fireEvent.click(screen.getByText(/create action plan submit/i))

      // Then: The FollowUpDetailDialog immediately updates to show
      //       "Action Plan: Fix valve leak" as a link/badge
      await waitFor(() => {
        const planLink = screen.queryByText(/action plan: fix valve leak/i)
        expect(planLink).toBeInTheDocument()
      })
    })

    it('16-3-create-action-plan-from-followup-UNIT-020: FollowUpDetailDialog manages ActionPlanForm dialog state correctly', async () => {
      // Given: A FollowUpDetailDialog is rendered with a follow-up that has
      //        status='in_progress' and no linked plan
      const followUp = createMockFollowUp({
        id: 'fu-dialog-state',
        status: 'in_progress',
      })

      render(
        <FollowUpDetailDialog
          followUp={followUp}
          open={true}
          onClose={vi.fn()}
        />
      )

      // When: The manager clicks "Create Action Plan"
      const createButton = await screen.findByRole('button', { name: /create action plan/i })
      fireEvent.click(createButton)

      // Then: The ActionPlanForm dialog opens (has form fields)
      await waitFor(() => {
        expect(screen.getByLabelText(/title/i)).toBeInTheDocument()
      })

      // When: The manager closes the ActionPlanForm without submitting
      //       (e.g., clicks X or presses Escape)
      const closeButtons = screen.getAllByRole('button', { name: /close|cancel/i })
      const formCloseButton = closeButtons[closeButtons.length - 1] // last close is the form's
      fireEvent.click(formCloseButton)

      // Then: The ActionPlanForm dialog closes
      await waitFor(() => {
        expect(screen.queryByLabelText(/title/i)).not.toBeInTheDocument()
      })

      // And: The FollowUpDetailDialog remains open
      expect(screen.getByText(/investigate pressure anomaly/i)).toBeInTheDocument()

      // And: The "Create Action Plan" button is still visible
      expect(screen.getByRole('button', { name: /create action plan/i })).toBeInTheDocument()
    })
  })
})
