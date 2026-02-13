/**
 * MorningSummarySection Component Tests (Story 17.2: Smart Summary On-Demand Generation)
 *
 * Tests the on-demand generation prompt UI, loading states during generation,
 * error handling with retry, and existing summary display.
 *
 * @see Story 17.2 - Smart Summary On-Demand Generation for Historical Dates
 * @see AC #1 - Historical date shows generation prompt
 * @see AC #2 - Generate button triggers API
 * @see AC #3 - Existing summary displayed immediately
 * @see AC #5 - Error handling with retry
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

// ---------------------------------------------------------------------------
// Import component AFTER mocks are set up
// ---------------------------------------------------------------------------

import { MorningSummarySection } from '../MorningSummarySection'

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: MorningSummarySection On-Demand Generation (Story 17.2)', () => {
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
  // AC1: Generation prompt for historical dates
  // =========================================================================
  describe('AC1: Generation prompt for historical dates', () => {
    it('Renders "Generate Summary" button when canGenerate=true and hasSummary=false', () => {
      mockUseSmartSummary.mockReturnValue(
        createMockSmartSummaryReturn({
          hasSummary: false,
          canGenerate: true,
        })
      )

      render(<MorningSummarySection reportDate="2026-01-15" />)

      expect(screen.getByText('No summary exists for this date. Generate one?')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /generate summary/i })).toBeInTheDocument()
    })

    it('Does NOT render generate button when hasSummary=true', () => {
      mockUseSmartSummary.mockReturnValue(
        createMockSmartSummaryReturn({
          data: {
            id: 'summary-001',
            date: '2026-01-15',
            summary_text: 'Production ran well.',
            citations: [],
            model_used: 'gpt-4o',
            prompt_tokens: 100,
            completion_tokens: 50,
            generation_duration_ms: 2000,
            is_fallback: false,
            created_at: '2026-01-15T08:00:00Z',
          },
          hasSummary: true,
          canGenerate: false,
        })
      )

      render(<MorningSummarySection reportDate="2026-01-15" />)

      expect(screen.queryByText(/generate summary/i)).not.toBeInTheDocument()
      expect(screen.queryByText('No summary exists for this date.')).not.toBeInTheDocument()
    })

    it('Passes autoGenerate: false to useSmartSummary when reportDate is provided', () => {
      render(<MorningSummarySection reportDate="2026-01-15" />)

      expect(mockUseSmartSummary).toHaveBeenCalledWith(
        expect.objectContaining({
          reportDate: '2026-01-15',
          autoGenerate: false,
        })
      )
    })

    it('Does not pass autoGenerate: false when no reportDate (default T-1 behavior)', () => {
      render(<MorningSummarySection />)

      // When no reportDate, should pass empty object (autoGenerate defaults to true in hook)
      expect(mockUseSmartSummary).toHaveBeenCalledWith({})
    })
  })

  // =========================================================================
  // AC2: Generate button triggers API
  // =========================================================================
  describe('AC2: Generate button interaction', () => {
    it('Clicking "Generate Summary" calls generate function', () => {
      const mockGenerate = vi.fn()
      mockUseSmartSummary.mockReturnValue(
        createMockSmartSummaryReturn({
          hasSummary: false,
          canGenerate: true,
          generate: mockGenerate,
        })
      )

      render(<MorningSummarySection reportDate="2026-01-15" />)

      const button = screen.getByRole('button', { name: /generate summary/i })
      fireEvent.click(button)

      expect(mockGenerate).toHaveBeenCalledTimes(1)
    })

    it('Shows loading/generating animation when isGenerating=true', () => {
      mockUseSmartSummary.mockReturnValue(
        createMockSmartSummaryReturn({
          isGenerating: true,
          canGenerate: false,
        })
      )

      render(<MorningSummarySection reportDate="2026-01-15" />)

      expect(screen.getByText('Generating AI analysis...')).toBeInTheDocument()
      // Generate button should not be visible during generation
      expect(screen.queryByRole('button', { name: /generate summary/i })).not.toBeInTheDocument()
    })
  })

  // =========================================================================
  // AC3: Existing summary displayed immediately
  // =========================================================================
  describe('AC3: Existing summary display', () => {
    it('Shows existing summary text when hasSummary=true with no generation prompt', () => {
      mockUseSmartSummary.mockReturnValue(
        createMockSmartSummaryReturn({
          data: {
            id: 'summary-001',
            date: '2026-01-15',
            summary_text: 'Production ran at 95% OEE with no safety incidents.',
            citations: [],
            model_used: 'gpt-4o',
            prompt_tokens: 100,
            completion_tokens: 50,
            generation_duration_ms: 2000,
            is_fallback: false,
            created_at: '2026-01-15T08:00:00Z',
          },
          hasSummary: true,
          canGenerate: false,
        })
      )

      render(<MorningSummarySection reportDate="2026-01-15" />)

      expect(screen.getByText(/Production ran at 95% OEE/)).toBeInTheDocument()
      expect(screen.getByText('Powered by AI analysis')).toBeInTheDocument()
      expect(screen.queryByText(/generate summary/i)).not.toBeInTheDocument()
    })
  })

  // =========================================================================
  // AC4: Regenerate button on existing summaries
  // =========================================================================
  describe('AC4: Regenerate button', () => {
    it('Renders regenerate button when hasSummary=true', () => {
      mockUseSmartSummary.mockReturnValue(
        createMockSmartSummaryReturn({
          data: {
            id: 'summary-001',
            date: '2026-01-15',
            summary_text: 'Existing summary.',
            citations: [],
            model_used: 'gpt-4o',
            prompt_tokens: 100,
            completion_tokens: 50,
            generation_duration_ms: 2000,
            is_fallback: false,
            created_at: '2026-01-15T08:00:00Z',
          },
          hasSummary: true,
          canGenerate: false,
        })
      )

      render(<MorningSummarySection reportDate="2026-01-15" />)

      expect(screen.getByTitle('Regenerate AI summary')).toBeInTheDocument()
    })
  })

  // =========================================================================
  // AC5: Error handling with retry
  // =========================================================================
  describe('AC5: Error handling', () => {
    it('Shows error with retry when generation fails', () => {
      const mockGenerate = vi.fn()
      mockUseSmartSummary.mockReturnValue(
        createMockSmartSummaryReturn({
          error: 'Unable to generate AI summary. Please try again.',
          hasSummary: false,
          canGenerate: true,
          generate: mockGenerate,
        })
      )

      render(<MorningSummarySection reportDate="2026-01-15" />)

      // Error state should be visible
      expect(screen.getByText(/AI summary unavailable/)).toBeInTheDocument()

      // Retry button should call generate (not refetch) since canGenerate is true
      const retryButton = screen.getByText('retry')
      fireEvent.click(retryButton)

      expect(mockGenerate).toHaveBeenCalledTimes(1)
    })

    it('Shows error with retry calling refetch when canGenerate is false', () => {
      const mockRefetch = vi.fn()
      mockUseSmartSummary.mockReturnValue(
        createMockSmartSummaryReturn({
          error: 'Unable to load AI summary.',
          hasSummary: false,
          canGenerate: false,
          refetch: mockRefetch,
        })
      )

      render(<MorningSummarySection />)

      const retryButton = screen.getByText('retry')
      fireEvent.click(retryButton)

      expect(mockRefetch).toHaveBeenCalledTimes(1)
    })
  })

  // =========================================================================
  // Story 19.1: "Ask about this" button
  // =========================================================================
  describe('Story 19.1: "Ask about this" button', () => {
    it('Renders "Ask about this" button when hasSummary=true', () => {
      mockUseDailyActions.mockReturnValue(
        createMockDailyActionsReturn({
          data: {
            report_date: '2026-02-10',
            actions: [{ asset_name: 'Grinder 5', category: 'oee' }],
          },
        })
      )
      mockUseSmartSummary.mockReturnValue(
        createMockSmartSummaryReturn({
          data: {
            id: 'summary-001',
            date: '2026-02-10',
            summary_text: 'Production ran at 95% OEE.',
            citations: [],
            model_used: 'gpt-4o',
            prompt_tokens: 100,
            completion_tokens: 50,
            generation_duration_ms: 2000,
            is_fallback: false,
            created_at: '2026-02-10T08:00:00Z',
          },
          hasSummary: true,
          canGenerate: false,
        })
      )

      render(<MorningSummarySection reportDate="2026-02-10" />)

      expect(screen.getByRole('button', { name: /ask about this/i })).toBeInTheDocument()
    })

    it('Does NOT render "Ask about this" button when hasSummary=false', () => {
      mockUseSmartSummary.mockReturnValue(
        createMockSmartSummaryReturn({
          hasSummary: false,
          canGenerate: true,
        })
      )

      render(<MorningSummarySection reportDate="2026-02-10" />)

      expect(screen.queryByRole('button', { name: /ask about this/i })).not.toBeInTheDocument()
    })

    it('Does NOT render "Ask about this" button when loading', () => {
      mockUseSmartSummary.mockReturnValue(
        createMockSmartSummaryReturn({
          isLoading: true,
          hasSummary: false,
        })
      )

      render(<MorningSummarySection reportDate="2026-02-10" />)

      expect(screen.queryByRole('button', { name: /ask about this/i })).not.toBeInTheDocument()
    })

    it('Does NOT render "Ask about this" button when generating', () => {
      mockUseSmartSummary.mockReturnValue(
        createMockSmartSummaryReturn({
          isGenerating: true,
          hasSummary: false,
        })
      )

      render(<MorningSummarySection reportDate="2026-02-10" />)

      expect(screen.queryByRole('button', { name: /ask about this/i })).not.toBeInTheDocument()
    })

    it('Does NOT render "Ask about this" button when error', () => {
      mockUseSmartSummary.mockReturnValue(
        createMockSmartSummaryReturn({
          error: 'Some error',
          hasSummary: false,
        })
      )

      render(<MorningSummarySection reportDate="2026-02-10" />)

      expect(screen.queryByRole('button', { name: /ask about this/i })).not.toBeInTheDocument()
    })

    it('Clicking "Ask about this" calls openChatWithContext with correct data', () => {
      mockUseDailyActions.mockReturnValue(
        createMockDailyActionsReturn({
          data: {
            report_date: '2026-02-10',
            actions: [{ asset_name: 'Grinder 5', category: 'oee' }],
          },
        })
      )
      mockUseSmartSummary.mockReturnValue(
        createMockSmartSummaryReturn({
          data: {
            id: 'summary-001',
            date: '2026-02-10',
            summary_text: 'Production ran at 95% OEE. [Source: daily_summaries, 2026-02-10]',
            citations: [],
            model_used: 'gpt-4o',
            prompt_tokens: 100,
            completion_tokens: 50,
            generation_duration_ms: 2000,
            is_fallback: false,
            created_at: '2026-02-10T08:00:00Z',
          },
          hasSummary: true,
          canGenerate: false,
        })
      )

      render(<MorningSummarySection reportDate="2026-02-10" />)

      const button = screen.getByRole('button', { name: /ask about this/i })
      fireEvent.click(button)

      expect(mockOpenChatWithContext).toHaveBeenCalledTimes(1)
      expect(mockOpenChatWithContext).toHaveBeenCalledWith({
        summaryText: 'Production ran at 95% OEE.',  // Citation tags cleaned
        actionItems: [{ asset_name: 'Grinder 5', category: 'oee' }],
        reportDate: '2026-02-10',
      })
    })
  })
})
