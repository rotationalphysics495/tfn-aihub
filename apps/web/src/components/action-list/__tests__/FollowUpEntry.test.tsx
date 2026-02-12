/**
 * FollowUpEntry Component Tests (Story 13.5: "My Assignments" Panel)
 *
 * TDD tests — these MUST FAIL until the FollowUpEntry component is implemented.
 * Tests cover entry rendering (asset name, action summary, assignee, relative time),
 * text truncation, "New update" indicator with localStorage, and click behavior.
 *
 * @see Story 13.5 - "My Assignments" Panel
 * @see AC #1 - Each entry shows: asset name, action summary, assignee, time since assigned
 * @see AC #2 - "New update" indicator when manager hasn't viewed the update yet
 */

import { render, screen, fireEvent } from '@testing-library/react'
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
  id: 'fu-default',
  action_item_id: 'action-safety-fu1',
  action_summary: 'Investigate pressure anomaly on main valve',
  asset_name: 'Grinder 5',
  category: 'safety',
  assigned_to: 'uuid-assignee-1',
  assigned_to_email: 'john@company.com',
  assigned_by: 'uuid-manager-1',
  note: 'Please check by EOD',
  status: 'assigned',
  report_date: '2026-02-11',
  created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
  updated_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
  ...overrides,
})

// ---------------------------------------------------------------------------
// Import component AFTER mocks are set up
// ---------------------------------------------------------------------------

// The component does not exist yet — this import will fail until it's created.
import { FollowUpEntry } from '../FollowUpEntry'

