import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'

/**
 * Global 404 Not Found Page
 *
 * Displays a user-friendly message when a page is not found.
 * Follows Industrial Clarity Design System guidelines.
 *
 * @see Epic 1, Scenario 9 - Error handling requirements
 */
export default function NotFound() {
  return (
    <main className="min-h-screen bg-background flex items-center justify-center px-4">
      <Card className="max-w-md w-full text-center">
        <CardContent className="pt-8 pb-8">
          {/* Icon */}
          <div className="mx-auto w-10 h-10 rounded-full bg-muted flex items-center justify-center mb-4">
            <svg
              className="w-5 h-5 text-muted-foreground"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>

          {/* Error Code */}
          <p className="text-5xl font-bold text-muted-foreground mb-2">404</p>

          {/* Title */}
          <h1 className="section-header text-foreground mb-3">
            Page Not Found
          </h1>

          {/* Description */}
          <p className="body-text text-muted-foreground mb-8">
            The page you&apos;re looking for doesn&apos;t exist or has been moved.
          </p>

          {/* Actions */}
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Button asChild>
              <Link href="/dashboard">
                Go to Dashboard
              </Link>
            </Button>
            <Button variant="outline" asChild>
              <Link href="/">
                Back to Home
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </main>
  )
}
