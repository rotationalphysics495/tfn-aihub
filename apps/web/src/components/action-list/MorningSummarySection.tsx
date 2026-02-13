'use client'

import { useMemo, useCallback, type ReactNode } from 'react'
import { AlertTriangle, TrendingDown, Gauge, Calendar, Sparkles, RefreshCw, AlertCircle, Wand2, MessageSquare } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { format, subDays, startOfDay } from 'date-fns'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useDailyActions } from '@/hooks/useDailyActions'
import { useSmartSummary } from '@/hooks/useSmartSummary'
import { DateNavigation } from '@/components/report'
import { useChatContext } from '@/components/chat'
import { SuggestedQuestions } from './SuggestedQuestions'
import { SummarySkeleton } from './ActionListSkeleton'
import { cn } from '@/lib/utils'
import { linkifyAssetNames, extractAssetNames } from '@/lib/linkifyAssets'

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
  reportDate?: string
  onDateChange?: (date: Date) => void
  selectedDate?: Date
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

// Strip inline citation tags like [Source: table, date] and [Asset: name, metric: value]
// These are stored for traceability but shouldn't be shown to users in the summary
function cleanSummaryText(text: string): string {
  return text
    .replace(/\s*\[Source:\s*[^\]]*\]/g, '')
    .replace(/\s*\[Asset:\s*[^\]]*\]/g, '')
    .trim()
}

function getDateBadgeText(selectedDate?: Date): string {
  if (!selectedDate) return 'T-1 Data'
  const yesterday = startOfDay(subDays(new Date(), 1))
  if (startOfDay(selectedDate).getTime() === yesterday.getTime()) {
    return 'T-1 Data'
  }
  return format(selectedDate, 'MMM d') + ' Data'
}

function getPerformanceLabel(selectedDate?: Date): string {
  if (!selectedDate) return "Yesterday's Performance"
  const yesterday = startOfDay(subDays(new Date(), 1))
  if (startOfDay(selectedDate).getTime() === yesterday.getTime()) {
    return "Yesterday's Performance"
  }
  return format(selectedDate, 'MMM d') + ' Performance'
}

