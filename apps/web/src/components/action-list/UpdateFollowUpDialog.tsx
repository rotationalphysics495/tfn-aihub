'use client'

import { useState, useCallback } from 'react'
import { CheckCircle2, Loader2 } from 'lucide-react'
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
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { updateFollowUp, type FollowUpItem } from '@/hooks/useMyFollowUps'

type Status = 'assigned' | 'in_progress' | 'resolved'

const STATUS_CONFIG: Record<Status, { label: string; variant: 'info' | 'warning' | 'success' }> = {
  assigned: { label: 'Assigned', variant: 'info' },
  in_progress: { label: 'In Progress', variant: 'warning' },
  resolved: { label: 'Resolved', variant: 'success' },
}

// Only allow forward transitions
const NEXT_STATUSES: Record<Status, Status[]> = {
  assigned: ['in_progress', 'resolved'],
  in_progress: ['resolved'],
  resolved: [],
}

interface UpdateFollowUpDialogProps {
  followUp: FollowUpItem
  open: boolean
  onOpenChange: (open: boolean) => void
  onUpdated: () => void
}

export function UpdateFollowUpDialog({
  followUp,
  open,
  onOpenChange,
  onUpdated,
}: UpdateFollowUpDialogProps) {
  const currentStatus = followUp.status
  const nextOptions = NEXT_STATUSES[currentStatus]

  const [selectedStatus, setSelectedStatus] = useState<Status>(nextOptions[0] ?? currentStatus)
  const [note, setNote] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleOpenChange = useCallback((open: boolean) => {
    if (!open) {
      // Reset state on close
      setSelectedStatus(nextOptions[0] ?? currentStatus)
      setNote('')
      setSubmitted(false)
      setError(null)
    }
    onOpenChange(open)
  }, [onOpenChange, nextOptions, currentStatus])

  const handleSubmit = useCallback(async () => {
    setIsSubmitting(true)
    setError(null)

    try {
      await updateFollowUp(followUp.id, selectedStatus, note.trim() || undefined)
      setSubmitted(true)
      setTimeout(() => {
        onOpenChange(false)
        onUpdated()
      }, 1500)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update status.')
    } finally {
      setIsSubmitting(false)
    }
  }, [followUp.id, selectedStatus, note, onOpenChange, onUpdated])

  const isResolved = currentStatus === 'resolved'

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        {submitted ? (
          <div className="flex flex-col items-center py-6 text-center">
            <CheckCircle2 className="w-12 h-12 text-success-green mb-3" />
            <DialogTitle className="text-lg font-semibold mb-1">
              Status Updated
            </DialogTitle>
            <DialogDescription>
              Follow-up marked as{' '}
              <span className="font-medium">{STATUS_CONFIG[selectedStatus].label}</span>.
            </DialogDescription>
          </div>
        ) : (
          <>
            <DialogHeader>
              <DialogTitle>Update Follow-Up Status</DialogTitle>
              <DialogDescription>
                Update the status of your assigned follow-up.
              </DialogDescription>
            </DialogHeader>

            {/* Context */}
            <div className="rounded-lg border border-border bg-muted/30 p-3 space-y-1">
              {followUp.asset_name && (
                <p className="text-xs text-muted-foreground font-medium">{followUp.asset_name}</p>
              )}
              <p className="text-sm text-foreground leading-snug">{followUp.action_summary}</p>
              <div className="flex items-center gap-2 pt-1">
                <span className="text-xs text-muted-foreground">Current status:</span>
                <Badge variant={STATUS_CONFIG[currentStatus].variant} className="text-xs">
                  {STATUS_CONFIG[currentStatus].label}
                </Badge>
              </div>
            </div>

            {isResolved ? (
              <p className="text-sm text-muted-foreground text-center py-2">
                This follow-up is already resolved. No further updates are needed.
              </p>
            ) : (
              <>
                {/* Status selection */}
                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground">
                    New status
                  </label>
                  <div className="flex gap-2">
                    {nextOptions.map((s) => (
                      <button
                        key={s}
                        type="button"
                        onClick={() => setSelectedStatus(s)}
                        className={cn(
                          'flex-1 rounded-md border px-3 py-2 text-sm font-medium transition-colors',
                          selectedStatus === s
                            ? 'border-primary bg-primary text-primary-foreground'
                            : 'border-border bg-background text-foreground hover:bg-muted'
                        )}
                      >
                        {STATUS_CONFIG[s].label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Note */}
                <div className="space-y-2">
                  <label htmlFor="update-note" className="text-sm font-medium text-foreground">
                    Note{' '}
                    <span className="text-muted-foreground font-normal">(optional)</span>
                  </label>
                  <Textarea
                    id="update-note"
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                    placeholder="Describe what you've done or found..."
                    rows={3}
                  />
                </div>

                {error && (
                  <p className="text-sm text-safety-red">{error}</p>
                )}

                <DialogFooter>
                  <Button
                    variant="outline"
                    onClick={() => handleOpenChange(false)}
                    disabled={isSubmitting}
                  >
                    Cancel
                  </Button>
                  <Button onClick={handleSubmit} disabled={isSubmitting}>
                    {isSubmitting ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Saving...
                      </>
                    ) : (
                      'Update Status'
                    )}
                  </Button>
                </DialogFooter>
              </>
            )}
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
