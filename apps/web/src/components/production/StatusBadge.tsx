'use client'

import { cn } from '@/lib/utils'

/**
 * Status Badge for Throughput Performance
 *
 * Visual indicator for production throughput status following Industrial Clarity design.
 *
 * CRITICAL: Does NOT use safety-red. Safety red is RESERVED EXCLUSIVELY for safety incidents.
 * Production status uses:
 * - on_target: success green (#10B981)
 * - behind: warning amber (#F59E0B)
 * - critical: warning amber-dark (#B45309)
 *
 * @see Story 2.3 - AC #3 Status Indicators
 */

export type ThroughputStatus = 'on_target' | 'behind' | 'critical'

interface StatusBadgeProps {
  status: ThroughputStatus
  className?: string
  size?: 'sm' | 'md' | 'lg'
}

const statusConfig: Record<ThroughputStatus, {
  label: string
  bgClass: string
  textClass: string
  borderClass: string
}> = {
  on_target: {
    label: 'On Target',
    bgClass: 'bg-success-green-light dark:bg-success-green-dark/20',
    textClass: 'text-success-green-dark dark:text-success-green',
    borderClass: 'border-success-green',
  },
  behind: {
    label: 'Behind',
    bgClass: 'bg-warning-amber-light dark:bg-warning-amber-dark/20',
    textClass: 'text-warning-amber-dark dark:text-warning-amber',
    borderClass: 'border-warning-amber',
  },
  critical: {
    label: 'Critical',
    bgClass: 'bg-warning-amber-light dark:bg-warning-amber-dark/30',
    textClass: 'text-warning-amber-dark dark:text-warning-amber',
    borderClass: 'border-warning-amber-dark',
  },
}

const sizeConfig = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-2.5 py-1 text-sm',
  lg: 'px-3 py-1.5 text-base',
}

export function StatusBadge({ status, className, size = 'md' }: StatusBadgeProps) {
  const config = statusConfig[status]

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-md border font-semibold',
        config.bgClass,
        config.textClass,
        config.borderClass,
        sizeConfig[size],
        className
      )}
      role="status"
      aria-label={`Production status: ${config.label}`}
    >
      {config.label}
    </span>
  )
}
