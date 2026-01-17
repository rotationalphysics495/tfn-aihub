'use client';

/**
 * VoiceControls Component (Story 8.4, 8.7)
 *
 * Playback controls for voice briefings with Play/Pause/Next/End buttons.
 * Includes section navigation, visual feedback, and keyboard shortcuts.
 *
 * Story 8.4:
 * AC#2: Play/Pause/Next/End Briefing controls
 * AC#3: Area section navigation
 * AC#4: Visual countdown for silence detection
 *
 * Story 8.7:
 * AC#3: Skip to Next functionality
 * AC#4: End Briefing with confirmation
 * Task 4.4: Keyboard shortcuts (Space for pause, Right arrow for skip)
 *
 * References:
 * - [Source: architecture/voice-briefing.md#Voice Integration Architecture]
 * - [Source: epic-8.md#Story 8.7]
 */

import React, { useEffect, useCallback, useState } from 'react';
import { type BriefingStatus, type BriefingSection } from '@/lib/hooks/useBriefing';

/**
 * VoiceControls props.
 */
export interface VoiceControlsProps {
  /** Current briefing status */
  status: BriefingStatus;
  /** Current section index */
  currentSectionIndex: number;
  /** Total number of sections */
  totalSections: number;
  /** Current section data */
  currentSection?: BriefingSection;
  /** Silence countdown (seconds remaining, null if not active) */
  silenceCountdown: number | null;
  /** Handler for play button */
  onPlay?: () => void;
  /** Handler for pause button */
  onPause?: () => void;
  /** Handler for next section */
  onNext?: () => void;
  /** Handler for previous section */
  onPrevious?: () => void;
  /** Handler for end briefing */
  onEnd?: () => void;
  /** Handler for continue after pause */
  onContinue?: () => void;
  /** Custom class name */
  className?: string;
  /** Compact mode */
  compact?: boolean;
  /** Enable keyboard shortcuts (default: true) */
  enableKeyboardShortcuts?: boolean;
  /** Show keyboard shortcut hints */
  showShortcutHints?: boolean;
}

/**
 * VoiceControls component for briefing playback.
 *
 * Story 8.4 Implementation:
 * - AC#2: Play/Pause/Next/End controls
 * - AC#3: Section navigation (skip forward/back)
 * - AC#4: Silence countdown display
 *
 * Story 8.7 Implementation:
 * - AC#3: Skip to Next immediately ends current section
 * - AC#4: End Briefing with confirmation dialog
 * - Task 4.4: Keyboard shortcuts
 */
