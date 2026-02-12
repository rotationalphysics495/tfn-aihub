'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { createClient } from '@/lib/supabase/client'

export interface DowntimeParetoItem {
  reason_code: string
  total_minutes: number
  percentage: number
  cumulative_percentage: number
  financial_impact: number
  event_count: number
  is_safety_related: boolean
}

export interface DowntimeParetoResponse {
  items: DowntimeParetoItem[]
  total_downtime_minutes: number
  total_financial_impact: number
  total_events: number
  data_source: string
  last_updated: string
  threshold_80_index: number | null
}

interface UseDowntimeParetoOptions {
  assetId: string
  reportDate: string
  enabled?: boolean
}

const ERROR_MESSAGES = {
  AUTH_ERROR: 'Your session has expired. Please log in again.',
  SERVER_ERROR: "Something went wrong on our end. We're working on it.",
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function useDowntimePareto(options: UseDowntimeParetoOptions) {
  const { assetId, reportDate, enabled = true } = options

  const [data, setData] = useState<DowntimeParetoResponse | null>(null)
  const [isLoading, setIsLoading] = useState(enabled)
  const [error, setError] = useState<string | null>(null)

  const mountedRef = useRef(true)

  const fetchData = useCallback(async () => {
    if (!mountedRef.current) return

    setIsLoading(true)
    setError(null)

    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.access_token) {
        if (!mountedRef.current) return
        setIsLoading(false)
        setError(ERROR_MESSAGES.AUTH_ERROR)
        return
      }

      const params = new URLSearchParams()
      params.set('asset_id', assetId)
      params.set('start_date', reportDate)

      const url = `${API_BASE_URL}/api/v1/downtime/pareto?${params.toString()}`

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      })

      if (!mountedRef.current) return

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error(ERROR_MESSAGES.AUTH_ERROR)
        }
        throw new Error(ERROR_MESSAGES.SERVER_ERROR)
      }

      const responseData: DowntimeParetoResponse = await response.json()

      if (!mountedRef.current) return

      setData(responseData)
      setIsLoading(false)
      setError(null)
    } catch (err) {
      if (!mountedRef.current) return

      const message = err instanceof Error
        ? err.message
        : ERROR_MESSAGES.SERVER_ERROR

      setData(null)
      setIsLoading(false)
      setError(message)
    }
  }, [assetId, reportDate])

  useEffect(() => {
    mountedRef.current = true

    if (enabled) {
      fetchData()
    }

    return () => {
      mountedRef.current = false
    }
  }, [enabled, fetchData])

  return {
    data,
    isLoading,
    error,
    refetch: fetchData,
  }
}
