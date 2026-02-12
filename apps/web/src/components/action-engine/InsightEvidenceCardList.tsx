'use client'

import { useMemo } from 'react'
import { CheckCircle2 } from 'lucide-react'
import { useDailyActions } from '@/hooks/useDailyActions'
import { useActionAcknowledgment } from '@/hooks/useActionAcknowledgment'
import { useFollowUps } from '@/hooks/useFollowUps'
import { ActionCardList } from './ActionCardList'
import { transformAPIActionItems } from './transformers'
import { cn } from '@/lib/utils'

/**
 * Insight + Evidence Card List with Data Integration
 *
 * A wrapper component that integrates with the useDailyActions hook
 * and transforms API data to the Insight + Evidence card format.
 * Includes acknowledgment tracking and "All items reviewed" banner.
 *
 * This is the recommended component to use in the Morning Report view.
 *
 * @see Story 3.4 - Insight + Evidence Cards
 * @see Story 13.2 - Action Acknowledgment UI
 * @see AC #5 - Data Source Integration
 * @see AC #7 - Integration with Action List Primary View
 */

interface InsightEvidenceCardListProps {
  className?: string
  reportDate?: string
}

export function InsightEvidenceCardList({ className, reportDate: reportDateProp }: InsightEvidenceCardListProps) {
  const {
    data,
    isLoading,
    error,
    refetch,
  } = useDailyActions(reportDateProp ? { reportDate: reportDateProp } : {})

  // Transform API action items to Insight + Evidence format
  const transformedItems = useMemo(() => {
    if (!data?.actions) return []
    return transformAPIActionItems(data.actions)
  }, [data?.actions])

  // Build acknowledgment input items from transformed data
  const ackItems = useMemo(() => {
    return transformedItems.map(item => ({
      id: item.id,
      acknowledgment: item.acknowledgment ?? null,
    }))
  }, [transformedItems])

  // Follow-up data hook (Story 13.4)
  const reportDate = data?.report_date ?? null
  const { followUps, refetch: refetchFollowUps } = useFollowUps({ reportDate })

  // Acknowledgment tracking hook
  const {
    acknowledge,
    acknowledgedCount,
    totalCount,
    getAcknowledgment,
  } = useActionAcknowledgment({ items: ackItems })

  // Merge acknowledgment state back into items for rendering
  const itemsWithAckState = useMemo(() => {
    return transformedItems.map(item => {
      const ack = getAcknowledgment(item.id)
      return {
        ...item,
        acknowledgment: ack,
      }
    })
  }, [transformedItems, getAcknowledgment])

  const allReviewed = acknowledgedCount === totalCount && totalCount > 0

  return (
    <div data-acknowledgment-tracking="true" className={cn('', className)}>
      {/* "All items reviewed" banner */}
      {allReviewed && (
        <div className="mb-4 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 p-4 flex items-center gap-3">
          <CheckCircle2 className="w-5 h-5 text-green-600 dark:text-green-400 flex-shrink-0" aria-hidden="true" />
          <span className="font-medium text-green-800 dark:text-green-200">
            All items reviewed
          </span>
          <span className="text-sm text-green-600 dark:text-green-400">
            {acknowledgedCount}/{totalCount} reviewed
          </span>
        </div>
      )}

      <ActionCardList
        items={itemsWithAckState}
        isLoading={isLoading}
        error={error}
        onRefetch={refetch}
        onAcknowledge={acknowledge}
        followUps={followUps}
        onFollowUpAssigned={refetchFollowUps}
      />
    </div>
  )
}
