'use client'

import { cn } from '@/lib/utils'

/**
 * Time Window Toggle Component
 *
 * Toggles between Yesterday (T-1) and Live (T-15m) data views.
 * Follows UX spec for visual distinction between retrospective and live modes.
 *
 * @see Story 2.5 - Downtime Pareto Analysis
 * @see AC #7 - Time Window Toggle
 */

type DataView = 'yesterday' | 'live'

interface TimeWindowToggleProps {
  activeView: DataView
  onViewChange: (view: DataView) => void
  isLoading?: boolean
  className?: string
}

export function TimeWindowToggle({
  activeView,
  onViewChange,
  isLoading = false,
  className,
}: TimeWindowToggleProps) {
  return (
    <div className={cn('flex items-center gap-2 p-1 bg-muted rounded-lg', className)}>
      <button
        onClick={() => onViewChange('yesterday')}
        disabled={isLoading}
        className={cn(
          'px-4 py-2 rounded-md text-sm font-medium transition-colors',
          activeView === 'yesterday'
            ? 'bg-card text-foreground shadow-sm'
            : 'text-muted-foreground hover:text-foreground',
          isLoading && 'opacity-50 cursor-not-allowed'
        )}
        aria-pressed={activeView === 'yesterday'}
      >
        <span className="flex items-center gap-2">
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
          Yesterday&apos;s Analysis
        </span>
      </button>
      <button
        onClick={() => onViewChange('live')}
        disabled={isLoading}
        className={cn(
          'px-4 py-2 rounded-md text-sm font-medium transition-colors',
          activeView === 'live'
            ? 'bg-card text-foreground shadow-sm'
            : 'text-muted-foreground hover:text-foreground',
          isLoading && 'opacity-50 cursor-not-allowed'
        )}
        aria-pressed={activeView === 'live'}
      >
        <span className="flex items-center gap-2">
          <span
            className={cn(
              'w-2 h-2 rounded-full',
              activeView === 'live'
                ? 'bg-live-pulse animate-live-pulse'
                : 'bg-muted-foreground'
            )}
            aria-hidden="true"
          />
          Live Pulse
        </span>
      </button>
    </div>
  )
}
