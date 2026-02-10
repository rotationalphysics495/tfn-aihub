'use client'

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { InsightEvidenceCardList } from '@/components/action-engine'

/**
 * ActionListSection - Primary section for Daily Action List
 *
 * Positioned as the primary/prominent section per "Action First, Data Second" principle.
 * Integrates with Action Engine API via InsightEvidenceCardList.
 *
 * @see Story 1.7 - Command Center UI Shell
 * @see Story 3.4 - Insight + Evidence Cards
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
        <CardContent>
          <InsightEvidenceCardList />
        </CardContent>
      </Card>
    </section>
  )
}
