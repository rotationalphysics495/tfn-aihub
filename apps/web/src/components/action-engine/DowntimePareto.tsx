'use client'

import { useId, useMemo } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import { cn } from '@/lib/utils'
import type { DowntimeParetoResponse } from '@/hooks/useDowntimePareto'

interface DowntimeParetoProps {
  data: DowntimeParetoResponse | null
  className?: string
}

const PARETO_COLORS = {
  unplanned: 'hsl(210, 50%, 50%)',
  planned: 'hsl(210, 50%, 70%)',
  safety: 'hsl(0, 72%, 51%)',
}

const MAX_ITEMS = 5
const MAX_NAME_LENGTH = 15

function truncateName(name: string): string {
  if (name.length <= MAX_NAME_LENGTH) return name
  return `${name.substring(0, MAX_NAME_LENGTH)}…`
}

function isPlannedItem(item: { reason_code: string; is_planned?: boolean }): boolean {
  if (typeof item.is_planned === 'boolean') return item.is_planned
  return item.reason_code === 'Planned Maintenance'
}

export function DowntimePareto({ data, className }: DowntimeParetoProps) {
  const instanceId = useId()
  const patternId = `hatch-pattern-${instanceId}`

  const chartData = useMemo(() => {
    if (!data || !data.items || data.items.length === 0) return null

    const items = data.items.slice(0, MAX_ITEMS)
    return items.map((item) => ({
      ...item,
      name: truncateName(item.reason_code),
      fullName: item.reason_code,
      total_minutes: item.total_minutes,
      percentage: item.percentage,
      planned: isPlannedItem(item as { reason_code: string; is_planned?: boolean }),
    }))
  }, [data])

  if (!chartData) return null

  const height = Math.max(100, Math.min(150, chartData.length * 28 + 16))

  return (
    <div className={cn('w-full', className)} data-testid="downtime-pareto">
      {/* SVG pattern definition for hatched bars */}
      <svg width="0" height="0" style={{ position: 'absolute' }}>
        <defs>
          <pattern
            id={patternId}
            patternUnits="userSpaceOnUse"
            width="6"
            height="6"
            patternTransform="rotate(45)"
          >
            <line
              x1="0" y1="0" x2="0" y2="6"
              stroke={PARETO_COLORS.planned}
              strokeWidth="3"
            />
          </pattern>
        </defs>
      </svg>

      {/* Reason code labels with duration and percentage */}
      <div className="space-y-1 mb-1">
        {chartData.map((item) => (
          <div
            key={item.fullName}
            className="text-xs text-muted-foreground dark:text-muted-foreground"
            data-planned={String(item.planned)}
          >
            {item.name} {item.total_minutes}min ({item.percentage}%)
          </div>
        ))}
      </div>

      {/* Recharts horizontal bar chart */}
      <ResponsiveContainer width="100%" height={height}>
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 0, right: 0, bottom: 0, left: 0 }}
          barCategoryGap="20%"
        >
          <XAxis type="number" hide={true} />
          <YAxis
            type="category"
            dataKey="name"
            hide={true}
          />
          <Bar
            dataKey="total_minutes"
            isAnimationActive={false}
          >
            {chartData.map((item, index) => (
              <Cell
                key={`cell-${index}`}
                fill={
                  item.planned
                    ? `url(#${patternId})`
                    : PARETO_COLORS.unplanned
                }
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Compact legend */}
      <p
        className="mt-1 text-xs text-muted-foreground dark:text-muted-foreground"
        data-testid="pareto-legend"
      >
        ■ Unplanned · ▨ Planned
      </p>
    </div>
  )
}

export function DowntimeParetoSkeleton() {
  return (
    <div className="animate-pulse space-y-2" data-testid="downtime-pareto-skeleton">
      <div className="h-3 w-full bg-industrial-200 dark:bg-industrial-700 rounded" />
      <div className="h-3 w-3/4 bg-industrial-200 dark:bg-industrial-700 rounded" />
      <div className="h-3 w-1/2 bg-industrial-200 dark:bg-industrial-700 rounded" />
      <div className="h-3 w-1/3 bg-industrial-200 dark:bg-industrial-700 rounded" />
    </div>
  )
}
