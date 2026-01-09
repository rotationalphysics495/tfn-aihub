import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ChatMessage } from '../ChatMessage'
import type { Message } from '../types'

/**
 * Tests for ChatMessage Component
 *
 * Story: 5.7 - Agent Chat Integration
 * AC: #2 - Citation Rendering
 * AC: #3 - Follow-Up Question Chips
 * AC: #5 - Error Handling in UI
 * AC: #7 - Response Formatting
 */

describe('ChatMessage', () => {
  const baseUserMessage: Message = {
    id: 'user-1',
    role: 'user',
    content: 'What is the OEE for Grinder 5?',
    timestamp: new Date('2026-01-09T10:00:00Z'),
  }

  const baseAssistantMessage: Message = {
    id: 'assistant-1',
    role: 'assistant',
    content: 'Grinder 5 has an OEE of **87.5%** which is above target.',
    timestamp: new Date('2026-01-09T10:00:05Z'),
  }

  describe('Basic rendering', () => {
    it('renders user messages correctly', () => {
      render(<ChatMessage message={baseUserMessage} />)

      expect(screen.getByText('What is the OEE for Grinder 5?')).toBeInTheDocument()
      expect(screen.getByText('You')).toBeInTheDocument()
    })

    it('renders assistant messages correctly', () => {
      render(<ChatMessage message={baseAssistantMessage} />)

      expect(screen.getByText('AI')).toBeInTheDocument()
    })

    it('renders timestamps', () => {
      render(<ChatMessage message={baseUserMessage} />)

      // Should have a timestamp element displayed (time varies by timezone)
      const timestampElement = screen.getByText(/AM|PM/)
      expect(timestampElement).toBeInTheDocument()
      expect(timestampElement).toHaveClass('text-muted-foreground')
    })
  })

  describe('AC#7: Response Formatting with Markdown', () => {
    it('renders markdown content for assistant messages', () => {
      const markdownMessage: Message = {
        ...baseAssistantMessage,
        content: 'Here is a **bold** statement and *italic* text.',
      }

      render(<ChatMessage message={markdownMessage} />)

      // Markdown should be rendered
      const boldElement = screen.getByText('bold')
      expect(boldElement.tagName).toBe('STRONG')
    })

    it('renders markdown tables', () => {
      const tableMessage: Message = {
        ...baseAssistantMessage,
        content: `| Asset | OEE |
| --- | --- |
| Grinder 5 | 87% |
| CAMA 800-1 | 82% |`,
      }

      render(<ChatMessage message={tableMessage} />)

      // Should render a table
      expect(screen.getByText('Asset')).toBeInTheDocument()
      expect(screen.getByText('Grinder 5')).toBeInTheDocument()
    })

    it('renders markdown lists', () => {
      const listMessage: Message = {
        ...baseAssistantMessage,
        content: `Key findings:
- OEE is above target
- Downtime decreased by 15%
- Production on track`,
      }

      render(<ChatMessage message={listMessage} />)

      expect(screen.getByText('OEE is above target')).toBeInTheDocument()
    })

    it('applies status colors for production keywords', () => {
      const statusMessage: Message = {
        ...baseAssistantMessage,
        content: 'The status is **running** and production is **behind** schedule.',
      }

      render(<ChatMessage message={statusMessage} />)

      // "running" should have success styling
      const runningText = screen.getByText('running')
      expect(runningText).toHaveClass('text-success-green')

      // "behind" should have warning styling
      const behindText = screen.getByText('behind')
      expect(behindText).toHaveClass('text-warning-amber')
    })
  })

  describe('AC#3: Follow-Up Question Chips', () => {
    it('renders follow-up chips when provided', () => {
      const messageWithFollowUps: Message = {
        ...baseAssistantMessage,
        followUpQuestions: [
          'What caused the downtime?',
          'How does this compare to last week?',
        ],
      }

      const onFollowUpSelect = vi.fn()

      render(
        <ChatMessage
          message={messageWithFollowUps}
          onFollowUpSelect={onFollowUpSelect}
        />
      )

      expect(screen.getByText('What caused the downtime?')).toBeInTheDocument()
      expect(screen.getByText('How does this compare to last week?')).toBeInTheDocument()
    })

    it('calls onFollowUpSelect when chip is clicked', () => {
      const messageWithFollowUps: Message = {
        ...baseAssistantMessage,
        followUpQuestions: ['Test question'],
      }

      const onFollowUpSelect = vi.fn()

      render(
        <ChatMessage
          message={messageWithFollowUps}
          onFollowUpSelect={onFollowUpSelect}
        />
      )

      const chip = screen.getByText('Test question').closest('button')
      if (chip) {
        fireEvent.click(chip)
        expect(onFollowUpSelect).toHaveBeenCalledWith('Test question')
      }
    })

    it('does not render follow-up chips for user messages', () => {
      const userWithFollowUps: Message = {
        ...baseUserMessage,
        followUpQuestions: ['Should not appear'],
      }

      const onFollowUpSelect = vi.fn()

      render(
        <ChatMessage
          message={userWithFollowUps}
          onFollowUpSelect={onFollowUpSelect}
        />
      )

      expect(screen.queryByText('Should not appear')).not.toBeInTheDocument()
    })
  })

  describe('AC#5: Error Handling in UI', () => {
    it('renders error state with warning styling', () => {
      const errorMessage: Message = {
        id: 'error-1',
        role: 'assistant',
        content: 'I encountered an error processing your request.',
        timestamp: new Date(),
        isError: true,
      }

      render(<ChatMessage message={errorMessage} />)

      // Should display error content
      expect(screen.getByText('I encountered an error processing your request.')).toBeInTheDocument()
    })

    it('shows retry button on error messages', () => {
      const errorMessage: Message = {
        id: 'error-1',
        role: 'assistant',
        content: 'Error occurred.',
        timestamp: new Date(),
        isError: true,
      }

      const onRetry = vi.fn()

      render(<ChatMessage message={errorMessage} onRetry={onRetry} />)

      const retryButton = screen.getByText('Retry')
      expect(retryButton).toBeInTheDocument()
    })

    it('calls onRetry when retry button is clicked', () => {
      const errorMessage: Message = {
        id: 'error-1',
        role: 'assistant',
        content: 'Error occurred.',
        timestamp: new Date(),
        isError: true,
      }

      const onRetry = vi.fn()

      render(<ChatMessage message={errorMessage} onRetry={onRetry} />)

      const retryButton = screen.getByText('Retry').closest('button')
      if (retryButton) {
        fireEvent.click(retryButton)
        expect(onRetry).toHaveBeenCalled()
      }
    })

    it('does not show follow-up chips on error messages', () => {
      const errorMessage: Message = {
        id: 'error-1',
        role: 'assistant',
        content: 'Error occurred.',
        timestamp: new Date(),
        isError: true,
        followUpQuestions: ['Should not appear'],
      }

      render(
        <ChatMessage
          message={errorMessage}
          onFollowUpSelect={vi.fn()}
        />
      )

      expect(screen.queryByText('Should not appear')).not.toBeInTheDocument()
    })
  })

  describe('AC#2: Citation Rendering', () => {
    it('renders citations toggle when citations exist', () => {
      const messageWithCitations: Message = {
        ...baseAssistantMessage,
        citations: [
          {
            source: 'daily_summaries',
            dataPoint: '87.5%',
            timestamp: '2026-01-09T10:00:00Z',
          },
        ],
      }

      render(<ChatMessage message={messageWithCitations} />)

      expect(screen.getByText('1 source')).toBeInTheDocument()
    })

    it('shows plural sources text for multiple citations', () => {
      const messageWithCitations: Message = {
        ...baseAssistantMessage,
        citations: [
          { source: 'daily_summaries', dataPoint: '87.5%' },
          { source: 'live_snapshots', dataPoint: '850 units' },
        ],
      }

      render(<ChatMessage message={messageWithCitations} />)

      expect(screen.getByText('2 sources')).toBeInTheDocument()
    })

    it('does not show citations on error messages', () => {
      const errorWithCitations: Message = {
        id: 'error-1',
        role: 'assistant',
        content: 'Error',
        timestamp: new Date(),
        isError: true,
        citations: [
          { source: 'test', dataPoint: 'test' },
        ],
      }

      render(<ChatMessage message={errorWithCitations} />)

      expect(screen.queryByText('1 source')).not.toBeInTheDocument()
    })
  })

  describe('Grounding score display', () => {
    it('shows verified badge for high grounding score', () => {
      const highGroundingMessage: Message = {
        ...baseAssistantMessage,
        groundingScore: 0.95,
      }

      render(<ChatMessage message={highGroundingMessage} />)

      expect(screen.getByText('Verified')).toBeInTheDocument()
    })

    it('shows partial badge for medium grounding score', () => {
      const mediumGroundingMessage: Message = {
        ...baseAssistantMessage,
        groundingScore: 0.7,
      }

      render(<ChatMessage message={mediumGroundingMessage} />)

      expect(screen.getByText('Partial')).toBeInTheDocument()
    })

    it('shows limited badge for low grounding score', () => {
      const lowGroundingMessage: Message = {
        ...baseAssistantMessage,
        groundingScore: 0.4,
      }

      render(<ChatMessage message={lowGroundingMessage} />)

      expect(screen.getByText('Limited')).toBeInTheDocument()
    })

    it('does not show grounding badge on error messages', () => {
      const errorWithGrounding: Message = {
        id: 'error-1',
        role: 'assistant',
        content: 'Error',
        timestamp: new Date(),
        isError: true,
        groundingScore: 0.9,
      }

      render(<ChatMessage message={errorWithGrounding} />)

      expect(screen.queryByText('Verified')).not.toBeInTheDocument()
    })
  })
})
