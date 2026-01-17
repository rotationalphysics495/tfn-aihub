'use client'

/**
 * DetailLevelToggle Component (Story 8.8)
 *
 * AC#2 - Step 5: Detail level preference (Summary or Detailed)
 * - Implement toggle between "Summary" and "Detailed"
 * - Show description of each level
 * - Use existing toggle/switch UI pattern
 *
 * References:
 * - [Source: prd/prd-functional-requirements.md#FR37]
 * - [Source: architecture/voice-briefing.md#User Preferences Architecture]
 */

import { cn } from '@/lib/utils'

export type DetailLevel = 'summary' | 'detailed'

interface DetailLevelToggleProps {
  /** Current detail level */
  value: DetailLevel
  /** Called when level changes */
  onChange: (level: DetailLevel) => void
  /** Optional CSS class name */
  className?: string
}

const detailLevels: Array<{
  id: DetailLevel
  title: string
  description: string
  icon: React.ReactNode
}> = [
  {
    id: 'summary',
    title: 'Summary',
    description: 'Quick overview with key metrics and highlights. Great for a fast morning catch-up.',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M4 6h16M4 12h8m-8 6h16"
        />
      </svg>
    ),
  },
  {
    id: 'detailed',
    title: 'Detailed',
    description: 'In-depth analysis with full breakdowns, trends, and recommendations.',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
        />
      </svg>
    ),
  },
]

export function DetailLevelToggle({
  value,
  onChange,
  className,
}: DetailLevelToggleProps) {
  return (
    <div className={cn('space-y-3', className)}>
      <div className="text-sm text-muted-foreground">
        Choose how much detail you want in your briefings
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {detailLevels.map((level) => {
          const isSelected = value === level.id

          return (
            <button
              key={level.id}
              type="button"
              onClick={() => onChange(level.id)}
              className={cn(
                'flex flex-col p-4 rounded-lg border-2 text-left transition-all',
                'hover:border-primary/50 hover:bg-accent/50',
                'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
                'touch-target',
                isSelected
                  ? 'border-primary bg-primary/5'
                  : 'border-border bg-card'
              )}
              aria-pressed={isSelected}
            >
              <div className="flex items-center gap-3 mb-2">
                <div
                  className={cn(
                    'w-10 h-10 rounded-full flex items-center justify-center',
                    isSelected
                      ? 'bg-primary/20 text-primary'
                      : 'bg-muted text-muted-foreground'
                  )}
                >
                  {level.icon}
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold">{level.title}</span>
                  {isSelected && (
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
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  )}
                </div>
              </div>
              <p className="text-sm text-muted-foreground">
                {level.description}
              </p>
            </button>
          )
        })}
      </div>
    </div>
  )
}

export default DetailLevelToggle
