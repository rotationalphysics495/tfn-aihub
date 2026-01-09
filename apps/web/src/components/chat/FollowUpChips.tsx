'use client'

/**
 * Follow-Up Chips Component (Story 5.7)
 *
 * Renders suggested follow-up questions as clickable chips below agent responses.
 * Clicking a chip sends that question as the next message in the conversation.
 *
 * @see Story 5.7 - Agent Chat Integration
 * @see AC #3 - Follow-Up Question Chips
 */

import { ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface FollowUpChipsProps {
  /** Array of suggested follow-up questions */
  questions: string[]
  /** Handler called when a chip is clicked */
  onSelect: (question: string) => void
  /** Maximum number of chips to display (default 3) */
  maxChips?: number
  /** Optional custom class name */
  className?: string
}

/**
 * Follow-up question chips component.
 *
 * Story 5.7 AC#3:
 * - GIVEN the agent returns suggested follow-up questions
 * - WHEN the response is displayed
 * - THEN follow-ups appear as clickable chips below the response
 * - AND clicking a chip sends that question as the next message
 * - AND chips match the existing chat UI styling
 *
 * Features:
 * - Fade-in/slide-up animation on appear
 * - Maximum 3 chips displayed by default
 * - Minimum 44px touch target for mobile accessibility
 * - Industrial Clarity design system styling
 */
export function FollowUpChips({
  questions,
  onSelect,
  maxChips = 3,
  className,
}: FollowUpChipsProps) {
  // Don't render if no questions
  if (!questions || questions.length === 0) return null

  // Limit to max chips
  const displayQuestions = questions.slice(0, maxChips)

  return (
    <div
      className={cn(
        'flex flex-wrap gap-2 mt-3',
        // Animation on appear (Story 5.7 AC#3)
        'animate-in fade-in slide-in-from-bottom-2 duration-300',
        className
      )}
      role="group"
      aria-label="Suggested follow-up questions"
    >
      {displayQuestions.map((question, index) => (
        <Button
          key={`followup-${index}`}
          variant="outline"
          size="sm"
          onClick={() => onSelect(question)}
          className={cn(
            // Base styling
            'text-xs h-auto py-2 px-3',
            // Minimum touch target for mobile (44px)
            'min-h-[44px]',
            // Industrial Clarity design system colors
            'border-industrial-300 dark:border-industrial-600',
            'bg-industrial-50 dark:bg-industrial-800/50',
            'text-industrial-700 dark:text-industrial-200',
            // Hover states
            'hover:bg-info-blue/10 hover:border-info-blue',
            'hover:text-info-blue dark:hover:text-info-blue',
            // Focus states for accessibility
            'focus-visible:ring-2 focus-visible:ring-info-blue focus-visible:ring-offset-2',
            // Transition
            'transition-colors duration-150',
            // Allow text wrapping for longer questions
            'whitespace-normal text-left'
          )}
          aria-label={`Ask: ${question}`}
        >
          <span className="line-clamp-2 flex-1">{question}</span>
          <ChevronRight
            className="ml-1.5 h-3.5 w-3.5 flex-shrink-0"
            aria-hidden="true"
          />
        </Button>
      ))}
    </div>
  )
}
