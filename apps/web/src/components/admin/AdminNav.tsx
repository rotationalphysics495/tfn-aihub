/**
 * Admin Navigation Component (Story 9.13, Task 5.2)
 *
 * Sidebar navigation for admin route group.
 * AC#1: Navigation component for admin pages.
 *
 * References:
 * - [Source: architecture/voice-briefing.md#Admin UI Architecture]
 */
'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { Users, Settings, ClipboardList, Shield, ArrowLeft } from 'lucide-react'

interface NavItem {
  href: string
  label: string
  icon: React.ReactNode
}

const navItems: NavItem[] = [
  {
    href: '/admin/assignments',
    label: 'Asset Assignments',
    icon: <ClipboardList className="h-5 w-5" />,
  },
  {
    href: '/admin/roles',
    label: 'Role Management',
    icon: <Users className="h-5 w-5" />,
  },
  {
    href: '/admin/audit',
    label: 'Audit Log',
    icon: <Shield className="h-5 w-5" />,
  },
  {
    href: '/admin/settings',
    label: 'Settings',
    icon: <Settings className="h-5 w-5" />,
  },
]

export function AdminNav() {
  const pathname = usePathname()

  return (
    <nav className="w-64 bg-slate-900 text-white min-h-screen p-4 flex flex-col">
      {/* Header */}
      <div className="mb-8">
        <Link
          href="/morning-report"
          className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors mb-4"
        >
          <ArrowLeft className="h-4 w-4" />
          <span className="text-sm">Back to App</span>
        </Link>
        <h1 className="text-xl font-semibold">Admin Panel</h1>
        <p className="text-slate-400 text-sm mt-1">Manage users and assets</p>
      </div>

      {/* Navigation Items */}
      <ul className="space-y-1 flex-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href
          return (
            <li key={item.href}>
              <Link
                href={item.href}
                className={cn(
                  'flex items-center gap-3 px-3 py-2 rounded-lg transition-colors',
                  isActive
                    ? 'bg-slate-800 text-white'
                    : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                )}
              >
                {item.icon}
                <span>{item.label}</span>
              </Link>
            </li>
          )
        })}
      </ul>

      {/* Footer */}
      <div className="mt-auto pt-4 border-t border-slate-800">
        <p className="text-xs text-slate-500">
          Admin actions are logged for audit purposes.
        </p>
      </div>
    </nav>
  )
}
