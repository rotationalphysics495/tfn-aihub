'use client';

/**
 * AreaProgress Component (Story 8.7)
 *
 * Vertical stepper component showing briefing progress through areas.
 * Displays current section highlighted, completed sections with checkmarks,
 * and upcoming sections dimmed.
 *
 * AC#1: Clear visual interface showing briefing progress
 * - Current section name and progress indicator
 * - List of upcoming areas (dimmed)
 * - Completed areas (checked)
 *
 * References:
 * - [Source: architecture/voice-briefing.md#Voice Integration Architecture]
 * - [Source: epic-8.md#Story 8.7]
 */

import React from 'react';
import { cn } from '@/lib/utils';
import { type BriefingSection } from '@/lib/hooks/useBriefing';

/**
 * AreaProgress props.
 */
export interface AreaProgressProps {
  /** Array of briefing sections */
  sections: BriefingSection[];
  /** Index of current section */
  currentIndex: number;
  /** Optional callback when a section is clicked */
  onSectionClick?: (index: number) => void;
  /** Custom class name */
  className?: string;
  /** Compact mode for smaller displays */
  compact?: boolean;
}

/**
 * AreaProgress component for displaying briefing area navigation.
 *
 * Story 8.7 Implementation:
 * - AC#1: Visual progress through briefing areas
 * - Active step: Full color, bold text, pulse indicator
 * - Completed steps: Muted color, checkmark icon
 * - Upcoming steps: Dimmed text, circle indicator
 */
export function AreaProgress({
  sections,
  currentIndex,
  onSectionClick,
  className,
  compact = false,
}: AreaProgressProps) {
  return (
    <div
      className={cn(
        'area-progress',
        compact ? 'space-y-1' : 'space-y-2',
        className
      )}
      role="navigation"
      aria-label="Briefing progress"
    >
      {/* Progress header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-700">
          Briefing Progress
        </h3>
        <span className="text-xs text-gray-500">
          {currentIndex + 1} of {sections.length}
        </span>
      </div>

      {/* Vertical stepper */}
      <ol className="relative" aria-label="Section list">
        {sections.map((section, index) => {
          const isCompleted = index < currentIndex;
          const isCurrent = index === currentIndex;
          const isUpcoming = index > currentIndex;

          return (
            <li
              key={`section-${index}`}
              className={cn(
                'relative flex items-start gap-3',
                compact ? 'pb-3' : 'pb-4',
                // Connection line (except for last item)
                index < sections.length - 1 &&
                  'before:absolute before:left-[11px] before:top-6 before:h-full before:w-0.5',
                isCompleted && 'before:bg-green-300',
                isCurrent && 'before:bg-blue-200',
                isUpcoming && 'before:bg-gray-200'
              )}
            >
              {/* Step indicator */}
              <div
                className={cn(
                  'relative z-10 flex-shrink-0 flex items-center justify-center rounded-full transition-all',
                  compact ? 'w-5 h-5' : 'w-6 h-6',
                  // Completed state
                  isCompleted && 'bg-green-500 text-white',
                  // Current state with pulse
                  isCurrent &&
                    'bg-blue-600 text-white ring-4 ring-blue-100 animate-pulse',
                  // Upcoming state
                  isUpcoming && 'bg-gray-200 text-gray-400 border-2 border-gray-300'
                )}
                aria-current={isCurrent ? 'step' : undefined}
              >
                {isCompleted ? (
                  // Checkmark for completed
                  <svg
                    className={compact ? 'w-3 h-3' : 'w-3.5 h-3.5'}
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="3"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M20 6L9 17l-5-5" />
                  </svg>
                ) : (
                  // Number for current/upcoming
                  <span className={cn('font-semibold', compact ? 'text-xs' : 'text-xs')}>
                    {index + 1}
                  </span>
                )}
              </div>

              {/* Section content */}
              <button
                type="button"
                onClick={() => onSectionClick?.(index)}
                disabled={!onSectionClick}
                className={cn(
                  'flex-grow text-left transition-all',
                  onSectionClick && 'cursor-pointer hover:bg-gray-50 -mx-2 px-2 py-1 rounded-md',
                  !onSectionClick && 'cursor-default'
                )}
              >
                <div
                  className={cn(
                    'font-medium transition-colors',
                    compact ? 'text-sm' : 'text-base',
                    // Completed: muted
                    isCompleted && 'text-gray-500',
                    // Current: emphasized
                    isCurrent && 'text-blue-700 font-semibold',
                    // Upcoming: dimmed
                    isUpcoming && 'text-gray-400'
                  )}
                >
                  {section.title}
                </div>

                {/* Section type badge for current */}
                {isCurrent && section.section_type && (
                  <span className="inline-block mt-1 px-2 py-0.5 text-xs bg-blue-100 text-blue-600 rounded-full">
                    {section.section_type}
                  </span>
                )}

                {/* Area ID for non-compact mode */}
                {!compact && section.area_id && (
                  <div
                    className={cn(
                      'text-xs mt-0.5',
                      isCompleted && 'text-gray-400',
                      isCurrent && 'text-blue-500',
                      isUpcoming && 'text-gray-300'
                    )}
                  >
                    {section.area_id}
                  </div>
                )}

                {/* Status indicators */}
                {isCompleted && (
                  <span className="text-xs text-green-500 mt-0.5 flex items-center gap-1">
                    <svg className="w-3 h-3" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
                    </svg>
                    Completed
                  </span>
                )}
              </button>
            </li>
          );
        })}
      </ol>

      {/* Progress bar */}
      {sections.length > 0 && (
        <div className="mt-4">
          <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-green-500 to-blue-500 transition-all duration-500"
              style={{
                width: `${((currentIndex + 1) / sections.length) * 100}%`,
              }}
            />
          </div>
          <div className="flex justify-between mt-1 text-xs text-gray-500">
            <span>Start</span>
            <span>
              {Math.round(((currentIndex + 1) / sections.length) * 100)}% complete
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

export default AreaProgress;
