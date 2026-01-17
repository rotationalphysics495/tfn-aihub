'use client'

/**
 * OnboardingFlow Component (Story 8.8)
 *
 * AC#1: Onboarding triggers on first interaction
 * AC#2: Multi-step wizard with all preference steps
 * AC#3: Save preferences on completion
 * AC#4: Handle abandonment with defaults
 *
 * Steps:
 * 1. Welcome + explain quick setup
 * 2. Role selection (Plant Manager or Supervisor)
 * 3. For Supervisor: display assigned assets
 * 4-6. Preferences (Area order, Detail level, Voice)
 * 7. Confirmation + handoff
 *
 * References:
 * - [Source: architecture/voice-briefing.md#User Preferences Architecture]
 * - [Source: prd-voice-briefing-context.md#Onboarding Flow Summary]
 */

import { useState, useCallback, useEffect } from 'react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { WelcomeStep } from '@/components/onboarding/WelcomeStep'
import { RoleStep, type UserRole } from '@/components/onboarding/RoleStep'
import { SupervisorAssetsStep } from '@/components/onboarding/SupervisorAssetsStep'
import { PreferencesStep, type PreferencesData } from '@/components/onboarding/PreferencesStep'
import { DEFAULT_AREA_ORDER } from '@/components/preferences/AreaOrderSelector'
import { createClient } from '@/lib/supabase/client'

export interface OnboardingData {
  role: UserRole | null
  areaOrder: string[]
  detailLevel: 'summary' | 'detailed'
  voiceEnabled: boolean
}

interface OnboardingFlowProps {
  /** Current user ID */
  userId: string
  /** URL to redirect to after completion */
  originalDestination: string | null
  /** Called when onboarding is completed */
  onComplete: () => void
  /** Called when onboarding is dismissed */
  onDismiss?: () => void
  /** Optional CSS class name */
  className?: string
}

type OnboardingStep = 'welcome' | 'role' | 'supervisor_assets' | 'preferences' | 'confirmation'

const STEP_SEQUENCE_PLANT_MANAGER: OnboardingStep[] = ['welcome', 'role', 'preferences', 'confirmation']
const STEP_SEQUENCE_SUPERVISOR: OnboardingStep[] = ['welcome', 'role', 'supervisor_assets', 'preferences', 'confirmation']

const DEFAULT_ONBOARDING_DATA: OnboardingData = {
  role: null,
  areaOrder: DEFAULT_AREA_ORDER,
  detailLevel: 'summary',
  voiceEnabled: true,
}

