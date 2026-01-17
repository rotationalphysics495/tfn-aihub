'use client';

/**
 * HandoffAcknowledge Component (Story 9.7)
 *
 * Confirmation dialog for acknowledging receipt of a shift handoff.
 *
 * @see Story 9.7 - Acknowledgment Flow
 * @see AC#1 - Acknowledgment UI Trigger
 * @see AC#3 - Optional Notes Attachment
 */

import { useState, useCallback } from 'react';
import { CheckCircle, Loader2, MessageSquare } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { cn } from '@/lib/utils';

// ============================================================================
// Types
// ============================================================================

export interface HandoffAcknowledgeProps {
  /** Whether the dialog is open */
  isOpen: boolean;
  /** Called when dialog should close */
  onClose: () => void;
  /** Called when acknowledgment is confirmed */
  onConfirm: (notes?: string) => Promise<void>;
  /** Handoff ID being acknowledged */
  handoffId: string;
  /** Name of the outgoing supervisor */
  creatorName: string;
  /** Shift date string */
  shiftDate: string;
  /** Shift type */
  shiftType: string;
  /** Whether acknowledgment is in progress */
  isLoading?: boolean;
  /** Error message if any */
  error?: string | null;
  /** Whether offline mode is active (AC#4) */
  isOffline?: boolean;
  /** Optional CSS class name */
  className?: string;
}

// ============================================================================
// Constants
// ============================================================================

const NOTES_MAX_LENGTH = 500;

// ============================================================================
// Component
// ============================================================================

/**
 * HandoffAcknowledge displays a confirmation dialog for acknowledging handoffs.
 *
 * Features:
 * - Confirmation dialog with modal pattern (AC#1)
 * - Optional notes textarea with character limit (AC#3)
 * - Loading state and success/error feedback (Task 2.4)
 * - Offline indicator for queued acknowledgments (AC#4)
 *
 * @example
 * ```tsx
 * <HandoffAcknowledge
 *   isOpen={showAckDialog}
 *   onClose={() => setShowAckDialog(false)}
 *   onConfirm={handleAcknowledge}
 *   handoffId="123"
 *   creatorName="John Smith"
 *   shiftDate="2026-01-15"
 *   shiftType="morning"
 * />
 * ```
 */
export function HandoffAcknowledge({
  isOpen,
  onClose,
  onConfirm,
  handoffId,
  creatorName,
  shiftDate,
  shiftType,
  isLoading = false,
  error = null,
  isOffline = false,
  className,
}: HandoffAcknowledgeProps) {
  const [notes, setNotes] = useState('');
  const [showNotes, setShowNotes] = useState(false);

  // Format shift date for display
  const formattedDate = new Date(shiftDate).toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  });

  // Format shift type for display
  const formattedShiftType =
    shiftType.charAt(0).toUpperCase() + shiftType.slice(1);

  // Handle confirm with optional notes
  const handleConfirm = useCallback(async () => {
    const trimmedNotes = notes.trim();
    await onConfirm(trimmedNotes || undefined);
  }, [notes, onConfirm]);

  // Handle close and reset state
  const handleClose = useCallback(() => {
    if (!isLoading) {
      setNotes('');
      setShowNotes(false);
      onClose();
    }
  }, [isLoading, onClose]);

  // Character count for notes
  const notesLength = notes.length;
  const notesRemaining = NOTES_MAX_LENGTH - notesLength;

  return (
    <Dialog
      open={isOpen}
      onOpenChange={(open) => !open && !isLoading && handleClose()}
      modal={true}
    >
      <DialogContent
        className={cn('sm:max-w-[425px]', className)}
        onPointerDownOutside={(e) => isLoading && e.preventDefault()}
        onEscapeKeyDown={(e) => isLoading && e.preventDefault()}
      >
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-xl">
            <CheckCircle className="w-6 h-6 text-success-green" />
            Acknowledge Handoff
          </DialogTitle>
          <DialogDescription className="text-base pt-2">
            Confirm receipt of the shift handoff from{' '}
            <span className="font-medium text-foreground">{creatorName}</span>
            <br />
            <span className="text-muted-foreground">
              {formattedShiftType} Shift - {formattedDate}
            </span>
          </DialogDescription>
        </DialogHeader>

        {/* Offline indicator (AC#4) */}
        {isOffline && (
          <div className="rounded-md bg-warning-amber/10 border border-warning-amber/30 p-3 text-sm">
            <p className="text-warning-amber-dark font-medium">
              You are currently offline
            </p>
            <p className="text-muted-foreground mt-1">
              Your acknowledgment will be queued and synced when connectivity is
              restored.
            </p>
          </div>
        )}

        {/* Error message */}
        {error && (
          <div className="rounded-md bg-destructive/10 border border-destructive/30 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {/* Optional notes section (AC#3) */}
        <div className="space-y-3">
          {!showNotes ? (
            <Button
              type="button"
              variant="ghost"
              onClick={() => setShowNotes(true)}
              className="w-full justify-start text-muted-foreground hover:text-foreground"
              disabled={isLoading}
            >
              <MessageSquare className="w-4 h-4 mr-2" />
              Add a note (optional)
            </Button>
          ) : (
            <div className="space-y-2">
              <label
                htmlFor="acknowledgment-notes"
                className="text-sm font-medium"
              >
                Acknowledgment Notes (optional)
              </label>
              <Textarea
                id="acknowledgment-notes"
                placeholder="Add any questions or comments about this handoff..."
                value={notes}
                onChange={(e) =>
                  setNotes(e.target.value.slice(0, NOTES_MAX_LENGTH))
                }
                disabled={isLoading}
                className="min-h-[100px] resize-none"
                aria-describedby="notes-count"
              />
              <div
                id="notes-count"
                className={cn(
                  'text-xs text-right',
                  notesRemaining < 50
                    ? 'text-warning-amber'
                    : 'text-muted-foreground'
                )}
              >
                {notesRemaining} characters remaining
              </div>
            </div>
          )}
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button
            type="button"
            variant="outline"
            onClick={handleClose}
            disabled={isLoading}
            className="min-h-[44px]" // AC#4: Touch target
          >
            Cancel
          </Button>
          <Button
            type="button"
            onClick={handleConfirm}
            disabled={isLoading}
            className="min-h-[44px]" // AC#4: Touch target
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                {isOffline ? 'Queuing...' : 'Acknowledging...'}
              </>
            ) : (
              <>
                <CheckCircle className="w-4 h-4 mr-2" />
                {isOffline ? 'Queue Acknowledgment' : 'Acknowledge'}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default HandoffAcknowledge;
