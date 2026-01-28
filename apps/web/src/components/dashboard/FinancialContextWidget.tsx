'use client'

import { cn } from '@/lib/utils'
import type { FinancialData } from '@/hooks/useLivePulse'

/**
 * Financial Context Widget Component
 *
 * Displays financial context for the Live Pulse ticker:
 * - Total Cost of Loss for current shift
 * - Rolling 15-minute financial impact
 * - Clear distinction between shift-to-date and rolling figures
 *
 * @see Story 2.9 - Live Pulse Ticker
 * @see AC #3 - Financial Context Integration
 * @see AC #7 - Industrial Clarity Compliance (24px+ for secondary values)
 */

interface FinancialContextWidgetProps {
  data: FinancialData | null
  isLoading?: boolean
  className?: string
}

/**
 * Format currency with proper dollar sign and commas
 */
function formatCurrency(value: number, currency: string = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

export function FinancialContextWidget({
  data,
  isLoading = false,
  className,
}: FinancialContextWidgetProps) {
  if (isLoading) {
    return (
      <div className={cn('animate-pulse', className)}>
        <div className="h-12 bg-live-surface/50 rounded-lg mb-3" />
        <div className="h-8 bg-live-surface/50 rounded-lg w-1/2" />
      </div>
    )
  }

  if (!data) {
    return (
      <div className={cn('text-muted-foreground', className)}>
        <p className="text-sm">No financial data available</p>
      </div>
    )
  }

  const { shift_to_date_loss, rolling_15_min_loss, currency } = data

  // Determine loss severity for color coding
  const getLossSeverity = (loss: number) => {
    if (loss >= 10000) return 'text-warning-amber-dark'
    if (loss >= 5000) return 'text-warning-amber'
    return 'text-foreground'
  }

  return (
    <div className={cn('space-y-4', className)}>
      {/* Header */}
      <div className="flex items-center gap-2">
        <svg
          className="w-5 h-5 text-live-primary"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          Cost of Loss
        </h3>
      </div>

      {/* Primary Metric: Shift-to-Date */}
      <div>
        <p className="text-xs uppercase tracking-wide text-muted-foreground mb-1">
          Shift-to-Date
        </p>
        <div className="flex items-baseline gap-1">
          <span className={cn(
            'text-2xl sm:text-3xl font-bold tabular-nums',
            getLossSeverity(shift_to_date_loss)
          )}>
            {formatCurrency(shift_to_date_loss, currency)}
          </span>
        </div>
        <p className="text-xs text-muted-foreground mt-1">
          Total financial impact this shift
        </p>
      </div>

      {/* Secondary Metric: Rolling 15-min */}
      <div className="border-t border-live-border dark:border-live-border-dark pt-4">
        <p className="text-xs uppercase tracking-wide text-muted-foreground mb-1">
          Rolling 15 Minutes
        </p>
        <div className="flex items-baseline gap-1">
          <span className={cn(
            'text-lg sm:text-xl font-semibold tabular-nums',
            getLossSeverity(rolling_15_min_loss)
          )}>
            {formatCurrency(rolling_15_min_loss, currency)}
          </span>
        </div>
        <p className="text-xs text-muted-foreground mt-1">
          Loss in last polling window
        </p>
      </div>

      {/* Loss Indicator Bar */}
      {shift_to_date_loss > 0 && (
        <div className="pt-2">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span className="inline-flex h-2 w-2 rounded-full bg-warning-amber animate-pulse" />
            <span>Losses accumulating</span>
          </div>
        </div>
      )}
    </div>
  )
}
