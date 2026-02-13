/**
 * MorningSummarySection Asset Link Integration Tests (Story 19.2)
 *
 * Tests that asset names in the smart summary render as clickable links,
 * scroll to action item cards on click, open detail pages on Ctrl/Cmd+click,
 * and degrade gracefully when data is unavailable.
 *
 * @see Story 19.2 - Clickable Asset Links in Smart Summary
 * @see AC #1 - Asset names displayed as clickable links, click scrolls to action item
 * @see AC #2 - Ctrl/Cmd+click opens asset detail page in new tab
 * @see AC #3 - Unknown asset names rendered as plain text
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

const mockGetSession = vi.fn()
vi.mock('@/lib/supabase/client', () => ({
  createClient: () => ({
    auth: { getSession: mockGetSession },
  }),
}))

const mockFetch = vi.fn()
global.fetch = mockFetch

// Mock useDailyActions
const mockUseDailyActions = vi.fn()
vi.mock('@/hooks/useDailyActions', () => ({
  useDailyActions: (opts?: unknown) => mockUseDailyActions(opts),
}))

// Mock useSmartSummary
const mockUseSmartSummary = vi.fn()
vi.mock('@/hooks/useSmartSummary', () => ({
  useSmartSummary: (opts?: unknown) => mockUseSmartSummary(opts),
}))

// Mock DateNavigation (simple stub)
vi.mock('@/components/report', () => ({
  DateNavigation: () => <div data-testid="date-navigation">DateNavigation</div>,
}))

// Mock useChatContext (Story 19.1)
const mockOpenChatWithContext = vi.fn()
vi.mock('@/components/chat', () => ({
  useChatContext: () => ({
    openChatWithContext: mockOpenChatWithContext,
    isOpen: false,
    reportContext: null,
    open: vi.fn(),
    close: vi.fn(),
    setIsOpen: vi.fn(),
    clearReportContext: vi.fn(),
  }),
}))

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const createMockAction = (overrides: Record<string, unknown> = {}) => ({
  id: 'action-123',
  asset_id: 'asset-1',
  asset_name: 'Grinder 5',
  priority_level: 'high',
  category: 'oee',
  primary_metric_value: '72%',
  recommendation_text: 'Check Grinder 5 bearings',
  evidence_summary: 'OEE below threshold',
  evidence_refs: [],
  created_at: '2026-02-10T08:00:00Z',
  financial_impact_usd: 5000,
  priority_rank: 1,
  title: 'Grinder 5 OEE Below Target',
  description: 'Grinder 5 OEE dropped below 75% threshold',
  ...overrides,
})

const createMockDailyActionsReturn = (overrides: Record<string, unknown> = {}) => ({
  data: {
    report_date: '2026-02-10',
    actions: [],
  },
  isLoading: false,
  error: null,
  summary: {
    totalActions: 3,
    safetyCount: 1,
    oeeCount: 1,
    financialCount: 1,
    qualityCount: 0,
  },
  refetch: vi.fn(),
  ...overrides,
})

const createMockSmartSummaryReturn = (overrides: Record<string, unknown> = {}) => ({
  data: null,
  isLoading: false,
  isGenerating: false,
  error: null,
  refetch: vi.fn(),
  regenerate: vi.fn(),
  generate: vi.fn(),
  hasSummary: false,
  canGenerate: false,
  ...overrides,
})

const createMockSummaryData = (overrides: Record<string, unknown> = {}) => ({
  id: 'summary-001',
  date: '2026-02-10',
  summary_text: 'Grinder 5 needs immediate attention.',
  citations: [],
  model_used: 'gpt-4o',
  prompt_tokens: 100,
  completion_tokens: 50,
  generation_duration_ms: 2000,
  is_fallback: false,
  created_at: '2026-02-10T08:00:00Z',
  ...overrides,
})

// ---------------------------------------------------------------------------
// Import component AFTER mocks are set up
// ---------------------------------------------------------------------------

import { MorningSummarySection } from '../MorningSummarySection'

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: Clickable Asset Links in Smart Summary (Story 19.2)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockReset()
    mockGetSession.mockReset()

    mockGetSession.mockResolvedValue({
      data: { session: { access_token: 'mock-token-abc' } },
    })

    // Default: data loaded, no smart summary
    mockUseDailyActions.mockReturnValue(createMockDailyActionsReturn())
    mockUseSmartSummary.mockReturnValue(createMockSmartSummaryReturn())
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // =========================================================================
  // AC1: Asset names rendered as clickable links
  // =========================================================================
  describe('AC1: Asset names in summary render as clickable links', () => {
    it('INT-001: Asset names in summary render as clickable buttons when matching action items', () => {
      // Given: The smart summary mentions "Grinder 5" and action items include "Grinder 5"
      const actions = [createMockAction({ asset_name: 'Grinder 5' })]
      mockUseDailyActions.mockReturnValue(
        createMockDailyActionsReturn({
          data: { report_date: '2026-02-10', actions },
        })
      )
      mockUseSmartSummary.mockReturnValue(
        createMockSmartSummaryReturn({
          data: createMockSummaryData({
            summary_text: 'Grinder 5 needs immediate attention.',
          }),
          hasSummary: true,
        })
      )

      // When: MorningSummarySection renders the summary
      render(<MorningSummarySection reportDate="2026-02-10" />)

      // Then: "Grinder 5" is rendered as a clickable button element (not plain text)
      const assetLink = screen.getByRole('button', { name: 'Grinder 5' })
      expect(assetLink).toBeInTheDocument()
      expect(assetLink).toHaveClass('text-info-blue')
      expect(assetLink).toHaveClass('cursor-pointer')
    })

    it('INT-002: Clicking asset link scrolls to the matching action item card', () => {
      // Given: Summary renders "Grinder 5" as a clickable link and a DOM element with matching data-asset-name exists
      const actions = [createMockAction({ asset_name: 'Grinder 5' })]
      mockUseDailyActions.mockReturnValue(
        createMockDailyActionsReturn({
          data: { report_date: '2026-02-10', actions },
        })
      )
      mockUseSmartSummary.mockReturnValue(
        createMockSmartSummaryReturn({
          data: createMockSummaryData({
            summary_text: 'Grinder 5 needs immediate attention.',
          }),
          hasSummary: true,
        })
      )

      // Create a mock scroll target element in the DOM
      const scrollTarget = document.createElement('div')
      scrollTarget.setAttribute('data-asset-name', 'Grinder 5')
      scrollTarget.scrollIntoView = vi.fn()
      document.body.appendChild(scrollTarget)

      render(<MorningSummarySection reportDate="2026-02-10" />)

      // When: The user clicks the "Grinder 5" link (no modifier keys)
      const assetLink = screen.getByRole('button', { name: 'Grinder 5' })
      fireEvent.click(assetLink)

      // Then: scrollIntoView is called on the target element
      expect(scrollTarget.scrollIntoView).toHaveBeenCalledWith({
        behavior: 'smooth',
        block: 'center',
      })

      // Cleanup
      document.body.removeChild(scrollTarget)
    })

    it('INT-003: Clicking asset link adds highlight flash animation to target card', () => {
      // Given: Summary renders "Grinder 5" as a clickable link and target card exists
      vi.useFakeTimers()

      const actions = [createMockAction({ asset_name: 'Grinder 5' })]
      mockUseDailyActions.mockReturnValue(
        createMockDailyActionsReturn({
          data: { report_date: '2026-02-10', actions },
        })
      )
      mockUseSmartSummary.mockReturnValue(
        createMockSmartSummaryReturn({
          data: createMockSummaryData({
            summary_text: 'Grinder 5 needs immediate attention.',
          }),
          hasSummary: true,
        })
      )

      // Create a mock scroll target element
      const scrollTarget = document.createElement('div')
      scrollTarget.setAttribute('data-asset-name', 'Grinder 5')
      scrollTarget.scrollIntoView = vi.fn()
      document.body.appendChild(scrollTarget)

      render(<MorningSummarySection reportDate="2026-02-10" />)

      // When: The user clicks the "Grinder 5" link
      const assetLink = screen.getByRole('button', { name: 'Grinder 5' })
      fireEvent.click(assetLink)

      // Then: A highlight class is temporarily added to the target card element
      expect(scrollTarget.classList.contains('highlight-flash')).toBe(true)

      // And removed after approximately 1500ms
      vi.advanceTimersByTime(1500)
      expect(scrollTarget.classList.contains('highlight-flash')).toBe(false)

      // Cleanup
      document.body.removeChild(scrollTarget)
      vi.useRealTimers()
    })

    it('INT-004: Multiple asset names in summary all render as clickable links', () => {
      // Given: Summary mentions "Grinder 5" and "CAMA 2400" and action items include both
      const actions = [
        createMockAction({ id: 'action-123', asset_name: 'Grinder 5' }),
        createMockAction({ id: 'action-456', asset_name: 'CAMA 2400' }),
      ]
      mockUseDailyActions.mockReturnValue(
        createMockDailyActionsReturn({
          data: { report_date: '2026-02-10', actions },
        })
      )
      mockUseSmartSummary.mockReturnValue(
        createMockSmartSummaryReturn({
          data: createMockSummaryData({
            summary_text: 'Grinder 5 is critical. CAMA 2400 needs review.',
          }),
          hasSummary: true,
        })
      )

      // When: MorningSummarySection renders the summary
      render(<MorningSummarySection reportDate="2026-02-10" />)

      // Then: Both "Grinder 5" and "CAMA 2400" are rendered as clickable button elements
      expect(screen.getByRole('button', { name: 'Grinder 5' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'CAMA 2400' })).toBeInTheDocument()
    })

    it('INT-005: Asset links render correctly within markdown bold text', () => {
      // Given: Summary contains "**Grinder 5** needs attention" (asset name inside markdown bold)
      const actions = [createMockAction({ asset_name: 'Grinder 5' })]
      mockUseDailyActions.mockReturnValue(
        createMockDailyActionsReturn({
          data: { report_date: '2026-02-10', actions },
        })
      )
      mockUseSmartSummary.mockReturnValue(
        createMockSmartSummaryReturn({
          data: createMockSummaryData({
            summary_text: '**Grinder 5** needs attention',
          }),
          hasSummary: true,
        })
      )

      // When: MorningSummarySection renders the summary
      render(<MorningSummarySection reportDate="2026-02-10" />)

      // Then: "Grinder 5" is rendered as a clickable button inside a bold wrapper
      const assetLink = screen.getByRole('button', { name: 'Grinder 5' })
      expect(assetLink).toBeInTheDocument()
    })

    it('INT-006: Asset links render correctly within markdown list items', () => {
      // Given: Summary contains a markdown list with asset names
      const actions = [
        createMockAction({ id: 'action-123', asset_name: 'Grinder 5' }),
        createMockAction({ id: 'action-456', asset_name: 'CAMA 2400' }),
      ]
      mockUseDailyActions.mockReturnValue(
        createMockDailyActionsReturn({
          data: { report_date: '2026-02-10', actions },
        })
      )
      mockUseSmartSummary.mockReturnValue(
        createMockSmartSummaryReturn({
          data: createMockSummaryData({
            summary_text: '- Grinder 5 is critical\n- CAMA 2400 needs review',
          }),
          hasSummary: true,
        })
      )

      // When: MorningSummarySection renders the summary
      render(<MorningSummarySection reportDate="2026-02-10" />)

      // Then: Both asset names within list items are rendered as clickable buttons
      expect(screen.getByRole('button', { name: 'Grinder 5' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'CAMA 2400' })).toBeInTheDocument()
    })

    it('INT-007: No links when actions data is null (loading state)', () => {
      // Given: Summary contains asset names but useDailyActions returns null data
      mockUseDailyActions.mockReturnValue(
        createMockDailyActionsReturn({
          data: null,
        })
      )
      mockUseSmartSummary.mockReturnValue(
        createMockSmartSummaryReturn({
          data: createMockSummaryData({
            summary_text: 'Grinder 5 needs attention',
          }),
          hasSummary: true,
        })
      )

      // When: MorningSummarySection renders the summary
      render(<MorningSummarySection reportDate="2026-02-10" />)

      // Then: All asset names render as plain text with no clickable buttons
      expect(screen.queryByRole('button', { name: 'Grinder 5' })).not.toBeInTheDocument()
      // The text should still be visible, just not as a button
      expect(screen.getByText(/Grinder 5/)).toBeInTheDocument()
    })

    it('INT-008: No links when actions array is empty', () => {
      // Given: Summary contains asset names but useDailyActions returns empty actions
      mockUseDailyActions.mockReturnValue(
        createMockDailyActionsReturn({
          data: { report_date: '2026-02-10', actions: [] },
        })
      )
      mockUseSmartSummary.mockReturnValue(
        createMockSmartSummaryReturn({
          data: createMockSummaryData({
            summary_text: 'Grinder 5 needs attention',
          }),
          hasSummary: true,
        })
      )

      // When: MorningSummarySection renders the summary
      render(<MorningSummarySection reportDate="2026-02-10" />)

      // Then: All asset names render as plain text with no clickable buttons
      expect(screen.queryByRole('button', { name: 'Grinder 5' })).not.toBeInTheDocument()
      expect(screen.getByText(/Grinder 5/)).toBeInTheDocument()
    })

    it('INT-009: Scroll target not found is handled gracefully (no-op)', () => {
      // Given: Summary renders "Grinder 5" as a clickable link but no scroll target exists in DOM
      const actions = [createMockAction({ asset_name: 'Grinder 5' })]
      mockUseDailyActions.mockReturnValue(
        createMockDailyActionsReturn({
          data: { report_date: '2026-02-10', actions },
        })
      )
      mockUseSmartSummary.mockReturnValue(
        createMockSmartSummaryReturn({
          data: createMockSummaryData({
            summary_text: 'Grinder 5 needs immediate attention.',
          }),
          hasSummary: true,
        })
      )

      render(<MorningSummarySection reportDate="2026-02-10" />)

      // When: The user clicks the "Grinder 5" link (no matching DOM target)
      const assetLink = screen.getByRole('button', { name: 'Grinder 5' })

      // Then: No error is thrown, click is a no-op
      expect(() => {
        fireEvent.click(assetLink)
      }).not.toThrow()
    })
  })

  // =========================================================================
  // AC2: Ctrl/Cmd+click opens asset detail page in new tab
  // =========================================================================
  describe('AC2: Ctrl/Cmd+click opens asset detail page in new tab', () => {
    it('INT-010: Ctrl+click on asset link opens action detail page in new tab', () => {
      // Given: Summary renders "Grinder 5" as a clickable link, action has id "action-123"
      const actions = [createMockAction({ id: 'action-123', asset_name: 'Grinder 5' })]
      mockUseDailyActions.mockReturnValue(
        createMockDailyActionsReturn({
          data: { report_date: '2026-02-10', actions },
        })
      )
      mockUseSmartSummary.mockReturnValue(
        createMockSmartSummaryReturn({
          data: createMockSummaryData({
            summary_text: 'Grinder 5 needs immediate attention.',
          }),
          hasSummary: true,
        })
      )

      const mockWindowOpen = vi.spyOn(window, 'open').mockImplementation(() => null)

      render(<MorningSummarySection reportDate="2026-02-10" />)

      // When: The user Ctrl+clicks the "Grinder 5" link
      const assetLink = screen.getByRole('button', { name: 'Grinder 5' })
      fireEvent.click(assetLink, { ctrlKey: true })

      // Then: window.open is called with the correct action detail URL
      expect(mockWindowOpen).toHaveBeenCalledWith(
        '/morning-report/action/action-123',
        '_blank'
      )

      mockWindowOpen.mockRestore()
    })

    it('INT-011: Cmd+click (metaKey) on asset link opens action detail page in new tab', () => {
      // Given: Summary renders "Grinder 5" as a clickable link, action has id "action-123"
      const actions = [createMockAction({ id: 'action-123', asset_name: 'Grinder 5' })]
      mockUseDailyActions.mockReturnValue(
        createMockDailyActionsReturn({
          data: { report_date: '2026-02-10', actions },
        })
      )
      mockUseSmartSummary.mockReturnValue(
        createMockSmartSummaryReturn({
          data: createMockSummaryData({
            summary_text: 'Grinder 5 needs immediate attention.',
          }),
          hasSummary: true,
        })
      )

      const mockWindowOpen = vi.spyOn(window, 'open').mockImplementation(() => null)

      render(<MorningSummarySection reportDate="2026-02-10" />)

      // When: The user Cmd+clicks the "Grinder 5" link (metaKey)
      const assetLink = screen.getByRole('button', { name: 'Grinder 5' })
      fireEvent.click(assetLink, { metaKey: true })

      // Then: window.open is called with the correct action detail URL
      expect(mockWindowOpen).toHaveBeenCalledWith(
        '/morning-report/action/action-123',
        '_blank'
      )

      mockWindowOpen.mockRestore()
    })

    it('INT-012: Ctrl/Cmd+click does NOT trigger scroll behavior', () => {
      // Given: Summary renders "Grinder 5" as a clickable link and a scroll target exists
      const actions = [createMockAction({ id: 'action-123', asset_name: 'Grinder 5' })]
      mockUseDailyActions.mockReturnValue(
        createMockDailyActionsReturn({
          data: { report_date: '2026-02-10', actions },
        })
      )
      mockUseSmartSummary.mockReturnValue(
        createMockSmartSummaryReturn({
          data: createMockSummaryData({
            summary_text: 'Grinder 5 needs immediate attention.',
          }),
          hasSummary: true,
        })
      )

      // Create a mock scroll target
      const scrollTarget = document.createElement('div')
      scrollTarget.setAttribute('data-asset-name', 'Grinder 5')
      scrollTarget.scrollIntoView = vi.fn()
      document.body.appendChild(scrollTarget)

      const mockWindowOpen = vi.spyOn(window, 'open').mockImplementation(() => null)

      render(<MorningSummarySection reportDate="2026-02-10" />)

      // When: The user Ctrl+clicks the "Grinder 5" link
      const assetLink = screen.getByRole('button', { name: 'Grinder 5' })
      fireEvent.click(assetLink, { ctrlKey: true })

      // Then: window.open is called, but scrollIntoView is NOT called
      expect(mockWindowOpen).toHaveBeenCalled()
      expect(scrollTarget.scrollIntoView).not.toHaveBeenCalled()

      // Cleanup
      document.body.removeChild(scrollTarget)
      mockWindowOpen.mockRestore()
    })

    it('INT-013: Ctrl+click uses correct action ID when multiple assets exist', () => {
      // Given: Summary mentions both "Grinder 5" and "CAMA 2400" with different action IDs
      const actions = [
        createMockAction({ id: 'action-123', asset_name: 'Grinder 5' }),
        createMockAction({ id: 'action-456', asset_name: 'CAMA 2400' }),
      ]
      mockUseDailyActions.mockReturnValue(
        createMockDailyActionsReturn({
          data: { report_date: '2026-02-10', actions },
        })
      )
      mockUseSmartSummary.mockReturnValue(
        createMockSmartSummaryReturn({
          data: createMockSummaryData({
            summary_text: 'Grinder 5 is critical. CAMA 2400 needs review.',
          }),
          hasSummary: true,
        })
      )

      const mockWindowOpen = vi.spyOn(window, 'open').mockImplementation(() => null)

      render(<MorningSummarySection reportDate="2026-02-10" />)

      // When: The user Ctrl+clicks the "CAMA 2400" link
      const assetLink = screen.getByRole('button', { name: 'CAMA 2400' })
      fireEvent.click(assetLink, { ctrlKey: true })

      // Then: window.open is called with CAMA 2400's action ID, not Grinder 5's
      expect(mockWindowOpen).toHaveBeenCalledWith(
        '/morning-report/action/action-456',
        '_blank'
      )

      mockWindowOpen.mockRestore()
    })

    it('INT-014: Duplicate asset names use first action item ID for Ctrl+click navigation', () => {
      // Given: Two action items have the same asset_name with different IDs
      const actions = [
        createMockAction({ id: 'action-123', asset_name: 'Grinder 5', priority_rank: 1 }),
        createMockAction({ id: 'action-789', asset_name: 'Grinder 5', priority_rank: 2 }),
      ]
      mockUseDailyActions.mockReturnValue(
        createMockDailyActionsReturn({
          data: { report_date: '2026-02-10', actions },
        })
      )
      mockUseSmartSummary.mockReturnValue(
        createMockSmartSummaryReturn({
          data: createMockSummaryData({
            summary_text: 'Grinder 5 needs immediate attention.',
          }),
          hasSummary: true,
        })
      )

      const mockWindowOpen = vi.spyOn(window, 'open').mockImplementation(() => null)

      render(<MorningSummarySection reportDate="2026-02-10" />)

      // When: The user Ctrl+clicks the "Grinder 5" link
      const assetLink = screen.getByRole('button', { name: 'Grinder 5' })
      fireEvent.click(assetLink, { ctrlKey: true })

      // Then: window.open is called with the FIRST action item's ID
      expect(mockWindowOpen).toHaveBeenCalledWith(
        '/morning-report/action/action-123',
        '_blank'
      )

      mockWindowOpen.mockRestore()
    })
  })

  // =========================================================================
  // AC3: Unknown asset names rendered as plain text
  // =========================================================================
  describe('AC3: Unmatched asset-like text renders as plain text', () => {
    it('INT-015: Unmatched asset-like text renders as plain text in the component', () => {
      // Given: Summary contains "Unknown Asset" which does not match any action item
      const actions = [createMockAction({ asset_name: 'Grinder 5' })]
      mockUseDailyActions.mockReturnValue(
        createMockDailyActionsReturn({
          data: { report_date: '2026-02-10', actions },
        })
      )
      mockUseSmartSummary.mockReturnValue(
        createMockSmartSummaryReturn({
          data: createMockSummaryData({
            summary_text: 'Unknown Asset has issues. Grinder 5 is critical.',
          }),
          hasSummary: true,
        })
      )

      // When: MorningSummarySection renders the summary
      render(<MorningSummarySection reportDate="2026-02-10" />)

      // Then: "Unknown Asset" is rendered as plain text, NOT as a button
      expect(screen.queryByRole('button', { name: 'Unknown Asset' })).not.toBeInTheDocument()
      expect(screen.getByText(/Unknown Asset/)).toBeInTheDocument()

      // And "Grinder 5" IS rendered as a clickable button
      expect(screen.getByRole('button', { name: 'Grinder 5' })).toBeInTheDocument()
    })
  })
})
