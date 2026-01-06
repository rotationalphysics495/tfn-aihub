'use client'

import { cn } from '@/lib/utils'
import type { ThroughputStatus } from './StatusBadge'

/**
 * Filter Bar Component for Throughput Dashboard
 *
 * Provides filtering options for asset area and status.
 *
 * @see Story 2.3 - AC #8 Asset Filtering (Optional Enhancement)
 */

interface FilterBarProps {
  areas: string[]
  selectedArea: string | null
  selectedStatus: ThroughputStatus | null
  onAreaChange: (area: string | null) => void
  onStatusChange: (status: ThroughputStatus | null) => void
  counts: {
    total: number
    on_target: number
    behind: number
    critical: number
  }
  className?: string
}

const statusFilters: { value: ThroughputStatus | null; label: string }[] = [
  { value: null, label: 'All' },
  { value: 'on_target', label: 'On Target' },
  { value: 'behind', label: 'Behind' },
  { value: 'critical', label: 'Critical' },
]

export function FilterBar({
  areas,
  selectedArea,
  selectedStatus,
  onAreaChange,
  onStatusChange,
  counts,
  className,
}: FilterBarProps) {
  return (
    <div
      className={cn(
        'flex flex-col sm:flex-row items-start sm:items-center gap-4',
        className
      )}
    >
      {/* Area Filter Dropdown */}
      <div className="flex items-center gap-2">
        <label
          htmlFor="area-filter"
          className="text-sm font-medium text-muted-foreground whitespace-nowrap"
        >
          Area:
        </label>
        <select
          id="area-filter"
          value={selectedArea || ''}
          onChange={(e) => onAreaChange(e.target.value || null)}
          className={cn(
            'px-3 py-2 text-sm rounded-md border border-input bg-background',
            'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
            'min-w-[150px] touch-target'
          )}
        >
          <option value="">All Areas</option>
          {areas.map((area) => (
            <option key={area} value={area}>
              {area}
            </option>
          ))}
        </select>
      </div>

      {/* Status Filter Tabs */}
      <div className="flex items-center gap-1 flex-wrap" role="tablist" aria-label="Filter by status">
        {statusFilters.map((filter) => {
          const isSelected = selectedStatus === filter.value
          const count =
            filter.value === null
              ? counts.total
              : counts[filter.value as keyof typeof counts]

          return (
            <button
              key={filter.value ?? 'all'}
              role="tab"
              aria-selected={isSelected}
              onClick={() => onStatusChange(filter.value)}
              className={cn(
                'px-3 py-2 text-sm font-medium rounded-md transition-colors',
                'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
                'touch-target',
                isSelected
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
              )}
            >
              {filter.label}
              <span
                className={cn(
                  'ml-1.5 px-1.5 py-0.5 text-xs rounded-full',
                  isSelected
                    ? 'bg-primary-foreground/20 text-primary-foreground'
                    : 'bg-muted text-muted-foreground'
                )}
              >
                {count}
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
