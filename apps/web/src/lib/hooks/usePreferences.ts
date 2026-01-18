'use client'

/**
 * usePreferences Hook (Story 8.8)
 *
 * AC#3: Load and save user preferences
 * AC#5: Settings page preference management
 *
 * This hook provides:
 * - loadPreferences(): Fetch current user preferences
 * - savePreferences(): Create or update preferences
 * - Loading/error state handling
 *
 * References:
 * - [Source: architecture/voice-briefing.md#User Preferences Architecture]
 * - [Source: prd-voice-briefing-context.md#Feature 3: User Preferences System]
 */

import { useState, useCallback, useRef, useEffect } from 'react'
import { createClient } from '@/lib/supabase/client'

export interface UserPreferences {
  userId: string
  role: 'plant_manager' | 'supervisor'
  areaOrder: string[]
  detailLevel: 'summary' | 'detailed'
  voiceEnabled: boolean
  onboardingComplete: boolean
  updatedAt: string
  // EOD Reminder preferences (Story 9.12)
  eodReminderEnabled: boolean
  eodReminderTime: string
  userTimezone: string
}

interface UsePreferencesState {
  preferences: UserPreferences | null
  isLoading: boolean
  isSaving: boolean
  error: string | null
  lastUpdated: Date | null
}

interface UsePreferencesReturn extends UsePreferencesState {
  /** Load current user preferences from API */
  loadPreferences: () => Promise<UserPreferences | null>
  /** Save preferences (create or update) */
  savePreferences: (prefs: Partial<UserPreferences>) => Promise<boolean>
  /** Clear any error state */
  clearError: () => void
}

interface UsePreferencesOptions {
  /** Auto-fetch preferences on mount */
  autoFetch?: boolean
}

const ERROR_MESSAGES = {
  AUTH_ERROR: 'Your session has expired. Please log in again.',
  NETWORK_ERROR: 'Unable to connect to the server. Please check your connection.',
  NOT_FOUND: 'No preferences found. Please complete onboarding.',
  SAVE_ERROR: 'Failed to save preferences. Please try again.',
  LOAD_ERROR: 'Failed to load preferences. Please try again.',
}

export function usePreferences(
  options: UsePreferencesOptions = {}
): UsePreferencesReturn {
  const { autoFetch = true } = options

  const [state, setState] = useState<UsePreferencesState>({
    preferences: null,
    isLoading: false,
    isSaving: false,
    error: null,
    lastUpdated: null,
  })

  const mountedRef = useRef(true)

  const loadPreferences = useCallback(async (): Promise<UserPreferences | null> => {
    if (!mountedRef.current) return null

    setState(prev => ({ ...prev, isLoading: true, error: null }))

    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.access_token) {
        throw new Error(ERROR_MESSAGES.AUTH_ERROR)
      }

      const response = await fetch('/api/v1/preferences', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      })

      if (response.status === 404) {
        // No preferences found - user needs onboarding
        if (mountedRef.current) {
          setState(prev => ({
            ...prev,
            preferences: null,
            isLoading: false,
            error: null,
          }))
        }
        return null
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || ERROR_MESSAGES.LOAD_ERROR)
      }

      const data = await response.json()

      const preferences: UserPreferences = {
        userId: data.user_id,
        role: data.role,
        areaOrder: data.area_order || [],
        detailLevel: data.detail_level,
        voiceEnabled: data.voice_enabled,
        onboardingComplete: data.onboarding_complete,
        updatedAt: data.updated_at,
        // EOD Reminder preferences (Story 9.12)
        eodReminderEnabled: data.eod_reminder_enabled ?? false,
        eodReminderTime: data.eod_reminder_time ?? '17:00',
        userTimezone: data.user_timezone ?? Intl.DateTimeFormat().resolvedOptions().timeZone,
      }

      if (mountedRef.current) {
        setState(prev => ({
          ...prev,
          preferences,
          isLoading: false,
          error: null,
          lastUpdated: new Date(),
        }))
      }

      return preferences
    } catch (err) {
      console.error('Error loading preferences:', err)

      if (mountedRef.current) {
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: err instanceof Error ? err.message : ERROR_MESSAGES.LOAD_ERROR,
        }))
      }

      return null
    }
  }, [])

  const savePreferences = useCallback(async (
    prefs: Partial<UserPreferences>
  ): Promise<boolean> => {
    if (!mountedRef.current) return false

    setState(prev => ({ ...prev, isSaving: true, error: null }))

    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.access_token) {
        throw new Error(ERROR_MESSAGES.AUTH_ERROR)
      }

      // Determine if we're creating or updating
      const method = state.preferences ? 'PUT' : 'POST'

      // Map from camelCase to snake_case for API
      const requestBody: Record<string, unknown> = {}
      if (prefs.role !== undefined) requestBody.role = prefs.role
      if (prefs.areaOrder !== undefined) requestBody.area_order = prefs.areaOrder
      if (prefs.detailLevel !== undefined) requestBody.detail_level = prefs.detailLevel
      if (prefs.voiceEnabled !== undefined) requestBody.voice_enabled = prefs.voiceEnabled
      if (prefs.onboardingComplete !== undefined) requestBody.onboarding_complete = prefs.onboardingComplete
      // EOD Reminder preferences (Story 9.12)
      if (prefs.eodReminderEnabled !== undefined) requestBody.eod_reminder_enabled = prefs.eodReminderEnabled
      if (prefs.eodReminderTime !== undefined) requestBody.eod_reminder_time = prefs.eodReminderTime
      if (prefs.userTimezone !== undefined) requestBody.user_timezone = prefs.userTimezone

      const response = await fetch('/api/v1/preferences', {
        method,
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || ERROR_MESSAGES.SAVE_ERROR)
      }

      const data = await response.json()

      const updatedPreferences: UserPreferences = {
        userId: data.user_id,
        role: data.role,
        areaOrder: data.area_order || [],
        detailLevel: data.detail_level,
        voiceEnabled: data.voice_enabled,
        onboardingComplete: data.onboarding_complete,
        updatedAt: data.updated_at,
        // EOD Reminder preferences (Story 9.12)
        eodReminderEnabled: data.eod_reminder_enabled ?? false,
        eodReminderTime: data.eod_reminder_time ?? '17:00',
        userTimezone: data.user_timezone ?? Intl.DateTimeFormat().resolvedOptions().timeZone,
      }

      if (mountedRef.current) {
        setState(prev => ({
          ...prev,
          preferences: updatedPreferences,
          isSaving: false,
          error: null,
          lastUpdated: new Date(),
        }))
      }

      return true
    } catch (err) {
      console.error('Error saving preferences:', err)

      if (mountedRef.current) {
        setState(prev => ({
          ...prev,
          isSaving: false,
          error: err instanceof Error ? err.message : ERROR_MESSAGES.SAVE_ERROR,
        }))
      }

      return false
    }
  }, [state.preferences])

  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }))
  }, [])

  // Auto-fetch on mount
  useEffect(() => {
    mountedRef.current = true

    if (autoFetch) {
      loadPreferences()
    }

    return () => {
      mountedRef.current = false
    }
  }, [autoFetch, loadPreferences])

  return {
    ...state,
    loadPreferences,
    savePreferences,
    clearError,
  }
}

export default usePreferences
