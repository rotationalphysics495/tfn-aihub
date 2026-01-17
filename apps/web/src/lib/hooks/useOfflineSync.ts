'use client';

/**
 * useOfflineSync Hook (Story 9.9, Task 5)
 *
 * Provides offline/online status detection and sync queue management.
 *
 * @see Story 9.9 - Offline Handoff Caching
 * @see AC#2 - Offline Handoff Access
 * @see AC#4 - Stale Cache Warning
 * @see AC#5 - Connectivity Restoration Sync
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { createClient } from '@/lib/supabase/client';
import {
  initializeSyncQueue,
  cleanupSyncQueue,
  syncPendingActions,
  getPendingActions,
  queueAcknowledgmentWithSync,
  hasPendingAcknowledgment,
  type SyncResult,
  type QueuedAction,
} from '@/lib/offline/sync-queue';
import { invalidateStaleCaches } from '@/lib/offline/handoff-cache';
import { onServiceWorkerMessage, clearStaleCache } from '@/lib/offline/sw-registration';

// ============================================================================
// Types
// ============================================================================

export interface UseOfflineSyncReturn {
  /** Whether the browser is online */
  isOnline: boolean;
  /** Whether the browser is offline */
  isOffline: boolean;
  /** Number of pending sync actions */
  pendingSyncCount: number;
  /** Queue an acknowledgment for offline sync */
  queueAcknowledgment: (handoffId: string, notes?: string) => Promise<QueuedAction>;
  /** Check if there's a pending acknowledgment for a handoff */
  hasPendingAck: (handoffId: string) => Promise<boolean>;
  /** Manually trigger sync (usually automatic on reconnect) */
  triggerSync: () => Promise<SyncResult[]>;
  /** Last sync results */
  lastSyncResults: SyncResult[];
  /** Whether a sync is in progress */
  isSyncing: boolean;
}

// ============================================================================
// Constants
// ============================================================================

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

// ============================================================================
// Hook
// ============================================================================

/**
 * Hook for managing offline/online status and sync queue.
 *
 * Features:
 * - Detects online/offline status using navigator.onLine (Task 5.2)
 * - Listens to online/offline events (Task 5.3)
 * - Exposes isOnline, isOffline, pendingSyncCount (Task 5.4)
 * - Triggers sync on online event (Task 5.5)
 * - Provides queueAcknowledgment function (Task 5.6)
 *
 * @example
 * ```tsx
 * const {
 *   isOnline,
 *   isOffline,
 *   pendingSyncCount,
 *   queueAcknowledgment,
 * } = useOfflineSync();
 *
 * if (isOffline) {
 *   await queueAcknowledgment(handoffId, notes);
 * }
 * ```
 */
export function useOfflineSync(): UseOfflineSyncReturn {
  // State
  const [isOnline, setIsOnline] = useState(() =>
    typeof navigator !== 'undefined' ? navigator.onLine : true
  );
  const [pendingSyncCount, setPendingSyncCount] = useState(0);
  const [lastSyncResults, setLastSyncResults] = useState<SyncResult[]>([]);
  const [isSyncing, setIsSyncing] = useState(false);

  // Refs
  const mountedRef = useRef(true);
  const accessTokenRef = useRef<string | null>(null);

  // Update pending count
  const updatePendingCount = useCallback(async () => {
    try {
      const pending = await getPendingActions();
      if (mountedRef.current) {
        setPendingSyncCount(pending.length);
      }
    } catch (error) {
      console.error('Failed to get pending actions:', error);
    }
  }, []);

  // Trigger sync manually
  const triggerSync = useCallback(async (): Promise<SyncResult[]> => {
    if (!accessTokenRef.current || isSyncing) {
      return [];
    }

    setIsSyncing(true);

    try {
      const results = await syncPendingActions(accessTokenRef.current, API_BASE_URL);

      if (mountedRef.current) {
        setLastSyncResults(results);
        await updatePendingCount();
      }

      return results;
    } catch (error) {
      console.error('Sync failed:', error);
      return [];
    } finally {
      if (mountedRef.current) {
        setIsSyncing(false);
      }
    }
  }, [isSyncing, updatePendingCount]);

  // Handle online event (Task 5.3, 5.5)
  const handleOnline = useCallback(() => {
    setIsOnline(true);

    // Trigger sync and clear stale caches
    triggerSync();
    invalidateStaleCaches().catch(console.error);
    clearStaleCache();
  }, [triggerSync]);

  // Handle offline event (Task 5.3)
  const handleOffline = useCallback(() => {
    setIsOnline(false);
  }, []);

  // Queue an acknowledgment (Task 5.6)
  const queueAck = useCallback(
    async (handoffId: string, notes?: string): Promise<QueuedAction> => {
      const action = await queueAcknowledgmentWithSync(handoffId, notes);
      await updatePendingCount();
      return action;
    },
    [updatePendingCount]
  );

  // Check pending acknowledgment
  const hasPendingAck = useCallback(
    async (handoffId: string): Promise<boolean> => {
      return hasPendingAcknowledgment(handoffId);
    },
    []
  );

  // Initialize on mount
  useEffect(() => {
    mountedRef.current = true;

    const init = async () => {
      try {
        // Get access token
        const supabase = createClient();
        const {
          data: { session },
        } = await supabase.auth.getSession();

        if (session?.access_token) {
          accessTokenRef.current = session.access_token;

          // Initialize sync queue
          initializeSyncQueue(session.access_token, API_BASE_URL, (results) => {
            if (mountedRef.current) {
              setLastSyncResults(results);
              updatePendingCount();
            }
          });
        }

        // Get initial pending count
        await updatePendingCount();
      } catch (error) {
        console.error('Failed to initialize offline sync:', error);
      }
    };

    init();

    // Add event listeners (Task 5.3)
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Listen for SW messages (sync-requested, cache-updated, cache-stale)
    const unsubscribe = onServiceWorkerMessage((event) => {
      const { type } = event.data || {};

      if (type === 'sync-requested') {
        // SW requested sync (from Background Sync)
        triggerSync();
      } else if (type === 'cache-updated') {
        // Cache was updated in background - could trigger UI refresh
        console.log('[useOfflineSync] Cache updated:', event.data.payload);
      } else if (type === 'cache-stale') {
        // Cache is stale - UI should show warning
        console.log('[useOfflineSync] Cache stale:', event.data.payload);
      }
    });

    return () => {
      mountedRef.current = false;
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      cleanupSyncQueue();
      unsubscribe();
    };
  }, [handleOnline, handleOffline, updatePendingCount, triggerSync]);

  // Re-initialize when auth changes
  useEffect(() => {
    const supabase = createClient();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, session) => {
      if (session?.access_token) {
        accessTokenRef.current = session.access_token;
        initializeSyncQueue(session.access_token, API_BASE_URL, (results) => {
          if (mountedRef.current) {
            setLastSyncResults(results);
            updatePendingCount();
          }
        });
      } else {
        accessTokenRef.current = null;
        cleanupSyncQueue();
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, [updatePendingCount]);

  return {
    isOnline,
    isOffline: !isOnline,
    pendingSyncCount,
    queueAcknowledgment: queueAck,
    hasPendingAck,
    triggerSync,
    lastSyncResults,
    isSyncing,
  };
}

export default useOfflineSync;
