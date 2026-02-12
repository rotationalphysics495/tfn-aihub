'use client'

import { useState, useEffect, useCallback } from 'react'
import { CheckCircle2, Loader2, ClipboardList } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { createClient } from '@/lib/supabase/client'
import { cn } from '@/lib/utils'

export interface ActionPlanPrefill {
  followUpId: string
  actionSummary: string
  assetName: string | null
  responseText: string
  category: string | null
}

interface ActionPlanFormProps {
  open: boolean
  onClose: () => void
  onSuccess?: (plan: { id: string; title: string; status: string }) => void
  prefill: ActionPlanPrefill
}

const CATEGORY_MAP: Record<string, string> = {
  safety: 'corrective',
  oee: 'improvement',
  financial: 'corrective',
}

const PRIORITY_MAP: Record<string, string> = {
  safety: 'high',
  oee: 'medium',
  financial: 'medium',
}

function buildTitle(actionSummary: string): string {
  const prefix = 'Action Plan: '
  const maxLen = 80
  const available = maxLen - prefix.length
  const summary = actionSummary.length > available
    ? actionSummary.slice(0, available)
    : actionSummary
  return `${prefix}${summary}`
}

export function ActionPlanForm({ open, onClose, onSuccess, prefill }: ActionPlanFormProps) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [category, setCategory] = useState('')
  const [rootCause, setRootCause] = useState('')
  const [correctiveAction, setCorrectiveAction] = useState('')
  const [preventiveAction, setPreventiveAction] = useState('')
  const [priority, setPriority] = useState('')
  const [dueDate, setDueDate] = useState('')
  const [assetId, setAssetId] = useState<string | null>(null)

  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Reset and pre-fill state when dialog opens
  useEffect(() => {
    if (!open) return

    setTitle(buildTitle(prefill.actionSummary))
    setDescription(
      prefill.responseText
        ? `${prefill.actionSummary}\n\nInvestigation findings:\n${prefill.responseText}`
        : prefill.actionSummary
    )
    setRootCause(prefill.responseText || '')
    setCorrectiveAction('')
    setPreventiveAction('')
    setDueDate('')
    setSubmitted(false)
    setError(null)
    setAssetId(null)

    if (prefill.category && CATEGORY_MAP[prefill.category]) {
      setCategory(CATEGORY_MAP[prefill.category])
    } else {
      setCategory('')
    }

    if (prefill.category && PRIORITY_MAP[prefill.category]) {
      setPriority(PRIORITY_MAP[prefill.category])
    } else {
      setPriority('')
    }

  }, [open, prefill])

  // Async asset lookup for when the sync result isn't available
  useEffect(() => {
    if (!open || !prefill.assetName) return

    let cancelled = false

    async function lookupAsset() {
      try {
        const supabase = createClient()
        const result = await supabase
          .from('assets')
          .select('id')
          .eq('name', prefill.assetName!)
          .single()

        if (!cancelled && result.data) {
          setAssetId(result.data.id)
        }
      } catch {
        // Asset lookup failure is non-blocking
      }
    }

    lookupAsset()

    return () => { cancelled = true }
  }, [open, prefill.assetName])

  const handleSubmit = useCallback(async () => {
    // Validate required fields
    if (!title.trim() || !category || !priority || !dueDate) {
      return
    }

    setIsSubmitting(true)
    setError(null)

    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.access_token) {
        setError('Session expired. Please log in again.')
        setIsSubmitting(false)
        return
      }

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

      const payload: Record<string, unknown> = {
        title: title.trim(),
        description: description.trim() || undefined,
        category,
        root_cause: rootCause.trim() || undefined,
        corrective_action: correctiveAction.trim() || undefined,
        preventive_action: preventiveAction.trim() || undefined,
        priority,
        due_date: dueDate,
        source_followup_id: prefill.followUpId,
        asset_id: assetId || undefined,
      }

      // Remove undefined values
      Object.keys(payload).forEach(key => {
        if (payload[key] === undefined) delete payload[key]
      })

      const response = await fetch(`${apiUrl}/api/v1/action-plans`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}))
        throw new Error(errData.detail || `Failed to create action plan (${response.status})`)
      }

      const data = await response.json()

      setSubmitted(true)

      if (onSuccess) {
        onSuccess({ id: data.id, title: data.title, status: data.status })
      }

      // Auto-close after success
      setTimeout(() => onClose(), 1500)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create action plan.')
    } finally {
      setIsSubmitting(false)
    }
  }, [title, description, category, rootCause, correctiveAction, preventiveAction, priority, dueDate, prefill.followUpId, assetId, onSuccess, onClose])

  const selectClasses = cn(
    'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm',
    'ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
    'disabled:cursor-not-allowed disabled:opacity-50'
  )

  return (
    <Dialog open={open} onOpenChange={(isOpen) => { if (!isOpen) onClose() }}>
      <DialogContent className="sm:max-w-lg max-h-[90vh] overflow-y-auto">
        {submitted ? (
          <div className="flex flex-col items-center py-6 text-center">
            <CheckCircle2 className="w-12 h-12 text-success-green mb-3" />
            <DialogTitle className="text-lg font-semibold mb-1">
              Action Plan Created
            </DialogTitle>
            <DialogDescription>
              The action plan has been created successfully.
            </DialogDescription>
          </div>
        ) : (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <ClipboardList className="w-5 h-5" />
                Create Action Plan
              </DialogTitle>
              <DialogDescription>
                Create an action plan from follow-up investigation findings.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4">
              {/* Asset display (read-only) */}
              {prefill.assetName && (
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-muted-foreground">Asset:</span>
                  <span className="text-sm">{prefill.assetName}</span>
                </div>
              )}

              {/* Title */}
              <div className="space-y-2">
                <label htmlFor="ap-title" className="text-sm font-medium text-foreground">
                  Title <span className="text-safety-red">*</span>
                </label>
                <Input
                  id="ap-title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Action plan title"
                />
              </div>

              {/* Description */}
              <div className="space-y-2">
                <label htmlFor="ap-description" className="text-sm font-medium text-foreground">
                  Description
                </label>
                <Textarea
                  id="ap-description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe the action plan..."
                  rows={2}
                />
              </div>

              {/* Category */}
              <div className="space-y-2">
                <label htmlFor="ap-category" className="text-sm font-medium text-foreground">
                  Category <span className="text-safety-red">*</span>
                </label>
                <select
                  id="ap-category"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className={selectClasses}
                >
                  <option value="">Select category...</option>
                  <option value="corrective">Corrective</option>
                  <option value="preventive">Preventive</option>
                  <option value="improvement">Improvement</option>
                </select>
              </div>

              {/* Root Cause */}
              <div className="space-y-2">
                <label htmlFor="ap-root-cause" className="text-sm font-medium text-foreground">
                  Root Cause
                </label>
                <Textarea
                  id="ap-root-cause"
                  value={rootCause}
                  onChange={(e) => setRootCause(e.target.value)}
                  placeholder="Describe the root cause..."
                  rows={2}
                />
              </div>

              {/* Corrective Action */}
              <div className="space-y-2">
                <label htmlFor="ap-corrective-action" className="text-sm font-medium text-foreground">
                  Corrective Action
                </label>
                <Textarea
                  id="ap-corrective-action"
                  value={correctiveAction}
                  onChange={(e) => setCorrectiveAction(e.target.value)}
                  placeholder="Describe corrective actions..."
                  rows={2}
                />
              </div>

              {/* Preventive Action */}
              <div className="space-y-2">
                <label htmlFor="ap-preventive-action" className="text-sm font-medium text-foreground">
                  Preventive Action
                </label>
                <Textarea
                  id="ap-preventive-action"
                  value={preventiveAction}
                  onChange={(e) => setPreventiveAction(e.target.value)}
                  placeholder="Describe preventive actions..."
                  rows={2}
                />
              </div>

              {/* Priority */}
              <div className="space-y-2">
                <label htmlFor="ap-priority" className="text-sm font-medium text-foreground">
                  Priority <span className="text-safety-red">*</span>
                </label>
                <select
                  id="ap-priority"
                  value={priority}
                  onChange={(e) => setPriority(e.target.value)}
                  className={selectClasses}
                >
                  <option value="">Select priority...</option>
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>

              {/* Due Date */}
              <div className="space-y-2">
                <label htmlFor="ap-due-date" className="text-sm font-medium text-foreground">
                  Due Date <span className="text-safety-red">*</span>
                </label>
                <input
                  type="date"
                  id="ap-due-date"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  className={selectClasses}
                />
              </div>

              {/* Error */}
              {error && (
                <p className="text-sm text-safety-red">{error}</p>
              )}
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={onClose} disabled={isSubmitting}>
                Cancel
              </Button>
              <Button
                onClick={handleSubmit}
                disabled={isSubmitting || !title.trim() || !category || !priority || !dueDate}
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <ClipboardList className="w-4 h-4" />
                    Create Action Plan
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
