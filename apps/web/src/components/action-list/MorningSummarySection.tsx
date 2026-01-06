'use client'

import { AlertTriangle, TrendingDown, Gauge, Calendar, Sparkles } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useDailyActions } from '@/hooks/useDailyActions'
import { SummarySkeleton } from './ActionListSkeleton'
import { cn } from '@/lib/utils'

/**
 * Morning Summary Section Component
 *
 * Displays key metrics and summary for yesterday's performance (T-1 data).
 *
 * @see Story 3.3 - Action List Primary View
 * @see AC #6 - Morning Summary Section
 * @see AC #8 - Industrial Clarity Visual Compliance
 */

interface MorningSummarySectionProps {
  className?: string
}

// Format date for display
function formatReportDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

// Format currency for display
function formatCurrency(value: number): string {
  if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(1)}M`
  }
  if (value >= 1000) {
    return `$${(value / 1000).toFixed(1)}K`
  }
  return `$${value.toFixed(0)}`
}

export function MorningSummarySection({ className }: MorningSummarySectionProps) {
  const { data, isLoading, summary } = useDailyActions()

  // Loading state
  if (isLoading && !data) {
    return <SummarySkeleton className={className} />
  }

  // Get report date or use yesterday as default
  const reportDate = data?.report_date
    ? formatReportDate(data.report_date)
    : formatReportDate(new Date(Date.now() - 86400000).toISOString())

  // Calculate placeholder OEE (would come from API in production)
  // For now, we'll estimate based on whether there are OEE-related action items
  const hasOeeIssues = summary.oeeCount > 0

  return (
    <Card mode="retrospective" className={cn('', className)}>
      <CardContent className="p-4 md:p-6">
        {/* Header with date context - AC #1, #6 */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
          <div>
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <Calendar className="w-4 h-4" aria-hidden="true" />
              <span className="text-sm font-medium">Yesterday&apos;s Performance</span>
            </div>
            <h2 className="text-lg md:text-xl font-semibold text-foreground">
              {reportDate}
            </h2>
          </div>

          <Badge variant="retrospective" className="self-start sm:self-center">
            T-1 Data
          </Badge>
        </div>

        {/* Key metrics at a glance - AC #6 */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 md:gap-6">
          {/* Total Action Items */}
          <div className="flex items-center gap-3 p-3 rounded-lg bg-retrospective-surface dark:bg-retrospective-surface-dark">
            <div className="w-10 h-10 rounded-full bg-industrial-200 dark:bg-industrial-700 flex items-center justify-center">
              <span className="text-lg font-bold text-foreground">
                {summary.totalActions}
              </span>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Action Items</p>
              <p className="text-base font-medium text-foreground">
                {summary.totalActions === 0 ? 'None' : `${summary.totalActions} require attention`}
              </p>
            </div>
          </div>

          {/* Safety Events - AC #6 */}
          <div
            className={cn(
              'flex items-center gap-3 p-3 rounded-lg',
              summary.safetyCount > 0
                ? 'bg-safety-red-light/50 dark:bg-safety-red-dark/20'
                : 'bg-retrospective-surface dark:bg-retrospective-surface-dark'
            )}
          >
            <div
              className={cn(
                'w-10 h-10 rounded-full flex items-center justify-center',
                summary.safetyCount > 0
                  ? 'bg-safety-red'
                  : 'bg-industrial-200 dark:bg-industrial-700'
              )}
            >
              <AlertTriangle
                className={cn(
                  'w-5 h-5',
                  summary.safetyCount > 0 ? 'text-white' : 'text-muted-foreground'
                )}
                aria-hidden="true"
              />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Safety Events</p>
              <p
                className={cn(
                  'text-base font-medium',
                  summary.safetyCount > 0 ? 'text-safety-red' : 'text-foreground'
                )}
              >
                {summary.safetyCount === 0 ? 'None reported' : `${summary.safetyCount} event${summary.safetyCount > 1 ? 's' : ''}`}
              </p>
            </div>
          </div>

          {/* Financial Impact - AC #6 */}
          <div className="flex items-center gap-3 p-3 rounded-lg bg-retrospective-surface dark:bg-retrospective-surface-dark">
            <div
              className={cn(
                'w-10 h-10 rounded-full flex items-center justify-center',
                summary.financialCount > 0
                  ? 'bg-warning-amber'
                  : 'bg-industrial-200 dark:bg-industrial-700'
              )}
            >
              <TrendingDown
                className={cn(
                  'w-5 h-5',
                  summary.financialCount > 0 ? 'text-white' : 'text-muted-foreground'
                )}
                aria-hidden="true"
              />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Financial Items</p>
              <p
                className={cn(
                  'text-base font-medium',
                  summary.financialCount > 0 ? 'text-warning-amber-dark dark:text-warning-amber' : 'text-foreground'
                )}
              >
                {summary.financialCount === 0 ? 'None flagged' : `${summary.financialCount} item${summary.financialCount > 1 ? 's' : ''}`}
              </p>
            </div>
          </div>
        </div>

        {/* AI Smart Summary placeholder slot - AC #6, Story 3.5 integration */}
        <div className="mt-4 pt-4 border-t border-retrospective-border dark:border-retrospective-border-dark">
          <div className="flex items-start gap-2">
            <Sparkles
              className="w-4 h-4 text-info-blue flex-shrink-0 mt-0.5"
              aria-hidden="true"
            />
            <div className="flex-1">
              <p className="text-sm font-medium text-muted-foreground mb-1">
                AI Summary
              </p>
              {/* Placeholder for Story 3.5 - Smart Summary Generator */}
              <p className="text-base text-muted-foreground italic">
                {summary.totalActions === 0
                  ? 'All systems operating within normal parameters. No immediate attention required.'
                  : summary.safetyCount > 0
                    ? `${summary.safetyCount} safety event${summary.safetyCount > 1 ? 's' : ''} require immediate attention. Review safety items first before addressing ${summary.oeeCount + summary.financialCount} other action items.`
                    : `${summary.totalActions} action item${summary.totalActions > 1 ? 's' : ''} identified for review. Focus on ${summary.oeeCount > 0 ? 'OEE performance' : 'financial impact'} items to optimize plant operations.`}
              </p>
              <p className="text-xs text-muted-foreground mt-2">
                Powered by AI analysis (enhanced summary coming in Story 3.5)
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
