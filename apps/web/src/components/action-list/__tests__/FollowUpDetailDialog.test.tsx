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
})
