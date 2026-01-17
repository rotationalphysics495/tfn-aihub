/**
 * useHandoffQA Hook (Story 9.6)
 *
 * State management and real-time subscription for handoff Q&A threads.
 * Handles question submission, thread updates, and real-time notifications.
 *
 * AC#1: Users can type or speak questions about handoff content
 * AC#2: AI responses include citations to source data (FR52)
 * AC#3: Outgoing supervisor can respond directly
 * AC#4: All Q&A entries preserved and visible
 * AC#5: Real-time updates via Supabase Realtime
 *
 * References:
 * - [Source: architecture/voice-briefing.md#Shift-Handoff-Workflow]
 * - [Source: prd/prd-functional-requirements.md#FR26,FR52]
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { createClient, RealtimeChannel } from '@supabase/supabase-js';

/**
 * Q&A entry content type.
 */
export type QAContentType = 'question' | 'ai_answer' | 'human_response';

/**
 * Citation for AI responses.
 */
export interface QACitation {
  value: string;
  field: string;
  table: string;
  context: string;
  timestamp?: string;
}

/**
 * Q&A entry in the thread.
 */
export interface QAEntry {
  id: string;
  handoff_id: string;
  user_id: string;
  user_name?: string;
  content_type: QAContentType;
  content: string;
  citations: QACitation[];
  voice_transcript?: string;
  created_at: string;
}

/**
 * Q&A thread state.
 */
export interface QAThread {
  handoff_id: string;
  entries: QAEntry[];
  count: number;
}

/**
 * Q&A hook state.
 */
export interface UseHandoffQAState {
  thread: QAThread | null;
  isLoading: boolean;
  isSubmitting: boolean;
  error: string | null;
  hasNewEntry: boolean;
}

/**
 * Q&A hook configuration.
 */
export interface UseHandoffQAConfig {
  /** API base URL */
  apiBaseUrl?: string;
  /** Supabase URL for realtime */
  supabaseUrl?: string;
  /** Supabase anon key */
  supabaseKey?: string;
  /** Callback when new entry arrives */
  onNewEntry?: (entry: QAEntry) => void;
  /** Callback on error */
  onError?: (error: string) => void;
}

/**
 * Q&A hook actions.
 */
export interface UseHandoffQAActions {
  /** Submit a question */
  submitQuestion: (question: string, voiceTranscript?: string) => Promise<void>;
  /** Submit a human response (for outgoing supervisor) */
  submitResponse: (response: string, questionEntryId?: string) => Promise<void>;
  /** Refresh the thread */
  refreshThread: () => Promise<void>;
  /** Clear error state */
  clearError: () => void;
  /** Acknowledge new entry notification */
  acknowledgeNewEntry: () => void;
}

/**
 * Initial state.
 */
const initialState: UseHandoffQAState = {
  thread: null,
  isLoading: false,
  isSubmitting: false,
  error: null,
  hasNewEntry: false,
};

/**
 * useHandoffQA hook for managing handoff Q&A threads.
 *
 * Story 9.6 Implementation:
 * - AC#1: Submit questions via text or voice
 * - AC#2: Display AI responses with citations
 * - AC#3: Support human responses from outgoing supervisor
 * - AC#4: Show complete thread history
 * - AC#5: Real-time updates via Supabase Realtime
 *
 * @param handoffId - UUID of the handoff
 * @param config - Configuration options
 * @returns [state, actions] tuple
 */
