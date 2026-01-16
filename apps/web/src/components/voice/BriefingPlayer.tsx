'use client';

/**
 * BriefingPlayer Component (Story 8.1)
 *
 * Dual delivery component for voice briefings with text transcript.
 * Displays text content while playing audio, with pause points between sections.
 *
 * AC#1: TTS Stream URL Generation - Plays audio from generated URLs
 * AC#3: Section Pause Points - Pauses at section boundaries
 *
 * References:
 * - [Source: architecture/voice-briefing.md#Voice Integration Architecture]
 * - [Source: prd/prd-functional-requirements.md#FR13]
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  ElevenLabsClient,
  createElevenLabsClient,
  AudioUtils,
  setupAutoplayUnlock,
} from '@/lib/voice';

/**
 * Briefing section data structure.
 */
export interface BriefingSection {
  id: string;
  title: string;
  content: string;
  areaId?: string;
  audioStreamUrl?: string | null;
  durationEstimateMs?: number | null;
}

/**
 * BriefingPlayer props.
 */
export interface BriefingPlayerProps {
  /** Briefing sections to display/play */
  sections: BriefingSection[];
  /** Global audio stream URL (if single audio for all sections) */
  audioStreamUrl?: string | null;
  /** Callback when a section completes */
  onSectionComplete?: (sectionIndex: number) => void;
  /** Callback when all sections complete */
  onComplete?: () => void;
  /** Callback on error */
  onError?: (error: Error) => void;
  /** Auto-play when component mounts */
  autoPlay?: boolean;
  /** Show playback controls */
  showControls?: boolean;
  /** Initial volume (0-1) */
  initialVolume?: number;
  /** Pause duration between sections in ms */
  pauseDurationMs?: number;
  /** Custom class name */
  className?: string;
}

/**
 * Playback state for the player.
 */
interface PlayerState {
  currentSectionIndex: number;
  isPlaying: boolean;
  isPaused: boolean;
  isLoading: boolean;
  volume: number;
  isMuted: boolean;
  currentTime: number;
  duration: number;
  error: Error | null;
}

/**
 * BriefingPlayer component for dual voice/text delivery.
 *
 * Story 8.1 Implementation:
 * - AC#1: Plays audio from streaming URLs
 * - AC#3: Emits onSectionComplete at pause points
 * - Text is always visible, audio plays if URL provided
 */
