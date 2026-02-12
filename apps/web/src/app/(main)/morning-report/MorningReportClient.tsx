'use client'

import { useState, useCallback, useMemo } from 'react'
import { useSearchParams, useRouter, usePathname } from 'next/navigation'
import { format, subDays, startOfDay, isValid, parseISO } from 'date-fns'
import { SafetyAlertsSection } from '@/components/dashboard'
import { MorningSummarySection, MyAssignmentsPanel } from '@/components/action-list'
import { InsightEvidenceCardList } from '@/components/action-engine'
import { Breadcrumb } from '@/components/navigation'
import { WorkcenterScorecard, ScheduleAttainment } from '@/components/production'
import { useDailyActions } from '@/hooks/useDailyActions'

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

  const handleDateChange = useCallback(
    (newDate: Date) => {
      setSelectedDate(newDate)
      const formatted = format(newDate, 'yyyy-MM-dd')
      router.push(`${pathname}?date=${formatted}`, { scroll: false })
    },
    [router, pathname]
  )

  // Empty state detection: use useDailyActions to check if data exists for the selected date
  const { data: actionsData, isLoading: actionsLoading, error: actionsError } = useDailyActions({ reportDate })
  const hasLoadedWithNoData =
    !actionsLoading &&
    !actionsError &&
    actionsData !== null &&
    actionsData.actions.length === 0

  const formattedDateDisplay = format(selectedDate, 'MMM d, yyyy')

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8">
      {/* Safety Alert Banner - Prominent display */}
      <SafetyAlertsSection className="mb-6" />

      {/* Breadcrumb navigation */}
      <Breadcrumb className="mb-4" />

      {/* Page Header */}
      <div className="mb-6 md:mb-8">
        <h1 className="page-title text-foreground">
          Morning Report
        </h1>
        <p className="body-text text-muted-foreground mt-2">
          Daily action items prioritized for your morning review.
        </p>
      </div>

      {/* Empty state for missing data - AC #5 */}
      {hasLoadedWithNoData ? (
        <div className="space-y-6">
          <MorningSummarySection
            reportDate={reportDate}
            onDateChange={handleDateChange}
            selectedDate={selectedDate}
          />
          <div className="rounded-lg border p-12 text-center">
            <p className="text-base text-muted-foreground">
              No production data available for {formattedDateDisplay}.
            </p>
          </div>
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

          {/* Workcenter Production Scorecard */}
          <WorkcenterScorecard date={reportDate} />

          {/* Schedule Attainment */}
          <ScheduleAttainment date={reportDate} />

          {/* Action List */}
          <section aria-label="Action items with evidence">
            <h2 className="section-header text-foreground mb-4">
              Action Items
            </h2>
            <InsightEvidenceCardList reportDate={reportDate} />
          </section>
        </div>
      )}
    </div>
  )
}
