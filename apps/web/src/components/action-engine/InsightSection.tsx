'use client'

import { useRouter } from 'next/navigation'
import { Clock, MapPin } from 'lucide-react'
import { cn } from '@/lib/utils'
import { PriorityBadge, type PriorityType } from './PriorityBadge'
import type { Recommendation, AssetReference } from './types'

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

export function InsightSection({
  priority,
  recommendation,
  asset,
  financialImpact,
  timestamp,
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
      </div>
    </div>
  )
}
