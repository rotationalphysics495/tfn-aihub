'use client'

/**
 * Message List Component
 *
 * Scrollable container for chat messages with auto-scroll to latest.
 * Uses Radix ScrollArea for consistent cross-browser scrolling.
 *
 * @see Story 4.3 - Chat Sidebar UI
 * @see Story 5.7 - Agent Chat Integration
 * @see AC #3 - Message Display (scrollable conversation view)
 */

import { useEffect, useRef } from 'react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { cn } from '@/lib/utils'
import { ChatMessage } from './ChatMessage'
import { ChatLoadingIndicator } from './ChatLoadingIndicator'
import type { Message } from './types'

interface MessageListProps {
  /** Array of messages to display */
  messages: Message[]
  /** Whether AI is currently generating a response */
  isLoading?: boolean
  /** Handler for follow-up chip selection (Story 5.7) */
  onFollowUpSelect?: (question: string) => void
  /** Handler for retry on error (Story 5.7) */
  onRetry?: (messageId: string) => void
  /** Optional custom class name */
  className?: string
}

/**
 * Scrollable message list with auto-scroll behavior.
 * Automatically scrolls to bottom when new messages arrive.
 *
 * Story 5.7: Passes through follow-up and retry handlers to messages.
 */
export function MessageList({
  messages,
  isLoading,
  onFollowUpSelect,
  onRetry,
  className,
}: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when messages change or loading state changes
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, isLoading])

  return (
    <ScrollArea className={cn('h-full', className)}>
      <div
        ref={containerRef}
        className="flex flex-col px-4 pb-4"
        role="log"
        aria-live="polite"
        aria-label="Chat messages"
      >
        {messages.length === 0 && !isLoading ? (
          <EmptyState />
        ) : (
          <>
            {messages.map((message) => (
              <ChatMessage
                key={message.id}
                message={message}
                onFollowUpSelect={onFollowUpSelect}
                onRetry={message.isError && onRetry ? () => onRetry(message.id) : undefined}
              />
            ))}

            {/* Loading indicator when AI is thinking */}
            {isLoading && <ChatLoadingIndicator />}
          </>
        )}

        {/* Invisible element for scroll-to-bottom behavior */}
        <div ref={bottomRef} aria-hidden="true" />
      </div>
    </ScrollArea>
  )
}

/**
 * Empty state shown when no messages exist.
 */
function EmptyState() {
  return (
    <div className="flex h-full flex-col items-center justify-center py-12 text-center">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-industrial-100 dark:bg-industrial-800">
        <span className="text-2xl font-semibold text-industrial-500 dark:text-industrial-400">
          AI
        </span>
      </div>
      <h3 className="mb-2 text-lg font-semibold text-foreground">
        Factory AI Assistant
      </h3>
      <p className="max-w-[280px] text-sm text-muted-foreground">
        Ask me about production metrics, equipment performance, downtime analysis,
        or any other factory data.
      </p>
    </div>
  )
}
