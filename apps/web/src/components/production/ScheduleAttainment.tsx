'use client'

import { RefreshCw, AlertCircle } from 'lucide-react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { useScheduleAttainment } from '@/hooks/useScheduleAttainment'
import { ProductVarianceCallout } from './ProductVarianceCallout'
import { ProductMixChart } from './ProductMixChart'

export interface ScheduleAttainmentProps {
  className?: string
  date?: string
}

function getAttainmentColor(pct: number): string {
  if (pct >= 95) return 'text-success-green-dark dark:text-success-green'
  if (pct >= 80) return 'text-warning-amber-dark dark:text-warning-amber'
  return 'text-safety-red'
}

function getAllProducts(workcenters: { products: { product_name: string; scheduled_quantity: number; actual_quantity: number; attainment_pct: number }[] }[]) {
  return workcenters.flatMap(wc => wc.products)
}

export function ScheduleAttainment({ className, date }: ScheduleAttainmentProps) {
  const { data, isLoading, error, refetch } = useScheduleAttainment(date ? { date } : {})

  // Loading state
  if (isLoading && !data) {
    return (
      <section aria-label="Schedule attainment" className={cn('', className)}>
        <h2 className="section-header text-foreground mb-4">
          Schedule Attainment
        </h2>
        <div className="space-y-4">
          {[1, 2].map(i => (
            <div
              key={i}
              className="animate-pulse border rounded-lg p-4 md:p-6"
            >
              <div className="flex items-center justify-between">
                <div className="space-y-2">
                  <div className="h-5 w-32 bg-industrial-200 dark:bg-industrial-700 rounded" />
                  <div className="h-4 w-24 bg-industrial-200 dark:bg-industrial-700 rounded" />
                </div>
                <div className="h-10 w-20 bg-industrial-200 dark:bg-industrial-700 rounded" />
              </div>
            </div>
          ))}
        </div>
      </section>
    )
  }

  // Error state
  if (error) {
    return (
      <section aria-label="Schedule attainment" className={cn('', className)}>
        <h2 className="section-header text-foreground mb-4">
          Schedule Attainment
        </h2>
        <div className="rounded-lg border border-warning-amber/30 bg-warning-amber-light/10 dark:bg-warning-amber-dark/10 p-6 md:p-8">
          <div className="flex flex-col items-center text-center">
            <AlertCircle
              className="w-12 h-12 text-warning-amber mb-4"
              aria-hidden="true"
            />
            <p className="text-base text-muted-foreground mb-4">
              {error}
            </p>
            <Button
              onClick={() => refetch()}
              variant="outline"
              className="gap-2"
            >
              <RefreshCw className="w-4 h-4" aria-hidden="true" />
              Try Again
            </Button>
          </div>
        </div>
      </section>
    )
  }

  // Empty state (no schedule data)
  if (data && !data.has_schedule) {
    return (
      <section aria-label="Schedule attainment" className={cn('', className)}>
        <h2 className="section-header text-foreground mb-4">
          Schedule Attainment
        </h2>
        <Card className="rounded-lg border p-6 text-center">
          <p className="text-base text-muted-foreground">
            No schedule uploaded for this date.
          </p>
          <Link
            href="/settings/schedule-upload"
            className="text-info-blue hover:underline mt-2 inline-block"
          >
            Upload schedule &rarr;
          </Link>
        </Card>
      </section>
    )
  }

  // Success state
  const workcenters = data?.workcenters ?? []
  const allProducts = getAllProducts(workcenters)

  return (
    <section aria-label="Schedule attainment" className={cn('', className)}>
      <h2 className="section-header text-foreground mb-4">
        Schedule Attainment
      </h2>
      <div className="space-y-4">
        {workcenters.map(wc => (
          <Card key={wc.workcenter_name} mode="retrospective">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-lg">{wc.workcenter_name}</CardTitle>
              <span
                className={cn(
                  'text-2xl font-bold tabular-nums',
                  getAttainmentColor(wc.overall_attainment_pct)
                )}
              >
                {wc.overall_attainment_pct}%
              </span>
            </CardHeader>
            <CardContent>
              {wc.products.length > 0 && (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-muted-foreground">
                        <th className="text-left py-2 font-medium">Product</th>
                        <th className="text-right py-2 font-medium">Scheduled</th>
                        <th className="text-right py-2 font-medium">Actual</th>
                        <th className="text-right py-2 font-medium">Attainment</th>
                      </tr>
                    </thead>
                    <tbody>
                      {wc.products.map(product => (
                        <tr key={product.product_name} className="border-b last:border-0">
                          <td className="py-2">{product.product_name}</td>
                          <td className="text-right py-2 tabular-nums">
                            {product.scheduled_quantity.toLocaleString()}
                          </td>
                          <td className="text-right py-2 tabular-nums">
                            {product.actual_quantity.toLocaleString()}
                          </td>
                          <td className={cn(
                            'text-right py-2 tabular-nums font-medium',
                            getAttainmentColor(product.attainment_pct)
                          )}>
                            {product.attainment_pct.toFixed(1)}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {wc.variance_callouts.length > 0 && (
                <div className="mt-3 space-y-2">
                  {wc.variance_callouts.map((v, i) => (
                    <ProductVarianceCallout key={i} variance={v} />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {allProducts.length > 0 && (
        <Card mode="retrospective" className="mt-4">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg">Product Mix Comparison</CardTitle>
          </CardHeader>
          <CardContent>
            <ProductMixChart products={allProducts} />
          </CardContent>
        </Card>
      )}
    </section>
  )
}
