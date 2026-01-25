/**
 * Admin Settings Page
 *
 * Placeholder page for system-wide administrative settings.
 * Will include configuration for system defaults, integrations, and global settings.
 */

import { Settings } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'

export const metadata = {
  title: 'System Settings | Admin',
  description: 'Configure system-wide defaults and integrations',
}

export default function AdminSettingsPage() {
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-slate-900">System Settings</h1>
        <p className="text-slate-500 mt-1">
          Configure system-wide defaults and integrations
        </p>
      </header>

      <Card>
        <CardContent className="py-12 text-center">
          <Settings className="w-12 h-12 text-slate-400 mx-auto mb-4" />
          <h2 className="text-lg font-medium text-slate-900">Coming Soon</h2>
          <p className="text-slate-500 mt-1 max-w-md mx-auto">
            System settings will be available in a future release. This will include
            notification preferences, integration settings, and system-wide defaults.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
