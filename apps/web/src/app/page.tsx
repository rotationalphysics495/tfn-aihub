import Link from 'next/link'

const routes = [
  { href: '/login', label: 'Login', description: 'Sign in to your account' },
  { href: '/dashboard', label: 'Dashboard', description: 'Main performance dashboard' },
  { href: '/dashboard/production/oee', label: 'OEE', description: 'Overall Equipment Effectiveness' },
  { href: '/dashboard/production/downtime', label: 'Downtime', description: 'Downtime tracking & analysis' },
  { href: '/dashboard/production/throughput', label: 'Throughput', description: 'Production throughput metrics' },
  { href: '/briefing', label: 'Briefings', description: 'Voice briefings list' },
  { href: '/briefing/eod', label: 'EOD Briefing', description: 'End of day briefing' },
  { href: '/morning-report', label: 'Morning Report', description: 'Daily morning report' },
  { href: '/handoff', label: 'Shift Handoffs', description: 'Shift handoff management' },
  { href: '/handoff/new', label: 'New Handoff', description: 'Create a new shift handoff' },
  { href: '/settings/preferences', label: 'Preferences', description: 'User preferences' },
  { href: '/assignments', label: 'Assignments', description: 'Admin: Supervisor assignments' },
  { href: '/users', label: 'Users', description: 'Admin: User management' },
  { href: '/audit', label: 'Audit Log', description: 'Admin: Audit logs' },
]

export default function Home() {
  return (
    <main className="min-h-screen bg-background py-12 px-4">
      <div className="max-w-4xl mx-auto space-y-8">
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold text-foreground">
            Manufacturing Performance Assistant
          </h1>
          <p className="text-lg text-muted-foreground">
            Plant performance monitoring and insights dashboard.
          </p>
          <p className="text-sm text-muted-foreground">
            Test user: <code className="bg-muted px-2 py-1 rounded">heimdall@test.com</code>
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {routes.map((route) => (
            <Link
              key={route.href}
              href={route.href}
              className="block p-4 rounded-lg border border-border bg-card hover:bg-accent hover:border-accent-foreground/20 transition-colors"
            >
              <h2 className="font-semibold text-foreground">{route.label}</h2>
              <p className="text-sm text-muted-foreground mt-1">{route.description}</p>
              <span className="text-xs text-muted-foreground/60 mt-2 block font-mono">
                {route.href}
              </span>
            </Link>
          ))}
        </div>

        <div className="text-center pt-4">
          <p className="text-xs text-muted-foreground">
            Development environment ready. Click any route above to navigate.
          </p>
        </div>
      </div>
    </main>
  )
}
