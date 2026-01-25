import { redirect } from 'next/navigation'
import Link from 'next/link'
import { createClient } from '@/lib/supabase/server'
import { OEEDashboard } from '@/components/oee'
import { Badge } from '@/components/ui/badge'

/**
 * OEE Dashboard Page
 *
 * Displays Overall Equipment Effectiveness metrics for plant managers.
 * Shows plant-wide OEE with breakdown by availability, performance, and quality.
 *
 * Route: /dashboard/production/oee
 *
 * @see Story 2.4 - OEE Metrics View
 * @see AC #3 - Plant-wide OEE prominently displayed
 * @see AC #6 - Visual indicators for Yesterday's Analysis vs Live Pulse
 * @see AC #9 - "Industrial Clarity" design - readable from 3 feet
 */

export const metadata = {
  title: 'OEE Metrics | TFN AI Hub',
  description: 'Overall Equipment Effectiveness metrics for manufacturing performance monitoring',
}

export default async function OEEDashboardPage() {
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
              OEE Metrics
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
              OEE Metrics
            </h1>
          </div>
          <p className="body-text text-muted-foreground max-w-2xl">
            Overall Equipment Effectiveness metrics combining availability, performance, and quality.
            Monitor plant-wide efficiency and identify opportunities for improvement.
          </p>
        </div>

        {/* Dashboard Content */}
        <OEEDashboard />
      </div>
    </main>
  )
}
