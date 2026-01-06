'use client'

import { cn } from '@/lib/utils'
import { Card, CardContent } from '@/components/ui/card'

/**
 * OEE Gauge Component
 *
 * Large numeric display for plant-wide OEE percentage.
 * Designed for "Industrial Clarity" - readable from 3 feet on tablet.
 *
 * @see Story 2.4 - OEE Metrics View
 * @see AC #3 - Plant-wide OEE prominently displayed
 * @see AC #9 - "Industrial Clarity" design - readable from 3 feet
 */

interface OEEGaugeProps {
  /** OEE percentage value (0-100) */
  value: number | null
  /** Target OEE percentage */
  target: number
  /** Status: green, yellow, red, or unknown */
  status: string
  /** Whether this is live (T-15m) or historical (T-1) data */
  isLive?: boolean
  /** Optional additional class names */
  className?: string
}

/**
 * Get the color classes based on OEE status.
 * Note: Uses standard colors, NOT Safety Red (reserved for incidents only)
 */
function getStatusColors(status: string): {
  text: string
  bg: string
  ring: string
} {
  switch (status) {
    case 'green':
      return {
        text: 'text-success-green',
        bg: 'bg-success-green-light dark:bg-success-green-dark/20',
        ring: 'ring-success-green/30',
      }
    case 'yellow':
      return {
        text: 'text-warning-amber',
        bg: 'bg-warning-amber-light dark:bg-warning-amber-dark/20',
        ring: 'ring-warning-amber/30',
      }
    case 'red':
      // Using standard red (red-500), NOT safety-red which is reserved for incidents
      return {
        text: 'text-red-500',
        bg: 'bg-red-50 dark:bg-red-900/20',
        ring: 'ring-red-500/30',
      }
    default:
      return {
        text: 'text-muted-foreground',
        bg: 'bg-muted',
        ring: 'ring-muted-foreground/30',
      }
  }
}

export function OEEGauge({
  value,
  target,
  status,
  isLive = false,
  className,
}: OEEGaugeProps) {
  const colors = getStatusColors(status)
  const displayValue = value !== null ? value.toFixed(1) : '--'
  const variance = value !== null ? value - target : null
  const varianceSign = variance !== null && variance >= 0 ? '+' : ''

  return (
    <Card
      mode={isLive ? 'live' : 'retrospective'}
      className={cn('relative overflow-hidden', className)}
    >
      <CardContent className="p-8">
        <div className="flex flex-col items-center text-center">
          {/* Main OEE Value */}
          <div
            className={cn(
              'relative flex items-center justify-center',
              'w-48 h-48 rounded-full ring-8',
              colors.bg,
              colors.ring,
              isLive && 'animate-live-pulse',
            )}
          >
            <div className="flex flex-col items-center">
              <span
                className={cn(
                  'metric-display',
                  colors.text,
                )}
              >
                {displayValue}
              </span>
              <span className="text-2xl font-bold text-muted-foreground">%</span>
            </div>
          </div>

          {/* Label */}
          <h3 className="mt-6 section-header text-foreground">
            Plant OEE
          </h3>
          <p className="mt-2 body-text text-muted-foreground">
            {isLive ? 'Live Pulse (T-15m)' : "Yesterday's Analysis (T-1)"}
          </p>

          {/* Target comparison */}
          <div className="mt-4 flex items-center gap-4">
            <div className="text-center">
              <p className="label-text text-muted-foreground">Target</p>
              <p className="text-xl font-semibold text-foreground">
                {target.toFixed(0)}%
              </p>
            </div>
            <div className="h-8 w-px bg-border" />
            <div className="text-center">
              <p className="label-text text-muted-foreground">Variance</p>
              <p
                className={cn(
                  'text-xl font-semibold',
                  variance !== null && variance >= 0
                    ? 'text-success-green'
                    : variance !== null
                      ? 'text-warning-amber'
                      : 'text-muted-foreground',
                )}
              >
                {variance !== null ? `${varianceSign}${variance.toFixed(1)}%` : '--'}
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
