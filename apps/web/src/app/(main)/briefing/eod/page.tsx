'use client';

/**
 * End of Day Summary Page (Story 9.10, 9.12)
 *
 * EOD summary UI for Plant Managers to review the day's performance
 * and compare against morning briefing predictions.
 *
 * AC#1: EOD Summary Trigger (FR31) - Plant Manager triggers summary
 * AC#2: Summary Content Structure - performance, wins, concerns, outlook
 * AC#3: No Morning Briefing Fallback - works without morning briefing
 *
 * Story 9.12 additions:
 * Task 7: EOD View Tracking (AC: 3)
 * - 7.1: Update last_eod_viewed_at when EOD summary page loads
 * - 7.2: Add API endpoint or direct Supabase update on page view
 * - 7.3: Ensure timestamp is user's local date for day comparison
 *
 * References:
 * - [Source: architecture/voice-briefing.md#Voice Integration Architecture]
 * - [Source: prd/prd-functional-requirements.md#FR31-FR34]
 */

import React, { useState, useCallback, useEffect } from 'react';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { createClient } from '@/lib/supabase/client';

/**
 * EOD section from API response.
 */
interface EODSection {
  section_type: string;
  title: string;
  content: string;
  area_id?: string;
  status: string;
  pause_point: boolean;
  error_message?: string;
}

/**
 * Morning comparison data.
 */
interface MorningComparison {
  morning_briefing_id: string;
  morning_generated_at: string;
  flagged_concerns: string[];
  concerns_resolved: string[];
  concerns_escalated: string[];
  predicted_wins: string[];
  actual_wins: string[];
  prediction_summary: string;
}

/**
 * EOD Summary response from API.
 */
interface EODSummaryData {
  summary_id: string;
  title: string;
  sections: EODSection[];
  audio_stream_url?: string;
  total_duration_estimate: number;
  generated_at: string;
  completion_percentage: number;
  timed_out: boolean;
  tool_failures: string[];
  morning_briefing_id?: string;
  comparison_available: boolean;
  morning_comparison?: MorningComparison;
  summary_date: string;
  time_range_start: string;
  time_range_end: string;
}

/**
 * Section type colors for visual differentiation.
 */
const sectionColors: Record<string, { bg: string; border: string; icon: string }> = {
  performance: { bg: 'bg-blue-50', border: 'border-blue-200', icon: '📊' },
  comparison: { bg: 'bg-purple-50', border: 'border-purple-200', icon: '🔄' },
  wins: { bg: 'bg-green-50', border: 'border-green-200', icon: '🏆' },
  concerns: { bg: 'bg-amber-50', border: 'border-amber-200', icon: '⚠️' },
  outlook: { bg: 'bg-indigo-50', border: 'border-indigo-200', icon: '🔮' },
  error: { bg: 'bg-red-50', border: 'border-red-200', icon: '❌' },
};

/**
 * Track EOD page view in user_preferences table.
 * Story 9.12 Task 7: EOD View Tracking (AC#3)
 * - 7.1: Update last_eod_viewed_at when EOD summary page loads
 * - 7.2: Direct Supabase update on page view
 * - 7.3: Ensure timestamp is UTC for consistent comparison
 */
async function trackEodPageView(): Promise<void> {
  try {
    const supabase = createClient();

    // Get current user
    const {
      data: { user },
      error: authError,
    } = await supabase.auth.getUser();

    if (authError || !user) {
      console.debug('Cannot track EOD view: user not authenticated');
      return;
    }

    // Update last_eod_viewed_at in user_preferences
    const { error: updateError } = await supabase
      .from('user_preferences')
      .update({
        last_eod_viewed_at: new Date().toISOString(),
      })
      .eq('user_id', user.id);

    if (updateError) {
      console.error('Failed to track EOD view:', updateError);
    } else {
      console.debug('EOD view tracked successfully');
    }
  } catch (err) {
    console.error('Error tracking EOD view:', err);
  }
}

/**
 * End of Day Summary Page component.
 */
