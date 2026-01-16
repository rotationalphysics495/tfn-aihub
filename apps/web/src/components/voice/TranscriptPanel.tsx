'use client';

/**
 * TranscriptPanel Component (Story 8.2)
 *
 * Displays transcribed user voice input and AI responses.
 * Shows real-time transcription status and auto-scrolls to latest entry.
 *
 * AC#2: WebSocket STT Streaming - Shows transcription results
 * AC#3: Q&A Processing Integration - Displays AI responses
 *
 * References:
 * - [Source: architecture/voice-briefing.md#Voice Integration Architecture]
 */

import React, { useEffect, useRef } from 'react';

/**
 * A single entry in the transcript.
 */
export interface TranscriptEntry {
  id: string;
  type: 'user' | 'assistant';
  text: string;
  timestamp: string;
  confidence?: number;
  citations?: string[];
  isProcessing?: boolean;
}

/**
 * TranscriptPanel props.
 */
export interface TranscriptPanelProps {
  /** Transcript entries */
  entries: TranscriptEntry[];
  /** Whether currently transcribing */
  isTranscribing?: boolean;
  /** Whether AI is processing a response */
  isProcessing?: boolean;
  /** Custom class name */
  className?: string;
  /** Show timestamps */
  showTimestamps?: boolean;
  /** Show confidence scores */
  showConfidence?: boolean;
  /** Maximum height before scrolling */
  maxHeight?: string;
  /** Empty state message */
  emptyMessage?: string;
}

/**
 * Format timestamp for display.
 */
function formatTimestamp(isoString: string): string {
  try {
    const date = new Date(isoString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch {
    return '';
  }
}

/**
 * Format confidence as percentage.
 */
function formatConfidence(confidence: number): string {
  return `${Math.round(confidence * 100)}%`;
}

/**
 * TranscriptPanel component for displaying voice interactions.
 *
 * Story 8.2 Implementation:
 * - AC#2: Displays transcribed user input
 * - AC#3: Shows AI responses with citations
 *
 * Usage:
 * ```tsx
 * <TranscriptPanel
 *   entries={transcriptEntries}
 *   isTranscribing={isRecording}
 *   isProcessing={isWaitingForResponse}
 * />
 * ```
 */
export function TranscriptPanel({
  entries,
  isTranscribing = false,
  isProcessing = false,
  className = '',
  showTimestamps = true,
  showConfidence = false,
  maxHeight = '400px',
  emptyMessage = 'Ask a question using the push-to-talk button',
}: TranscriptPanelProps) {
  // Ref for auto-scrolling
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when entries change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [entries, isTranscribing, isProcessing]);

  return (
    <div
      className={`transcript-panel bg-white rounded-lg border border-gray-200 ${className}`}
      style={{ maxHeight }}
    >
      {/* Header */}
      <div className="transcript-panel__header px-4 py-2 border-b border-gray-100 flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-700">Transcript</h3>
        {(isTranscribing || isProcessing) && (
          <span className="flex items-center gap-1 text-xs text-blue-600">
            <span className="w-2 h-2 bg-blue-600 rounded-full animate-pulse" />
            {isTranscribing ? 'Transcribing...' : 'Processing...'}
          </span>
        )}
      </div>

      {/* Content */}
      <div className="transcript-panel__content overflow-y-auto p-4 space-y-4">
        {/* Empty state */}
        {entries.length === 0 && !isTranscribing && !isProcessing && (
          <div className="text-center text-gray-400 py-8">
            <svg
              className="w-12 h-12 mx-auto mb-2 opacity-50"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
            >
              <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
              <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
            </svg>
            <p className="text-sm">{emptyMessage}</p>
          </div>
        )}

        {/* Entries */}
        {entries.map((entry) => (
          <div
            key={entry.id}
            className={`transcript-panel__entry ${
              entry.type === 'user'
                ? 'transcript-panel__entry--user'
                : 'transcript-panel__entry--assistant'
            }`}
          >
            {/* User message */}
            {entry.type === 'user' && (
              <div className="flex justify-end">
                <div className="max-w-[80%]">
                  <div className="bg-blue-600 text-white rounded-lg rounded-br-sm px-4 py-2">
                    <p className="text-sm">{entry.text}</p>
                  </div>
                  <div className="flex items-center justify-end gap-2 mt-1 text-xs text-gray-400">
                    {showTimestamps && entry.timestamp && (
                      <span>{formatTimestamp(entry.timestamp)}</span>
                    )}
                    {showConfidence && entry.confidence !== undefined && (
                      <span className="text-gray-300">
                        {formatConfidence(entry.confidence)} confidence
                      </span>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Assistant message */}
            {entry.type === 'assistant' && (
              <div className="flex justify-start">
                <div className="max-w-[80%]">
                  <div className="bg-gray-100 text-gray-800 rounded-lg rounded-bl-sm px-4 py-2">
                    {entry.isProcessing ? (
                      <div className="flex items-center gap-2">
                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
                      </div>
                    ) : (
                      <p className="text-sm whitespace-pre-wrap">{entry.text}</p>
                    )}
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    {showTimestamps && entry.timestamp && (
                      <span className="text-xs text-gray-400">
                        {formatTimestamp(entry.timestamp)}
                      </span>
                    )}
                    {/* Citations */}
                    {entry.citations && entry.citations.length > 0 && (
                      <div className="flex items-center gap-1">
                        <span className="text-xs text-gray-400">Sources:</span>
                        {entry.citations.map((citation, idx) => (
                          <span
                            key={idx}
                            className="text-xs text-blue-600 hover:underline cursor-pointer"
                            title={citation}
                          >
                            [{idx + 1}]
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}

        {/* Transcribing indicator */}
        {isTranscribing && (
          <div className="flex justify-end">
            <div className="max-w-[80%]">
              <div className="bg-blue-100 text-blue-600 rounded-lg px-4 py-2 border border-blue-200">
                <div className="flex items-center gap-2">
                  <svg
                    className="w-4 h-4 animate-pulse"
                    viewBox="0 0 24 24"
                    fill="currentColor"
                  >
                    <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
                    <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
                  </svg>
                  <span className="text-sm">Listening...</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Processing indicator */}
        {isProcessing && !isTranscribing && (
          <div className="flex justify-start">
            <div className="max-w-[80%]">
              <div className="bg-gray-100 text-gray-600 rounded-lg px-4 py-2">
                <div className="flex items-center gap-1">
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                  <span
                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: '0.1s' }}
                  />
                  <span
                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: '0.2s' }}
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Auto-scroll anchor */}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}

export default TranscriptPanel;
