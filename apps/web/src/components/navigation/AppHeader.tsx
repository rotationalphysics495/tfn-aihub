/**
 * AppHeader Component
 *
 * Unified header component for authenticated pages.
 * Composes AppLogo, ViewModeToggle, SafetyHeaderIndicator, and UserMenu.
 *
 * @see Story 3.3 - Action List Primary View (AC #7)
 */

import { AppLogo } from './AppLogo'
import { ViewModeToggle } from './ViewModeToggle'
import { UserMenu } from './UserMenu'
import { SafetyHeaderIndicator } from '@/components/dashboard'

interface AppHeaderProps {
  /** User object with email - required for UserMenu */
  user: { email: string }
  /** Show the ViewModeToggle for switching between dashboard/morning-report (default: true) */
  showViewModeToggle?: boolean
  /** Make header sticky (default: true) */
  sticky?: boolean
  /** Additional actions to render in the header (before safety indicator) */
  actions?: React.ReactNode
  /** Additional CSS classes */
  className?: string
}

export function AppHeader({
  user,
  showViewModeToggle = true,
  sticky = true,
  actions,
  className = '',
}: AppHeaderProps) {
  const stickyClasses = sticky ? 'sticky top-0 z-40' : ''

  return (
    <header
      className={`border-b border-border bg-card ${stickyClasses} ${className}`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo and title */}
          <AppLogo />

          {/* Navigation and user info */}
          <nav className="flex items-center gap-4" aria-label="Main navigation">
            {/* Custom actions slot */}
            {actions}

            {/* View mode toggle */}
            {showViewModeToggle && <ViewModeToggle />}

            {/* Safety Alert Indicator */}
            <SafetyHeaderIndicator />

            {/* User menu with email and logout */}
            <UserMenu email={user.email || ''} />
          </nav>
        </div>
      </div>
    </header>
  )
}
