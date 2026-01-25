'use client'

/**
 * UserMenu Component
 *
 * Displays user email and logout button in the application header.
 * Client component that handles logout via Supabase.
 */

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'

interface UserMenuProps {
  /** User's email address */
  email: string
  /** Hide email on mobile screens (default: true) */
  hideEmailOnMobile?: boolean
  /** Additional CSS classes */
  className?: string
}

export function UserMenu({
  email,
  hideEmailOnMobile = true,
  className = '',
}: UserMenuProps) {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(false)

  const handleLogout = async () => {
    setIsLoading(true)
    const supabase = createClient()

    await supabase.auth.signOut()

    router.push('/login')
    router.refresh()
  }

  return (
    <div className={`flex items-center gap-4 ${className}`}>
      <span
        className={`text-sm text-muted-foreground ${
          hideEmailOnMobile ? 'hidden sm:inline' : ''
        }`}
      >
        {email}
      </span>
      <button
        onClick={handleLogout}
        disabled={isLoading}
        className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-muted-foreground hover:text-foreground bg-secondary hover:bg-secondary/80 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? (
          <>
            <svg
              className="animate-spin -ml-0.5 mr-1.5 h-3.5 w-3.5"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            Signing out...
          </>
        ) : (
          <>
            <svg
              className="w-4 h-4 mr-1.5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
              />
            </svg>
            Sign Out
          </>
        )}
      </button>
    </div>
  )
}
