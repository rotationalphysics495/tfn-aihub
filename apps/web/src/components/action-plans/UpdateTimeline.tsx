'use client'

import { formatRelativeTime } from './types'
import type { ActionPlanUpdate } from './types'

interface UpdateTimelineProps {
  updates: ActionPlanUpdate[]
}

function formatStatusChange(statusChange: string): string {
  // Convert "open -> in_progress" to "open → in_progress"
  return statusChange.replace('->', '→')
}

export function UpdateTimeline({ updates }: UpdateTimelineProps) {
  if (updates.length === 0) {
    return (
      <div className="text-sm text-muted-foreground text-center py-4">
        No updates yet
      </div>
    )
  }

  // Sort by created_at descending (most recent first)
  const sorted = [...updates].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  )

  return (
    <div className="space-y-0">
      {sorted.map((update, index) => (
        <div key={update.id} className="relative pl-6 pb-4">
          {/* Timeline line */}
          {index < sorted.length - 1 && (
            <div className="absolute left-[9px] top-3 bottom-0 w-px bg-border" />
          )}

          {/* Timeline dot */}
          <div
            className={`absolute left-0 top-1.5 w-[18px] h-[18px] rounded-full border-2 ${
              update.status_change
                ? 'bg-primary border-primary'
                : 'bg-background border-border'
            }`}
          />

          <div className="space-y-1">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span>{update.author_email || update.author_id}</span>
              <span>{formatRelativeTime(update.created_at)}</span>
            </div>

            {update.update_text && (
              <p className="text-sm">{update.update_text}</p>
            )}

            {update.status_change && (
              <div className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded bg-muted">
                Status: {formatStatusChange(update.status_change)}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
