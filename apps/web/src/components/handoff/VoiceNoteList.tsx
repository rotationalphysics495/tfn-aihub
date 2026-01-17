'use client';

/**
 * VoiceNoteList Component (Story 9.3, Task 5)
 *
 * Displays a list of recorded voice notes with playback, reordering, and deletion.
 *
 * AC#3: Multiple Voice Notes Management
 * - Shows sequence number badge
 * - Duration display (e.g., "0:45")
 * - Timestamp
 * - Play button for review
 * - Delete button (with confirmation)
 * - Drag-and-drop reordering
 * - Expandable transcript
 *
 * References:
 * - [Source: epic-9.md#Story 9.3]
 * - [Source: prd-functional-requirements.md#FR23]
 */

import React, { useState, useCallback } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { VoiceNotePlayer } from './VoiceNotePlayer';
import type { VoiceNote } from './VoiceNoteRecorder';

// ============================================================================
// Types
// ============================================================================

export interface VoiceNoteListProps {
  /** List of voice notes */
  notes: VoiceNote[];
  /** Called when a note is deleted */
  onDelete: (noteId: string) => void;
  /** Called when notes are reordered */
  onReorder?: (noteIds: string[]) => void;
  /** Loading state for delete operation */
  deletingId?: string | null;
  /** Whether the list is editable */
  editable?: boolean;
  /** Custom class name */
  className?: string;
}

// ============================================================================
// Helper Functions
// ============================================================================

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function formatTimestamp(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
}

// ============================================================================
// Component
// ============================================================================

/**
 * VoiceNoteList component for displaying voice notes.
 *
 * Story 9.3 Implementation:
 * - AC#3: Displays all voice notes with metadata
 * - Supports playback, deletion, and transcript viewing
 *
 * Usage:
 * ```tsx
 * <VoiceNoteList
 *   notes={voiceNotes}
 *   onDelete={(id) => handleDelete(id)}
 *   editable={true}
 * />
 * ```
 */
