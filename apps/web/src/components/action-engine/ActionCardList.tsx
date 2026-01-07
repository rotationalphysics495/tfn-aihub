'use client'

import { useMemo } from 'react'
import { RefreshCw, AlertCircle, CheckCircle2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { InsightEvidenceCard, InsightEvidenceCardSkeleton } from './InsightEvidenceCard'
import type { ActionItem } from './types'
import type { PriorityType } from './PriorityBadge'

/**
 * Action Card List Container Component
 *
 * Container component that manages the list of Insight + Evidence cards.
 * Handles sorting by priority, loading states, error states, and empty states.
 *
 * Features:
 * - Consumes action items from Daily Action List API
 * - Sorts by priority: Safety > Financial ($) > OEE
 * - Loading state with skeleton cards
 * - Error state with retry option
 * - Empty state ("All systems operating normally")
 *
 * @see Story 3.4 - Insight + Evidence Cards
 * @see AC #4 - Cards sorted by priority
 * @see AC #5 - Data Source Integration
 */

interface ActionCardListProps {
  items: ActionItem[]
  isLoading?: boolean
  error?: string | null
  onRefetch?: () => void
  className?: string
}

// Priority order for sorting (lower number = higher priority)
const PRIORITY_ORDER: Record<PriorityType, number> = {
  SAFETY: 0,
  FINANCIAL: 1,
  OEE: 2,
}

/**
 * Sort action items by priority
 * Safety first, then Financial Impact ($), then OEE deviation
 */
function sortByPriority(items: ActionItem[]): ActionItem[] {
  return [...items].sort((a, b) => {
    // First sort by priority type
    const priorityDiff = PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority]
    if (priorityDiff !== 0) return priorityDiff

    // Within same priority type, sort by priorityScore (descending)
    return b.priorityScore - a.priorityScore
  })
}

/**
 * Loading State Component
 */
function LoadingState({ count = 3 }: { count?: number }) {
  return (
    <div
      className="space-y-4"
      role="status"
      aria-label="Loading action items"
    >
      {Array.from({ length: count }).map((_, index) => (
        <InsightEvidenceCardSkeleton key={index} />
      ))}
      <span className="sr-only">Loading action items...</span>
    </div>
  )
}

/**
 * Error State Component
 */
function ErrorState({
  error,
  onRetry,
}: {
  error: string
  onRetry?: () => void
}) {
  return (
    <div className="rounded-lg border border-warning-amber/30 bg-warning-amber-light/10 dark:bg-warning-amber-dark/10 p-6 md:p-8">
      <div className="flex flex-col items-center text-center">
        <AlertCircle
          className="w-12 h-12 text-warning-amber mb-4"
          aria-hidden="true"
        />
        <h3 className="text-xl font-semibold text-foreground mb-2">
          Unable to Load Action Items
        </h3>
        <p className="text-base text-muted-foreground mb-4 max-w-md">
          {error}
        </p>
        {onRetry && (
          <Button onClick={onRetry} variant="outline" className="gap-2">
            <RefreshCw className="w-4 h-4" aria-hidden="true" />
            Try Again
          </Button>
        )}
      </div>
    </div>
  )
}

/**
 * Empty State Component
 * Displays when there are no action items (all systems operating normally)
 */
function EmptyState() {
  return (
    <div className="rounded-lg border border-success-green/30 bg-success-green-light/10 dark:bg-success-green-dark/10 p-6 md:p-8">
      <div className="flex flex-col items-center text-center">
        <CheckCircle2
          className="w-12 h-12 text-success-green mb-4"
          aria-hidden="true"
        />
        <h3 className="text-xl font-semibold text-foreground mb-2">
          All Systems Operating Normally
        </h3>
        <p className="text-base text-muted-foreground max-w-md">
          No immediate actions required. All performance metrics are within
          acceptable thresholds. Continue monitoring the Live Pulse view for
          real-time updates.
        </p>
        <div className="mt-4 text-sm text-muted-foreground">
          <p>Actions appear when:</p>
          <ul className="list-disc list-inside mt-2 text-left">
            <li>Safety events are detected</li>
            <li>OEE falls below target threshold</li>
            <li>Significant financial impact is identified</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

export function ActionCardList({
  items,
  isLoading = false,
  error = null,
  onRefetch,
  className,
}: ActionCardListProps) {
  // Sort items by priority (AC #4)
  const sortedItems = useMemo(() => sortByPriority(items), [items])

  // Loading state (AC #5 - Handle loading state)
  if (isLoading && items.length === 0) {
    return (
      <div className={cn('', className)}>
        <LoadingState count={3} />
      </div>
    )
  }

  // Error state (AC #5 - Handle error state)
  if (error) {
    return (
      <div className={cn('', className)}>
        <ErrorState error={error} onRetry={onRefetch} />
      </div>
    )
  }

  // Empty state (AC #5 - Handle empty state)
  if (sortedItems.length === 0) {
    return (
      <div className={cn('', className)}>
        <EmptyState />
      </div>
    )
  }

  // Render sorted cards
  return (
    <div className={cn('space-y-4', className)}>
      {/* Refresh button */}
      {onRefetch && (
        <div className="flex justify-end">
          <Button
            variant="ghost"
            size="sm"
            onClick={onRefetch}
            disabled={isLoading}
            className="gap-2 text-muted-foreground hover:text-foreground"
          >
            <RefreshCw
              className={cn('w-4 h-4', isLoading && 'animate-spin')}
              aria-hidden="true"
            />
            Refresh
          </Button>
        </div>
      )}

      {/* Action cards */}
      <div className="space-y-4" role="list" aria-label="Action items">
        {sortedItems.map((item) => (
          <div key={item.id} role="listitem">
            <InsightEvidenceCard item={item} />
          </div>
        ))}
      </div>

      {/* Loading overlay for refetch */}
      {isLoading && items.length > 0 && (
        <div className="fixed inset-0 bg-background/50 flex items-center justify-center z-50">
          <div className="flex items-center gap-2 bg-card px-4 py-2 rounded-lg shadow-lg">
            <RefreshCw className="w-4 h-4 animate-spin" aria-hidden="true" />
            <span className="text-sm">Refreshing...</span>
          </div>
        </div>
      )}
    </div>
  )
}

/**
 * @deprecated Use InsightEvidenceCardList instead which properly integrates
 * with useDailyActions hook and transforms data automatically.
 * @see InsightEvidenceCardList
 */
export function ActionCardListWithData({ className }: { className?: string }) {
  console.warn(
    'ActionCardListWithData is deprecated. Use InsightEvidenceCardList instead.'
  )
  return (
    <div className={className}>
      <p className="text-warning-amber text-center py-8">
        This component is deprecated. Use InsightEvidenceCardList instead.
      </p>
    </div>
  )
}
