import { redirect } from 'next/navigation'
import Link from 'next/link'
import { createClient } from '@/lib/supabase/server'
import { DowntimeDashboard } from '@/components/downtime'

/**
 * Downtime Pareto Analysis Page
 *
 * Displays granular downtime breakdown and pareto charts organized by reason code.
 * Helps plant managers quickly identify top causes of production loss.
 *
 * Route: /dashboard/production/downtime
 *
 * @see Story 2.5 - Downtime Pareto Analysis
 * @see AC #3 - Pareto Chart Visualization
 * @see AC #4 - Granular Breakdown Table
 * @see AC #5 - Financial Impact Integration
 * @see AC #6 - Safety Reason Code Highlighting
 * @see AC #7 - Time Window Toggle
 */

export const metadata = {
  title: 'Downtime Analysis | TFN AI Hub',
  description: 'Pareto analysis of downtime events by reason code with financial impact',
}

export default async function DowntimeAnalysisPage() {
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
              <Link
                href="/dashboard"
                className="flex items-center gap-3 hover:opacity-80 transition-opacity"
              >
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
              </Link>
            </div>
            <nav className="flex items-center gap-4" aria-label="Main navigation">
              <Link
                href="/dashboard"
                className="text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                Command Center
              </Link>
              <span className="text-sm text-muted-foreground">
                {user.email}
              </span>
            </nav>
          </div>
        </div>
      </header>

      {/* Breadcrumb */}
      <div className="border-b border-border bg-muted/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
          <nav className="flex items-center gap-2 text-sm" aria-label="Breadcrumb">
            <Link
              href="/dashboard"
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              Command Center
            </Link>
            <span className="text-muted-foreground">/</span>
            <span className="text-muted-foreground">
              Production Intelligence
            </span>
            <span className="text-muted-foreground">/</span>
            <span className="text-foreground font-medium" aria-current="page">
              Downtime Analysis
            </span>
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <h1 className="page-title text-foreground">
              Downtime Analysis
            </h1>
          </div>
          <p className="body-text text-muted-foreground max-w-2xl">
            Pareto analysis of downtime events by reason code. Identify top causes of
            production loss and prioritize corrective actions based on data-driven insights.
          </p>
        </div>

        {/* Dashboard Content */}
        <DowntimeDashboard />
      </div>
    </main>
  )
}
