'use client'

import Link from "next/link"
import { LivePulseTicker } from "./LivePulseTicker"

/**
 * LivePulseSection - Real-time status monitoring section
 *
 * Contains the Live Pulse Ticker (Story 2.9) for real-time production monitoring
 * and navigation links to detailed dashboard views.
 *
 * Uses mode="live" Card variant for vibrant styling per Industrial Clarity design.
 *
 * @see Story 1.7 - Command Center UI Shell
 * @see Story 2.9 - Live Pulse Ticker (replaces placeholder)
 * @see Story 2.3 - Throughput Dashboard
 * @see Story 2.4 - OEE Metrics View
 * @see Story 2.5 - Downtime Pareto Analysis
 */
export function LivePulseSection() {
  return (
    <section aria-labelledby="live-pulse-heading" className="space-y-6">
      {/* Live Pulse Ticker - Main Content */}
      <div id="live-pulse-heading">
        <LivePulseTicker />
      </div>

      {/* Quick Navigation Links to Detailed Views */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-foreground group-hover:text-live-primary transition-colors truncate">
              Throughput Dashboard
            </p>
            <p className="text-sm text-muted-foreground truncate">
              Actual vs target metrics
            </p>
          </div>
          <svg
            className="w-5 h-5 text-muted-foreground group-hover:text-live-primary transition-colors flex-shrink-0"
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
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-foreground group-hover:text-live-primary transition-colors truncate">
              OEE Metrics
            </p>
            <p className="text-sm text-muted-foreground truncate">
              Availability, performance &amp; quality
            </p>
          </div>
          <svg
            className="w-5 h-5 text-muted-foreground group-hover:text-live-primary transition-colors flex-shrink-0"
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
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-foreground group-hover:text-live-primary transition-colors truncate">
              Downtime Analysis
            </p>
            <p className="text-sm text-muted-foreground truncate">
              Pareto charts by reason code
            </p>
          </div>
          <svg
            className="w-5 h-5 text-muted-foreground group-hover:text-live-primary transition-colors flex-shrink-0"
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
    </section>
  )
}
