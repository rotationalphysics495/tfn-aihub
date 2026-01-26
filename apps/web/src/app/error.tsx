'use client'

import { useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'

/**
 * Global Error Boundary Page
 *
 * Catches and displays runtime errors with a user-friendly message.
 * Follows Industrial Clarity Design System guidelines.
 *
 * Note: Uses warning-amber for errors (NOT safety-red, which is reserved
 * exclusively for actual safety incidents per design system).
 *
 * @see Epic 1, Scenario 9 - Error handling requirements
 */
export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    // Log the error to console for debugging
    console.error('Application error:', error)
  }, [error])

  return (
    <main className="min-h-screen bg-background flex items-center justify-center px-4">
      <Card className="max-w-md w-full text-center">
        <CardContent className="pt-8 pb-8">
          {/* Icon */}
          <div className="mx-auto w-16 h-16 rounded-full bg-warning-amber/10 flex items-center justify-center mb-6">
            <svg
              className="w-8 h-8 text-warning-amber"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>

          {/* Title */}
          <h1 className="section-header text-foreground mb-3">
            Something Went Wrong
          </h1>

          {/* Description */}
          <p className="body-text text-muted-foreground mb-6">
            An unexpected error occurred. Our team has been notified.
          </p>

          {/* Error digest for support reference */}
          {error.digest && (
            <p className="label-text text-muted-foreground mb-6">
              Reference: <code className="text-xs bg-muted px-2 py-1 rounded">{error.digest}</code>
            </p>
          )}

          {/* Actions */}
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Button onClick={reset}>
              Try Again
            </Button>
            <Button
              variant="outline"
              onClick={() => window.location.href = '/dashboard'}
            >
              Go to Dashboard
            </Button>
          </div>
        </CardContent>
      </Card>
    </main>
  )
}
