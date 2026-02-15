'use client'

/**
 * OnboardingGate Component (Story 8.8)
 *
 * AC#1: Trigger onboarding for first-time users
 * AC#4: Handle abandonment and re-trigger
 *
 * This component wraps authenticated pages and:
 * - Checks if user needs onboarding
 * - Shows OnboardingFlow as full-screen overlay when required
 * - Blocks navigation until onboarding completes or is dismissed
 *
 * References:
 * - [Source: architecture/voice-briefing.md#User Preferences Architecture]
 * - [Source: prd-voice-briefing-context.md#Onboarding Flow Summary]
 */

import { useCallback, useState } from 'react'
import { useOnboardingRequired } from '@/lib/hooks/useOnboardingRequired'
import { OnboardingFlow } from '@/components/preferences/OnboardingFlow'

interface OnboardingGateProps {
  /** Child components to render */
  children: React.ReactNode
}

export function OnboardingGate({ children }: OnboardingGateProps) {
  const { isRequired, isLoading, originalDestination, userId, recheck } = useOnboardingRequired()
  const [dismissed, setDismissed] = useState(false)

  const handleComplete = useCallback(() => {
    // Recheck status and reload to clear any stale state
    recheck().then(() => {
      // Force reload to ensure fresh state
      window.location.reload()
    })
  }, [recheck])

  const handleDismiss = useCallback(() => {
    // Let the user through for this session with default settings.
    // OnboardingFlow saves defaults with onboarding_complete=false,
    // so onboarding will re-trigger on next login/page load.
    setDismissed(true)
  }, [])

  // Show loading state while checking
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  // Show onboarding flow if required (unless dismissed this session)
  if (isRequired && userId && !dismissed) {
    return (
      <>
        {/* Render children in background (dimmed) */}
        <div className="opacity-20 pointer-events-none blur-sm">
          {children}
        </div>
        {/* Overlay onboarding flow */}
        <OnboardingFlow
          userId={userId}
          originalDestination={originalDestination}
          onComplete={handleComplete}
          onDismiss={handleDismiss}
        />
      </>
    )
  }

  // Onboarding complete - render children normally
  return <>{children}</>
}

export default OnboardingGate