// Also import the formatRelativeTime utility if it exists
// import { formatRelativeTime } from '../FollowUpEntry'  // or from a utils file

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: FollowUpEntry Component (Story 13.5)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorageMock.clear()
    // Reset localStorage mock data
    Object.keys(mockLocalStorage).forEach(k => delete mockLocalStorage[k])
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // =========================================================================
  // AC1: Entry displays asset name, action summary, assignee, relative time
  // =========================================================================
  describe('AC1: Entry Display Fields', () => {
    it('UNIT-007: FollowUpEntry renders asset name, action summary, assignee, and relative time', () => {
      // Given: A follow-up entry with specific data
      const followUp = createMockFollowUp({
        asset_name: 'Grinder 5',
        action_summary: 'Investigate pressure anomaly on main valve',
        assigned_to_email: 'john@company.com',
        created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
      })

      // When: The FollowUpEntry component renders
      render(<FollowUpEntry followUp={followUp} onSelect={vi.fn()} />)

      // Then: The asset name "Grinder 5" is displayed
      expect(screen.getByText(/grinder 5/i)).toBeInTheDocument()

      // And: The action summary is displayed (possibly truncated)
      expect(screen.getByText(/investigate pressure anomaly/i)).toBeInTheDocument()

      // And: "john@company.com" is displayed as the assignee
      expect(screen.getByText(/john@company\.com/)).toBeInTheDocument()

      // And: "2h ago" is displayed as the relative time
      expect(screen.getByText(/2h ago/)).toBeInTheDocument()
    })

    it('UNIT-008: FollowUpEntry truncates long action summaries', () => {
      // Given: A follow-up entry with action_summary exceeding 80+ characters
      const longSummary =
        'Investigate the root cause of the intermittent pressure fluctuations observed on the main hydraulic valve during the morning shift operation which caused multiple alerts'

      const followUp = createMockFollowUp({
        action_summary: longSummary,
      })

      // When: The FollowUpEntry component renders
      render(<FollowUpEntry followUp={followUp} onSelect={vi.fn()} />)

      // Then: The action summary is truncated with ellipsis
      // The full text should NOT be displayed
      const displayedText = screen.getByText(/investigate the root cause/i)
      expect(displayedText).toBeInTheDocument()

      // Check for truncation (either CSS or JS truncation)
      const textContent = displayedText.textContent || ''
      const hasEllipsis = textContent.includes('…') || textContent.includes('...')
      const hasCssTruncation = displayedText.className.includes('truncate') ||
        displayedText.className.includes('line-clamp')

      expect(hasEllipsis || hasCssTruncation).toBe(true)
    })

    it('UNIT-009: formatRelativeTime utility returns correct relative times', () => {
      // Given: Various ISO timestamp strings representing different time differences
      // Import the utility function
      // This will fail until the utility is implemented
      const { formatRelativeTime } = require('../FollowUpEntry')

      const now = Date.now()

      // When/Then:
      // "0m ago" for current time
      expect(formatRelativeTime(new Date(now).toISOString())).toBe('0m ago')

      // "30m ago" for 30 minutes ago
      expect(formatRelativeTime(new Date(now - 30 * 60 * 1000).toISOString())).toBe('30m ago')

      // "2h ago" for 2 hours ago
      expect(formatRelativeTime(new Date(now - 2 * 60 * 60 * 1000).toISOString())).toBe('2h ago')

      // "1d ago" for 24 hours ago
      expect(formatRelativeTime(new Date(now - 24 * 60 * 60 * 1000).toISOString())).toBe('1d ago')

      // "7d ago" for 7 days ago
      expect(formatRelativeTime(new Date(now - 7 * 24 * 60 * 60 * 1000).toISOString())).toBe('7d ago')
    })
  })

  // =========================================================================
  // AC2: "New update" indicator
  // =========================================================================
  describe('AC2: "New Update" Indicator', () => {
    it('UNIT-017: "New update" dot indicator shows when updated_at > lastViewedTimestamp', () => {
      // Given: A follow-up has updated_at="2026-02-11T10:30:00Z"
      //        and localStorage "followup-viewed-fu-updated" has value "2026-02-11T08:00:00Z"
      const followUp = createMockFollowUp({
        id: 'fu-updated',
        updated_at: '2026-02-11T10:30:00Z',
      })
      mockLocalStorage['followup-viewed-fu-updated'] = new Date('2026-02-11T08:00:00Z').getTime().toString()

      // When: The FollowUpEntry component renders
      render(<FollowUpEntry followUp={followUp} onSelect={vi.fn()} />)

      // Then: A "New update" visual indicator (blue dot or similar) is visible
      const indicator = document.querySelector(
        '[class*="new-update"], [class*="dot"], [aria-label*="new update"], [data-testid="new-update-indicator"]'
      )
      expect(indicator).toBeTruthy()
    })

    it('UNIT-018: "New update" indicator does NOT show when already viewed', () => {
      // Given: A follow-up has updated_at="2026-02-11T10:30:00Z"
      //        and localStorage has a LATER value "2026-02-11T11:00:00Z"
      const followUp = createMockFollowUp({
        id: 'fu-viewed',
        updated_at: '2026-02-11T10:30:00Z',
      })
      mockLocalStorage['followup-viewed-fu-viewed'] = new Date('2026-02-11T11:00:00Z').getTime().toString()

      // When: The FollowUpEntry component renders
      render(<FollowUpEntry followUp={followUp} onSelect={vi.fn()} />)

      // Then: No "New update" indicator is visible
      const indicator = document.querySelector(
        '[class*="new-update"], [data-testid="new-update-indicator"]'
      )
      expect(indicator).toBeNull()
    })

    it('UNIT-019: "New update" indicator shows when no localStorage entry exists', () => {
      // Given: A follow-up exists but no localStorage key has been set
      const followUp = createMockFollowUp({
        id: 'fu-new',
        updated_at: '2026-02-11T10:30:00Z',
      })
      // No localStorage entry for this follow-up

      // When: The FollowUpEntry component renders
      render(<FollowUpEntry followUp={followUp} onSelect={vi.fn()} />)

      // Then: A "New update" indicator is visible (first time viewing)
      const indicator = document.querySelector(
        '[class*="new-update"], [class*="dot"], [aria-label*="new update"], [data-testid="new-update-indicator"]'
      )
      expect(indicator).toBeTruthy()
    })

    it('UNIT-020: "New update" indicator clears when detail dialog is opened', () => {
      // Given: A follow-up has a "New update" indicator visible
      const followUp = createMockFollowUp({
        id: 'fu-clear',
        updated_at: '2026-02-11T10:30:00Z',
      })
      // No localStorage entry — so "New update" should show initially

      const mockOnSelect = vi.fn()

      // When: The user clicks on the follow-up entry
      render(<FollowUpEntry followUp={followUp} onSelect={mockOnSelect} />)

      // Verify indicator is initially visible
      let indicator = document.querySelector(
        '[class*="new-update"], [class*="dot"], [aria-label*="new update"], [data-testid="new-update-indicator"]'
      )
      expect(indicator).toBeTruthy()

      // Click the entry
      const entry = screen.getByText(/grinder 5/i).closest('[role="button"]') ||
        screen.getByText(/grinder 5/i).closest('button') ||
        screen.getByText(/grinder 5/i).parentElement
      if (entry) {
        fireEvent.click(entry)
      }

      // Then: localStorage key "followup-viewed-fu-clear" is updated
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'followup-viewed-fu-clear',
        expect.any(String)
      )
    })
  })

  // =========================================================================
  // AC2 (Story 15.4): has_unread server-side indicator
  // =========================================================================
  describe('AC2 (Story 15.4): has_unread Server-Side Indicator', () => {
    it('15-4-message-thread-ui-UNIT-007: FollowUpEntry shows blue dot when has_unread is true', () => {
      // Given: A FollowUpEntry component receives a follow-up item with has_unread=true
      const followUp = createMockFollowUp({
        id: 'fu-unread',
        has_unread: true,
      } as Partial<MockFollowUpItem>)

      // When: The component renders
      render(<FollowUpEntry followUp={followUp} onSelect={vi.fn()} />)

      // Then: A blue dot indicator (data-testid="new-update-indicator") is visible
      const indicator = screen.getByTestId('new-update-indicator')
      expect(indicator).toBeInTheDocument()
    })

    it('15-4-message-thread-ui-UNIT-008: FollowUpEntry hides blue dot when has_unread is false', () => {
      // Given: A FollowUpEntry component receives a follow-up item with has_unread=false
      const followUp = createMockFollowUp({
        id: 'fu-read',
        has_unread: false,
      } as Partial<MockFollowUpItem>)

      // When: The component renders
      render(<FollowUpEntry followUp={followUp} onSelect={vi.fn()} />)

      // Then: No blue dot indicator is present on the entry
      const indicator = screen.queryByTestId('new-update-indicator')
      expect(indicator).toBeNull()
    })

    it('15-4-message-thread-ui-UNIT-009: FollowUpEntry hides blue dot when has_unread is undefined (backward compat)', () => {
      // Given: A FollowUpEntry component receives a follow-up item without the has_unread property
      const followUp = createMockFollowUp({
        id: 'fu-no-unread-field',
        updated_at: '2026-02-11T10:30:00Z',
      })
      // has_unread is undefined — should fall back to localStorage-based behavior

      // When: The component renders
      render(<FollowUpEntry followUp={followUp} onSelect={vi.fn()} />)

      // Then: Falls back to existing localStorage-based unread detection behavior
      // With no localStorage entry and updated_at set, the localStorage-based check
      // should show the indicator (existing behavior from Story 13.5)
      const indicator = document.querySelector(
        '[data-testid="new-update-indicator"]'
      )
      // When has_unread is undefined, the component should use localStorage logic
      // (the existing UNIT-019 test verifies localStorage fallback)
      expect(indicator).toBeTruthy()
    })
  })

  // =========================================================================
  // Click behavior
  // =========================================================================
  describe('Click Behavior', () => {
    it('UNIT-023: FollowUpEntry click triggers onSelect callback', () => {
      // Given: A FollowUpEntry component is rendered with a follow-up item
      const followUp = createMockFollowUp({ id: 'fu-click' })
      const mockOnSelect = vi.fn()

      // When: The user clicks on the entry
      render(<FollowUpEntry followUp={followUp} onSelect={mockOnSelect} />)

      const entry = screen.getByText(/grinder 5/i).closest('[role="button"]') ||
        screen.getByText(/grinder 5/i).closest('button') ||
        screen.getByText(/grinder 5/i).parentElement
      if (entry) {
        fireEvent.click(entry)
      }

      // Then: The onSelect callback is called with the follow-up data
      expect(mockOnSelect).toHaveBeenCalledWith(
        expect.objectContaining({ id: 'fu-click' })
      )
    })
  })

  // =========================================================================
  // Edge cases
  // =========================================================================
  describe('Edge Cases', () => {
    it('FollowUpEntry handles null asset_name gracefully', () => {
      // Given: A follow-up entry with null asset_name
      const followUp = createMockFollowUp({ asset_name: null })

      // When/Then: No error is thrown
      expect(() => {
        render(<FollowUpEntry followUp={followUp} onSelect={vi.fn()} />)
      }).not.toThrow()
    })
  })
})
