'use client'

import { useState } from 'react'
import { ChevronDown, ChevronRight, AlertCircle, RefreshCw, ClipboardList } from 'lucide-react'
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useMyFollowUps, type FollowUpItem } from '@/hooks/useMyFollowUps'
import { FollowUpEntry } from './FollowUpEntry'
import { FollowUpDetailDialog } from './FollowUpDetailDialog'

const STATUS_GROUPS = [
  { key: 'assigned' as const, label: 'Assigned', variant: 'info' as const },
  { key: 'in_progress' as const, label: 'In Progress', variant: 'warning' as const },
  { key: 'resolved' as const, label: 'Resolved', variant: 'success' as const },
] as const

export function MyAssignmentsPanel() {
  const { isLoading, error, grouped, totalCount, hasFollowUps, refetch } = useMyFollowUps()
  const [isExpanded, setIsExpanded] = useState<boolean | null>(null)
  const [selectedFollowUp, setSelectedFollowUp] = useState<FollowUpItem | null>(null)

  // Default: expanded if loading, error, or has follow-ups; collapsed if empty
  const expanded = isExpanded !== null ? isExpanded : (isLoading || !!error || hasFollowUps)

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ClipboardList className="h-5 w-5 text-muted-foreground" />
            <h3 className="text-lg font-semibold">My Assignments</h3>
            {totalCount > 0 && (
              <Badge variant="secondary">{totalCount}</Badge>
            )}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsExpanded(!expanded)}
            aria-label={expanded ? 'Collapse panel' : 'Expand panel'}
          >
            {expanded ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </Button>
        </div>
      </CardHeader>

      {expanded && (
        <CardContent>
          {isLoading && (
            <div className="space-y-3">
              <div className="h-12 rounded-md bg-muted animate-pulse skeleton" />
              <div className="h-12 rounded-md bg-muted animate-pulse skeleton" />
              <div className="h-12 rounded-md bg-muted animate-pulse skeleton" />
            </div>
          )}

          {!isLoading && error && (
            <div className="flex flex-col items-center gap-3 py-4 text-center">
              <AlertCircle className="h-8 w-8 text-destructive" />
              <p className="text-sm text-muted-foreground">Failed to load follow-ups. Network error.</p>
              <Button variant="outline" size="sm" onClick={refetch}>
                <RefreshCw className="h-4 w-4 mr-1" />
                Retry
              </Button>
            </div>
          )}

          {!isLoading && !error && !hasFollowUps && (
            <p className="text-sm text-muted-foreground py-4 text-center">
              No open follow-ups. Assign actions from the report below.
            </p>
          )}

          {!isLoading && !error && hasFollowUps && (
            <div className="space-y-4">
              {STATUS_GROUPS.map(({ key, label, variant }) => {
                const items = grouped[key]
                if (items.length === 0) return null
                return (
                  <div key={key}>
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant={variant}>{label}</Badge>
                      <span className="text-xs text-muted-foreground">({items.length})</span>
                    </div>
                    <div className="space-y-1">
                      {items.map((followUp) => (
                        <FollowUpEntry
                          key={followUp.id}
                          followUp={followUp}
                          onSelect={setSelectedFollowUp}
                        />
                      ))}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      )}

      {!expanded && !hasFollowUps && !isLoading && (
        <CardContent className="pt-0">
          <p className="text-sm text-muted-foreground text-center">
            No open follow-ups. Assign actions from the report below.
          </p>
        </CardContent>
      )}

      {selectedFollowUp && (
        <FollowUpDetailDialog
          followUp={selectedFollowUp}
          open={!!selectedFollowUp}
          onClose={() => setSelectedFollowUp(null)}
        />
      )}
    </Card>
  )
}
