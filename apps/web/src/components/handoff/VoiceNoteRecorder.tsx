'use client';

/**
 * VoiceNoteRecorder Component (Story 9.3, Task 4)
 *
 * Push-to-talk voice note recording for shift handoffs.
 * Reuses push-to-talk infrastructure from Story 8.2.
 *
 * AC#1: Voice Note Recording Initiation
 * AC#2: Recording Completion and Transcription
 * AC#4: Recording Error Handling
 *
 * References:
 * - [Source: architecture/voice-briefing.md#Voice Integration Architecture]
 * - [Source: epic-9.md#Story 9.3]
 * - [Source: prd-functional-requirements.md#FR23 Voice Note Support]
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { isPushToTalkSupported } from '@/lib/voice';
import { createClient } from '@/lib/supabase/client';

// ============================================================================
// Types
// ============================================================================

export interface VoiceNote {
  id: string;
  handoff_id: string;
  user_id: string;
  storage_path: string;
  storage_url: string | null;
  transcript: string | null;
  duration_seconds: number;
  sequence_order: number;
  created_at: string;
}

type RecorderState =
  | 'idle'
  | 'requesting_permission'
  | 'ready'
  | 'recording'
  | 'uploading'
  | 'transcribing'
  | 'complete'
  | 'error';

export interface VoiceNoteRecorderProps {
  /** Handoff ID to attach note to */
  handoffId: string;
  /** Called when note successfully recorded and transcribed */
  onNoteAdded: (note: VoiceNote) => void;
  /** Called on recording error */
  onError: (error: string) => void;
  /** Whether max notes limit reached */
  disabled?: boolean;
  /** Current note count */
  noteCount?: number;
  /** Maximum notes allowed */
  maxNotes?: number;
  /** Custom class name */
  className?: string;
}

// Constants
const MAX_DURATION_SECONDS = 60;
const MAX_NOTES = 5;

// ============================================================================
// Helper Functions
// ============================================================================

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// ============================================================================
// Component
// ============================================================================

/**
 * VoiceNoteRecorder component for recording voice notes.
 *
 * Story 9.3 Implementation:
 * - AC#1: Press-and-hold initiates recording with visual feedback
 * - AC#2: Auto-transcribes and attaches to handoff on release
 * - AC#4: Handles permission and upload errors gracefully
 *
 * Usage:
 * ```tsx
 * <VoiceNoteRecorder
 *   handoffId={handoffId}
 *   onNoteAdded={(note) => addToList(note)}
 *   onError={(error) => showToast(error)}
 *   noteCount={2}
 * />
 * ```
 */
