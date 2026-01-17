'use client';

/**
 * useOfflineHandoff Hook (Story 9.9, Task 7)
 *
 * Fetches handoffs with cache-then-network strategy for offline support.
 *
 * @see Story 9.9 - Offline Handoff Caching
 * @see AC#1 - Online Handoff Caching
 * @see AC#2 - Offline Handoff Access
 * @see AC#4 - Stale Cache Warning
 * @see AC#5 - Connectivity Restoration Sync
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { createClient } from '@/lib/supabase/client';
import {
  cacheHandoffWithVoiceNotes,
  getCachedHandoffWithVoiceNotes,
  getCacheMetadata,
  invalidateCache,
} from '@/lib/offline/handoff-cache';
import { useOfflineSync } from './useOfflineSync';
import type { Handoff, HandoffDetailResponse } from '@/types/handoff';

// ============================================================================
// Types
// ============================================================================

export interface UseOfflineHandoffOptions {
  /** Handoff ID to fetch */
  handoffId: string;
  /** Auto-fetch on mount (default: true) */
  autoFetch?: boolean;
}

export interface UseOfflineHandoffReturn {
  /** Handoff data (from cache or network) */
  handoff: Handoff | null;
  /** Whether loading */
  isLoading: boolean;
  /** Error message */
  error: string | null;
  /** Whether user can acknowledge */
  canAcknowledge: boolean;
  /** Whether data is from cache */
  isFromCache: boolean;
  /** Whether cache is stale (>48 hours) */
  isCacheStale: boolean;
  /** Cache age in milliseconds */
  cacheAgeMs: number | undefined;
  /** Refresh data from network */
  refetch: () => Promise<void>;
  /** Whether refreshing */
  isRefreshing: boolean;
}

// ============================================================================
// Constants
// ============================================================================

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Unable to connect to server. Check your connection.',
  AUTH_ERROR: 'Your session has expired. Please log in again.',
  NOT_FOUND: 'Handoff not found or you do not have access.',
  SERVER_ERROR: "Something went wrong on our end.",
};

// ============================================================================
// Hook
// ============================================================================

/**
 * Hook for fetching handoffs with offline support.
 *
 * Strategy (cache-then-network):
 * 1. Return cached data immediately if available
 * 2. Fetch fresh data from network in background
 * 3. Update cache and state with fresh data
 * 4. Show stale warning if cache is >48 hours old
 *
 * @example
 * ```tsx
 * const {
 *   handoff,
 *   isLoading,
 *   isFromCache,
 *   isCacheStale,
 *   refetch,
 * } = useOfflineHandoff({ handoffId: '123' });
 * ```
 */
