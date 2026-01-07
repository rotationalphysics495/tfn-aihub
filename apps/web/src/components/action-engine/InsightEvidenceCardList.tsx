'use client'

import { useMemo } from 'react'
import { useDailyActions } from '@/hooks/useDailyActions'
import { ActionCardList } from './ActionCardList'
import { transformAPIActionItems } from './transformers'
import { cn } from '@/lib/utils'

/**
 * Insight + Evidence Card List with Data Integration
 *
 * A wrapper component that integrates with the useDailyActions hook
 * and transforms API data to the Insight + Evidence card format.
 *
 * This is the recommended component to use in the Morning Report view.
 *
 * @see Story 3.4 - Insight + Evidence Cards
 * @see AC #5 - Data Source Integration
 * @see AC #7 - Integration with Action List Primary View
 */

interface InsightEvidenceCardListProps {
  className?: string
}

export function InsightEvidenceCardList({ className }: InsightEvidenceCardListProps) {
  const {
    data,
    isLoading,
    error,
    refetch,
  } = useDailyActions()

  // Transform API action items to Insight + Evidence format
  const transformedItems = useMemo(() => {
    if (!data?.actions) return []
    return transformAPIActionItems(data.actions)
  }, [data?.actions])

  return (
    <ActionCardList
      items={transformedItems}
      isLoading={isLoading}
      error={error}
      onRefetch={refetch}
      className={cn('', className)}
    />
  )
}
