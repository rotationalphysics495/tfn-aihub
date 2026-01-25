/**
 * Main Layout (Story 8.8)
 *
 * Layout for authenticated main application routes.
 * Includes OnboardingGate to trigger first-time user onboarding.
 * Provides consistent navigation via AppShell (header + sidebar).
 *
 * AC#1: Onboarding triggers on first interaction
 *
 * References:
 * - [Source: architecture/voice-briefing.md#User Preferences Architecture]
 */

import { redirect } from 'next/navigation'
import { createClient } from '@/lib/supabase/server'
import { OnboardingGate } from '@/components/onboarding/OnboardingGate'
import { AppShell } from '@/components/navigation'

export default async function MainLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const supabase = await createClient()
  const { data: { user }, error } = await supabase.auth.getUser()

  if (error || !user) {
    redirect('/login')
  }

  return (
    <OnboardingGate>
      <AppShell user={{ email: user.email || '' }}>
        {children}
      </AppShell>
    </OnboardingGate>
  )
}
