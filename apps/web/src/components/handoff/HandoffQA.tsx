'use client';

/**
 * HandoffQA Component (Story 9.6)
 *
 * Q&A interface for shift handoffs allowing supervisors to ask
 * follow-up questions and receive AI-powered answers with citations.
 *
 * @see Story 9.6 - Handoff Q&A
 * @see AC#1 - Text/voice input for questions (FR26)
 * @see AC#2 - AI responses with citations (FR52)
 * @see AC#3 - Outgoing supervisor notifications and direct responses
 * @see AC#4 - Preserved Q&A thread visible to both supervisors
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import {
  MessageSquare,
  Send,
  Mic,
  User,
  Bot,
  Loader2,
  ExternalLink,
  RefreshCw,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { useHandoffQA, QAEntry, QACitation } from '@/lib/hooks/useHandoffQA';

// ============================================================================
// Types
// ============================================================================

export interface HandoffQAProps {
  /** Handoff ID to show Q&A for */
  handoffId: string;
  /** Whether current user is the handoff creator (outgoing supervisor) */
  isCreator?: boolean;
  /** Whether user can respond (outgoing supervisor online) */
  canRespond?: boolean;
  /** Optional CSS class name */
  className?: string;
  /** Callback when push-to-talk is pressed */
  onPushToTalk?: () => void;
  /** Voice transcript from STT */
  voiceTranscript?: string;
  /** Whether voice input is active */
  isVoiceActive?: boolean;
}

// ============================================================================
// Helper Functions
// ============================================================================

function formatTimestamp(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
}

function formatDate(isoString: string): string {
  const date = new Date(isoString);
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);

  if (date.toDateString() === today.toDateString()) {
    return 'Today';
  } else if (date.toDateString() === yesterday.toDateString()) {
    return 'Yesterday';
  }

  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });
}

function getEntryIcon(contentType: string) {
  switch (contentType) {
    case 'question':
      return User;
    case 'ai_answer':
      return Bot;
    case 'human_response':
      return User;
    default:
      return MessageSquare;
  }
}

function getEntryLabel(contentType: string, userName?: string): string {
  switch (contentType) {
    case 'question':
      return userName || 'You';
    case 'ai_answer':
      return 'AI Assistant';
    case 'human_response':
      return userName || 'Supervisor';
    default:
      return 'Unknown';
  }
}

// ============================================================================
// Sub-components
// ============================================================================

interface CitationBadgeProps {
  citation: QACitation;
}

function CitationBadge({ citation }: CitationBadgeProps) {
  return (
    <Badge
      variant="secondary"
      className="text-xs font-normal cursor-help"
      title={`${citation.context} (from ${citation.table})`}
    >
      <ExternalLink className="w-3 h-3 mr-1" />
      {citation.value}
    </Badge>
  );
}

interface QAEntryCardProps {
  entry: QAEntry;
  isCurrentUser: boolean;
}

function QAEntryCard({ entry, isCurrentUser }: QAEntryCardProps) {
  const Icon = getEntryIcon(entry.content_type);
  const label = getEntryLabel(entry.content_type, entry.user_name);
  const isAI = entry.content_type === 'ai_answer';
  const isQuestion = entry.content_type === 'question';

  return (
    <div
      className={cn(
        'flex gap-3',
        isQuestion && isCurrentUser && 'flex-row-reverse'
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
          isAI
            ? 'bg-primary text-primary-foreground'
            : 'bg-muted text-muted-foreground'
        )}
      >
        <Icon className="w-4 h-4" />
      </div>

      {/* Content */}
      <div
        className={cn(
          'flex-1 max-w-[85%]',
          isQuestion && isCurrentUser && 'text-right'
        )}
      >
        {/* Header */}
        <div
          className={cn(
            'flex items-center gap-2 mb-1',
            isQuestion && isCurrentUser && 'flex-row-reverse'
          )}
        >
          <span className="text-sm font-medium">{label}</span>
          <span className="text-xs text-muted-foreground">
            {formatTimestamp(entry.created_at)}
          </span>
        </div>

        {/* Message bubble */}
        <div
          className={cn(
            'rounded-lg p-3',
            isQuestion
              ? isCurrentUser
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted'
              : 'bg-card border'
          )}
        >
          <p className="text-sm whitespace-pre-wrap">{entry.content}</p>

          {/* Citations for AI responses */}
          {isAI && entry.citations && entry.citations.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2 pt-2 border-t border-border/50">
              {entry.citations.map((citation, idx) => (
                <CitationBadge key={idx} citation={citation} />
              ))}
            </div>
          )}
        </div>

        {/* Voice transcript indicator */}
        {entry.voice_transcript && (
          <div className="mt-1 text-xs text-muted-foreground flex items-center gap-1">
            <Mic className="w-3 h-3" />
            Voice transcription
          </div>
        )}
      </div>
    </div>
  );
}

