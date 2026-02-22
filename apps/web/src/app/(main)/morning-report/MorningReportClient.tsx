'use client'

import { useState, useCallback, useMemo } from 'react'
import { useSearchParams, useRouter, usePathname } from 'next/navigation'
import { format, subDays, startOfDay, isValid, parseISO } from 'date-fns'
import { SafetyAlertsSection } from '@/components/dashboard'
import { MorningSummarySection, MyAssignmentsPanel } from '@/components/action-list'
import { InsightEvidenceCardList } from '@/components/action-engine'
import type { ActionItem as InsightActionItem } from '@/components/action-engine/types'
import type { PriorityType } from '@/components/action-engine/PriorityBadge'
import { Breadcrumb } from '@/components/navigation'
import { WorkcenterScorecard, ScheduleAttainment, ShiftTabs } from '@/components/production'
import { useDailyActions } from '@/hooks/useDailyActions'
import { useFollowUps } from '@/hooks/useFollowUps'
import { MeetingModeToggle } from '@/components/report/MeetingModeToggle'
import { MeetingModeView } from '@/components/report/MeetingModeView'

function getYesterday(): Date {
  return startOfDay(subDays(new Date(), 1))
}

function parseDateParam(param: string | null): Date {
  if (!param) return getYesterday()

  const parsed = parseISO(param)
  if (!isValid(parsed)) return getYesterday()

  const yesterday = getYesterday()
  if (startOfDay(parsed) > yesterday) return yesterday

  return startOfDay(parsed)
}

