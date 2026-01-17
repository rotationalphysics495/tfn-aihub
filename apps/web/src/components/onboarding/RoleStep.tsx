'use client'

/**
 * RoleStep Component (Story 8.8)
 *
 * Step 2 of the onboarding flow: Role selection.
 *
 * AC#2 - Step 2: Role selection (Plant Manager or Supervisor)
 * - Display role selection cards
 * - Show role descriptions and scope differences
 * - Update state on role selection
 *
 * References:
 * - [Source: architecture/voice-briefing.md#Role-Based Access Control]
 * - [Source: prd-voice-briefing-context.md#Feature 3: User Preferences System]
 */

import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export type UserRole = 'plant_manager' | 'supervisor'

interface RoleStepProps {
  /** Currently selected role */
  selectedRole: UserRole | null
  /** Called when role is selected */
  onSelect: (role: UserRole) => void
  /** Called when user clicks Back */
  onBack: () => void
  /** Called when user clicks Continue */
  onContinue: () => void
  /** Optional CSS class name */
  className?: string
}

const roles: Array<{
  id: UserRole
  title: string
  description: string
  scope: string
  icon: React.ReactNode
}> = [
  {
    id: 'plant_manager',
    title: 'Plant Manager',
    description: 'Full visibility across the entire plant',
    scope: 'See all 7 production areas in your briefings',
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
      </svg>
    ),
  },
  {
    id: 'supervisor',
    title: 'Supervisor',
    description: 'Focused view on your assigned assets',
    scope: 'Briefings filtered to your specific responsibilities',
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
      </svg>
    ),
  },
]

export function RoleStep({
  selectedRole,
  onSelect,
  onBack,
  onContinue,
  className,
}: RoleStepProps) {
  return (
    <Card className={cn('w-full max-w-2xl mx-auto', className)}>
      <CardHeader className="text-center">
        <CardTitle className="text-xl">What&apos;s your role?</CardTitle>
        <CardDescription>
          This helps us show you the right level of detail in your briefings
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid gap-4 sm:grid-cols-2">
          {roles.map((role) => {
            const isSelected = selectedRole === role.id
            return (
              <button
                key={role.id}
                onClick={() => onSelect(role.id)}
                className={cn(
                  'flex flex-col items-center p-6 rounded-lg border-2 transition-all',
                  'hover:border-primary/50 hover:bg-accent/50',
                  'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
                  'touch-target text-left',
                  isSelected
                    ? 'border-primary bg-primary/5'
                    : 'border-border bg-card'
                )}
                aria-pressed={isSelected}
              >
                <div
                  className={cn(
                    'w-16 h-16 rounded-full flex items-center justify-center mb-4',
                    isSelected ? 'bg-primary/20 text-primary' : 'bg-muted text-muted-foreground'
                  )}
                >
                  {role.icon}
                </div>
                <h3 className="font-semibold text-lg mb-1">{role.title}</h3>
                <p className="text-sm text-muted-foreground text-center mb-2">
                  {role.description}
                </p>
                <p className="text-xs text-muted-foreground/80 text-center">
                  {role.scope}
                </p>
                {isSelected && (
                  <div className="mt-3">
                    <svg
                      className="w-6 h-6 text-primary"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                  </div>
                )}
              </button>
            )
          })}
        </div>

        <div className="flex gap-3 pt-4">
          <Button variant="outline" onClick={onBack} className="flex-1 touch-target">
            Back
          </Button>
          <Button
            onClick={onContinue}
            disabled={!selectedRole}
            className="flex-1 touch-target"
          >
            Continue
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

export default RoleStep
