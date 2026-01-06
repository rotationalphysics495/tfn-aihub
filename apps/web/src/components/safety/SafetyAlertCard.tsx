'use client'

import Link from 'next/link'
import { cn } from '@/lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

/**
 * Safety Alert Card Component
 *
 * Displays individual safety event details in a card format.
 * Uses "Safety Red" styling exclusively for safety incidents.
 *
 * @see Story 2.6 - Safety Alert System
 * @see AC #3 - "Safety Red" exclusive color
 * @see AC #4 - Glanceable design
 * @see AC #5 - Links to asset
 * @see AC #10 - Financial impact context
 */

export interface SafetyEvent {
  id: string
  asset_id: string
  asset_name: string
  area: string | null
  event_timestamp: string
  reason_code: string
  severity: string
  description: string | null
  duration_minutes: number | null
  financial_impact: number | null
  acknowledged: boolean
  acknowledged_at: string | null
}

interface SafetyAlertCardProps {
  event: SafetyEvent
  onAcknowledge?: (eventId: string) => void
  onViewDetails?: (event: SafetyEvent) => void
  compact?: boolean
  className?: string
}

export function SafetyAlertCard({
  event,
  onAcknowledge,
  onViewDetails,
  compact = false,
  className,
}: SafetyAlertCardProps) {
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

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount)
  }

  const getSeverityBadge = (severity: string) => {
    const severityConfig: Record<string, { label: string; className: string }> = {
      critical: { label: 'Critical', className: 'bg-safety-red text-white border-safety-red' },
      high: { label: 'High', className: 'bg-safety-red/80 text-white border-safety-red/80' },
      medium: { label: 'Medium', className: 'bg-warning-amber text-white border-warning-amber' },
      low: { label: 'Low', className: 'bg-muted text-foreground border-border' },
    }
    const config = severityConfig[severity.toLowerCase()] || severityConfig.low
    return (
      <Badge className={cn('font-semibold', config.className)}>
        {config.label}
      </Badge>
    )
  }

  if (compact) {
    // Compact view for lists
    return (
      <div
        className={cn(
          'flex items-center gap-3 p-3 rounded-lg border transition-colors cursor-pointer',
          event.acknowledged
            ? 'bg-muted/50 border-border hover:bg-muted'
            : 'bg-safety-red-light border-safety-red/30 hover:bg-safety-red-light/80',
          className
        )}
        onClick={() => onViewDetails?.(event)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && onViewDetails?.(event)}
        aria-label={`Safety event: ${event.reason_code} on ${event.asset_name}`}
      >
        {/* Warning Icon */}
        <div className={cn(
          'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
          event.acknowledged ? 'bg-muted' : 'bg-safety-red/20'
        )}>
          <svg
            className={cn(
              'w-4 h-4',
              event.acknowledged ? 'text-muted-foreground' : 'text-safety-red'
            )}
            fill="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path d="M12 2L1 21h22L12 2zm0 3.17L20.04 19H3.96L12 5.17zM11 16h2v2h-2v-2zm0-6h2v4h-2v-4z"/>
          </svg>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className={cn(
              'font-semibold truncate',
              event.acknowledged ? 'text-muted-foreground' : 'text-safety-red-dark'
            )}>
              {event.asset_name}
            </span>
            {getSeverityBadge(event.severity)}
          </div>
          <p className="text-sm text-muted-foreground truncate">
            {event.reason_code} - {formatTimestamp(event.event_timestamp)}
          </p>
        </div>

        {/* Acknowledge Button */}
        {!event.acknowledged && onAcknowledge && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              onAcknowledge(event.id)
            }}
            className="flex-shrink-0 p-1.5 rounded hover:bg-safety-red/10 transition-colors"
            aria-label="Acknowledge safety event"
          >
            <svg
              className="w-4 h-4 text-safety-red"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </button>
        )}
      </div>
    )
  }

  // Full card view
  return (
    <Card
      className={cn(
        event.acknowledged
          ? 'border-border'
          : 'border-safety-red/30 bg-safety-red-light/30',
        className
      )}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-3">
            {/* Warning Icon */}
            <div className={cn(
              'w-10 h-10 rounded-full flex items-center justify-center',
              event.acknowledged ? 'bg-muted' : 'bg-safety-red/20'
            )}>
              <svg
                className={cn(
                  'w-5 h-5',
                  event.acknowledged ? 'text-muted-foreground' : 'text-safety-red'
                )}
                fill="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path d="M12 2L1 21h22L12 2zm0 3.17L20.04 19H3.96L12 5.17zM11 16h2v2h-2v-2zm0-6h2v4h-2v-4z"/>
              </svg>
            </div>

            <div>
              <CardTitle className={cn(
                'text-base font-semibold',
                event.acknowledged ? 'text-muted-foreground' : 'text-safety-red-dark'
              )}>
                {event.reason_code}
              </CardTitle>
              <p className="text-sm text-muted-foreground">
                {formatTimestamp(event.event_timestamp)}
              </p>
            </div>
          </div>

          {getSeverityBadge(event.severity)}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Asset Link - AC #5 */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Asset</span>
          <Link
            href={`/dashboard/assets/${event.asset_id}`}
            className={cn(
              'font-medium hover:underline',
              event.acknowledged ? 'text-foreground' : 'text-safety-red-dark'
            )}
          >
            {event.asset_name}
          </Link>
        </div>

        {/* Area */}
        {event.area && (
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Area</span>
            <span className="font-medium">{event.area}</span>
          </div>
        )}

        {/* Duration */}
        {event.duration_minutes && event.duration_minutes > 0 && (
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Duration</span>
            <span className="font-medium">{event.duration_minutes} min</span>
          </div>
        )}

        {/* Financial Impact - AC #10 */}
        {event.financial_impact && event.financial_impact > 0 && (
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Est. Financial Impact</span>
            <span className={cn(
              'font-semibold',
              event.acknowledged ? 'text-warning-amber-dark' : 'text-safety-red-dark'
            )}>
              {formatCurrency(event.financial_impact)}
            </span>
          </div>
        )}

        {/* Description */}
        {event.description && (
          <div className="pt-2 border-t border-border">
            <span className="text-sm text-muted-foreground block mb-1">Description</span>
            <p className="text-sm">{event.description}</p>
          </div>
        )}

        {/* Status */}
        <div className="flex items-center justify-between pt-2 border-t border-border">
          <span className="text-sm text-muted-foreground">Status</span>
          <span className={cn(
            'font-medium',
            event.acknowledged ? 'text-success-green' : 'text-safety-red'
          )}>
            {event.acknowledged ? 'Acknowledged' : 'Active'}
          </span>
        </div>

        {/* Acknowledge Button */}
        {!event.acknowledged && onAcknowledge && (
          <div className="pt-2">
            <button
              onClick={() => onAcknowledge(event.id)}
              className="w-full py-2 px-4 bg-safety-red hover:bg-safety-red-dark text-white font-semibold rounded-md transition-colors"
            >
              Acknowledge Alert
            </button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
