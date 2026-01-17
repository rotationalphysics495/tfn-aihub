'use client'

/**
 * HandoffCreator Component (Story 9.1, Task 4)
 *
 * AC#1: Create handoff flow with pre-populated assets and auto-detected shift
 * AC#2: Handoff screen with summary, notes, and confirmation
 * AC#3: No assets assigned error handling
 * AC#4: Duplicate handoff handling
 *
 * Wizard-style flow:
 * - Step 1: Shift confirmation (auto-detected shift, assets list)
 * - Step 2: Summary display (auto-generated + editable text notes)
 * - Step 3: Voice notes (placeholder for Story 9.3)
 * - Step 4: Confirmation
 *
 * References:
 * - [Source: architecture/voice-briefing.md#Shift-Handoff-Workflow]
 * - [Source: prd-functional-requirements.md#FR21-FR30]
 */

import { useState, useCallback, useEffect } from 'react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { createClient } from '@/lib/supabase/client'

// ============================================================================
// Types
// ============================================================================

interface ShiftInfo {
  shift_type: 'morning' | 'afternoon' | 'night'
  start_time: string
  end_time: string
  shift_date: string
}

interface SupervisorAsset {
  asset_id: string
  asset_name: string
  area_name: string | null
}

interface ExistingHandoff {
  exists: boolean
  existing_handoff_id?: string
  status?: string
  message: string
  can_edit: boolean
  can_add_supplemental: boolean
}

interface InitiateResponse {
  shift_info: ShiftInfo
  assigned_assets: SupervisorAsset[]
  existing_handoff: ExistingHandoff | null
  can_create: boolean
  message: string
}

interface HandoffCreatorProps {
  /** User ID */
  userId: string
  /** Called when handoff is successfully created */
  onComplete: (handoffId: string) => void
  /** Called when user cancels */
  onCancel?: () => void
  /** Called when redirect to edit is needed */
  onEditExisting?: (handoffId: string) => void
  /** Optional CSS class name */
  className?: string
}

type WizardStep = 'loading' | 'shift_confirmation' | 'summary_notes' | 'voice_notes' | 'confirmation' | 'error'

// ============================================================================
// Helper Functions
// ============================================================================

function formatShiftType(type: string): string {
  return type.charAt(0).toUpperCase() + type.slice(1)
}

function formatTime(isoString: string): string {
  const date = new Date(isoString)
  return date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  })
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  })
}

// ============================================================================
// Component
// ============================================================================

