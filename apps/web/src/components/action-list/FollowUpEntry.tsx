'use client'

import { User, Clock } from 'lucide-react'
import type { FollowUpItem } from '@/hooks/useMyFollowUps'

export function formatRelativeTime(isoString: string): string {
  const diff = Date.now() - new Date(isoString).getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

function hasNewUpdate(followUpId: string, updatedAt: string): boolean {
  try {
    const stored = localStorage.getItem(`followup-viewed-${followUpId}`)
    if (!stored) return true
    const lastViewed = parseInt(stored, 10)
    const updatedTime = new Date(updatedAt).getTime()
    return updatedTime > lastViewed
  } catch {
    return false
  }
}

function markAsViewed(followUpId: string) {
  try {
    localStorage.setItem(`followup-viewed-${followUpId}`, Date.now().toString())
  } catch {
    // localStorage unavailable
  }
}

interface FollowUpEntryProps {
  followUp: FollowUpItem
  onSelect: (followUp: FollowUpItem) => void
}

export function FollowUpEntry({ followUp, onSelect }: FollowUpEntryProps) {
  // Prefer server-side has_unread when available, fall back to localStorage
  const followUpAny = followUp as FollowUpItem & { has_unread?: boolean }
  const isNew = followUpAny.has_unread !== undefined
    ? followUpAny.has_unread
    : hasNewUpdate(followUp.id, followUp.updated_at)

  const handleClick = () => {
    markAsViewed(followUp.id)
    onSelect(followUp)
  }

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={handleClick}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') handleClick()
      }}
      className="flex items-start gap-3 p-3 rounded-md hover:bg-muted/50 cursor-pointer transition-colors relative"
    >
      {isNew && (
        <span
          data-testid="new-update-indicator"
          className="new-update dot absolute top-3 left-0 w-2 h-2 rounded-full bg-blue-500"
          aria-label="new update"
        />
      )}
      <div className="flex-1 min-w-0 ml-2">
        <div className="flex items-center gap-2">
          {followUp.asset_name && (
            <span className="text-sm font-medium text-foreground">
              {followUp.asset_name}
            </span>
          )}
          <span className="text-xs text-muted-foreground flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {formatRelativeTime(followUp.created_at)}
          </span>
        </div>
        <p className="text-sm text-muted-foreground truncate mt-0.5">
          {followUp.action_summary}
        </p>
        {followUp.assigned_to_email && (
          <div className="flex items-center gap-1 mt-1 text-xs text-muted-foreground">
            <User className="h-3 w-3" />
            <span>{followUp.assigned_to_email}</span>
          </div>
        )}
      </div>
    </div>
  )
}
