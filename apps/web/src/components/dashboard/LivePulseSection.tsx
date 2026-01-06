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
        <CardContent className="flex flex-col items-center justify-center py-8">
          <div className="flex flex-col items-center gap-4 text-center">
            <div className="w-12 h-12 rounded-full bg-live-primary/20 flex items-center justify-center">
              <svg
                className="w-6 h-6 text-live-primary"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
            </div>
            <div>
              <p className="body-text text-muted-foreground">
                Real-time plant status and monitoring data
              </p>
            </div>
            <Badge variant="secondary">Coming in Epic 2</Badge>
          </div>
        </CardContent>
      </Card>
    </section>
  )
}