export function useOfflineHandoff(
  options: UseOfflineHandoffOptions
): UseOfflineHandoffReturn {
  const { handoffId, autoFetch = true } = options;

  // State
  const [handoff, setHandoff] = useState<Handoff | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [canAcknowledge, setCanAcknowledge] = useState(false);
  const [isFromCache, setIsFromCache] = useState(false);
  const [isCacheStale, setIsCacheStale] = useState(false);
  const [cacheAgeMs, setCacheAgeMs] = useState<number | undefined>(undefined);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Refs
  const mountedRef = useRef(true);

  // Offline sync hook
  const { isOnline } = useOfflineSync();

  // Fetch from network
  const fetchFromNetwork = useCallback(async (): Promise<{
    handoff: Handoff;
    canAcknowledge: boolean;
  } | null> => {
    try {
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session?.access_token) {
        throw new Error(ERROR_MESSAGES.AUTH_ERROR);
      }

      const url = `${API_BASE_URL}/api/v1/handoff/${handoffId}`;

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error(ERROR_MESSAGES.AUTH_ERROR);
        }
        if (response.status === 404) {
          throw new Error(ERROR_MESSAGES.NOT_FOUND);
        }
        throw new Error(ERROR_MESSAGES.SERVER_ERROR);
      }

      const data: HandoffDetailResponse = await response.json();

      // Cache the handoff with voice notes (Task 7.3)
      await cacheHandoffWithVoiceNotes(data.handoff);

      return {
        handoff: data.handoff,
        canAcknowledge: data.can_acknowledge,
      };
    } catch (err) {
      console.error('[useOfflineHandoff] Network fetch failed:', err);
      return null;
    }
  }, [handoffId]);

  // Fetch from cache
  const fetchFromCache = useCallback(async (): Promise<{
    handoff: Handoff;
    isStale: boolean;
    ageMs: number;
  } | null> => {
    try {
      const cached = await getCachedHandoffWithVoiceNotes(handoffId);

      if (!cached) {
        return null;
      }

      const metadata = await getCacheMetadata(handoffId);

      return {
        handoff: cached.handoff,
        isStale: cached.isStale,
        ageMs: metadata?.ageMs || 0,
      };
    } catch (err) {
      console.error('[useOfflineHandoff] Cache fetch failed:', err);
      return null;
    }
  }, [handoffId]);

  // Main fetch with cache-then-network strategy (Task 7.1, 7.2)
  const fetchData = useCallback(async () => {
    if (!handoffId) return;

    setIsLoading(true);
    setError(null);

    // 1. Try cache first (Task 7.2)
    const cached = await fetchFromCache();

    if (cached) {
      if (mountedRef.current) {
        setHandoff(cached.handoff);
        setIsFromCache(true);
        setIsCacheStale(cached.isStale);
        setCacheAgeMs(cached.ageMs);
        setIsLoading(false);
      }
    }

    // 2. Fetch from network in background (Task 7.3)
    if (isOnline) {
      const networkResult = await fetchFromNetwork();

      if (networkResult && mountedRef.current) {
        setHandoff(networkResult.handoff);
        setCanAcknowledge(networkResult.canAcknowledge);
        setIsFromCache(false);
        setIsCacheStale(false);
        setCacheAgeMs(undefined);
        setError(null);
      } else if (!cached && mountedRef.current) {
        // Network failed and no cache
        setError(ERROR_MESSAGES.NETWORK_ERROR);
      }
    } else if (!cached) {
      // Offline and no cache
      if (mountedRef.current) {
        setError('No cached data available. Connect to the internet to load this handoff.');
      }
    }

    if (mountedRef.current) {
      setIsLoading(false);
    }
  }, [handoffId, isOnline, fetchFromCache, fetchFromNetwork]);

  // Refetch from network (Task 7.5)
  const refetch = useCallback(async () => {
    if (!isOnline) {
      return;
    }

    setIsRefreshing(true);

    // Invalidate stale cache first
    await invalidateCache(handoffId);

    const networkResult = await fetchFromNetwork();

    if (networkResult && mountedRef.current) {
      setHandoff(networkResult.handoff);
      setCanAcknowledge(networkResult.canAcknowledge);
      setIsFromCache(false);
      setIsCacheStale(false);
      setCacheAgeMs(undefined);
      setError(null);
    }

    if (mountedRef.current) {
      setIsRefreshing(false);
    }
  }, [handoffId, isOnline, fetchFromNetwork]);

  // Initial fetch
  useEffect(() => {
    mountedRef.current = true;

    if (autoFetch) {
      fetchData();
    }

    return () => {
      mountedRef.current = false;
    };
  }, [autoFetch, fetchData]);

  // Refetch when coming back online (Task 7.5)
  useEffect(() => {
    if (isOnline && isFromCache && isCacheStale) {
      refetch();
    }
  }, [isOnline, isFromCache, isCacheStale, refetch]);

  return {
    handoff,
    isLoading,
    error,
    canAcknowledge,
    isFromCache,
    isCacheStale,
    cacheAgeMs,
    refetch,
    isRefreshing,
  };
}

export default useOfflineHandoff;
