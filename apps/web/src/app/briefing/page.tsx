'use client';

/**
 * Morning Briefing Page (Story 8.4)
 *
 * Briefing launcher UI for Plant Managers to start and control
 * morning briefings covering all production areas.
 *
 * AC#1: Start Morning Briefing with area preview
 * AC#2: Pause prompts between sections with Q&A
 * AC#3: Continue commands (No/Continue/Next)
 * AC#4: Silence detection for auto-continue
 * AC#5: Q&A during pause with citations
 *
 * References:
 * - [Source: architecture/voice-briefing.md#Voice Integration Architecture]
 */

import React, { useEffect, useState, useCallback } from 'react';
import { useBriefing, type BriefingSection } from '@/lib/hooks/useBriefing';
import { BriefingPlayer } from '@/components/voice/BriefingPlayer';
import { VoiceControls } from '@/components/voice/VoiceControls';
import { PushToTalkButton } from '@/components/voice/PushToTalkButton';
import { TranscriptPanel, type TranscriptEntry } from '@/components/voice/TranscriptPanel';

/**
 * Production area info for preview.
 */
interface ProductionArea {
  id: string;
  name: string;
  description: string;
  assets: string[];
}

/**
 * Morning Briefing Page component.
 */
export default function BriefingPage() {
  // Briefing state and actions
  const [state, actions] = useBriefing({
    onComplete: () => {
      console.log('Briefing complete');
    },
    onError: (error) => {
      console.error('Briefing error:', error);
    },
    onSectionChange: (index, section) => {
      console.log(`Section changed to ${index}: ${section.title}`);
    },
  });

  // Production areas for preview
  const [areas, setAreas] = useState<ProductionArea[]>([]);
  const [defaultOrder, setDefaultOrder] = useState<string[]>([]);
  const [isLoadingAreas, setIsLoadingAreas] = useState(true);

  // Fetch production areas on mount
  useEffect(() => {
    async function fetchAreas() {
      try {
        const response = await fetch('/api/v1/briefing/areas');
        if (response.ok) {
          const data = await response.json();
          setAreas(data.areas);
          setDefaultOrder(data.default_order);
        }
      } catch (error) {
        console.error('Failed to fetch areas:', error);
      } finally {
        setIsLoadingAreas(false);
      }
    }
    fetchAreas();
  }, []);

  // Handle start briefing
  const handleStartBriefing = useCallback(async () => {
    // TODO: Get actual user ID from auth context
    await actions.startBriefing('current-user', defaultOrder);
  }, [actions, defaultOrder]);

  // Handle transcription from push-to-talk
  const handleTranscription = useCallback(
    (result: { text: string; confidence: number }) => {
      // Check for continue commands (AC#3)
      const text = result.text.toLowerCase().trim();
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
        // Submit as a question (AC#5)
        actions.cancelSilenceDetection();
        actions.submitQuestion(result.text);
      }
    },
    [actions]
  );

  // Convert sections to BriefingPlayer format
  const playerSections = state.sections.map((section, index) => ({
    id: `section-${index}`,
    title: section.title,
    content: section.content,
    areaId: section.area_id,
    audioStreamUrl: state.audioStreamUrl,
  }));

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

  // Current section
  const currentSection = state.sections[state.currentSectionIndex];

  // Show launcher if not started
  if (state.status === 'idle') {
    return (
      <main className="min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 py-8">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Morning Briefing
            </h1>
            <p className="text-gray-600">
              Get a comprehensive overview of all production areas
            </p>
          </div>

          {/* Start button */}
          <div className="text-center mb-8">
            <button
              type="button"
              onClick={handleStartBriefing}
              disabled={isLoadingAreas}
              className="
                inline-flex items-center gap-3 px-8 py-4
                bg-blue-600 hover:bg-blue-700 text-white
                rounded-xl shadow-lg hover:shadow-xl
                transition-all active:scale-95
                disabled:bg-blue-400 disabled:cursor-wait
                text-lg font-semibold
              "
            >
              {isLoadingAreas ? (
                <>
                  <svg
                    className="animate-spin w-6 h-6"
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
                  Loading...
                </>
              ) : (
                <>
                  <svg
                    className="w-6 h-6"
                    viewBox="0 0 24 24"
                    fill="currentColor"
                  >
                    <path d="M8 5v14l11-7z" />
                  </svg>
                  Start Morning Briefing
                </>
              )}
            </button>
          </div>

          {/* Area preview */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Production Areas Covered
            </h2>

            {isLoadingAreas ? (
              <div className="animate-pulse space-y-3">
                {[1, 2, 3, 4, 5, 6, 7].map((i) => (
                  <div key={i} className="h-12 bg-gray-100 rounded-lg" />
                ))}
              </div>
            ) : (
              <div className="space-y-3">
                {areas.map((area, index) => (
                  <div
                    key={area.id}
                    className="flex items-center gap-4 p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors"
                  >
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-semibold text-sm">
                      {index + 1}
                    </div>
                    <div className="flex-grow">
                      <h3 className="font-medium text-gray-900">{area.name}</h3>
                      <p className="text-sm text-gray-500">{area.description}</p>
                    </div>
                    <div className="flex-shrink-0 text-xs text-gray-400">
                      {area.assets.length} assets
                    </div>
                  </div>
                ))}
              </div>
            )}

            <p className="mt-4 text-sm text-gray-500 text-center">
              The briefing will pause after each area for questions
            </p>
          </div>
        </div>
      </main>
    );
  }

  // Show briefing interface
  return (
    <main className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-6">
        {/* Header */}
        <header className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{state.title}</h1>
            <p className="text-sm text-gray-500">
              {state.status === 'loading'
                ? 'Preparing your briefing...'
                : state.status === 'complete'
                ? 'Briefing complete'
                : `Section ${state.currentSectionIndex + 1} of ${state.sections.length}`}
            </p>
          </div>
          <button
            type="button"
            onClick={() => {
              actions.endBriefing();
              actions.reset();
            }}
            className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1"
          >
            <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
            </svg>
            Exit
          </button>
        </header>

        {/* Loading state */}
        {state.status === 'loading' && (
          <div className="flex items-center justify-center py-16">
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
              <p className="text-gray-600">Generating your morning briefing...</p>
              <p className="text-sm text-gray-400 mt-1">
                Gathering data from all production areas
              </p>
            </div>
          </div>
        )}

        {/* Error state */}
        {state.status === 'error' && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
            <svg
              className="w-12 h-12 text-red-500 mx-auto mb-4"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <h3 className="text-lg font-semibold text-red-800 mb-2">
              Unable to Generate Briefing
            </h3>
            <p className="text-red-600 mb-4">{state.error}</p>
            <button
              type="button"
              onClick={() => {
                actions.reset();
              }}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
            >
              Try Again
            </button>
          </div>
        )}

        {/* Main briefing interface */}
        {state.status !== 'loading' && state.status !== 'error' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main content - Briefing Player */}
            <div className="lg:col-span-2 space-y-6">
              {/* Current section content */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                {currentSection && (
                  <>
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-semibold text-sm">
                        {state.currentSectionIndex + 1}
                      </div>
                      <h2 className="text-xl font-semibold text-gray-900">
                        {currentSection.title}
                      </h2>
                      {currentSection.area_id && (
                        <span className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">
                          {currentSection.area_id}
                        </span>
                      )}
                    </div>
                    <p className="text-gray-700 leading-relaxed">
                      {currentSection.content}
                    </p>
                    {currentSection.error_message && (
                      <p className="mt-2 text-sm text-amber-600">
                        Note: {currentSection.error_message}
                      </p>
                    )}
                  </>
                )}

                {state.status === 'complete' && (
                  <div className="text-center py-8">
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
                    <p className="text-gray-600">
                      You&apos;ve reviewed all {state.sections.length} production areas.
                    </p>
                  </div>
                )}
              </div>

              {/* Voice controls */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
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
                  onEnd={actions.endBriefing}
                  onContinue={actions.continueAfterPause}
                />
              </div>

              {/* Section overview */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-3">
                  Briefing Overview
                </h3>
                <div className="flex flex-wrap gap-2">
                  {state.sections.map((section, index) => (
                    <button
                      key={index}
                      type="button"
                      onClick={() => actions.goToSection(index)}
                      className={`
                        px-3 py-1.5 rounded-lg text-sm transition-all
                        ${
                          index === state.currentSectionIndex
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
              </div>
            </div>

            {/* Sidebar - Q&A */}
            <div className="space-y-4">
              {/* Push-to-talk for Q&A */}
              {(state.status === 'awaiting_response' || state.status === 'qa') && (
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
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
                </div>
              )}

              {/* Transcript panel */}
              <TranscriptPanel
                entries={transcriptEntries}
                isTranscribing={false}
                isProcessing={state.status === 'qa'}
                maxHeight="400px"
                emptyMessage="Questions and responses will appear here"
              />
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
