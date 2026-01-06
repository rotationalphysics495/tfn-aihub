'use client'

import { useCallback, useEffect, useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import { cn } from '@/lib/utils'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ParetoChart, type ParetoItem } from './ParetoChart'
import { DowntimeTable, type DowntimeEvent } from './DowntimeTable'
import { CostOfLossWidget, type CostOfLossSummaryData } from './CostOfLossWidget'
import { TimeWindowToggle } from './TimeWindowToggle'
import { DowntimeFilterBar } from './DowntimeFilterBar'
import { SafetyEventModal, type SafetyEventDetail } from './SafetyEventModal'

/**
 * Downtime Dashboard Client Component
 *
 * Main container for Downtime Pareto Analysis.
 * Handles data fetching, state management, auto-refresh, and filtering.
 *
 * @see Story 2.5 - Downtime Pareto Analysis
 * @see AC #7 - Time Window Toggle with auto-refresh for Live view
 */

interface ParetoResponse {
  items: ParetoItem[]
  total_downtime_minutes: number
  total_financial_impact: number
  total_events: number
  data_source: string
  last_updated: string
  threshold_80_index: number | null
}

interface EventsResponse {
  events: DowntimeEvent[]
  total_count: number
  total_downtime_minutes: number
  total_financial_impact: number
  data_source: string
  last_updated: string
}

// Auto-refresh interval: 15 minutes per AC#7 for Live view
const AUTO_REFRESH_INTERVAL = 15 * 60 * 1000

type DataView = 'yesterday' | 'live'

