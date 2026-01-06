'use client'

import { CostOfLossWidget } from '@/components/financial'
import { useCostOfLoss } from '@/hooks/useCostOfLoss'

/**
 * FinancialWidgetsSection - Financial impact and cost metrics section
 *
 * Displays the Cost of Loss widget in the Command Center dashboard.
 * Shows T-1 (yesterday) data by default for Morning Report context.
 *
 * @see Story 1.7 - Command Center UI Shell (integration point)
 * @see Story 2.8 - Cost of Loss Widget
 * @see AC #3 - Integration into Command Center Dashboard
 */
export function FinancialWidgetsSection() {
  // Fetch T-1 (daily) data for the Command Center view
  // This aligns with the Morning Report use case
  const { data, isLoading, error, lastUpdated, refetch } = useCostOfLoss({
    period: 'daily',
    autoFetch: true,
    autoRefresh: false, // No auto-refresh for daily/retrospective data
  })

  return (
    <section aria-labelledby="financial-widgets-heading">
      <CostOfLossWidget
        period="daily"
        data={data}
        isLoading={isLoading}
        error={error}
        lastUpdated={lastUpdated}
        showBreakdown={true}
        autoRefresh={false}
        className="h-full min-h-[200px]"
      />
    </section>
  )
}