interface QAInputProps {
  onSubmit: (question: string, voiceTranscript?: string) => Promise<void>;
  isSubmitting: boolean;
  onPushToTalk?: () => void;
  isVoiceActive?: boolean;
  voiceTranscript?: string;
  placeholder?: string;
}

function QAInput({
  onSubmit,
  isSubmitting,
  onPushToTalk,
  isVoiceActive,
  voiceTranscript,
  placeholder = 'Ask a question about this handoff...',
}: QAInputProps) {
  const [inputValue, setInputValue] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  // Update input when voice transcript changes
  useEffect(() => {
    if (voiceTranscript) {
      setInputValue(voiceTranscript);
    }
  }, [voiceTranscript]);

  const handleSubmit = useCallback(async (e?: React.FormEvent) => {
    e?.preventDefault();
    const question = inputValue.trim();
    if (!question || isSubmitting) return;

    await onSubmit(question, voiceTranscript);
    setInputValue('');
  }, [inputValue, voiceTranscript, isSubmitting, onSubmit]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }, [handleSubmit]);

  return (
    <form onSubmit={handleSubmit} className="flex items-center gap-2">
      {/* Push-to-talk button (Story 8.2 integration) */}
      {onPushToTalk && (
        <Button
          type="button"
          variant={isVoiceActive ? 'default' : 'outline'}
          size="icon"
          onClick={onPushToTalk}
          disabled={isSubmitting}
          className={cn(
            'flex-shrink-0 min-w-[44px] min-h-[44px]',
            isVoiceActive && 'animate-pulse bg-red-500 hover:bg-red-600'
          )}
          aria-label={isVoiceActive ? 'Stop recording' : 'Start recording'}
        >
          <Mic className="w-5 h-5" />
        </Button>
      )}

      {/* Text input */}
      <div className="relative flex-1">
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={isSubmitting}
          className={cn(
            'w-full px-4 py-3 pr-12 rounded-lg border bg-background',
            'focus:outline-none focus:ring-2 focus:ring-primary',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            'min-h-[44px]' // AC#4: Touch target
          )}
        />
      </div>

      {/* Send button */}
      <Button
        type="submit"
        size="icon"
        disabled={!inputValue.trim() || isSubmitting}
        className="flex-shrink-0 min-w-[44px] min-h-[44px]"
        aria-label="Send question"
      >
        {isSubmitting ? (
          <Loader2 className="w-5 h-5 animate-spin" />
        ) : (
          <Send className="w-5 h-5" />
        )}
      </Button>
    </form>
  );
}

// ============================================================================
// Main Component
// ============================================================================

/**
 * HandoffQA displays and manages the Q&A thread for a handoff.
 *
 * Features:
 * - Text input for questions
 * - Push-to-talk button integration (Story 8.2)
 * - AI-generated answers with citations
 * - Human response capability for outgoing supervisor
 * - Real-time updates via Supabase Realtime
 * - Proper loading and error states
 *
 * @example
 * ```tsx
 * <HandoffQA
 *   handoffId={handoff.id}
 *   isCreator={false}
 *   onPushToTalk={() => startRecording()}
 * />
 * ```
 */
