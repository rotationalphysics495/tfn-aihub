'use client';

/**
 * HandoffViewer Component (Story 9.5, 9.6, 9.7)
 *
 * Displays full handoff details including summary, notes, voice notes, and Q&A.
 *
 * @see Story 9.5 - Handoff Review UI
 * @see Story 9.6 - Handoff Q&A
 * @see Story 9.7 - Acknowledgment Flow
 * @see AC#2 - Handoff Detail View
 * @see AC#3 - Voice Note Playback
 * @see AC#4 - Tablet-Optimized Layout
 */

import { useState } from 'react';
import { Clock, User, FileText, Mic, CheckCircle, MessageSquare, WifiOff } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { VoiceNotePlayer } from './VoiceNotePlayer';
import { HandoffQA } from './HandoffQA';
import { HandoffAcknowledge } from './HandoffAcknowledge';
import { StaleCacheWarning } from '@/components/offline/StaleCacheWarning';
import { cn } from '@/lib/utils';
import type { Handoff, HandoffVoiceNote, HandoffStatus } from '@/types/handoff';

// ============================================================================
// Types
// ============================================================================

export interface HandoffViewerProps {
  /** Handoff data */
  handoff: Handoff;
  /** Whether current user is the handoff creator (outgoing supervisor) */
  isCreator?: boolean;
  /** Whether user can acknowledge this handoff */
  canAcknowledge?: boolean;
  /** Called when acknowledge is confirmed (Story 9.7) */
  onAcknowledge?: (notes?: string) => Promise<void>;
  /** Whether acknowledge is in progress */
  isAcknowledging?: boolean;
  /** Error message from acknowledgment attempt */
  acknowledgeError?: string | null;
  /** Whether offline mode is active (AC#4) */
  isOffline?: boolean;
  /** Whether there's a pending acknowledgment queued (AC#4) */
  hasPendingAcknowledgment?: boolean;
  /** Acknowledgment notes if acknowledged (AC#3) */
  acknowledgmentNotes?: string | null;
  /** Name of the user who acknowledged */
  acknowledgedByName?: string | null;
  /** Callback when push-to-talk is pressed for Q&A */
  onPushToTalk?: () => void;
  /** Voice transcript from STT for Q&A */
  voiceTranscript?: string;
  /** Whether voice input is active for Q&A */
  isVoiceActive?: boolean;
  /** Whether cache is stale (Story 9.9 AC#4) */
  isCacheStale?: boolean;
  /** Cache age in milliseconds (Story 9.9 AC#4) */
  cacheAgeMs?: number;
  /** Called when user requests fresh data (Story 9.9 AC#4) */
  onRefreshCache?: () => void;
  /** Whether refreshing cache (Story 9.9 AC#4) */
  isRefreshingCache?: boolean;
  /** Optional CSS class name */
  className?: string;
}

// ============================================================================
// Helper Functions
// ============================================================================

function formatShiftType(type: string): string {
  return type.charAt(0).toUpperCase() + type.slice(1);
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });
}

