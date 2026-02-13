'use client'

/**
 * SuggestedQuestions Component (Story 19.3)
 *
 * Renders 2-3 contextual follow-up question chips below the smart summary.
 * Replicates the FollowUpChips visual pattern from the chat domain.
 *
 * @see Story 19.3 - Context-Aware Follow-Up Suggestions
 * @see AC #1 - 2-3 contextual follow-up questions shown as clickable chips
 * @see AC #2 - Clicking chip opens chat with question pre-filled and sent
 * @see AC #3 - Suggestions update when report content changes
 */

import { useMemo } from 'react'
import { ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { generateSuggestions } from '@/lib/generateSuggestions'
import type { ActionItem } from '@/hooks/useDailyActions'

interface SuggestedQuestionsProps {
  actionItems: ActionItem[]
  summaryText: string
  reportDate: string
  onQuestionSelect: (question: string) => void
  className?: string
}

/**
 * Suggested follow-up question chips for the morning report.
 *
 * Uses useMemo to memoize generateSuggestions() output based on
 * actionItems, summaryText, and reportDate. Returns null when no
 * suggestions can be generated.
 */
export function SuggestedQuestions({
  actionItems,
  summaryText,
  reportDate,
  onQuestionSelect,
  className,
}: SuggestedQuestionsProps) {
  const suggestions = useMemo(
    () =>
      generateSuggestions({
        actions: actionItems,
        summaryText,
        reportDate,
      }),
    [actionItems, summaryText, reportDate]
  )

  if (suggestions.length === 0) {
    return null
  }

  return (
    <div
      className={cn(
        'flex flex-wrap gap-2 mt-3',
        'animate-in fade-in slide-in-from-bottom-2 duration-300',
        className
      )}
      role="group"
      aria-label="Suggested follow-up questions about the morning report"
    >
      {suggestions.map((question, index) => (
        <Button
          key={`suggestion-${index}`}
          variant="outline"
          size="sm"
          onClick={() => onQuestionSelect(question)}
          className={cn(
            'text-xs h-auto py-2 px-3',
            'min-h-[44px]',
            'border-industrial-300 dark:border-industrial-600',
            'bg-industrial-50 dark:bg-industrial-800/50',
            'text-industrial-700 dark:text-industrial-200',
            'hover:bg-info-blue/10 hover:border-info-blue',
            'hover:text-info-blue dark:hover:text-info-blue',
            'focus-visible:ring-2 focus-visible:ring-info-blue focus-visible:ring-offset-2',
            'transition-colors duration-150',
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
