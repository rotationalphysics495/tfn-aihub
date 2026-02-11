'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { createClient } from '@/lib/supabase/client'

export interface AssetDetail {
  asset_name: string
  actual: number
  target: number
  oee: number | null
  downtime_minutes: number | null
}

export interface WorkcenterEntry {
  workcenter_name: string
  total_actual: number
  total_target: number
  attainment_percentage: number
  assets_on_target: number
  assets_missed: number
  total_assets: number
  assets: AssetDetail[]
}

export interface WorkcenterSummaryResponse {
  workcenters: WorkcenterEntry[]
  date: string
  total_actual: number
  total_target: number
  total_attainment: number
  message?: string | null
}

interface WorkcenterSummaryState {
  data: WorkcenterSummaryResponse | null
  isLoading: boolean
  error: string | null
}

interface UseWorkcenterSummaryOptions {
  autoFetch?: boolean
  apiUrl?: string
  date?: string
}

export interface UseWorkcenterSummaryReturn extends WorkcenterSummaryState {
  refetch: () => Promise<void>
}

const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Unable to connect to server. Check your connection and try again.',
  AUTH_ERROR: 'Authentication required. Please log in again.',
  SERVER_ERROR: "Something went wrong on our end. We're working on it.",
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

function getYesterday(): string {
  const d = new Date()
  d.setDate(d.getDate() - 1)
  return d.toISOString().split('T')[0]
}

export function useWorkcenterSummary(
  options: UseWorkcenterSummaryOptions = {}
): UseWorkcenterSummaryReturn {
  const { autoFetch = true, apiUrl = API_BASE_URL, date } = options

  const [state, setState] = useState<WorkcenterSummaryState>({
    data: null,
    isLoading: false,
    error: null,
  })

  const mountedRef = useRef(true)

  const fetchData = useCallback(async () => {
    if (!mountedRef.current) return

    setState(prev => ({ ...prev, isLoading: true, error: null }))

    try {
      const supabase = createClient()
      const {
        data: { session },
      } = await supabase.auth.getSession()

      if (!session?.access_token) {
        if (!mountedRef.current) return
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: ERROR_MESSAGES.AUTH_ERROR,
        }))
        return
      }

      const queryDate = date || getYesterday()
      const url = `${apiUrl}/api/v1/production/workcenter-summary?date=${queryDate}`

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      })

      if (!mountedRef.current) return

      if (response.status === 404) {
        setState({
          data: {
            workcenters: [],
            date: queryDate,
            total_actual: 0,
            total_target: 0,
            total_attainment: 0,
            message: 'No production data available for this date.',
          },
          isLoading: false,
          error: null,
        })
        return
      }

      if (response.status === 401) {
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: ERROR_MESSAGES.AUTH_ERROR,
        }))
        return
      }

      if (!response.ok) {
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: ERROR_MESSAGES.SERVER_ERROR,
        }))
        return
      }

      const data: WorkcenterSummaryResponse = await response.json()

      if (!mountedRef.current) return

      setState({
        data,
        isLoading: false,
        error: null,
      })
    } catch (error) {
      if (!mountedRef.current) return

      const message =
        error instanceof TypeError
          ? ERROR_MESSAGES.NETWORK_ERROR
          : error instanceof Error
            ? error.message
            : ERROR_MESSAGES.SERVER_ERROR

      setState(prev => ({
        ...prev,
        isLoading: false,
        error: message,
      }))
    }
  }, [apiUrl, date])

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
    ...state,
    refetch: fetchData,
  }
}