export default function EODSummaryPage() {
  const [summary, setSummary] = useState<EODSummaryData | null>(null);
  const [status, setStatus] = useState<'idle' | 'loading' | 'complete' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Set<number>>(new Set([0]));

  // Track EOD page view on mount (Story 9.12 Task 7)
  useEffect(() => {
    trackEodPageView();
  }, []);

  /**
   * Fetch EOD summary from API.
   */
  const handleGenerateSummary = useCallback(async () => {
    setStatus('loading');
    setError(null);

    try {
      // Note: user_id is included in request body for backwards compatibility
      // The API also validates via auth token (get_current_user dependency)
      const response = await fetch('/api/v1/briefing/eod', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Include auth cookies/tokens
        body: JSON.stringify({
          user_id: 'current-user', // Placeholder - actual user comes from auth context
          include_audio: true,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate EOD summary');
      }

      const data: EODSummaryData = await response.json();
      setSummary(data);
      setStatus('complete');

      // Expand all sections by default
      setExpandedSections(new Set(data.sections.map((_, i) => i)));
    } catch (err) {
      console.error('Failed to generate EOD summary:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
      setStatus('error');
    }
  }, []);

  /**
   * Toggle section expansion.
   */
  const toggleSection = (index: number) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  /**
   * Format time for display.
   */
  const formatTime = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
      });
    } catch {
      return isoString;
    }
  };

  /**
   * Format date for display.
   */
  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        weekday: 'long',
        month: 'long',
        day: 'numeric',
      });
    } catch {
      return dateString;
    }
  };

  // Idle state - show launcher
  if (status === 'idle') {
    return (
      <main className="min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 py-8">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              End of Day Summary
            </h1>
            <p className="text-gray-600">
              Review today&apos;s performance and compare against this morning&apos;s briefing
            </p>
          </div>

          {/* Start button */}
          <div className="text-center mb-8">
            <button
              type="button"
              onClick={handleGenerateSummary}
              className="
                inline-flex items-center gap-3 px-8 py-4
                bg-indigo-600 hover:bg-indigo-700 text-white
                rounded-xl shadow-lg hover:shadow-xl
                transition-all active:scale-95
                text-lg font-semibold
              "
            >
              <svg
                className="w-6 h-6"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M12 8v4l3 3" />
                <circle cx="12" cy="12" r="10" />
              </svg>
              Generate End of Day Summary
            </button>
          </div>

          {/* Summary preview */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              What&apos;s Included
            </h2>

            <div className="space-y-3">
              <div className="flex items-center gap-4 p-3 rounded-lg bg-blue-50">
                <span className="text-2xl">📊</span>
                <div>
                  <h3 className="font-medium text-gray-900">Day&apos;s Performance</h3>
                  <p className="text-sm text-gray-500">Overall output vs target and OEE metrics</p>
                </div>
              </div>

              <div className="flex items-center gap-4 p-3 rounded-lg bg-purple-50">
                <span className="text-2xl">🔄</span>
                <div>
                  <h3 className="font-medium text-gray-900">Morning Comparison</h3>
                  <p className="text-sm text-gray-500">How actual results compared to morning predictions</p>
                </div>
              </div>

              <div className="flex items-center gap-4 p-3 rounded-lg bg-green-50">
                <span className="text-2xl">🏆</span>
                <div>
                  <h3 className="font-medium text-gray-900">Wins That Materialized</h3>
                  <p className="text-sm text-gray-500">Areas that exceeded targets and key achievements</p>
                </div>
              </div>

              <div className="flex items-center gap-4 p-3 rounded-lg bg-amber-50">
                <span className="text-2xl">⚠️</span>
                <div>
                  <h3 className="font-medium text-gray-900">Concerns Status</h3>
                  <p className="text-sm text-gray-500">Issues resolved or escalated during the day</p>
                </div>
              </div>

              <div className="flex items-center gap-4 p-3 rounded-lg bg-indigo-50">
                <span className="text-2xl">🔮</span>
                <div>
                  <h3 className="font-medium text-gray-900">Tomorrow&apos;s Outlook</h3>
                  <p className="text-sm text-gray-500">Carry-forward priorities and focus areas</p>
                </div>
              </div>
            </div>

            <p className="mt-4 text-sm text-gray-500 text-center">
              Summary covers 6:00 AM to current time
            </p>
          </div>
        </div>
      </main>
    );
  }

  // Loading state
  if (status === 'loading') {
    return (
      <main className="min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 py-8">
          <div className="flex items-center justify-center py-16">
            <div className="text-center">
              <svg
                className="animate-spin w-12 h-12 text-indigo-600 mx-auto mb-4"
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
              <p className="text-gray-600">Generating your end of day summary...</p>
              <p className="text-sm text-gray-400 mt-1">
                Analyzing data and comparing to morning briefing
              </p>
            </div>
          </div>
        </div>
      </main>
    );
  }

  // Error state
  if (status === 'error') {
    return (
      <main className="min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 py-8">
          <Alert variant="warning" className="mb-6">
            <AlertTitle>Unable to Generate Summary</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>

          <div className="text-center">
            <button
              type="button"
              onClick={() => setStatus('idle')}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              Try Again
            </button>
          </div>
        </div>
      </main>
    );
  }

  // Summary display
  if (!summary) {
    return null;
  }

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <header className="mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{summary.title}</h1>
              <p className="text-sm text-gray-500">
                {formatDate(summary.summary_date)} &bull;{' '}
                {formatTime(summary.time_range_start)} - {formatTime(summary.time_range_end)}
              </p>
            </div>
            <button
              type="button"
              onClick={() => {
                setSummary(null);
                setStatus('idle');
              }}
              className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1"
            >
              <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                <path d="M17.65 6.35A7.958 7.958 0 0012 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08A5.99 5.99 0 0112 18c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z" />
              </svg>
              Generate New
            </button>
          </div>

          {/* Morning comparison status */}
          {summary.comparison_available ? (
            <div className="mt-3 px-3 py-2 bg-purple-50 border border-purple-200 rounded-lg text-sm text-purple-700">
              Compared against morning briefing generated at{' '}
              {summary.morning_comparison
                ? formatTime(summary.morning_comparison.morning_generated_at)
                : 'N/A'}
            </div>
          ) : (
            <div className="mt-3 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-600">
              No morning briefing to compare &bull; Showing day&apos;s standalone performance
            </div>
          )}

          {/* Status indicators */}
          {(summary.timed_out || summary.tool_failures.length > 0) && (
            <Alert variant="warning" className="mt-3">
              <AlertDescription>
                {summary.timed_out && 'Summary generation timed out. '}
                {summary.tool_failures.length > 0 &&
                  `Some data unavailable: ${summary.tool_failures.join(', ')}`}
              </AlertDescription>
            </Alert>
          )}
        </header>

        {/* Summary sections */}
        <div className="space-y-4">
          {summary.sections.map((section, index) => {
            const colors = sectionColors[section.section_type] || sectionColors.performance;
            const isExpanded = expandedSections.has(index);

            return (
              <div
                key={index}
                className={`rounded-xl border ${colors.border} overflow-hidden`}
              >
                {/* Section header */}
                <button
                  type="button"
                  onClick={() => toggleSection(index)}
                  className={`w-full px-4 py-3 ${colors.bg} flex items-center justify-between text-left`}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xl">{colors.icon}</span>
                    <h2 className="font-semibold text-gray-900">{section.title}</h2>
                    {section.status === 'partial' && (
                      <span className="px-2 py-0.5 bg-amber-100 text-amber-700 rounded text-xs">
                        Partial
                      </span>
                    )}
                    {section.status === 'failed' && (
                      <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded text-xs">
                        Failed
                      </span>
                    )}
                  </div>
                  <svg
                    className={`w-5 h-5 text-gray-500 transition-transform ${
                      isExpanded ? 'rotate-180' : ''
                    }`}
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {/* Section content */}
                {isExpanded && (
                  <div className="px-4 py-4 bg-white">
                    <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                      {section.content}
                    </p>
                    {section.error_message && (
                      <p className="mt-2 text-sm text-amber-600">
                        Note: {section.error_message}
                      </p>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Morning comparison details (if available) */}
        {summary.morning_comparison && (
          <div className="mt-6 bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Detailed Morning Comparison
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Wins column */}
              <div>
                <h4 className="font-medium text-green-700 mb-2 flex items-center gap-2">
                  <span className="w-2 h-2 bg-green-500 rounded-full" />
                  Wins That Materialized
                </h4>
                {summary.morning_comparison.actual_wins.length > 0 ? (
                  <ul className="space-y-1 text-sm text-gray-600">
                    {summary.morning_comparison.actual_wins.map((win, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-green-500">✓</span>
                        {win}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-gray-400">No specific wins tracked</p>
                )}
              </div>

              {/* Concerns column */}
              <div>
                <h4 className="font-medium text-amber-700 mb-2 flex items-center gap-2">
                  <span className="w-2 h-2 bg-amber-500 rounded-full" />
                  Concerns Status
                </h4>
                {summary.morning_comparison.concerns_resolved.length > 0 && (
                  <div className="mb-2">
                    <p className="text-xs text-gray-500 uppercase tracking-wide">Resolved</p>
                    <ul className="space-y-1 text-sm text-green-600">
                      {summary.morning_comparison.concerns_resolved.map((concern, i) => (
                        <li key={i}>✓ {concern}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {summary.morning_comparison.concerns_escalated.length > 0 && (
                  <div>
                    <p className="text-xs text-gray-500 uppercase tracking-wide">Escalated</p>
                    <ul className="space-y-1 text-sm text-amber-600">
                      {summary.morning_comparison.concerns_escalated.map((concern, i) => (
                        <li key={i}>→ {concern}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {summary.morning_comparison.concerns_resolved.length === 0 &&
                  summary.morning_comparison.concerns_escalated.length === 0 && (
                    <p className="text-sm text-gray-400">No concerns tracked</p>
                  )}
              </div>
            </div>
          </div>
        )}

        {/* Footer with generation info */}
        <footer className="mt-6 text-center text-sm text-gray-400">
          Generated at {formatTime(summary.generated_at)} &bull;{' '}
          {summary.completion_percentage.toFixed(0)}% complete
        </footer>
      </div>
    </main>
  );
}
