'use client'

import { useMemo } from 'react'
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'

/**
 * Pareto Chart Component
 *
 * Displays downtime duration per reason code as bars with cumulative percentage line.
 * Includes 80% threshold indicator for Pareto principle visualization.
 *
 * @see Story 2.5 - Downtime Pareto Analysis
 * @see AC #3 - Pareto Chart Visualization
 * @see UX Design - Industrial Clarity, readable at 3 feet
 */

export interface ParetoItem {
  reason_code: string
  total_minutes: number
  percentage: number
  cumulative_percentage: number
  financial_impact: number
  event_count: number
  is_safety_related: boolean
}

interface ParetoChartProps {
  data: ParetoItem[]
  threshold80Index: number | null
  isLive: boolean
  className?: string
}

// Color palette for Industrial Clarity design
const CHART_COLORS = {
  bar: {
    retrospective: 'hsl(210, 50%, 50%)',     // Cool blue for T-1
    live: 'hsl(200, 80%, 50%)',              // Vibrant blue for Live
  },
  barSafety: 'hsl(0, 72%, 51%)',             // Safety Red - reserved for safety issues only
  line: {
    retrospective: 'hsl(210, 30%, 40%)',     // Darker blue
    live: 'hsl(200, 60%, 40%)',              // Darker vibrant
  },
  threshold: 'hsl(0, 0%, 60%)',              // Neutral gray for 80% line
}

export function ParetoChart({ data, threshold80Index, isLive, className }: ParetoChartProps) {
  // Format data for chart
  const chartData = useMemo(() => {
    return data.map((item, index) => ({
      ...item,
      name: item.reason_code.length > 15
        ? `${item.reason_code.substring(0, 12)}...`
        : item.reason_code,
      fullName: item.reason_code,
      isAt80Threshold: threshold80Index !== null && index <= threshold80Index,
    }))
  }, [data, threshold80Index])

  const barColor = isLive ? CHART_COLORS.bar.live : CHART_COLORS.bar.retrospective
  const lineColor = isLive ? CHART_COLORS.line.live : CHART_COLORS.line.retrospective

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload?.length) return null

    const item = payload[0].payload as ParetoItem & { fullName: string }
    return (
      <div className="bg-card border border-border rounded-lg shadow-lg p-3 min-w-[200px]">
        <p className="font-semibold text-foreground mb-2">{item.fullName}</p>
        <div className="space-y-1 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Duration:</span>
            <span className="font-medium">{item.total_minutes} min</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">% of Total:</span>
            <span className="font-medium">{item.percentage.toFixed(1)}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Cumulative:</span>
            <span className="font-medium">{item.cumulative_percentage.toFixed(1)}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Events:</span>
            <span className="font-medium">{item.event_count}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Cost:</span>
            <span className="font-medium text-warning-amber">
              ${item.financial_impact.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
          </div>
          {item.is_safety_related && (
            <div className="mt-2 flex items-center gap-1 text-safety-red font-semibold">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2L1 21h22L12 2zm0 3.17L20.04 19H3.96L12 5.17zM11 16h2v2h-2v-2zm0-6h2v4h-2v-4z"/>
              </svg>
              Safety Issue
            </div>
          )}
        </div>
      </div>
    )
  }

  if (!data || data.length === 0) {
    return (
      <Card mode={isLive ? 'live' : 'retrospective'} className={className}>
        <CardHeader>
          <CardTitle className="text-lg">Downtime by Reason Code</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-[300px] text-muted-foreground">
            No downtime data available
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card mode={isLive ? 'live' : 'retrospective'} className={className}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Downtime by Reason Code</CardTitle>
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded"
                style={{ backgroundColor: barColor }}
              />
              <span className="text-muted-foreground">Duration (min)</span>
            </div>
            <div className="flex items-center gap-2">
              <div
                className="w-8 h-0.5"
                style={{ backgroundColor: lineColor }}
              />
              <span className="text-muted-foreground">Cumulative %</span>
            </div>
            <div className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded"
                style={{ backgroundColor: CHART_COLORS.barSafety }}
              />
              <span className="text-muted-foreground">Safety Issue</span>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-[350px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart
              data={chartData}
              margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="hsl(var(--border))"
                opacity={0.5}
              />
              <XAxis
                dataKey="name"
                angle={-45}
                textAnchor="end"
                interval={0}
                height={60}
                tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
              />
              <YAxis
                yAxisId="left"
                tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
                label={{
                  value: 'Duration (min)',
                  angle: -90,
                  position: 'insideLeft',
                  style: { textAnchor: 'middle', fill: 'hsl(var(--muted-foreground))' }
                }}
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                domain={[0, 100]}
                tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
                label={{
                  value: 'Cumulative %',
                  angle: 90,
                  position: 'insideRight',
                  style: { textAnchor: 'middle', fill: 'hsl(var(--muted-foreground))' }
                }}
              />
              <Tooltip content={<CustomTooltip />} />

              {/* 80% Threshold Reference Line */}
              <ReferenceLine
                yAxisId="right"
                y={80}
                stroke={CHART_COLORS.threshold}
                strokeDasharray="5 5"
                strokeWidth={2}
                label={{
                  value: '80%',
                  position: 'right',
                  fill: CHART_COLORS.threshold,
                  fontSize: 12,
                }}
              />

              {/* Bar chart for downtime duration */}
              <Bar
                yAxisId="left"
                dataKey="total_minutes"
                name="Duration"
                radius={[4, 4, 0, 0]}
              >
                {chartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.is_safety_related ? CHART_COLORS.barSafety : barColor}
                    opacity={entry.isAt80Threshold ? 1 : 0.6}
                  />
                ))}
              </Bar>

              {/* Line chart for cumulative percentage */}
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="cumulative_percentage"
                name="Cumulative %"
                stroke={lineColor}
                strokeWidth={2}
                dot={{ fill: lineColor, strokeWidth: 2, r: 4 }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        {/* Pareto Principle Info */}
        {threshold80Index !== null && (
          <div className="mt-4 text-sm text-muted-foreground text-center">
            <span className="font-medium text-foreground">
              {threshold80Index + 1} of {data.length} reason codes
            </span>
            {' '}account for 80% of total downtime (Pareto Principle)
          </div>
        )}
      </CardContent>
    </Card>
  )
}
