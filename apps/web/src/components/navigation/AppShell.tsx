/**
 * AppShell Component
 *
 * Main layout wrapper that combines AppHeader and AppSidebar.
 * Used by the (main) layout for consistent navigation across all authenticated pages.
 */

import { AppHeader } from './AppHeader'
import { AppSidebar } from './AppSidebar'

interface AppShellProps {
  /** User object with email */
  user: { email: string }
  /** Child content to render in the main area */
  children: React.ReactNode
}

export function AppShell({ user, children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header - Full width at top */}
      <AppHeader user={user} showViewModeToggle />

      {/* Main container with sidebar and content */}
      <div className="flex flex-1">
        {/* Sidebar - Fixed on left */}
        <AppSidebar className="hidden md:flex shrink-0" />

        {/* Main content area */}
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  )
}
