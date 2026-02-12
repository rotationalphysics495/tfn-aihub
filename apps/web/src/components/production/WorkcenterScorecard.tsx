'use client'

import { RefreshCw, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { useWorkcenterSummary } from '@/hooks/useWorkcenterSummary'
import { WorkcenterRow } from './WorkcenterRow'

interface WorkcenterScorecardProps {
  className?: string
  date?: string
}

export function WorkcenterScorecard({ className, date }: WorkcenterScorecardProps) {
  const { data, isLoading, error, refetch } = useWorkcenterSummary(date ? { date } : {})

  // Loading state
  if (isLoading && !data) {
    return (
      <div className={cn('', className)}>
        <h2 className="section-header text-foreground mb-4">
          Production Scorecard
        </h2>
        <div className="space-y-4">
          {[1, 2, 3].map(i => (
            <div
              key={i}
              className="animate-pulse border rounded-lg p-4 md:p-6"
            >
              <div className="flex items-center justify-between">
                <div className="space-y-2">
                  <div className="h-5 w-32 bg-muted rounded" />
                  <div className="h-4 w-24 bg-muted rounded" />
                </div>
                <div className="h-10 w-20 bg-muted rounded" />
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className={cn('', className)}>
        <h2 className="section-header text-foreground mb-4">
          Production Scorecard
        </h2>
        <div className="rounded-lg border border-warning-amber/30 bg-warning-amber-light/10 dark:bg-warning-amber-dark/10 p-6 md:p-8">
          <div className="flex flex-col items-center text-center">
            <AlertCircle
              className="w-12 h-12 text-warning-amber mb-4"
              aria-hidden="true"
            />
            <p className="text-base text-muted-foreground mb-4">
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

  // Empty state
  if (data && data.workcenters.length === 0) {
    return (
      <div className={cn('', className)}>
        <h2 className="section-header text-foreground mb-4">
          Production Scorecard
        </h2>
        <div className="rounded-lg border p-6 md:p-8 text-center">
          <p className="text-base text-muted-foreground">
            {data.message || 'No production data available for this date.'}
          </p>
        </div>
      </div>
    )
  }

  // Success state
  const workcenters = data?.workcenters ?? []

  return (
    <div className={cn('', className)}>
      <h2 className="section-header text-foreground mb-4">
        Production Scorecard
      </h2>
      <div className="space-y-4">
        {workcenters.map(entry => (
          <WorkcenterRow key={entry.workcenter_name} entry={entry} />
        ))}
      </div>
    </div>
  )
}