export function HandoffQA({
  handoffId,
  isCreator = false,
  canRespond = false,
  className,
  onPushToTalk,
  voiceTranscript,
  isVoiceActive = false,
}: HandoffQAProps) {
  const [state, actions] = useHandoffQA(handoffId);
  const threadEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new entries arrive
  useEffect(() => {
    if (state.thread?.entries.length) {
      threadEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [state.thread?.entries.length]);

  // Acknowledge new entry notification
  useEffect(() => {
    if (state.hasNewEntry) {
      actions.acknowledgeNewEntry();
    }
  }, [state.hasNewEntry, actions]);

  // Group entries by date for display
  const entriesByDate = state.thread?.entries.reduce((groups, entry) => {
    const date = formatDate(entry.created_at);
    if (!groups[date]) {
      groups[date] = [];
    }
    groups[date].push(entry);
    return groups;
  }, {} as Record<string, QAEntry[]>) || {};

  return (
    <Card className={cn('handoff-qa', className)}>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5" />
            Questions & Answers
            {state.thread && state.thread.count > 0 && (
              <Badge variant="secondary" className="ml-2">
                {state.thread.count}
              </Badge>
            )}
          </div>

          {/* Refresh button */}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => actions.refreshThread()}
            disabled={state.isLoading}
            className="h-8 w-8"
            aria-label="Refresh Q&A thread"
          >
            <RefreshCw
              className={cn('w-4 h-4', state.isLoading && 'animate-spin')}
            />
          </Button>
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Error state */}
        {state.error && (
          <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm">
            {state.error}
            <Button
              variant="link"
              size="sm"
              onClick={actions.clearError}
              className="ml-2 h-auto p-0"
            >
              Dismiss
            </Button>
          </div>
        )}

        {/* Loading state */}
        {state.isLoading && !state.thread && (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
          </div>
        )}

        {/* Empty state */}
        {!state.isLoading && (!state.thread || state.thread.count === 0) && (
          <div className="text-center py-8 text-muted-foreground">
            <MessageSquare className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p className="text-sm">No questions yet.</p>
            <p className="text-xs mt-1">
              Ask a question about this handoff to get started.
            </p>
          </div>
        )}

        {/* Q&A thread */}
        {state.thread && state.thread.count > 0 && (
          <div className="space-y-6 max-h-[400px] overflow-y-auto pr-2">
            {Object.entries(entriesByDate).map(([date, entries]) => (
              <div key={date}>
                {/* Date separator */}
                <div className="flex items-center gap-2 my-4">
                  <div className="flex-1 h-px bg-border" />
                  <span className="text-xs text-muted-foreground px-2">
                    {date}
                  </span>
                  <div className="flex-1 h-px bg-border" />
                </div>

                {/* Entries for this date */}
                <div className="space-y-4">
                  {entries.map((entry) => (
                    <QAEntryCard
                      key={entry.id}
                      entry={entry}
                      isCurrentUser={!isCreator}
                    />
                  ))}
                </div>
              </div>
            ))}

            {/* Scroll anchor */}
            <div ref={threadEndRef} />
          </div>
        )}

        {/* Input area */}
        <div className="pt-4 border-t">
          <QAInput
            onSubmit={actions.submitQuestion}
            isSubmitting={state.isSubmitting}
            onPushToTalk={onPushToTalk}
            isVoiceActive={isVoiceActive}
            voiceTranscript={voiceTranscript}
            placeholder={
              isCreator
                ? 'Type your response...'
                : 'Ask a question about this handoff...'
            }
          />

          {/* Processing indicator */}
          {state.isSubmitting && (
            <div className="flex items-center gap-2 mt-2 text-sm text-muted-foreground">
              <Loader2 className="w-4 h-4 animate-spin" />
              Processing your question...
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default HandoffQA;