export function VoiceNoteList({
  notes,
  onDelete,
  onReorder,
  deletingId,
  editable = true,
  className,
}: VoiceNoteListProps) {
  // State
  const [expandedTranscripts, setExpandedTranscripts] = useState<Set<string>>(new Set());
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const [playingId, setPlayingId] = useState<string | null>(null);
  const [draggedId, setDraggedId] = useState<string | null>(null);
  const [dragOverId, setDragOverId] = useState<string | null>(null);

  // ============================================================================
  // Handlers
  // ============================================================================

  const toggleTranscript = useCallback((noteId: string) => {
    setExpandedTranscripts(prev => {
      const next = new Set(prev);
      if (next.has(noteId)) {
        next.delete(noteId);
      } else {
        next.add(noteId);
      }
      return next;
    });
  }, []);

  const handleDeleteClick = useCallback((noteId: string) => {
    setConfirmDeleteId(noteId);
  }, []);

  const handleConfirmDelete = useCallback(() => {
    if (confirmDeleteId) {
      onDelete(confirmDeleteId);
      setConfirmDeleteId(null);
    }
  }, [confirmDeleteId, onDelete]);

  const handleCancelDelete = useCallback(() => {
    setConfirmDeleteId(null);
  }, []);

  const handlePlay = useCallback((noteId: string) => {
    setPlayingId(noteId);
  }, []);

  const handlePlayEnd = useCallback(() => {
    setPlayingId(null);
  }, []);

  // ============================================================================
  // Drag and Drop Handlers
  // ============================================================================

  const handleDragStart = useCallback((e: React.DragEvent, noteId: string) => {
    if (!editable || !onReorder) return;
    setDraggedId(noteId);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', noteId);
  }, [editable, onReorder]);

  const handleDragOver = useCallback((e: React.DragEvent, noteId: string) => {
    if (!editable || !onReorder) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    if (noteId !== draggedId) {
      setDragOverId(noteId);
    }
  }, [editable, onReorder, draggedId]);

  const handleDragLeave = useCallback(() => {
    setDragOverId(null);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent, targetId: string) => {
    e.preventDefault();
    if (!editable || !onReorder || !draggedId || draggedId === targetId) {
      setDraggedId(null);
      setDragOverId(null);
      return;
    }

    // Calculate new order
    const currentOrder = notes.map(n => n.id);
    const draggedIndex = currentOrder.indexOf(draggedId);
    const targetIndex = currentOrder.indexOf(targetId);

    // Remove dragged item and insert at new position
    const newOrder = [...currentOrder];
    newOrder.splice(draggedIndex, 1);
    newOrder.splice(targetIndex, 0, draggedId);

    onReorder(newOrder);
    setDraggedId(null);
    setDragOverId(null);
  }, [editable, onReorder, draggedId, notes]);

  const handleDragEnd = useCallback(() => {
    setDraggedId(null);
    setDragOverId(null);
  }, []);

  // ============================================================================
  // Render
  // ============================================================================

  if (notes.length === 0) {
    return (
      <div className={cn('text-center py-8 text-muted-foreground', className)}>
        No voice notes attached
      </div>
    );
  }

  return (
    <div className={cn('space-y-3', className)}>
      {notes.map((note, index) => {
        const isExpanded = expandedTranscripts.has(note.id);
        const isConfirmingDelete = confirmDeleteId === note.id;
        const isDeleting = deletingId === note.id;
        const isPlaying = playingId === note.id;
        const isDragging = draggedId === note.id;
        const isDragOver = dragOverId === note.id;

        return (
          <div
            key={note.id}
            className={cn(
              'border rounded-lg p-3 transition-all',
              isDragging && 'opacity-50 scale-95',
              isDragOver && 'border-primary border-2',
              isDeleting && 'opacity-50 pointer-events-none'
            )}
            draggable={editable && !!onReorder}
            onDragStart={(e) => handleDragStart(e, note.id)}
            onDragOver={(e) => handleDragOver(e, note.id)}
            onDragLeave={handleDragLeave}
            onDrop={(e) => handleDrop(e, note.id)}
            onDragEnd={handleDragEnd}
          >
            {/* Header row */}
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-3">
                {/* Sequence badge */}
                <div className="w-6 h-6 rounded-full bg-primary text-primary-foreground text-xs font-medium flex items-center justify-center">
                  {index + 1}
                </div>

                {/* Duration */}
                <span className="text-sm font-medium">
                  {formatDuration(note.duration_seconds)}
                </span>

                {/* Timestamp */}
                <span className="text-xs text-muted-foreground">
                  {formatTimestamp(note.created_at)}
                </span>
              </div>

              {/* Action buttons */}
              <div className="flex items-center gap-2">
                {/* Play button */}
                <button
                  type="button"
                  onClick={() => handlePlay(note.id)}
                  className={cn(
                    'p-1.5 rounded-full transition-colors',
                    isPlaying
                      ? 'bg-primary text-white'
                      : 'hover:bg-muted'
                  )}
                  aria-label={isPlaying ? 'Playing' : 'Play voice note'}
                >
                  {isPlaying ? (
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                      <rect x="6" y="4" width="4" height="16" rx="1" />
                      <rect x="14" y="4" width="4" height="16" rx="1" />
                    </svg>
                  ) : (
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M8 5v14l11-7z" />
                    </svg>
                  )}
                </button>

                {/* Transcript toggle */}
                {note.transcript && (
                  <button
                    type="button"
                    onClick={() => toggleTranscript(note.id)}
                    className={cn(
                      'p-1.5 rounded-full transition-colors',
                      isExpanded ? 'bg-muted' : 'hover:bg-muted'
                    )}
                    aria-label={isExpanded ? 'Hide transcript' : 'Show transcript'}
                    aria-expanded={isExpanded}
                  >
                    <svg
                      className={cn('w-4 h-4 transition-transform', isExpanded && 'rotate-180')}
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                )}

                {/* Delete button */}
                {editable && (
                  <button
                    type="button"
                    onClick={() => handleDeleteClick(note.id)}
                    className="p-1.5 rounded-full hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-colors"
                    aria-label="Delete voice note"
                    disabled={isDeleting}
                  >
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                )}

                {/* Drag handle */}
                {editable && onReorder && (
                  <div className="p-1.5 cursor-grab text-muted-foreground">
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M8 6h2v2H8V6zm6 0h2v2h-2V6zM8 11h2v2H8v-2zm6 0h2v2h-2v-2zM8 16h2v2H8v-2zm6 0h2v2h-2v-2z" />
                    </svg>
                  </div>
                )}
              </div>
            </div>

            {/* Audio player (when playing) */}
            {isPlaying && note.storage_url && (
              <div className="mb-2">
                <VoiceNotePlayer
                  src={note.storage_url}
                  onEnded={handlePlayEnd}
                  autoPlay
                />
              </div>
            )}

            {/* Expandable transcript */}
            {note.transcript && isExpanded && (
              <div className="mt-2 pt-2 border-t">
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                  {note.transcript}
                </p>
              </div>
            )}

            {/* No transcript indicator */}
            {!note.transcript && (
              <div className="text-xs text-muted-foreground italic">
                Transcript unavailable
              </div>
            )}

            {/* Delete confirmation */}
            {isConfirmingDelete && (
              <div className="mt-3 pt-3 border-t flex items-center justify-between bg-destructive/5 -mx-3 -mb-3 p-3 rounded-b-lg">
                <span className="text-sm text-destructive">Delete this voice note?</span>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCancelDelete}
                  >
                    Cancel
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={handleConfirmDelete}
                    disabled={isDeleting}
                  >
                    {isDeleting ? 'Deleting...' : 'Delete'}
                  </Button>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

export default VoiceNoteList;
