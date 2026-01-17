'use client';

/**
 * useHandoff Hook (Story 9.5, Task 7.2)
 *
 * Data fetching hook for single handoff detail.
 *
 * @see Story 9.5 - Handoff Review UI
 * @see AC#2 - Handoff Detail View
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { createClient } from '@/lib/supabase/client';
import type {
  Handoff,
  HandoffDetailResponse,
  HandoffState,
} from '@/types/handoff';

// ============================================================================
// Types
// ============================================================================

export interface UseHandoffOptions {
  /** Handoff ID to fetch */
  handoffId: string;
  /** Auto-fetch on mount (default: true) */
  autoFetch?: boolean;
}

export interface UseHandoffReturn extends HandoffState<Handoff> {
  /** Manually refetch handoff */
  refetch: () => Promise<void>;
  /** Whether user can acknowledge this handoff */
  canAcknowledge: boolean;
}

// ============================================================================
// Constants
// ============================================================================

const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Unable to connect to server. Check your connection and try again.',
  AUTH_ERROR: 'Your session has expired. Please log in again.',
  NOT_FOUND: 'Handoff not found or you do not have access.',
  SERVER_ERROR: "Something went wrong on our end. We're working on it.",
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

// ============================================================================
// Hook
// ============================================================================

/**
 * Hook for fetching a single handoff with full details.
 *
 * @example
 * ```tsx
 * const { data: handoff, isLoading, error, canAcknowledge } = useHandoff({
 *   handoffId: 'handoff-123',
 * });
 * ```
 */
export function useHandoff(options: UseHandoffOptions): UseHandoffReturn {
  const { handoffId, autoFetch = true } = options;

  const [state, setState] = useState<HandoffState<Handoff>>({
    data: null,
    isLoading: false,
    error: null,
  });
  const [canAcknowledge, setCanAcknowledge] = useState(false);

  const mountedRef = useRef(true);

  const fetchHandoff = useCallback(async () => {
    if (!mountedRef.current || !handoffId) return;

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

      if (!mountedRef.current) return;

      setState({
        data: data.handoff,
        isLoading: false,
        error: null,
      });
      setCanAcknowledge(data.can_acknowledge);
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
  }, [handoffId]);

  // Initial fetch on mount
  useEffect(() => {
    mountedRef.current = true;

    if (autoFetch) {
      fetchHandoff();
    }

    return () => {
      mountedRef.current = false;
    };
  }, [autoFetch, fetchHandoff]);

  return {
    ...state,
    refetch: fetchHandoff,
    canAcknowledge,
  };
}

export default useHandoff;
