'use client'

import { useRouter } from 'next/navigation'
import { AlertTriangle, DollarSign, Info, ChevronRight } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { ActionItem, ActionCategory } from '@/hooks/useDailyActions'

/**
 * Action Item Card Component
 *
 * Displays a single action item with priority indicators and visual hierarchy.
 *
 * @see Story 3.3 - Action List Primary View
 * @see AC #3 - Action Item Card Display
 * @see AC #4 - Action Priority Ordering
 * @see AC #8 - Industrial Clarity Visual Compliance
 */

interface ActionItemCardProps {
  action: ActionItem
  rank: number
  className?: string
}

// Priority icon mapping per AC #3
const categoryIcons: Record<ActionCategory, typeof AlertTriangle> = {
  safety: AlertTriangle,
  oee: Info,
  financial: DollarSign,
}

// Priority colors per Industrial Clarity - safety red ONLY for safety items
const categoryStyles: Record<ActionCategory, {
  iconColor: string
  badgeVariant: 'safety' | 'warning' | 'info'
  label: string
}> = {
  safety: {
    iconColor: 'text-safety-red',
    badgeVariant: 'safety',
    label: 'Safety',
  },
  oee: {
    iconColor: 'text-info-blue',
    badgeVariant: 'info',
    label: 'Performance',
  },
  financial: {
    iconColor: 'text-warning-amber',
    badgeVariant: 'warning',
    label: 'Financial',
  },
}

// Priority level styles
const priorityStyles: Record<string, string> = {
  critical: 'border-l-4 border-l-safety-red',
  high: 'border-l-4 border-l-warning-amber',
  medium: 'border-l-4 border-l-info-blue',
  low: 'border-l-4 border-l-industrial-400',
}

export function ActionItemCard({ action, rank, className }: ActionItemCardProps) {
  const router = useRouter()
  const Icon = categoryIcons[action.category]
  const style = categoryStyles[action.category]
  const priorityBorder = priorityStyles[action.priority_level] || ''

  // Format financial impact for display
  const formatCurrency = (value: number): string => {
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`
    }
    if (value >= 1000) {
      return `$${(value / 1000).toFixed(1)}K`
    }
    return `$${value.toFixed(0)}`
  }

  // Handle card click for drill-down (Story 3.4 integration)
  const handleClick = () => {
    // Navigate to action detail view (Story 3.4)
    router.push(`/morning-report/action/${action.id}`)
  }

  return (
    <Card
      mode="retrospective"
      className={cn(
        'cursor-pointer transition-all duration-200',
        'hover:shadow-md hover:scale-[1.01]',
        'focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
        priorityBorder,
        action.category === 'safety' && 'bg-safety-red-light/10 dark:bg-safety-red-dark/10',
        className
      )}
      onClick={handleClick}
      tabIndex={0}
      role="button"
      aria-label={`Action ${rank}: ${action.recommendation_text}`}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          handleClick()
        }
      }}
    >
      <CardContent className="p-4 md:p-6">
        <div className="flex items-start gap-4">
          {/* Rank indicator - AC #4 */}
          <div
            className={cn(
              'flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center',
              'text-xl font-bold',
              action.category === 'safety'
                ? 'bg-safety-red text-white'
                : 'bg-industrial-200 dark:bg-industrial-700 text-industrial-700 dark:text-industrial-200'
            )}
          >
            #{rank}
          </div>

          {/* Main content */}
          <div className="flex-1 min-w-0">
            {/* Header row with badge and icon */}
            <div className="flex items-center gap-2 mb-2">
              <Icon
                className={cn('w-5 h-5 flex-shrink-0', style.iconColor)}
                aria-hidden="true"
              />
              <Badge
                variant={style.badgeVariant}
                className="text-xs"
              >
                {style.label}
              </Badge>
              {action.asset_name && (
                <span className="text-sm text-muted-foreground truncate">
                  {action.asset_name}
                </span>
              )}
            </div>

            {/* Action title - AC #8: 24px+ for key values */}
            <h3 className="text-xl md:text-2xl font-semibold text-foreground mb-2 leading-tight">
              {action.recommendation_text}
            </h3>

            {/* Supporting detail - AC #8: minimum 18px body */}
            <p className="text-base text-muted-foreground mb-3">
              {action.evidence_summary}
            </p>

            {/* Metrics row */}
            <div className="flex flex-wrap items-center gap-3 text-sm">
              {/* Primary metric */}
              <span className="font-medium text-foreground">
                {action.primary_metric_value}
              </span>

              {/* Financial impact if applicable */}
              {action.financial_impact_usd > 0 && (
                <span className="text-warning-amber font-semibold">
                  {formatCurrency(action.financial_impact_usd)} impact
                </span>
              )}

              {/* Priority level indicator */}
              <span
                className={cn(
                  'text-xs px-2 py-0.5 rounded',
                  action.priority_level === 'critical' && 'bg-safety-red-light text-safety-red-dark dark:bg-safety-red-dark/20 dark:text-safety-red',
                  action.priority_level === 'high' && 'bg-warning-amber-light text-warning-amber-dark dark:bg-warning-amber-dark/20 dark:text-warning-amber',
                  action.priority_level === 'medium' && 'bg-info-blue-light text-info-blue-dark dark:bg-info-blue-dark/20 dark:text-info-blue',
                  action.priority_level === 'low' && 'bg-industrial-200 text-industrial-600 dark:bg-industrial-700 dark:text-industrial-400'
                )}
              >
                {action.priority_level.charAt(0).toUpperCase() + action.priority_level.slice(1)} Priority
              </span>
            </div>
          </div>

          {/* Drill-down indicator */}
          <ChevronRight
            className="w-6 h-6 text-muted-foreground flex-shrink-0 self-center"
            aria-hidden="true"
          />
        </div>
      </CardContent>
    </Card>
  )
}
