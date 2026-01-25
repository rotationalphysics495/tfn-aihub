import {
  ActionListSection,
  LivePulseSection,
  FinancialWidgetsSection,
  SafetyAlertsSection,
} from '@/components/dashboard'

export const metadata = {
  title: 'Command Center | TFN AI Hub',
  description: 'Manufacturing Performance Command Center - Your home base for critical manufacturing intelligence',
}

export default function DashboardPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Safety Alert Banner - AC #4 Prominent display */}
      <SafetyAlertsSection className="mb-6" />

      {/* Page Header */}
      <div className="mb-8">
        <h1 className="page-title text-foreground">
          Command Center
        </h1>
        <p className="body-text text-muted-foreground mt-2">
          Welcome back. Here&apos;s your plant overview.
        </p>
      </div>

      {/* Dashboard Grid - Responsive layout */}
      {/* Mobile: 1 column, Tablet (md): 2 columns, Desktop (lg): 3 columns */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Action List - Primary section spanning 2 columns on desktop */}
        <ActionListSection />

        {/* Live Pulse - Real-time status section */}
        <LivePulseSection />

        {/* Financial Widgets - Financial impact section */}
        <FinancialWidgetsSection />

        {/* Second Financial Widget slot for future expansion */}
        <div className="hidden lg:block" aria-hidden="true">
          {/* Reserved space for additional widgets */}
        </div>
      </div>
    </div>
  )
}
