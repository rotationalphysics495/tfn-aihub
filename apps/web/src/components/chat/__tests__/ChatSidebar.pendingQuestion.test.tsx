/**
 * ChatSidebar Pending Question Integration Tests (Story 19.3)
 *
 * Tests that ChatSidebar consumes pendingQuestion from ChatContext
 * and auto-sends it as a user message when the sidebar opens.
 *
 * @see Story 19.3 - Context-Aware Follow-Up Suggestions
 * @see AC #2 - Clicking chip opens chat with question pre-filled and sent
 */

import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'

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

// Mock clearPendingQuestion to track calls
const mockClearPendingQuestion = vi.fn()

// Track pending question state
let mockPendingQuestion: string | null = null
let mockIsOpen = false
let mockReportContext: Record<string, unknown> | null = null

vi.mock('@/components/chat/ChatContextProvider', () => ({
  useChatContext: () => ({
    isOpen: mockIsOpen,
    reportContext: mockReportContext,
    pendingQuestion: mockPendingQuestion,
    open: vi.fn(),
    close: vi.fn(),
    setIsOpen: vi.fn(),
    openChatWithContext: vi.fn(),
    openChatWithQuestion: vi.fn(),
    clearReportContext: vi.fn(),
    clearPendingQuestion: mockClearPendingQuestion,
  }),
  ChatContextProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

// ---------------------------------------------------------------------------
// Import component AFTER mocks
// ---------------------------------------------------------------------------

import { ChatSidebar } from '../ChatSidebar'

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: ChatSidebar Pending Question (Story 19.3)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockReset()
    mockGetSession.mockReset()
    mockPendingQuestion = null
    mockIsOpen = false
    mockReportContext = null

    mockGetSession.mockResolvedValue({
      data: { session: { access_token: 'mock-token-abc' } },
    })

    // Default: successful API responses
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        content: 'AI response to pending question',
        citations: [],
        suggested_questions: [],
      }),
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // =========================================================================
  // AC2: ChatSidebar consumes pendingQuestion
  // =========================================================================
  describe('AC2: Pending question auto-send', () => {
    it('19-3-context-aware-followup-suggestions-INT-007: consumes pendingQuestion and auto-sends it', async () => {
      // Given: ChatSidebar is open with a reportContext and pendingQuestion set
      mockIsOpen = true
      mockReportContext = {
        summaryText: 'Production summary for Feb 10',
        actionItems: [{ asset_name: 'Grinder 5', category: 'oee' }],
        reportDate: '2026-02-10',
      }
      mockPendingQuestion = 'What were the top downtime reasons for Grinder 5?'

      // When: The sidebar renders and processes the pendingQuestion
      render(<ChatSidebar />)

      // Then: The pending question text should appear as a user message
      await waitFor(() => {
        const questionText = screen.queryByText(
          /What were the top downtime reasons for Grinder 5/
        )
        expect(questionText).toBeInTheDocument()
      })

      // And: clearPendingQuestion should be called to reset the pending state
      await waitFor(() => {
        expect(mockClearPendingQuestion).toHaveBeenCalled()
      })

      // And: sendMessage (fetch) should have been called with the question
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.any(String),
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('What were the top downtime reasons for Grinder 5'),
          })
        )
      })
    })
  })
})
