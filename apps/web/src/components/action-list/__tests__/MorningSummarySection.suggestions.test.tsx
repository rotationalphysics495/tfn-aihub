/**
 * MorningSummarySection Integration Tests for Suggested Questions (Story 19.3)
 *
 * Tests the integration of SuggestedQuestions with MorningSummarySection,
 * ChatSidebar, and the ChatContextProvider.
 * These tests MUST FAIL until the feature is implemented (TDD).
 *
 * @see Story 19.3 - Context-Aware Follow-Up Suggestions
 * @see AC #2 - Clicking a suggestion chip opens ChatSidebar with question pre-filled
 * @see AC #3 - Suggestions update when report content changes
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
const mockOpenChatWithQuestion = vi.fn()
vi.mock('@/components/chat', () => ({
  useChatContext: () => ({
    openChatWithContext: mockOpenChatWithContext,
    openChatWithQuestion: mockOpenChatWithQuestion,
    isOpen: false,
    reportContext: null,
    pendingQuestion: null,
    open: vi.fn(),
    close: vi.fn(),
    setIsOpen: vi.fn(),
    clearReportContext: vi.fn(),
    clearPendingQuestion: vi.fn(),
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
  evidence_summary: 'OEE dropped below threshold',
  evidence_refs: [],
  created_at: '2026-02-13T08:00:00Z',
  financial_impact_usd: 0,
  priority_rank: 2,
  title: 'OEE Alert',
  description: 'OEE dropped on Grinder 5',
  ...overrides,
})

const createMockDailyActionsReturn = (overrides: Record<string, unknown> = {}) => ({
  data: {
    report_date: '2026-02-13',
    actions: [],
  },
  isLoading: false,
  error: null,
  summary: {
    totalActions: 3,
    safetyCount: 1,
    oeeCount: 1,
    financialCount: 1,
  },
  refetch: vi.fn(),
  hasActions: true,
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

const mockSummaryData = {
  id: 'summary-001',
  date: '2026-02-13',
  summary_text: 'OEE across all lines was 82%. Safety incident reported on Grinder 5.',
  citations: [],
  model_used: 'gpt-4o',
  prompt_tokens: 200,
  completion_tokens: 100,
  generation_duration_ms: 3000,
  is_fallback: false,
  created_at: '2026-02-13T06:00:00Z',
}

// ---------------------------------------------------------------------------
// Import component AFTER mocks are set up
// ---------------------------------------------------------------------------

import { MorningSummarySection } from '../MorningSummarySection'

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: MorningSummarySection Suggested Questions Integration (Story 19.3)', () => {
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
  // AC2: Clicking chip opens ChatSidebar with question and report context
  // =========================================================================
  describe('AC2: Suggestion chip opens chat with question pre-filled and report context', () => {
    it('19-3-context-aware-followup-suggestions-INT-001: Clicking a suggestion chip opens ChatSidebar with question pre-filled and report context', () => {
      // Given: MorningSummarySection rendered with smart summary, action items, and ChatContextProvider
      mockUseDailyActions.mockReturnValue(
        createMockDailyActionsReturn({
          data: {
            report_date: '2026-02-13',
            actions: [
              createMockAction({ id: 's1', asset_name: 'Grinder 5', category: 'safety', priority_level: 'critical' }),
              createMockAction({ id: 'o1', asset_name: 'Grinder 5', category: 'oee', priority_level: 'high' }),
            ],
          },
        })
      )
      mockUseSmartSummary.mockReturnValue(
        createMockSmartSummaryReturn({
          data: mockSummaryData,
          hasSummary: true,
          canGenerate: false,
        })
      )

      render(<MorningSummarySection reportDate="2026-02-13" />)

      // When: The user clicks a suggested question chip
      const suggestionGroup = screen.getByRole('group', {
        name: /suggested follow-up questions/i,
      })
      const chips = suggestionGroup.querySelectorAll('button')
      expect(chips.length).toBeGreaterThanOrEqual(2)

      fireEvent.click(chips[0])

      // Then: openChatWithQuestion is called with the ReportContext and the selected question string
      expect(mockOpenChatWithQuestion).toHaveBeenCalledTimes(1)
      expect(mockOpenChatWithQuestion).toHaveBeenCalledWith(
        expect.objectContaining({
          summaryText: expect.any(String),
          actionItems: expect.any(Array),
          reportDate: '2026-02-13',
        }),
        expect.any(String) // The selected question text
      )
    })

    it('19-3-context-aware-followup-suggestions-INT-002: ChatSidebar auto-sends the pending question after opening with context', () => {
      // Given: MorningSummarySection rendered with smart summary
      mockUseDailyActions.mockReturnValue(
        createMockDailyActionsReturn({
          data: {
            report_date: '2026-02-13',
            actions: [
              createMockAction({ id: 'o1', asset_name: 'Grinder 5', category: 'oee', priority_level: 'high' }),
            ],
          },
        })
      )
      mockUseSmartSummary.mockReturnValue(
        createMockSmartSummaryReturn({
          data: mockSummaryData,
          hasSummary: true,
          canGenerate: false,
        })
      )

      render(<MorningSummarySection reportDate="2026-02-13" />)

      // When: The user clicks a suggestion chip
      const suggestionGroup = screen.getByRole('group', {
        name: /suggested follow-up questions/i,
      })
      const chips = suggestionGroup.querySelectorAll('button')
      expect(chips.length).toBeGreaterThan(0)
      fireEvent.click(chips[0])

      // Then: The question text is passed through the chat mechanism
      expect(mockOpenChatWithQuestion).toHaveBeenCalledTimes(1)
      const questionArg = mockOpenChatWithQuestion.mock.calls[0][1]
      expect(typeof questionArg).toBe('string')
      expect(questionArg.length).toBeGreaterThan(10)
    })

    it('19-3-context-aware-followup-suggestions-INT-003: Report context is included when question is sent from suggestion chip', () => {
      // Given: MorningSummarySection renders with specific summary and actions
      mockUseDailyActions.mockReturnValue(
        createMockDailyActionsReturn({
          data: {
            report_date: '2026-02-13',
            actions: [
              createMockAction({ id: 'o1', asset_name: 'Grinder 5', category: 'oee', priority_level: 'high' }),
              createMockAction({ id: 'f1', asset_name: 'Line 2', category: 'financial', financial_impact_usd: 12500 }),
            ],
          },
        })
      )
      mockUseSmartSummary.mockReturnValue(
        createMockSmartSummaryReturn({
          data: mockSummaryData,
          hasSummary: true,
          canGenerate: false,
        })
      )

      render(<MorningSummarySection reportDate="2026-02-13" />)

      // When: The user clicks a suggestion chip
      const suggestionGroup = screen.getByRole('group', {
        name: /suggested follow-up questions/i,
      })
      const chips = suggestionGroup.querySelectorAll('button')
      expect(chips.length).toBeGreaterThan(0)
      fireEvent.click(chips[0])

      // Then: The ReportContext includes summaryText, actionItems, and reportDate
      expect(mockOpenChatWithQuestion).toHaveBeenCalledTimes(1)
      const reportContext = mockOpenChatWithQuestion.mock.calls[0][0]
      expect(reportContext).toHaveProperty('summaryText')
      expect(reportContext.summaryText).toContain('OEE across all lines was 82%')
      expect(reportContext).toHaveProperty('actionItems')
      expect(Array.isArray(reportContext.actionItems)).toBe(true)
      expect(reportContext.actionItems.length).toBeGreaterThanOrEqual(1)
      expect(reportContext).toHaveProperty('reportDate', '2026-02-13')
    })

    it('19-3-context-aware-followup-suggestions-INT-004: Clicking a second suggestion chip re-sends with updated question', () => {
      // Given: MorningSummarySection rendered with multiple suggestion chips
      mockUseDailyActions.mockReturnValue(
        createMockDailyActionsReturn({
          data: {
            report_date: '2026-02-13',
            actions: [
              createMockAction({ id: 's1', asset_name: 'Grinder 5', category: 'safety', priority_level: 'critical' }),
              createMockAction({ id: 'o1', asset_name: 'Grinder 5', category: 'oee', priority_level: 'high' }),
            ],
          },
        })
      )
      mockUseSmartSummary.mockReturnValue(
        createMockSmartSummaryReturn({
          data: mockSummaryData,
          hasSummary: true,
          canGenerate: false,
        })
      )

      render(<MorningSummarySection reportDate="2026-02-13" />)

      const suggestionGroup = screen.getByRole('group', {
        name: /suggested follow-up questions/i,
      })
      const chips = suggestionGroup.querySelectorAll('button')
      expect(chips.length).toBeGreaterThanOrEqual(2)

      // Click first chip
      fireEvent.click(chips[0])
      const firstQuestion = mockOpenChatWithQuestion.mock.calls[0][1]

      // When: The user clicks a different suggestion chip
      fireEvent.click(chips[1])

      // Then: openChatWithQuestion is called again with a different question
      expect(mockOpenChatWithQuestion).toHaveBeenCalledTimes(2)
      const secondQuestion = mockOpenChatWithQuestion.mock.calls[1][1]
      expect(secondQuestion).not.toBe(firstQuestion)
    })

    it('19-3-context-aware-followup-suggestions-INT-005: Clicking the same suggestion chip twice triggers the question again', () => {
      // Given: MorningSummarySection rendered with suggestion chips
      mockUseDailyActions.mockReturnValue(
        createMockDailyActionsReturn({
          data: {
            report_date: '2026-02-13',
            actions: [
              createMockAction({ id: 'o1', asset_name: 'Grinder 5', category: 'oee', priority_level: 'high' }),
            ],
          },
        })
      )
      mockUseSmartSummary.mockReturnValue(
        createMockSmartSummaryReturn({
          data: mockSummaryData,
          hasSummary: true,
          canGenerate: false,
        })
      )

      render(<MorningSummarySection reportDate="2026-02-13" />)

      const suggestionGroup = screen.getByRole('group', {
        name: /suggested follow-up questions/i,
      })
      const chips = suggestionGroup.querySelectorAll('button')
      expect(chips.length).toBeGreaterThan(0)

      // When: The user clicks the same chip twice
      fireEvent.click(chips[0])
      fireEvent.click(chips[0])

      // Then: openChatWithQuestion is triggered both times
      expect(mockOpenChatWithQuestion).toHaveBeenCalledTimes(2)
    })
  })

  // =========================================================================
  // AC3: Suggestions update when report content changes
  // =========================================================================
  describe('AC3: Suggestions update when MorningSummarySection receives new data', () => {
    it('19-3-context-aware-followup-suggestions-INT-006: Suggestions update when MorningSummarySection receives new smart summary data', () => {
      // Given: MorningSummarySection displays suggestions based on safety data for "Grinder 5"
      mockUseDailyActions.mockReturnValue(
        createMockDailyActionsReturn({
          data: {
            report_date: '2026-02-13',
            actions: [
              createMockAction({ id: 's1', asset_name: 'Grinder 5', category: 'safety', priority_level: 'critical' }),
            ],
          },
        })
      )
      mockUseSmartSummary.mockReturnValue(
        createMockSmartSummaryReturn({
          data: { ...mockSummaryData, summary_text: 'Safety event on Grinder 5' },
          hasSummary: true,
        })
      )

      const { rerender } = render(<MorningSummarySection reportDate="2026-02-13" />)

      // Verify initial suggestions contain "Grinder 5" safety reference
      let suggestionGroup = screen.getByRole('group', {
        name: /suggested follow-up questions/i,
      })
      const initialChipTexts = Array.from(suggestionGroup.querySelectorAll('button')).map(
        (b) => b.textContent
      )
      expect(initialChipTexts.some((t) => t?.includes('Grinder 5'))).toBe(true)

      // When: useSmartSummary and useDailyActions return new data (financial for "Kiln 3")
      mockUseDailyActions.mockReturnValue(
        createMockDailyActionsReturn({
          data: {
            report_date: '2026-02-13',
            actions: [
              createMockAction({ id: 'f1', asset_name: 'Kiln 3', category: 'financial', priority_level: 'high', financial_impact_usd: 12500 }),
            ],
          },
        })
      )
      mockUseSmartSummary.mockReturnValue(
        createMockSmartSummaryReturn({
          data: { ...mockSummaryData, summary_text: 'Financial impact of $12,500 on Kiln 3' },
          hasSummary: true,
        })
      )

      rerender(<MorningSummarySection reportDate="2026-02-13" />)

      // Then: The suggestion chips re-render with new questions reflecting updated content
      suggestionGroup = screen.getByRole('group', {
        name: /suggested follow-up questions/i,
      })
      const updatedChipTexts = Array.from(suggestionGroup.querySelectorAll('button')).map(
        (b) => b.textContent
      )
      expect(updatedChipTexts.some((t) => t?.includes('Kiln 3'))).toBe(true)
      // Should no longer reference old data
      expect(updatedChipTexts).not.toEqual(initialChipTexts)
    })
  })
})
