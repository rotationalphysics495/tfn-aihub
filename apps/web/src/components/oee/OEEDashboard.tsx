'use client'

import { useCallback, useEffect, useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import { cn } from '@/lib/utils'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { OEEGauge } from './OEEGauge'
import { OEEBreakdown } from './OEEBreakdown'
import { AssetOEEList, type AssetOEEData } from './AssetOEEList'

/**
 * OEE Dashboard Client Component
 *
 * Main container for OEE metrics display.
 * Handles data fetching, state management, auto-refresh, and view toggling.
 *
 * @see Story 2.4 - OEE Metrics View
 * @see AC #5 - OEE values update within 60 seconds of new data ingestion
 * @see AC #6 - Visual indicators distinguish Yesterday's Analysis (T-1) and Live Pulse (T-15m)
 */

interface PlantOEE {
  overall: number | null
  availability: number | null
  performance: number | null
  quality: number | null
  target: number
  status: string
}

interface OEEData {
  plant_oee: PlantOEE
  assets: AssetOEEData[]
  data_source: string
  last_updated: string
}

// Auto-refresh interval: 60 seconds per NFR2 requirement
const AUTO_REFRESH_INTERVAL = 60000

type DataView = 'yesterday' | 'live'

export function OEEDashboard() {
  const [data, setData] = useState<OEEData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeView, setActiveView] = useState<DataView>('yesterday')

  const fetchOEEData = useCallback(async (showRefreshing = false) => {
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
      const url = `${apiUrl}/api/oee/plant?source=${source}`

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }

      const oeeData: OEEData = await response.json()
      setData(oeeData)
      setError(null)
    } catch (err) {
      console.error('Failed to fetch OEE data:', err)
      setError('Failed to load OEE data. Please try again.')
    } finally {
      setIsLoading(false)
      setIsRefreshing(false)
    }
  }, [activeView])

  // Initial data fetch and refetch on view change
  useEffect(() => {
    setIsLoading(true)
    fetchOEEData()
  }, [fetchOEEData])

  // Auto-refresh every 60 seconds (only for Live view per requirements)
  useEffect(() => {
    if (activeView !== 'live') return

    const interval = setInterval(() => {
      fetchOEEData(false)
    }, AUTO_REFRESH_INTERVAL)

    return () => clearInterval(interval)
  }, [fetchOEEData, activeView])

  const handleRefresh = useCallback(() => {
    fetchOEEData(true)
  }, [fetchOEEData])

  const handleViewChange = useCallback((view: DataView) => {
    setActiveView(view)
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

  // Loading state
  if (isLoading) {
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

  const isLive = activeView === 'live'

  return (
    <div className="space-y-8">
      {/* View Toggle and Status Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        {/* View Toggle Tabs */}
        <div className="flex items-center gap-2 p-1 bg-muted rounded-lg">
          <button
            onClick={() => handleViewChange('yesterday')}
            className={cn(
              'px-4 py-2 rounded-md text-sm font-medium transition-colors',
              activeView === 'yesterday'
                ? 'bg-card text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground',
            )}
          >
            <span className="flex items-center gap-2">
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                />
              </svg>
              Yesterday&apos;s Analysis
            </span>
          </button>
          <button
            onClick={() => handleViewChange('live')}
            className={cn(
              'px-4 py-2 rounded-md text-sm font-medium transition-colors',
              activeView === 'live'
                ? 'bg-card text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground',
            )}
          >
            <span className="flex items-center gap-2">
              <span
                className={cn(
                  'w-2 h-2 rounded-full',
                  activeView === 'live'
                    ? 'bg-live-pulse animate-live-pulse'
                    : 'bg-muted-foreground',
                )}
              />
              Live Pulse
            </span>
          </button>
        </div>

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
              {data?.last_updated ? formatLastUpdated(data.last_updated) : '--'}
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

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Plant-Wide OEE Gauge */}
        <div className="lg:col-span-1">
          <OEEGauge
            value={data?.plant_oee.overall ?? null}
            target={data?.plant_oee.target ?? 85}
            status={data?.plant_oee.status ?? 'unknown'}
            isLive={isLive}
          />
        </div>

        {/* OEE Components Breakdown */}
        <div className="lg:col-span-2">
          <OEEBreakdown
            availability={data?.plant_oee.availability ?? null}
            performance={data?.plant_oee.performance ?? null}
            quality={data?.plant_oee.quality ?? null}
            isLive={isLive}
          />
        </div>
      </div>

      {/* Asset OEE List */}
      <AssetOEEList
        assets={data?.assets ?? []}
        isLive={isLive}
      />

      {/* Auto-refresh indicator for Live view */}
      {isLive && (
        <div className="text-center text-sm text-muted-foreground">
          <span className="inline-flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-live-pulse animate-live-pulse" />
            Auto-refreshing every 60 seconds
          </span>
        </div>
      )}
    </div>
  )
}

function LoadingSkeleton() {
  return (
    <div className="space-y-8">
      {/* Header skeleton */}
      <div className="flex items-center justify-between">
        <div className="h-10 w-64 bg-muted rounded-lg animate-pulse" />
        <div className="h-8 w-48 bg-muted rounded animate-pulse" />
      </div>

      {/* Main grid skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Gauge skeleton */}
        <div className="lg:col-span-1">
          <Card className="animate-pulse">
            <CardContent className="p-8 flex flex-col items-center">
              <div className="w-48 h-48 rounded-full bg-muted" />
              <div className="mt-6 h-8 w-32 bg-muted rounded" />
              <div className="mt-2 h-4 w-48 bg-muted rounded" />
            </CardContent>
          </Card>
        </div>

        {/* Breakdown skeleton */}
        <div className="lg:col-span-2">
          <Card className="animate-pulse">
            <CardContent className="p-6 space-y-8">
              {[1, 2, 3].map((i) => (
                <div key={i} className="space-y-2">
                  <div className="flex justify-between">
                    <div className="h-6 w-32 bg-muted rounded" />
                    <div className="h-8 w-20 bg-muted rounded" />
                  </div>
                  <div className="h-4 w-full bg-muted rounded-full" />
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Asset list skeleton */}
      <Card className="animate-pulse">
        <CardContent className="p-6">
          <div className="h-6 w-48 bg-muted rounded mb-4" />
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-16 w-full bg-muted rounded" />
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
