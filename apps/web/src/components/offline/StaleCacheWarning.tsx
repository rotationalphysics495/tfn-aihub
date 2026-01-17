'use client';

/**
 * StaleCacheWarning Component (Story 9.9, Task 6.2)
 *
 * Displays a warning when cached data is older than 48 hours.
 *
 * @see Story 9.9 - Offline Handoff Caching
 * @see AC#4 - Stale Cache Warning
 */

import { useState, useEffect } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

// ============================================================================
// Types
// ============================================================================

export interface StaleCacheWarningProps {
  /** Whether the cache is stale */
  isStale: boolean;
  /** Age of the cache in milliseconds */
  cacheAgeMs?: number;
  /** Called when user requests refresh */
  onRefresh?: () => void;
  /** Whether refresh is in progress */
  isRefreshing?: boolean;
  /** Whether currently online (SSR-safe, defaults to true) */
  isOnline?: boolean;
  /** Optional CSS class name */
  className?: string;
}

// ============================================================================
// Helper Functions
// ============================================================================

function formatCacheAge(ageMs: number): string {
  const hours = Math.floor(ageMs / (1000 * 60 * 60));
  const days = Math.floor(hours / 24);

  if (days > 0) {
    return `${days} day${days !== 1 ? 's' : ''} ago`;
  }

  return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
}

// ============================================================================
// Component
// ============================================================================

/**
 * StaleCacheWarning displays a warning when cached data is stale.
 *
 * Features:
 * - Shows warning when cache > 48 hours old
 * - Displays cache age
 * - Provides refresh button when online
 *
 * @example
 * ```tsx
 * <StaleCacheWarning
 *   isStale={true}
 *   cacheAgeMs={172800000}
 *   onRefresh={handleRefresh}
 * />
 * ```
 */
export function StaleCacheWarning({
  isStale,
  cacheAgeMs,
  onRefresh,
  isRefreshing = false,
  isOnline: isOnlineProp,
  className,
}: StaleCacheWarningProps) {
  // SSR-safe online state - default to true during SSR, then hydrate with actual value
  const [isOnline, setIsOnline] = useState(true);

  useEffect(() => {
    // Set initial value after hydration
    setIsOnline(isOnlineProp ?? navigator.onLine);

    // If prop is provided, use it instead of listening to events
    if (isOnlineProp !== undefined) {
      return;
    }

    // Listen for online/offline events
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [isOnlineProp]);

  if (!isStale) {
    return null;
  }

  return (
    <div
      className={cn(
        'stale-cache-warning',
        'rounded-lg border border-warning-amber/50 bg-warning-amber/10',
        'p-4 flex items-start gap-3',
        className
      )}
      role="alert"
    >
      <AlertTriangle className="w-5 h-5 text-warning-amber flex-shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-warning-amber-dark">
          This data may be outdated
        </p>
        <p className="text-sm text-muted-foreground mt-1">
          {cacheAgeMs
            ? `Last updated ${formatCacheAge(cacheAgeMs)}.`
            : 'Cached data is older than 48 hours.'}{' '}
          {isOnline
            ? 'Connect to refresh with the latest data.'
            : 'Data will refresh when you reconnect.'}
        </p>
        {onRefresh && isOnline && (
          <Button
            variant="outline"
            size="sm"
            onClick={onRefresh}
            disabled={isRefreshing}
            className="mt-3"
          >
            {isRefreshing ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                Refreshing...
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh now
              </>
            )}
          </Button>
        )}
      </div>
    </div>
  );
}

export default StaleCacheWarning;
