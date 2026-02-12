'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { createClient } from '@/lib/supabase/client'

export interface ActiveActionPlan {
  id: string
  title: string
  due_date: string
  status: 'open' | 'in_progress'
}

interface UseActiveActionPlansReturn {
  plans: ActiveActionPlan[]
  isLoading: boolean
  error: string | null
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const ACTIVE_STATUSES: ReadonlySet<string> = new Set(['open', 'in_progress'])

export function useActiveActionPlans(assetId?: string): UseActiveActionPlansReturn {
  const [plans, setPlans] = useState<ActiveActionPlan[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const mountedRef = useRef(true)

  const fetchPlans = useCallback(async () => {
    if (!assetId) return
    if (!mountedRef.current) return

    setIsLoading(true)
    setError(null)

    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.access_token) {
        if (mountedRef.current) {
          setIsLoading(false)
        }
        return
      }

      const params = new URLSearchParams()
      params.set('asset_id', assetId)
      params.set('status', 'open,in_progress')

      const url = `${API_BASE_URL}/api/v1/action-plans?${params.toString()}`

      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      })

      if (!mountedRef.current) return

      if (!response.ok) {
        setIsLoading(false)
        setError('Failed to fetch action plans')
        return
      }

      const data = await response.json()

      if (!mountedRef.current) return

      // Client-side filter as safety net
      const activePlans: ActiveActionPlan[] = (Array.isArray(data) ? data : [])
        .filter((plan: { status: string }) => ACTIVE_STATUSES.has(plan.status))
        .map((plan: { id: string; title: string; due_date: string; status: string }) => ({
          id: plan.id,
          title: plan.title,
          due_date: plan.due_date,
          status: plan.status as 'open' | 'in_progress',
        }))

      setPlans(activePlans)
      setIsLoading(false)
    } catch {
      if (!mountedRef.current) return
      setIsLoading(false)
      setError('Failed to fetch action plans')
    }
  }, [assetId])

  useEffect(() => {
    mountedRef.current = true

    if (assetId) {
      fetchPlans()
    }

    return () => {
      mountedRef.current = false
    }
  }, [assetId, fetchPlans])

  return { plans, isLoading, error }
}
