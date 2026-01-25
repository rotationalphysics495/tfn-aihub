'use client';

/**
 * Briefing Playback Page (Story 8.7)
 *
 * Dynamic route for playing a specific briefing with full UI:
 * - Area-by-area progress stepper
 * - Text transcript with auto-scroll
 * - Voice controls with keyboard shortcuts
 * - Pause countdown overlay
 *
 * AC#1: Clear visual interface showing briefing progress
 * AC#2: Pause prompt with countdown timer
 * AC#3: Skip to Next functionality
 * AC#4: End Briefing with confirmation and partial completion tracking
 *
 * References:
 * - [Source: architecture/voice-briefing.md#Voice Integration Architecture]
 * - [Source: epic-8.md#Story 8.7]
 */

import React, { useEffect, useCallback, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useBriefing, type BriefingSection } from '@/lib/hooks/useBriefing';
import { AreaProgress } from '@/components/voice/AreaProgress';
import { BriefingTranscript } from '@/components/voice/BriefingTranscript';
import { VoiceControls } from '@/components/voice/VoiceControls';
import { PauseCountdown } from '@/components/voice/PauseCountdown';
import { PushToTalkButton } from '@/components/voice/PushToTalkButton';
import { TranscriptPanel, type TranscriptEntry } from '@/components/voice/TranscriptPanel';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

/**
 * Session storage key for tracking partial completion.
 */
const PARTIAL_COMPLETION_KEY = 'briefing_partial_completion';

/**
 * Partial completion data structure.
 */
interface PartialCompletion {
  briefingId: string;
  completedSections: number;
  totalSections: number;
  timestamp: string;
}

/**
 * Save partial completion to session storage (Story 8.7 AC#4).
 */
function savePartialCompletion(data: PartialCompletion) {
  try {
    const existing = sessionStorage.getItem(PARTIAL_COMPLETION_KEY);
    const completions: PartialCompletion[] = existing ? JSON.parse(existing) : [];

    // Update or add entry
    const index = completions.findIndex(c => c.briefingId === data.briefingId);
    if (index >= 0) {
      completions[index] = data;
    } else {
      completions.push(data);
    }

    sessionStorage.setItem(PARTIAL_COMPLETION_KEY, JSON.stringify(completions));
  } catch (error) {
    console.error('Failed to save partial completion:', error);
  }
}

/**
 * Briefing Playback Page component.
 */
