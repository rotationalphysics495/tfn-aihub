'use client'

import { useCallback, useEffect, useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import {
  ThroughputGrid,
  EmptyState,
  FilterBar,
  DataFreshnessIndicator,
  type ThroughputCardData,
  type ThroughputStatus,
} from '@/components/production'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

/**
 * Throughput Dashboard Client Component
 *
 * Handles data fetching, state management, auto-refresh, and filtering.
 *
 * @see Story 2.3 - Throughput Dashboard
 * @see AC #5 - Real-time Data Binding
 * @see NFR2 - 60 second latency requirement
 */

interface ThroughputData {
  assets: ThroughputCardData[]
  last_updated: string
  total_assets: number
  on_target_count: number
  behind_count: number
  critical_count: number
}

// Auto-refresh interval: 30 seconds to stay within NFR2 (60 second) requirement
const AUTO_REFRESH_INTERVAL = 30000

export function ThroughputDashboard() {
  const [data, setData] = useState<ThroughputData | null>(null)
  const [areas, setAreas] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Filter state
  const [selectedArea, setSelectedArea] = useState<string | null>(null)
  const [selectedStatus, setSelectedStatus] = useState<ThroughputStatus | null>(null)

  const fetchThroughputData = useCallback(async (showRefreshing = false) => {
    if (showRefreshing) {
      setIsRefreshing(true)
    }

    try {
      const supabase = createClient()

      // Get user session for API auth
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.access_token) {
        setError('Authentication required')
        return
      }

      // Build query params
      const params = new URLSearchParams()
      if (selectedArea) params.set('area', selectedArea)
      if (selectedStatus) params.set('status', selectedStatus)

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const queryString = params.toString()
      const url = `${apiUrl}/api/production/throughput${queryString ? `?${queryString}` : ''}`

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }

      const throughputData: ThroughputData = await response.json()
      setData(throughputData)
      setError(null)
    } catch (err) {
      console.error('Failed to fetch throughput data:', err)
      setError('Failed to load throughput data. Please try again.')
    } finally {
      setIsLoading(false)
      setIsRefreshing(false)
    }
  }, [selectedArea, selectedStatus])

  const fetchAreas = useCallback(async () => {
    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.access_token) return

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/production/throughput/areas`, {
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

  // Initial data fetch
  useEffect(() => {
    fetchThroughputData()
    fetchAreas()
  }, [fetchThroughputData, fetchAreas])

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchThroughputData(false)
    }, AUTO_REFRESH_INTERVAL)

    return () => clearInterval(interval)
  }, [fetchThroughputData])

  const handleRefresh = useCallback(() => {
    fetchThroughputData(true)
  }, [fetchThroughputData])

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-6">
        <LoadingSkeleton />
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <Card mode="live" className="min-h-[300px]">
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

  const counts = {
    total: data?.total_assets || 0,
    on_target: data?.on_target_count || 0,
    behind: data?.behind_count || 0,
    critical: data?.critical_count || 0,
  }

  return (
    <div className="space-y-6">
      {/* Summary Bar */}
      <div className="flex flex-wrap items-center gap-4">
        <Badge variant="live" className="text-sm">
          <span className="inline-flex h-2 w-2 rounded-full bg-live-pulse mr-2 animate-live-pulse" />
          Live
        </Badge>
        <div className="flex items-center gap-2 text-sm">
          <span className="font-medium">{counts.total}</span>
          <span className="text-muted-foreground">assets monitored</span>
        </div>
        <div className="hidden sm:flex items-center gap-4 text-sm">
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-success-green" />
            <span className="font-medium">{counts.on_target}</span>
            <span className="text-muted-foreground">on target</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-warning-amber" />
            <span className="font-medium">{counts.behind + counts.critical}</span>
            <span className="text-muted-foreground">need attention</span>
          </span>
        </div>
      </div>

      {/* Filter Bar and Freshness Indicator */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <FilterBar
          areas={areas}
          selectedArea={selectedArea}
          selectedStatus={selectedStatus}
          onAreaChange={setSelectedArea}
          onStatusChange={setSelectedStatus}
          counts={counts}
        />
        <DataFreshnessIndicator
          lastUpdated={data?.last_updated || null}
          onRefresh={handleRefresh}
          isRefreshing={isRefreshing}
        />
      </div>

      {/* Main Content */}
      {data?.assets && data.assets.length > 0 ? (
        <ThroughputGrid assets={data.assets} />
      ) : (
        <EmptyState />
      )}
    </div>
  )
}

function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      {/* Summary skeleton */}
      <div className="flex items-center gap-4">
        <div className="h-6 w-20 bg-muted rounded animate-pulse" />
        <div className="h-4 w-32 bg-muted rounded animate-pulse" />
      </div>

      {/* Filter bar skeleton */}
      <div className="flex items-center gap-4">
        <div className="h-10 w-40 bg-muted rounded animate-pulse" />
        <div className="h-10 w-64 bg-muted rounded animate-pulse" />
      </div>

      {/* Grid skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <Card key={i} className="h-[280px] animate-pulse">
            <CardContent className="p-6 space-y-4">
              <div className="flex justify-between items-start">
                <div className="space-y-2">
                  <div className="h-5 w-32 bg-muted rounded" />
                  <div className="h-4 w-20 bg-muted rounded" />
                </div>
                <div className="h-6 w-20 bg-muted rounded" />
              </div>
              <div className="h-16 bg-muted rounded" />
              <div className="h-3 bg-muted rounded" />
              <div className="grid grid-cols-2 gap-4">
                <div className="h-16 bg-muted rounded" />
                <div className="h-16 bg-muted rounded" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
