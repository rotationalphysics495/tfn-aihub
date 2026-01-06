'use client'

import { cn } from '@/lib/utils'

/**
 * OEE Status Badge Component
 *
 * Color-coded status indicator for OEE values.
 * Uses standard status colors (NOT Safety Red, which is reserved for incidents).
 *
 * @see Story 2.4 - OEE Metrics View
 * @see AC #8 - Color-coded status indicators: Green (>=85%), Yellow (70-84%), Red (<70%)
 */

export type OEEStatusType = 'green' | 'yellow' | 'red' | 'unknown'

interface OEEStatusBadgeProps {
  /** OEE status classification */
  status: OEEStatusType | string
  /** Optional: Show the label text */
  showLabel?: boolean
  /** Size variant */
  size?: 'sm' | 'md' | 'lg'
  /** Optional additional class names */
  className?: string
}

/**
 * Get status configuration based on OEE status.
 * IMPORTANT: Uses standard red (red-500), NOT safety-red which is reserved for incidents.
 */
function getStatusConfig(status: string): {
  label: string
  bgColor: string
  textColor: string
  dotColor: string
  description: string
} {
  switch (status) {
    case 'green':
      return {
        label: 'On Target',
        bgColor: 'bg-success-green-light dark:bg-success-green-dark/20',
        textColor: 'text-success-green-dark dark:text-success-green',
        dotColor: 'bg-success-green',
        description: 'OEE >= 85%',
      }
    case 'yellow':
      return {
        label: 'Attention',
        bgColor: 'bg-warning-amber-light dark:bg-warning-amber-dark/20',
        textColor: 'text-warning-amber-dark dark:text-warning-amber',
        dotColor: 'bg-warning-amber',
        description: 'OEE 70-84%',
      }
    case 'red':
      // Using standard red-500, NOT safety-red (reserved for safety incidents only)
      return {
        label: 'Critical',
        bgColor: 'bg-red-50 dark:bg-red-900/20',
        textColor: 'text-red-600 dark:text-red-400',
        dotColor: 'bg-red-500',
        description: 'OEE < 70%',
      }
    default:
      return {
        label: 'Unknown',
        bgColor: 'bg-muted',
        textColor: 'text-muted-foreground',
        dotColor: 'bg-muted-foreground',
        description: 'No data',
      }
  }
}

const sizeClasses = {
  sm: {
    badge: 'px-2 py-0.5 text-xs',
    dot: 'w-1.5 h-1.5',
  },
  md: {
    badge: 'px-2.5 py-1 text-sm',
    dot: 'w-2 h-2',
  },
  lg: {
    badge: 'px-3 py-1.5 text-base',
    dot: 'w-2.5 h-2.5',
  },
}

export function OEEStatusBadge({
  status,
  showLabel = true,
  size = 'md',
  className,
}: OEEStatusBadgeProps) {
  const config = getStatusConfig(status)
  const sizes = sizeClasses[size]

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-md font-medium',
        config.bgColor,
        config.textColor,
        sizes.badge,
        className,
      )}
      title={config.description}
    >
      <span className={cn('rounded-full', config.dotColor, sizes.dot)} />
      {showLabel && config.label}
    </span>
  )
}

/**
 * Compact OEE status dot (no text, just the indicator).
 */
export function OEEStatusDot({
  status,
  size = 'md',
  className,
}: Omit<OEEStatusBadgeProps, 'showLabel'>) {
  const config = getStatusConfig(status)
  const dotSizes = {
    sm: 'w-2 h-2',
    md: 'w-3 h-3',
    lg: 'w-4 h-4',
  }

  return (
    <span
      className={cn(
        'inline-block rounded-full',
        config.dotColor,
        dotSizes[size],
        className,
      )}
      title={`${config.label}: ${config.description}`}
    />
  )
}
