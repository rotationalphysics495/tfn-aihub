'use client'

/**
 * VoiceToggle Component (Story 8.8)
 *
 * AC#2 - Step 6: Voice preference (On/Off)
 * - Implement On/Off toggle for voice delivery
 * - Show description of voice feature
 * - Default to "On"
 *
 * References:
 * - [Source: architecture/voice-briefing.md#User Preferences Architecture]
 * - [Source: prd-voice-briefing-context.md#Feature 3: User Preferences System]
 */

import { cn } from '@/lib/utils'

interface VoiceToggleProps {
  /** Whether voice is enabled */
  value: boolean
  /** Called when voice setting changes */
  onChange: (enabled: boolean) => void
  /** Optional CSS class name */
  className?: string
}

export function VoiceToggle({
  value,
  onChange,
  className,
}: VoiceToggleProps) {
  return (
    <div className={cn('space-y-4', className)}>
      <div className="text-sm text-muted-foreground">
        Enable voice delivery to hear your briefings read aloud.
      </div>

      <div className="flex items-center justify-between p-4 rounded-lg border bg-card">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
            {value ? (
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
            ) : (
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
                  d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"
                  clipRule="evenodd"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2"
                />
              </svg>
            )}
          </div>
          <div>
            <p className="font-medium">Voice Briefings</p>
            <p className="text-sm text-muted-foreground">
              {value ? 'Briefings will be read aloud' : 'Text-only briefings'}
            </p>
          </div>
        </div>

        {/* Toggle switch */}
        <button
          type="button"
          role="switch"
          aria-checked={value}
          onClick={() => onChange(!value)}
          className={cn(
            'relative inline-flex h-7 w-12 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent',
            'transition-colors duration-200 ease-in-out',
            'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
            'touch-target',
            value ? 'bg-primary' : 'bg-muted'
          )}
        >
          <span className="sr-only">Enable voice briefings</span>
          <span
            aria-hidden="true"
            className={cn(
              'pointer-events-none inline-block h-6 w-6 transform rounded-full bg-background shadow ring-0',
              'transition duration-200 ease-in-out',
              value ? 'translate-x-5' : 'translate-x-0'
            )}
          />
        </button>
      </div>

      <div className="bg-muted/50 rounded-lg p-3 text-sm text-muted-foreground">
        <p className="flex items-center gap-2">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          You can always pause and ask follow-up questions during voice briefings.
        </p>
      </div>
    </div>
  )
}

export default VoiceToggle
