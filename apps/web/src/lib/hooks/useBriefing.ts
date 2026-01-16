/**
 * useBriefing Hook (Story 8.4)
 *
 * State management and control for morning briefing sessions.
 * Handles section navigation, pause/resume, silence detection, and Q&A.
 *
 * AC#2: Pause prompts between sections
 * AC#3: Continue commands (No/Continue/Next)
 * AC#4: Silence detection for auto-continue (3-4 seconds)
 * AC#5: Q&A during pause
 *
 * References:
 * - [Source: architecture/voice-briefing.md#Voice Integration Architecture]
 */

import { useState, useCallback, useRef, useEffect } from 'react';

/**
 * Briefing section from API.
 */
export interface BriefingSection {
  section_type: string;
  title: string;
  content: string;
  area_id?: string;
  status: string;
  pause_point: boolean;
  duration_estimate_ms?: number;
  error_message?: string;
}

/**
 * Transcript entry for Q&A panel.
 */
export interface TranscriptEntry {
  id: string;
  type: 'user' | 'assistant' | 'system';
  text: string;
  timestamp: string;
  confidence?: number;
  citations?: string[];
  isProcessing?: boolean;
}

/**
 * Briefing status states.
 */
export type BriefingStatus =
  | 'idle'
  | 'loading'
  | 'playing'
  | 'paused'
  | 'awaiting_response' // After section pause prompt
  | 'qa'  // Processing Q&A
  | 'complete'
  | 'error';

/**
 * Briefing state interface.
 */
export interface BriefingState {
  briefingId: string | null;
  title: string;
  sections: BriefingSection[];
  currentSectionIndex: number;
  status: BriefingStatus;
  silenceCountdown: number | null;
  transcript: TranscriptEntry[];
  audioStreamUrl: string | null;
  totalDurationEstimate: number;
  error: string | null;
}

/**
 * Configuration for the hook.
 */
export interface UseBriefingConfig {
  /** API base URL */
  apiBaseUrl?: string;
  /** Silence timeout in milliseconds (default: 3500ms) */
  silenceTimeoutMs?: number;
  /** Callback when briefing completes */
  onComplete?: () => void;
  /** Callback on error */
  onError?: (error: string) => void;
  /** Callback when section changes */
  onSectionChange?: (index: number, section: BriefingSection) => void;
}

/**
 * Actions returned by the hook.
 */
export interface BriefingActions {
  /** Start a new morning briefing */
  startBriefing: (userId: string, areaOrder?: string[]) => Promise<void>;
  /** Play/resume the current section */
  play: () => void;
  /** Pause playback */
  pause: () => void;
  /** Skip to next section */
  nextSection: () => void;
  /** Go to previous section */
  previousSection: () => void;
  /** Go to specific section */
  goToSection: (index: number) => void;
  /** Submit a Q&A question */
  submitQuestion: (question: string) => Promise<void>;
  /** Continue after pause (user said "Continue" or silence detected) */
  continueAfterPause: () => void;
  /** End the briefing session */
  endBriefing: () => void;
  /** Reset state */
  reset: () => void;
  /** Start silence detection */
  startSilenceDetection: () => void;
  /** Cancel silence detection */
  cancelSilenceDetection: () => void;
}

/**
 * Initial state.
 */
const initialState: BriefingState = {
  briefingId: null,
  title: '',
  sections: [],
  currentSectionIndex: 0,
  status: 'idle',
  silenceCountdown: null,
  transcript: [],
  audioStreamUrl: null,
  totalDurationEstimate: 0,
  error: null,
};

/**
 * useBriefing hook for managing morning briefing state.
 *
 * Story 8.4 Implementation:
 * - AC#2: Manages pause state between sections
 * - AC#3: Handles continue commands
 * - AC#4: Implements silence detection with countdown
 * - AC#5: Integrates Q&A during pauses
 */
