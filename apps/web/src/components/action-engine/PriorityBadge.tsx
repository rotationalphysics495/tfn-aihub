'use client'

import { cn } from '@/lib/utils'

/**
 * Priority Badge Component
 *
 * Displays the priority level badge for insight/evidence cards.
 * Follows Industrial Clarity design system with specific color coding:
 * - SAFETY: Safety Red (#DC2626) - RESERVED EXCLUSIVELY for safety incidents
 * - FINANCIAL: Amber (#F59E0B) - High financial impact items
 * - OEE: Yellow (#EAB308) - OEE threshold items
 *
 * @see Story 3.4 - Insight + Evidence Cards
 * @see AC #4 - Visual Hierarchy and Priority Styling
 */

export type PriorityType = 'SAFETY' | 'FINANCIAL' | 'OEE'

interface PriorityBadgeProps {
  priority: PriorityType
  className?: string
}

// Priority styling per Industrial Clarity design system
const priorityStyles: Record<
  PriorityType,
  {
    bgColor: string
    textColor: string
    borderColor: string
    label: string
  }
> = {
  SAFETY: {
    bgColor: 'bg-[#DC2626]',
    textColor: 'text-white',
    borderColor: 'border-[#DC2626]',
    label: 'SAFETY',
  },
  FINANCIAL: {
    bgColor: 'bg-[#F59E0B]',
    textColor: 'text-[#1F2937]',
    borderColor: 'border-[#F59E0B]',
    label: 'FINANCIAL',
  },
  OEE: {
    bgColor: 'bg-[#EAB308]',
    textColor: 'text-[#1F2937]',
    borderColor: 'border-[#EAB308]',
    label: 'OEE',
  },
}

export function PriorityBadge({ priority, className }: PriorityBadgeProps) {
  const style = priorityStyles[priority]

  return (
    <span
      className={cn(
        'inline-flex items-center justify-center',
        'px-3 py-1 rounded-md',
        'text-base font-bold tracking-wide', // 16px minimum for glanceability
        'border',
        style.bgColor,
        style.textColor,
        style.borderColor,
        className
      )}
      role="status"
      aria-label={`Priority: ${style.label}`}
    >
      {style.label}
    </span>
  )
}

/**
 * Get border color class for card based on priority
 */
export function getPriorityBorderColor(priority: PriorityType): string {
  switch (priority) {
    case 'SAFETY':
      return 'border-l-[#DC2626]'
    case 'FINANCIAL':
      return 'border-l-[#F59E0B]'
    case 'OEE':
      return 'border-l-[#EAB308]'
    default:
      return 'border-l-industrial-400'
  }
}

/**
 * Get accent color for card background based on priority
 */
export function getPriorityAccentBg(priority: PriorityType): string {
  switch (priority) {
    case 'SAFETY':
      return 'bg-safety-red-light/10 dark:bg-safety-red-dark/10'
    case 'FINANCIAL':
      return 'bg-warning-amber-light/10 dark:bg-warning-amber-dark/10'
    case 'OEE':
      return 'bg-[#EAB308]/5 dark:bg-[#EAB308]/10'
    default:
      return ''
  }
}
