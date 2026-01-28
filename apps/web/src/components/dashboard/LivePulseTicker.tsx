'use client'

import { useCallback } from 'react'
import { cn } from '@/lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useLivePulse } from '@/hooks/useLivePulse'
import { ProductionStatusMetric } from './ProductionStatusMetric'
import { FinancialContextWidget } from './FinancialContextWidget'
import { LivePulseSafetyIndicator } from './LivePulseSafetyIndicator'

/**
 * LivePulseTicker Component
 *
 * Main ticker component for the Live Pulse section of the Command Center.
 * Displays real-time production status, financial context, and safety alerts.
 *
 * Features:
 * - Auto-refresh every 15 minutes (matching Pipeline B polling cycle)
 * - Pulsing animation indicator for live status
 * - Data staleness warning (> 20 minutes)
 * - Manual refresh button
 * - Safety alerts take visual priority
 *
 * @see Story 2.9 - Live Pulse Ticker
 * @see AC #1 - Live Pulse Ticker Component
 * @see AC #6 - Performance Requirements (500ms render, 2s refresh)
 * @see AC #7 - Industrial Clarity Compliance
 */

interface LivePulseTickerProps {
  className?: string
  /** Custom polling interval in ms (default: 900000 = 15 min) */
  pollingInterval?: number
}

/**
 * Format timestamp for display
 */
function formatTimestamp(isoString: string | null): string {
  if (!isoString) return 'Never'

  try {
    const date = new Date(isoString)
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true,
    })
  } catch {
    return 'Unknown'
  }
}

/**
 * Format data age for display
 */
function formatDataAge(seconds: number): string {
  if (seconds < 60) return `${seconds}s ago`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  return `${Math.floor(seconds / 3600)}h ago`
}

export function LivePulseTicker({
  className,
  pollingInterval = 900000, // 15 minutes
}: LivePulseTickerProps) {
  const {
    data,
    isLoading,
    error,
    lastFetched,
    refetch,
    hasActiveIncident,
    isDataStale,
  } = useLivePulse({ pollingInterval })

  const handleRefresh = useCallback(async () => {
    await refetch()
  }, [refetch])

  return (
    <Card
      mode="live"
      className={cn(
        'h-full',
        // Add safety border when incidents are active
        hasActiveIncident && 'border-safety-red ring-2 ring-safety-red/20',
        className
      )}
    >
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-3">
            <CardTitle className="card-title">
              Live Pulse
            </CardTitle>
            {/* Pulsing Live Indicator */}
            <span
              className={cn(
                'inline-flex h-2.5 w-2.5 rounded-full',
                isDataStale ? 'bg-warning-amber' : 'bg-live-primary animate-live-pulse'
              )}
              aria-label={isDataStale ? 'Data stale' : 'Live indicator'}
            />
            <Badge variant={isDataStale ? 'warning' : 'live'}>
              {isDataStale ? 'Data Stale' : 'Real-time'}
            </Badge>
          </div>

          {/* Last Updated & Refresh */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">
              Updated: {formatTimestamp(lastFetched)}
              {data?.meta?.data_age != null && (
                <span className="ml-1">
                  ({formatDataAge(data.meta.data_age)})
                </span>
              )}
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRefresh}
              disabled={isLoading}
              className="h-7 w-7 p-0"
              aria-label="Refresh data"
            >
              <svg
                className={cn('w-4 h-4', isLoading && 'animate-spin')}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
            </Button>
          </div>
        </div>

        {/* Data Stale Warning */}
        {isDataStale && (
          <div className="mt-2 flex items-center gap-2 text-sm text-warning-amber bg-warning-amber-light dark:bg-warning-amber-dark/20 px-3 py-2 rounded-md">
            <svg
              className="w-4 h-4"
              fill="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
            </svg>
            <span>Data is more than 20 minutes old. Check data pipeline status.</span>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="mt-2 flex items-center gap-2 text-sm text-warning-amber-dark bg-warning-amber-light dark:bg-warning-amber-dark/20 px-3 py-2 rounded-md">
            <svg
              className="w-4 h-4"
              fill="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
            </svg>
            <span>{error}</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRefresh}
              className="ml-auto h-6 text-xs"
            >
              Retry
            </Button>
          </div>
        )}
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Safety Alert - Always First (Visual Priority per FR4) */}
        <LivePulseSafetyIndicator
          data={data?.safety ?? null}
          isLoading={isLoading && !data}
        />

        {/* Two-Column Layout for Production and Financial */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {/* Production Status */}
          <div className="space-y-2">
            <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground flex items-center gap-2">
              <svg
                className="w-4 h-4 text-live-primary flex-shrink-0"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
              Production Status
            </h3>
            <ProductionStatusMetric
              data={data?.production ?? null}
              isLoading={isLoading && !data}
            />
          </div>

          {/* Financial Context */}
          <div className="space-y-2 border-t xl:border-t-0 xl:border-l border-live-border dark:border-live-border-dark pt-6 xl:pt-0 xl:pl-6">
            <FinancialContextWidget
              data={data?.financial ?? null}
              isLoading={isLoading && !data}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
