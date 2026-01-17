'use client'

/**
 * WelcomeStep Component (Story 8.8)
 *
 * Step 1 of the onboarding flow: Welcome message and quick setup explanation.
 *
 * AC#2 - Step 1: Welcome + explain quick setup
 * - Display welcome message
 * - Explain the setup process
 * - Show estimated completion time (under 2 minutes)
 * - "Get Started" button to proceed
 *
 * References:
 * - [Source: architecture/voice-briefing.md#User Preferences Architecture]
 * - [Source: prd-voice-briefing-context.md#Onboarding Flow Summary]
 */

import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

interface WelcomeStepProps {
  /** Called when user clicks "Get Started" */
  onContinue: () => void
  /** Optional CSS class name */
  className?: string
}

export function WelcomeStep({ onContinue, className }: WelcomeStepProps) {
  return (
    <Card className={cn('w-full max-w-lg mx-auto', className)}>
      <CardHeader className="text-center">
        <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
          <svg
            className="w-8 h-8 text-primary"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"
            />
          </svg>
        </div>
        <CardTitle className="text-2xl">Welcome to TFN AI Hub</CardTitle>
        <CardDescription className="text-base mt-2">
          Let&apos;s personalize your briefing experience
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-4 text-center">
          <p className="text-muted-foreground">
            We&apos;ll ask a few quick questions to customize your morning briefings
            and make sure you see the information most relevant to your role.
          </p>

          <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span>Takes less than 2 minutes</span>
          </div>
        </div>

        <div className="space-y-3 bg-muted/50 rounded-lg p-4">
          <h3 className="font-medium text-sm">What we&apos;ll set up:</h3>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li className="flex items-center gap-2">
              <svg className="w-4 h-4 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Your role and assigned areas
            </li>
            <li className="flex items-center gap-2">
              <svg className="w-4 h-4 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Preferred area order for briefings
            </li>
            <li className="flex items-center gap-2">
              <svg className="w-4 h-4 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Detail level and voice preferences
            </li>
          </ul>
        </div>

        <Button
          size="lg"
          className="w-full touch-target"
          onClick={onContinue}
        >
          Get Started
        </Button>
      </CardContent>
    </Card>
  )
}

export default WelcomeStep
