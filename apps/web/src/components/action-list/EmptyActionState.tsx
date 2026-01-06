'use client'

import { CheckCircle2 } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'

/**
 * Empty Action State Component
 *
 * Displays a positive message when no action items exist.
 *
 * @see Story 3.3 - Action List Primary View
 * @see AC #5 - Shows empty state messaging when no action items exist
 */

interface EmptyActionStateProps {
  className?: string
}

export function EmptyActionState({ className }: EmptyActionStateProps) {
  return (
    <Card
      mode="retrospective"
      className={cn(
        'border-success-green/30 bg-success-green-light/10 dark:bg-success-green-dark/10',
        className
      )}
    >
      <CardContent className="p-8 md:p-12 text-center">
        <div className="flex flex-col items-center">
          {/* Success icon */}
          <div className="w-16 h-16 rounded-full bg-success-green-light dark:bg-success-green-dark/30 flex items-center justify-center mb-4">
            <CheckCircle2
              className="w-10 h-10 text-success-green"
              aria-hidden="true"
            />
          </div>

          {/* Primary message - AC #8: Large text for glanceability */}
          <h3 className="text-2xl md:text-3xl font-semibold text-foreground mb-2">
            All Systems Performing Within Targets
          </h3>

          {/* Supporting text */}
          <p className="text-base md:text-lg text-muted-foreground max-w-md">
            No immediate actions required. Your plant is operating within expected parameters.
          </p>

          {/* Additional context */}
          <div className="mt-6 pt-6 border-t border-success-green/20 w-full max-w-sm">
            <p className="text-sm text-muted-foreground">
              Action items will appear here when:
            </p>
            <ul className="mt-2 text-sm text-muted-foreground space-y-1">
              <li>Safety events require attention</li>
              <li>OEE falls below target thresholds</li>
              <li>Financial impact exceeds configured limits</li>
            </ul>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
