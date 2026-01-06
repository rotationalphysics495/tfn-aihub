import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

/**
 * Industrial Clarity Alert Component
 *
 * Variants:
 * - default: Standard informational alert
 * - destructive: RESERVED EXCLUSIVELY for safety incidents (uses Safety Red)
 * - warning: Non-safety warnings and important notices (uses amber)
 * - info: Informational messages
 * - success: Positive confirmations and success messages
 *
 * CRITICAL: The "destructive" variant uses Safety Red (#DC2626).
 * This is RESERVED EXCLUSIVELY for safety incident alerts.
 * Per UX Design Section 2.4: "Safety Red is reserved EXCLUSIVELY for incidents"
 *
 * For non-safety alerts:
 * - Use "warning" for important notices and non-safety warnings
 * - Use "info" for general information
 * - Use "success" for positive confirmations
 */
const alertVariants = cva(
  "relative w-full rounded-lg border px-4 py-3 text-sm [&>svg+div]:translate-y-[-3px] [&>svg]:absolute [&>svg]:left-4 [&>svg]:top-4 [&>svg]:text-foreground [&>svg~*]:pl-7",
  {
    variants: {
      variant: {
        default: "bg-background text-foreground",
        // SAFETY INCIDENT ONLY - Uses Safety Red
        destructive:
          "border-safety-red bg-safety-red-light text-safety-red-dark dark:bg-safety-red-dark/20 dark:text-safety-red dark:border-safety-red [&>svg]:text-safety-red animate-safety-pulse",
        // Non-safety variants
        warning:
          "border-warning-amber bg-warning-amber-light text-warning-amber-dark dark:bg-warning-amber-dark/20 dark:text-warning-amber dark:border-warning-amber [&>svg]:text-warning-amber",
        info:
          "border-info-blue bg-info-blue-light text-info-blue-dark dark:bg-info-blue-dark/20 dark:text-info-blue dark:border-info-blue [&>svg]:text-info-blue",
        success:
          "border-success-green bg-success-green-light text-success-green-dark dark:bg-success-green-dark/20 dark:text-success-green dark:border-success-green [&>svg]:text-success-green",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

const Alert = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & VariantProps<typeof alertVariants>
>(({ className, variant, ...props }, ref) => (
  <div
    ref={ref}
    role="alert"
    className={cn(alertVariants({ variant }), className)}
    {...props}
  />
))
Alert.displayName = "Alert"

const AlertTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h5
    ref={ref}
    className={cn("mb-1 font-semibold leading-none tracking-tight text-base", className)}
    {...props}
  />
))
AlertTitle.displayName = "AlertTitle"

const AlertDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("text-sm [&_p]:leading-relaxed", className)}
    {...props}
  />
))
AlertDescription.displayName = "AlertDescription"

export { Alert, AlertTitle, AlertDescription, alertVariants }
