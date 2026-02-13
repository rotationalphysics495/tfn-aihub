/**
 * ChatContextProvider Pending Question Tests (Story 19.3)
 *
 * Tests the openChatWithQuestion and clearPendingQuestion methods
 * that enable suggested question chips to open the chat sidebar
 * with a pre-filled question.
 *
 * @see Story 19.3 - Context-Aware Follow-Up Suggestions
 * @see AC #2 - Clicking chip opens chat with question pre-filled and sent
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ChatContextProvider, useChatContext } from '../ChatContextProvider'
import type { ReportContext } from '../types'

// ---------------------------------------------------------------------------
// Test helper component that exposes pendingQuestion context values
// ---------------------------------------------------------------------------

function PendingQuestionTestConsumer() {
  const ctx = useChatContext()
  return (
    <div>
      <span data-testid="isOpen">{String(ctx.isOpen)}</span>
      <span data-testid="hasContext">{String(ctx.reportContext !== null)}</span>
      <span data-testid="pendingQuestion">
        {(ctx as Record<string, unknown>).pendingQuestion as string ?? 'none'}
      </span>
      <span data-testid="reportDate">{ctx.reportContext?.reportDate ?? 'none'}</span>
      <button
        data-testid="openChatWithQuestion"
        onClick={() =>
          (ctx as Record<string, unknown> & {
            openChatWithQuestion?: (context: ReportContext, question: string) => void
          }).openChatWithQuestion?.(
            {
              summaryText: 'Test summary',
              actionItems: [{ asset_name: 'Grinder 5' }],
              reportDate: '2026-02-10',
            },
            'What were the top downtime reasons for Grinder 5?'
          )
        }
      >
        Open With Question
      </button>
      <button
        data-testid="clearPendingQuestion"
        onClick={() =>
          (ctx as Record<string, unknown> & {
            clearPendingQuestion?: () => void
          }).clearPendingQuestion?.()
        }
      >
        Clear Pending Question
      </button>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: ChatContextProvider Pending Question (Story 19.3)', () => {
  // =========================================================================
  // AC2: openChatWithQuestion and clearPendingQuestion
  // =========================================================================
  describe('AC2: Pending question state management', () => {
    it('19-3-context-aware-followup-suggestions-UNIT-025: openChatWithQuestion sets reportContext, pendingQuestion, and opens sidebar', () => {
      // Given: ChatContextProvider is rendered with a TestConsumer
      render(
        <ChatContextProvider>
          <PendingQuestionTestConsumer />
        </ChatContextProvider>
      )

      // Verify initial state
      expect(screen.getByTestId('isOpen').textContent).toBe('false')
      expect(screen.getByTestId('pendingQuestion').textContent).toBe('none')
      expect(screen.getByTestId('hasContext').textContent).toBe('false')

      // When: openChatWithQuestion is called with a ReportContext and a question string
      fireEvent.click(screen.getByTestId('openChatWithQuestion'))

      // Then: isOpen becomes true, reportContext is set, and pendingQuestion is set
      expect(screen.getByTestId('isOpen').textContent).toBe('true')
      expect(screen.getByTestId('hasContext').textContent).toBe('true')
      expect(screen.getByTestId('reportDate').textContent).toBe('2026-02-10')
      expect(screen.getByTestId('pendingQuestion').textContent).toBe(
        'What were the top downtime reasons for Grinder 5?'
      )
    })

    it('19-3-context-aware-followup-suggestions-UNIT-026: clearPendingQuestion resets pendingQuestion to null', () => {
      // Given: ChatContextProvider has a pendingQuestion set via openChatWithQuestion
      render(
        <ChatContextProvider>
          <PendingQuestionTestConsumer />
        </ChatContextProvider>
      )

      // Set the pending question first
      fireEvent.click(screen.getByTestId('openChatWithQuestion'))
      expect(screen.getByTestId('pendingQuestion').textContent).toBe(
        'What were the top downtime reasons for Grinder 5?'
      )

      // When: clearPendingQuestion is called
      fireEvent.click(screen.getByTestId('clearPendingQuestion'))

      // Then: pendingQuestion is reset to null
      expect(screen.getByTestId('pendingQuestion').textContent).toBe('none')
    })
  })
})
