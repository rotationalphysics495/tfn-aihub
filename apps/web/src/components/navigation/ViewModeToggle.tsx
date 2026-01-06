'use client'

import { usePathname, useRouter } from 'next/navigation'
import { Calendar, Activity } from 'lucide-react'
import { cn } from '@/lib/utils'

/**
 * View Mode Toggle Component
 *
 * Navigation toggle between Morning Report (T-1) and Live Pulse (T-15m) views.
 *
 * @see Story 3.3 - Action List Primary View
 * @see AC #7 - Quick navigation to switch between views
 */

interface ViewModeToggleProps {
  className?: string
}

type ViewMode = 'morning-report' | 'live-pulse'

const viewModes: { id: ViewMode; label: string; href: string; icon: typeof Calendar; description: string }[] = [
  {
    id: 'morning-report',
    label: 'Morning Report',
    href: '/morning-report',
    icon: Calendar,
    description: "Yesterday's action items (T-1)",
  },
  {
    id: 'live-pulse',
    label: 'Live Pulse',
    href: '/dashboard',
    icon: Activity,
    description: 'Real-time monitoring (T-15m)',
  },
]

export function ViewModeToggle({ className }: ViewModeToggleProps) {
  const pathname = usePathname()
  const router = useRouter()

  // Determine current mode from pathname
  const currentMode: ViewMode = pathname.startsWith('/morning-report')
    ? 'morning-report'
    : 'live-pulse'

  return (
    <div
      className={cn(
        'inline-flex items-center rounded-lg bg-industrial-100 dark:bg-industrial-800 p-1',
        className
      )}
      role="tablist"
      aria-label="View mode"
    >
      {viewModes.map((mode) => {
        const isActive = mode.id === currentMode
        const Icon = mode.icon

        return (
          <button
            key={mode.id}
            role="tab"
            aria-selected={isActive}
            aria-controls={`${mode.id}-panel`}
            onClick={() => router.push(mode.href)}
            className={cn(
              'flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-all touch-target',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
              isActive
                ? mode.id === 'morning-report'
                  ? 'bg-retrospective-surface dark:bg-retrospective-surface-dark text-foreground shadow-sm'
                  : 'bg-live-surface dark:bg-live-surface-dark text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground hover:bg-industrial-200/50 dark:hover:bg-industrial-700/50'
            )}
          >
            <Icon
              className={cn(
                'w-4 h-4',
                isActive && mode.id === 'morning-report' && 'text-retrospective-primary',
                isActive && mode.id === 'live-pulse' && 'text-live-primary animate-live-pulse'
              )}
              aria-hidden="true"
            />
            <span className="hidden sm:inline">{mode.label}</span>
          </button>
        )
      })}
    </div>
  )
}

/**
 * Extended View Mode Toggle with descriptions
 */
interface ViewModeToggleExtendedProps {
  className?: string
}

export function ViewModeToggleExtended({ className }: ViewModeToggleExtendedProps) {
  const pathname = usePathname()
  const router = useRouter()

  const currentMode: ViewMode = pathname.startsWith('/morning-report')
    ? 'morning-report'
    : 'live-pulse'

  return (
    <div
      className={cn('flex flex-col sm:flex-row gap-2', className)}
      role="tablist"
      aria-label="View mode"
    >
      {viewModes.map((mode) => {
        const isActive = mode.id === currentMode
        const Icon = mode.icon

        return (
          <button
            key={mode.id}
            role="tab"
            aria-selected={isActive}
            onClick={() => router.push(mode.href)}
            className={cn(
              'flex items-center gap-3 px-4 py-3 rounded-lg text-left transition-all touch-target',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
              'border',
              isActive
                ? mode.id === 'morning-report'
                  ? 'bg-retrospective-surface dark:bg-retrospective-surface-dark border-retrospective-border dark:border-retrospective-border-dark'
                  : 'bg-live-surface dark:bg-live-surface-dark border-live-border dark:border-live-border-dark'
                : 'bg-card border-border hover:bg-industrial-50 dark:hover:bg-industrial-900'
            )}
          >
            <div
              className={cn(
                'w-10 h-10 rounded-full flex items-center justify-center',
                isActive && mode.id === 'morning-report' && 'bg-retrospective-primary/10',
                isActive && mode.id === 'live-pulse' && 'bg-live-primary/10',
                !isActive && 'bg-industrial-100 dark:bg-industrial-800'
              )}
            >
              <Icon
                className={cn(
                  'w-5 h-5',
                  isActive && mode.id === 'morning-report' && 'text-retrospective-primary',
                  isActive && mode.id === 'live-pulse' && 'text-live-primary animate-live-pulse',
                  !isActive && 'text-muted-foreground'
                )}
                aria-hidden="true"
              />
            </div>
            <div>
              <p className={cn('font-medium', isActive ? 'text-foreground' : 'text-muted-foreground')}>
                {mode.label}
              </p>
              <p className="text-xs text-muted-foreground">
                {mode.description}
              </p>
            </div>
          </button>
        )
      })}
    </div>
  )
}
