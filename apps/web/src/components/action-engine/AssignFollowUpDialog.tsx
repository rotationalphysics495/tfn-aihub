'use client'

import { useState, useEffect, useCallback } from 'react'
import { UserPlus, CheckCircle2, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { PriorityBadge, type PriorityType } from './PriorityBadge'
import { createClient } from '@/lib/supabase/client'
import { cn } from '@/lib/utils'

interface AssignFollowUpDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  actionItem: {
    id: string
    priority: PriorityType
    recommendationText: string
    assetName: string
    category: string
    reportDate: string
  }
}

interface TeamMember {
  user_id: string
  email: string
  role: string
}

export function AssignFollowUpDialog({
  open,
  onOpenChange,
  actionItem,
}: AssignFollowUpDialogProps) {
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([])
  const [selectedUserId, setSelectedUserId] = useState('')
  const [note, setNote] = useState('')
  const [isLoadingUsers, setIsLoadingUsers] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Fetch team members when dialog opens
  useEffect(() => {
    if (!open) return
    // Reset state on open
    setSelectedUserId('')
    setNote('')
    setSubmitted(false)
    setError(null)

    async function fetchUsers() {
      setIsLoadingUsers(true)
      try {
        const supabase = createClient()
        const { data: { session } } = await supabase.auth.getSession()
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

        const response = await fetch(`${apiUrl}/api/v1/team/members`, {
          headers: {
            'Authorization': `Bearer ${session?.access_token}`,
            'Content-Type': 'application/json',
          },
        })

        if (!response.ok) {
          throw new Error(`Failed to fetch team members (${response.status})`)
        }

        const data = await response.json()
        const members = data.members || []
        setTeamMembers(
          members.map((m: { user_id: string; email?: string; role?: string }) => ({
            user_id: m.user_id,
            email: m.email || m.user_id.slice(0, 8) + '...',
            role: m.role || 'user',
          }))
        )
      } catch {
        setError('Unable to load team members.')
      } finally {
        setIsLoadingUsers(false)
      }
    }

    fetchUsers()
  }, [open])

  const handleSubmit = useCallback(async () => {
    if (!selectedUserId) return

    setIsSubmitting(true)
    setError(null)

    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.user?.id) {
        setError('Session expired. Please log in again.')
        return
      }

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/v1/followups`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action_item_id: actionItem.id,
          action_summary: actionItem.recommendationText,
          asset_name: actionItem.assetName,
          category: actionItem.category.toLowerCase(),
          assigned_to: selectedUserId,
          note: note.trim() || null,
          report_date: actionItem.reportDate,
        }),
      })

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}))
        throw new Error(errData.detail || `Failed to assign follow-up (${response.status})`)
      }

      setSubmitted(true)
      // Auto-close after success
      setTimeout(() => onOpenChange(false), 1500)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to assign follow-up.')
    } finally {
      setIsSubmitting(false)
    }
  }, [selectedUserId, note, actionItem, onOpenChange])

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        {submitted ? (
          // Success state
          <div className="flex flex-col items-center py-6 text-center">
            <CheckCircle2 className="w-12 h-12 text-success-green mb-3" />
            <DialogTitle className="text-lg font-semibold mb-1">
              Follow-Up Assigned
            </DialogTitle>
            <DialogDescription>
              {teamMembers.find((m) => m.user_id === selectedUserId)?.email || 'Teammate'} has been assigned this action item.
            </DialogDescription>
          </div>
        ) : (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <UserPlus className="w-5 h-5" />
                Assign Follow-Up
              </DialogTitle>
              <DialogDescription>
                Assign this action item to a teammate for follow-up.
              </DialogDescription>
            </DialogHeader>

            {/* Action item context */}
            <div className="rounded-lg border border-border bg-industrial-50/50 dark:bg-industrial-900/30 p-3 space-y-2">
              <PriorityBadge priority={actionItem.priority} className="text-xs px-2 py-0.5" />
              <p className="text-sm font-medium text-foreground leading-snug">
                {actionItem.recommendationText}
              </p>
              <p className="text-xs text-muted-foreground">{actionItem.assetName}</p>
            </div>

            {/* Assign to */}
            <div className="space-y-2">
              <label htmlFor="assign-to" className="text-sm font-medium text-foreground">
                Assign to
              </label>
              {isLoadingUsers ? (
                <div className="flex items-center gap-2 text-sm text-muted-foreground py-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Loading team members...
                </div>
              ) : (
                <select
                  id="assign-to"
                  value={selectedUserId}
                  onChange={(e) => setSelectedUserId(e.target.value)}
                  className={cn(
                    'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm',
                    'ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                    'disabled:cursor-not-allowed disabled:opacity-50'
                  )}
                >
                  <option value="">Select a team member...</option>
                  {teamMembers.map((member) => (
                    <option key={member.user_id} value={member.user_id}>
                      {member.email} ({member.role.replace('_', ' ')})
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* Note */}
            <div className="space-y-2">
              <label htmlFor="followup-note" className="text-sm font-medium text-foreground">
                Note <span className="text-muted-foreground font-normal">(optional)</span>
              </label>
              <Textarea
                id="followup-note"
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="Add context or instructions..."
                rows={3}
              />
            </div>

            {/* Error */}
            {error && (
              <p className="text-sm text-safety-red">{error}</p>
            )}

            <DialogFooter>
              <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isSubmitting}>
                Cancel
              </Button>
              <Button
                onClick={handleSubmit}
                disabled={!selectedUserId || isSubmitting}
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Assigning...
                  </>
                ) : (
                  <>
                    <UserPlus className="w-4 h-4" />
                    Assign
                  </>
                )}
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
