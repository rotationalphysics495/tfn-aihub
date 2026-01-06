'use client'

import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'

/**
 * Cost of Loss Summary Widget
 *
 * Prominently displays total financial loss and key downtime metrics.
 * FR5 requirement: Financial impact displayed prominently.
 *
 * @see Story 2.5 - Downtime Pareto Analysis
 * @see AC #5 - Financial Impact Integration
 */

export interface CostOfLossSummaryData {
  total_financial_loss: number
  total_downtime_minutes: number
  total_downtime_hours: number
  top_reason_code: string | null
  top_reason_percentage: number | null
  safety_events_count: number
  safety_downtime_minutes: number
  data_source: string
  last_updated: string
}

interface CostOfLossWidgetProps {
  data: CostOfLossSummaryData | null
  isLive: boolean
  isLoading: boolean
  className?: string
}

export function CostOfLossWidget({
  data,
  isLive,
  isLoading,
  className,
}: CostOfLossWidgetProps) {
  // Format currency
  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
  }

  // Format hours
  const formatHours = (hours: number): string => {
    if (hours < 1) {
      return `${Math.round(hours * 60)} min`
    }
    return `${hours.toFixed(1)} hrs`
  }

  if (isLoading) {
    return (
      <Card mode={isLive ? 'live' : 'retrospective'} className={cn('animate-pulse', className)}>
        <CardContent className="p-6">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="space-y-2">
                <div className="h-4 w-24 bg-muted rounded" />
                <div className="h-8 w-32 bg-muted rounded" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!data) {
    return (
      <Card mode={isLive ? 'live' : 'retrospective'} className={className}>
        <CardContent className="p-6 text-center text-muted-foreground">
          No data available
        </CardContent>
      </Card>
    )
  }

  return (
    <Card mode={isLive ? 'live' : 'retrospective'} className={className}>
      <CardContent className="p-6">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Total Financial Loss - Primary Metric */}
          <div className="col-span-2 lg:col-span-1">
            <div className="text-sm font-medium text-muted-foreground mb-1">
              Total Cost of Loss
            </div>
            <div className="text-3xl font-bold text-warning-amber tracking-tight">
              {formatCurrency(data.total_financial_loss)}
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              Based on hourly rates
            </div>
          </div>

          {/* Total Downtime */}
          <div>
            <div className="text-sm font-medium text-muted-foreground mb-1">
              Total Downtime
            </div>
            <div className="text-2xl font-bold text-foreground">
              {formatHours(data.total_downtime_hours)}
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              {data.total_downtime_minutes} minutes
            </div>
          </div>

          {/* Top Reason Code */}
          <div>
            <div className="text-sm font-medium text-muted-foreground mb-1">
              Top Reason
            </div>
            {data.top_reason_code ? (
              <>
                <div className="text-lg font-semibold text-foreground truncate" title={data.top_reason_code}>
                  {data.top_reason_code.length > 18
                    ? `${data.top_reason_code.substring(0, 15)}...`
                    : data.top_reason_code}
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  {data.top_reason_percentage?.toFixed(1)}% of total
                </div>
              </>
            ) : (
              <div className="text-lg text-muted-foreground">--</div>
            )}
          </div>

          {/* Safety Events */}
          <div>
            <div className="text-sm font-medium text-muted-foreground mb-1">
              Safety Issues
            </div>
            <div className={cn(
              'text-2xl font-bold',
              data.safety_events_count > 0 ? 'text-safety-red' : 'text-success-green'
            )}>
              {data.safety_events_count}
            </div>
            {data.safety_events_count > 0 ? (
              <div className="flex items-center gap-1 text-xs text-safety-red mt-1">
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2L1 21h22L12 2zm0 3.17L20.04 19H3.96L12 5.17zM11 16h2v2h-2v-2zm0-6h2v4h-2v-4z"/>
                </svg>
                {data.safety_downtime_minutes} min downtime
              </div>
            ) : (
              <div className="text-xs text-success-green mt-1">
                No safety incidents
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
