'use client'

import { RefreshCw, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useDailyActions } from '@/hooks/useDailyActions'
import { ActionItemCard } from './ActionItemCard'
import { ActionListSkeleton } from './ActionListSkeleton'
import { EmptyActionState } from './EmptyActionState'
import { cn } from '@/lib/utils'

/**
 * Action List Container Component
 *
 * Container component that handles data fetching and rendering of action items.
 *
 * @see Story 3.3 - Action List Primary View
 * @see AC #2 - Action First Layout Structure
 * @see AC #5 - Data Integration with Action Engine API
 */

interface ActionListContainerProps {
  className?: string
}

export function ActionListContainer({ className }: ActionListContainerProps) {
  const {
    data,
    isLoading,
    error,
    refetch,
    hasActions,
  } = useDailyActions()

  // Loading state - AC #5
  if (isLoading && !data) {
    return (
      <div className={cn('', className)}>
        <ActionListSkeleton count={3} />
      </div>
    )
  }

  // Error state with retry - AC #5
  if (error) {
    return (
      <div className={cn('', className)}>
        <div className="rounded-lg border border-warning-amber/30 bg-warning-amber-light/10 dark:bg-warning-amber-dark/10 p-6 md:p-8">
          <div className="flex flex-col items-center text-center">
            <AlertCircle
              className="w-12 h-12 text-warning-amber mb-4"
              aria-hidden="true"
            />
            <h3 className="text-xl font-semibold text-foreground mb-2">
              Unable to Load Actions
            </h3>
            <p className="text-base text-muted-foreground mb-4 max-w-md">
              {error}
            </p>
            <Button
              onClick={() => refetch()}
              variant="outline"
              className="gap-2"
            >
              <RefreshCw className="w-4 h-4" aria-hidden="true" />
              Try Again
            </Button>
          </div>
        </div>
      </div>
    )
  }

  // Empty state - AC #5
  if (!hasActions) {
    return (
      <div className={cn('', className)}>
        <EmptyActionState />
      </div>
    )
  }

  // Action items list - AC #2, #4
  const actions = data?.actions ?? []

  return (
    <div className={cn('space-y-4', className)}>
      {/* Refresh button */}
      <div className="flex justify-end">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => refetch()}
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

      {/* Action cards - sorted by priority (AC #4) */}
      <div className="space-y-4" role="list" aria-label="Action items">
        {actions.map((action, index) => (
          <ActionItemCard
            key={action.id}
            action={action}
            rank={index + 1}
          />
        ))}
      </div>

      {/* Loading overlay for refetch */}
      {isLoading && data && (
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
