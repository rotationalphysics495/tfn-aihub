'use client'

import { useState, useEffect, useCallback, useRef } from 'react'

/**
 * Safety Alert Hook
 *
 * Manages safety alert data fetching and real-time updates.
 *
 * @see Story 2.6 - Safety Alert System
 * @see AC #4 - Real-time polling/refresh for safety alert status
 * @see AC #6 - Alert persistence until acknowledged
 */

export interface SafetyAlert {
  id: string
  asset_id: string
  asset_name: string
  area: string | null
  event_timestamp: string
  reason_code: string
  severity: string
  description: string | null
  duration_minutes: number | null
  financial_impact: number | null
  acknowledged: boolean
  acknowledged_at: string | null
  created_at: string
}

export interface SafetyAlertsState {
  alerts: SafetyAlert[]
  activeCount: number
  isLoading: boolean
  error: string | null
  lastUpdated: string | null
}

interface UseSafetyAlertsOptions {
  /** Polling interval in milliseconds (default: 30000 = 30s) */
  pollingInterval?: number
  /** Whether to auto-fetch on mount (default: true) */
  autoFetch?: boolean
  /** API base URL (default: process.env.NEXT_PUBLIC_API_URL) */
  apiUrl?: string
}

export interface UseSafetyAlertsReturn extends SafetyAlertsState {
  /** Manually refetch safety alerts */
  refetch: () => Promise<void>
  /** Acknowledge a safety event */
  acknowledge: (eventId: string) => Promise<boolean>
  /** Check if there are any active (unacknowledged) alerts */
  hasActiveAlerts: boolean
}

const DEFAULT_POLLING_INTERVAL = 30000 // 30 seconds
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function useSafetyAlerts(options: UseSafetyAlertsOptions = {}): UseSafetyAlertsReturn {
  const {
    pollingInterval = DEFAULT_POLLING_INTERVAL,
    autoFetch = true,
    apiUrl = API_BASE_URL,
  } = options

  const [state, setState] = useState<SafetyAlertsState>({
    alerts: [],
    activeCount: 0,
    isLoading: false,
    error: null,
    lastUpdated: null,
  })

  const pollingRef = useRef<NodeJS.Timeout | null>(null)
  const mountedRef = useRef(true)

  // Fetch active safety alerts
  const fetchAlerts = useCallback(async () => {
    if (!mountedRef.current) return

    setState(prev => ({ ...prev, isLoading: true, error: null }))

    try {
      const response = await fetch(`${apiUrl}/api/safety/active`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch safety alerts: ${response.status}`)
      }

      const data = await response.json()

      if (!mountedRef.current) return

      setState({
        alerts: data.events || [],
        activeCount: data.count || 0,
        isLoading: false,
        error: null,
        lastUpdated: data.last_updated || new Date().toISOString(),
      })
    } catch (error) {
      if (!mountedRef.current) return

      const message = error instanceof Error ? error.message : 'Failed to fetch safety alerts'
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: message,
      }))
    }
  }, [apiUrl])

  // Acknowledge a safety event
  const acknowledge = useCallback(async (eventId: string): Promise<boolean> => {
    try {
      const response = await fetch(`${apiUrl}/api/safety/acknowledge/${eventId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({}),
      })

      if (!response.ok) {
        throw new Error(`Failed to acknowledge event: ${response.status}`)
      }

      const data = await response.json()

      if (data.success) {
        // Update local state to reflect acknowledgement
        setState(prev => ({
          ...prev,
          alerts: prev.alerts.map(alert =>
            alert.id === eventId
              ? { ...alert, acknowledged: true, acknowledged_at: new Date().toISOString() }
              : alert
          ),
          activeCount: Math.max(0, prev.activeCount - 1),
        }))

        return true
      }

      return false
    } catch (error) {
      console.error('Failed to acknowledge safety event:', error)
      return false
    }
  }, [apiUrl])

  // Set up polling
  useEffect(() => {
    mountedRef.current = true

    if (autoFetch) {
      fetchAlerts()
    }

    // Set up polling interval
    if (pollingInterval > 0) {
      pollingRef.current = setInterval(() => {
        fetchAlerts()
      }, pollingInterval)
    }

    return () => {
      mountedRef.current = false
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
        pollingRef.current = null
      }
    }
  }, [autoFetch, pollingInterval, fetchAlerts])

  return {
    ...state,
    refetch: fetchAlerts,
    acknowledge,
    hasActiveAlerts: state.activeCount > 0,
  }
}

/**
 * Hook to get just the safety alert count for the header indicator.
 * Uses a longer polling interval since it's less critical.
 */
export function useSafetyAlertCount(options: UseSafetyAlertsOptions = {}): {
  count: number
  isLoading: boolean
  refetch: () => Promise<void>
} {
  const { alerts, activeCount, isLoading, refetch } = useSafetyAlerts({
    ...options,
    pollingInterval: options.pollingInterval || 60000, // Default 60s for count-only
  })

  return {
    count: activeCount,
    isLoading,
    refetch,
  }
}
