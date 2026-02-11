'use client'

import { useMemo } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

export interface ProductMixChartProps {
  products: {
    product_name: string
    scheduled_quantity: number
    actual_quantity: number
    attainment_pct: number
  }[]
}

const COLORS = {
  planned: 'hsl(var(--info-blue))',
  actual: 'hsl(var(--success-green))',
}

export function ProductMixChart({ products }: ProductMixChartProps) {
  const chartData = useMemo(() => {
    if (!products || products.length === 0) return []

    const totalScheduled = products.reduce((sum, p) => sum + p.scheduled_quantity, 0)
    const totalActual = products.reduce((sum, p) => sum + p.actual_quantity, 0)

    return products.map(p => ({
      name: p.product_name.length > 15
        ? `${p.product_name.substring(0, 12)}...`
        : p.product_name,
      fullName: p.product_name,
      planned_pct: totalScheduled > 0
        ? Math.round((p.scheduled_quantity / totalScheduled) * 1000) / 10
        : 0,
      actual_pct: totalActual > 0
        ? Math.round((p.actual_quantity / totalActual) * 1000) / 10
        : 0,
    }))
  }, [products])

  if (!products || products.length === 0) {
    return (
      <div className="text-center text-sm text-muted-foreground py-4">
        No data available
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={250}>
      <BarChart
        data={chartData}
        margin={{ top: 10, right: 20, left: 10, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.5} />
        <XAxis
          dataKey="name"
          tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
        />
        <YAxis
          tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
          label={{
            value: '%',
            angle: -90,
            position: 'insideLeft',
            style: { textAnchor: 'middle', fill: 'hsl(var(--muted-foreground))' },
          }}
        />
        <Tooltip />
        <Legend />
        <Bar dataKey="planned_pct" name="Planned %" fill={COLORS.planned} radius={[4, 4, 0, 0]} />
        <Bar dataKey="actual_pct" name="Actual %" fill={COLORS.actual} radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
