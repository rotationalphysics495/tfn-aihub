'use client'

import { cn } from '@/lib/utils'

/**
 * Safety Indicator Component
 *
 * Displays the safety alert count in the Command Center header.
 * Uses "Safety Red" styling exclusively for safety incidents.
 *
 * @see Story 2.6 - Safety Alert System
 * @see AC #9 - Safety alert count visible in Command Center header/status area
 */

interface SafetyIndicatorProps {
  count: number
  onClick?: () => void
  className?: string
}

export function SafetyIndicator({
  count,
  onClick,
  className,
}: SafetyIndicatorProps) {
  // Don't render if no active alerts
  if (count <= 0) {
    return null
  }

  return (
    <button
      onClick={onClick}
      className={cn(
        // Safety Red exclusive styling
        'inline-flex items-center gap-2 px-3 py-1.5 rounded-full',
        'bg-safety-red text-white',
        'font-semibold text-sm',
        // Pulsing animation for attention
        'animate-safety-pulse',
        // Interactive states
        'hover:bg-safety-red-dark transition-colors',
        'focus:outline-none focus:ring-2 focus:ring-safety-red focus:ring-offset-2',
        className
      )}
      aria-label={`${count} active safety alert${count === 1 ? '' : 's'}. Click to view.`}
    >
      {/* Warning Icon */}
      <svg
        className="w-4 h-4"
        fill="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path d="M12 2L1 21h22L12 2zm0 3.17L20.04 19H3.96L12 5.17zM11 16h2v2h-2v-2zm0-6h2v4h-2v-4z"/>
      </svg>

      {/* Count */}
      <span>{count}</span>

      {/* Screen reader text */}
      <span className="sr-only">
        {count} active safety alert{count === 1 ? '' : 's'}
      </span>
    </button>
  )
}
