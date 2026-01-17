'use client';

/**
 * BriefingTranscript Component (Story 8.7)
 *
 * Scrollable transcript panel displaying current section text with auto-scroll.
 * Shows the briefing content as text alongside audio playback.
 *
 * AC#1: Text transcript of current section with auto-scroll
 *
 * References:
 * - [Source: architecture/voice-briefing.md#Voice Integration Architecture]
 * - [Source: epic-8.md#Story 8.7]
 */

import React, { useEffect, useRef } from 'react';
import { cn } from '@/lib/utils';
import { type BriefingSection } from '@/lib/hooks/useBriefing';
import { ScrollArea } from '@/components/ui/scroll-area';

/**
 * BriefingTranscript props.
 */
export interface BriefingTranscriptProps {
  /** Array of briefing sections */
  sections: BriefingSection[];
  /** Current section index */
  currentIndex: number;
  /** Whether to show all sections or only current */
  showAllSections?: boolean;
  /** Maximum height for scrollable area */
  maxHeight?: string;
  /** Custom class name */
  className?: string;
}

/**
 * BriefingTranscript component for displaying briefing text content.
 *
 * Story 8.7 Implementation:
 * - AC#1: Text transcript of current section
 * - Auto-scrolls to current section when it changes
 * - Highlights current section, mutes completed sections
 */
export function BriefingTranscript({
  sections,
  currentIndex,
  showAllSections = true,
  maxHeight = '400px',
  className,
}: BriefingTranscriptProps) {
  // Ref for auto-scrolling to current section
  const currentSectionRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to current section when it changes
  useEffect(() => {
    if (currentSectionRef.current) {
      currentSectionRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      });
    }
  }, [currentIndex]);

  // Get current section for single-section view
  const currentSection = sections[currentIndex];

  // Single section view
  if (!showAllSections) {
    return (
      <div className={cn('briefing-transcript', className)}>
        {currentSection && (
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            {/* Section header */}
            <div className="flex items-center gap-3 mb-4">
              <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-semibold text-sm">
                {currentIndex + 1}
              </div>
              <div>
                <h2 className="text-xl font-semibold text-gray-900">
                  {currentSection.title}
                </h2>
                {currentSection.area_id && (
                  <span className="text-xs text-gray-500">
                    {currentSection.area_id}
                  </span>
                )}
              </div>
            </div>

            {/* Content */}
            <div className="prose prose-gray max-w-none">
              <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                {currentSection.content}
              </p>
            </div>

            {/* Error message if present */}
            {currentSection.error_message && (
              <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                <p className="text-sm text-amber-700">
                  <span className="font-medium">Note:</span>{' '}
                  {currentSection.error_message}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  // Full transcript view with all sections
  return (
    <div className={cn('briefing-transcript', className)}>
      <ScrollArea className="rounded-lg border border-gray-200 bg-white" style={{ maxHeight }}>
        <div className="p-4 space-y-6">
          {sections.map((section, index) => {
            const isCompleted = index < currentIndex;
            const isCurrent = index === currentIndex;
            const isUpcoming = index > currentIndex;

            return (
              <div
                key={`transcript-${index}`}
                ref={isCurrent ? currentSectionRef : undefined}
                className={cn(
                  'transcript-section rounded-lg p-4 transition-all',
                  // Completed: muted
                  isCompleted && 'bg-gray-50 opacity-60',
                  // Current: highlighted
                  isCurrent && 'bg-blue-50 border border-blue-200 ring-2 ring-blue-100',
                  // Upcoming: subtle
                  isUpcoming && 'bg-gray-50/50 opacity-50'
                )}
              >
                {/* Section header */}
                <div className="flex items-center gap-3 mb-3">
                  <div
                    className={cn(
                      'w-7 h-7 rounded-full flex items-center justify-center text-sm font-semibold',
                      isCompleted && 'bg-green-100 text-green-600',
                      isCurrent && 'bg-blue-600 text-white',
                      isUpcoming && 'bg-gray-200 text-gray-500'
                    )}
                  >
                    {isCompleted ? (
                      <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                        <path d="M20 6L9 17l-5-5" />
                      </svg>
                    ) : (
                      index + 1
                    )}
                  </div>
                  <div className="flex-grow">
                    <h3
                      className={cn(
                        'font-semibold',
                        isCompleted && 'text-gray-500',
                        isCurrent && 'text-blue-800',
                        isUpcoming && 'text-gray-400'
                      )}
                    >
                      {section.title}
                    </h3>
                    {section.area_id && (
                      <span
                        className={cn(
                          'text-xs',
                          isCompleted && 'text-gray-400',
                          isCurrent && 'text-blue-600',
                          isUpcoming && 'text-gray-300'
                        )}
                      >
                        {section.area_id}
                      </span>
                    )}
                  </div>
                  {/* Status badge */}
                  {isCompleted && (
                    <span className="px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded-full">
                      Done
                    </span>
                  )}
                  {isCurrent && (
                    <span className="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded-full animate-pulse">
                      Now Playing
                    </span>
                  )}
                </div>

                {/* Content */}
                <p
                  className={cn(
                    'leading-relaxed whitespace-pre-wrap',
                    isCompleted && 'text-gray-500',
                    isCurrent && 'text-gray-800',
                    isUpcoming && 'text-gray-400'
                  )}
                >
                  {section.content}
                </p>

                {/* Error message */}
                {section.error_message && isCurrent && (
                  <div className="mt-3 p-2 bg-amber-50 border border-amber-200 rounded">
                    <p className="text-xs text-amber-700">
                      Note: {section.error_message}
                    </p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </ScrollArea>
    </div>
  );
}

export default BriefingTranscript;
