'use client'

import { useEffect, useCallback } from 'react'
import { cn } from '@/lib/utils'

/**
 * Safety Event Detail Modal
 *
 * Displays detailed information about safety-related downtime events.
 * FR4 requirement: Safety alerting with full event details.
 *
 * @see Story 2.5 - Downtime Pareto Analysis
 * @see AC #6 - Safety Reason Code Highlighting
 */

export interface SafetyEventDetail {
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
  is_resolved: boolean
  resolved_at: string | null
}

interface SafetyEventModalProps {
  event: SafetyEventDetail | null
  isOpen: boolean
  onClose: () => void
  isLoading?: boolean
}

export function SafetyEventModal({
  event,
  isOpen,
  onClose,
  isLoading = false,
}: SafetyEventModalProps) {
  // Close on escape key
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose()
    }
  }, [onClose])

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown)
      document.body.style.overflow = 'hidden'
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = ''
    }
  }, [isOpen, handleKeyDown])

  if (!isOpen) return null

  const formatTimestamp = (timestamp: string): string => {
    try {
      const date = new Date(timestamp)
      return date.toLocaleString('en-US', {
        weekday: 'short',
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

  const getSeverityBadge = (severity: string) => {
    const severityConfig: Record<string, { label: string; className: string }> = {
      critical: { label: 'Critical', className: 'bg-safety-red text-white' },
      high: { label: 'High', className: 'bg-safety-red/80 text-white' },
      medium: { label: 'Medium', className: 'bg-warning-amber text-white' },
      low: { label: 'Low', className: 'bg-muted text-foreground' },
    }
    const config = severityConfig[severity.toLowerCase()] || severityConfig.low
    return (
      <span className={cn('px-2 py-1 rounded text-sm font-medium', config.className)}>
        {config.label}
      </span>
    )
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      role="dialog"
      aria-modal="true"
      aria-labelledby="safety-modal-title"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div className="relative bg-card border border-safety-red/30 rounded-lg shadow-xl max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-start justify-between p-4 border-b border-border bg-safety-red/10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-safety-red/20 flex items-center justify-center">
              <svg
                className="w-5 h-5 text-safety-red"
                fill="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path d="M12 2L1 21h22L12 2zm0 3.17L20.04 19H3.96L12 5.17zM11 16h2v2h-2v-2zm0-6h2v4h-2v-4z"/>
              </svg>
            </div>
            <div>
              <h2 id="safety-modal-title" className="text-lg font-semibold text-safety-red">
                Safety Event Details
              </h2>
              <p className="text-sm text-muted-foreground">
                {isLoading ? 'Loading...' : event?.reason_code || 'Unknown'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-md hover:bg-muted transition-colors"
            aria-label="Close modal"
          >
            <svg className="w-5 h-5 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-4">
          {isLoading ? (
            <div className="space-y-4 animate-pulse">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="flex justify-between">
                  <div className="h-4 w-24 bg-muted rounded" />
                  <div className="h-4 w-32 bg-muted rounded" />
                </div>
              ))}
            </div>
          ) : event ? (
            <div className="space-y-4">
              {/* Severity Badge */}
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Severity</span>
                {getSeverityBadge(event.severity)}
              </div>

              {/* Asset Info */}
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Asset</span>
                <span className="font-medium">{event.asset_name}</span>
              </div>

              {event.area && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Area</span>
                  <span className="font-medium">{event.area}</span>
                </div>
              )}

              {/* Time */}
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Occurred</span>
                <span className="font-medium">{formatTimestamp(event.event_timestamp)}</span>
              </div>

              {/* Duration */}
              {event.duration_minutes && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Duration</span>
                  <span className="font-medium">{event.duration_minutes} min</span>
                </div>
              )}

              {/* Financial Impact */}
              {event.financial_impact && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Financial Impact</span>
                  <span className="font-medium text-warning-amber">
                    ${event.financial_impact.toLocaleString('en-US', {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                  </span>
                </div>
              )}

              {/* Status */}
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Status</span>
                <span className={cn(
                  'font-medium',
                  event.is_resolved ? 'text-success-green' : 'text-safety-red'
                )}>
                  {event.is_resolved ? 'Resolved' : 'Active'}
                </span>
              </div>

              {event.is_resolved && event.resolved_at && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Resolved At</span>
                  <span className="font-medium">{formatTimestamp(event.resolved_at)}</span>
                </div>
              )}

              {/* Description */}
              {event.description && (
                <div className="pt-4 border-t border-border">
                  <span className="text-sm text-muted-foreground block mb-2">Description</span>
                  <p className="text-foreground">{event.description}</p>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center text-muted-foreground py-8">
              No event details available
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-2 p-4 border-t border-border bg-muted/30">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-muted text-foreground rounded-md hover:bg-muted/80 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
