'use client'

import Link from 'next/link'
import { cn } from '@/lib/utils'
import type { SafetyData } from '@/hooks/useLivePulse'

/**
 * Live Pulse Safety Alert Indicator Component
 *
 * Displays safety alert status in the Live Pulse ticker:
 * - Prominent "Safety Red" indicator for active incidents
 * - Takes visual priority over all other metrics
 * - Links to Safety Alert System for details
 *
 * IMPORTANT: "Safety Red" (#DC2626) is ONLY used for actual safety incidents
 *
 * @see Story 2.9 - Live Pulse Ticker
 * @see AC #4 - Safety Alert Integration
 * @see AC #7 - Industrial Clarity Compliance
 */

interface LivePulseSafetyIndicatorProps {
  data: SafetyData | null
  isLoading?: boolean
  className?: string
}

export function LivePulseSafetyIndicator({
  data,
  isLoading = false,
  className,
}: LivePulseSafetyIndicatorProps) {
  if (isLoading) {
    return (
      <div className={cn('animate-pulse', className)}>
        <div className="h-16 bg-live-surface/50 rounded-lg" />
      </div>
    )
  }

  // No active incidents - show safe status
  if (!data?.has_active_incident || data.active_incidents.length === 0) {
    return (
      <div className={cn(
        'flex items-center gap-3 p-4 rounded-lg',
        'bg-success-green-light dark:bg-success-green-dark/20',
        'border border-success-green/30',
        className
      )}>
        <div className="flex-shrink-0">
          <svg
            className="w-6 h-6 text-success-green"
            fill="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              fillRule="evenodd"
              d="M12 2.25c-5.385 0-9.75 4.365-9.75 9.75s4.365 9.75 9.75 9.75 9.75-4.365 9.75-9.75S17.385 2.25 12 2.25zm-1.72 6.97a.75.75 0 10-1.06 1.06L10.94 12l-1.72 1.72a.75.75 0 101.06 1.06L12 13.06l1.72 1.72a.75.75 0 101.06-1.06L13.06 12l1.72-1.72a.75.75 0 10-1.06-1.06L12 10.94l-1.72-1.72z"
              clipRule="evenodd"
            />
          </svg>
        </div>
        <div>
          <p className="font-semibold text-success-green">No Active Safety Incidents</p>
          <p className="text-sm text-muted-foreground">All systems operating safely</p>
        </div>
      </div>
    )
  }

  const incidentCount = data.active_incidents.length

  return (
    <div className={cn('space-y-3', className)}>
      {/* Safety Red Alert Banner - Takes visual priority */}
      <Link
        href="/dashboard/safety"
        className={cn(
          'flex items-center gap-3 p-4 rounded-lg',
          // Safety Red - EXCLUSIVELY for safety incidents
          'bg-safety-red text-white',
          'animate-safety-pulse',
          'hover:bg-safety-red-dark transition-colors',
          'focus:outline-none focus:ring-2 focus:ring-safety-red focus:ring-offset-2'
        )}
        aria-label={`${incidentCount} active safety incident${incidentCount === 1 ? '' : 's'}. Click to view details.`}
      >
        {/* Warning Icon */}
        <div className="flex-shrink-0">
          <svg
            className="w-8 h-8"
            fill="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path d="M12 2L1 21h22L12 2zm0 3.17L20.04 19H3.96L12 5.17zM11 16h2v2h-2v-2zm0-6h2v4h-2v-4z"/>
          </svg>
        </div>

        {/* Alert Content */}
        <div className="flex-1">
          <p className="text-xl font-bold">
            {incidentCount} Active Safety Incident{incidentCount === 1 ? '' : 's'}
          </p>
          <p className="text-sm text-white/90">
            Immediate attention required
          </p>
        </div>

        {/* Arrow indicator */}
        <svg
          className="w-6 h-6 flex-shrink-0"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 5l7 7-7 7"
          />
        </svg>
      </Link>

      {/* Incident List */}
      <ul className="space-y-2">
        {data.active_incidents.slice(0, 3).map((incident) => (
          <li
            key={incident.id}
            className={cn(
              'flex items-center justify-between text-sm',
              'bg-safety-red-light dark:bg-safety-red-dark/20',
              'border border-safety-red/30',
              'px-3 py-2 rounded-md'
            )}
          >
            <div className="flex items-center gap-2">
              <span className="inline-flex h-2 w-2 rounded-full bg-safety-red animate-pulse" />
              <span className="font-medium text-safety-red dark:text-safety-red-light">
                {incident.asset_name}
              </span>
            </div>
            <span className="text-xs text-muted-foreground uppercase">
              {incident.severity}
            </span>
          </li>
        ))}
      </ul>

      {data.active_incidents.length > 3 && (
        <p className="text-xs text-muted-foreground text-center">
          +{data.active_incidents.length - 3} more incidents
        </p>
      )}
    </div>
  )
}
