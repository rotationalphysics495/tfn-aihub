'use client'

import { useState, useCallback } from 'react'
import { UserPlus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { PriorityBadge, getPriorityBorderColor } from '@/components/action-engine/PriorityBadge'
import { AssignmentBadge } from '@/components/action-engine/AssignmentBadge'
import { AssignFollowUpDialog } from '@/components/action-engine/AssignFollowUpDialog'
import { cn } from '@/lib/utils'
import type { ActionItem, FollowUpData } from '@/components/action-engine/types'

interface MeetingTalkingPointProps {
  item: ActionItem
  followUp?: FollowUpData
  reportDate?: string
  onAssign?: (item: ActionItem) => void
  className?: string
}

const PRIORITY_TO_CATEGORY: Record<string, string> = {
  SAFETY: 'safety',
  FINANCIAL: 'financial',
  OEE: 'oee',
}

export function MeetingTalkingPoint({ item, followUp, reportDate, onAssign, className }: MeetingTalkingPointProps) {
  const [dialogOpen, setDialogOpen] = useState(false)

  const handleAssignClick = useCallback(() => {
    setDialogOpen(true)
    onAssign?.(item)
  }, [item, onAssign])

  const borderColor = getPriorityBorderColor(item.priority)

  return (
    <>
      <div
        role="article"
        aria-label={`Action item: ${item.recommendation.text}`}
        className={cn(
          'rounded-lg border bg-card p-4 md:p-6',
          'border-l-4',
          borderColor,
          className
        )}
      >
        <div className="flex flex-col gap-3">
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <PriorityBadge priority={item.priority} />
              <h3 className="text-xl md:text-2xl font-semibold text-foreground mt-2 leading-tight">
                {item.recommendation.text}
              </h3>
              {item.asset?.name && (
                <p className="text-base text-muted-foreground mt-1">
                  {item.asset.name}
                </p>
              )}
            </div>
          </div>

          <div className="flex items-center gap-3 flex-wrap">
            {followUp && (
              <AssignmentBadge followUp={followUp} />
            )}
            <Button
              variant="outline"
              size="default"
              onClick={handleAssignClick}
              className="gap-2"
            >
              <UserPlus className="w-4 h-4" aria-hidden="true" />
              Assign Follow-Up
            </Button>
          </div>
        </div>
      </div>

      <AssignFollowUpDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        actionItem={{
          id: item.id,
          priority: item.priority,
          recommendationText: item.recommendation.text,
          assetName: item.asset?.name || '',
          category: PRIORITY_TO_CATEGORY[item.priority] || 'financial',
          reportDate: reportDate ?? new Date().toISOString().split('T')[0],
        }}
      />
    </>
  )
}
