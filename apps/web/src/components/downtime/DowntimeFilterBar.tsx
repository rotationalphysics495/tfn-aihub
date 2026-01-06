'use client'

import { cn } from '@/lib/utils'

/**
 * Downtime Filter Bar Component
 *
 * Provides filtering controls for asset, area, and date range.
 *
 * @see Story 2.5 - Downtime Pareto Analysis
 * @see AC #2 - Supports filtering by date range, asset, area, and shift
 */

interface DowntimeFilterBarProps {
  areas: string[]
  selectedArea: string | null
  onAreaChange: (area: string | null) => void
  className?: string
}

export function DowntimeFilterBar({
  areas,
  selectedArea,
  onAreaChange,
  className,
}: DowntimeFilterBarProps) {
  return (
    <div className={cn('flex flex-wrap items-center gap-4', className)}>
      {/* Area Filter */}
      <div className="flex items-center gap-2">
        <label htmlFor="area-filter" className="text-sm text-muted-foreground whitespace-nowrap">
          Filter by Area:
        </label>
        <select
          id="area-filter"
          value={selectedArea || ''}
          onChange={(e) => onAreaChange(e.target.value || null)}
          className="px-3 py-2 bg-background border border-input rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
        >
          <option value="">All Areas</option>
          {areas.map((area) => (
            <option key={area} value={area}>
              {area}
            </option>
          ))}
        </select>
      </div>

      {/* Clear Filters */}
      {selectedArea && (
        <button
          onClick={() => onAreaChange(null)}
          className="text-sm text-muted-foreground hover:text-foreground underline"
        >
          Clear filter
        </button>
      )}
    </div>
  )
}