export function VoiceNoteRecorder({
  handoffId,
  onNoteAdded,
  onError,
  disabled = false,
  noteCount = 0,
  maxNotes = MAX_NOTES,
  className,
}: VoiceNoteRecorderProps) {
  // State
  const [state, setState] = useState<RecorderState>('idle');
  const [audioLevel, setAudioLevel] = useState(0);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSupported, setIsSupported] = useState(true);
  const [isInitialized, setIsInitialized] = useState(false);

  // Refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const isPressingRef = useRef(false);
  const pressTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const durationIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const recordingStartTimeRef = useRef<number>(0);
  const stateRef = useRef<RecorderState>(state);
  stateRef.current = state; // Keep ref in sync with state

  const isLimitReached = noteCount >= maxNotes;
  const isDisabled = disabled || isLimitReached || !isSupported;

  // ============================================================================
  // Initialize Recording
  // ============================================================================

  useEffect(() => {
    // Check browser support
    if (!isPushToTalkSupported()) {
      setIsSupported(false);
      return;
    }

    setState('ready');
    setIsInitialized(true);

    return () => {
      // Cleanup
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
      }
      if (pressTimeoutRef.current) {
        clearTimeout(pressTimeoutRef.current);
      }
    };
  }, []);

  // ============================================================================
  // Recording Functions
  // ============================================================================

  const startRecording = useCallback(async () => {
    if (isDisabled || !isInitialized) return;

    setState('requesting_permission');
    setErrorMessage(null);
    audioChunksRef.current = [];

    try {
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });

      // Find supported MIME type
      const mimeTypes = [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/ogg;codecs=opus',
        'audio/mp4',
      ];
      const mimeType = mimeTypes.find(type => MediaRecorder.isTypeSupported(type)) || 'audio/webm';

      // Create MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType,
        audioBitsPerSecond: 128000,
      });

      mediaRecorderRef.current = mediaRecorder;

      // Handle data
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      // Handle stop
      mediaRecorder.onstop = async () => {
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());

        // Calculate duration
        const duration = Math.round((Date.now() - recordingStartTimeRef.current) / 1000);

        // Clear duration interval
        if (durationIntervalRef.current) {
          clearInterval(durationIntervalRef.current);
          durationIntervalRef.current = null;
        }

        // Check if we have audio
        if (audioChunksRef.current.length === 0) {
          setState('ready');
          return;
        }

        // Create audio blob
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });

        // Upload the recording
        await uploadRecording(audioBlob, duration);
      };

      // Handle error
      mediaRecorder.onerror = () => {
        setState('error');
        setErrorMessage('Recording failed');
        stream.getTracks().forEach(track => track.stop());
      };

      // Start recording
      recordingStartTimeRef.current = Date.now();
      setRecordingDuration(0);
      mediaRecorder.start(100); // 100ms chunks
      setState('recording');

      // Start duration timer
      durationIntervalRef.current = setInterval(() => {
        const elapsed = Math.floor((Date.now() - recordingStartTimeRef.current) / 1000);
        setRecordingDuration(elapsed);

        // Auto-stop at max duration
        if (elapsed >= MAX_DURATION_SECONDS) {
          stopRecording();
        }
      }, 1000);

      // Set up audio level monitoring
      setupAudioLevelMonitoring(stream);

    } catch (error) {
      setState('error');
      if (error instanceof DOMException && error.name === 'NotAllowedError') {
        setErrorMessage('Microphone access required. You can add text notes instead.');
        onError('Microphone access required. You can add text notes instead.');
      } else {
        const msg = error instanceof Error ? error.message : 'Failed to start recording';
        setErrorMessage(msg);
        onError(msg);
      }
    }
  }, [isDisabled, isInitialized, onError]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
  }, []);

  const setupAudioLevelMonitoring = useCallback((stream: MediaStream) => {
    try {
      const audioContext = new AudioContext();
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);

      const dataArray = new Uint8Array(analyser.frequencyBinCount);

      const updateLevel = () => {
        // Use ref to avoid stale closure
        if (stateRef.current !== 'recording') return;

        analyser.getByteFrequencyData(dataArray);
        const sum = dataArray.reduce((a, b) => a + b, 0);
        const average = sum / dataArray.length;
        setAudioLevel(average / 255);

        requestAnimationFrame(updateLevel);
      };

      updateLevel();
    } catch (error) {
      console.warn('Failed to set up audio level monitoring:', error);
    }
  }, []);

  // ============================================================================
  // Upload Function
  // ============================================================================

  const uploadRecording = async (audioBlob: Blob, duration: number) => {
    setState('uploading');

    try {
      // Get auth token
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();

      if (!session?.access_token) {
        throw new Error('Not authenticated');
      }

      // Create form data
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');
      formData.append('duration_seconds', duration.toString());

      setState('transcribing');

      // Upload to API
      const response = await fetch(`/api/v1/handoff/${handoffId}/voice-notes`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMsg = errorData.detail?.error || errorData.detail || 'Upload failed';
        throw new Error(errorMsg);
      }

      const data = await response.json();

      setState('complete');
      onNoteAdded(data.note);

      // Reset to ready after a moment
      setTimeout(() => {
        setState('ready');
        setRecordingDuration(0);
        setAudioLevel(0);
      }, 1500);

    } catch (error) {
      setState('error');
      const msg = error instanceof Error ? error.message : 'Upload failed. Tap to retry.';
      setErrorMessage(msg);
      onError(msg);
    }
  };

  // ============================================================================
  // Press Handlers
  // ============================================================================

  const handlePressStart = useCallback(() => {
    if (isDisabled || state === 'uploading' || state === 'transcribing') {
      return;
    }

    isPressingRef.current = true;
    setErrorMessage(null);

    // Small delay to prevent accidental taps
    pressTimeoutRef.current = setTimeout(() => {
      if (isPressingRef.current) {
        startRecording();
      }
    }, 100);
  }, [isDisabled, state, startRecording]);

  const handlePressEnd = useCallback(() => {
    isPressingRef.current = false;

    if (pressTimeoutRef.current) {
      clearTimeout(pressTimeoutRef.current);
      pressTimeoutRef.current = null;
    }

    if (state === 'recording') {
      stopRecording();
    }
  }, [state, stopRecording]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === ' ' || e.key === 'Enter') {
      e.preventDefault();
      handlePressStart();
    }
  }, [handlePressStart]);

  const handleKeyUp = useCallback((e: React.KeyboardEvent) => {
    if (e.key === ' ' || e.key === 'Enter') {
      e.preventDefault();
      handlePressEnd();
    }
  }, [handlePressEnd]);

  const handleRetry = useCallback(() => {
    setErrorMessage(null);
    setState('ready');
    setRecordingDuration(0);
    setAudioLevel(0);
  }, []);

  // ============================================================================
  // Render
  // ============================================================================

  const getButtonClasses = () => {
    const base = `
      w-16 h-16 rounded-full flex items-center justify-center
      transition-all duration-200 focus:outline-none focus:ring-2
      focus:ring-offset-2 touch-target
    `;

    if (isDisabled) {
      return cn(base, 'bg-muted cursor-not-allowed opacity-50');
    }

    switch (state) {
      case 'recording':
        return cn(base, 'bg-red-500 hover:bg-red-600 text-white shadow-lg scale-110');
      case 'uploading':
      case 'transcribing':
        return cn(base, 'bg-yellow-500 text-white cursor-wait');
      case 'complete':
        return cn(base, 'bg-green-500 text-white');
      case 'error':
        return cn(base, 'bg-red-100 border-2 border-destructive text-destructive');
      case 'requesting_permission':
        return cn(base, 'bg-blue-500 text-white cursor-wait');
      case 'ready':
      case 'idle':
      default:
        return cn(base, 'bg-primary hover:bg-primary/90 text-white shadow-md hover:shadow-lg active:scale-95');
    }
  };

  const renderButtonContent = () => {
    if (!isSupported) {
      return (
        <svg className="w-7 h-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M18.36 5.64l-12.73 12.73M5.64 5.64l12.73 12.73" />
        </svg>
      );
    }

    if (state === 'uploading' || state === 'transcribing') {
      return (
        <svg className="w-7 h-7 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" strokeDasharray="32" strokeLinecap="round" />
        </svg>
      );
    }

    if (state === 'complete') {
      return (
        <svg className="w-7 h-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      );
    }

    if (state === 'recording') {
      // Recording indicator with audio level visualization
      return (
        <div className="relative">
          <div
            className="absolute inset-0 rounded-full bg-white opacity-30"
            style={{
              transform: `scale(${1 + audioLevel * 0.5})`,
              transition: 'transform 100ms ease-out',
            }}
          />
          <svg className="w-7 h-7" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
            <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
          </svg>
        </div>
      );
    }

    // Default microphone icon
    return (
      <svg className="w-7 h-7" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
        <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
      </svg>
    );
  };

  const remainingTime = MAX_DURATION_SECONDS - recordingDuration;
  const showCountdown = state === 'recording' && remainingTime <= 10;

  return (
    <div className={cn('flex flex-col items-center gap-3', className)}>
      {/* Limit indicator */}
      {isLimitReached && (
        <div className="text-sm text-muted-foreground">
          Maximum {maxNotes} voice notes reached
        </div>
      )}

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
        disabled={isDisabled || state === 'uploading' || state === 'transcribing'}
        aria-label={
          state === 'recording'
            ? `Recording - ${recordingDuration}s - release to stop`
            : 'Press and hold to record voice note'
        }
        aria-pressed={state === 'recording'}
      >
        {renderButtonContent()}
      </button>

      {/* Status text and countdown */}
      <div className="text-sm text-center min-h-[1.5rem]">
        {!isSupported && (
          <span className="text-muted-foreground">Voice recording not supported</span>
        )}
        {state === 'recording' && (
          <div className="flex flex-col items-center">
            <span className={cn(
              'font-medium',
              showCountdown ? 'text-red-600 animate-pulse' : 'text-red-600'
            )}>
              Recording {formatDuration(recordingDuration)}
            </span>
            {showCountdown && (
              <span className="text-xs text-red-500">
                {remainingTime}s remaining
              </span>
            )}
          </div>
        )}
        {state === 'uploading' && (
          <span className="text-yellow-600">Uploading...</span>
        )}
        {state === 'transcribing' && (
          <span className="text-yellow-600">Transcribing...</span>
        )}
        {state === 'complete' && (
          <span className="text-green-600">Voice note saved!</span>
        )}
        {state === 'requesting_permission' && (
          <span className="text-blue-600">Requesting microphone access...</span>
        )}
        {errorMessage && (
          <span className="text-destructive">{errorMessage}</span>
        )}
      </div>

      {/* Retry button on error */}
      {errorMessage && state === 'error' && (
        <Button
          variant="outline"
          size="sm"
          onClick={handleRetry}
        >
          Try again
        </Button>
      )}

      {/* Hint text */}
      {state === 'ready' && !errorMessage && !isLimitReached && (
        <span className="text-xs text-muted-foreground">
          Press and hold to record (max {MAX_DURATION_SECONDS}s)
        </span>
      )}
    </div>
  );
}

export default VoiceNoteRecorder;
