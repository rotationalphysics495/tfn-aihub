'use client';

/**
 * HandoffCard Component (Story 9.5, Task 3)
 *
 * Displays a handoff summary in a card format for list views.
 *
 * @see Story 9.5 - Handoff Review UI
 * @see AC#1 - Handoff Notification Banner
 * @see AC#2 - Handoff Detail View (preview)
 */

import { useRouter } from 'next/navigation';
import { Clock, User, ChevronRight, Mic } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type { HandoffListItem, HandoffStatus } from '@/types/handoff';

// ============================================================================
// Types
// ============================================================================

export interface HandoffCardProps {
  /** Handoff data */
  handoff: HandoffListItem;
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
    weekday: 'short',
    month: 'short',
    day: 'numeric',
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
      return 'Pending';
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
// Component
// ============================================================================

/**
 * HandoffCard displays a handoff summary in the list view.
 *
 * Features:
 * - Displays outgoing supervisor name and timestamp
 * - Shows summary preview
 * - Indicates pending/acknowledged status
 * - Links to detail page
 * - Touch-optimized for tablet (44x44px targets)
 *
 * @example
 * ```tsx
 * <HandoffCard handoff={handoffItem} />
 * ```
 */
export function HandoffCard({ handoff, className }: HandoffCardProps) {
  const router = useRouter();

  const isPending = handoff.status === 'pending_acknowledgment';

  // Handle card click for drill-down
  const handleClick = () => {
    router.push(`/handoff/${handoff.id}`);
  };

  return (
    <Card
      className={cn(
        'cursor-pointer transition-all duration-200',
        'hover:shadow-md hover:scale-[1.01]',
        'focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
        isPending && 'border-l-4 border-l-info-blue',
        className
      )}
      onClick={handleClick}
      tabIndex={0}
      role="button"
      aria-label={`Handoff from ${handoff.creator_name} on ${formatDate(handoff.shift_date)}`}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleClick();
        }
      }}
    >
      <CardContent className="p-4 md:p-6">
        <div className="flex items-start gap-4">
          {/* Main content */}
          <div className="flex-1 min-w-0">
            {/* Header row with status badge */}
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <Badge
                variant={getStatusBadgeVariant(handoff.status)}
                className="text-xs"
              >
                {getStatusLabel(handoff.status)}
              </Badge>
              <span className="text-sm text-muted-foreground">
                {formatShiftType(handoff.shift_type)} Shift
              </span>
            </div>

            {/* Creator name - AC#8: 24px+ for key values */}
            <h3 className="text-xl md:text-2xl font-semibold text-foreground mb-2 leading-tight flex items-center gap-2">
              <User className="w-5 h-5 text-muted-foreground flex-shrink-0" />
              {handoff.creator_name}
            </h3>

            {/* Summary preview - AC#8: minimum 18px body */}
            {handoff.summary_preview && (
              <p className="text-base text-muted-foreground mb-3 line-clamp-2">
                {handoff.summary_preview}
              </p>
            )}

            {/* Metadata row */}
            <div className="flex flex-wrap items-center gap-3 text-sm">
              {/* Date */}
              <span className="flex items-center gap-1 text-muted-foreground">
                <Clock className="w-4 h-4" />
                {formatDate(handoff.shift_date)}
                {handoff.submitted_at && ` at ${formatTime(handoff.submitted_at)}`}
              </span>

              {/* Voice notes indicator */}
              {handoff.voice_note_count > 0 && (
                <span className="flex items-center gap-1 text-muted-foreground">
                  <Mic className="w-4 h-4" />
                  {handoff.voice_note_count} voice note
                  {handoff.voice_note_count !== 1 ? 's' : ''}
                </span>
              )}

              {/* Asset count */}
              <span className="text-muted-foreground">
                {handoff.assets_covered.length} asset
                {handoff.assets_covered.length !== 1 ? 's' : ''}
              </span>
            </div>
          </div>

          {/* Drill-down indicator */}
          <ChevronRight
            className="w-6 h-6 text-muted-foreground flex-shrink-0 self-center"
            aria-hidden="true"
          />
        </div>
      </CardContent>
    </Card>
  );
}

export default HandoffCard;
