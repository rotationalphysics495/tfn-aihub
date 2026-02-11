'use client'

import { AlertTriangle, ArrowRightLeft, Package } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface VarianceCalloutData {
  type: 'product_swap' | 'underproduction' | 'unscheduled' | string
  asset_name: string
  message: string
  scheduled_product?: string
  actual_product?: string
  quantity_gap?: number
}

export interface ProductVarianceCalloutProps {
  variance: VarianceCalloutData
}

export function ProductVarianceCallout({ variance }: ProductVarianceCalloutProps) {
  const isUnscheduled = variance.type === 'unscheduled'

  const containerClasses = isUnscheduled
    ? 'border-l-4 border-info-blue bg-info-blue-light/50 dark:bg-info-blue-dark/20 text-info-blue-dark dark:text-info-blue'
    : 'border-l-4 border-warning-amber bg-warning-amber-light/50 dark:bg-warning-amber-dark/20 text-warning-amber-dark dark:text-warning-amber'

  const Icon = variance.type === 'product_swap'
    ? ArrowRightLeft
    : variance.type === 'unscheduled'
      ? Package
      : AlertTriangle

  return (
    <div className={cn('rounded-lg p-3 flex items-start gap-2', containerClasses)}>
      <Icon className="w-4 h-4 mt-0.5 shrink-0" aria-hidden="true" />
      <span className="text-sm">{variance.message}</span>
    </div>
  )
}
