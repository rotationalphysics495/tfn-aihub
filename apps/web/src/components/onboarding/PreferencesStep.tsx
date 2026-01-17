'use client'

/**
 * PreferencesStep Component (Story 8.8)
 *
 * AC#2 - Steps 4-6: Preferences composite component
 * - Compose AreaOrderSelector, DetailLevelToggle, VoiceToggle
 * - Manage local state for all preferences
 * - Add navigation (Back/Continue) buttons
 *
 * References:
 * - [Source: architecture/voice-briefing.md#User Preferences Architecture]
 * - [Source: prd-voice-briefing-context.md#Onboarding Flow Summary]
 */

import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { AreaOrderSelector, DEFAULT_AREA_ORDER } from '@/components/preferences/AreaOrderSelector'
import { DetailLevelToggle, type DetailLevel } from '@/components/preferences/DetailLevelToggle'
import { VoiceToggle } from '@/components/preferences/VoiceToggle'

export interface PreferencesData {
  areaOrder: string[]
  detailLevel: DetailLevel
  voiceEnabled: boolean
}

interface PreferencesStepProps {
  /** Current preferences */
  value: PreferencesData
  /** Called when preferences change */
  onChange: (preferences: PreferencesData) => void
  /** Called when user clicks Back */
  onBack: () => void
  /** Called when user clicks Continue */
  onContinue: () => void
  /** Optional CSS class name */
  className?: string
}

export function PreferencesStep({
  value,
  onChange,
  onBack,
  onContinue,
  className,
}: PreferencesStepProps) {
  const handleAreaOrderChange = (newOrder: string[]) => {
    onChange({ ...value, areaOrder: newOrder })
  }

  const handleDetailLevelChange = (level: DetailLevel) => {
    onChange({ ...value, detailLevel: level })
  }

  const handleVoiceEnabledChange = (enabled: boolean) => {
    onChange({ ...value, voiceEnabled: enabled })
  }

  return (
    <Card className={cn('w-full max-w-2xl mx-auto', className)}>
      <CardHeader className="text-center">
        <CardTitle className="text-xl">Customize Your Preferences</CardTitle>
        <CardDescription>
          Set up how you want to receive your morning briefings
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-8">
        {/* Area Order */}
        <div className="space-y-3">
          <h3 className="font-semibold flex items-center gap-2">
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
          </h3>
          <AreaOrderSelector
            value={value.areaOrder.length > 0 ? value.areaOrder : DEFAULT_AREA_ORDER}
            onChange={handleAreaOrderChange}
          />
        </div>

        {/* Detail Level */}
        <div className="space-y-3">
          <h3 className="font-semibold flex items-center gap-2">
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
          </h3>
          <DetailLevelToggle
            value={value.detailLevel}
            onChange={handleDetailLevelChange}
          />
        </div>

        {/* Voice Setting */}
        <div className="space-y-3">
          <h3 className="font-semibold flex items-center gap-2">
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
          </h3>
          <VoiceToggle
            value={value.voiceEnabled}
            onChange={handleVoiceEnabledChange}
          />
        </div>

        {/* Navigation */}
        <div className="flex gap-3 pt-4">
          <Button variant="outline" onClick={onBack} className="flex-1 touch-target">
            Back
          </Button>
          <Button onClick={onContinue} className="flex-1 touch-target">
            Continue
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

export default PreferencesStep
