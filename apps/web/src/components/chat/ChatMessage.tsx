'use client'

/**
 * Chat Message Component
 *
 * Renders individual chat messages with distinct styling for user vs AI.
 * Includes collapsible citation display for AI responses.
 *
 * @see Story 4.3 - Chat Sidebar UI
 * @see AC #3 - Message Display (clear visual distinction)
 * @see AC #6 - Citation Display (structured evidence area)
 */

import { useState } from 'react'
import { ChevronDown, ChevronUp, Database } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import type { Message, Citation } from './types'

interface ChatMessageProps {
  /** The message to display */
  message: Message
  /** Optional custom class name */
  className?: string
}

/**
 * Individual chat message bubble with role-based styling.
 * - User messages: right-aligned, info-blue background
 * - AI messages: left-aligned, industrial-gray background with citations
 */
export function ChatMessage({ message, className }: ChatMessageProps) {
  const [showCitations, setShowCitations] = useState(false)
  const isUser = message.role === 'user'
  const hasCitations = message.citations && message.citations.length > 0

  return (
    <div
      className={cn(
        'flex w-full gap-3 py-2',
        isUser ? 'flex-row-reverse' : 'flex-row',
        className
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'flex h-8 w-8 shrink-0 items-center justify-center rounded-full',
          isUser
            ? 'bg-info-blue text-white'
            : 'bg-industrial-200 dark:bg-industrial-700'
        )}
      >
        <span
          className={cn(
            'text-xs font-semibold',
            isUser
              ? 'text-white'
              : 'text-industrial-600 dark:text-industrial-300'
          )}
        >
          {isUser ? 'You' : 'AI'}
        </span>
      </div>

      {/* Message content */}
      <div
        className={cn(
          'flex max-w-[80%] flex-col gap-1',
          isUser ? 'items-end' : 'items-start'
        )}
      >
        {/* Message bubble */}
        <div
          className={cn(
            'rounded-lg px-4 py-3 text-base leading-relaxed',
            isUser
              ? 'bg-info-blue text-white'
              : 'bg-industrial-100 text-industrial-900 dark:bg-industrial-800 dark:text-industrial-100'
          )}
        >
          {message.content}
        </div>

        {/* Citations section for AI messages */}
        {!isUser && hasCitations && (
          <div className="w-full">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowCitations(!showCitations)}
              className="h-auto gap-1 px-2 py-1 text-xs text-muted-foreground hover:text-foreground"
              aria-expanded={showCitations}
              aria-controls={`citations-${message.id}`}
            >
              <Database className="h-3 w-3" />
              <span>
                {message.citations!.length} source
                {message.citations!.length !== 1 ? 's' : ''}
              </span>
              {showCitations ? (
                <ChevronUp className="h-3 w-3" />
              ) : (
                <ChevronDown className="h-3 w-3" />
              )}
            </Button>

            {/* Collapsible citations list */}
            {showCitations && (
              <div
                id={`citations-${message.id}`}
                className="mt-2 rounded-md border border-industrial-200 bg-industrial-50 p-3 dark:border-industrial-700 dark:bg-industrial-900"
                role="region"
                aria-label="Data sources"
              >
                <ul className="space-y-2">
                  {message.citations!.map((citation, index) => (
                    <CitationItem key={index} citation={citation} />
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Timestamp */}
        <span className="text-xs text-muted-foreground">
          {formatTime(message.timestamp)}
        </span>
      </div>
    </div>
  )
}

/**
 * Individual citation display within AI messages.
 */
function CitationItem({ citation }: { citation: Citation }) {
  return (
    <li className="flex flex-col gap-0.5 text-sm">
      <span className="font-medium text-industrial-700 dark:text-industrial-300">
        {citation.dataPoint}
      </span>
      <span className="text-xs text-muted-foreground">
        {citation.source}
        {citation.timestamp && ` • ${citation.timestamp}`}
      </span>
    </li>
  )
}

/**
 * Format timestamp for display.
 * Shows relative time for recent messages, otherwise HH:MM.
 */
function formatTime(date: Date): string {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / (1000 * 60))

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`

  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
