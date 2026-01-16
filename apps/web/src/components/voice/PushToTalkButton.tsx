'use client';

/**
 * PushToTalkButton Component (Story 8.2)
 *
 * Press-and-hold button for voice input with visual feedback.
 * Handles recording state, audio level visualization, and error states.
 *
 * AC#1: Push-to-Talk Recording Initiation
 * AC#4: No Speech Detection
 * AC#5: Network Error Handling
 *
 * References:
 * - [Source: architecture/voice-briefing.md#Voice Integration Architecture]
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  PushToTalk,
  createPushToTalk,
  isPushToTalkSupported,
  type RecordingState,
  type STTResult,
  type STTError,
} from '@/lib/voice';

/**
 * PushToTalkButton props.
 */
export interface PushToTalkButtonProps {
  /** Whether the briefing session is active */
  isSessionActive?: boolean;
  /** Callback when transcription is complete */
  onTranscription?: (result: STTResult) => void;
  /** Callback on error */
  onError?: (error: STTError) => void;
  /** Callback when recording state changes */
  onStateChange?: (state: RecordingState) => void;
  /** Whether voice is enabled in user preferences */
  voiceEnabled?: boolean;
  /** WebSocket URL for STT */
  websocketUrl?: string;
  /** Custom class name */
  className?: string;
  /** Disabled state */
  disabled?: boolean;
  /** Size variant */
  size?: 'small' | 'medium' | 'large';
}

/**
 * PushToTalkButton component for voice input.
 *
 * Story 8.2 Implementation:
 * - AC#1: Press-and-hold initiates recording with visual feedback
 * - AC#4: Handles no-speech detection gracefully
 * - AC#5: Handles network errors with retry affordance
 *
 * Usage:
 * ```tsx
 * <PushToTalkButton
 *   isSessionActive={true}
 *   onTranscription={(result) => handleQuestion(result.text)}
 *   onError={(error) => showError(error.message)}
 * />
 * ```
 */