export function HandoffCreator({
  userId,
  onComplete,
  onCancel,
  onEditExisting,
  className,
}: HandoffCreatorProps) {
  // State
  const [currentStep, setCurrentStep] = useState<WizardStep>('loading')
  const [shiftInfo, setShiftInfo] = useState<ShiftInfo | null>(null)
  const [assignedAssets, setAssignedAssets] = useState<SupervisorAsset[]>([])
  const [selectedAssets, setSelectedAssets] = useState<Set<string>>(new Set())
  const [existingHandoff, setExistingHandoff] = useState<ExistingHandoff | null>(null)
  const [textNotes, setTextNotes] = useState('')
  const [summary, setSummary] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Computed values
  const canCreate = assignedAssets.length > 0 && !existingHandoff?.exists
  const stepSequence: WizardStep[] = ['shift_confirmation', 'summary_notes', 'voice_notes', 'confirmation']
  const currentStepIndex = stepSequence.indexOf(currentStep)
  const totalSteps = stepSequence.length

  // ============================================================================
  // API Calls
  // ============================================================================

  const initiateHandoff = useCallback(async () => {
    setError(null)

    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.access_token) {
        throw new Error('Not authenticated')
      }

      const response = await fetch('/api/v1/handoff/initiate', {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
        },
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Failed to initiate handoff')
      }

      const data: InitiateResponse = await response.json()

      setShiftInfo(data.shift_info)
      setAssignedAssets(data.assigned_assets)
      setExistingHandoff(data.existing_handoff)

      // Select all assets by default
      setSelectedAssets(new Set(data.assigned_assets.map(a => a.asset_id)))

      // Check for error conditions
      if (!data.can_create && data.assigned_assets.length === 0) {
        // No assets assigned (AC#3)
        setError(data.message)
        setCurrentStep('error')
      } else if (data.existing_handoff?.can_edit) {
        // Existing draft handoff (AC#4)
        setCurrentStep('shift_confirmation')
      } else {
        setCurrentStep('shift_confirmation')
      }
    } catch (err) {
      console.error('Error initiating handoff:', err)
      setError(err instanceof Error ? err.message : 'Failed to initiate handoff')
      setCurrentStep('error')
    }
  }, [userId])

  const createHandoff = useCallback(async () => {
    setIsSubmitting(true)
    setError(null)

    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.access_token) {
        throw new Error('Not authenticated')
      }

      const response = await fetch('/api/v1/handoff/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text_notes: textNotes || null,
          assets_covered: Array.from(selectedAssets),
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        if (response.status === 409) {
          // Duplicate handoff (AC#4)
          const detail = errorData.detail || {}
          if (detail.action === 'edit' && onEditExisting) {
            onEditExisting(detail.existing_handoff_id)
            return
          }
        }
        throw new Error(errorData.detail?.message || errorData.detail || 'Failed to create handoff')
      }

      const data = await response.json()
      onComplete(data.id)
    } catch (err) {
      console.error('Error creating handoff:', err)
      setError(err instanceof Error ? err.message : 'Failed to create handoff')
    } finally {
      setIsSubmitting(false)
    }
  }, [userId, textNotes, selectedAssets, onComplete, onEditExisting])

  // ============================================================================
  // Effects
  // ============================================================================

  useEffect(() => {
    initiateHandoff()
  }, [initiateHandoff])

  // ============================================================================
  // Handlers
  // ============================================================================

  const handleNext = useCallback(() => {
    const nextIndex = currentStepIndex + 1
    if (nextIndex < stepSequence.length) {
      setCurrentStep(stepSequence[nextIndex])
    }
  }, [currentStepIndex, stepSequence])

  const handleBack = useCallback(() => {
    const prevIndex = currentStepIndex - 1
    if (prevIndex >= 0) {
      setCurrentStep(stepSequence[prevIndex])
    }
  }, [currentStepIndex, stepSequence])

  const handleAssetToggle = useCallback((assetId: string) => {
    setSelectedAssets(prev => {
      const next = new Set(prev)
      if (next.has(assetId)) {
        next.delete(assetId)
      } else {
        next.add(assetId)
      }
      return next
    })
  }, [])

  const handleSelectAll = useCallback(() => {
    setSelectedAssets(new Set(assignedAssets.map(a => a.asset_id)))
  }, [assignedAssets])

  const handleDeselectAll = useCallback(() => {
    setSelectedAssets(new Set())
  }, [])

  // ============================================================================
  // Render Helpers
  // ============================================================================

  const ProgressIndicator = () => (
    <div className="flex items-center justify-center gap-1 mb-6">
      {stepSequence.map((step, idx) => (
        <div
          key={step}
          className={cn(
            'h-2 rounded-full transition-all',
            idx === currentStepIndex
              ? 'w-8 bg-primary'
              : idx < currentStepIndex
                ? 'w-2 bg-primary/60'
                : 'w-2 bg-muted'
          )}
        />
      ))}
    </div>
  )

  // ============================================================================
  // Step Renderers
  // ============================================================================

  const renderLoadingStep = () => (
    <Card className="w-full max-w-lg mx-auto">
      <CardContent className="flex flex-col items-center justify-center py-12">
        <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-muted-foreground">Loading shift information...</p>
      </CardContent>
    </Card>
  )

  const renderErrorStep = () => (
    <Card className="w-full max-w-lg mx-auto">
      <CardHeader className="text-center">
        <div className="w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center mx-auto mb-4">
          <svg
            className="w-8 h-8 text-destructive"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>
        <CardTitle className="text-xl">Unable to Create Handoff</CardTitle>
        <CardDescription className="text-base mt-2">
          {error || 'An error occurred'}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Button
          variant="outline"
          onClick={onCancel}
          className="w-full touch-target"
        >
          Go Back
        </Button>
      </CardContent>
    </Card>
  )

  const renderShiftConfirmationStep = () => (
    <Card className="w-full max-w-lg mx-auto">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl">Create Shift Handoff</CardTitle>
        <CardDescription className="text-base mt-2">
          Confirm your shift details and select the assets to include
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Existing handoff warning */}
        {existingHandoff?.exists && (
          <div className="bg-warning-amber/10 border border-warning-amber/30 rounded-lg p-4">
            <p className="text-sm font-medium text-warning-amber-dark mb-2">
              {existingHandoff.message}
            </p>
            {existingHandoff.can_edit && onEditExisting && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onEditExisting(existingHandoff.existing_handoff_id!)}
              >
                Edit Existing Handoff
              </Button>
            )}
          </div>
        )}

        {/* Shift info */}
        {shiftInfo && (
          <div className="bg-muted/50 rounded-lg p-4 space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Shift Type</span>
              <span className="font-medium">{formatShiftType(shiftInfo.shift_type)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Date</span>
              <span className="font-medium">{formatDate(shiftInfo.shift_date)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Time Range</span>
              <span className="font-medium">
                {formatTime(shiftInfo.start_time)} - {formatTime(shiftInfo.end_time)}
              </span>
            </div>
          </div>
        )}

        {/* Assets list */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="font-medium">Assets Covered</h4>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={handleSelectAll}
                className="text-xs text-primary hover:underline"
              >
                Select All
              </button>
              <span className="text-muted-foreground">|</span>
              <button
                type="button"
                onClick={handleDeselectAll}
                className="text-xs text-primary hover:underline"
              >
                Deselect All
              </button>
            </div>
          </div>

          <div className="space-y-2 max-h-48 overflow-y-auto">
            {assignedAssets.map(asset => (
              <label
                key={asset.asset_id}
                className={cn(
                  'flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors',
                  selectedAssets.has(asset.asset_id)
                    ? 'bg-primary/5 border-primary'
                    : 'bg-background hover:bg-muted/50'
                )}
              >
                <input
                  type="checkbox"
                  checked={selectedAssets.has(asset.asset_id)}
                  onChange={() => handleAssetToggle(asset.asset_id)}
                  className="h-4 w-4 rounded border-gray-300"
                />
                <div className="flex-1">
                  <div className="font-medium text-sm">{asset.asset_name}</div>
                  {asset.area_name && (
                    <div className="text-xs text-muted-foreground">{asset.area_name}</div>
                  )}
                </div>
              </label>
            ))}
          </div>

          {selectedAssets.size === 0 && (
            <p className="text-sm text-destructive">
              Please select at least one asset to include in the handoff
            </p>
          )}
        </div>

        {/* Navigation */}
        <div className="flex gap-3 pt-4">
          <Button
            variant="outline"
            onClick={onCancel}
            className="flex-1 touch-target"
          >
            Cancel
          </Button>
          <Button
            onClick={handleNext}
            className="flex-1 touch-target"
            disabled={selectedAssets.size === 0 || (existingHandoff?.exists && !existingHandoff.can_add_supplemental)}
          >
            Next
          </Button>
        </div>
      </CardContent>
    </Card>
  )

  const renderSummaryNotesStep = () => (
    <Card className="w-full max-w-lg mx-auto">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl">Add Notes</CardTitle>
        <CardDescription className="text-base mt-2">
          Add any additional notes for the incoming shift
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Auto-generated summary placeholder */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Shift Summary</label>
          <div className="bg-muted/50 rounded-lg p-4 min-h-[100px]">
            <p className="text-sm text-muted-foreground italic">
              Auto-generated summary will be available in Story 9.2
            </p>
          </div>
        </div>

        {/* Text notes */}
        <div className="space-y-2">
          <label htmlFor="text-notes" className="text-sm font-medium">
            Additional Notes (Optional)
          </label>
          <textarea
            id="text-notes"
            value={textNotes}
            onChange={(e) => setTextNotes(e.target.value)}
            placeholder="Add any important information for the incoming shift..."
            className="w-full min-h-[120px] p-3 rounded-lg border bg-background resize-none focus:outline-none focus:ring-2 focus:ring-primary"
            maxLength={2000}
          />
          <p className="text-xs text-muted-foreground text-right">
            {textNotes.length}/2000 characters
          </p>
        </div>

        {/* Navigation */}
        <div className="flex gap-3 pt-4">
          <Button
            variant="outline"
            onClick={handleBack}
            className="flex-1 touch-target"
          >
            Back
          </Button>
          <Button
            onClick={handleNext}
            className="flex-1 touch-target"
          >
            Next
          </Button>
        </div>
      </CardContent>
    </Card>
  )

  const renderVoiceNotesStep = () => (
    <Card className="w-full max-w-lg mx-auto">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl">Voice Notes</CardTitle>
        <CardDescription className="text-base mt-2">
          Record voice notes to include in your handoff
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Placeholder for voice recording */}
        <div className="bg-muted/30 rounded-lg p-8 flex flex-col items-center justify-center min-h-[200px] border-2 border-dashed border-muted">
          <svg
            className="w-16 h-16 text-muted-foreground mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
            />
          </svg>
          <p className="text-muted-foreground text-center">
            Voice note recording will be available in Story 9.3
          </p>
          <Button
            variant="outline"
            className="mt-4"
            disabled
          >
            Add Voice Note
          </Button>
        </div>

        {/* Voice notes list placeholder */}
        <div className="text-sm text-muted-foreground text-center">
          No voice notes attached
        </div>

        {/* Navigation */}
        <div className="flex gap-3 pt-4">
          <Button
            variant="outline"
            onClick={handleBack}
            className="flex-1 touch-target"
          >
            Back
          </Button>
          <Button
            onClick={handleNext}
            className="flex-1 touch-target"
          >
            Next
          </Button>
        </div>
      </CardContent>
    </Card>
  )

  const renderConfirmationStep = () => (
    <Card className="w-full max-w-lg mx-auto">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl">Review &amp; Submit</CardTitle>
        <CardDescription className="text-base mt-2">
          Review your handoff details before submitting
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Summary */}
        <div className="bg-muted/50 rounded-lg p-4 space-y-4">
          {/* Shift info */}
          {shiftInfo && (
            <div className="space-y-1">
              <h4 className="font-medium text-sm">Shift Information</h4>
              <div className="text-sm text-muted-foreground">
                {formatShiftType(shiftInfo.shift_type)} shift on {formatDate(shiftInfo.shift_date)}
              </div>
              <div className="text-sm text-muted-foreground">
                {formatTime(shiftInfo.start_time)} - {formatTime(shiftInfo.end_time)}
              </div>
            </div>
          )}

          {/* Assets */}
          <div className="space-y-1 pt-2 border-t">
            <h4 className="font-medium text-sm">Assets Covered</h4>
            <div className="text-sm text-muted-foreground">
              {selectedAssets.size} asset{selectedAssets.size !== 1 ? 's' : ''} selected
            </div>
          </div>

          {/* Notes */}
          {textNotes && (
            <div className="space-y-1 pt-2 border-t">
              <h4 className="font-medium text-sm">Notes</h4>
              <div className="text-sm text-muted-foreground line-clamp-3">
                {textNotes}
              </div>
            </div>
          )}
        </div>

        {/* Error display */}
        {error && (
          <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {/* Navigation */}
        <div className="flex gap-3 pt-4">
          <Button
            variant="outline"
            onClick={handleBack}
            className="flex-1 touch-target"
            disabled={isSubmitting}
          >
            Back
          </Button>
          <Button
            onClick={createHandoff}
            className="flex-1 touch-target"
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <>
                <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin mr-2" />
                Creating...
              </>
            ) : (
              'Create Handoff'
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  )

  // ============================================================================
  // Main Render
  // ============================================================================

  const renderStep = () => {
    switch (currentStep) {
      case 'loading':
        return renderLoadingStep()
      case 'error':
        return renderErrorStep()
      case 'shift_confirmation':
        return renderShiftConfirmationStep()
      case 'summary_notes':
        return renderSummaryNotesStep()
      case 'voice_notes':
        return renderVoiceNotesStep()
      case 'confirmation':
        return renderConfirmationStep()
      default:
        return null
    }
  }

  return (
    <div className={cn('w-full max-w-2xl mx-auto', className)}>
      {/* Header with step indicator */}
      {currentStep !== 'loading' && currentStep !== 'error' && (
        <>
          <div className="flex items-center justify-between mb-4">
            <div className="text-sm text-muted-foreground">
              Step {currentStepIndex + 1} of {totalSteps}
            </div>
            <button
              onClick={onCancel}
              className="p-2 rounded-full hover:bg-muted transition-colors"
              aria-label="Cancel handoff creation"
            >
              <svg
                className="w-5 h-5 text-muted-foreground"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          <ProgressIndicator />
        </>
      )}

      {/* Step content */}
      {renderStep()}
    </div>
  )
}

export default HandoffCreator
