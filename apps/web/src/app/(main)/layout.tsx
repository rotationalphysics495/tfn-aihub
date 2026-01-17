/**
 * Main Layout (Story 8.8)
 *
 * Layout for authenticated main application routes.
 * Includes OnboardingGate to trigger first-time user onboarding.
 *
 * AC#1: Onboarding triggers on first interaction
 *
 * References:
 * - [Source: architecture/voice-briefing.md#User Preferences Architecture]
 */

import { OnboardingGate } from '@/components/onboarding/OnboardingGate'

export default function MainLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <OnboardingGate>
      {children}
    </OnboardingGate>
  )
}
