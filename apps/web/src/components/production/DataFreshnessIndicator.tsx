'use client'

import { useEffect, useState } from 'react'
import { cn } from '@/lib/utils'

/**
 * Data Freshness Indicator
 *
 * Shows the last updated timestamp and warns if data is stale (>60 seconds old).
 * Includes auto-refresh and manual refresh capabilities.
 *
 * @see Story 2.3 - AC #4 Data Freshness Indicator
 * @see NFR2 - Data reflects SQL within 60 seconds
 */

interface DataFreshnessIndicatorProps {
  lastUpdated: string | null
  onRefresh: () => void
  isRefreshing?: boolean
  className?: string
}

function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffSeconds = Math.floor(diffMs / 1000)
  const diffMinutes = Math.floor(diffSeconds / 60)

  if (diffSeconds < 60) {
    return 'Just now'
  } else if (diffMinutes < 60) {
    return `${diffMinutes} min ago`
  } else {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
}

function isStale(timestamp: string, thresholdSeconds = 60): boolean {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  return diffMs > thresholdSeconds * 1000
}

export function DataFreshnessIndicator({
  lastUpdated,
  onRefresh,
  isRefreshing = false,
  className,
}: DataFreshnessIndicatorProps) {
  const [displayTime, setDisplayTime] = useState<string>('')
  const [stale, setStale] = useState(false)

  useEffect(() => {
    if (!lastUpdated) return

    const updateDisplay = () => {
      setDisplayTime(formatTimestamp(lastUpdated))
      setStale(isStale(lastUpdated))
    }

    updateDisplay()

    // Update display every 10 seconds
    const interval = setInterval(updateDisplay, 10000)

    return () => clearInterval(interval)
  }, [lastUpdated])

  if (!lastUpdated) {
    return (
      <div className={cn('flex items-center gap-2 text-sm text-muted-foreground', className)}>
        <span>No data available</span>
      </div>
    )
  }

  return (
    <div className={cn('flex items-center gap-3', className)}>
      <div className="flex items-center gap-2">
        {stale ? (
          <span
            className="inline-flex h-2 w-2 rounded-full bg-warning-amber animate-pulse"
            aria-label="Data may be stale"
          />
        ) : (
          <span
            className="inline-flex h-2 w-2 rounded-full bg-success-green"
            aria-label="Data is fresh"
          />
        )}
        <span
          className={cn(
            'text-sm',
            stale ? 'text-warning-amber-dark dark:text-warning-amber' : 'text-muted-foreground'
          )}
        >
          Last updated: {displayTime}
        </span>
        {stale && (
          <span className="text-xs text-warning-amber-dark dark:text-warning-amber">
            (Data may be stale)
          </span>
        )}
      </div>
      <button
        onClick={onRefresh}
        disabled={isRefreshing}
        className={cn(
          'inline-flex items-center gap-1 px-3 py-1.5 text-sm font-medium rounded-md',
          'bg-secondary text-secondary-foreground',
          'hover:bg-secondary/80 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          'touch-target'
        )}
        aria-label="Refresh data"
      >
        <svg
          className={cn('w-4 h-4', isRefreshing && 'animate-spin')}
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
        {isRefreshing ? 'Refreshing...' : 'Refresh'}
      </button>
    </div>
  )
}
