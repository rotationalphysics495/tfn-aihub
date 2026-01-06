import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

/**
 * ActionListSection - Primary section for Daily Action List
 *
 * Positioned as the primary/prominent section per "Action First, Data Second" principle.
 * Contains placeholder indicating "Daily Action List - Coming in Epic 3".
 *
 * @see Story 1.7 - Command Center UI Shell
 */
export function ActionListSection() {
  return (
    <section aria-labelledby="action-list-heading" className="lg:col-span-2">
      <Card className="h-full min-h-[300px]">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <CardTitle id="action-list-heading" className="section-header">
              Daily Action List
            </CardTitle>
            <Badge variant="info">Primary</Badge>
          </div>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center py-12">
          <div className="flex flex-col items-center gap-4 text-center">
            <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
              <svg
                className="w-8 h-8 text-primary"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
                />
              </svg>
            </div>
            <div>
              <h3 className="card-title text-foreground mb-2">
                Action-First Intelligence
              </h3>
              <p className="body-text text-muted-foreground max-w-md">
                Your prioritized daily actions will appear here, guiding you to
                the most impactful decisions for your plant operations.
              </p>
            </div>
            <Badge variant="secondary" className="mt-4">
              Coming in Epic 3
            </Badge>
          </div>
        </CardContent>
      </Card>
    </section>
  )
}
