/**
 * Safety Alert Components
 *
 * Components for the Safety Alert System (Story 2.6).
 * These components use "Safety Red" (#DC2626) EXCLUSIVELY for safety incidents.
 *
 * DO NOT use these components or the safety-red color for:
 * - Error states
 * - Validation errors
 * - General warnings
 * - Destructive actions
 *
 * For non-safety alerts, use the warning-amber color instead.
 */

export { SafetyAlertBanner, type SafetyAlert } from './SafetyAlertBanner'
export { SafetyAlertCard, type SafetyEvent } from './SafetyAlertCard'
export { SafetyIndicator } from './SafetyIndicator'