export function PushToTalkButton({
  isSessionActive = true,
  onTranscription,
  onError,
  onStateChange,
  voiceEnabled = true,
  websocketUrl = '/api/v1/voice/stt',
  className = '',
  disabled = false,
  size = 'medium',
}: PushToTalkButtonProps) {
  // State
  const [state, setState] = useState<RecordingState>('idle');
  const [audioLevel, setAudioLevel] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSupported, setIsSupported] = useState(true);
  const [isInitialized, setIsInitialized] = useState(false);

  // Refs
  const pushToTalkRef = useRef<PushToTalk | null>(null);
  const isPressingRef = useRef(false);
  const pressTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * Initialize push-to-talk on mount.
   */
  useEffect(() => {
    // Check browser support
    if (!isPushToTalkSupported()) {
      setIsSupported(false);
      return;
    }

    // Create and initialize push-to-talk
    const ptt = createPushToTalk({
      websocketUrl,
      onTranscription: (result) => {
        setErrorMessage(null);
        onTranscription?.(result);
      },
      onError: (error) => {
        if (error.code === 'no_speech') {
          setErrorMessage('No speech detected');
        } else if (error.code !== 'recording_too_short') {
          setErrorMessage(error.message);
        }
        onError?.(error);
      },
      onStateChange: (newState) => {
        setState(newState);
        onStateChange?.(newState);
      },
      onAudioLevel: (level) => {
        setAudioLevel(level);
      },
    });

    pushToTalkRef.current = ptt;

    // Initialize
    ptt.initialize().then((success) => {
      if (success) {
        setIsInitialized(true);
        // Connect WebSocket
        ptt.connect();
      }
    });

    return () => {
      ptt.disconnect();
    };
  }, [websocketUrl, onTranscription, onError, onStateChange]);

  /**
   * Handle button press start.
   */
  const handlePressStart = useCallback(() => {
    if (disabled || !voiceEnabled || !isSessionActive || !isInitialized) {
      return;
    }

    isPressingRef.current = true;
    setErrorMessage(null);

    // Small delay to prevent accidental taps
    pressTimeoutRef.current = setTimeout(() => {
      if (isPressingRef.current && pushToTalkRef.current) {
        pushToTalkRef.current.startRecording();
      }
    }, 100);
  }, [disabled, voiceEnabled, isSessionActive, isInitialized]);

  /**
   * Handle button press end.
   */
  const handlePressEnd = useCallback(() => {
    isPressingRef.current = false;

    if (pressTimeoutRef.current) {
      clearTimeout(pressTimeoutRef.current);
      pressTimeoutRef.current = null;
    }

    if (pushToTalkRef.current && state === 'recording') {
      pushToTalkRef.current.stopRecording();
    }
  }, [state]);

  /**
   * Handle retry after error.
   */
  const handleRetry = useCallback(() => {
    setErrorMessage(null);
    setState('ready');
  }, []);

  /**
   * Handle keyboard events.
   */
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === ' ' || e.key === 'Enter') {
        e.preventDefault();
        handlePressStart();
      }
    },
    [handlePressStart]
  );

  const handleKeyUp = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === ' ' || e.key === 'Enter') {
        e.preventDefault();
        handlePressEnd();
      }
    },
    [handlePressEnd]
  );

  // Size classes
  const sizeClasses = {
    small: 'w-11 h-11',
    medium: 'w-14 h-14',
    large: 'w-16 h-16',
  };

  const iconSizes = {
    small: 'w-5 h-5',
    medium: 'w-6 h-6',
    large: 'w-7 h-7',
  };

  // State-based styling
  const getButtonClasses = () => {
    const base = `
      push-to-talk-button
      ${sizeClasses[size]}
      rounded-full
      flex items-center justify-center
      transition-all duration-200
      focus:outline-none focus:ring-2 focus:ring-offset-2
      ${className}
    `;

    if (!isSupported || disabled || !voiceEnabled) {
      return `${base} bg-gray-300 cursor-not-allowed opacity-50`;
    }

    switch (state) {
      case 'recording':
        return `${base} bg-red-500 hover:bg-red-600 text-white shadow-lg scale-110 animate-pulse`;
      case 'processing':
        return `${base} bg-yellow-500 text-white cursor-wait`;
      case 'error':
        return `${base} bg-red-100 border-2 border-red-500 text-red-700`;
      case 'requesting_permission':
        return `${base} bg-blue-500 text-white cursor-wait`;
      case 'ready':
      case 'idle':
      default:
        return `${base} bg-blue-600 hover:bg-blue-700 text-white shadow-md hover:shadow-lg active:scale-95`;
    }
  };

  // Render different content based on state
  const renderButtonContent = () => {
    if (!isSupported) {
      return (
        <svg
          className={iconSizes[size]}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path d="M18.36 5.64l-12.73 12.73M5.64 5.64l12.73 12.73" />
        </svg>
      );
    }

    if (state === 'processing') {
      return (
        <svg
          className={`${iconSizes[size]} animate-spin`}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <circle cx="12" cy="12" r="10" strokeDasharray="32" strokeLinecap="round" />
        </svg>
      );
    }

    if (state === 'recording') {
      // Recording indicator with audio level visualization
      return (
        <div className="relative">
          {/* Pulsing ring based on audio level */}
          <div
            className="absolute inset-0 rounded-full bg-white opacity-30"
            style={{
              transform: `scale(${1 + audioLevel * 0.5})`,
              transition: 'transform 100ms ease-out',
            }}
          />
          {/* Microphone icon */}
          <svg
            className={iconSizes[size]}
            viewBox="0 0 24 24"
            fill="currentColor"
          >
            <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
            <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
          </svg>
        </div>
      );
    }

    // Default microphone icon
    return (
      <svg
        className={iconSizes[size]}
        viewBox="0 0 24 24"
        fill="currentColor"
      >
        <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
        <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
      </svg>
    );
  };

  return (
    <div className="push-to-talk-container flex flex-col items-center gap-2">
      {/* Main button */}
      <button
        type="button"
        className={getButtonClasses()}
        onMouseDown={handlePressStart}
        onMouseUp={handlePressEnd}
        onMouseLeave={handlePressEnd}
        onTouchStart={handlePressStart}
        onTouchEnd={handlePressEnd}
        onKeyDown={handleKeyDown}
        onKeyUp={handleKeyUp}
        disabled={disabled || !voiceEnabled || !isSupported}
        aria-label={
          state === 'recording'
            ? 'Recording - release to stop'
            : 'Press and hold to speak'
        }
        aria-pressed={state === 'recording'}
      >
        {renderButtonContent()}
      </button>

      {/* Status text */}
      <div className="text-sm text-center min-h-[1.5rem]">
        {!isSupported && (
          <span className="text-gray-500">Voice not supported</span>
        )}
        {state === 'recording' && (
          <span className="text-red-600 font-medium">Recording...</span>
        )}
        {state === 'processing' && (
          <span className="text-yellow-600">Transcribing...</span>
        )}
        {state === 'requesting_permission' && (
          <span className="text-blue-600">Requesting microphone access...</span>
        )}
        {errorMessage && (
          <span className="text-red-600">{errorMessage}</span>
        )}
      </div>

      {/* Retry button on error */}
      {errorMessage && state !== 'recording' && state !== 'processing' && (
        <button
          type="button"
          className="text-sm text-blue-600 hover:text-blue-800 underline"
          onClick={handleRetry}
        >
          Try again
        </button>
      )}

      {/* Hint text */}
      {state === 'ready' && !errorMessage && (
        <span className="text-xs text-gray-400">
          Press and hold to ask a question
        </span>
      )}
    </div>
  );
}

export default PushToTalkButton;
