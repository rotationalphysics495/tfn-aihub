'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import { groupPlans } from '@/components/action-plans/types'
import type { ActionPlan, GroupedPlans } from '@/components/action-plans/types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const ERROR_MESSAGES = {
  AUTH_ERROR: 'Your session has expired. Please log in again.',
  SERVER_ERROR: "Something went wrong on our end. We're working on it.",
  NETWORK_ERROR: 'Unable to connect to server. Check your connection and try again.',
}

interface ActionPlansDashboardState {
  plans: ActionPlan[]
  isLoading: boolean
  error: string | null
}

export interface UseActionPlansDashboardReturn {
  plans: ActionPlan[]
  isLoading: boolean
  error: string | null
  refetch: () => void
  grouped: GroupedPlans
  totalCount: number
  filters: {
    status: string
    priority: string
    asset_id: string
    owner_id: string
  }
  updateFilter: (key: string, value: string) => void
}

export function useActionPlansDashboard(): UseActionPlansDashboardReturn {
  const searchParams = useSearchParams()
  const router = useRouter()
  const mountedRef = useRef(true)

  const statusFilter = searchParams.get('status') || 'all'
  const priorityFilter = searchParams.get('priority') || 'all'
  const assetFilter = searchParams.get('asset_id') || 'all'
  const ownerFilter = searchParams.get('owner_id') || 'all'

  const [state, setState] = useState<ActionPlansDashboardState>({
    plans: [],
    isLoading: true,
    error: null,
  })

  const fetchPlans = useCallback(async () => {
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

      const params = new URLSearchParams()
      params.set('page_size', '100')

      if (statusFilter && statusFilter !== 'all') {
        params.set('status', statusFilter)
      }
      if (priorityFilter && priorityFilter !== 'all') {
        params.set('priority', priorityFilter)
      }
      if (assetFilter && assetFilter !== 'all') {
        params.set('asset_id', assetFilter)
      }
      if (ownerFilter && ownerFilter !== 'all') {
        params.set('owner_id', ownerFilter)
      }

      const url = `${API_BASE_URL}/api/v1/action-plans?${params.toString()}`

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
        throw new Error(ERROR_MESSAGES.SERVER_ERROR)
      }

      const data = await response.json()

      if (!mountedRef.current) return

      // Support both `plans` and `items` response shapes
      const plans: ActionPlan[] = data.plans || data.items || []

      setState({
        plans,
        isLoading: false,
        error: null,
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
  }, [statusFilter, priorityFilter, assetFilter, ownerFilter])

  useEffect(() => {
    mountedRef.current = true

    fetchPlans()

    return () => {
      mountedRef.current = false
    }
  }, [fetchPlans])

  const updateFilter = useCallback((key: string, value: string) => {
    const params = new URLSearchParams(searchParams.toString())
    if (value === 'all' || value === '') {
      params.delete(key)
    } else {
      params.set(key, value)
    }
    const qs = params.toString()
    router.replace(qs ? `/action-plans?${qs}` : '/action-plans')
  }, [searchParams, router])

  const grouped = groupPlans(state.plans)
  const totalCount = state.plans.length

  return {
    plans: state.plans,
    isLoading: state.isLoading,
    error: state.error,
    refetch: fetchPlans,
    grouped,
    totalCount,
    filters: {
      status: statusFilter,
      priority: priorityFilter,
      asset_id: assetFilter,
      owner_id: ownerFilter,
    },
    updateFilter,
  }
}
