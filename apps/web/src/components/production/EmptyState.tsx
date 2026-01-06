'use client'

import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'

/**
 * Empty State Component for Throughput Dashboard
 *
 * Displays a meaningful message when no throughput data is available.
 *
 * @see Story 2.3 - AC #7 Empty State Handling
 */

interface EmptyStateProps {
  className?: string
}

export function EmptyState({ className }: EmptyStateProps) {
  return (
    <Card mode="live" className={cn('min-h-[300px]', className)}>
      <CardContent className="flex flex-col items-center justify-center py-16 px-4">
        <div className="flex flex-col items-center gap-6 text-center max-w-md">
          {/* Icon */}
          <div className="w-16 h-16 rounded-full bg-live-surface dark:bg-live-surface-dark border border-live-border dark:border-live-border-dark flex items-center justify-center">
            <svg
              className="w-8 h-8 text-live-primary"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
          </div>

          {/* Message */}
          <div>
            <h3 className="text-xl font-semibold text-foreground mb-2">
              No Throughput Data Available
            </h3>
            <p className="text-base text-muted-foreground">
              Waiting for Live Pulse data. The pipeline runs every 15 minutes to collect
              production metrics from your manufacturing systems.
            </p>
          </div>

          {/* Live indicator */}
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span
              className="inline-flex h-2 w-2 rounded-full bg-live-primary animate-live-pulse"
              aria-label="Waiting for data"
            />
            <span>Monitoring for incoming data...</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
