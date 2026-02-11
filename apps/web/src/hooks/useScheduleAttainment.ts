'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { createClient } from '@/lib/supabase/client'

export interface ProductAttainment {
  product_name: string
  product_id?: string
  scheduled_quantity: number
  actual_quantity: number
  attainment_pct: number
}

export interface VarianceCallout {
  type: string
  asset_name: string
  message: string
  scheduled_product?: string
  actual_product?: string
  quantity_gap?: number
}

export interface WorkcenterAttainment {
  workcenter_name: string
  overall_attainment_pct: number
  products: ProductAttainment[]
  variance_callouts: VarianceCallout[]
}

export interface ScheduleAttainmentResponse {
  workcenters: WorkcenterAttainment[]
  report_date: string
  has_schedule: boolean
  message?: string
}

interface ScheduleAttainmentState {
  data: ScheduleAttainmentResponse | null
  isLoading: boolean
  error: string | null
}

interface UseScheduleAttainmentOptions {
  autoFetch?: boolean
  apiUrl?: string
  date?: string
}

export interface UseScheduleAttainmentReturn extends ScheduleAttainmentState {
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

function mapApiResponse(apiData: Record<string, unknown>): ScheduleAttainmentResponse {
  const workcenters = (apiData.workcenters as Array<Record<string, unknown>> || []).map(wc => ({
    workcenter_name: (wc.workcenter ?? wc.workcenter_name) as string,
    overall_attainment_pct: wc.overall_attainment_pct as number,
    products: (wc.products as ProductAttainment[]) || [],
    variance_callouts: ((wc.variances ?? wc.variance_callouts) as Array<Record<string, unknown>> || []).map(v => ({
      type: (v.variance_type ?? v.type) as string,
      asset_name: v.asset_name as string,
      message: v.message as string,
      scheduled_product: v.scheduled_product as string | undefined,
      actual_product: v.actual_product as string | undefined,
      quantity_gap: v.quantity_gap as number | undefined,
    })),
  }))

  return {
    workcenters,
    report_date: (apiData.date ?? apiData.report_date) as string,
    has_schedule: (apiData.has_data ?? apiData.has_schedule) as boolean,
    message: apiData.message as string | undefined,
  }
}

export function useScheduleAttainment(
  options: UseScheduleAttainmentOptions = {}
): UseScheduleAttainmentReturn {
  const { autoFetch = true, apiUrl = API_BASE_URL, date } = options

  const [state, setState] = useState<ScheduleAttainmentState>({
    data: null,
    isLoading: true,
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
      const url = `${apiUrl}/api/v1/production/schedule-attainment?date=${queryDate}`

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      })

      if (!mountedRef.current) return

      if (response.status === 401) {
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: ERROR_MESSAGES.AUTH_ERROR,
        }))
        return
      }

      if (response.status === 404) {
        setState({
          data: {
            workcenters: [],
            report_date: queryDate,
            has_schedule: false,
            message: 'No schedule data available for this date.',
          },
          isLoading: false,
          error: null,
        })
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

      const rawData = await response.json()

      if (!mountedRef.current) return

      const data = mapApiResponse(rawData)

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
