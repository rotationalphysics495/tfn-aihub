import { SafetyAlertsSection } from '@/components/dashboard'
import { MorningSummarySection } from '@/components/action-list'
import { InsightEvidenceCardList } from '@/components/action-engine'
import { Breadcrumb } from '@/components/navigation'

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

export default function MorningReportPage() {
  return (
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
  )
}