function formatTime(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function getStatusBadgeVariant(
  status: HandoffStatus
): 'info' | 'success' | 'secondary' {
  switch (status) {
    case 'pending_acknowledgment':
      return 'info';
    case 'acknowledged':
      return 'success';
    default:
      return 'secondary';
  }
}

function getStatusLabel(status: HandoffStatus): string {
  switch (status) {
    case 'pending_acknowledgment':
      return 'Pending Acknowledgment';
    case 'acknowledged':
      return 'Acknowledged';
    case 'draft':
      return 'Draft';
    case 'superseded':
      return 'Superseded';
    default:
      return status;
  }
}

// ============================================================================
// Sub-components
// ============================================================================

interface VoiceNoteSectionProps {
  notes: HandoffVoiceNote[];
}

function VoiceNoteSection({ notes }: VoiceNoteSectionProps) {
  const [expandedNoteId, setExpandedNoteId] = useState<string | null>(null);

  if (notes.length === 0) {
    return null;
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center gap-2">
          <Mic className="w-5 h-5" />
          Voice Notes ({notes.length})
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {notes
          .sort((a, b) => a.sequence_order - b.sequence_order)
          .map((note, index) => {
            const isExpanded = expandedNoteId === note.id;

            return (
              <div
                key={note.id}
                className="border rounded-lg overflow-hidden"
              >
                {/* Note header */}
                <button
                  type="button"
                  onClick={() =>
                    setExpandedNoteId(isExpanded ? null : note.id)
                  }
                  className={cn(
                    'w-full flex items-center justify-between p-4 text-left',
                    'hover:bg-muted/50 transition-colors',
                    'min-h-[44px]' // AC#4: Touch target
                  )}
                >
                  <div className="flex items-center gap-3">
                    {/* Sequence badge */}
                    <div className="w-6 h-6 rounded-full bg-primary text-primary-foreground text-xs font-medium flex items-center justify-center">
                      {index + 1}
                    </div>
                    <span className="font-medium">
                      Voice Note {index + 1}
                    </span>
                    <span className="text-sm text-muted-foreground">
                      {formatDuration(note.duration_seconds)}
                    </span>
                  </div>
                  <svg
                    className={cn(
                      'w-5 h-5 text-muted-foreground transition-transform',
                      isExpanded && 'rotate-180'
                    )}
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </button>

                {/* Expandable content with player */}
                {isExpanded && note.storage_url && (
                  <div className="px-4 pb-4 border-t bg-muted/30">
                    <div className="pt-4">
                      <VoiceNotePlayer
                        src={note.storage_url}
                        transcript={note.transcript}
                      />
                    </div>
                  </div>
                )}
              </div>
            );
          })}
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Main Component
// ============================================================================

/**
 * HandoffViewer displays full handoff details.
 *
 * Features:
 * - Shift summary section with citations
 * - Text notes section
 * - Voice note player integration
 * - Q&A section for follow-up questions (Story 9.6)
 * - Acknowledgment flow with dialog (Story 9.7)
 * - Offline acknowledgment queuing (Story 9.7 AC#4)
 * - Tablet-first responsive layout
 *
 * @example
 * ```tsx
 * <HandoffViewer
 *   handoff={handoff}
 *   canAcknowledge={true}
 *   onAcknowledge={async (notes) => handleAcknowledge(notes)}
 * />
 * ```
 */
export function HandoffViewer({
  handoff,
  isCreator = false,
  canAcknowledge = false,
  onAcknowledge,
  isAcknowledging = false,
  acknowledgeError = null,
  isOffline = false,
  hasPendingAcknowledgment = false,
  acknowledgmentNotes = null,
  acknowledgedByName = null,
  onPushToTalk,
  voiceTranscript,
  isVoiceActive = false,
  isCacheStale = false,
  cacheAgeMs,
  onRefreshCache,
  isRefreshingCache = false,
  className,
}: HandoffViewerProps) {
  // State for acknowledgment dialog (Story 9.7 AC#1)
  const [showAckDialog, setShowAckDialog] = useState(false);

  // Handle opening the acknowledgment dialog
  const handleAcknowledgeClick = () => {
    setShowAckDialog(true);
  };

  // Handle acknowledgment confirmation
  const handleAcknowledgeConfirm = async (notes?: string) => {
    if (onAcknowledge) {
      await onAcknowledge(notes);
      setShowAckDialog(false);
    }
  };

  return (
    <div
      className={cn(
        'handoff-viewer',
        'p-4 md:p-6 lg:p-8',
        'grid gap-4 md:gap-6',
        className
      )}
    >
      {/* Stale cache warning (Story 9.9 AC#4) */}
      {isCacheStale && (
        <StaleCacheWarning
          isStale={isCacheStale}
          cacheAgeMs={cacheAgeMs}
          onRefresh={onRefreshCache}
          isRefreshing={isRefreshingCache}
        />
      )}

      {/* Header section */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
            {/* Left: Creator info */}
            <div className="space-y-2">
              <Badge
                variant={getStatusBadgeVariant(handoff.status)}
                className="mb-2"
              >
                {getStatusLabel(handoff.status)}
              </Badge>

              {/* Creator name - AC#8: 24px+ for key values */}
              <h1 className="text-2xl md:text-3xl font-semibold text-foreground flex items-center gap-3">
                <User className="w-7 h-7 text-muted-foreground flex-shrink-0" />
                Handoff from {handoff.creator_name}
              </h1>

              {/* Shift details */}
              <div className="flex flex-wrap items-center gap-4 text-base text-muted-foreground">
                <span className="flex items-center gap-2">
                  <Clock className="w-5 h-5" />
                  {formatShiftType(handoff.shift_type)} Shift
                </span>
                <span>{formatDate(handoff.shift_date)}</span>
                {handoff.submitted_at && (
                  <span>Submitted at {formatTime(handoff.submitted_at)}</span>
                )}
              </div>
            </div>

            {/* Right: Acknowledge button (Story 9.7) */}
            {canAcknowledge && onAcknowledge && !hasPendingAcknowledgment && (
              <div className="flex flex-col items-end gap-2">
                {isOffline && (
                  <div className="flex items-center gap-1 text-xs text-warning-amber">
                    <WifiOff className="w-3 h-3" />
                    <span>Offline</span>
                  </div>
                )}
                <Button
                  onClick={handleAcknowledgeClick}
                  disabled={isAcknowledging}
                  size="lg"
                  className="min-w-[44px] min-h-[44px]" // AC#4: Touch target
                >
                  {isAcknowledging ? (
                    <>
                      <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin mr-2" />
                      Acknowledging...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="w-5 h-5 mr-2" />
                      Acknowledge Handoff
                    </>
                  )}
                </Button>
              </div>
            )}

            {/* Pending sync indicator (Story 9.7 AC#4) */}
            {hasPendingAcknowledgment && (
              <div className="flex items-center gap-2 px-3 py-2 rounded-md bg-warning-amber/10 border border-warning-amber/30">
                <WifiOff className="w-4 h-4 text-warning-amber" />
                <span className="text-sm text-warning-amber-dark">
                  Acknowledgment pending sync
                </span>
              </div>
            )}

            {/* Already acknowledged indicator (Story 9.7 AC#2) */}
            {handoff.status === 'acknowledged' && handoff.acknowledged_at && (
              <div className="flex flex-col items-end gap-1">
                <div className="flex items-center gap-2 text-success-green">
                  <CheckCircle className="w-5 h-5" />
                  <span className="text-sm font-medium">
                    Acknowledged
                  </span>
                </div>
                <span className="text-xs text-muted-foreground">
                  {formatTime(handoff.acknowledged_at)}
                  {acknowledgedByName && ` by ${acknowledgedByName}`}
                </span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Shift Summary section */}
      {handoff.summary_text && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Shift Summary
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose prose-sm max-w-none dark:prose-invert">
              <p className="text-base leading-relaxed whitespace-pre-wrap">
                {handoff.summary_text}
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Text Notes section */}
      {handoff.text_notes && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Additional Notes
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-base text-muted-foreground whitespace-pre-wrap">
              {handoff.text_notes}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Voice Notes section */}
      <VoiceNoteSection notes={handoff.voice_notes} />

      {/* Q&A Section (Story 9.6) */}
      {handoff.status !== 'draft' && (
        <HandoffQA
          handoffId={handoff.id}
          isCreator={isCreator}
          canRespond={isCreator}
          onPushToTalk={onPushToTalk}
          voiceTranscript={voiceTranscript}
          isVoiceActive={isVoiceActive}
        />
      )}

      {/* Acknowledgment notes section (Story 9.7 AC#3) */}
      {handoff.status === 'acknowledged' && acknowledgmentNotes && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <MessageSquare className="w-5 h-5" />
              Acknowledgment Notes
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-base text-muted-foreground whitespace-pre-wrap">
              {acknowledgmentNotes}
            </p>
            {acknowledgedByName && (
              <p className="text-sm text-muted-foreground mt-2 italic">
                - {acknowledgedByName}
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Assets covered section */}
      {handoff.assets_covered.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">
              Assets Covered ({handoff.assets_covered.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {handoff.assets_covered.map((assetId) => (
                <Badge key={assetId} variant="secondary">
                  {assetId}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Acknowledgment Dialog (Story 9.7 AC#1) */}
      <HandoffAcknowledge
        isOpen={showAckDialog}
        onClose={() => setShowAckDialog(false)}
        onConfirm={handleAcknowledgeConfirm}
        handoffId={handoff.id}
        creatorName={handoff.creator_name}
        shiftDate={handoff.shift_date}
        shiftType={handoff.shift_type}
        isLoading={isAcknowledging}
        error={acknowledgeError}
        isOffline={isOffline}
      />
    </div>
  );
}

export default HandoffViewer;
