'use client';

/**
 * PauseCountdown Component (Story 8.7)
 *
 * Overlay component showing countdown timer for auto-continue during pause.
 * Displays large countdown number with option to continue immediately.
 *
 * AC#2: Pause prompt with countdown timer showing silence detection progress
 *
 * References:
 * - [Source: architecture/voice-briefing.md#Voice Integration Architecture]
 * - [Source: epic-8.md#Story 8.7]
 */

import React from 'react';
import { cn } from '@/lib/utils';
import { type BriefingSection } from '@/lib/hooks/useBriefing';
import { Button } from '@/components/ui/button';

/**
 * PauseCountdown props.
 */
export interface PauseCountdownProps {
  /** Seconds remaining before auto-continue */
  countdown: number;
  /** Next section that will play */
  nextSection?: BriefingSection;
  /** Current section's pause prompt */
  pausePrompt?: string;
  /** Handler for manual continue */
  onContinue?: () => void;
  /** Handler for asking a question */
  onAskQuestion?: () => void;
  /** Whether displayed as overlay or inline */
  overlay?: boolean;
  /** Custom class name */
  className?: string;
}

/**
 * PauseCountdown component for displaying auto-continue countdown.
 *
 * Story 8.7 Implementation:
 * - AC#2: Countdown timer showing silence detection progress
 * - Large countdown number with "Continuing to [Next Area]..."
 * - Manual continue button below countdown
 */
export function PauseCountdown({
  countdown,
  nextSection,
  pausePrompt,
  onContinue,
  onAskQuestion,
  overlay = false,
  className,
}: PauseCountdownProps) {
  // Calculate countdown ring progress (for SVG circle)
  const maxCountdown = 4; // Assuming 4 seconds max
  const progress = (countdown / maxCountdown) * 100;
  const circumference = 2 * Math.PI * 45; // radius = 45
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  const content = (
    <div className="text-center space-y-4">
      {/* Pause prompt */}
      {pausePrompt && (
        <p className={cn(
          'text-lg font-medium',
          overlay ? 'text-white' : 'text-gray-700'
        )}>
          {pausePrompt}
        </p>
      )}

      {/* Countdown circle */}
      <div className="relative inline-flex items-center justify-center">
        {/* Background circle */}
        <svg className="w-28 h-28 transform -rotate-90">
          <circle
            cx="56"
            cy="56"
            r="45"
            stroke={overlay ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.1)'}
            strokeWidth="6"
            fill="none"
          />
          {/* Progress circle */}
          <circle
            cx="56"
            cy="56"
            r="45"
            stroke={overlay ? 'white' : '#3B82F6'}
            strokeWidth="6"
            fill="none"
            strokeLinecap="round"
            style={{
              strokeDasharray: circumference,
              strokeDashoffset,
              transition: 'stroke-dashoffset 0.5s ease-out',
            }}
          />
        </svg>

        {/* Countdown number */}
        <span
          className={cn(
            'absolute text-5xl font-bold tabular-nums',
            overlay ? 'text-white' : 'text-blue-600',
            countdown <= 1 && 'animate-pulse'
          )}
        >
          {countdown}
        </span>
      </div>

      {/* Next section info */}
      <div className={cn(
        'text-sm',
        overlay ? 'text-white/80' : 'text-gray-500'
      )}>
        {nextSection ? (
          <>
            Continuing to <span className="font-semibold">{nextSection.title}</span> in{' '}
            {countdown} second{countdown !== 1 ? 's' : ''}...
          </>
        ) : (
          <>
            Completing briefing in {countdown} second{countdown !== 1 ? 's' : ''}...
          </>
        )}
      </div>

      {/* Action buttons */}
      <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
        <Button
          onClick={onContinue}
          variant={overlay ? 'outline' : 'default'}
          className={cn(
            'min-w-[140px]',
            overlay && 'bg-white text-gray-900 hover:bg-white/90'
          )}
        >
          <svg className="w-4 h-4 mr-2" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 4l-1.41 1.41L16.17 11H4v2h12.17l-5.58 5.59L12 20l8-8z" />
          </svg>
          Continue Now
        </Button>

        {onAskQuestion && (
          <Button
            onClick={onAskQuestion}
            variant="ghost"
            className={cn(
              'min-w-[140px]',
              overlay ? 'text-white hover:bg-white/10' : 'text-gray-600'
            )}
          >
            <svg className="w-4 h-4 mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
              <line x1="12" y1="17" x2="12.01" y2="17" />
            </svg>
            Ask a Question
          </Button>
        )}
      </div>

      {/* Hint text */}
      <p className={cn(
        'text-xs',
        overlay ? 'text-white/60' : 'text-gray-400'
      )}>
        Say &quot;Continue&quot; or press Space to proceed
      </p>
    </div>
  );

  // Overlay mode wraps content in a backdrop
  if (overlay) {
    return (
      <div
        className={cn(
          'fixed inset-0 z-50 flex items-center justify-center',
          'bg-black/60 backdrop-blur-sm',
          className
        )}
        role="dialog"
        aria-modal="true"
        aria-label="Pause countdown"
      >
        <div className="bg-gray-900/80 rounded-2xl p-8 max-w-md mx-4">
          {content}
        </div>
      </div>
    );
  }

  // Inline mode
  return (
    <div
      className={cn(
        'bg-yellow-50 border border-yellow-200 rounded-xl p-6',
        className
      )}
      role="alert"
      aria-live="polite"
    >
      {content}
    </div>
  );
}

export default PauseCountdown;
