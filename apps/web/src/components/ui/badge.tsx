import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

/**
 * Industrial Clarity Badge Component
 *
 * Variants:
 * - default: Neutral badge
 * - secondary: Muted secondary badge
 * - outline: Bordered outline badge
 * - safety: RESERVED EXCLUSIVELY for safety incidents (uses Safety Red)
 * - warning: Non-safety warnings and alerts (uses amber)
 * - info: Informational status
 * - success: Positive/success status
 * - retrospective: For retrospective/historical data labels
 * - live: For live/real-time data labels
 *
 * CRITICAL: The "safety" variant uses Safety Red (#DC2626).
 * This variant is RESERVED EXCLUSIVELY for safety incident data.
 * DO NOT use for error states, validation errors, or general warnings.
 * Use "warning" variant for non-safety alerts.
 */
const badgeVariants = cva(
  "inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary text-primary-foreground shadow hover:bg-primary/80",
        secondary:
          "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        outline: "text-foreground",
        // Status variants for Industrial Clarity
        safety:
          "border-safety-red bg-safety-red-light text-safety-red-dark dark:bg-safety-red-dark/20 dark:text-safety-red dark:border-safety-red",
        warning:
          "border-warning-amber bg-warning-amber-light text-warning-amber-dark dark:bg-warning-amber-dark/20 dark:text-warning-amber dark:border-warning-amber",
        info:
          "border-info-blue bg-info-blue-light text-info-blue-dark dark:bg-info-blue-dark/20 dark:text-info-blue dark:border-info-blue",
        success:
          "border-success-green bg-success-green-light text-success-green-dark dark:bg-success-green-dark/20 dark:text-success-green dark:border-success-green",
        // Mode variants
        retrospective:
          "border-retrospective-border bg-retrospective-surface text-retrospective-primary dark:bg-retrospective-surface-dark dark:border-retrospective-border-dark",
        live:
          "border-live-border bg-live-surface text-live-primary dark:bg-live-surface-dark dark:border-live-border-dark",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
