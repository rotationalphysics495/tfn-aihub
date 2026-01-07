import { redirect } from 'next/navigation'
import { createClient } from '@/lib/supabase/server'
import { LogoutButton } from '@/app/dashboard/logout-button'
import { SafetyAlertsSection, SafetyHeaderIndicator } from '@/components/dashboard'
import { MorningSummarySection } from '@/components/action-list'
import { InsightEvidenceCardList } from '@/components/action-engine'
import { ViewModeToggle, Breadcrumb } from '@/components/navigation'

/**
 * Morning Report Page
 *
 * Primary landing page for authenticated users displaying the Daily Action List.
 *
 * @see Story 3.3 - Action List Primary View
 * @see AC #1 - Action List as Primary Landing View
 * @see AC #2 - Action First Layout Structure
 * @see AC #9 - Authentication Flow Integration
 */

export const metadata = {
  title: 'Morning Report | Manufacturing Performance Assistant',
  description: 'Daily action list and prioritized recommendations for plant managers',
}

export default async function MorningReportPage() {
  const supabase = await createClient()

  // AC #9: Authentication check - redirect unauthenticated to login
  const { data: { user }, error } = await supabase.auth.getUser()

  if (error || !user) {
    redirect('/login')
  }

  return (
    <main className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo and title */}
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                <svg
                  className="w-4 h-4 text-primary"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                  />
                </svg>
              </div>
              <span className="font-semibold text-foreground">
                Manufacturing Performance Assistant
              </span>
            </div>

            {/* Navigation and user info */}
            <nav className="flex items-center gap-4" aria-label="Main navigation">
              {/* View mode toggle - AC #7 */}
              <ViewModeToggle />

              {/* Safety Alert Indicator */}
              <SafetyHeaderIndicator />

              <span className="text-sm text-muted-foreground hidden sm:inline">
                {user.email}
              </span>
              <LogoutButton />
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8">
        {/* Safety Alert Banner - Prominent display */}
        <SafetyAlertsSection className="mb-6" />

        {/* Breadcrumb navigation - AC #7 */}
        <Breadcrumb className="mb-4" />

        {/* Page Header - AC #1 */}
        <div className="mb-6 md:mb-8">
          <h1 className="page-title text-foreground">
            Morning Report
          </h1>
          <p className="body-text text-muted-foreground mt-2">
            Daily action items prioritized for your morning review.
          </p>
        </div>

        {/* Action First Layout - AC #2 */}
        <div className="space-y-6">
          {/* Morning Summary Section - Secondary context - AC #6 */}
          <MorningSummarySection />

          {/* Action List - Primary content area - AC #2 */}
          {/* Story 3.4: Insight + Evidence Cards - recommendation + supporting data */}
          <section aria-label="Action items with evidence">
            <h2 className="section-header text-foreground mb-4">
              Today&apos;s Action Items
            </h2>
            <InsightEvidenceCardList />
          </section>
        </div>
      </div>
    </main>
  )
}