export default function BriefingPlaybackPage() {
  const router = useRouter();
  const params = useParams();
  const briefingId = params.id as string;

  // Briefing state and actions from hook
  const [state, actions] = useBriefing({
    onComplete: () => {
      // Clear partial completion on full completion
      try {
        const existing = sessionStorage.getItem(PARTIAL_COMPLETION_KEY);
        if (existing) {
          const completions: PartialCompletion[] = JSON.parse(existing);
          const filtered = completions.filter(c => c.briefingId !== briefingId);
          sessionStorage.setItem(PARTIAL_COMPLETION_KEY, JSON.stringify(filtered));
        }
      } catch (error) {
        // Silently handle storage errors - partial completion is non-critical
      }
    },
    onError: (_error) => {
      // Error is handled via state.error and displayed in UI
    },
    onSectionChange: (index, section) => {

      // Track partial completion (Story 8.7 Task 5.4)
      if (state.briefingId) {
        savePartialCompletion({
          briefingId: state.briefingId,
          completedSections: index,
          totalSections: state.sections.length,
          timestamp: new Date().toISOString(),
        });
      }
    },
  });

  // Local state for showing pause countdown overlay
  const [showPauseOverlay, setShowPauseOverlay] = useState(false);

  // Initialize briefing data on mount
  // Note: When API integration is complete, this will fetch existing briefings by ID
  useEffect(() => {
    if (state.status === 'idle' && briefingId !== 'new') {
      // Briefing loading is handled by the launcher page (Story 8.4)
      // This page receives an active briefing or redirects to launcher
    }
  }, [briefingId, state.status]);

  // Show pause overlay when awaiting response with countdown
  useEffect(() => {
    if (state.status === 'awaiting_response' && state.silenceCountdown !== null) {
      setShowPauseOverlay(true);
    } else {
      setShowPauseOverlay(false);
    }
  }, [state.status, state.silenceCountdown]);

  // Handle transcription from push-to-talk
  const handleTranscription = useCallback(
    (result: { text: string; confidence: number }) => {
      const text = result.text.toLowerCase().trim();

      // Check for continue commands
      if (
        text === 'no' ||
        text === 'continue' ||
        text === 'next' ||
        text === 'no questions' ||
        text.includes('continue')
      ) {
        actions.cancelSilenceDetection();
        actions.continueAfterPause();
      } else if (result.text.trim()) {
        // Submit as a question
        actions.cancelSilenceDetection();
        actions.submitQuestion(result.text);
      }
    },
    [actions]
  );

  // Handle end briefing and return to launcher
  const handleEndBriefing = useCallback(() => {
    // Save partial completion before ending
    if (state.briefingId) {
      savePartialCompletion({
        briefingId: state.briefingId,
        completedSections: state.currentSectionIndex + 1,
        totalSections: state.sections.length,
        timestamp: new Date().toISOString(),
      });
    }

    actions.endBriefing();

    // Navigate back to launcher
    router.push('/briefing');
  }, [state.briefingId, state.currentSectionIndex, state.sections.length, actions, router]);

  // Handle section click from AreaProgress
  const handleSectionClick = useCallback((index: number) => {
    actions.goToSection(index);
  }, [actions]);

  // Map transcript entries
  const transcriptEntries: TranscriptEntry[] = state.transcript.map((entry) => ({
    id: entry.id,
    type: entry.type === 'system' ? 'assistant' : entry.type,
    text: entry.text,
    timestamp: entry.timestamp,
    confidence: entry.confidence,
    citations: entry.citations,
    isProcessing: entry.isProcessing,
  }));

  // Current and next sections
  const currentSection = state.sections[state.currentSectionIndex];
  const nextSection = state.sections[state.currentSectionIndex + 1];

  // Handle continue from pause
  const handleContinue = useCallback(() => {
    setShowPauseOverlay(false);
    actions.continueAfterPause();
  }, [actions]);

  // Loading state
  if (state.status === 'loading') {
    return (
      <main className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <svg
            className="animate-spin w-12 h-12 text-blue-600 mx-auto mb-4"
            viewBox="0 0 24 24"
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
          <p className="text-gray-600 text-lg">Generating your briefing...</p>
          <p className="text-sm text-gray-400 mt-1">
            Gathering data from all production areas
          </p>
        </div>
      </main>
    );
  }

  // Error state
  if (state.status === 'error') {
    return (
      <main className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardContent className="pt-6 text-center">
            <svg
              className="w-12 h-12 text-amber-500 mx-auto mb-4"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Unable to Load Briefing
            </h2>
            <p className="text-gray-600 mb-6">{state.error}</p>
            <Button onClick={() => router.push('/briefing')}>
              Return to Briefing
            </Button>
          </CardContent>
        </Card>
      </main>
    );
  }

  // Idle state (no briefing started) - redirect to launcher
  if (state.status === 'idle' && state.sections.length === 0) {
    return (
      <main className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardContent className="pt-6 text-center">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              No Active Briefing
            </h2>
            <p className="text-gray-600 mb-6">
              Start a new briefing from the launcher page.
            </p>
            <Button onClick={() => router.push('/briefing')}>
              Go to Briefing Launcher
            </Button>
          </CardContent>
        </Card>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50">
      {/* Pause Countdown Overlay (AC#2) */}
      {showPauseOverlay && state.silenceCountdown !== null && (
        <PauseCountdown
          countdown={state.silenceCountdown}
          nextSection={nextSection}
          pausePrompt={currentSection?.pause_point ? `Any questions on ${currentSection.title}?` : undefined}
          onContinue={handleContinue}
          overlay={true}
        />
      )}

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Header */}
        <header className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {state.title || 'Morning Briefing'}
            </h1>
            <p className="text-sm text-gray-500">
              {state.status === 'complete'
                ? 'Briefing complete'
                : `Section ${state.currentSectionIndex + 1} of ${state.sections.length}`}
            </p>
          </div>
          <Button
            variant="ghost"
            onClick={() => router.push('/briefing')}
            className="text-gray-500 hover:text-gray-700"
          >
            <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" className="mr-1">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
            </svg>
            Exit
          </Button>
        </header>

        {/* Main content - responsive layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left sidebar - Area Progress (AC#1) */}
          <aside className="lg:col-span-3">
            <Card>
              <CardContent className="p-4">
                <AreaProgress
                  sections={state.sections}
                  currentIndex={state.currentSectionIndex}
                  onSectionClick={handleSectionClick}
                  compact={false}
                />
              </CardContent>
            </Card>
          </aside>

          {/* Main content area */}
          <div className="lg:col-span-6 space-y-6">
            {/* Current section content (AC#1) */}
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold text-lg">
                    {state.currentSectionIndex + 1}
                  </div>
                  <div>
                    <CardTitle className="text-xl">
                      {currentSection?.title || 'Section'}
                    </CardTitle>
                    {currentSection?.area_id && (
                      <span className="text-xs text-gray-500">
                        {currentSection.area_id}
                      </span>
                    )}
                  </div>
                  {/* Status indicator */}
                  {state.status === 'playing' && (
                    <span className="ml-auto px-2 py-1 text-xs bg-blue-100 text-blue-600 rounded-full animate-pulse">
                      Playing
                    </span>
                  )}
                  {state.status === 'awaiting_response' && (
                    <span className="ml-auto px-2 py-1 text-xs bg-yellow-100 text-yellow-600 rounded-full">
                      Paused
                    </span>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                {/* Text transcript (AC#1) */}
                <div className="prose prose-gray max-w-none">
                  <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                    {currentSection?.content}
                  </p>
                </div>

                {/* Error message if present */}
                {currentSection?.error_message && (
                  <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                    <p className="text-sm text-amber-700">
                      <span className="font-medium">Note:</span>{' '}
                      {currentSection.error_message}
                    </p>
                  </div>
                )}

                {/* Completion message */}
                {state.status === 'complete' && (
                  <div className="mt-6 text-center py-8 bg-green-50 rounded-lg">
                    <svg
                      className="w-16 h-16 text-green-500 mx-auto mb-4"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M20 6L9 17l-5-5" />
                    </svg>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">
                      Briefing Complete
                    </h3>
                    <p className="text-gray-600 mb-4">
                      You&apos;ve reviewed all {state.sections.length} production areas.
                    </p>
                    <Button onClick={() => router.push('/briefing')}>
                      Back to Briefing
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Voice Controls (AC#1, AC#3, AC#4) */}
            {state.status !== 'complete' && (
              <Card>
                <CardContent className="p-4">
                  <VoiceControls
                    status={state.status}
                    currentSectionIndex={state.currentSectionIndex}
                    totalSections={state.sections.length}
                    currentSection={currentSection}
                    silenceCountdown={state.silenceCountdown}
                    onPlay={actions.play}
                    onPause={actions.pause}
                    onNext={actions.nextSection}
                    onPrevious={actions.previousSection}
                    onEnd={handleEndBriefing}
                    onContinue={handleContinue}
                    enableKeyboardShortcuts={true}
                    showShortcutHints={true}
                  />
                </CardContent>
              </Card>
            )}

            {/* Section Overview (quick navigation) */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-semibold text-gray-700">
                  Quick Navigation
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-2">
                <div className="flex flex-wrap gap-2">
                  {state.sections.map((section, index) => (
                    <button
                      key={index}
                      type="button"
                      onClick={() => actions.goToSection(index)}
                      className={`
                        px-3 py-1.5 rounded-lg text-sm transition-all
                        ${index === state.currentSectionIndex
                          ? 'bg-blue-600 text-white'
                          : index < state.currentSectionIndex
                          ? 'bg-green-100 text-green-700 hover:bg-green-200'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }
                      `}
                    >
                      {section.title}
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right sidebar - Q&A */}
          <aside className="lg:col-span-3 space-y-4">
            {/* Push-to-talk for Q&A */}
            {(state.status === 'awaiting_response' || state.status === 'qa') && (
              <Card>
                <CardContent className="p-4">
                  <h3 className="text-sm font-semibold text-gray-700 mb-3 text-center">
                    Ask a Question
                  </h3>
                  <div className="flex justify-center">
                    <PushToTalkButton
                      isSessionActive={state.status === 'awaiting_response'}
                      onTranscription={handleTranscription}
                      size="large"
                      disabled={state.status === 'qa'}
                    />
                  </div>
                  <p className="text-xs text-gray-500 text-center mt-3">
                    Say &quot;Continue&quot; to move to the next section
                  </p>
                </CardContent>
              </Card>
            )}

            {/* Transcript panel */}
            <Card>
              <CardContent className="p-0">
                <TranscriptPanel
                  entries={transcriptEntries}
                  isTranscribing={false}
                  isProcessing={state.status === 'qa'}
                  maxHeight="400px"
                  emptyMessage="Questions and responses will appear here"
                />
              </CardContent>
            </Card>
          </aside>
        </div>
      </div>
    </main>
  );
}
