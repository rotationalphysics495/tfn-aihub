'use client'

import { useState, useCallback } from 'react'
import { ExternalLink, Loader2 } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'
import { createClient } from '@/lib/supabase/client'
import { UpdateTimeline } from './UpdateTimeline'
import type { ActionPlan, ActionPlanUpdate, ActionPlanStatus } from './types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface ActionPlanWithUpdates extends ActionPlan {
  updates: ActionPlanUpdate[]
}

interface ActionPlanDetailProps {
  plan: ActionPlanWithUpdates
  open: boolean
  onClose: () => void
  onStatusChange?: () => void
}

const STATUS_DISPLAY: Record<ActionPlanStatus, { label: string; className: string }> = {
  open: {
    label: 'Open',
    className: 'text-blue-600 bg-blue-100 border-blue-200 dark:text-blue-400 dark:bg-blue-900/30',
  },
  in_progress: {
    label: 'In Progress',
    className: 'text-amber-600 bg-amber-100 border-amber-200 dark:text-amber-400 dark:bg-amber-900/30',
  },
  completed: {
    label: 'Completed',
    className: 'text-green-600 bg-green-100 border-green-200 dark:text-green-400 dark:bg-green-900/30',
  },
  verified: {
    label: 'Verified',
    className: 'text-emerald-600 bg-emerald-100 border-emerald-200 dark:text-emerald-400 dark:bg-emerald-900/30',
  },
}