export function OnboardingFlow({
  userId,
  originalDestination,
  onComplete,
  onDismiss,
  className,
}: OnboardingFlowProps) {
  const [currentStep, setCurrentStep] = useState<OnboardingStep>('welcome')
  const [data, setData] = useState<OnboardingData>(DEFAULT_ONBOARDING_DATA)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Determine step sequence based on role
  const stepSequence = data.role === 'supervisor'
    ? STEP_SEQUENCE_SUPERVISOR
    : STEP_SEQUENCE_PLANT_MANAGER

  const currentStepIndex = stepSequence.indexOf(currentStep)
  const totalSteps = stepSequence.length
  const isLastStep = currentStepIndex === totalSteps - 1

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

  const handleRoleSelect = useCallback((role: UserRole) => {
    setData(prev => ({ ...prev, role }))
  }, [])

  const handlePreferencesChange = useCallback((preferences: PreferencesData) => {
    setData(prev => ({
      ...prev,
      areaOrder: preferences.areaOrder,
      detailLevel: preferences.detailLevel,
      voiceEnabled: preferences.voiceEnabled,
    }))
  }, [])

  const savePreferences = useCallback(async (markComplete: boolean) => {
    setIsSubmitting(true)
    setError(null)

    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.access_token) {
        throw new Error('Not authenticated')
      }

      const response = await fetch('/api/v1/preferences', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          role: data.role || 'plant_manager',
          area_order: data.areaOrder.length > 0 ? data.areaOrder : DEFAULT_AREA_ORDER,
          detail_level: data.detailLevel,
          voice_enabled: data.voiceEnabled,
          onboarding_complete: markComplete,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Failed to save preferences')
      }

      return true
    } catch (err) {
      console.error('Error saving preferences:', err)
      setError(err instanceof Error ? err.message : 'Failed to save preferences')
      return false
    } finally {
      setIsSubmitting(false)
    }
  }, [data])

  const handleComplete = useCallback(async () => {
    const success = await savePreferences(true)
    if (success) {
      onComplete()
    }
  }, [savePreferences, onComplete])

  const handleDismiss = useCallback(async () => {
    // Apply defaults when dismissing
    const defaultData = {
      role: 'plant_manager' as UserRole,
      areaOrder: DEFAULT_AREA_ORDER,
      detailLevel: 'summary' as const,
      voiceEnabled: true,
    }
    setData(defaultData)

    // Save defaults but mark onboarding_complete as false so it triggers again
    const supabase = createClient()
    const { data: { session } } = await supabase.auth.getSession()

    if (session?.access_token) {
      await fetch('/api/v1/preferences', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          role: 'plant_manager',
          area_order: DEFAULT_AREA_ORDER,
          detail_level: 'summary',
          voice_enabled: true,
          onboarding_complete: false,
        }),
      }).catch(() => {
        // Ignore errors on dismiss
      })
    }

    onDismiss?.()
  }, [onDismiss])

  // Step progress indicator
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

  // Render current step content
  const renderStep = () => {
    switch (currentStep) {
      case 'welcome':
        return (
          <WelcomeStep onContinue={handleNext} />
        )

      case 'role':
        return (
          <RoleStep
            selectedRole={data.role}
            onSelect={handleRoleSelect}
            onBack={handleBack}
            onContinue={handleNext}
          />
        )

      case 'supervisor_assets':
        return (
          <SupervisorAssetsStep
            userId={userId}
            onBack={handleBack}
            onContinue={handleNext}
          />
        )

      case 'preferences':
        return (
          <PreferencesStep
            value={{
              areaOrder: data.areaOrder,
              detailLevel: data.detailLevel,
              voiceEnabled: data.voiceEnabled,
            }}
            onChange={handlePreferencesChange}
            onBack={handleBack}
            onContinue={handleNext}
          />
        )

      case 'confirmation':
        return (
          <Card className="w-full max-w-lg mx-auto">
            <CardHeader className="text-center">
              <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
                <svg
                  className="w-8 h-8 text-primary"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
              <CardTitle className="text-2xl">You&apos;re All Set!</CardTitle>
              <CardDescription className="text-base mt-2">
                Your preferences have been configured
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Summary of selections */}
              <div className="bg-muted/50 rounded-lg p-4 space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Role</span>
                  <span className="font-medium capitalize">
                    {data.role?.replace('_', ' ')}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Detail Level</span>
                  <span className="font-medium capitalize">{data.detailLevel}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Voice Briefings</span>
                  <span className="font-medium">{data.voiceEnabled ? 'On' : 'Off'}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">First Area</span>
                  <span className="font-medium">{data.areaOrder[0] || DEFAULT_AREA_ORDER[0]}</span>
                </div>
              </div>

              {error && (
                <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-3 text-sm text-destructive">
                  {error}
                </div>
              )}

              <p className="text-sm text-muted-foreground text-center">
                You can update these anytime in Settings &gt; Preferences
              </p>

              <div className="flex gap-3">
                <Button
                  variant="outline"
                  onClick={handleBack}
                  className="flex-1 touch-target"
                  disabled={isSubmitting}
                >
                  Back
                </Button>
                <Button
                  onClick={handleComplete}
                  className="flex-1 touch-target"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? (
                    <>
                      <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin mr-2" />
                      Saving...
                    </>
                  ) : (
                    'Start Briefing'
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        )

      default:
        return null
    }
  }

  return (
    <div
      className={cn(
        'fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/95 backdrop-blur-sm',
        className
      )}
    >
      <div className="w-full max-w-2xl">
        {/* Header with dismiss button */}
        <div className="flex items-center justify-between mb-4">
          <div className="text-sm text-muted-foreground">
            Step {currentStepIndex + 1} of {totalSteps}
          </div>
          <button
            onClick={handleDismiss}
            className="p-2 rounded-full hover:bg-muted transition-colors"
            aria-label="Skip onboarding"
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

        {/* Progress indicator */}
        <ProgressIndicator />

        {/* Step content */}
        {renderStep()}
      </div>
    </div>
  )
}

export default OnboardingFlow