export function DowntimeDashboard() {
  const [paretoData, setParetoData] = useState<ParetoResponse | null>(null)
  const [eventsData, setEventsData] = useState<EventsResponse | null>(null)
  const [summaryData, setSummaryData] = useState<CostOfLossSummaryData | null>(null)
  const [areas, setAreas] = useState<string[]>([])

  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [activeView, setActiveView] = useState<DataView>('yesterday')
  const [selectedArea, setSelectedArea] = useState<string | null>(null)

  // Safety modal state
  const [selectedSafetyEvent, setSelectedSafetyEvent] = useState<SafetyEventDetail | null>(null)
  const [isSafetyModalOpen, setIsSafetyModalOpen] = useState(false)
  const [isSafetyLoading, setIsSafetyLoading] = useState(false)

  const fetchData = useCallback(async (showRefreshing = false) => {
    if (showRefreshing) {
      setIsRefreshing(true)
    }

    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.access_token) {
        setError('Authentication required')
        return
      }

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const source = activeView === 'live' ? 'live' : 'yesterday'

      // Build query params
      const params = new URLSearchParams()
      params.set('source', source)
      if (selectedArea) params.set('area', selectedArea)

      const headers = {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json',
      }

      // Fetch all data in parallel
      const [paretoRes, eventsRes, summaryRes] = await Promise.all([
        fetch(`${apiUrl}/api/v1/downtime/pareto?${params}`, { headers }),
        fetch(`${apiUrl}/api/v1/downtime/events?${params}&limit=500`, { headers }),
        fetch(`${apiUrl}/api/v1/downtime/summary?${params}`, { headers }),
      ])

      if (!paretoRes.ok || !eventsRes.ok || !summaryRes.ok) {
        throw new Error('Failed to fetch downtime data')
      }

      const [pareto, events, summary] = await Promise.all([
        paretoRes.json() as Promise<ParetoResponse>,
        eventsRes.json() as Promise<EventsResponse>,
        summaryRes.json() as Promise<CostOfLossSummaryData>,
      ])

      setParetoData(pareto)
      setEventsData(events)
      setSummaryData(summary)
      setError(null)
    } catch (err) {
      console.error('Failed to fetch downtime data:', err)
      setError('Failed to load downtime data. Please try again.')
    } finally {
      setIsLoading(false)
      setIsRefreshing(false)
    }
  }, [activeView, selectedArea])

  const fetchAreas = useCallback(async () => {
    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.access_token) return

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/v1/downtime/areas`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      })

      if (response.ok) {
        const areasData: string[] = await response.json()
        setAreas(areasData)
      }
    } catch (err) {
      console.error('Failed to fetch areas:', err)
    }
  }, [])

  const fetchSafetyEventDetail = useCallback(async (eventId: string) => {
    setIsSafetyLoading(true)
    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.access_token) return

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/v1/downtime/safety/${eventId}`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      })

      if (response.ok) {
        const detail: SafetyEventDetail = await response.json()
        setSelectedSafetyEvent(detail)
      }
    } catch (err) {
      console.error('Failed to fetch safety event detail:', err)
    } finally {
      setIsSafetyLoading(false)
    }
  }, [])

  // Fetch areas once on mount
  useEffect(() => {
    fetchAreas()
  }, [fetchAreas])

  // Fetch data on mount and when view/filter changes
  useEffect(() => {
    setIsLoading(true)
    fetchData()
  }, [activeView, selectedArea, fetchData])

  // Auto-refresh every 15 minutes for Live view
  useEffect(() => {
    if (activeView !== 'live') return

    const interval = setInterval(() => {
      fetchData(false)
    }, AUTO_REFRESH_INTERVAL)

    return () => clearInterval(interval)
  }, [fetchData, activeView])

  const handleRefresh = useCallback(() => {
    fetchData(true)
  }, [fetchData])

  const handleViewChange = useCallback((view: DataView) => {
    setActiveView(view)
  }, [])

  const handleSafetyClick = useCallback((event: DowntimeEvent) => {
    if (event.id) {
      fetchSafetyEventDetail(event.id)
      setIsSafetyModalOpen(true)
    }
  }, [fetchSafetyEventDetail])

  const handleCloseSafetyModal = useCallback(() => {
    setIsSafetyModalOpen(false)
    setSelectedSafetyEvent(null)
  }, [])

  // Format last updated timestamp
  const formatLastUpdated = (isoString: string): string => {
    try {
      const date = new Date(isoString)
      return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
      })
    } catch {
      return isoString
    }
  }

  const isLive = activeView === 'live'

  // Loading state
  if (isLoading && !paretoData) {
    return <LoadingSkeleton />
  }

  // Error state
  if (error) {
    return (
      <Card mode="default" className="min-h-[300px]">
        <CardContent className="flex flex-col items-center justify-center py-16">
          <div className="text-center">
            <svg
              className="w-12 h-12 text-warning-amber mx-auto mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <p className="text-lg text-foreground mb-2">{error}</p>
            <button
              onClick={handleRefresh}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
            >
              Try Again
            </button>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* View Toggle and Status Bar */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        {/* View Toggle */}
        <TimeWindowToggle
          activeView={activeView}
          onViewChange={handleViewChange}
          isLoading={isRefreshing}
        />

        {/* Data Freshness */}
        <div className="flex items-center gap-4">
          <Badge variant={isLive ? 'live' : 'retrospective'} className="text-sm">
            {isLive ? (
              <>
                <span className="inline-flex h-2 w-2 rounded-full bg-live-pulse mr-2 animate-live-pulse" />
                T-15m Data
              </>
            ) : (
              <>T-1 Data</>
            )}
          </Badge>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>Last updated:</span>
            <span className="font-medium text-foreground">
              {paretoData?.last_updated ? formatLastUpdated(paretoData.last_updated) : '--'}
            </span>
          </div>
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className={cn(
              'p-2 rounded-md hover:bg-muted transition-colors',
              isRefreshing && 'animate-spin',
            )}
            title="Refresh data"
          >
            <svg
              className="w-4 h-4 text-muted-foreground"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
          </button>
        </div>
      </div>

      {/* Cost of Loss Summary Widget */}
      <CostOfLossWidget
        data={summaryData}
        isLive={isLive}
        isLoading={isLoading}
      />

      {/* Filter Bar */}
      <DowntimeFilterBar
        areas={areas}
        selectedArea={selectedArea}
        onAreaChange={setSelectedArea}
      />

      {/* Pareto Chart */}
      <ParetoChart
        data={paretoData?.items || []}
        threshold80Index={paretoData?.threshold_80_index ?? null}
        isLive={isLive}
      />

      {/* Downtime Events Table */}
      <DowntimeTable
        events={eventsData?.events || []}
        isLive={isLive}
        onSafetyClick={handleSafetyClick}
      />

      {/* Safety Event Modal */}
      <SafetyEventModal
        event={selectedSafetyEvent}
        isOpen={isSafetyModalOpen}
        onClose={handleCloseSafetyModal}
        isLoading={isSafetyLoading}
      />

      {/* Auto-refresh indicator for Live view */}
      {isLive && (
        <div className="text-center text-sm text-muted-foreground">
          <span className="inline-flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-live-pulse animate-live-pulse" />
            Auto-refreshing every 15 minutes
          </span>
        </div>
      )}
    </div>
  )
}

function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      {/* Header skeleton */}
      <div className="flex items-center justify-between">
        <div className="h-10 w-64 bg-muted rounded-lg animate-pulse" />
        <div className="h-8 w-48 bg-muted rounded animate-pulse" />
      </div>

      {/* Summary widget skeleton */}
      <Card className="animate-pulse">
        <CardContent className="p-6">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="space-y-2">
                <div className="h-4 w-24 bg-muted rounded" />
                <div className="h-8 w-32 bg-muted rounded" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Chart skeleton */}
      <Card className="animate-pulse">
        <CardContent className="p-6">
          <div className="h-6 w-48 bg-muted rounded mb-4" />
          <div className="h-[350px] w-full bg-muted rounded" />
        </CardContent>
      </Card>

      {/* Table skeleton */}
      <Card className="animate-pulse">
        <CardContent className="p-6">
          <div className="h-6 w-48 bg-muted rounded mb-4" />
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-12 w-full bg-muted rounded" />
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
