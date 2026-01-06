import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

/**
 * LivePulseSection - Real-time status monitoring section
 *
 * Positioned to show real-time status area with distinct visual treatment
 * for "Live" context (vibrant/pulsing indicators ready).
 *
 * Uses mode="live" Card variant for vibrant styling per Industrial Clarity design.
 *
 * @see Story 1.7 - Command Center UI Shell
 * @see Story 2.3 - Throughput Dashboard (now links to production throughput)
 * @see Story 2.4 - OEE Metrics View
 * @see Story 2.5 - Downtime Pareto Analysis
 */
export function LivePulseSection() {
  return (
    <section aria-labelledby="live-pulse-heading">
      <Card mode="live" className="h-full min-h-[200px]">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <CardTitle id="live-pulse-heading" className="card-title">
                Live Pulse
              </CardTitle>
              <span
                className="inline-flex h-2 w-2 rounded-full bg-live-primary animate-live-pulse"
                aria-label="Live indicator"
              />
            </div>
            <Badge variant="live">Real-time</Badge>
          </div>
        </CardHeader>
        <CardContent className="py-4">
          <div className="flex flex-col gap-4">
            {/* Production Intelligence Link */}
            <Link
              href="/dashboard/production/throughput"
              className="group flex items-center gap-3 p-4 rounded-lg bg-live-surface/50 dark:bg-live-surface-dark/50 border border-live-border dark:border-live-border-dark hover:bg-live-surface dark:hover:bg-live-surface-dark transition-colors"
            >
              <div className="w-10 h-10 rounded-full bg-live-primary/20 flex items-center justify-center group-hover:bg-live-primary/30 transition-colors">
                <svg
                  className="w-5 h-5 text-live-primary"
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
              <div className="flex-1">
                <p className="font-semibold text-foreground group-hover:text-live-primary transition-colors">
                  Throughput Dashboard
                </p>
                <p className="text-sm text-muted-foreground">
                  Actual vs target production metrics
                </p>
              </div>
              <svg
                className="w-5 h-5 text-muted-foreground group-hover:text-live-primary transition-colors"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </Link>

            {/* OEE Metrics Link */}
            <Link
              href="/dashboard/production/oee"
              className="group flex items-center gap-3 p-4 rounded-lg bg-live-surface/50 dark:bg-live-surface-dark/50 border border-live-border dark:border-live-border-dark hover:bg-live-surface dark:hover:bg-live-surface-dark transition-colors"
            >
              <div className="w-10 h-10 rounded-full bg-live-primary/20 flex items-center justify-center group-hover:bg-live-primary/30 transition-colors">
                <svg
                  className="w-5 h-5 text-live-primary"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z"
                  />
                </svg>
              </div>
              <div className="flex-1">
                <p className="font-semibold text-foreground group-hover:text-live-primary transition-colors">
                  OEE Metrics
                </p>
                <p className="text-sm text-muted-foreground">
                  Availability, performance &amp; quality
                </p>
              </div>
              <svg
                className="w-5 h-5 text-muted-foreground group-hover:text-live-primary transition-colors"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </Link>

            {/* Downtime Analysis Link */}
            <Link
              href="/dashboard/production/downtime"
              className="group flex items-center gap-3 p-4 rounded-lg bg-live-surface/50 dark:bg-live-surface-dark/50 border border-live-border dark:border-live-border-dark hover:bg-live-surface dark:hover:bg-live-surface-dark transition-colors"
            >
              <div className="w-10 h-10 rounded-full bg-live-primary/20 flex items-center justify-center group-hover:bg-live-primary/30 transition-colors">
                <svg
                  className="w-5 h-5 text-live-primary"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <div className="flex-1">
                <p className="font-semibold text-foreground group-hover:text-live-primary transition-colors">
                  Downtime Analysis
                </p>
                <p className="text-sm text-muted-foreground">
                  Pareto charts by reason code
                </p>
              </div>
              <svg
                className="w-5 h-5 text-muted-foreground group-hover:text-live-primary transition-colors"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </Link>
          </div>
        </CardContent>
      </Card>
    </section>
  )
}
