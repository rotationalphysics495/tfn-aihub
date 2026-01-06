import { redirect } from 'next/navigation'
import { createClient } from '@/lib/supabase/server'
import { LogoutButton } from './logout-button'
import {
  ActionListSection,
  LivePulseSection,
  FinancialWidgetsSection,
  SafetyAlertsSection,
  SafetyHeaderIndicator,
} from '@/components/dashboard'

export const metadata = {
  title: 'Command Center | TFN AI Hub',
  description: 'Manufacturing Performance Command Center - Your home base for critical manufacturing intelligence',
}

export default async function DashboardPage() {
  const supabase = await createClient()

  const { data: { user }, error } = await supabase.auth.getUser()

  if (error || !user) {
    redirect('/login')
  }

  return (
    <main className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
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
            <nav className="flex items-center gap-4" aria-label="Main navigation">
              {/* Safety Alert Indicator - AC #9 */}
              <SafetyHeaderIndicator />
              <span className="text-sm text-muted-foreground">
                {user.email}
              </span>
              <LogoutButton />
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
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
    </main>
  )
}
