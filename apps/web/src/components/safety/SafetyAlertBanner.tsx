'use client'

import { useCallback } from 'react'
import Link from 'next/link'
import { cn } from '@/lib/utils'

/**
 * Safety Alert Banner Component
 *
 * Displays a prominent "Safety Red" banner when active safety alerts exist.
 * Designed for "glanceability" - readable from 3 feet away on a tablet.
 *
 * @see Story 2.6 - Safety Alert System
 * @see AC #3 - "Safety Red" visual indicator distinct from all other status colors
 * @see AC #4 - Prominent display with glanceability (readable from 3 feet)
 * @see AC #5 - Links to specific asset
 * @see AC #6 - Persists until acknowledged
 */

export interface SafetyAlert {
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
}

interface SafetyAlertBannerProps {
  alerts: SafetyAlert[]
  onAcknowledge?: (eventId: string) => void
  onViewDetails?: (alert: SafetyAlert) => void
  className?: string
}

export function SafetyAlertBanner({
  alerts,
  onAcknowledge,
  onViewDetails,
  className,
}: SafetyAlertBannerProps) {
  // Filter to only show unacknowledged alerts
  const activeAlerts = alerts.filter(alert => !alert.acknowledged)

  const handleAcknowledge = useCallback((e: React.MouseEvent, eventId: string) => {
    e.preventDefault()
    e.stopPropagation()
    onAcknowledge?.(eventId)
  }, [onAcknowledge])

  const formatTimeAgo = (timestamp: string): string => {
    try {
      const date = new Date(timestamp)
      const now = new Date()
      const diffMs = now.getTime() - date.getTime()
      const diffMins = Math.floor(diffMs / 60000)

      if (diffMins < 1) return 'Just now'
      if (diffMins < 60) return `${diffMins} min ago`

      const diffHours = Math.floor(diffMins / 60)
      if (diffHours < 24) return `${diffHours} hr ago`

      const diffDays = Math.floor(diffHours / 24)
      return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`
    } catch {
      return 'Recently'
    }
  }

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
  }

  if (activeAlerts.length === 0) {
    return null
  }

  // Show the most recent alert prominently
  const primaryAlert = activeAlerts[0]
  const additionalCount = activeAlerts.length - 1

  return (
    <div
      className={cn(
        // Safety Red exclusive styling - DO NOT use for non-safety elements
        'bg-safety-red text-white',
        // High contrast for glanceability (AC #4)
        'rounded-lg shadow-lg',
        // Pulsing animation for attention
        'animate-safety-pulse',
        className
      )}
      role="alert"
      aria-live="assertive"
      aria-label={`Safety Alert: ${primaryAlert.reason_code} on ${primaryAlert.asset_name}`}
    >
      {/* Main Alert Row - Glanceable (readable from 3 feet) */}
      <div className="flex items-center justify-between p-4 gap-4">
        <div className="flex items-center gap-4 flex-1 min-w-0">
          {/* Warning Icon - Large for visibility */}
          <div className="flex-shrink-0 w-12 h-12 rounded-full bg-white/20 flex items-center justify-center">
            <svg
              className="w-7 h-7 text-white"
              fill="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path d="M12 2L1 21h22L12 2zm0 3.17L20.04 19H3.96L12 5.17zM11 16h2v2h-2v-2zm0-6h2v4h-2v-4z"/>
            </svg>
          </div>

          {/* Alert Content - Large font for glanceability */}
          <div className="flex-1 min-w-0">
            {/* Primary Line - 18px+ for AC #4 glanceability */}
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold tracking-wide">
                SAFETY ALERT
              </span>
              {additionalCount > 0 && (
                <span className="bg-white/30 text-white text-sm font-semibold px-2 py-0.5 rounded">
                  +{additionalCount} more
                </span>
              )}
            </div>

            {/* Secondary Line - Asset and reason */}
            <p className="text-base font-medium mt-1 truncate">
              {primaryAlert.reason_code} detected on{' '}
              <Link
                href={`/dashboard/assets/${primaryAlert.asset_id}`}
                className="underline hover:no-underline font-bold"
                onClick={(e) => e.stopPropagation()}
              >
                {primaryAlert.asset_name}
              </Link>
            </p>

            {/* Tertiary Line - Time and financial impact */}
            <p className="text-sm opacity-90 mt-1 flex items-center gap-3 flex-wrap">
              <span>Detected {formatTimeAgo(primaryAlert.event_timestamp)}</span>
              {primaryAlert.financial_impact && primaryAlert.financial_impact > 0 && (
                <>
                  <span className="text-white/60">|</span>
                  <span className="font-semibold">
                    Est. Impact: {formatCurrency(primaryAlert.financial_impact)}/hr
                  </span>
                </>
              )}
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2 flex-shrink-0">
          {/* View Details */}
          {onViewDetails && (
            <button
              onClick={() => onViewDetails(primaryAlert)}
              className="px-4 py-2 bg-white/20 hover:bg-white/30 text-white text-sm font-semibold rounded-md transition-colors"
              aria-label="View safety alert details"
            >
              Details
            </button>
          )}

          {/* Acknowledge/Dismiss */}
          {onAcknowledge && (
            <button
              onClick={(e) => handleAcknowledge(e, primaryAlert.id)}
              className="p-2 bg-white/20 hover:bg-white/30 rounded-md transition-colors"
              aria-label="Acknowledge and dismiss safety alert"
            >
              <svg
                className="w-5 h-5 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
