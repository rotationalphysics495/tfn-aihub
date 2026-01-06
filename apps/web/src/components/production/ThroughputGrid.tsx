'use client'

import { ThroughputCard, type ThroughputCardData } from './ThroughputCard'
import { cn } from '@/lib/utils'

/**
 * Throughput Grid Component
 *
 * Responsive grid container for ThroughputCard components.
 * Optimized for tablet (primary) and desktop displays.
 *
 * @see Story 2.3 - AC #6 Responsive Layout
 */

interface ThroughputGridProps {
  assets: ThroughputCardData[]
  className?: string
}

export function ThroughputGrid({ assets, className }: ThroughputGridProps) {
  if (assets.length === 0) {
    return null
  }

  return (
    <div
      className={cn(
        // Mobile: 1 column
        'grid grid-cols-1',
        // Tablet: 2 columns
        'md:grid-cols-2',
        // Desktop: 3 columns
        'lg:grid-cols-3',
        // Spacing optimized for touch targets
        'gap-4 md:gap-6',
        className
      )}
    >
      {assets.map((asset) => (
        <ThroughputCard key={asset.id} data={asset} />
      ))}
    </div>
  )
}