export function VoiceControls({
  status,
  currentSectionIndex,
  totalSections,
  currentSection,
  silenceCountdown,
  onPlay,
  onPause,
  onNext,
  onPrevious,
  onEnd,
  onContinue,
  className = '',
  compact = false,
  enableKeyboardShortcuts = true,
  showShortcutHints = false,
}: VoiceControlsProps) {
  const isPlaying = status === 'playing';
  const isPaused = status === 'paused';
  const isAwaitingResponse = status === 'awaiting_response';
  const isQA = status === 'qa';
  const isComplete = status === 'complete';
  const isLoading = status === 'loading';

  const canGoBack = currentSectionIndex > 0;
  const canGoForward = currentSectionIndex < totalSections - 1;

  // State for end briefing confirmation dialog
  const [showEndConfirmation, setShowEndConfirmation] = useState(false);

  /**
   * Handle keyboard shortcuts (Story 8.7 Task 4.4)
   * - Space: Pause/Resume or Continue
   * - Right Arrow: Skip to next section
   * - Left Arrow: Go to previous section
   * - Escape: Close confirmation dialog
   */
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      // Don't handle if user is typing in an input
      if (
        event.target instanceof HTMLInputElement ||
        event.target instanceof HTMLTextAreaElement
      ) {
        return;
      }

      switch (event.key) {
        case ' ':
        case 'Spacebar':
          event.preventDefault();
          if (isAwaitingResponse) {
            onContinue?.();
          } else if (isPlaying) {
            onPause?.();
          } else if (isPaused || status === 'idle') {
            onPlay?.();
          }
          break;

        case 'ArrowRight':
          event.preventDefault();
          if (canGoForward && !isLoading) {
            onNext?.();
          } else if (isAwaitingResponse) {
            onContinue?.();
          }
          break;

        case 'ArrowLeft':
          event.preventDefault();
          if (canGoBack && !isLoading) {
            onPrevious?.();
          }
          break;

        case 'Escape':
          if (showEndConfirmation) {
            event.preventDefault();
            setShowEndConfirmation(false);
          }
          break;
      }
    },
    [
      status,
      isPlaying,
      isPaused,
      isAwaitingResponse,
      isLoading,
      canGoBack,
      canGoForward,
      showEndConfirmation,
      onPlay,
      onPause,
      onNext,
      onPrevious,
      onContinue,
    ]
  );

  // Register keyboard event listener
  useEffect(() => {
    if (!enableKeyboardShortcuts) return;

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [enableKeyboardShortcuts, handleKeyDown]);

  /**
   * Handle end briefing with confirmation (Story 8.7 AC#4)
   */
  const handleEndClick = useCallback(() => {
    setShowEndConfirmation(true);
  }, []);

  const handleConfirmEnd = useCallback(() => {
    setShowEndConfirmation(false);
    onEnd?.();
  }, [onEnd]);

  const handleCancelEnd = useCallback(() => {
    setShowEndConfirmation(false);
  }, []);

  // Status text
  const getStatusText = () => {
    switch (status) {
      case 'loading':
        return 'Preparing briefing...';
      case 'playing':
        return currentSection?.title || 'Playing';
      case 'paused':
        return 'Paused';
      case 'awaiting_response':
        return silenceCountdown !== null
          ? `Continuing in ${silenceCountdown}s...`
          : 'Ask a question or say "Continue"';
      case 'qa':
        return 'Processing question...';
      case 'complete':
        return 'Briefing complete';
      case 'error':
        return 'Error occurred';
      default:
        return 'Ready';
    }
  };

  return (
    <div className={`voice-controls ${compact ? 'voice-controls--compact' : ''} ${className}`}>
      {/* Status display */}
      <div className="voice-controls__status flex items-center justify-between mb-3">
        <span className="text-sm font-medium text-gray-700">
          {getStatusText()}
        </span>
        <span className="text-xs text-gray-500">
          Section {currentSectionIndex + 1} of {totalSections}
        </span>
      </div>

      {/* Progress bar */}
      {totalSections > 0 && (
        <div className="voice-controls__progress mb-4">
          <div className="h-1 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-600 transition-all duration-300"
              style={{
                width: `${((currentSectionIndex + 1) / totalSections) * 100}%`,
              }}
            />
          </div>
          {/* Section markers */}
          <div className="flex justify-between mt-1">
            {Array.from({ length: totalSections }).map((_, idx) => (
              <div
                key={idx}
                className={`w-2 h-2 rounded-full ${
                  idx < currentSectionIndex
                    ? 'bg-blue-600'
                    : idx === currentSectionIndex
                    ? 'bg-blue-600 ring-2 ring-blue-200'
                    : 'bg-gray-300'
                }`}
                title={`Section ${idx + 1}`}
              />
            ))}
          </div>
        </div>
      )}

      {/* Silence countdown indicator */}
      {silenceCountdown !== null && isAwaitingResponse && (
        <div className="voice-controls__countdown mb-4">
          <div className="flex items-center justify-center gap-2 py-2 px-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <svg
              className="w-5 h-5 text-yellow-600"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <circle cx="12" cy="12" r="10" />
              <polyline points="12,6 12,12 16,14" />
            </svg>
            <span className="text-sm text-yellow-700">
              Auto-continuing in {silenceCountdown} seconds...
            </span>
            <button
              type="button"
              className="text-xs text-yellow-600 hover:text-yellow-800 underline"
              onClick={onContinue}
            >
              Continue now
            </button>
          </div>
        </div>
      )}

      {/* Main controls */}
      <div className="voice-controls__buttons flex items-center justify-center gap-4">
        {/* Previous button */}
        <button
          type="button"
          className={`
            voice-controls__btn voice-controls__btn--secondary
            p-2 rounded-full transition-all
            ${canGoBack
              ? 'bg-gray-100 hover:bg-gray-200 text-gray-700'
              : 'bg-gray-50 text-gray-300 cursor-not-allowed'
            }
          `}
          onClick={onPrevious}
          disabled={!canGoBack || isLoading}
          aria-label="Previous section"
        >
          <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
            <path d="M6 6h2v12H6zm3.5 6l8.5 6V6z" />
          </svg>
        </button>

        {/* Play/Pause/Continue button */}
        {isAwaitingResponse ? (
          <button
            type="button"
            className="
              voice-controls__btn voice-controls__btn--primary
              w-14 h-14 rounded-full bg-green-600 hover:bg-green-700
              text-white shadow-lg flex items-center justify-center
              transition-all active:scale-95
            "
            onClick={onContinue}
            aria-label="Continue to next section"
          >
            <svg viewBox="0 0 24 24" width="28" height="28" fill="currentColor">
              <path d="M12 4l-1.41 1.41L16.17 11H4v2h12.17l-5.58 5.59L12 20l8-8z" />
            </svg>
          </button>
        ) : (
          <button
            type="button"
            className={`
              voice-controls__btn voice-controls__btn--primary
              w-14 h-14 rounded-full shadow-lg flex items-center justify-center
              transition-all active:scale-95
              ${isPlaying
                ? 'bg-blue-600 hover:bg-blue-700 text-white'
                : isPaused
                ? 'bg-blue-600 hover:bg-blue-700 text-white'
                : isComplete
                ? 'bg-gray-400 text-white cursor-not-allowed'
                : isLoading || isQA
                ? 'bg-blue-400 text-white cursor-wait'
                : 'bg-blue-600 hover:bg-blue-700 text-white'
              }
            `}
            onClick={isPlaying ? onPause : onPlay}
            disabled={isComplete || isLoading || isQA}
            aria-label={isPlaying ? 'Pause' : 'Play'}
          >
            {isLoading || isQA ? (
              <svg
                className="animate-spin"
                viewBox="0 0 24 24"
                width="28"
                height="28"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <circle
                  cx="12"
                  cy="12"
                  r="10"
                  strokeDasharray="32"
                  strokeLinecap="round"
                />
              </svg>
            ) : isPlaying ? (
              <svg viewBox="0 0 24 24" width="28" height="28" fill="currentColor">
                <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
              </svg>
            ) : (
              <svg viewBox="0 0 24 24" width="28" height="28" fill="currentColor">
                <path d="M8 5v14l11-7z" />
              </svg>
            )}
          </button>
        )}

        {/* Next button */}
        <button
          type="button"
          className={`
            voice-controls__btn voice-controls__btn--secondary
            p-2 rounded-full transition-all
            ${canGoForward && !isLoading
              ? 'bg-gray-100 hover:bg-gray-200 text-gray-700'
              : 'bg-gray-50 text-gray-300 cursor-not-allowed'
            }
          `}
          onClick={onNext}
          disabled={!canGoForward || isLoading}
          aria-label="Next section"
        >
          <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
            <path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z" />
          </svg>
        </button>
      </div>

      {/* End briefing button */}
      {!isComplete && (
        <div className="voice-controls__end mt-4 flex justify-center">
          <button
            type="button"
            className="
              text-sm text-gray-500 hover:text-gray-700
              flex items-center gap-1 transition-colors
            "
            onClick={handleEndClick}
            aria-label="End briefing"
          >
            <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
              <path d="M6 6h12v12H6z" />
            </svg>
            End briefing
          </button>
        </div>
      )}

      {/* End Briefing Confirmation Dialog (Story 8.7 AC#4) */}
      {showEndConfirmation && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
          aria-labelledby="end-confirmation-title"
        >
          <div className="bg-white rounded-xl shadow-xl p-6 max-w-sm mx-4">
            <h3
              id="end-confirmation-title"
              className="text-lg font-semibold text-gray-900 mb-2"
            >
              End Briefing?
            </h3>
            <p className="text-sm text-gray-600 mb-6">
              You&apos;ve completed {currentSectionIndex + 1} of {totalSections} sections.
              Your progress will be saved.
            </p>
            <div className="flex justify-end gap-3">
              <button
                type="button"
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                onClick={handleCancelEnd}
                autoFocus
              >
                Continue Briefing
              </button>
              <button
                type="button"
                className="px-4 py-2 text-sm font-medium text-white bg-amber-600 hover:bg-amber-700 rounded-lg transition-colors"
                onClick={handleConfirmEnd}
              >
                End Briefing
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Keyboard Shortcut Hints */}
      {showShortcutHints && !isComplete && (
        <div className="voice-controls__shortcuts mt-4 text-center">
          <div className="inline-flex items-center gap-4 text-xs text-gray-400">
            <span>
              <kbd className="px-1.5 py-0.5 bg-gray-100 rounded border border-gray-200 font-mono">Space</kbd>
              {' '}Pause/Play
            </span>
            <span>
              <kbd className="px-1.5 py-0.5 bg-gray-100 rounded border border-gray-200 font-mono">→</kbd>
              {' '}Skip
            </span>
            <span>
              <kbd className="px-1.5 py-0.5 bg-gray-100 rounded border border-gray-200 font-mono">←</kbd>
              {' '}Previous
            </span>
          </div>
        </div>
      )}

      {/* Completion message */}
      {isComplete && (
        <div className="voice-controls__complete mt-4 text-center">
          <div className="inline-flex items-center gap-2 py-2 px-4 bg-green-50 border border-green-200 rounded-lg">
            <svg
              className="w-5 h-5 text-green-600"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M20 6L9 17l-5-5" />
            </svg>
            <span className="text-sm text-green-700">
              Morning briefing complete
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

export default VoiceControls;