export function useBriefing(config: UseBriefingConfig = {}): [BriefingState, BriefingActions] {
  const {
    apiBaseUrl = '/api/v1/briefing',
    silenceTimeoutMs = 3500,
    onComplete,
    onError,
    onSectionChange,
  } = config;

  // State
  const [state, setState] = useState<BriefingState>(initialState);

  // Refs
  const silenceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const countdownIntervalRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * Generate unique ID for transcript entries.
   */
  const generateId = () => `entry-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

  /**
   * Add entry to transcript.
   */
  const addTranscriptEntry = useCallback((
    type: 'user' | 'assistant' | 'system',
    text: string,
    options: { confidence?: number; citations?: string[]; isProcessing?: boolean } = {}
  ) => {
    setState(prev => ({
      ...prev,
      transcript: [
        ...prev.transcript,
        {
          id: generateId(),
          type,
          text,
          timestamp: new Date().toISOString(),
          ...options,
        },
      ],
    }));
  }, []);

  /**
   * Update the last transcript entry (for processing -> complete).
   */
  const updateLastTranscriptEntry = useCallback((
    updates: Partial<TranscriptEntry>
  ) => {
    setState(prev => ({
      ...prev,
      transcript: prev.transcript.map((entry, idx) =>
        idx === prev.transcript.length - 1
          ? { ...entry, ...updates }
          : entry
      ),
    }));
  }, []);

  /**
   * Clear silence detection timers.
   */
  const clearSilenceTimers = useCallback(() => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
    if (countdownIntervalRef.current) {
      clearInterval(countdownIntervalRef.current);
      countdownIntervalRef.current = null;
    }
    setState(prev => ({ ...prev, silenceCountdown: null }));
  }, []);

  /**
   * Start silence detection countdown.
   * AC#4: 3-4 seconds of silence triggers auto-continue
   */
  const startSilenceDetection = useCallback(() => {
    // Clear any existing timers
    clearSilenceTimers();

    // Start countdown display
    const countdownSeconds = Math.ceil(silenceTimeoutMs / 1000);
    setState(prev => ({ ...prev, silenceCountdown: countdownSeconds }));

    // Countdown interval (update every second)
    countdownIntervalRef.current = setInterval(() => {
      setState(prev => {
        const newCount = (prev.silenceCountdown ?? countdownSeconds) - 1;
        if (newCount <= 0) {
          return { ...prev, silenceCountdown: 0 };
        }
        return { ...prev, silenceCountdown: newCount };
      });
    }, 1000);

    // Auto-continue timer
    silenceTimerRef.current = setTimeout(() => {
      clearSilenceTimers();
      // Auto-continue to next section
      setState(prev => {
        if (prev.status === 'awaiting_response') {
          const nextIndex = prev.currentSectionIndex + 1;
          if (nextIndex < prev.sections.length) {
            onSectionChange?.(nextIndex, prev.sections[nextIndex]);
            return {
              ...prev,
              currentSectionIndex: nextIndex,
              status: 'playing',
              silenceCountdown: null,
            };
          } else {
            onComplete?.();
            return {
              ...prev,
              status: 'complete',
              silenceCountdown: null,
            };
          }
        }
        return prev;
      });
    }, silenceTimeoutMs);
  }, [silenceTimeoutMs, clearSilenceTimers, onSectionChange, onComplete]);

  /**
   * Cancel silence detection.
   */
  const cancelSilenceDetection = useCallback(() => {
    clearSilenceTimers();
  }, [clearSilenceTimers]);

  /**
   * Start a new morning briefing.
   */
  const startBriefing = useCallback(async (userId: string, areaOrder?: string[]) => {
    setState(prev => ({ ...prev, status: 'loading', error: null }));

    try {
      const response = await fetch(`${apiBaseUrl}/morning`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          area_order: areaOrder,
          include_audio: true,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to start briefing: ${response.status}`);
      }

      const data = await response.json();

      setState(prev => ({
        ...prev,
        briefingId: data.briefing_id,
        title: data.title,
        sections: data.sections,
        currentSectionIndex: 0,
        status: 'playing',
        audioStreamUrl: data.audio_stream_url,
        totalDurationEstimate: data.total_duration_estimate,
        transcript: [],
        error: null,
      }));

      // Notify section change
      if (data.sections.length > 0) {
        onSectionChange?.(0, data.sections[0]);
      }

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to start briefing';
      setState(prev => ({
        ...prev,
        status: 'error',
        error: errorMessage,
      }));
      onError?.(errorMessage);
    }
  }, [apiBaseUrl, onSectionChange, onError]);

  /**
   * Play/resume the current section.
   */
  const play = useCallback(() => {
    setState(prev => {
      if (prev.status === 'paused' || prev.status === 'awaiting_response') {
        return { ...prev, status: 'playing' };
      }
      return prev;
    });
    clearSilenceTimers();
  }, [clearSilenceTimers]);

  /**
   * Pause playback.
   */
  const pause = useCallback(() => {
    setState(prev => {
      if (prev.status === 'playing') {
        return { ...prev, status: 'paused' };
      }
      return prev;
    });
    clearSilenceTimers();
  }, [clearSilenceTimers]);

  /**
   * Go to next section.
   */
  const nextSection = useCallback(() => {
    clearSilenceTimers();
    setState(prev => {
      const nextIndex = prev.currentSectionIndex + 1;
      if (nextIndex < prev.sections.length) {
        onSectionChange?.(nextIndex, prev.sections[nextIndex]);
        return {
          ...prev,
          currentSectionIndex: nextIndex,
          status: 'playing',
        };
      } else {
        onComplete?.();
        return { ...prev, status: 'complete' };
      }
    });
  }, [clearSilenceTimers, onSectionChange, onComplete]);

  /**
   * Go to previous section.
   */
  const previousSection = useCallback(() => {
    clearSilenceTimers();
    setState(prev => {
      const prevIndex = prev.currentSectionIndex - 1;
      if (prevIndex >= 0) {
        onSectionChange?.(prevIndex, prev.sections[prevIndex]);
        return {
          ...prev,
          currentSectionIndex: prevIndex,
          status: 'playing',
        };
      }
      return prev;
    });
  }, [clearSilenceTimers, onSectionChange]);

  /**
   * Go to specific section.
   */
  const goToSection = useCallback((index: number) => {
    clearSilenceTimers();
    setState(prev => {
      if (index >= 0 && index < prev.sections.length) {
        onSectionChange?.(index, prev.sections[index]);
        return {
          ...prev,
          currentSectionIndex: index,
          status: 'playing',
        };
      }
      return prev;
    });
  }, [clearSilenceTimers, onSectionChange]);

  /**
   * Submit a Q&A question.
   * AC#5: Q&A during pause
   */
  const submitQuestion = useCallback(async (question: string) => {
    if (!state.briefingId) return;

    clearSilenceTimers();
    setState(prev => ({ ...prev, status: 'qa' }));

    // Add user question to transcript
    addTranscriptEntry('user', question);

    // Add processing indicator
    addTranscriptEntry('assistant', '', { isProcessing: true });

    try {
      const currentSection = state.sections[state.currentSectionIndex];

      const response = await fetch(`${apiBaseUrl}/${state.briefingId}/qa`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question,
          area_id: currentSection?.area_id,
          user_id: 'current-user', // Should come from auth context
        }),
      });

      if (!response.ok) {
        throw new Error(`Q&A request failed: ${response.status}`);
      }

      const data = await response.json();

      // Update processing entry with actual response
      updateLastTranscriptEntry({
        text: data.answer,
        citations: data.citations,
        isProcessing: false,
      });

      // Add follow-up prompt as system message
      addTranscriptEntry('system', data.follow_up_prompt);

      // Return to awaiting response state (ready for more questions or continue)
      setState(prev => ({ ...prev, status: 'awaiting_response' }));

      // Restart silence detection for auto-continue
      startSilenceDetection();

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to process question';

      // Update processing entry with error
      updateLastTranscriptEntry({
        text: 'I had trouble processing that question. Please try again.',
        isProcessing: false,
      });

      setState(prev => ({ ...prev, status: 'awaiting_response' }));
      onError?.(errorMessage);
    }
  }, [
    state.briefingId,
    state.sections,
    state.currentSectionIndex,
    apiBaseUrl,
    clearSilenceTimers,
    addTranscriptEntry,
    updateLastTranscriptEntry,
    startSilenceDetection,
    onError,
  ]);

  /**
   * Continue after pause.
   * AC#3: User says "No" / "Continue" / "Next"
   */
  const continueAfterPause = useCallback(() => {
    clearSilenceTimers();
    nextSection();
  }, [clearSilenceTimers, nextSection]);

  /**
   * End the briefing session.
   */
  const endBriefing = useCallback(async () => {
    clearSilenceTimers();

    if (state.briefingId) {
      try {
        await fetch(`${apiBaseUrl}/${state.briefingId}/end`, {
          method: 'POST',
        });
      } catch (error) {
        // Ignore errors on end
      }
    }

    setState(prev => ({ ...prev, status: 'complete' }));
    onComplete?.();
  }, [state.briefingId, apiBaseUrl, clearSilenceTimers, onComplete]);

  /**
   * Reset state.
   */
  const reset = useCallback(() => {
    clearSilenceTimers();
    setState(initialState);
  }, [clearSilenceTimers]);

  /**
   * Handle section completion (called when audio ends).
   */
  const handleSectionComplete = useCallback(() => {
    const currentSection = state.sections[state.currentSectionIndex];

    if (currentSection?.pause_point) {
      // AC#2: Pause for Q&A
      setState(prev => ({ ...prev, status: 'awaiting_response' }));

      // Add pause prompt to transcript
      const areaName = currentSection.title || 'this section';
      addTranscriptEntry('system', `Any questions on ${areaName} before I continue?`);

      // Start silence detection
      startSilenceDetection();
    } else {
      // No pause point, continue to next
      nextSection();
    }
  }, [state.sections, state.currentSectionIndex, addTranscriptEntry, startSilenceDetection, nextSection]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clearSilenceTimers();
    };
  }, [clearSilenceTimers]);

  // Actions object
  const actions: BriefingActions = {
    startBriefing,
    play,
    pause,
    nextSection,
    previousSection,
    goToSection,
    submitQuestion,
    continueAfterPause,
    endBriefing,
    reset,
    startSilenceDetection,
    cancelSilenceDetection,
  };

  return [state, actions];
}

export default useBriefing;
