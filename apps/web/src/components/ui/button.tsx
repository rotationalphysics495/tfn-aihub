import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

/**
 * Industrial Clarity Button Component
 *
 * Variants:
 * - default: Primary action button
 * - destructive: Non-safety destructive actions (uses amber, NOT safety-red)
 * - outline: Secondary bordered button
 * - secondary: Muted secondary button
 * - ghost: Minimal style button
 * - link: Text-style link button
 * - retrospective: Cool/muted styling for retrospective analysis mode
 * - live: Vibrant styling for real-time monitoring mode
 *
 * CRITICAL: The "destructive" variant uses amber/warning colors.
 * Safety-red is RESERVED EXCLUSIVELY for safety incident components.
 */
const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0 touch-target",
  {
    variants: {
      variant: {
        default:
          "bg-primary text-primary-foreground shadow hover:bg-primary/90",
        destructive:
          "bg-warning-amber text-white shadow-sm hover:bg-warning-amber-dark",
        outline:
          "border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground",
        secondary:
          "bg-secondary text-secondary-foreground shadow-sm hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
        // Industrial Clarity mode variants
        retrospective:
          "bg-retrospective-primary text-white shadow-sm hover:bg-retrospective-primary/90 border border-retrospective-border",
        live:
          "bg-live-primary text-white shadow-sm hover:bg-live-pulse border border-live-border animate-live-pulse",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3 text-xs",
        lg: "h-12 rounded-md px-8 text-base",
        xl: "h-14 rounded-md px-10 text-lg",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