function formatDate(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

export function ActionPlanDetail({ plan, open, onClose, onStatusChange }: ActionPlanDetailProps) {
  const [updateText, setUpdateText] = useState('')
  const [statusChange, setStatusChange] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const statusConfig = STATUS_DISPLAY[plan.status]

  const getAuthToken = useCallback(async (): Promise<string | null> => {
    const supabase = createClient()
    const { data: { session } } = await supabase.auth.getSession()
    return session?.access_token || null
  }, [])

  const handleAddUpdate = useCallback(async () => {
    if (!updateText.trim()) return

    setIsSubmitting(true)
    setError(null)

    try {
      const token = await getAuthToken()
      if (!token) {
        setError('Session expired. Please log in again.')
        return
      }

      const body: Record<string, string> = { update_text: updateText.trim() }
      if (statusChange) {
        body.status_change = statusChange
      }

      const response = await fetch(`${API_BASE_URL}/api/v1/action-plans/${plan.id}/updates`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      })

      if (!response.ok) {
        throw new Error('Failed to add update.')
      }

      setUpdateText('')
      setStatusChange('')
      onStatusChange?.()
    } catch {
      setError('Failed to add update.')
    } finally {
      setIsSubmitting(false)
    }
  }, [updateText, statusChange, plan.id, getAuthToken, onStatusChange])

  const handleStatusChange = useCallback(async (newStatus: string) => {
    setIsSubmitting(true)
    setError(null)

    try {
      const token = await getAuthToken()
      if (!token) {
        setError('Session expired. Please log in again.')
        return
      }

      const response = await fetch(`${API_BASE_URL}/api/v1/action-plans/${plan.id}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus }),
      })

      if (!response.ok) {
        throw new Error('Failed to update status.')
      }

      onStatusChange?.()
    } catch {
      setError('Failed to update status.')
    } finally {
      setIsSubmitting(false)
    }
  }, [plan.id, getAuthToken, onStatusChange])

  const handleVerify = useCallback(async () => {
    setIsSubmitting(true)
    setError(null)

    try {
      const token = await getAuthToken()
      if (!token) {
        setError('Session expired. Please log in again.')
        return
      }

      const response = await fetch(`${API_BASE_URL}/api/v1/action-plans/${plan.id}/verify`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({}),
      })

      if (!response.ok) {
        throw new Error('Failed to verify plan.')
      }

      onStatusChange?.()
    } catch {
      setError('Failed to verify plan.')
    } finally {
      setIsSubmitting(false)
    }
  }, [plan.id, getAuthToken, onStatusChange])

  return (
    <Dialog open={open} onOpenChange={(isOpen) => { if (!isOpen) onClose() }}>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <DialogTitle className="flex-1">{plan.title}</DialogTitle>
            <Badge className={cn('shrink-0', statusConfig.className)}>
              {statusConfig.label}
            </Badge>
          </div>
          <DialogDescription>
            Action plan details and progress
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Description */}
          {plan.description && (
            <div>
              <h4 className="text-sm font-medium text-muted-foreground mb-1">Description</h4>
              <p className="text-sm">{plan.description}</p>
            </div>
          )}

          {/* Root Cause */}
          {plan.root_cause && (
            <div>
              <h4 className="text-sm font-medium text-muted-foreground mb-1">Root Cause</h4>
              <p className="text-sm">{plan.root_cause}</p>
            </div>
          )}

          {/* Corrective Action */}
          {plan.corrective_action && (
            <div>
              <h4 className="text-sm font-medium text-muted-foreground mb-1">Corrective Action</h4>
              <p className="text-sm">{plan.corrective_action}</p>
            </div>
          )}

          {/* Preventive Action */}
          {plan.preventive_action && (
            <div>
              <h4 className="text-sm font-medium text-muted-foreground mb-1">Preventive Action</h4>
              <p className="text-sm">{plan.preventive_action}</p>
            </div>
          )}

          {/* Metadata */}
          <div className="grid grid-cols-2 gap-3 text-sm">
            {plan.asset_name && (
              <div>
                <span className="text-muted-foreground">Asset: </span>
                <span>{plan.asset_name}</span>
              </div>
            )}
            {plan.owner_email && (
              <div>
                <span className="text-muted-foreground">Owner: </span>
                <span>{plan.owner_email}</span>
              </div>
            )}
            <div>
              <span className="text-muted-foreground">Priority: </span>
              <span className="capitalize">{plan.priority}</span>
            </div>
            {plan.due_date && (
              <div>
                <span className="text-muted-foreground">Due: </span>
                <span>{formatDate(plan.due_date + 'T00:00:00')}</span>
              </div>
            )}
            <div>
              <span className="text-muted-foreground">Created: </span>
              <span>{plan.created_at.split('T')[0]}</span>
            </div>
          </div>

          {/* Source Follow-Up Link */}
          {plan.source_followup_id && (
            <a
              href={`/followups/${plan.source_followup_id}/respond`}
              className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
            >
              <ExternalLink className="w-3 h-3" />
              View Source Follow-Up
            </a>
          )}

          {/* Progress Updates Timeline */}
          <div>
            <h4 className="text-sm font-medium text-muted-foreground mb-2">Progress Updates</h4>
            <UpdateTimeline updates={plan.updates || []} />
          </div>

          {/* Add Update Form */}
          <div className="space-y-2 border-t pt-4">
            <div className="flex gap-2">
              <Textarea
                placeholder="Add a progress update..."
                value={updateText}
                onChange={(e) => setUpdateText(e.target.value)}
                rows={2}
                className="flex-1"
              />
            </div>
            <div className="flex items-center gap-2">
              <div className="flex-1">
                <label htmlFor="status-change" className="sr-only">Status change</label>
                <select
                  id="status-change"
                  aria-label="Status change"
                  value={statusChange}
                  onChange={(e) => setStatusChange(e.target.value)}
                  className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <option value="">No status change</option>
                  {plan.status === 'open' && (
                    <option value="in_progress">Start Work</option>
                  )}
                  {(plan.status === 'open' || plan.status === 'in_progress') && (
                    <option value="completed">Mark Done</option>
                  )}
                </select>
              </div>
              <Button
                size="sm"
                onClick={handleAddUpdate}
                disabled={isSubmitting || !updateText.trim()}
                aria-label="Add Update"
              >
                {isSubmitting ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  'Add Update'
                )}
              </Button>
            </div>
          </div>

          {/* Status Action Buttons */}
          <div className="flex gap-2 border-t pt-4">
            {plan.status === 'open' && (
              <Button
                onClick={() => handleStatusChange('in_progress')}
                disabled={isSubmitting}
              >
                Mark In Progress
              </Button>
            )}
            {plan.status === 'in_progress' && (
              <Button
                onClick={() => handleStatusChange('completed')}
                disabled={isSubmitting}
              >
                Mark Completed
              </Button>
            )}
            {plan.status === 'completed' && (
              <Button
                onClick={handleVerify}
                disabled={isSubmitting}
              >
                Verify
              </Button>
            )}
          </div>

          {/* Error */}
          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}
        </div>

        {/* Radix dialog provides built-in close button (X icon with sr-only "Close") */}
      </DialogContent>
    </Dialog>
  )
}
