'use client';

/**
 * ServiceWorkerProvider Component (Story 9.9, Task 1.4, 1.5)
 *
 * Handles Service Worker registration on app load and provides
 * update notification UI.
 *
 * @see Story 9.9 - Offline Handoff Caching
 * @see AC#1 - Online Handoff Caching
 * @see AC#5 - Connectivity Restoration Sync
 */

import { useEffect, useState, useCallback } from 'react';
import { RefreshCw, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  registerServiceWorker,
  onServiceWorkerUpdate,
  activateUpdate,
  setupReloadOnControllerChange,
  type SWUpdateInfo,
} from '@/lib/offline/sw-registration';

// ============================================================================
// Types
// ============================================================================

export interface ServiceWorkerProviderProps {
  children: React.ReactNode;
}

// ============================================================================
// Component
// ============================================================================

/**
 * ServiceWorkerProvider registers the Service Worker and handles updates.
 *
 * Features:
 * - Registers SW on mount
 * - Shows update notification banner
 * - Handles reload on SW update
 *
 * @example
 * ```tsx
 * <ServiceWorkerProvider>
 *   <App />
 * </ServiceWorkerProvider>
 * ```
 */
export function ServiceWorkerProvider({ children }: ServiceWorkerProviderProps) {
  const [updateAvailable, setUpdateAvailable] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  // Register Service Worker on mount
  useEffect(() => {
    // Only register in production or when explicitly enabled
    if (
      process.env.NODE_ENV === 'production' ||
      process.env.NEXT_PUBLIC_ENABLE_SW === 'true'
    ) {
      registerServiceWorker();
      setupReloadOnControllerChange();

      // Listen for updates
      onServiceWorkerUpdate((info: SWUpdateInfo) => {
        if (info.updateAvailable) {
          setUpdateAvailable(true);
        }
      });
    }
  }, []);

  // Handle update click
  const handleUpdate = useCallback(() => {
    activateUpdate();
    // Page will reload via controllerchange event
  }, []);

  // Handle dismiss
  const handleDismiss = useCallback(() => {
    setDismissed(true);
  }, []);

  return (
    <>
      {children}

      {/* Update notification banner (Task 1.5) */}
      {updateAvailable && !dismissed && (
        <div
          className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-96 z-50"
          role="alert"
          aria-live="polite"
        >
          <div className="bg-primary text-primary-foreground rounded-lg shadow-lg p-4 flex items-start gap-3">
            <RefreshCw className="w-5 h-5 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <p className="font-medium text-sm">Update available</p>
              <p className="text-xs opacity-90 mt-1">
                A new version of the app is ready. Refresh to get the latest features.
              </p>
              <div className="flex gap-2 mt-3">
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={handleUpdate}
                  className="text-xs"
                >
                  Refresh now
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={handleDismiss}
                  className="text-xs opacity-75 hover:opacity-100"
                >
                  Later
                </Button>
              </div>
            </div>
            <button
              type="button"
              onClick={handleDismiss}
              className="text-primary-foreground/75 hover:text-primary-foreground"
              aria-label="Dismiss update notification"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </>
  );
}

export default ServiceWorkerProvider;