export function MorningSummarySection({ className, reportDate: reportDateProp, onDateChange, selectedDate }: MorningSummarySectionProps) {
  const { data, isLoading, summary } = useDailyActions(reportDateProp ? { reportDate: reportDateProp } : {})
  const { data: smartSummary, isLoading: isSummaryLoading, isGenerating, error: summaryError, refetch: refetchSummary, regenerate: regenerateSummary, generate: generateSummary, hasSummary, canGenerate } = useSmartSummary(reportDateProp ? { reportDate: reportDateProp, autoGenerate: false } : {})
  const { openChatWithContext, openChatWithQuestion } = useChatContext()

  // Story 19.2: Extract asset names and build lookup map for asset linkification
  const assetNames = useMemo(
    () => extractAssetNames((data?.actions ?? []).map((a) => ({ asset_name: a.asset_name }))),
    [data?.actions]
  )

  const assetNameToId = useMemo(() => {
    const map = new Map<string, string>()
    for (const action of data?.actions ?? []) {
      const key = action.asset_name?.toLowerCase()
      if (key && !map.has(key)) {
        map.set(key, action.id)
      }
    }
    return map
  }, [data?.actions])

  // Story 19.2: Scroll to and highlight a target action card
  const scrollToAsset = useCallback((assetName: string) => {
    const target = document.querySelector(`[data-asset-name="${CSS.escape(assetName)}"]`)
    target?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    if (target) {
      target.classList.add('highlight-flash')
      setTimeout(() => {
        target.classList.remove('highlight-flash')
      }, 1500)
    }
  }, [])

  // Story 19.2: Process React children to replace [[ASSET:name]] tokens with clickable buttons
  const processTextChildren = useCallback(
    (children: ReactNode): ReactNode => {
      if (!children) return children
      const childArray = Array.isArray(children) ? children : [children]
      return childArray.map((child, i) => {
        if (typeof child === 'string') {
          const parts = child.split(/\[\[ASSET:(.*?)\]\]/g)
          if (parts.length === 1) return child
          return parts.map((part, j) => {
            if (j % 2 === 1) {
              // This is the captured asset name
              const assetName = part
              return (
                <button
                  key={`asset-${i}-${j}`}
                  type="button"
                  className="text-info-blue hover:underline cursor-pointer inline bg-transparent border-none p-0 text-left text-[length:inherit] [font-family:inherit]"
                  onClick={(e) => {
                    if (e.metaKey || e.ctrlKey) {
                      const actionId = assetNameToId.get(assetName.toLowerCase())
                      if (actionId) {
                        window.open(`/morning-report/action/${actionId}`, '_blank')
                      }
                    } else {
                      scrollToAsset(assetName)
                    }
                  }}
                >
                  {assetName}
                </button>
              )
            }
            return part || null
          })
        }
        // For React elements, recursively process their children
        if (child && typeof child === 'object' && 'props' in child) {
          const { children: nestedChildren, ...restProps } = child.props
          return { ...child, props: { ...restProps, children: processTextChildren(nestedChildren) }, key: child.key ?? `wrap-${i}` }
        }
        return child
      })
    },
    [assetNameToId, scrollToAsset]
  )

  // Story 19.2: Custom ReactMarkdown component overrides for asset link rendering
  const markdownComponents = useMemo(
    () => ({
      p: ({ children }: { children?: ReactNode }) => <p>{processTextChildren(children)}</p>,
      li: ({ children }: { children?: ReactNode }) => <li>{processTextChildren(children)}</li>,
      strong: ({ children }: { children?: ReactNode }) => <strong>{processTextChildren(children)}</strong>,
      em: ({ children }: { children?: ReactNode }) => <em>{processTextChildren(children)}</em>,
    }),
    [processTextChildren]
  )

  // Loading state
  if (isLoading && !data) {
    return <SummarySkeleton className={className} />
  }

  // Get report date or use yesterday as default
  const displayDate = data?.report_date
    ? formatReportDate(data.report_date)
    : formatReportDate(new Date(Date.now() - 86400000).toISOString())

  // Calculate placeholder OEE (would come from API in production)
  // For now, we'll estimate based on whether there are OEE-related action items
  const hasOeeIssues = summary.oeeCount > 0

  return (
    <Card mode="retrospective" className={cn('', className)}>
      <CardContent className="p-4 md:p-6">
        {/* Header with date context - AC #1, #6, Story 17.1 */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
          <div>
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <Calendar className="w-4 h-4" aria-hidden="true" />
              <span className="text-sm font-medium">{getPerformanceLabel(selectedDate)}</span>
            </div>
            <h2 className="text-lg md:text-xl font-semibold text-foreground">
              {displayDate}
            </h2>
          </div>

          <div className="flex items-center gap-2 self-start sm:self-center">
            <Badge variant="retrospective">
              {getDateBadgeText(selectedDate)}
            </Badge>
            {onDateChange && selectedDate && (
              <DateNavigation date={selectedDate} onDateChange={onDateChange} />
            )}
          </div>
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

        {/* AI Smart Summary - Story 3.5 */}
        <div className="mt-4 pt-4 border-t border-retrospective-border dark:border-retrospective-border-dark">
          <div className="flex items-start gap-2">
            <Sparkles
              className={cn(
                'w-4 h-4 flex-shrink-0 mt-0.5',
                isGenerating ? 'text-info-blue animate-pulse' : 'text-info-blue'
              )}
              aria-hidden="true"
            />
            <div className="flex-1">
              <div className="flex items-center justify-between mb-1">
                <p className="text-sm font-medium text-muted-foreground">
                  AI Summary
                  {smartSummary?.is_fallback && (
                    <span className="ml-2 text-xs text-warning-amber">(fallback)</span>
                  )}
                </p>
                {hasSummary && (
                  <button
                    onClick={() => regenerateSummary()}
                    className="text-muted-foreground hover:text-foreground transition-colors p-1 rounded"
                    title="Regenerate AI summary"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>

              {/* Loading / Generating state */}
              {(isSummaryLoading || isGenerating) && (
                <div className="space-y-1.5">
                  <div className="animate-pulse bg-industrial-200 dark:bg-industrial-700 rounded h-4 w-full" />
                  <div className="animate-pulse bg-industrial-200 dark:bg-industrial-700 rounded h-4 w-5/6" />
                  {isGenerating && (
                    <p className="text-xs text-info-blue mt-2">Generating AI analysis...</p>
                  )}
                </div>
              )}

              {/* Error state — fall back to basic template */}
              {!isSummaryLoading && !isGenerating && summaryError && (
                <div>
                  <p className="text-base text-muted-foreground italic">
                    {summary.totalActions === 0
                      ? 'All systems operating within normal parameters. No immediate attention required.'
                      : summary.safetyCount > 0
                        ? `${summary.safetyCount} safety event${summary.safetyCount > 1 ? 's' : ''} require immediate attention. Review safety items first before addressing ${summary.oeeCount + summary.financialCount} other action items.`
                        : `${summary.totalActions} action item${summary.totalActions > 1 ? 's' : ''} identified for review. Focus on ${summary.oeeCount > 0 ? 'OEE performance' : 'financial impact'} items to optimize plant operations.`}
                  </p>
                  <div className="flex items-center gap-1 mt-2">
                    <AlertCircle className="w-3 h-3 text-muted-foreground" />
                    <p className="text-xs text-muted-foreground">
                      AI summary unavailable &mdash;{' '}
                      <button
                        onClick={() => canGenerate ? generateSummary() : refetchSummary()}
                        className="underline hover:text-foreground transition-colors"
                      >
                        retry
                      </button>
                    </p>
                  </div>
                </div>
              )}

              {/* Real AI summary */}
              {!isSummaryLoading && !isGenerating && !summaryError && hasSummary && (
                <div>
                  <div className="text-sm text-foreground space-y-2 [&_ul]:list-disc [&_ul]:pl-4 [&_ul]:space-y-0.5 [&_li]:text-sm [&_strong]:font-semibold [&_strong]:text-foreground [&_h2]:text-sm [&_h2]:font-semibold [&_h2]:mt-3 [&_h2]:mb-1 [&_h3]:text-sm [&_h3]:font-semibold [&_h3]:mt-2 [&_h3]:mb-1 [&_p]:my-0">
                    <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                      {linkifyAssetNames(cleanSummaryText(smartSummary?.summary_text ?? ''), assetNames)}
                    </ReactMarkdown>
                  </div>
                  <div className="flex items-center justify-between mt-2">
                    <p className="text-xs text-muted-foreground">
                      Powered by AI analysis
                    </p>
                    {/* Story 19.1 AC#1: "Ask about this" button */}
                    <Button
                      variant="outline"
                      size="sm"
                      className="gap-1.5 text-xs h-7 border-info-blue/30 text-info-blue hover:bg-info-blue/10 hover:text-info-blue"
                      onClick={() => openChatWithContext({
                        summaryText: cleanSummaryText(smartSummary?.summary_text ?? ''),
                        actionItems: (data?.actions ?? []) as unknown as Array<Record<string, unknown>>,
                        reportDate: data?.report_date ?? '',
                      })}
                    >
                      <MessageSquare className="w-3.5 h-3.5" />
                      Ask about this
                    </Button>
                  </div>
                  {/* Story 19.3: Contextual follow-up suggestion chips */}
                  <SuggestedQuestions
                    actionItems={data?.actions ?? []}
                    summaryText={cleanSummaryText(smartSummary?.summary_text ?? '')}
                    reportDate={data?.report_date ?? ''}
                    onQuestionSelect={(question) =>
                      openChatWithQuestion(
                        {
                          summaryText: cleanSummaryText(smartSummary?.summary_text ?? ''),
                          actionItems: (data?.actions ?? []) as unknown as Array<Record<string, unknown>>,
                          reportDate: data?.report_date ?? '',
                        },
                        question
                      )
                    }
                  />
                </div>
              )}

              {/* On-demand generation prompt for historical dates */}
              {!isSummaryLoading && !isGenerating && !summaryError && !hasSummary && canGenerate && (
                <div className="text-center py-3">
                  <p className="text-sm text-muted-foreground mb-2">
                    No summary exists for this date. Generate one?
                  </p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => generateSummary()}
                    disabled={isGenerating}
                    className="gap-2"
                  >
                    <Wand2 className="w-4 h-4" />
                    Generate Summary
                  </Button>
                </div>
              )}

              {/* No summary and no error (shouldn't happen normally, but safe fallback) */}
              {!isSummaryLoading && !isGenerating && !summaryError && !hasSummary && !canGenerate && (
                <p className="text-base text-muted-foreground italic">
                  No AI summary available for this date.
                </p>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
