'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { StatusBadge, type ThroughputStatus } from './StatusBadge'
import { cn } from '@/lib/utils'

/**
 * Throughput Card Component
 *
 * Displays throughput metrics for a single asset with actual vs target visualization.
 * Follows Industrial Clarity design for "glanceability" - readable from 3 feet away.
 *
 * @see Story 2.3 - AC #2 Actual vs Target Visualization
 * @see Story 2.3 - AC #3 Status Indicators
 */

export interface ThroughputCardData {
  id: string
  name: string
  area?: string | null
  actual_output: number
  target_output: number
  variance: number
  percentage: number
  status: ThroughputStatus
  snapshot_timestamp: string
}

interface ThroughputCardProps {
  data: ThroughputCardData
  className?: string
}

function formatNumber(num: number): string {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toLocaleString()
}

function getVarianceDisplay(variance: number): { text: string; isPositive: boolean } {
  const isPositive = variance >= 0
  const prefix = isPositive ? '+' : ''
  return {
    text: `${prefix}${formatNumber(variance)}`,
    isPositive,
  }
}

export function ThroughputCard({ data, className }: ThroughputCardProps) {
  const varianceDisplay = getVarianceDisplay(data.variance)

  return (
    <Card
      mode="live"
      className={cn(
        'h-full transition-all duration-200',
        'hover:shadow-lg hover:scale-[1.01]',
        className
      )}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <CardTitle className="text-lg font-semibold truncate" title={data.name}>
              {data.name}
            </CardTitle>
            {data.area && (
              <p className="text-sm text-muted-foreground mt-0.5 truncate" title={data.area}>
                {data.area}
              </p>
            )}
          </div>
          <StatusBadge status={data.status} size="md" />
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        {/* Main Metrics - Large for glanceability */}
        <div className="space-y-4">
          {/* Percentage Display - Primary metric */}
          <div className="text-center">
            <p
              className={cn(
                'text-5xl font-bold tracking-tight tabular-nums',
                data.status === 'on_target' && 'text-success-green-dark dark:text-success-green',
                data.status === 'behind' && 'text-warning-amber-dark dark:text-warning-amber',
                data.status === 'critical' && 'text-warning-amber-dark dark:text-warning-amber'
              )}
              aria-label={`${data.percentage.toFixed(1)} percent of target`}
            >
              {data.percentage.toFixed(1)}%
            </p>
            <p className="text-sm text-muted-foreground mt-1">of target</p>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-muted rounded-full h-3 overflow-hidden">
            <div
              className={cn(
                'h-full rounded-full transition-all duration-500',
                data.status === 'on_target' && 'bg-success-green',
                data.status === 'behind' && 'bg-warning-amber',
                data.status === 'critical' && 'bg-warning-amber-dark'
              )}
              style={{ width: `${Math.min(data.percentage, 100)}%` }}
              role="progressbar"
              aria-valuenow={data.percentage}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={`Progress: ${data.percentage.toFixed(1)}%`}
            />
          </div>

          {/* Actual vs Target Details */}
          <div className="grid grid-cols-2 gap-4 pt-2">
            <div className="text-center p-3 bg-muted/50 rounded-lg">
              <p className="text-2xl font-bold tabular-nums">
                {formatNumber(data.actual_output)}
              </p>
              <p className="text-xs text-muted-foreground uppercase tracking-wider mt-1">
                Actual
              </p>
            </div>
            <div className="text-center p-3 bg-muted/50 rounded-lg">
              <p className="text-2xl font-bold tabular-nums">
                {formatNumber(data.target_output)}
              </p>
              <p className="text-xs text-muted-foreground uppercase tracking-wider mt-1">
                Target
              </p>
            </div>
          </div>

          {/* Variance Display */}
          <div className="flex items-center justify-center gap-2 pt-1">
            <span
              className={cn(
                'text-lg font-semibold tabular-nums',
                varianceDisplay.isPositive
                  ? 'text-success-green-dark dark:text-success-green'
                  : 'text-warning-amber-dark dark:text-warning-amber'
              )}
            >
              {varianceDisplay.text}
            </span>
            <span className="text-sm text-muted-foreground">variance</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
