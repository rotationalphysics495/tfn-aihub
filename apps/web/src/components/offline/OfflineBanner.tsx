'use client';

/**
 * OfflineBanner Component (Story 9.9, Task 6.1)
 *
 * Displays a banner when the user is offline.
 *
 * @see Story 9.9 - Offline Handoff Caching
 * @see AC#2 - Offline Handoff Access
 */

import { WifiOff, CloudOff } from 'lucide-react';
import { cn } from '@/lib/utils';

// ============================================================================
// Types
// ============================================================================

export interface OfflineBannerProps {
  /** Whether the app is offline */
  isOffline: boolean;
  /** Number of pending sync actions */
  pendingCount?: number;
  /** Optional CSS class name */
  className?: string;
}

// ============================================================================
// Component
// ============================================================================

/**
 * OfflineBanner displays a notification when viewing content offline.
 *
 * Features:
 * - Shows offline indicator with icon
 * - Displays pending sync count
 * - Fixed position at top of viewport
 *
 * @example
 * ```tsx
 * <OfflineBanner isOffline={true} pendingCount={2} />
 * ```
 */
export function OfflineBanner({
  isOffline,
  pendingCount = 0,
  className,
}: OfflineBannerProps) {
  if (!isOffline) {
    return null;
  }

  return (
    <div
      className={cn(
        'offline-banner',
        'fixed top-0 left-0 right-0 z-50',
        'bg-warning-amber/95 text-warning-amber-dark',
        'px-4 py-2 flex items-center justify-center gap-2',
        'text-sm font-medium shadow-md',
        className
      )}
      role="alert"
      aria-live="polite"
    >
      <WifiOff className="w-4 h-4 flex-shrink-0" />
      <span>Viewing offline - some features limited</span>
      {pendingCount > 0 && (
        <>
          <span className="mx-1">|</span>
          <CloudOff className="w-4 h-4 flex-shrink-0" />
          <span>
            {pendingCount} action{pendingCount !== 1 ? 's' : ''} pending sync
          </span>
        </>
      )}
    </div>
  );
}

export default OfflineBanner;
