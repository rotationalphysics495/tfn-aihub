import { Suspense } from 'react'
import { SummarySkeleton } from '@/components/action-list'
import { MorningReportClient } from './MorningReportClient'

/**
 * Morning Report Page
 *
 * Primary landing page for authenticated users displaying the Daily Action List.
 * Server Component that wraps the client-side MorningReportClient in Suspense
 * for useSearchParams compatibility.
 *
 * @see Story 3.3 - Action List Primary View
 * @see Story 17.1 - Date Picker on Morning Report
 */

export const metadata = {
  title: 'Morning Report | Manufacturing Performance Assistant',
  description: 'Daily action list and prioritized recommendations for plant managers',
}

export default function MorningReportPage() {
  return (
    <Suspense fallback={
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8">
        <div className="mb-6 md:mb-8">
          <h1 className="page-title text-foreground">Morning Report</h1>
          <p className="body-text text-muted-foreground mt-2">
            Daily action items prioritized for your morning review.
          </p>
        </div>
        <SummarySkeleton />
      </div>
    }>
      <MorningReportClient />
    </Suspense>
  )
}
