"use client"

import * as React from "react"
import { ThemeProvider as NextThemesProvider, type ThemeProviderProps } from "next-themes"

/**
 * Theme Provider for Industrial Clarity Design System
 *
 * Supports:
 * - Light mode: Optimized for bright factory floor conditions
 * - Dark mode: Optimized for low-light factory areas
 * - System preference: Follows user's OS theme preference
 *
 * Usage:
 * Wrap the app in this provider in layout.tsx.
 * Use the useTheme hook from next-themes to toggle themes.
 */
export function ThemeProvider({ children, ...props }: ThemeProviderProps) {
  return <NextThemesProvider {...props}>{children}</NextThemesProvider>
}