export function MorningReportClient() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const pathname = usePathname()

  const [selectedDate, setSelectedDate] = useState<Date>(() =>
    parseDateParam(searchParams.get('date'))
  )

  const reportDate = useMemo(
    () => format(selectedDate, 'yyyy-MM-dd'),
    [selectedDate]
  )

  // Story 17.4: Shift filter state synced with URL
  const [selectedShift, setSelectedShift] = useState<string>(
    () => searchParams.get('shift') || 'all'
  )

  // Story 18.1: Meeting mode state initialized from URL
  const [isMeetingMode, setIsMeetingMode] = useState<boolean>(
    () => searchParams.get('mode') === 'meeting'
  )

  const handleDateChange = useCallback(
    (newDate: Date) => {
      setSelectedDate(newDate)
      const formatted = format(newDate, 'yyyy-MM-dd')
      const shiftParam = selectedShift !== 'all' ? `&shift=${selectedShift}` : ''
      const modeParam = isMeetingMode ? '&mode=meeting' : ''
      router.push(`${pathname}?date=${formatted}${shiftParam}${modeParam}`, { scroll: false })
    },
    [router, pathname, selectedShift, isMeetingMode]
  )

  const handleShiftChange = useCallback(
    (shift: string) => {
      setSelectedShift(shift)
      const shiftParam = shift !== 'all' ? `&shift=${shift}` : ''
      const modeParam = isMeetingMode ? '&mode=meeting' : ''
      router.push(`${pathname}?date=${reportDate}${shiftParam}${modeParam}`, { scroll: false })
    },
    [router, pathname, reportDate, isMeetingMode]
  )

  // Story 18.1: Meeting mode toggle handler with URL state sync
  const handleMeetingModeToggle = useCallback(
    (isMeeting: boolean) => {
      setIsMeetingMode(isMeeting)
      const params = new URLSearchParams(searchParams.toString())
      if (isMeeting) {
        params.set('mode', 'meeting')
      } else {
        params.delete('mode')
      }
      router.push(`${pathname}?${params.toString()}`, { scroll: false })
    },
    [router, pathname, searchParams]
  )

  // Empty state detection: use useDailyActions to check if data exists for the selected date
  const { data: actionsData, isLoading: actionsLoading, error: actionsError } = useDailyActions({ reportDate })
  const hasLoadedWithNoData =
    !actionsLoading &&
    !actionsError &&
    actionsData !== null &&
    actionsData.actions.length === 0

  // Story 18.1: Transform actions for meeting mode
  const meetingModeItems = useMemo((): InsightActionItem[] => {
    if (!actionsData?.actions) return []
    return actionsData.actions.map((item: any) => {
      const category = item.category as string
      const priorityMap: Record<string, PriorityType> = { safety: 'SAFETY', financial: 'FINANCIAL', oee: 'OEE' }
      const priority = priorityMap[category] ?? 'OEE'

      // Handle both API field names (id) and alternative names (action_item_id)
      const id = item.id ?? item.action_item_id ?? ''
      const priorityScore = item.priority_rank ?? item.priority_score ?? 500
      const recText = item.recommendation_text ?? item.title ?? ''
      const recSummary = item.evidence_summary ?? item.recommendation_summary ?? item.description ?? ''
      const assetId = item.asset_id ?? ''
      const assetName = item.asset_name ?? ''
      const financialImpact = item.financial_impact_usd ?? item.financial_impact ?? 0

      return {
        id,
        priority,
        priorityScore,
        recommendation: { text: recText, summary: recSummary },
        asset: { id: assetId, name: assetName, area: item.asset_area ?? '' },
        evidence: {
          type: (item.evidence_type ?? (category === 'safety' ? 'safety_event' : category === 'oee' ? 'oee_deviation' : 'financial_loss')) as any,
          data: item.evidence_data ?? {},
          source: {
            table: item.evidence_source_table ?? 'daily_summaries',
            date: item.evidence_source_date ?? reportDate,
            recordId: item.evidence_source_record_id ?? '',
          },
        },
        financialImpact,
        timestamp: item.created_at ?? item.generated_at ?? new Date().toISOString(),
      } satisfies InsightActionItem
    })
  }, [actionsData?.actions, reportDate])

  // Story 18.1: Follow-up data for meeting mode (only fetch when meeting mode is active)
  const meetingReportDate = isMeetingMode ? (actionsData?.report_date ?? null) : null
  const { followUps } = useFollowUps({ reportDate: meetingReportDate })

  const formattedDateDisplay = format(selectedDate, 'MMM d, yyyy')

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8">
      {/* Safety Alert Banner - Prominent display */}
      <SafetyAlertsSection className="mb-6" />

      {/* Breadcrumb navigation */}
      <Breadcrumb className="mb-4" />

      {/* Page Header */}
      <div className="mb-6 md:mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="page-title text-foreground">
            Morning Report
          </h1>
          <p className="body-text text-muted-foreground mt-2">
            Daily action items prioritized for your morning review.
          </p>
        </div>
        <MeetingModeToggle
          pressed={isMeetingMode}
          onToggle={handleMeetingModeToggle}
        />
      </div>

      {/* Empty state for missing data - AC #5 */}
      {hasLoadedWithNoData ? (
        <div className="space-y-6">
          <MorningSummarySection
            reportDate={reportDate}
            onDateChange={handleDateChange}
            selectedDate={selectedDate}
          />
          <ShiftTabs value={selectedShift} onValueChange={handleShiftChange} />
          <WorkcenterScorecard date={reportDate} selectedShift={selectedShift} />
          <ScheduleAttainment date={reportDate} />
          <div className="rounded-lg border p-12 text-center">
            <p className="text-base text-muted-foreground">
              No action items available for {formattedDateDisplay}.
            </p>
          </div>
        </div>
      ) : isMeetingMode ? (
        /* Story 18.1: Meeting mode view */
        <div className="space-y-6">
          <MeetingModeView
            items={meetingModeItems}
            followUps={followUps}
            reportDate={reportDate}
          />
        </div>
      ) : (
        <div className="space-y-6">
          {/* Morning Summary Section */}
          <MorningSummarySection
            reportDate={reportDate}
            onDateChange={handleDateChange}
            selectedDate={selectedDate}
          />

          {/* My Assignments Panel */}
          <MyAssignmentsPanel />

          {/* Story 17.4: Shift filter tabs */}
          <ShiftTabs value={selectedShift} onValueChange={handleShiftChange} />

          {/* Workcenter Production Scorecard */}
          <WorkcenterScorecard date={reportDate} selectedShift={selectedShift} />

          {/* Schedule Attainment */}
          <ScheduleAttainment date={reportDate} />

          {/* Action List */}
          <section aria-label="Action items with evidence">
            <h2 className="section-header text-foreground mb-4">
              Action Items
            </h2>
            <InsightEvidenceCardList reportDate={reportDate} selectedShift={selectedShift} />
          </section>
        </div>
      )}
    </div>
  )
}
