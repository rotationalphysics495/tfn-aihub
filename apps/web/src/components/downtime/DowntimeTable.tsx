'use client'

import { useState, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'

/**
 * Downtime Breakdown Table Component
 *
 * Displays granular downtime events with sorting and pagination.
 * Highlights safety-related events with Safety Red styling.
 *
 * @see Story 2.5 - Downtime Pareto Analysis
 * @see AC #4 - Granular Breakdown Table
 * @see AC #6 - Safety Reason Code Highlighting
 */

export interface DowntimeEvent {
  id: string | null
  asset_id: string
  asset_name: string
  area: string | null
  reason_code: string
  duration_minutes: number
  event_timestamp: string
  end_timestamp: string | null
  financial_impact: number
  is_safety_related: boolean
  severity: string | null
  description: string | null
}

type SortField = 'asset_name' | 'reason_code' | 'duration_minutes' | 'event_timestamp' | 'financial_impact'
type SortDirection = 'asc' | 'desc'

interface DowntimeTableProps {
  events: DowntimeEvent[]
  isLive: boolean
  onRowClick?: (event: DowntimeEvent) => void
  onSafetyClick?: (event: DowntimeEvent) => void
  className?: string
}

const ITEMS_PER_PAGE = 10

export function DowntimeTable({
  events,
  isLive,
  onRowClick,
  onSafetyClick,
  className,
}: DowntimeTableProps) {
  const [sortField, setSortField] = useState<SortField>('duration_minutes')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')
  const [currentPage, setCurrentPage] = useState(1)

  // Sort events with safety events prioritized
  const sortedEvents = useMemo(() => {
    const sorted = [...events].sort((a, b) => {
      // Safety events always come first
      if (a.is_safety_related && !b.is_safety_related) return -1
      if (!a.is_safety_related && b.is_safety_related) return 1

      // Then sort by selected field
      let comparison = 0
      switch (sortField) {
        case 'asset_name':
          comparison = a.asset_name.localeCompare(b.asset_name)
          break
        case 'reason_code':
          comparison = a.reason_code.localeCompare(b.reason_code)
          break
        case 'duration_minutes':
          comparison = a.duration_minutes - b.duration_minutes
          break
        case 'event_timestamp':
          comparison = new Date(a.event_timestamp).getTime() - new Date(b.event_timestamp).getTime()
          break
        case 'financial_impact':
          comparison = a.financial_impact - b.financial_impact
          break
      }
      return sortDirection === 'asc' ? comparison : -comparison
    })
    return sorted
  }, [events, sortField, sortDirection])

  // Pagination
  const totalPages = Math.ceil(sortedEvents.length / ITEMS_PER_PAGE)
  const paginatedEvents = sortedEvents.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  )

  // Handle sort toggle
  const handleSort = (field: SortField) => {
    if (field === sortField) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('desc')
    }
    setCurrentPage(1) // Reset to first page on sort
  }

  // Format timestamp for display
  const formatTimestamp = (timestamp: string): string => {
    try {
      const date = new Date(timestamp)
      return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
      })
    } catch {
      return timestamp
    }
  }

  // Format currency
  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount)
  }

  // Sort indicator
  const SortIndicator = ({ field }: { field: SortField }) => {
    if (field !== sortField) {
      return (
        <svg className="w-4 h-4 text-muted-foreground/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
        </svg>
      )
    }
    return (
      <svg className="w-4 h-4 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        {sortDirection === 'asc' ? (
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
        ) : (
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        )}
      </svg>
    )
  }

  if (!events || events.length === 0) {
    return (
      <Card mode={isLive ? 'live' : 'retrospective'} className={className}>
        <CardHeader>
          <CardTitle className="text-lg">Downtime Events</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-[200px] text-muted-foreground">
            No downtime events found
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card mode={isLive ? 'live' : 'retrospective'} className={className}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Downtime Events</CardTitle>
          <span className="text-sm text-muted-foreground">
            {events.length} total events
          </span>
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th
                  className="px-3 py-3 text-left font-medium text-muted-foreground cursor-pointer hover:text-foreground"
                  onClick={() => handleSort('asset_name')}
                >
                  <div className="flex items-center gap-1">
                    Asset
                    <SortIndicator field="asset_name" />
                  </div>
                </th>
                <th
                  className="px-3 py-3 text-left font-medium text-muted-foreground cursor-pointer hover:text-foreground"
                  onClick={() => handleSort('reason_code')}
                >
                  <div className="flex items-center gap-1">
                    Reason Code
                    <SortIndicator field="reason_code" />
                  </div>
                </th>
                <th
                  className="px-3 py-3 text-right font-medium text-muted-foreground cursor-pointer hover:text-foreground"
                  onClick={() => handleSort('duration_minutes')}
                >
                  <div className="flex items-center justify-end gap-1">
                    Duration
                    <SortIndicator field="duration_minutes" />
                  </div>
                </th>
                <th
                  className="px-3 py-3 text-left font-medium text-muted-foreground cursor-pointer hover:text-foreground"
                  onClick={() => handleSort('event_timestamp')}
                >
                  <div className="flex items-center gap-1">
                    Start Time
                    <SortIndicator field="event_timestamp" />
                  </div>
                </th>
                <th className="px-3 py-3 text-left font-medium text-muted-foreground">
                  End Time
                </th>
                <th
                  className="px-3 py-3 text-right font-medium text-muted-foreground cursor-pointer hover:text-foreground"
                  onClick={() => handleSort('financial_impact')}
                >
                  <div className="flex items-center justify-end gap-1">
                    Financial Impact
                    <SortIndicator field="financial_impact" />
                  </div>
                </th>
              </tr>
            </thead>
            <tbody>
              {paginatedEvents.map((event, index) => (
                <tr
                  key={event.id || `${event.asset_id}-${index}`}
                  className={cn(
                    'border-b border-border/50 transition-colors',
                    event.is_safety_related
                      ? 'bg-safety-red/5 hover:bg-safety-red/10'
                      : 'hover:bg-muted/50',
                    onRowClick && 'cursor-pointer'
                  )}
                  onClick={() => {
                    if (event.is_safety_related && onSafetyClick) {
                      onSafetyClick(event)
                    } else if (onRowClick) {
                      onRowClick(event)
                    }
                  }}
                >
                  <td className="px-3 py-3">
                    <div className="flex items-center gap-2">
                      {event.is_safety_related && (
                        <svg
                          className="w-4 h-4 text-safety-red flex-shrink-0"
                          fill="currentColor"
                          viewBox="0 0 24 24"
                          aria-label="Safety Issue"
                        >
                          <path d="M12 2L1 21h22L12 2zm0 3.17L20.04 19H3.96L12 5.17zM11 16h2v2h-2v-2zm0-6h2v4h-2v-4z"/>
                        </svg>
                      )}
                      <div>
                        <div className={cn(
                          'font-medium',
                          event.is_safety_related && 'text-safety-red'
                        )}>
                          {event.asset_name}
                        </div>
                        {event.area && (
                          <div className="text-xs text-muted-foreground">
                            {event.area}
                          </div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-3 py-3">
                    <span className={cn(
                      event.is_safety_related && 'text-safety-red font-medium'
                    )}>
                      {event.reason_code}
                    </span>
                  </td>
                  <td className="px-3 py-3 text-right font-medium">
                    {event.duration_minutes} min
                  </td>
                  <td className="px-3 py-3 text-muted-foreground">
                    {formatTimestamp(event.event_timestamp)}
                  </td>
                  <td className="px-3 py-3 text-muted-foreground">
                    {event.end_timestamp ? formatTimestamp(event.end_timestamp) : '--'}
                  </td>
                  <td className="px-3 py-3 text-right font-medium text-warning-amber">
                    {formatCurrency(event.financial_impact)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between mt-4 pt-4 border-t border-border">
            <div className="text-sm text-muted-foreground">
              Showing {((currentPage - 1) * ITEMS_PER_PAGE) + 1} to{' '}
              {Math.min(currentPage * ITEMS_PER_PAGE, events.length)} of {events.length}
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className={cn(
                  'px-3 py-1 rounded-md text-sm',
                  currentPage === 1
                    ? 'text-muted-foreground cursor-not-allowed'
                    : 'text-foreground hover:bg-muted'
                )}
              >
                Previous
              </button>
              <div className="flex items-center gap-1">
                {Array.from({ length: totalPages }, (_, i) => i + 1)
                  .filter(page => {
                    // Show first, last, current, and adjacent pages
                    return page === 1 ||
                      page === totalPages ||
                      Math.abs(page - currentPage) <= 1
                  })
                  .map((page, idx, arr) => {
                    // Add ellipsis if there's a gap
                    const showEllipsis = idx > 0 && arr[idx - 1] !== page - 1
                    return (
                      <span key={page}>
                        {showEllipsis && <span className="px-2 text-muted-foreground">...</span>}
                        <button
                          onClick={() => setCurrentPage(page)}
                          className={cn(
                            'px-3 py-1 rounded-md text-sm',
                            page === currentPage
                              ? 'bg-primary text-primary-foreground'
                              : 'hover:bg-muted'
                          )}
                        >
                          {page}
                        </button>
                      </span>
                    )
                  })}
              </div>
              <button
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className={cn(
                  'px-3 py-1 rounded-md text-sm',
                  currentPage === totalPages
                    ? 'text-muted-foreground cursor-not-allowed'
                    : 'text-foreground hover:bg-muted'
                )}
              >
                Next
              </button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
