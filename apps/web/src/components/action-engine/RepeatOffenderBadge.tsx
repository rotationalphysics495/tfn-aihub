'use client'

import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { TrendData } from './types'

interface RepeatOffenderBadgeProps {
  trendData?: TrendData | null
  className?: string
}

function getOrdinalSuffix(n: number): string {
  const mod100 = n % 100
  if (mod100 >= 11 && mod100 <= 13) return 'th'
  switch (n % 10) {
    case 1: return 'st'
    case 2: return 'nd'
    case 3: return 'rd'
    default: return 'th'
  }
}

export function RepeatOffenderBadge({ trendData, className }: RepeatOffenderBadgeProps) {
  if (!trendData) return null

  const { consecutiveDays, daysOnReport } = trendData

  // Guard against invalid data
  if (consecutiveDays <= 0 && daysOnReport <= 0) return null
  if (consecutiveDays < 0) return null

  // New item: first appearance
  if (consecutiveDays === 1 && daysOnReport === 1) {
    return (
      <Badge
        variant="info"
        className={cn('gap-1.5', className)}
        aria-label="New issue"
      >
        New
      </Badge>
    )
  }

  // Consecutive days >= 3 takes precedence
  if (consecutiveDays >= 3) {
    const text = `${consecutiveDays}${getOrdinalSuffix(consecutiveDays)} day in a row`
    return (
      <Badge
        variant="warning"
        className={cn('gap-1.5', className)}
        aria-label={`Repeat issue: ${text}`}
      >
        {text}
      </Badge>
    )
  }

  // Frequency badge: days_on_report >= 3 but not consecutive
  if (daysOnReport >= 3) {
    const text = `${daysOnReport} of 7 days`
    return (
      <Badge
        variant="warning"
        className={cn('gap-1.5', className)}
        aria-label={`Repeat issue: ${text}`}
      >
        {text}
      </Badge>
    )
  }

  // Second day
  if (consecutiveDays === 2) {
    return (
      <Badge
        variant="outline"
        className={cn('gap-1.5', className)}
        aria-label="Repeat issue: 2nd day"
      >
        2nd day
      </Badge>
    )
  }

  return null
}
