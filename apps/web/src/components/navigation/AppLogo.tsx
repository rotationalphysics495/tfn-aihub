/**
 * AppLogo Component
 *
 * Reusable logo component for the application header.
 * Displays the bar chart icon and "Manufacturing Performance Assistant" text.
 */

import Link from 'next/link'

interface AppLogoProps {
  /** Show text beside logo on larger screens (default: true) */
  showText?: boolean
  /** Link destination (default: '/morning-report') */
  href?: string
  /** Additional CSS classes */
  className?: string
}

export function AppLogo({
  showText = true,
  href = '/morning-report',
  className = '',
}: AppLogoProps) {
  return (
    <Link href={href} className={`flex items-center gap-3 ${className}`}>
      <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
        <svg
          className="w-4 h-4 text-primary"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
          />
        </svg>
      </div>
      {showText && (
        <span className="font-semibold text-foreground">
          Manufacturing Performance Assistant
        </span>
      )}
    </Link>
  )
}
