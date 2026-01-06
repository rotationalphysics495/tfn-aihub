'use client'

import { cn } from '@/lib/utils'
import type { ProductionData, ActiveDowntime } from '@/hooks/useLivePulse'

/**
 * Production Status Metric Component
 *
 * Displays production metrics for the Live Pulse ticker:
 * - Throughput vs target (percentage + absolute)
 * - OEE percentage
 * - Machine status breakdown (running/idle/down)
 * - Active downtime events with reason codes
 *
 * @see Story 2.9 - Live Pulse Ticker
 * @see AC #2 - Production Status Display
 * @see AC #7 - Industrial Clarity Compliance (48px+ primary metrics)
 */

interface ProductionStatusMetricProps {
  data: ProductionData | null
  isLoading?: boolean
  className?: string
}

export function ProductionStatusMetric({
  data,
  isLoading = false,
  className,
}: ProductionStatusMetricProps) {
  if (isLoading) {
    return (
      <div className={cn('animate-pulse', className)}>
        <div className="h-16 bg-live-surface/50 rounded-lg mb-3" />
        <div className="h-8 bg-live-surface/50 rounded-lg w-2/3" />
      </div>
    )
  }

  if (!data) {
    return (
      <div className={cn('text-muted-foreground', className)}>
        <p className="text-sm">No production data available</p>
      </div>
    )
  }

  const { current_output, target_output, output_percentage, oee_percentage, machine_status, active_downtime } = data

  // Determine throughput status color
  const getThroughputStatus = () => {
    if (output_percentage >= 100) return { color: 'text-success-green', label: 'On Target' }
    if (output_percentage >= 90) return { color: 'text-warning-amber', label: 'Behind' }
    return { color: 'text-warning-amber-dark', label: 'Critical' }
  }

  const throughputStatus = getThroughputStatus()

  // Determine OEE status color
  const getOeeStatus = () => {
    if (oee_percentage >= 85) return 'text-success-green'
    if (oee_percentage >= 70) return 'text-warning-amber'
    return 'text-warning-amber-dark'
  }

  return (
    <div className={cn('space-y-4', className)}>
      {/* Primary Metrics Row - Large Text for Glanceability */}
      <div className="grid grid-cols-2 gap-4">
        {/* Throughput */}
        <div>
          <p className="text-xs uppercase tracking-wide text-muted-foreground mb-1">
            Throughput
          </p>
          <div className="flex items-baseline gap-2">
            <span className={cn('text-4xl font-bold tabular-nums', throughputStatus.color)}>
              {output_percentage.toFixed(0)}%
            </span>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            {current_output.toLocaleString()} / {target_output.toLocaleString()} units
          </p>
        </div>

        {/* OEE */}
        <div>
          <p className="text-xs uppercase tracking-wide text-muted-foreground mb-1">
            OEE
          </p>
          <div className="flex items-baseline gap-2">
            <span className={cn('text-4xl font-bold tabular-nums', getOeeStatus())}>
              {oee_percentage.toFixed(1)}%
            </span>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Current efficiency
          </p>
        </div>
      </div>

      {/* Machine Status */}
      <div className="border-t border-live-border dark:border-live-border-dark pt-4">
        <p className="text-xs uppercase tracking-wide text-muted-foreground mb-2">
          Machine Status
        </p>
        <div className="flex gap-4">
          {/* Running */}
          <div className="flex items-center gap-2">
            <span className="inline-flex h-3 w-3 rounded-full bg-success-green" />
            <span className="text-xl font-semibold tabular-nums">
              {machine_status.running}
            </span>
            <span className="text-sm text-muted-foreground">Running</span>
          </div>

          {/* Idle */}
          <div className="flex items-center gap-2">
            <span className="inline-flex h-3 w-3 rounded-full bg-warning-amber" />
            <span className="text-xl font-semibold tabular-nums">
              {machine_status.idle}
            </span>
            <span className="text-sm text-muted-foreground">Idle</span>
          </div>

          {/* Down */}
          <div className="flex items-center gap-2">
            <span className="inline-flex h-3 w-3 rounded-full bg-industrial-400" />
            <span className="text-xl font-semibold tabular-nums">
              {machine_status.down}
            </span>
            <span className="text-sm text-muted-foreground">Down</span>
          </div>
        </div>
        <p className="text-xs text-muted-foreground mt-1">
          {machine_status.total} total machines
        </p>
      </div>

      {/* Active Downtime Events */}
      {active_downtime.length > 0 && (
        <div className="border-t border-live-border dark:border-live-border-dark pt-4">
          <p className="text-xs uppercase tracking-wide text-muted-foreground mb-2">
            Active Downtime
          </p>
          <ul className="space-y-2">
            {active_downtime.slice(0, 3).map((event, index) => (
              <li
                key={`${event.asset_name}-${index}`}
                className="flex items-center justify-between text-sm bg-warning-amber-light dark:bg-warning-amber-dark/20 px-3 py-2 rounded-md"
              >
                <span className="font-medium">{event.asset_name}</span>
                <span className="text-muted-foreground">
                  {event.reason_code} ({event.duration_minutes} min)
                </span>
              </li>
            ))}
          </ul>
          {active_downtime.length > 3 && (
            <p className="text-xs text-muted-foreground mt-2">
              +{active_downtime.length - 3} more downtime events
            </p>
          )}
        </div>
      )}
    </div>
  )
}
