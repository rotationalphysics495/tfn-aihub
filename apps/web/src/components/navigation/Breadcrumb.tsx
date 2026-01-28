'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { ChevronRight, Home } from 'lucide-react'
import { cn } from '@/lib/utils'

/**
 * Breadcrumb Navigation Component
 *
 * Shows current location within the app hierarchy.
 *
 * @see Story 3.3 - Action List Primary View
 * @see AC #7 - Breadcrumb or clear indication of current view mode
 */

interface BreadcrumbItem {
  label: string
  href?: string
}

interface BreadcrumbProps {
  items?: BreadcrumbItem[]
  className?: string
}

// Default route labels
const routeLabels: Record<string, string> = {
  '/': 'Home',
  '/dashboard': 'Command Center',
  '/morning-report': 'Morning Report',
  '/live-pulse': 'Live Pulse',
}

export function Breadcrumb({ items, className }: BreadcrumbProps) {
  const pathname = usePathname()

  // Auto-generate breadcrumb items from pathname if not provided
  const breadcrumbItems: BreadcrumbItem[] = items || generateBreadcrumbs(pathname)

  if (breadcrumbItems.length === 0) {
    return null
  }

  return (
    <nav
      className={cn('flex items-center text-sm', className)}
      aria-label="Breadcrumb"
    >
      <ol className="flex items-center space-x-1">
        {/* Home link */}
        <li>
          <Link
            href="/dashboard"
            className="text-muted-foreground hover:text-foreground transition-colors touch-target inline-flex items-center"
            aria-label="Home"
          >
            <Home className="w-4 h-4" aria-hidden="true" />
          </Link>
        </li>

        {breadcrumbItems.map((item, index) => {
          const isLast = index === breadcrumbItems.length - 1

          return (
            <li key={index} className="flex items-center">
              <ChevronRight
                className="w-4 h-4 text-muted-foreground mx-1"
                aria-hidden="true"
              />
              {isLast || !item.href ? (
                <span
                  className={cn(
                    'font-medium',
                    isLast ? 'text-foreground' : 'text-muted-foreground'
                  )}
                  aria-current={isLast ? 'page' : undefined}
                >
                  {item.label}
                </span>
              ) : (
                <Link
                  href={item.href}
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  {item.label}
                </Link>
              )}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}

function generateBreadcrumbs(pathname: string): BreadcrumbItem[] {
  const segments = pathname.split('/').filter(Boolean)
  const items: BreadcrumbItem[] = []

  let currentPath = ''
  for (const segment of segments) {
    currentPath += `/${segment}`
    const label = routeLabels[currentPath] || formatSegment(segment)
    items.push({
      label,
      href: currentPath,
    })
  }

  return items
}

function formatSegment(segment: string): string {
  // Convert slug to title case
  return segment
    .split('-')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}
