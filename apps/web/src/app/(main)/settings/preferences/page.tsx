'use client'

/**
 * Settings > Preferences Page (Story 8.8, 9.12)
 *
 * AC#5: All onboarding options available to edit
 * - Reuse all preference components (AreaOrderSelector, etc.)
 * - Load current preferences on mount
 * - Save on submit with feedback message
 *
 * Story 9.12 additions:
 * - EOD Reminder toggle and time picker
 * - Push notification permission handling
 *
 * References:
 * - [Source: architecture/voice-briefing.md#User Preferences Architecture]
 * - [Source: prd-voice-briefing-context.md#Feature 3: User Preferences System]
 */

import { useState, useCallback, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { AreaOrderSelector, DEFAULT_AREA_ORDER } from '@/components/preferences/AreaOrderSelector'
import { DetailLevelToggle, type DetailLevel } from '@/components/preferences/DetailLevelToggle'
import { VoiceToggle } from '@/components/preferences/VoiceToggle'
import { EODReminderSettings } from '@/components/preferences/EODReminderSettings'
import { usePreferences, type UserPreferences } from '@/lib/hooks/usePreferences'

// VAPID public key for push notifications (from environment)
const VAPID_PUBLIC_KEY = process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY || ''

export default function PreferencesPage() {
  const {
    preferences,
    isLoading,
    isSaving,
    error,
    loadPreferences,
    savePreferences,
    clearError,
  } = usePreferences({ autoFetch: true })

  // Local state for editing
  const [localPrefs, setLocalPrefs] = useState<{
    role: 'plant_manager' | 'supervisor'
    areaOrder: string[]
    detailLevel: DetailLevel
    voiceEnabled: boolean
    // EOD Reminder preferences (Story 9.12)
    eodReminderEnabled: boolean
    eodReminderTime: string
  }>({
    role: 'plant_manager',
    areaOrder: DEFAULT_AREA_ORDER,
    detailLevel: 'summary',
    voiceEnabled: true,
    eodReminderEnabled: false,
    eodReminderTime: '17:00',
  })

  const [hasChanges, setHasChanges] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)

  // Update local state when preferences load
  useEffect(() => {
    if (preferences) {
      setLocalPrefs({
        role: preferences.role,
        areaOrder: preferences.areaOrder.length > 0 ? preferences.areaOrder : DEFAULT_AREA_ORDER,
        detailLevel: preferences.detailLevel,
        voiceEnabled: preferences.voiceEnabled,
        // EOD Reminder preferences (Story 9.12)
        eodReminderEnabled: preferences.eodReminderEnabled,
        eodReminderTime: preferences.eodReminderTime,
      })
    }
  }, [preferences])

  // Track changes
  useEffect(() => {
    if (!preferences) {
      setHasChanges(false)
      return
    }

    const changed =
      localPrefs.role !== preferences.role ||
      JSON.stringify(localPrefs.areaOrder) !== JSON.stringify(preferences.areaOrder) ||
      localPrefs.detailLevel !== preferences.detailLevel ||
      localPrefs.voiceEnabled !== preferences.voiceEnabled ||
      // EOD Reminder changes (Story 9.12)
      localPrefs.eodReminderEnabled !== preferences.eodReminderEnabled ||
      localPrefs.eodReminderTime !== preferences.eodReminderTime

    setHasChanges(changed)
    if (changed) {
      setSaveSuccess(false)
    }
  }, [localPrefs, preferences])

  const handleAreaOrderChange = useCallback((newOrder: string[]) => {
    setLocalPrefs(prev => ({ ...prev, areaOrder: newOrder }))
  }, [])

  const handleDetailLevelChange = useCallback((level: DetailLevel) => {
    setLocalPrefs(prev => ({ ...prev, detailLevel: level }))
  }, [])

  const handleVoiceChange = useCallback((enabled: boolean) => {
    setLocalPrefs(prev => ({ ...prev, voiceEnabled: enabled }))
  }, [])

  const handleRoleChange = useCallback((role: 'plant_manager' | 'supervisor') => {
    setLocalPrefs(prev => ({ ...prev, role }))
  }, [])

  // EOD Reminder handlers (Story 9.12)
  const handleEodReminderEnabledChange = useCallback((enabled: boolean) => {
    setLocalPrefs(prev => ({ ...prev, eodReminderEnabled: enabled }))
  }, [])

  const handleEodReminderTimeChange = useCallback((time: string) => {
    setLocalPrefs(prev => ({ ...prev, eodReminderTime: time }))
  }, [])

  const handleSave = useCallback(async () => {
    setSaveSuccess(false)
    clearError()

    const success = await savePreferences({
      role: localPrefs.role,
      areaOrder: localPrefs.areaOrder,
      detailLevel: localPrefs.detailLevel,
      voiceEnabled: localPrefs.voiceEnabled,
      // EOD Reminder preferences (Story 9.12)
      eodReminderEnabled: localPrefs.eodReminderEnabled,
      eodReminderTime: localPrefs.eodReminderTime,
      userTimezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    })

    if (success) {
      setSaveSuccess(true)
      setHasChanges(false)
      // Clear success message after 3 seconds
      setTimeout(() => setSaveSuccess(false), 3000)
    }
  }, [localPrefs, savePreferences, clearError])

  const handleReset = useCallback(() => {
    if (preferences) {
      setLocalPrefs({
        role: preferences.role,
        areaOrder: preferences.areaOrder.length > 0 ? preferences.areaOrder : DEFAULT_AREA_ORDER,
        detailLevel: preferences.detailLevel,
        voiceEnabled: preferences.voiceEnabled,
        // EOD Reminder preferences (Story 9.12)
        eodReminderEnabled: preferences.eodReminderEnabled,
        eodReminderTime: preferences.eodReminderTime,
      })
    }
    clearError()
    setSaveSuccess(false)
  }, [preferences, clearError])

  if (isLoading) {
    return (
      <div className="container max-w-3xl py-8">
        <div className="flex flex-col items-center justify-center py-12">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mb-3" />
          <p className="text-sm text-muted-foreground">Loading preferences...</p>
        </div>
      </div>
    )
  }

  if (!preferences && !isLoading) {
    return (
      <div className="container max-w-3xl py-8">
        <Card>
          <CardContent className="py-12">
            <div className="flex flex-col items-center text-center">
              <svg
                className="w-12 h-12 text-muted-foreground/50 mb-4"
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
              <h3 className="font-semibold text-lg mb-2">No Preferences Found</h3>
              <p className="text-muted-foreground mb-4">
                Please complete the onboarding process to set up your preferences.
              </p>
              <Button onClick={() => window.location.href = '/dashboard'}>
                Go to Dashboard
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container max-w-3xl py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold">Preferences</h1>
        <p className="text-muted-foreground">
          Customize how you receive your morning briefings
        </p>
      </div>

      {/* Success message */}
      {saveSuccess && (
        <div className="mb-6 p-4 bg-primary/10 border border-primary/20 rounded-lg flex items-center gap-3 text-primary">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 13l4 4L19 7"
            />
          </svg>
          <span>Your preferences have been saved successfully.</span>
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="mb-6 p-4 bg-destructive/10 border border-destructive/20 rounded-lg flex items-center gap-3 text-destructive">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
          <span>{error}</span>
        </div>
      )}

      <div className="space-y-6">
        {/* Role Section */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <svg
                className="w-5 h-5 text-primary"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                />
              </svg>
              Your Role
            </CardTitle>
            <CardDescription>
              This affects the scope of your briefings
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 sm:grid-cols-2">
              {(['plant_manager', 'supervisor'] as const).map((role) => {
                const isSelected = localPrefs.role === role
                const title = role === 'plant_manager' ? 'Plant Manager' : 'Supervisor'
                const description =
                  role === 'plant_manager'
                    ? 'Full visibility across the entire plant'
                    : 'Focused view on your assigned assets'

                return (
                  <button
                    key={role}
                    type="button"
                    onClick={() => handleRoleChange(role)}
                    className={`flex items-center gap-3 p-4 rounded-lg border-2 text-left transition-all
                      hover:border-primary/50 hover:bg-accent/50
                      focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2
                      ${isSelected ? 'border-primary bg-primary/5' : 'border-border bg-card'}`}
                    aria-pressed={isSelected}
                  >
                    <div
                      className={`w-5 h-5 rounded-full border-2 flex items-center justify-center
                        ${isSelected ? 'border-primary bg-primary' : 'border-muted-foreground'}`}
                    >
                      {isSelected && (
                        <div className="w-2 h-2 rounded-full bg-primary-foreground" />
                      )}
                    </div>
                    <div>
                      <p className="font-medium">{title}</p>
                      <p className="text-sm text-muted-foreground">{description}</p>
                    </div>
                  </button>
                )
              })}
            </div>
          </CardContent>
        </Card>

        {/* Area Order Section */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <svg
                className="w-5 h-5 text-primary"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 10h16M4 14h16M4 18h16"
                />
              </svg>
              Area Order
            </CardTitle>
            <CardDescription>
              Set the order in which areas appear in your briefings
            </CardDescription>
          </CardHeader>
          <CardContent>
            <AreaOrderSelector
              value={localPrefs.areaOrder}
              onChange={handleAreaOrderChange}
              compact
            />
          </CardContent>
        </Card>

        {/* Detail Level Section */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <svg
                className="w-5 h-5 text-primary"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              Detail Level
            </CardTitle>
            <CardDescription>
              Choose how much information to include in briefings
            </CardDescription>
          </CardHeader>
          <CardContent>
            <DetailLevelToggle
              value={localPrefs.detailLevel}
              onChange={handleDetailLevelChange}
            />
          </CardContent>
        </Card>

        {/* Voice Section */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <svg
                className="w-5 h-5 text-primary"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"
                />
              </svg>
              Voice Delivery
            </CardTitle>
            <CardDescription>
              Enable or disable voice reading of briefings
            </CardDescription>
          </CardHeader>
          <CardContent>
            <VoiceToggle
              value={localPrefs.voiceEnabled}
              onChange={handleVoiceChange}
            />
          </CardContent>
        </Card>

        {/* EOD Reminder Section (Story 9.12) */}
        {localPrefs.role === 'plant_manager' && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <svg
                  className="w-5 h-5 text-primary"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                  />
                </svg>
                EOD Summary Reminders
              </CardTitle>
              <CardDescription>
                Get reminded to review your End of Day summary
              </CardDescription>
            </CardHeader>
            <CardContent>
              <EODReminderSettings
                enabled={localPrefs.eodReminderEnabled}
                reminderTime={localPrefs.eodReminderTime}
                onEnabledChange={handleEodReminderEnabledChange}
                onTimeChange={handleEodReminderTimeChange}
                vapidPublicKey={VAPID_PUBLIC_KEY}
              />
            </CardContent>
          </Card>
        )}

        {/* Action buttons */}
        <div className="flex gap-3 justify-end pt-4">
          <Button
            variant="outline"
            onClick={handleReset}
            disabled={!hasChanges || isSaving}
          >
            Reset Changes
          </Button>
          <Button
            onClick={handleSave}
            disabled={!hasChanges || isSaving}
          >
            {isSaving ? (
              <>
                <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin mr-2" />
                Saving...
              </>
            ) : (
              'Save Preferences'
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}
