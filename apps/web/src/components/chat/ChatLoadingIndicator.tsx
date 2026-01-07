'use client'

/**
 * Chat Loading Indicator Component
 *
 * Displays animated feedback while AI responses are being generated.
 * Uses subtle, professional styling appropriate for factory floor use.
 *
 * @see Story 4.3 - Chat Sidebar UI
 * @see AC #5 - Loading States
 */

import { cn } from '@/lib/utils'

interface ChatLoadingIndicatorProps {
  /** Optional custom class name */
  className?: string
}

/**
 * Animated "thinking" indicator for AI response generation.
 * Shows three pulsing dots to indicate processing.
 */
export function ChatLoadingIndicator({ className }: ChatLoadingIndicatorProps) {
  return (
    <div
      className={cn('flex items-start gap-3 py-4', className)}
      role="status"
      aria-label="AI is thinking"
    >
      {/* AI avatar placeholder */}
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-industrial-200 dark:bg-industrial-700">
        <span className="text-xs font-semibold text-industrial-600 dark:text-industrial-300">
          AI
        </span>
      </div>

      {/* Thinking indicator with animated dots */}
      <div className="flex items-center gap-1 rounded-lg bg-industrial-100 px-4 py-3 dark:bg-industrial-800">
        <span className="sr-only">Thinking</span>
        <span
          className="h-2 w-2 animate-bounce rounded-full bg-industrial-400"
          style={{ animationDelay: '0ms' }}
        />
        <span
          className="h-2 w-2 animate-bounce rounded-full bg-industrial-400"
          style={{ animationDelay: '150ms' }}
        />
        <span
          className="h-2 w-2 animate-bounce rounded-full bg-industrial-400"
          style={{ animationDelay: '300ms' }}
        />
      </div>
    </div>
  )
}
