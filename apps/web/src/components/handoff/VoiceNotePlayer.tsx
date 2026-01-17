'use client';

/**
 * VoiceNotePlayer Component (Story 9.3, Task 6)
 *
 * HTML5 audio player for voice note playback with custom controls.
 *
 * AC#3: Multiple Voice Notes Management
 * - Play/pause toggle
 * - Progress bar with seek
 * - Current time / duration display
 * - Fetch audio from Supabase Storage signed URL
 * - Display transcript below audio controls
 *
 * References:
 * - [Source: epic-9.md#Story 9.3]
 * - [Source: prd-functional-requirements.md#FR23]
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { cn } from '@/lib/utils';

// ============================================================================
// Types
// ============================================================================

export interface VoiceNotePlayerProps {
  /** Audio source URL (signed URL from Supabase Storage) */
  src: string;
  /** Optional transcript to display below player */
  transcript?: string | null;
  /** Called when audio playback ends */
  onEnded?: () => void;
  /** Called when there's a playback error */
  onError?: (error: string) => void;
  /** Auto-play on mount */
  autoPlay?: boolean;
  /** Custom class name */
  className?: string;
}

// ============================================================================
// Helper Functions
// ============================================================================

function formatTime(seconds: number): string {
  if (!isFinite(seconds) || seconds < 0) return '0:00';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// ============================================================================
// Component
// ============================================================================

/**
 * VoiceNotePlayer component for audio playback.
 *
 * Story 9.3 Implementation:
 * - AC#3: Provides playback controls for voice notes
 * - Supports seeking, play/pause, and time display
 *
 * Usage:
 * ```tsx
 * <VoiceNotePlayer
 *   src={note.storage_url}
 *   transcript={note.transcript}
 *   onEnded={() => setPlaying(false)}
 * />
 * ```
 */
export function VoiceNotePlayer({
  src,
  transcript,
  onEnded,
  onError,
  autoPlay = false,
  className,
}: VoiceNotePlayerProps) {
  // State
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSeeking, setIsSeeking] = useState(false);

  // Refs
  const audioRef = useRef<HTMLAudioElement>(null);
  const progressRef = useRef<HTMLDivElement>(null);

  // Computed values
  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

  // ============================================================================
  // Event Handlers
  // ============================================================================

  const handleLoadedMetadata = useCallback(() => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration);
      setIsLoading(false);
    }
  }, []);

  const handleTimeUpdate = useCallback(() => {
    if (audioRef.current && !isSeeking) {
      setCurrentTime(audioRef.current.currentTime);
    }
  }, [isSeeking]);

  const handleEnded = useCallback(() => {
    setIsPlaying(false);
    setCurrentTime(0);
    onEnded?.();
  }, [onEnded]);

  const handleError = useCallback(() => {
    setError('Failed to load audio');
    setIsLoading(false);
    onError?.('Failed to load audio');
  }, [onError]);

  const handleCanPlay = useCallback(() => {
    setIsLoading(false);
    setError(null);
  }, []);

  // ============================================================================
  // Control Handlers
  // ============================================================================

  const togglePlay = useCallback(() => {
    if (!audioRef.current) return;

    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play().catch((err) => {
        console.error('Playback failed:', err);
        setError('Playback failed');
      });
    }
    setIsPlaying(!isPlaying);
  }, [isPlaying]);

  const handleSeek = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!audioRef.current || !progressRef.current) return;

    const rect = progressRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = Math.max(0, Math.min(1, x / rect.width));
    const newTime = percentage * duration;

    audioRef.current.currentTime = newTime;
    setCurrentTime(newTime);
  }, [duration]);

  const handleSeekStart = useCallback(() => {
    setIsSeeking(true);
  }, []);

  const handleSeekEnd = useCallback(() => {
    setIsSeeking(false);
  }, []);

  // ============================================================================
  // Effects
  // ============================================================================

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    // Named handlers for proper cleanup
    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);

    audio.addEventListener('loadedmetadata', handleLoadedMetadata);
    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('error', handleError);
    audio.addEventListener('canplay', handleCanPlay);
    audio.addEventListener('play', handlePlay);
    audio.addEventListener('pause', handlePause);

    return () => {
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('error', handleError);
      audio.removeEventListener('canplay', handleCanPlay);
      audio.removeEventListener('play', handlePlay);
      audio.removeEventListener('pause', handlePause);
    };
  }, [handleLoadedMetadata, handleTimeUpdate, handleEnded, handleError, handleCanPlay]);

  // Auto-play effect
  useEffect(() => {
    if (autoPlay && audioRef.current && !isLoading && !error) {
      audioRef.current.play().catch((err) => {
        console.error('Auto-play failed:', err);
        // Auto-play often fails due to browser policies, don't show error
      });
    }
  }, [autoPlay, isLoading, error]);

  // ============================================================================
  // Render
  // ============================================================================

  return (
    <div className={cn('voice-note-player', className)}>
      {/* Hidden audio element */}
      <audio ref={audioRef} src={src} preload="metadata" />

      {/* Error state */}
      {error && (
        <div className="flex items-center gap-2 text-sm text-destructive p-2 bg-destructive/10 rounded">
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <path d="M12 8v4M12 16h.01" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      {/* Player controls */}
      {!error && (
        <div className="flex items-center gap-3">
          {/* Play/Pause button */}
          <button
            type="button"
            onClick={togglePlay}
            disabled={isLoading}
            className={cn(
              'w-10 h-10 rounded-full flex items-center justify-center transition-colors',
              isLoading
                ? 'bg-muted cursor-wait'
                : 'bg-primary hover:bg-primary/90 text-white'
            )}
            aria-label={isPlaying ? 'Pause' : 'Play'}
          >
            {isLoading ? (
              <svg className="w-5 h-5 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" strokeDasharray="32" strokeLinecap="round" />
              </svg>
            ) : isPlaying ? (
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                <rect x="6" y="4" width="4" height="16" rx="1" />
                <rect x="14" y="4" width="4" height="16" rx="1" />
              </svg>
            ) : (
              <svg className="w-5 h-5 ml-0.5" viewBox="0 0 24 24" fill="currentColor">
                <path d="M8 5v14l11-7z" />
              </svg>
            )}
          </button>

          {/* Progress bar and time */}
          <div className="flex-1 flex items-center gap-2">
            {/* Current time */}
            <span className="text-xs text-muted-foreground min-w-[3rem]">
              {formatTime(currentTime)}
            </span>

            {/* Progress bar */}
            <div
              ref={progressRef}
              onClick={handleSeek}
              onMouseDown={handleSeekStart}
              onMouseUp={handleSeekEnd}
              className="flex-1 h-2 bg-muted rounded-full cursor-pointer relative group"
              role="slider"
              aria-label="Seek"
              aria-valuemin={0}
              aria-valuemax={duration}
              aria-valuenow={currentTime}
            >
              {/* Progress fill */}
              <div
                className="absolute inset-y-0 left-0 bg-primary rounded-full transition-all"
                style={{ width: `${progress}%` }}
              />

              {/* Seek handle */}
              <div
                className={cn(
                  'absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-primary rounded-full shadow transition-opacity',
                  'opacity-0 group-hover:opacity-100'
                )}
                style={{ left: `calc(${progress}% - 6px)` }}
              />
            </div>

            {/* Duration */}
            <span className="text-xs text-muted-foreground min-w-[3rem] text-right">
              {formatTime(duration)}
            </span>
          </div>
        </div>
      )}

      {/* Transcript */}
      {transcript && (
        <div className="mt-3 pt-3 border-t">
          <p className="text-sm text-muted-foreground whitespace-pre-wrap">
            {transcript}
          </p>
        </div>
      )}
    </div>
  );
}

export default VoiceNotePlayer;
