import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

/**
 * FinancialWidgetsSection - Financial impact and cost metrics section
 *
 * Contains placeholder for financial impact/cost widgets.
 * Financial Intelligence features coming in Epic 2.
 *
 * @see Story 1.7 - Command Center UI Shell
 */
export function FinancialWidgetsSection() {
  return (
    <section aria-labelledby="financial-widgets-heading">
      <Card className="h-full min-h-[200px]">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <CardTitle id="financial-widgets-heading" className="card-title">
              Financial Intelligence
            </CardTitle>
            <Badge variant="success">Impact</Badge>
          </div>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center py-8">
          <div className="flex flex-col items-center gap-4 text-center">
            <div className="w-12 h-12 rounded-full bg-success-green/20 flex items-center justify-center">
              <svg
                className="w-6 h-6 text-success-green"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <div>
              <p className="body-text text-muted-foreground">
                Cost impact and financial metrics
              </p>
            </div>
            <Badge variant="secondary">Coming in Epic 2</Badge>
          </div>
        </CardContent>
      </Card>
    </section>
  )
}
