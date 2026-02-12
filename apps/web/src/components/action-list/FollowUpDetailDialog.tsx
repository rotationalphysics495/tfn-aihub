'use client'

import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Clock, User, ClipboardList, ExternalLink } from 'lucide-react'
import type { FollowUpItem } from '@/hooks/useMyFollowUps'
import { useFollowUpMessages } from '@/hooks/useFollowUpMessages'
import { useActionPlans, type ActionPlanResponse } from '@/hooks/useActionPlans'
import { ActionPlanForm, type ActionPlanPrefill } from '@/components/action-plans'
import { MessageThread } from './MessageThread'

const STATUS_CONFIG: Record<string, { label: string; variant: 'info' | 'warning' | 'success' }> = {
  assigned: { label: 'Assigned', variant: 'info' },
  in_progress: { label: 'In Progress', variant: 'warning' },
  resolved: { label: 'Resolved', variant: 'success' },
}

function formatTimestamp(isoString: string): string {
  const d = new Date(isoString)
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

interface FollowUpDetailDialogProps {
  followUp: FollowUpItem
  open: boolean
  onClose: () => void
}

export function FollowUpDetailDialog({ followUp, open, onClose }: FollowUpDetailDialogProps) {
  const {
    messages,
    isLoading: messagesLoading,
    assignee_name,
    markViewed,
  } = useFollowUpMessages({ followUpId: followUp.id, autoFetch: open })

  const { getLinkedActionPlan } = useActionPlans()

  const [linkedPlan, setLinkedPlan] = useState<ActionPlanResponse | null>(null)
  const [linkedPlanLoading, setLinkedPlanLoading] = useState(false)
  const [actionPlanDialogOpen, setActionPlanDialogOpen] = useState(false)

  useEffect(() => {
    if (open && followUp) {
      try {
        localStorage.setItem(
          `followup-viewed-${followUp.id}`,
          Date.now().toString()
        )
      } catch {
        // localStorage unavailable
      }
      markViewed()
    }
  }, [open, followUp, markViewed])

  // Check for linked action plan when dialog opens
  useEffect(() => {
    if (!open) {
      setLinkedPlan(null)
      setLinkedPlanLoading(false)
      return
    }

    let cancelled = false

    async function checkLinkedPlan() {
      setLinkedPlanLoading(true)
      try {
        const plan = await getLinkedActionPlan(followUp.id)
        if (!cancelled) {
          setLinkedPlan(plan)
        }
      } catch {
        // Failure to find linked plan is non-blocking
      } finally {
        if (!cancelled) {
          setLinkedPlanLoading(false)
        }
      }
    }

    checkLinkedPlan()

    return () => { cancelled = true }
  }, [open, followUp.id, getLinkedActionPlan])

  const statusConfig = STATUS_CONFIG[followUp.status] || STATUS_CONFIG.assigned

  // Determine if "Create Action Plan" button should show
  const hasResponse = followUp.status !== 'assigned'
  const showCreateButton = hasResponse && !linkedPlan && !linkedPlanLoading

  // Extract response text from inbound messages for pre-fill
  const inboundMessages = messages.filter(m => m.direction === 'inbound')
  const responseText = inboundMessages.length > 0
    ? inboundMessages[inboundMessages.length - 1].body
    : ''

  const prefill: ActionPlanPrefill = {
    followUpId: followUp.id,
    actionSummary: followUp.action_summary,
    assetName: followUp.asset_name,
    responseText,
    category: followUp.category,
  }

  const handleActionPlanSuccess = (plan: { id: string; title: string; status: string }) => {
    setLinkedPlan({
      id: plan.id,
      title: plan.title,
      status: plan.status,
    } as ActionPlanResponse)
    setActionPlanDialogOpen(false)
  }

  return (
    <>
      <Dialog open={open} onOpenChange={(isOpen) => { if (!isOpen) onClose() }}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {followUp.asset_name && (
                <span>{followUp.asset_name}</span>
              )}
              <Badge variant={statusConfig.variant}>
                {statusConfig.label}
              </Badge>
            </DialogTitle>
            <DialogDescription>
              {followUp.action_summary}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {followUp.category && (
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-muted-foreground">Category:</span>
                <span className="text-sm capitalize">{followUp.category}</span>
              </div>
            )}

            {followUp.assigned_to_email && (
              <div className="flex items-center gap-2">
                <User className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium text-muted-foreground">Assigned to:</span>
                <span className="text-sm">{followUp.assigned_to_email}</span>
              </div>
            )}

            <div>
              <span className="text-sm font-medium text-muted-foreground">Assignment Note</span>
              <p className="text-sm mt-1">
                {followUp.note || 'No note provided'}
              </p>
            </div>

            <div className="border-t pt-3">
              <MessageThread
                messages={messages}
                assignee_name={assignee_name || followUp.assigned_to_email || ''}
                loading={messagesLoading}
              />
            </div>

            {/* Linked Action Plan or Create Button */}
            {linkedPlan && (
              <div className="border-t pt-3">
                <a
                  href={`/action-plans/${linkedPlan.id}`}
                  className="flex items-center gap-2 text-sm text-info-blue hover:underline"
                  role="link"
                >
                  <ExternalLink className="h-4 w-4" />
                  Action Plan: {linkedPlan.title?.replace(/^Action Plan:\s*/i, '') || linkedPlan.id}
                </a>
              </div>
            )}

            {showCreateButton && (
              <div className="border-t pt-3">
                <Button
                  variant="outline"
                  onClick={() => setActionPlanDialogOpen(true)}
                  className="w-full"
                >
                  <ClipboardList className="w-4 h-4 mr-2" />
                  Create Action Plan
                </Button>
              </div>
            )}

            <div className="border-t pt-3 space-y-2">
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Clock className="h-3 w-3" />
                <span>Created: {formatTimestamp(followUp.created_at)}</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Clock className="h-3 w-3" />
                <span>Last updated: {formatTimestamp(followUp.updated_at)}</span>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <ActionPlanForm
        open={actionPlanDialogOpen}
        onClose={() => setActionPlanDialogOpen(false)}
        onSuccess={handleActionPlanSuccess}
        prefill={prefill}
      />
    </>
  )
}
