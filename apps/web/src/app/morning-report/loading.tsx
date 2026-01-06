import { ActionListSkeleton, SummarySkeleton } from '@/components/action-list'

/**
 * Morning Report Loading State
 *
 * Displays skeleton UI while the page is loading.
 *
 * @see Story 3.3 - Action List Primary View
 * @see AC #10 - Initial page render (with loading state) within 500ms
 */

export default function MorningReportLoading() {
  return (
    <main className="min-h-screen bg-background">
      {/* Header skeleton */}
      <header className="border-b border-border bg-card">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-industrial-200 dark:bg-industrial-700 animate-pulse" />
              <div className="h-5 w-48 bg-industrial-200 dark:bg-industrial-700 rounded animate-pulse" />
            </div>
            <div className="flex items-center gap-4">
              <div className="h-9 w-48 bg-industrial-200 dark:bg-industrial-700 rounded-lg animate-pulse" />
              <div className="h-8 w-8 bg-industrial-200 dark:bg-industrial-700 rounded animate-pulse" />
              <div className="h-4 w-32 bg-industrial-200 dark:bg-industrial-700 rounded animate-pulse hidden sm:block" />
              <div className="h-9 w-20 bg-industrial-200 dark:bg-industrial-700 rounded animate-pulse" />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8">
        {/* Breadcrumb skeleton */}
        <div className="flex items-center gap-2 mb-4">
          <div className="h-4 w-4 bg-industrial-200 dark:bg-industrial-700 rounded animate-pulse" />
          <div className="h-4 w-2 bg-industrial-200 dark:bg-industrial-700 rounded animate-pulse" />
          <div className="h-4 w-24 bg-industrial-200 dark:bg-industrial-700 rounded animate-pulse" />
        </div>

        {/* Page Header skeleton */}
        <div className="mb-6 md:mb-8">
          <div className="h-12 w-64 bg-industrial-200 dark:bg-industrial-700 rounded animate-pulse mb-2" />
          <div className="h-5 w-96 bg-industrial-200 dark:bg-industrial-700 rounded animate-pulse" />
        </div>

        {/* Content skeleton */}
        <div className="space-y-6">
          <SummarySkeleton />

          <div>
            <div className="h-8 w-48 bg-industrial-200 dark:bg-industrial-700 rounded animate-pulse mb-4" />
            <ActionListSkeleton count={3} />
          </div>
        </div>
      </div>
    </main>
  )
}
