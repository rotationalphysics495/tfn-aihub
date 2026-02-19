'use client';

/**
 * useHandoffList Hook (Story 9.5, Task 7.3)
 *
 * Data fetching hook for handoff list filtered by supervisor assignments.
 *
 * @see Story 9.5 - Handoff Review UI
 * @see AC#1 - Handoff Notification Banner
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { createClient } from '@/lib/supabase/client';
import type {
  HandoffListItem,
  HandoffListResponse,
  HandoffListFilters,
  HandoffState,
} from '@/types/handoff';

// ============================================================================
// Types
// ============================================================================

export interface UseHandoffListOptions {
  /** Filter options */
  filters?: HandoffListFilters;
  /** Auto-fetch on mount (default: true) */
  autoFetch?: boolean;
}

export interface UseHandoffListReturn extends HandoffState<HandoffListItem[]> {
  /** Manually refetch handoffs */
  refetch: () => Promise<void>;
  /** Count of pending handoffs */
  pendingCount: number;
  /** Count of acknowledged handoffs */
  acknowledgedCount: number;
  /** Whether there are any pending handoffs */
  hasPending: boolean;
}

// ============================================================================
// Constants
// ============================================================================

const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Unable to connect to server. Check your connection and try again.',
  AUTH_ERROR: 'Your session has expired. Please log in again.',
  SERVER_ERROR: "Something went wrong on our end. We're working on it.",
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

// ============================================================================
// Hook
// ============================================================================

/**
 * Hook for fetching handoff list with supervisor asset filtering.
 *
 * @example
 * ```tsx
 * const { data: handoffs, isLoading, error, pendingCount, hasPending } = useHandoffList({
 *   filters: { status: 'pending_acknowledgment' },
 * });
 * ```
 */
export function useHandoffList(
  options: UseHandoffListOptions = {}
): UseHandoffListReturn {
  const { filters, autoFetch = true } = options;

  const [state, setState] = useState<HandoffState<HandoffListItem[]>>({
    data: null,
    isLoading: false,
    error: null,
  });
  const [pendingCount, setPendingCount] = useState(0);
  const [acknowledgedCount, setAcknowledgedCount] = useState(0);

  const mountedRef = useRef(true);

  const fetchHandoffs = useCallback(async () => {
    if (!mountedRef.current) return;

    setState((prev) => ({ ...prev, isLoading: true, error: null }));

    try {
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session?.access_token) {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: ERROR_MESSAGES.AUTH_ERROR,
        }));
        return;
      }

      // Build query params
      const params = new URLSearchParams();
      if (filters?.status) {
        params.set('status', filters.status);
      }
      if (filters?.shift_date) {
        params.set('shift_date', filters.shift_date);
      }

      const url = `${API_BASE_URL}/api/v1/handoff${params.toString() ? `?${params.toString()}` : ''}`;
      const pendingUrl = `${API_BASE_URL}/api/v1/handoff/pending`;

      const headers = {
        Authorization: `Bearer ${session.access_token}`,
        'Content-Type': 'application/json',
      };

      const [response, pendingResponse] = await Promise.all([
        fetch(url, { method: 'GET', headers }),
        fetch(pendingUrl, { method: 'GET', headers }),
      ]);

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error(ERROR_MESSAGES.AUTH_ERROR);
        }
        throw new Error(ERROR_MESSAGES.SERVER_ERROR);
      }

      const data: HandoffListResponse = await response.json();

      // Merge incoming pending handoffs from other supervisors
      let allHandoffs = data.handoffs;
      if (pendingResponse.ok) {
        const pendingData = await pendingResponse.json();
        const incomingIds = new Set(allHandoffs.map((h) => h.id));
        const incoming = (pendingData.handoffs ?? []).filter(
          (h: HandoffListItem) => !incomingIds.has(h.id)
        );
        allHandoffs = [...allHandoffs, ...incoming];
      }

      if (!mountedRef.current) return;

      setState({
        data: allHandoffs,
        isLoading: false,
        error: null,
      });
      setPendingCount(
        allHandoffs.filter((h) => h.status === 'pending_acknowledgment').length
      );
      setAcknowledgedCount(
        allHandoffs.filter((h) => h.status === 'acknowledged').length
      );
    } catch (error) {
      if (!mountedRef.current) return;

      const message =
        error instanceof Error ? error.message : ERROR_MESSAGES.SERVER_ERROR;

      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: message,
      }));
    }
  }, [filters?.status, filters?.shift_date]);

  // Initial fetch on mount
  useEffect(() => {
    mountedRef.current = true;

    if (autoFetch) {
      fetchHandoffs();
    }

    return () => {
      mountedRef.current = false;
    };
  }, [autoFetch, fetchHandoffs]);

  // Computed values
  const hasPending = pendingCount > 0;

  return {
    ...state,
    refetch: fetchHandoffs,
    pendingCount,
    acknowledgedCount,
    hasPending,
  };
}

export default useHandoffList;
