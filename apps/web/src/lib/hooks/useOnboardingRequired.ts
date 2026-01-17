'use client'

/**
 * useOnboardingRequired Hook (Story 8.8)
 *
 * AC#1: Detect first-time users
 * AC#4: Return isRequired for triggering onboarding
 *
 * This hook checks if the current user needs to complete onboarding:
 * - Query user_preferences for current user
 * - Return isRequired: true if no record exists or onboarding_complete is false
 * - Return originalDestination for post-onboarding redirect
 *
 * References:
 * - [Source: architecture/voice-briefing.md#User Preferences Architecture]
 * - [Source: prd-voice-briefing-context.md#Onboarding Flow Summary]
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import { createClient } from '@/lib/supabase/client'

interface UseOnboardingRequiredReturn {
  /** Whether onboarding is required */
  isRequired: boolean
  /** Whether we're still checking */
  isLoading: boolean
  /** The original URL the user was trying to access */
  originalDestination: string | null
  /** Current user ID */
  userId: string | null
  /** Recheck onboarding status */
  recheck: () => Promise<void>
  /** Error message if check failed */
  error: string | null
}

interface UseOnboardingRequiredOptions {
  /** Skip onboarding check (useful for auth pages) */
  skip?: boolean
}

export function useOnboardingRequired(
  options: UseOnboardingRequiredOptions = {}
): UseOnboardingRequiredReturn {
  const { skip = false } = options

  const [state, setState] = useState<{
    isRequired: boolean
    isLoading: boolean
    originalDestination: string | null
    userId: string | null
    error: string | null
  }>({
    isRequired: false,
    isLoading: true,
    originalDestination: null,
    userId: null,
    error: null,
  })

  const mountedRef = useRef(true)

  const checkOnboarding = useCallback(async () => {
    if (skip) {
      setState(prev => ({
        ...prev,
        isRequired: false,
        isLoading: false,
      }))
      return
    }

    if (!mountedRef.current) return

    setState(prev => ({ ...prev, isLoading: true, error: null }))

    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.user) {
        // Not authenticated - don't require onboarding (let auth redirect handle it)
        if (mountedRef.current) {
          setState(prev => ({
            ...prev,
            isRequired: false,
            isLoading: false,
            userId: null,
          }))
        }
        return
      }

      const userId = session.user.id

      // Check if user has completed onboarding
      const { data, error: fetchError } = await supabase
        .from('user_preferences')
        .select('onboarding_complete')
        .eq('user_id', userId)
        .maybeSingle()

      if (fetchError) {
        // If table doesn't exist yet, treat as needing onboarding
        if (fetchError.code === '42P01') {
          if (mountedRef.current) {
            setState({
              isRequired: true,
              isLoading: false,
              originalDestination: typeof window !== 'undefined' ? window.location.pathname : null,
              userId,
              error: null,
            })
          }
          return
        }
        throw fetchError
      }

      if (mountedRef.current) {
        // No record or onboarding not complete = require onboarding
        const needsOnboarding = !data || !data.onboarding_complete

        setState({
          isRequired: needsOnboarding,
          isLoading: false,
          originalDestination: needsOnboarding && typeof window !== 'undefined'
            ? window.location.pathname
            : null,
          userId,
          error: null,
        })
      }
    } catch (err) {
      console.error('Error checking onboarding status:', err)
      if (mountedRef.current) {
        setState(prev => ({
          ...prev,
          isRequired: false, // Don't block on error
          isLoading: false,
          error: err instanceof Error ? err.message : 'Failed to check onboarding status',
        }))
      }
    }
  }, [skip])

  useEffect(() => {
    mountedRef.current = true
    checkOnboarding()

    return () => {
      mountedRef.current = false
    }
  }, [checkOnboarding])

  return {
    ...state,
    recheck: checkOnboarding,
  }
}

export default useOnboardingRequired
