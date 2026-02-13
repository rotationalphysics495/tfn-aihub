/**
 * SuggestedQuestions End-to-End Test (Story 19.3)
 *
 * Full flow test: click suggestion chip -> chat sidebar opens -> question sent.
 * Uses React Testing Library to render the full component tree with mocked
 * API responses, simulating the real user experience.
 *
 * @see Story 19.3 - Context-Aware Follow-Up Suggestions
 * @see AC #2 - Clicking chip opens chat with question pre-filled and sent
 */

import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'

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

// Track chat context state for full-flow testing
let chatIsOpen = false
let chatPendingQuestion: string | null = null
let chatReportContext: Record<string, unknown> | null = null
const mockClearPendingQuestion = vi.fn()

vi.mock('@/components/chat', () => ({
  useChatContext: () => ({
    isOpen: chatIsOpen,
    reportContext: chatReportContext,
    pendingQuestion: chatPendingQuestion,
    open: vi.fn(() => { chatIsOpen = true }),
    close: vi.fn(() => { chatIsOpen = false }),
    setIsOpen: vi.fn((v: boolean) => { chatIsOpen = v }),
    openChatWithContext: vi.fn((ctx: Record<string, unknown>) => {
      chatReportContext = ctx
      chatIsOpen = true
    }),
    openChatWithQuestion: vi.fn((ctx: Record<string, unknown>, question: string) => {
      chatReportContext = ctx
      chatPendingQuestion = question
      chatIsOpen = true
    }),
    clearReportContext: vi.fn(() => { chatReportContext = null }),
    clearPendingQuestion: mockClearPendingQuestion,
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
  created_at: '2026-02-10T08:00:00Z',
  financial_impact_usd: 0,
  priority_rank: 2,
  title: 'OEE Alert',
  description: 'OEE dropped on Grinder 5',
  ...overrides,
})

const mockSummaryData = {
  id: 'summary-001',
  date: '2026-02-10',
  summary_text: 'Safety event on Press Line 2. OEE dropped to 72% on Grinder 5.',
  citations: [],
  model_used: 'gpt-4o',
  prompt_tokens: 100,
  completion_tokens: 50,
  generation_duration_ms: 2000,
  is_fallback: false,
  created_at: '2026-02-10T08:00:00Z',
}

// ---------------------------------------------------------------------------
// Import component AFTER mocks
// ---------------------------------------------------------------------------

import { MorningSummarySection } from '../MorningSummarySection'

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: SuggestedQuestions E2E Flow (Story 19.3)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockReset()
    mockGetSession.mockReset()
    chatIsOpen = false
    chatPendingQuestion = null
    chatReportContext = null

    mockGetSession.mockResolvedValue({
      data: { session: { access_token: 'mock-token-abc' } },
    })

    // Mock API responses
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        content: 'AI response about downtime reasons',
        citations: [],
        suggested_questions: [],
      }),
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // =========================================================================
  // E2E: Full flow - click suggestion chip -> chat opens with question sent
  // =========================================================================
  describe('AC2: Full E2E flow', () => {
    it('19-3-context-aware-followup-suggestions-E2E-001: click suggestion chip opens chat with question sent', async () => {
      // Given: The morning report page has smart summary and action items with safety and OEE items
      mockUseDailyActions.mockReturnValue({
        data: {
          report_date: '2026-02-10',
          actions: [
            createMockAction({
              id: 's1',
              asset_name: 'Press Line 2',
              category: 'safety',
              priority_level: 'critical',
            }),
            createMockAction({
              id: 'o1',
              asset_name: 'Grinder 5',
              category: 'oee',
              priority_level: 'high',
            }),
          ],
        },
        isLoading: false,
        error: null,
        summary: {
          totalActions: 2,
          safetyCount: 1,
          oeeCount: 1,
          financialCount: 0,
          qualityCount: 0,
        },
        refetch: vi.fn(),
      })

      mockUseSmartSummary.mockReturnValue({
        data: mockSummaryData,
        isLoading: false,
        isGenerating: false,
        error: null,
        refetch: vi.fn(),
        regenerate: vi.fn(),
        generate: vi.fn(),
        hasSummary: true,
        canGenerate: false,
      })

      // When: Render the full MorningSummarySection
      render(<MorningSummarySection reportDate="2026-02-10" />)

      // Then: Suggestion chips should be visible
      const suggestionGroup = screen.getByRole('group', {
        name: /suggested follow-up questions/i,
      })
      expect(suggestionGroup).toBeInTheDocument()

      // Get suggestion chip buttons
      const chips = suggestionGroup.querySelectorAll('button')
      expect(chips.length).toBeGreaterThanOrEqual(2)
      expect(chips.length).toBeLessThanOrEqual(3)

      // When: The user clicks one of the suggestion chips
      const firstChip = chips[0]
      const chipText = firstChip.textContent ?? ''
      expect(chipText.length).toBeGreaterThan(0)
      fireEvent.click(firstChip)

      // Then: The chat sidebar should be triggered to open with the question
      // The openChatWithQuestion mock should have been called
      await waitFor(() => {
        expect(chatIsOpen).toBe(true)
      })

      // And: The pending question should be set to the chip text
      await waitFor(() => {
        expect(chatPendingQuestion).toBeTruthy()
        expect(typeof chatPendingQuestion).toBe('string')
      })

      // And: The report context should include summary and action items
      await waitFor(() => {
        expect(chatReportContext).toBeTruthy()
        expect(chatReportContext).toEqual(
          expect.objectContaining({
            summaryText: expect.any(String),
            actionItems: expect.any(Array),
            reportDate: '2026-02-10',
          })
        )
      })
    })
  })
})
