'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

/**
 * Cost of Loss Widget Component
 *
 * Displays financial loss metrics for the current view period.
 * Shows total loss and breakdown by category (Downtime, Waste, OEE Loss).
 *
 * @see Story 2.8 - Cost of Loss Widget
 * @see AC #1 - Cost of Loss Widget Component
 * @see AC #5 - Industrial Clarity Design Compliance
 */

export interface CostOfLossData {
  total_loss: number
  breakdown: {
    downtime_cost: number
    waste_cost: number
    oee_loss_cost: number
  }
  period: 'daily' | 'live'
  last_updated: string
}

export interface CostOfLossWidgetProps {
  /** Period type for data display */
  period: 'daily' | 'live'
  /** Optional asset ID filter */
  assetId?: string
  /** Whether to show the breakdown section (default: true) */
  showBreakdown?: boolean
  /** Whether auto-refresh is enabled (default: true for 'live' period) */
  autoRefresh?: boolean
  /** Additional CSS classes for layout customization */
  className?: string
  /** Widget data from API */
  data?: CostOfLossData | null
  /** Loading state */
  isLoading?: boolean
  /** Error message */
  error?: string | null
  /** Last updated timestamp override (from parent component) */
  lastUpdated?: string | null
}

/**
 * Format currency value to USD with appropriate precision
 * Uses large format for total loss (no decimals for readability)
 * Uses decimals for breakdown items
 */
function formatCurrency(amount: number, includeDecimals = false): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: includeDecimals ? 2 : 0,
    maximumFractionDigits: includeDecimals ? 2 : 0,
  }).format(amount)
}

/**
 * Format timestamp for display
 */
function formatTimestamp(isoString: string): string {
  try {
    const date = new Date(isoString)
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    })
  } catch {
    return isoString
  }
}

/**
 * Loading skeleton component
 */
function LoadingSkeleton({ showBreakdown, className }: { showBreakdown: boolean; className?: string }) {
  return (
    <Card className={cn("animate-pulse", className)}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="h-6 w-32 bg-muted rounded" />
          <div className="h-5 w-16 bg-muted rounded" />
        </div>
      </CardHeader>
      <CardContent className="pt-4">
        {/* Total loss skeleton */}
        <div className="mb-6">
          <div className="h-4 w-20 bg-muted rounded mb-2" />
          <div className="h-12 w-40 bg-muted rounded" />
        </div>

        {/* Breakdown skeleton */}
        {showBreakdown && (
          <div className="grid grid-cols-3 gap-4 pt-4 border-t border-border">
            {[1, 2, 3].map((i) => (
              <div key={i} className="space-y-2">
                <div className="h-3 w-16 bg-muted rounded" />
                <div className="h-6 w-24 bg-muted rounded" />
              </div>
            ))}
          </div>
        )}

        {/* Footer skeleton */}
        <div className="mt-4 pt-4 border-t border-border">
          <div className="h-3 w-40 bg-muted rounded" />
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * Error state component
 */
function ErrorState({ error, onRetry }: { error: string; onRetry?: () => void }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg font-semibold">Cost of Loss</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col items-center justify-center py-8">
        <div className="text-center">
          <svg
            className="w-10 h-10 text-warning-amber mx-auto mb-3"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
          <p className="text-sm text-muted-foreground mb-3">{error}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="px-4 py-2 bg-primary text-primary-foreground text-sm rounded-md hover:bg-primary/90 transition-colors"
            >
              Try Again
            </button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * Empty state component
 */
function EmptyState({ period }: { period: 'daily' | 'live' }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold">Cost of Loss</CardTitle>
          <Badge variant={period === 'live' ? 'live' : 'retrospective'}>
            {period === 'live' ? (
              <>
                <span className="inline-flex h-2 w-2 rounded-full bg-live-pulse mr-1.5 animate-live-pulse" />
                Live
              </>
            ) : (
              'T-1'
            )}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="flex flex-col items-center justify-center py-8">
        <div className="text-center">
          <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center mx-auto mb-3">
            <svg
              className="w-6 h-6 text-muted-foreground"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <p className="text-sm text-muted-foreground">
            No financial data available for this period
          </p>
        </div>
      </CardContent>
    </Card>
  )
}

export function CostOfLossWidget({
  period,
  assetId,
  showBreakdown = true,
  autoRefresh = true,
  className,
  data,
  isLoading = false,
  error = null,
  lastUpdated,
}: CostOfLossWidgetProps) {
  // Loading state
  if (isLoading) {
    return <LoadingSkeleton showBreakdown={showBreakdown} className={className} />
  }

  // Error state
  if (error) {
    return <ErrorState error={error} />
  }

  // Empty state
  if (!data || data.total_loss === 0) {
    return <EmptyState period={period} />
  }

  const isLive = period === 'live'
  const displayLastUpdated = lastUpdated || data.last_updated

  return (
    <Card mode={isLive ? 'live' : 'retrospective'} className={cn('h-full', className)}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold">
            Cost of Loss
          </CardTitle>
          <Badge variant={isLive ? 'live' : 'retrospective'}>
            {isLive ? (
              <>
                <span className="inline-flex h-2 w-2 rounded-full bg-live-pulse mr-1.5 animate-live-pulse" />
                Live
              </>
            ) : (
              'T-1'
            )}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="pt-4">
        {/* Total Financial Loss - Primary Metric (AC #1, #5) */}
        {/* Large, bold typography for "glanceability" - readable from 3 feet */}
        <div className="mb-6">
          <div className="text-sm font-medium text-muted-foreground mb-1">
            Total Financial Impact
          </div>
          <div className="text-4xl font-bold text-warning-amber tracking-tight">
            {formatCurrency(data.total_loss)}
          </div>
          <div className="text-xs text-muted-foreground mt-1">
            {isLive ? 'Current shift accumulated' : "Yesterday's total"}
          </div>
        </div>

        {/* Breakdown by Category (AC #1) */}
        {showBreakdown && (
          <div className="grid grid-cols-3 gap-4 pt-4 border-t border-border">
            {/* Downtime Cost */}
            <div>
              <div className="text-xs font-medium text-muted-foreground mb-1">
                Downtime
              </div>
              <div className="text-lg font-semibold text-foreground">
                {formatCurrency(data.breakdown.downtime_cost, true)}
              </div>
            </div>

            {/* Waste/Scrap Cost */}
            <div>
              <div className="text-xs font-medium text-muted-foreground mb-1">
                Waste/Scrap
              </div>
              <div className="text-lg font-semibold text-foreground">
                {formatCurrency(data.breakdown.waste_cost, true)}
              </div>
            </div>

            {/* OEE Loss Cost */}
            <div>
              <div className="text-xs font-medium text-muted-foreground mb-1">
                OEE Loss
              </div>
              <div className="text-lg font-semibold text-foreground">
                {formatCurrency(data.breakdown.oee_loss_cost, true)}
              </div>
            </div>
          </div>
        )}

        {/* Last Updated Timestamp (AC #6) */}
        <div className="mt-4 pt-4 border-t border-border">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Last updated: {formatTimestamp(displayLastUpdated)}</span>
            {isLive && autoRefresh && (
              <span className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-live-pulse animate-live-pulse" />
                Auto-refresh
              </span>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
