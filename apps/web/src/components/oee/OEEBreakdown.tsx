'use client'

import { cn } from '@/lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

/**
 * OEE Breakdown Component
 *
 * Displays the three OEE components: Availability, Performance, Quality.
 * Shows how each contributes to overall OEE.
 *
 * @see Story 2.4 - OEE Metrics View
 * @see AC #1 - OEE displays three core components
 * @see AC #4 - Individual asset OEE breakdown showing each component's contribution
 */

interface OEEBreakdownProps {
  /** Availability percentage */
  availability: number | null
  /** Performance percentage */
  performance: number | null
  /** Quality percentage */
  quality: number | null
  /** Whether this is live (T-15m) or historical (T-1) data */
  isLive?: boolean
  /** Optional additional class names */
  className?: string
}

interface ComponentBarProps {
  label: string
  value: number | null
  description: string
  color: string
  bgColor: string
}

function ComponentBar({ label, value, description, color, bgColor }: ComponentBarProps) {
  const displayValue = value !== null ? value.toFixed(1) : '--'
  const barWidth = value !== null ? Math.min(value, 100) : 0

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div>
          <p className="card-title text-foreground">{label}</p>
          <p className="text-sm text-muted-foreground">{description}</p>
        </div>
        <span className={cn('text-3xl font-bold tabular-nums', color)}>
          {displayValue}%
        </span>
      </div>

      {/* Progress bar */}
      <div className={cn('h-4 rounded-full overflow-hidden', bgColor)}>
        <div
          className={cn('h-full rounded-full transition-all duration-500 ease-out', color.replace('text-', 'bg-'))}
          style={{ width: `${barWidth}%` }}
        />
      </div>

      {/* Reference markers */}
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>0%</span>
        <span className="text-warning-amber">70%</span>
        <span className="text-success-green">85%</span>
        <span>100%</span>
      </div>
    </div>
  )
}

/**
 * Get color based on component value.
 * Uses standard status colors (not Safety Red).
 */
function getComponentColor(value: number | null): { text: string; bg: string } {
  if (value === null) {
    return { text: 'text-muted-foreground', bg: 'bg-muted' }
  }

  if (value >= 95) {
    return { text: 'text-success-green', bg: 'bg-success-green-light dark:bg-success-green-dark/20' }
  } else if (value >= 85) {
    return { text: 'text-success-green', bg: 'bg-success-green-light dark:bg-success-green-dark/20' }
  } else if (value >= 70) {
    return { text: 'text-warning-amber', bg: 'bg-warning-amber-light dark:bg-warning-amber-dark/20' }
  } else {
    // Use standard red, not safety-red
    return { text: 'text-red-500', bg: 'bg-red-50 dark:bg-red-900/20' }
  }
}

export function OEEBreakdown({
  availability,
  performance,
  quality,
  isLive = false,
  className,
}: OEEBreakdownProps) {
  const availColors = getComponentColor(availability)
  const perfColors = getComponentColor(performance)
  const qualColors = getComponentColor(quality)

  return (
    <Card
      mode={isLive ? 'live' : 'retrospective'}
      className={cn('', className)}
    >
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <svg
            className="w-5 h-5 text-muted-foreground"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
          OEE Components
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-8">
        <ComponentBar
          label="Availability"
          value={availability}
          description="Run Time / Planned Production Time"
          color={availColors.text}
          bgColor={availColors.bg}
        />

        <ComponentBar
          label="Performance"
          value={performance}
          description="Actual Output / Target Output"
          color={perfColors.text}
          bgColor={perfColors.bg}
        />

        <ComponentBar
          label="Quality"
          value={quality}
          description="Good Units / Total Units"
          color={qualColors.text}
          bgColor={qualColors.bg}
        />

        {/* Formula reference */}
        <div className="pt-4 border-t border-border">
          <p className="text-sm text-muted-foreground text-center">
            <span className="font-medium">OEE = Availability</span> x{' '}
            <span className="font-medium">Performance</span> x{' '}
            <span className="font-medium">Quality</span>
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
