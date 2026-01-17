'use client';

/**
 * HandoffList Component (Story 9.5, Task 2)
 *
 * Displays a list of handoffs filtered by supervisor assignments.
 *
 * @see Story 9.5 - Handoff Review UI
 * @see AC#1 - Handoff Notification Banner
 */

import { cn } from '@/lib/utils';
import { HandoffCard } from './HandoffCard';
import type { HandoffListItem } from '@/types/handoff';

// ============================================================================
// Types
// ============================================================================

export interface HandoffListProps {
  /** List of handoffs to display */
  handoffs: HandoffListItem[];
  /** Whether to show pending section header */
  showSections?: boolean;
  /** Loading state */
  isLoading?: boolean;
  /** Optional CSS class name */
  className?: string;
}

// ============================================================================
// Component
// ============================================================================

/**
 * HandoffList displays handoffs organized by status.
 *
 * Features:
 * - Pending and completed sections
 * - Loading skeleton state
 * - Empty state handling
 *
 * @example
 * ```tsx
 * <HandoffList handoffs={handoffs} showSections />
 * ```
 */
export function HandoffList({
  handoffs,
  showSections = true,
  isLoading = false,
  className,
}: HandoffListProps) {
  // Split into pending and completed
  const pendingHandoffs = handoffs.filter(
    (h) => h.status === 'pending_acknowledgment'
  );
  const completedHandoffs = handoffs.filter(
    (h) => h.status === 'acknowledged' || h.status === 'superseded'
  );

  // Loading skeleton
  if (isLoading) {
    return (
      <div className={cn('space-y-4', className)}>
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="h-32 bg-muted/50 rounded-lg animate-pulse"
          />
        ))}
      </div>
    );
  }

  // Empty state
  if (handoffs.length === 0) {
    return (
      <div
        className={cn(
          'flex flex-col items-center justify-center py-12 text-center',
          className
        )}
      >
        <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
          <svg
            className="w-8 h-8 text-muted-foreground"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-foreground mb-2">
          No handoffs yet
        </h3>
        <p className="text-sm text-muted-foreground max-w-sm">
          Handoffs from previous shifts will appear here when supervisors submit
          them for your assigned assets.
        </p>
      </div>
    );
  }

  // Render without sections
  if (!showSections) {
    return (
      <div className={cn('space-y-4', className)}>
        {handoffs.map((handoff) => (
          <HandoffCard key={handoff.id} handoff={handoff} />
        ))}
      </div>
    );
  }

  // Render with sections
  return (
    <div className={cn('space-y-8', className)}>
      {/* Pending handoffs section */}
      {pendingHandoffs.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
            <span className="flex items-center justify-center w-6 h-6 rounded-full bg-info-blue text-white text-sm font-medium">
              {pendingHandoffs.length}
            </span>
            Pending Review
          </h2>
          <div className="space-y-4">
            {pendingHandoffs.map((handoff) => (
              <HandoffCard key={handoff.id} handoff={handoff} />
            ))}
          </div>
        </section>
      )}

      {/* Completed handoffs section */}
      {completedHandoffs.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-muted-foreground mb-4">
            Previously Reviewed
          </h2>
          <div className="space-y-4">
            {completedHandoffs.map((handoff) => (
              <HandoffCard key={handoff.id} handoff={handoff} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

export default HandoffList;
