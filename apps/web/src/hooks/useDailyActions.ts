'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { createClient } from '@/lib/supabase/client'

/**
 * Daily Actions Hook
 *
 * Fetches and manages daily action list data from the Action Engine API.
 *
 * @see Story 3.3 - Action List Primary View
 * @see AC #5 - Data Integration with Action Engine API
 */

// Types matching the backend API response (Story 3.2)
export type ActionCategory = 'safety' | 'oee' | 'financial'
export type PriorityLevel = 'critical' | 'high' | 'medium' | 'low'

export interface EvidenceRef {
  table: string
  column: string
  value: string
  record_id: string
  context?: string
  // Alias fields from backend
  source_table?: string
  metric_name?: string
  metric_value?: string
}

export interface ActionItem {
  id: string
  asset_id: string
  asset_name: string
  priority_level: PriorityLevel
  category: ActionCategory
  primary_metric_value: string
  recommendation_text: string
  evidence_summary: string
  evidence_refs: EvidenceRef[]
  created_at: string
  financial_impact_usd: number
  // Computed/alias fields from backend
  priority_rank: number
  title: string
  description: string
}

export interface ActionListResponse {
  actions: ActionItem[]
  generated_at: string
  report_date: string
  total_count: number
  counts_by_category: {
    safety: number
    oee: number
    financial: number
  }
}

export interface DailyActionsState {
  data: ActionListResponse | null
  isLoading: boolean
  error: string | null
  lastUpdated: string | null
}

interface UseDailyActionsOptions {
  /** Auto-fetch on mount (default: true) */
  autoFetch?: boolean
  /** API base URL (default: process.env.NEXT_PUBLIC_API_URL) */
  apiUrl?: string
  /** Report date override (ISO date string, defaults to T-1/yesterday) */
  reportDate?: string
}

export interface UseDailyActionsReturn extends DailyActionsState {
  /** Manually refetch daily actions */
  refetch: () => Promise<void>
  /** Check if there are any action items */
  hasActions: boolean
  /** Summary metrics for quick access */
  summary: {
    totalActions: number
    safetyCount: number
    oeeCount: number
    financialCount: number
  }
}

// Error messages
const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Unable to connect to server. Check your connection and try again.',
  AUTH_ERROR: 'Your session has expired. Please log in again.',
  SERVER_ERROR: "Something went wrong on our end. We're working on it.",
  NO_DATA: 'No data available for yesterday. This may happen on Mondays after plant shutdown.',
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function useDailyActions(options: UseDailyActionsOptions = {}): UseDailyActionsReturn {
  const {
    autoFetch = true,
    apiUrl = API_BASE_URL,
    reportDate,
  } = options

  const [state, setState] = useState<DailyActionsState>({
    data: null,
    isLoading: false,
    error: null,
    lastUpdated: null,
  })

  const mountedRef = useRef(true)

  const fetchActions = useCallback(async () => {
    if (!mountedRef.current) return

    setState(prev => ({ ...prev, isLoading: true, error: null }))

    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.access_token) {
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: ERROR_MESSAGES.AUTH_ERROR,
        }))
        return
      }

      // Build query params
      const params = new URLSearchParams()
      if (reportDate) {
        params.set('date', reportDate)
      }

      const url = `${apiUrl}/api/v1/actions/daily${params.toString() ? `?${params.toString()}` : ''}`

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error(ERROR_MESSAGES.AUTH_ERROR)
        }
        if (response.status === 404) {
          throw new Error(ERROR_MESSAGES.NO_DATA)
        }
        throw new Error(ERROR_MESSAGES.SERVER_ERROR)
      }

      const data: ActionListResponse = await response.json()

      if (!mountedRef.current) return

      setState({
        data,
        isLoading: false,
        error: null,
        lastUpdated: new Date().toISOString(),
      })
    } catch (error) {
      if (!mountedRef.current) return

      const message = error instanceof Error
        ? error.message
        : ERROR_MESSAGES.SERVER_ERROR

      setState(prev => ({
        ...prev,
        isLoading: false,
        error: message,
      }))
    }
  }, [apiUrl, reportDate])

  // Initial fetch on mount
  useEffect(() => {
    mountedRef.current = true

    if (autoFetch) {
      fetchActions()
    }

    return () => {
      mountedRef.current = false
    }
  }, [autoFetch, fetchActions])

  // Computed values
  const hasActions = (state.data?.total_count ?? 0) > 0
  const summary = {
    totalActions: state.data?.total_count ?? 0,
    safetyCount: state.data?.counts_by_category?.safety ?? 0,
    oeeCount: state.data?.counts_by_category?.oee ?? 0,
    financialCount: state.data?.counts_by_category?.financial ?? 0,
  }

  return {
    ...state,
    refetch: fetchActions,
    hasActions,
    summary,
  }
}
