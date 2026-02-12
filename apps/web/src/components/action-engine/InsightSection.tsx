'use client'

import { useRouter } from 'next/navigation'
import { CheckCircle2, Circle, Clock, MapPin, UserPlus } from 'lucide-react'
import { cn } from '@/lib/utils'
import { PriorityBadge, type PriorityType } from './PriorityBadge'
import { AssignmentBadge } from './AssignmentBadge'
import type { Recommendation, AssetReference, FollowUpData, TrendData } from './types'
import { TrendIndicator } from './TrendIndicator'
import { RepeatOffenderBadge } from './RepeatOffenderBadge'
import { ActivePlanBadge } from './ActivePlanBadge'

/**
 * Insight Section Component (Left side of card)
 *
 * Displays the recommendation/insight with:
 * - Priority badge (SAFETY/FINANCIAL/OEE)
 * - Natural language recommendation text
 * - Financial impact in dollars
 * - Timestamp of insight generation
 * - Asset name/location
 *
 * @see Story 3.4 - Insight + Evidence Cards
 * @see AC #2 - Recommendation/Insight Display (Left Side)
 */

interface InsightSectionProps {
  priority: PriorityType
  recommendation: Recommendation
  asset: AssetReference
  financialImpact: number
  timestamp: string
  onAssign?: () => void
  isAcknowledged?: boolean
  acknowledgedAt?: string | null
  onAcknowledge?: () => void
  followUp?: FollowUpData | null
  trendData?: TrendData
  isLoading?: boolean
  className?: string
}

// Format financial impact for display
function formatCurrency(value: number): string {
  if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(1)}M`
  }
  if (value >= 1000) {
    return `$${Math.round(value / 1000)}K`
  }
  return `$${Math.round(value)}`
}

// Format timestamp for display
function formatTimestamp(isoString: string): string {
  const date = new Date(isoString)
  return date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  })
}

// Format acknowledgment timestamp for display (UTC to match server timestamps)
function formatAcknowledgedTime(isoString: string): string {
  const date = new Date(isoString)
  return date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
    timeZone: 'UTC',
  })
}

export function InsightSection({
  priority,
  recommendation,
  asset,
  financialImpact,
  timestamp,
  onAssign,
  isAcknowledged = false,
  acknowledgedAt,
  onAcknowledge,
  followUp,
  trendData,
  isLoading,
  className,
}: InsightSectionProps) {
  const router = useRouter()

  // Handle asset name click for navigation to Asset Detail View (AC #6)
  const handleAssetClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    router.push(`/assets/${asset.id}`)
  }

  return (
    <div className={cn('flex flex-col gap-3', className)}>
      {/* Priority badge - prominent and glanceable (AC #4) */}
      <div className="flex items-center gap-3 flex-wrap">
        <PriorityBadge priority={priority} />
        <RepeatOffenderBadge trendData={trendData} />

        {/* Financial impact - prominent display when applicable (AC #2) */}
        {financialImpact > 0 && (
          <span
            className={cn(
              'text-xl md:text-2xl font-bold',
              priority === 'SAFETY' && 'text-safety-red',
              priority === 'FINANCIAL' && 'text-warning-amber-dark dark:text-warning-amber',
              priority === 'OEE' && 'text-[#CA8A04] dark:text-[#EAB308]'
            )}
            aria-label={`Financial impact: ${formatCurrency(financialImpact)}`}
          >
            {formatCurrency(financialImpact)} loss
          </span>
        )}
      </div>

      {/* Trend indicator row (Story 14.4 AC #2, #3, #5) */}
      {(trendData || isLoading) && (
        <TrendIndicator trendData={trendData} priority={priority} isLoading={isLoading} />
      )}

      {/* Assignment badge - shows when a follow-up exists (Story 13.4 AC #1) */}
      {followUp && <AssignmentBadge followUp={followUp} />}

      {/* Recommendation text - readable from 3ft (AC #2, #4 Glanceability) */}
      <h3 className="text-xl md:text-2xl font-semibold text-foreground leading-tight">
        {recommendation.text}
      </h3>

      {/* Context row: Asset and timestamp (AC #2) */}
      <div className="flex flex-wrap items-center gap-4 text-base text-muted-foreground">
        {/* Asset name - clickable for navigation (AC #6) */}
        <button
          type="button"
          onClick={handleAssetClick}
          className={cn(
            'flex items-center gap-1.5',
            'text-foreground font-medium',
            'hover:text-primary hover:underline',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
            'rounded-sm'
          )}
          aria-label={`View asset details for ${asset.name}`}
        >
          <MapPin className="w-4 h-4 flex-shrink-0" aria-hidden="true" />
          <span>{asset.name}</span>
          {asset.area && (
            <span className="text-muted-foreground">({asset.area})</span>
          )}
        </button>

        {/* Timestamp (AC #2) */}
        <div className="flex items-center gap-1.5">
          <Clock className="w-4 h-4 flex-shrink-0" aria-hidden="true" />
          <span>Generated at {formatTimestamp(timestamp)}</span>
        </div>

        {/* Active plan badge (Story 16.4) */}
        {asset.id && <ActivePlanBadge assetId={asset.id} />}

        {/* Acknowledge action */}
        <div className="flex flex-col">
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation()
              onAcknowledge?.()
            }}
            className={cn(
              'flex items-center gap-1.5',
              'text-sm font-medium',
              'hover:underline',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
              'rounded-sm',
              isAcknowledged
                ? 'text-green-600 dark:text-green-400'
                : 'text-muted-foreground hover:text-foreground'
            )}
          >
            {isAcknowledged ? (
              <CheckCircle2 className="w-4 h-4 flex-shrink-0" aria-hidden="true" />
            ) : (
              <>
                <span className="sr-only">Mark action as reviewed.</span>
                <Circle className="w-4 h-4 flex-shrink-0" aria-hidden="true" />
              </>
            )}
            <span>{isAcknowledged ? 'Reviewed' : 'Mark Reviewed'}</span>
          </button>
          {isAcknowledged && acknowledgedAt && (
            <span className="text-sm text-muted-foreground ml-[22px]">
              {formatAcknowledgedTime(acknowledgedAt)}
            </span>
          )}
        </div>

        {/* Assign follow-up */}
        {onAssign && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation()
              onAssign()
            }}
            className={cn(
              'flex items-center gap-1.5 ml-auto',
              'text-sm font-medium text-primary',
              'hover:text-primary/80 hover:underline',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
              'rounded-sm'
            )}
            aria-label={followUp ? 'Reassign follow-up action' : 'Assign follow-up action'}
          >
            <UserPlus className="w-4 h-4 flex-shrink-0" aria-hidden="true" />
            <span>{followUp ? 'Reassign' : 'Assign'}</span>
          </button>
        )}
      </div>
    </div>
  )
}
