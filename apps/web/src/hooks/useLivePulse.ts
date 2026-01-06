'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { createClient } from '@/lib/supabase/client'

/**
 * Live Pulse Hook
 *
 * Manages live pulse ticker data fetching and auto-refresh.
 *
 * @see Story 2.9 - Live Pulse Ticker
 * @see AC #1 - Updates automatically every 15 minutes
 * @see AC #5 - Data Source Integration
 * @see AC #6 - Performance Requirements
 */

// Type definitions matching API response schema
export interface MachineStatus {
  running: number
  idle: number
  down: number
  total: number
}

export interface ActiveDowntime {
  asset_name: string
  reason_code: string
  duration_minutes: number
}

export interface ProductionData {
  current_output: number
  target_output: number
  output_percentage: number
  oee_percentage: number
  machine_status: MachineStatus
  active_downtime: ActiveDowntime[]
}

export interface FinancialData {
  shift_to_date_loss: number
  rolling_15_min_loss: number
  currency: string
}

export interface SafetyIncident {
  id: string
  asset_name: string
  detected_at: string
  severity: string
}

export interface SafetyData {
  has_active_incident: boolean
  active_incidents: SafetyIncident[]
}

export interface MetaData {
  data_age: number
  is_stale: boolean
}

export interface LivePulseData {
  timestamp: string
  production: ProductionData
  financial: FinancialData
  safety: SafetyData
  meta: MetaData
}

export interface LivePulseState {
  data: LivePulseData | null
  isLoading: boolean
  error: string | null
  lastFetched: string | null
}

interface UseLivePulseOptions {
  /** Polling interval in milliseconds (default: 900000 = 15 minutes) */
  pollingInterval?: number
  /** Whether to auto-fetch on mount (default: true) */
  autoFetch?: boolean
  /** API base URL (default: process.env.NEXT_PUBLIC_API_URL) */
  apiUrl?: string
}

export interface UseLivePulseReturn extends LivePulseState {
  /** Manually refetch live pulse data */
  refetch: () => Promise<void>
  /** Check if there are any active safety incidents */
  hasActiveIncident: boolean
  /** Check if data is stale (> 20 minutes old) */
  isDataStale: boolean
}

// 15 minutes in milliseconds
const DEFAULT_POLLING_INTERVAL = 900000
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function useLivePulse(options: UseLivePulseOptions = {}): UseLivePulseReturn {
  const {
    pollingInterval = DEFAULT_POLLING_INTERVAL,
    autoFetch = true,
    apiUrl = API_BASE_URL,
  } = options

  const [state, setState] = useState<LivePulseState>({
    data: null,
    isLoading: false,
    error: null,
    lastFetched: null,
  })

  const pollingRef = useRef<NodeJS.Timeout | null>(null)
  const mountedRef = useRef(true)

  // Fetch live pulse data
  const fetchData = useCallback(async () => {
    if (!mountedRef.current) return

    setState(prev => ({ ...prev, isLoading: true, error: null }))

    try {
      // Get session for authentication
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.access_token) {
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: 'Authentication required',
        }))
        return
      }

      const response = await fetch(`${apiUrl}/api/live-pulse`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch live pulse data: ${response.status}`)
      }

      const data: LivePulseData = await response.json()

      if (!mountedRef.current) return

      setState({
        data,
        isLoading: false,
        error: null,
        lastFetched: new Date().toISOString(),
      })
    } catch (error) {
      if (!mountedRef.current) return

      const message = error instanceof Error ? error.message : 'Failed to fetch live pulse data'
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: message,
      }))
    }
  }, [apiUrl])

  // Set up polling
  useEffect(() => {
    mountedRef.current = true

    if (autoFetch) {
      fetchData()
    }

    // Set up polling interval (15 minutes)
    if (pollingInterval > 0) {
      pollingRef.current = setInterval(() => {
        fetchData()
      }, pollingInterval)
    }

    return () => {
      mountedRef.current = false
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
        pollingRef.current = null
      }
    }
  }, [autoFetch, pollingInterval, fetchData])

  // Derived values
  const hasActiveIncident = state.data?.safety?.has_active_incident ?? false
  const isDataStale = state.data?.meta?.is_stale ?? false

  return {
    ...state,
    refetch: fetchData,
    hasActiveIncident,
    isDataStale,
  }
}
