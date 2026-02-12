'use client'

import { TrendingUp, TrendingDown, ArrowRight } from 'lucide-react'
import { LineChart, Line } from 'recharts'
import { cn } from '@/lib/utils'
import type { PriorityType } from './PriorityBadge'
import type { TrendData } from './types'

interface TrendIndicatorProps {
  trendData?: TrendData
  priority: PriorityType
  isLoading?: boolean
  className?: string
}

type TrendDirection = 'improving' | 'worsening' | 'stable'

const STABLE_THRESHOLD = 2

const TREND_COLORS: Record<TrendDirection, string> = {
  improving: '#22c55e',
  worsening: '#ef4444',
  stable: '#9ca3af',
}

const TREND_TEXT_CLASSES: Record<TrendDirection, string> = {
  improving: 'text-green-600 dark:text-green-400',
  worsening: 'text-red-600 dark:text-red-400',
  stable: 'text-gray-500 dark:text-gray-400',
}

function getTrendDirection(
  change: number | null,
  priority: PriorityType
): TrendDirection | null {
  if (change === null || change === undefined || Number.isNaN(change)) return null
  if (priority === 'SAFETY') return null

  const absChange = Math.abs(change)
  if (absChange < STABLE_THRESHOLD) return 'stable'

  if (priority === 'OEE') {
    return change > 0 ? 'improving' : 'worsening'
  }

  // FINANCIAL: lower is better
  return change < 0 ? 'improving' : 'worsening'
}

function formatPercentChange(change: number): string {
  const sign = change > 0 ? '+' : ''
  return `${sign}${change.toFixed(1)}%`
}

function getAriaLabel(
  direction: TrendDirection | null,
  priority: PriorityType,
  change: number | null
): string {
  if (!direction || change === null) return 'Trend: unavailable'

  const absChange = Math.abs(change).toFixed(1)
  if (direction === 'stable') return 'Trend: stable'

  const upOrDown = change > 0 ? 'up' : 'down'
  return `Trend: ${direction}, ${priority} ${upOrDown} ${absChange}%`
}

export function TrendIndicator({
  trendData,
  priority,
  isLoading = false,
  className,
}: TrendIndicatorProps) {
  // Loading skeleton
  if (isLoading) {
    return (
      <div
        data-testid="trend-indicator-skeleton"
        className={cn('flex items-center gap-2 animate-pulse', className)}
      >
        <div className="h-5 w-10 bg-industrial-200 dark:bg-industrial-700 rounded" />
        <div className="h-6 w-20 bg-industrial-200 dark:bg-industrial-700 rounded" />
      </div>
    )
  }

  // No data and not loading = render nothing
  if (!trendData) return null

  const { weekOverWeekChange, metricHistory } = trendData
  const direction = getTrendDirection(weekOverWeekChange, priority)

  // Filter out null values for sparkline data
  const sparkData = metricHistory
    .filter((v): v is number => v !== null)
    .map((value) => ({ value }))

  const hasSparkData = sparkData.length > 0
  const strokeColor = direction ? TREND_COLORS[direction] : TREND_COLORS.stable

  return (
    <div className={cn('flex items-center gap-2 flex-wrap', className)}>
      {/* Trend Arrow + Percentage */}
      {direction && (
        <div
          data-testid="trend-arrow"
          className={cn('flex items-center gap-1', TREND_TEXT_CLASSES[direction])}
          aria-label={getAriaLabel(direction, priority, weekOverWeekChange)}
        >
          {direction === 'improving' && (
            <TrendingUp className="w-4 h-4" aria-hidden="true" />
          )}
          {direction === 'worsening' && (
            <TrendingDown className="w-4 h-4" aria-hidden="true" />
          )}
          {direction === 'stable' && (
            <ArrowRight className="w-4 h-4" aria-hidden="true" />
          )}
          {weekOverWeekChange !== null && !Number.isNaN(weekOverWeekChange) && (
            <span className="text-xs font-medium">
              {formatPercentChange(weekOverWeekChange)}
            </span>
          )}
        </div>
      )}

      {/* Sparkline */}
      {hasSparkData && (
        <LineChart width={80} height={24} data={sparkData}>
          <Line
            type="monotone"
            dataKey="value"
            stroke={strokeColor}
            strokeWidth={1.5}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      )}
    </div>
  )
}