export function useHandoffQA(
  handoffId: string | null,
  config: UseHandoffQAConfig = {}
): [UseHandoffQAState, UseHandoffQAActions] {
  const {
    apiBaseUrl = '/api/v1/handoff',
    supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '',
    supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '',
    onNewEntry,
    onError,
  } = config;

  // State
  const [state, setState] = useState<UseHandoffQAState>(initialState);

  // Refs
  const channelRef = useRef<RealtimeChannel | null>(null);
  const supabaseRef = useRef<ReturnType<typeof createClient> | null>(null);

  /**
   * Fetch the current Q&A thread.
   */
  const fetchThread = useCallback(async () => {
    if (!handoffId) return;

    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await fetch(`${apiBaseUrl}/${handoffId}/qa`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch Q&A thread: ${response.status}`);
      }

      const data: QAThread = await response.json();

      setState(prev => ({
        ...prev,
        thread: data,
        isLoading: false,
        error: null,
      }));
    } catch (error) {
      const errorMessage = error instanceof Error
        ? error.message
        : 'Failed to fetch Q&A thread';

      setState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }));
      onError?.(errorMessage);
    }
  }, [handoffId, apiBaseUrl, onError]);

  /**
   * Submit a Q&A question.
   * AC#1: Users can type or speak questions
   */
  const submitQuestion = useCallback(async (
    question: string,
    voiceTranscript?: string
  ) => {
    if (!handoffId) return;

    setState(prev => ({ ...prev, isSubmitting: true, error: null }));

    try {
      const response = await fetch(`${apiBaseUrl}/${handoffId}/qa`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          question,
          voice_transcript: voiceTranscript,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `Failed to submit question: ${response.status}`
        );
      }

      const data = await response.json();

      // Update thread with new entries
      setState(prev => ({
        ...prev,
        thread: prev.thread
          ? {
              ...prev.thread,
              entries: [
                ...prev.thread.entries,
                data.question_entry,
                data.entry,
              ],
              count: data.thread_count,
            }
          : {
              handoff_id: handoffId,
              entries: [data.question_entry, data.entry],
              count: data.thread_count,
            },
        isSubmitting: false,
        error: null,
      }));

    } catch (error) {
      const errorMessage = error instanceof Error
        ? error.message
        : 'Failed to submit question';

      setState(prev => ({
        ...prev,
        isSubmitting: false,
        error: errorMessage,
      }));
      onError?.(errorMessage);
    }
  }, [handoffId, apiBaseUrl, onError]);

  /**
   * Submit a human response.
   * AC#3: Outgoing supervisor can respond directly
   */
  const submitResponse = useCallback(async (
    response: string,
    questionEntryId?: string
  ) => {
    if (!handoffId) return;

    setState(prev => ({ ...prev, isSubmitting: true, error: null }));

    try {
      const fetchResponse = await fetch(`${apiBaseUrl}/${handoffId}/qa/respond`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          response,
          question_entry_id: questionEntryId,
        }),
      });

      if (!fetchResponse.ok) {
        const errorData = await fetchResponse.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `Failed to submit response: ${fetchResponse.status}`
        );
      }

      const data: QAEntry = await fetchResponse.json();

      // Update thread with new entry
      setState(prev => ({
        ...prev,
        thread: prev.thread
          ? {
              ...prev.thread,
              entries: [...prev.thread.entries, data],
              count: prev.thread.count + 1,
            }
          : {
              handoff_id: handoffId,
              entries: [data],
              count: 1,
            },
        isSubmitting: false,
        error: null,
      }));

    } catch (error) {
      const errorMessage = error instanceof Error
        ? error.message
        : 'Failed to submit response';

      setState(prev => ({
        ...prev,
        isSubmitting: false,
        error: errorMessage,
      }));
      onError?.(errorMessage);
    }
  }, [handoffId, apiBaseUrl, onError]);

  /**
   * Refresh the thread.
   */
  const refreshThread = useCallback(async () => {
    await fetchThread();
  }, [fetchThread]);

  /**
   * Clear error state.
   */
  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  /**
   * Acknowledge new entry notification.
   */
  const acknowledgeNewEntry = useCallback(() => {
    setState(prev => ({ ...prev, hasNewEntry: false }));
  }, []);

  /**
   * Handle real-time insert event.
   * AC#5: Real-time updates via Supabase Realtime
   */
  const handleRealtimeInsert = useCallback((payload: { new: Record<string, unknown> }) => {
    const newEntry: QAEntry = {
      id: payload.new.id as string,
      handoff_id: payload.new.handoff_id as string,
      user_id: payload.new.user_id as string,
      user_name: payload.new.user_name as string | undefined,
      content_type: payload.new.content_type as QAContentType,
      content: payload.new.content as string,
      citations: (payload.new.citations as QACitation[]) || [],
      voice_transcript: payload.new.voice_transcript as string | undefined,
      created_at: payload.new.created_at as string,
    };

    // Check if this entry is already in the thread (avoid duplicates)
    setState(prev => {
      const existingIds = new Set(prev.thread?.entries.map(e => e.id) || []);
      if (existingIds.has(newEntry.id)) {
        return prev;
      }

      // Add to thread
      return {
        ...prev,
        thread: prev.thread
          ? {
              ...prev.thread,
              entries: [...prev.thread.entries, newEntry],
              count: prev.thread.count + 1,
            }
          : {
              handoff_id: newEntry.handoff_id,
              entries: [newEntry],
              count: 1,
            },
        hasNewEntry: true,
      };
    });

    // Notify callback
    onNewEntry?.(newEntry);
  }, [onNewEntry]);

  /**
   * Set up real-time subscription.
   * AC#5: Real-time updates for Q&A entries
   */
  useEffect(() => {
    if (!handoffId || !supabaseUrl || !supabaseKey) return;

    // Create Supabase client if not exists
    if (!supabaseRef.current) {
      supabaseRef.current = createClient(supabaseUrl, supabaseKey);
    }

    const supabase = supabaseRef.current;

    // Clean up existing channel
    if (channelRef.current) {
      supabase.removeChannel(channelRef.current);
      channelRef.current = null;
    }

    // Create channel for this handoff's Q&A entries
    const channel = supabase
      .channel(`handoff-qa:${handoffId}`)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'handoff_qa_entries',
          filter: `handoff_id=eq.${handoffId}`,
        },
        handleRealtimeInsert
      )
      .subscribe();

    channelRef.current = channel;

    // Cleanup on unmount or handoffId change
    return () => {
      if (channelRef.current) {
        supabase.removeChannel(channelRef.current);
        channelRef.current = null;
      }
    };
  }, [handoffId, supabaseUrl, supabaseKey, handleRealtimeInsert]);

  /**
   * Fetch thread on mount and handoffId change.
   */
  useEffect(() => {
    if (handoffId) {
      fetchThread();
    } else {
      setState(initialState);
    }
  }, [handoffId, fetchThread]);

  // Actions object
  const actions: UseHandoffQAActions = {
    submitQuestion,
    submitResponse,
    refreshThread,
    clearError,
    acknowledgeNewEntry,
  };

  return [state, actions];
}

export default useHandoffQA;
