/**
 * Admin Layout (Story 9.13, Task 5.1)
 *
 * Layout for admin route group with sidebar navigation.
 * AC#1: Admin UI uses separate route group (/admin/*).
 *
 * References:
 * - [Source: architecture/voice-briefing.md#Admin UI Architecture]
 */

import { AdminNav } from '@/components/admin/AdminNav'

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex min-h-screen bg-slate-50">
      {/* Admin Sidebar Navigation */}
      <AdminNav />

      {/* Main Content Area */}
      <main className="flex-1 p-8">
        {children}
      </main>
    </div>
  )
}
