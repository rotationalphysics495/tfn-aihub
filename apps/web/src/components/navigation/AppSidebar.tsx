'use client'

/**
 * AppSidebar Component
 *
 * Collapsible sidebar navigation for the main application.
 * Provides persistent access to all app sections.
 */

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard,
  ClipboardList,
  Mic,
  ArrowLeftRight,
  Settings,
  ChevronLeft,
  ChevronRight,
  Shield,
  Users,
  FileText,
  UserCog,
  Sun,
  Moon,
} from 'lucide-react'

interface NavItem {
  href: string
  label: string
  icon: React.ReactNode
  badge?: string
}

interface NavGroup {
  label: string
  items: NavItem[]
}

const navGroups: NavGroup[] = [
  {
    label: 'Main',
    items: [
      { href: '/morning-report', label: 'Morning Report', icon: <ClipboardList className="w-5 h-5" /> },
      { href: '/dashboard', label: 'Live Pulse', icon: <LayoutDashboard className="w-5 h-5" /> },
    ],
  },
  {
    label: 'Production',
    items: [
      { href: '/dashboard/production/oee', label: 'OEE', icon: <FileText className="w-5 h-5" /> },
      { href: '/dashboard/production/downtime', label: 'Downtime', icon: <FileText className="w-5 h-5" /> },
      { href: '/dashboard/production/throughput', label: 'Throughput', icon: <FileText className="w-5 h-5" /> },
    ],
  },
  {
    label: 'Operations',
    items: [
      { href: '/briefing', label: 'Briefings', icon: <Mic className="w-5 h-5" /> },
      { href: '/handoff', label: 'Shift Handoffs', icon: <ArrowLeftRight className="w-5 h-5" /> },
    ],
  },
  {
    label: 'Settings',
    items: [
      { href: '/settings/preferences', label: 'Preferences', icon: <Settings className="w-5 h-5" /> },
    ],
  },
  {
    label: 'Admin',
    items: [
      { href: '/admin/assignments', label: 'Assignments', icon: <UserCog className="w-5 h-5" /> },
      { href: '/admin/users', label: 'Users', icon: <Users className="w-5 h-5" /> },
      { href: '/admin/audit', label: 'Audit Log', icon: <Shield className="w-5 h-5" /> },
    ],
  },
]

interface AppSidebarProps {
  className?: string
}

export function AppSidebar({ className = '' }: AppSidebarProps) {
  const pathname = usePathname()
  const [isCollapsed, setIsCollapsed] = useState(false)

  const isActive = (href: string) => {
    if (href === '/dashboard' && pathname === '/dashboard') return true
    if (href === '/morning-report' && pathname === '/morning-report') return true
    if (href !== '/dashboard' && href !== '/morning-report' && pathname.startsWith(href)) return true
    return pathname === href
  }

  return (
    <aside
      className={`
        ${isCollapsed ? 'w-16' : 'w-64'}
        bg-card border-r border-border
        flex flex-col
        transition-all duration-300 ease-in-out
        ${className}
      `}
    >
      {/* Collapse Toggle */}
      <div className="flex justify-end p-2 border-b border-border">
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="p-2 rounded-md hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
          aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isCollapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <ChevronLeft className="w-4 h-4" />
          )}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4">
        {navGroups.map((group) => (
          <div key={group.label} className="mb-6">
            {/* Group Label */}
            {!isCollapsed && (
              <h3 className="px-4 mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                {group.label}
              </h3>
            )}

            {/* Group Items */}
            <ul className="space-y-1 px-2">
              {group.items.map((item) => {
                const active = isActive(item.href)
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className={`
                        flex items-center gap-3 px-3 py-2 rounded-lg
                        transition-colors
                        ${active
                          ? 'bg-primary/10 text-primary font-medium'
                          : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                        }
                        ${isCollapsed ? 'justify-center' : ''}
                      `}
                      title={isCollapsed ? item.label : undefined}
                    >
                      {item.icon}
                      {!isCollapsed && (
                        <span className="truncate">{item.label}</span>
                      )}
                      {!isCollapsed && item.badge && (
                        <span className="ml-auto text-xs bg-primary/20 text-primary px-2 py-0.5 rounded-full">
                          {item.badge}
                        </span>
                      )}
                    </Link>
                  </li>
                )
              })}
            </ul>
          </div>
        ))}
      </nav>

      {/* Footer */}
      {!isCollapsed && (
        <div className="p-4 border-t border-border">
          <p className="text-xs text-muted-foreground text-center">
            TFN AI Hub v0.1
          </p>
        </div>
      )}
    </aside>
  )
}
