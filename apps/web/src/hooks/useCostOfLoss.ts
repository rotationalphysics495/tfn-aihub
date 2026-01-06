'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { createClient } from '@/lib/supabase/client'
import type { CostOfLossData } from '@/components/financial'

/**
 * Cost of Loss Data Fetching Hook
 *
 * Manages data fetching and auto-refresh for the Cost of Loss widget.
 *
 * @see Story 2.8 - Cost of Loss Widget
 * @see AC #3 - Data Fetching and State Management
 * @see AC #6 - Real-Time Update Support (15-minute refresh for live mode)
 */

// Auto-refresh interval: 15 minutes for Live Pulse alignment (AC #6)
const LIVE_REFRESH_INTERVAL = 15 * 60 * 1000 // 15 minutes

export interface UseCostOfLossOptions {
  /** Period type: 'daily' for T-1 data, 'live' for rolling data */
  period: 'daily' | 'live'
  /** Optional asset ID filter */
  assetId?: string
  /** Whether to auto-fetch on mount (default: true) */
  autoFetch?: boolean
  /** Whether to auto-refresh for live mode (default: true) */
  autoRefresh?: boolean
  /** API base URL (default: process.env.NEXT_PUBLIC_API_URL) */
  apiUrl?: string
}

export interface UseCostOfLossReturn {
  /** Cost of loss data from API */
  data: CostOfLossData | null
  /** Loading state */
  isLoading: boolean
  /** Error message */
  error: string | null
  /** Last updated timestamp */
  lastUpdated: string | null
  /** Manual refetch function */
  refetch: () => Promise<void>
}

const DEFAULT_API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function useCostOfLoss(options: UseCostOfLossOptions): UseCostOfLossReturn {
  const {
    period,
    assetId,
    autoFetch = true,
    autoRefresh = true,
    apiUrl = DEFAULT_API_URL,
  } = options

  const [data, setData] = useState<CostOfLossData | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<string | null>(null)

  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const mountedRef = useRef(true)

  /**
   * Fetch cost of loss data from the API
   */
  const fetchData = useCallback(async () => {
    if (!mountedRef.current) return

    setIsLoading(true)
    setError(null)

    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.access_token) {
        setError('Authentication required')
        setIsLoading(false)
        return
      }

      // Build query params
      const params = new URLSearchParams()
      params.set('period', period)
      if (assetId) {
        params.set('asset_id', assetId)
      }

      const response = await fetch(`${apiUrl}/api/financial/cost-of-loss?${params}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      })

      if (!mountedRef.current) return

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `API error: ${response.status}`)
      }

      const result: CostOfLossData = await response.json()

      if (!mountedRef.current) return

      setData(result)
      setLastUpdated(result.last_updated)
      setError(null)
    } catch (err) {
      if (!mountedRef.current) return

      const message = err instanceof Error ? err.message : 'Failed to fetch cost of loss data'
      console.error('Failed to fetch cost of loss data:', err)
      setError(message)
    } finally {
      if (mountedRef.current) {
        setIsLoading(false)
      }
    }
  }, [period, assetId, apiUrl])

  /**
   * Set up auto-refresh for live mode
   */
  useEffect(() => {
    // Clear any existing interval
    if (refreshIntervalRef.current) {
      clearInterval(refreshIntervalRef.current)
      refreshIntervalRef.current = null
    }

    // Only set up auto-refresh for live mode if enabled
    if (period === 'live' && autoRefresh) {
      refreshIntervalRef.current = setInterval(() => {
        fetchData()
      }, LIVE_REFRESH_INTERVAL)
    }

    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current)
        refreshIntervalRef.current = null
      }
    }
  }, [period, autoRefresh, fetchData])

  /**
   * Initial fetch and refetch on period/assetId change
   */
  useEffect(() => {
    mountedRef.current = true

    if (autoFetch) {
      fetchData()
    }

    return () => {
      mountedRef.current = false
    }
  }, [autoFetch, fetchData])

  return {
    data,
    isLoading,
    error,
    lastUpdated,
    refetch: fetchData,
  }
}
