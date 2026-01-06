'use client'

import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'

/**
 * Action List Loading Skeleton
 *
 * Displays skeleton placeholders while fetching action items.
 *
 * @see Story 3.3 - Action List Primary View
 * @see AC #5 - Displays loading skeleton while fetching action items
 * @see AC #10 - Initial page render (with loading state) within 500ms
 */

interface ActionListSkeletonProps {
  count?: number
  className?: string
}

function SkeletonPulse({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        'animate-pulse bg-industrial-200 dark:bg-industrial-700 rounded',
        className
      )}
    />
  )
}

function ActionCardSkeleton() {
  return (
    <Card mode="retrospective" className="border-l-4 border-l-industrial-300 dark:border-l-industrial-600">
      <CardContent className="p-4 md:p-6">
        <div className="flex items-start gap-4">
          {/* Rank indicator skeleton */}
          <SkeletonPulse className="w-10 h-10 rounded-full flex-shrink-0" />

          {/* Main content skeleton */}
          <div className="flex-1 min-w-0">
            {/* Header row */}
            <div className="flex items-center gap-2 mb-2">
              <SkeletonPulse className="w-5 h-5" />
              <SkeletonPulse className="w-20 h-5" />
              <SkeletonPulse className="w-24 h-4" />
            </div>

            {/* Title skeleton */}
            <SkeletonPulse className="h-7 w-full mb-2" />
            <SkeletonPulse className="h-7 w-3/4 mb-2" />

            {/* Description skeleton */}
            <SkeletonPulse className="h-5 w-full mb-3" />

            {/* Metrics row skeleton */}
            <div className="flex items-center gap-3">
              <SkeletonPulse className="w-24 h-4" />
              <SkeletonPulse className="w-20 h-4" />
              <SkeletonPulse className="w-28 h-5" />
            </div>
          </div>

          {/* Chevron skeleton */}
          <SkeletonPulse className="w-6 h-6 flex-shrink-0" />
        </div>
      </CardContent>
    </Card>
  )
}

export function ActionListSkeleton({ count = 3, className }: ActionListSkeletonProps) {
  return (
    <div className={cn('space-y-4', className)} aria-label="Loading action items" role="status">
      {Array.from({ length: count }).map((_, index) => (
        <ActionCardSkeleton key={index} />
      ))}
      <span className="sr-only">Loading action items...</span>
    </div>
  )
}

/**
 * Summary Section Skeleton
 */
export function SummarySkeleton({ className }: { className?: string }) {
  return (
    <Card mode="retrospective" className={cn('', className)}>
      <CardContent className="p-4 md:p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          {/* Date and title skeleton */}
          <div className="space-y-2">
            <SkeletonPulse className="h-5 w-48" />
            <SkeletonPulse className="h-8 w-64" />
          </div>

          {/* Metrics skeleton */}
          <div className="flex flex-wrap gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="text-center">
                <SkeletonPulse className="h-10 w-20 mb-1" />
                <SkeletonPulse className="h-4 w-16 mx-auto" />
              </div>
            ))}
          </div>
        </div>

        {/* AI summary placeholder skeleton */}
        <div className="mt-4 pt-4 border-t border-retrospective-border dark:border-retrospective-border-dark">
          <SkeletonPulse className="h-4 w-32 mb-2" />
          <SkeletonPulse className="h-4 w-full" />
          <SkeletonPulse className="h-4 w-5/6 mt-1" />
        </div>
      </CardContent>
    </Card>
  )
}