export function BriefingPlayer({
  sections,
  audioStreamUrl,
  onSectionComplete,
  onComplete,
  onError,
  autoPlay = false,
  showControls = true,
  initialVolume = 1.0,
  pauseDurationMs = 1500,
  className = '',
}: BriefingPlayerProps) {
  // Player state
  const [state, setState] = useState<PlayerState>({
    currentSectionIndex: 0,
    isPlaying: false,
    isPaused: false,
    isLoading: false,
    volume: initialVolume,
    isMuted: false,
    currentTime: 0,
    duration: 0,
    error: null,
  });

  // Audio client ref
  const clientRef = useRef<ElevenLabsClient | null>(null);
  const pauseTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const audioUnlockedRef = useRef(false);

  // Get current section
  const currentSection = sections[state.currentSectionIndex];
  const hasAudio = !!(
    audioStreamUrl ||
    sections.some((s) => s.audioStreamUrl)
  );

  /**
   * Initialize audio client.
   */
  useEffect(() => {
    clientRef.current = createElevenLabsClient();

    // Set up autoplay unlock
    const cleanup = setupAutoplayUnlock(() => {
      audioUnlockedRef.current = true;
    });

    return () => {
      cleanup();
      clientRef.current?.stop();
    };
  }, []);

  /**
   * Handle section audio completion (AC#3: pause points).
   */
  const handleSectionComplete = useCallback(
    (sectionIndex: number) => {
      // Clear any existing pause timeout
      if (pauseTimeoutRef.current) {
        clearTimeout(pauseTimeoutRef.current);
      }

      // Emit callback
      onSectionComplete?.(sectionIndex);

      // Check if there are more sections
      const nextIndex = sectionIndex + 1;
      if (nextIndex < sections.length) {
        // Pause between sections
        setState((prev) => ({ ...prev, isPaused: true }));

        pauseTimeoutRef.current = setTimeout(() => {
          // Move to next section
          setState((prev) => ({
            ...prev,
            currentSectionIndex: nextIndex,
            isPaused: false,
          }));
        }, pauseDurationMs);
      } else {
        // All sections complete
        setState((prev) => ({
          ...prev,
          isPlaying: false,
          isPaused: false,
        }));
        onComplete?.();
      }
    },
    [sections.length, pauseDurationMs, onSectionComplete, onComplete]
  );

  /**
   * Play current section's audio.
   */
  const playSection = useCallback(
    async (sectionIndex: number) => {
      const client = clientRef.current;
      if (!client) return;

      const section = sections[sectionIndex];
      const url = section.audioStreamUrl || audioStreamUrl;

      if (!url) {
        // No audio, just emit completion
        handleSectionComplete(sectionIndex);
        return;
      }

      setState((prev) => ({ ...prev, isLoading: true, error: null }));

      try {
        // Set up event handlers
        client.onComplete = () => handleSectionComplete(sectionIndex);
        client.onError = (error) => {
          setState((prev) => ({ ...prev, error, isPlaying: false }));
          onError?.(error);
        };
        client.onTimeUpdate = (currentTime, duration) => {
          setState((prev) => ({ ...prev, currentTime, duration }));
        };

        await client.playStream(url);
        setState((prev) => ({
          ...prev,
          isPlaying: true,
          isLoading: false,
        }));
      } catch (error) {
        const err = error instanceof Error ? error : new Error(String(error));
        setState((prev) => ({
          ...prev,
          error: err,
          isLoading: false,
          isPlaying: false,
        }));
        onError?.(err);
      }
    },
    [sections, audioStreamUrl, handleSectionComplete, onError]
  );

  /**
   * Auto-play on mount if enabled.
   */
  useEffect(() => {
    if (autoPlay && audioUnlockedRef.current && hasAudio) {
      playSection(0);
    }
  }, [autoPlay, hasAudio, playSection]);

  /**
   * Play button handler.
   */
  const handlePlay = useCallback(() => {
    const client = clientRef.current;

    if (state.isPaused && client) {
      client.resume();
      setState((prev) => ({ ...prev, isPlaying: true, isPaused: false }));
    } else if (!state.isPlaying) {
      playSection(state.currentSectionIndex);
    }
  }, [state.isPaused, state.isPlaying, state.currentSectionIndex, playSection]);

  /**
   * Pause button handler.
   */
  const handlePause = useCallback(() => {
    const client = clientRef.current;

    if (client && state.isPlaying) {
      client.pause();
      setState((prev) => ({ ...prev, isPlaying: false, isPaused: true }));
    }
  }, [state.isPlaying]);

  /**
   * Toggle play/pause.
   */
  const handleTogglePlayPause = useCallback(() => {
    if (state.isPlaying) {
      handlePause();
    } else {
      handlePlay();
    }
  }, [state.isPlaying, handlePlay, handlePause]);

  /**
   * Volume change handler.
   */
  const handleVolumeChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const volume = parseFloat(e.target.value);
      clientRef.current?.setVolume(volume);
      setState((prev) => ({ ...prev, volume }));
    },
    []
  );

  /**
   * Mute toggle handler.
   */
  const handleToggleMute = useCallback(() => {
    clientRef.current?.toggleMute();
    setState((prev) => ({ ...prev, isMuted: !prev.isMuted }));
  }, []);

  /**
   * Skip to next section.
   */
  const handleSkipNext = useCallback(() => {
    const nextIndex = state.currentSectionIndex + 1;
    if (nextIndex < sections.length) {
      clientRef.current?.stop();
      setState((prev) => ({ ...prev, currentSectionIndex: nextIndex }));
      if (state.isPlaying) {
        playSection(nextIndex);
      }
    }
  }, [state.currentSectionIndex, state.isPlaying, sections.length, playSection]);

  /**
   * Skip to previous section.
   */
  const handleSkipPrevious = useCallback(() => {
    const prevIndex = state.currentSectionIndex - 1;
    if (prevIndex >= 0) {
      clientRef.current?.stop();
      setState((prev) => ({ ...prev, currentSectionIndex: prevIndex }));
      if (state.isPlaying) {
        playSection(prevIndex);
      }
    }
  }, [state.currentSectionIndex, state.isPlaying, playSection]);

  /**
   * Go to specific section.
   */
  const handleGoToSection = useCallback(
    (index: number) => {
      if (index >= 0 && index < sections.length) {
        clientRef.current?.stop();
        setState((prev) => ({ ...prev, currentSectionIndex: index }));
        if (state.isPlaying) {
          playSection(index);
        }
      }
    },
    [sections.length, state.isPlaying, playSection]
  );

  /**
   * Calculate progress percentage.
   */
  const progress = AudioUtils.getProgress(state.currentTime, state.duration);

  return (
    <div className={`briefing-player ${className}`}>
      {/* Error display */}
      {state.error && (
        <div className="briefing-player__error" role="alert">
          <span className="briefing-player__error-icon">!</span>
          <span>{state.error.message}</span>
        </div>
      )}

      {/* Section list / transcript */}
      <div className="briefing-player__sections">
        {sections.map((section, index) => (
          <div
            key={section.id}
            className={`briefing-player__section ${
              index === state.currentSectionIndex
                ? 'briefing-player__section--active'
                : ''
            } ${
              index < state.currentSectionIndex
                ? 'briefing-player__section--completed'
                : ''
            }`}
            onClick={() => handleGoToSection(index)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                handleGoToSection(index);
              }
            }}
          >
            <div className="briefing-player__section-header">
              <span className="briefing-player__section-number">
                {index + 1}
              </span>
              <h3 className="briefing-player__section-title">{section.title}</h3>
              {section.areaId && (
                <span className="briefing-player__section-area">
                  {section.areaId}
                </span>
              )}
            </div>
            <p className="briefing-player__section-content">{section.content}</p>
          </div>
        ))}
      </div>

      {/* Playback controls */}
      {showControls && hasAudio && (
        <div className="briefing-player__controls">
          {/* Progress bar */}
          <div className="briefing-player__progress">
            <div
              className="briefing-player__progress-bar"
              style={{ width: `${progress}%` }}
            />
          </div>

          {/* Time display */}
          <div className="briefing-player__time">
            <span>{AudioUtils.formatTime(state.currentTime)}</span>
            <span>/</span>
            <span>{AudioUtils.formatTime(state.duration)}</span>
          </div>

          {/* Control buttons */}
          <div className="briefing-player__buttons">
            {/* Previous */}
            <button
              className="briefing-player__btn briefing-player__btn--skip"
              onClick={handleSkipPrevious}
              disabled={state.currentSectionIndex === 0}
              aria-label="Previous section"
            >
              <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                <path d="M6 6h2v12H6zm3.5 6l8.5 6V6z" />
              </svg>
            </button>

            {/* Play/Pause */}
            <button
              className="briefing-player__btn briefing-player__btn--play"
              onClick={handleTogglePlayPause}
              disabled={state.isLoading}
              aria-label={state.isPlaying ? 'Pause' : 'Play'}
            >
              {state.isLoading ? (
                <svg
                  viewBox="0 0 24 24"
                  width="24"
                  height="24"
                  fill="currentColor"
                  className="animate-spin"
                >
                  <circle
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="2"
                    fill="none"
                    strokeDasharray="32"
                    strokeLinecap="round"
                  />
                </svg>
              ) : state.isPlaying ? (
                <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
                  <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
                </svg>
              ) : (
                <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
                  <path d="M8 5v14l11-7z" />
                </svg>
              )}
            </button>

            {/* Next */}
            <button
              className="briefing-player__btn briefing-player__btn--skip"
              onClick={handleSkipNext}
              disabled={state.currentSectionIndex === sections.length - 1}
              aria-label="Next section"
            >
              <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                <path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z" />
              </svg>
            </button>
          </div>

          {/* Volume controls */}
          <div className="briefing-player__volume">
            <button
              className="briefing-player__btn briefing-player__btn--mute"
              onClick={handleToggleMute}
              aria-label={state.isMuted ? 'Unmute' : 'Mute'}
            >
              {state.isMuted || state.volume === 0 ? (
                <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                  <path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z" />
                </svg>
              ) : (
                <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                  <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z" />
                </svg>
              )}
            </button>
            <input
              type="range"
              className="briefing-player__volume-slider"
              min="0"
              max="1"
              step="0.1"
              value={state.volume}
              onChange={handleVolumeChange}
              aria-label="Volume"
            />
          </div>

          {/* Section indicator */}
          <div className="briefing-player__section-indicator">
            Section {state.currentSectionIndex + 1} of {sections.length}
          </div>
        </div>
      )}

      {/* Fallback message when no audio */}
      {!hasAudio && (
        <div className="briefing-player__fallback">
          <span>Voice temporarily unavailable - showing text</span>
        </div>
      )}
    </div>
  );
}

export default BriefingPlayer;
