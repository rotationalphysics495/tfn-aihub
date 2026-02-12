'use client'

import { useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { InsightSection } from './InsightSection'
import { EvidenceSection } from './EvidenceSection'
import { AssignFollowUpDialog } from './AssignFollowUpDialog'
import { getPriorityBorderColor, getPriorityAccentBg } from './PriorityBadge'
import type { ActionItem, FollowUpData } from './types'

/**
 * Insight + Evidence Card Component
 *
 * Main card component that combines insight (left) and evidence (right) sections.
 * Follows the "Insight + Evidence" design principle from the UX design.
 *
 * Features:
 * - Two-column layout (side-by-side on desktop/tablet, stacked on mobile)
 * - Priority-based color coding (Safety Red, Amber, Yellow)
 * - 4px left border indicating priority
 * - Industrial Clarity high-contrast styling
 * - Accessible with ARIA labels and keyboard navigation
 *
 * @see Story 3.4 - Insight + Evidence Cards
 * @see AC #1 - Insight + Evidence Card Component
 * @see AC #4 - Visual Hierarchy and Priority Styling
 * @see AC #7 - Performance and Accessibility
 */

interface InsightEvidenceCardProps {
  item: ActionItem
  className?: string
  defaultEvidenceExpanded?: boolean
  onAcknowledge?: (actionId: string) => void
  followUp?: FollowUpData
  onFollowUpAssigned?: () => void
}

export function InsightEvidenceCard({
  item,
  className,
  defaultEvidenceExpanded = false,
  onAcknowledge,
  followUp,
  onFollowUpAssigned,
}: InsightEvidenceCardProps) {
  const [isHovered, setIsHovered] = useState(false)
  const [assignDialogOpen, setAssignDialogOpen] = useState(false)

  const borderColor = getPriorityBorderColor(item.priority)
  const accentBg = getPriorityAccentBg(item.priority)
  const isItemAcknowledged = item.acknowledgment != null

  // Derive report date from item timestamp (fallback to yesterday)
  const reportDate = item.timestamp
    ? item.timestamp.split('T')[0]
    : new Date(Date.now() - 86400000).toISOString().split('T')[0]

  return (
    <>
      <Card
        mode="retrospective"
        className={cn(
          // Base card styling
          'overflow-hidden transition-all duration-200',
          // 4px left border with priority color (AC #4)
          'border-l-4',
          isItemAcknowledged ? 'border-l-muted' : borderColor,
          // Priority-based background accent (AC #4)
          accentBg,
          // Hover state (AC #6)
          'hover:shadow-lg',
          isHovered && 'scale-[1.005]',
          // Focus visible state for accessibility (AC #7)
          'focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2',
          // Acknowledged muted styling
          isItemAcknowledged && 'opacity-60',
          className
        )}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        role="article"
        aria-label={`${item.priority} priority action: ${item.recommendation.summary}`}
      >
        <CardContent className="p-0">
          {/* Two-column grid: side-by-side on md+, stacked on mobile (AC #1) */}
          <div className="grid grid-cols-1 md:grid-cols-2">
            {/* Left side: Insight/Recommendation (AC #2) */}
            <div className="p-4 md:p-6 md:border-r border-border">
              <InsightSection
                priority={item.priority}
                recommendation={item.recommendation}
                asset={item.asset}
                financialImpact={item.financialImpact}
                timestamp={item.timestamp}
                onAssign={() => setAssignDialogOpen(true)}
                isAcknowledged={isItemAcknowledged}
                acknowledgedAt={item.acknowledgment?.acknowledged_at}
                onAcknowledge={onAcknowledge ? () => onAcknowledge(item.id) : undefined}
                followUp={followUp}
                trendData={item.trendData}
                shiftAttribution={item.shiftAttribution}
              />
            </div>

            {/* Right side: Evidence/Supporting Data (AC #3) */}
            <div className="bg-industrial-50/50 dark:bg-industrial-900/30">
              <EvidenceSection
                evidence={item.evidence}
                defaultExpanded={defaultEvidenceExpanded}
                assetId={item.asset.id}
                reportDate={reportDate}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <AssignFollowUpDialog
        open={assignDialogOpen}
        onOpenChange={(open) => {
          setAssignDialogOpen(open)
          if (!open) onFollowUpAssigned?.()
        }}
        actionItem={{
          id: item.id,
          priority: item.priority,
          recommendationText: item.recommendation.text,
          assetName: item.asset.name,
          category: item.priority.toLowerCase(),
          reportDate,
        }}
      />
    </>
  )
}

/**
 * Skeleton loader for InsightEvidenceCard
 */
export function InsightEvidenceCardSkeleton() {
  return (
    <Card mode="retrospective" className="overflow-hidden border-l-4 border-l-industrial-300">
      <CardContent className="p-0">
        <div className="grid grid-cols-1 md:grid-cols-2 animate-pulse">
          {/* Left side skeleton */}
          <div className="p-4 md:p-6 md:border-r border-border space-y-4">
            {/* Priority badge skeleton */}
            <div className="h-8 w-28 bg-industrial-200 dark:bg-industrial-700 rounded-md" />
            {/* Title skeleton */}
            <div className="space-y-2">
              <div className="h-6 bg-industrial-200 dark:bg-industrial-700 rounded w-full" />
              <div className="h-6 bg-industrial-200 dark:bg-industrial-700 rounded w-3/4" />
            </div>
            {/* Context skeleton */}
            <div className="flex gap-4">
              <div className="h-5 w-32 bg-industrial-200 dark:bg-industrial-700 rounded" />
              <div className="h-5 w-24 bg-industrial-200 dark:bg-industrial-700 rounded" />
            </div>
          </div>

          {/* Right side skeleton */}
          <div className="bg-industrial-50/50 dark:bg-industrial-900/30 p-4">
            <div className="space-y-3">
              <div className="h-10 bg-industrial-200 dark:bg-industrial-700 rounded" />
              <div className="h-4 w-48 bg-industrial-200 dark:bg-industrial-700 rounded" />
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
