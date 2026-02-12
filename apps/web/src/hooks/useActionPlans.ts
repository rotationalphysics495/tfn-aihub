'use client'

import { useState, useCallback, useRef, useEffect } from 'react'
import { createClient } from '@/lib/supabase/client'

export interface ActionPlanCreateRequest {
  title: string
  description?: string
  category: string
  root_cause?: string
  corrective_action?: string
  preventive_action?: string
  asset_id?: string | null
  priority: string
  due_date: string
  source_followup_id?: string | null
}

export interface ActionPlanResponse {
  id: string
  title: string
  description: string | null
  asset_id: string | null
  category: string
  root_cause: string | null
  corrective_action: string | null
  preventive_action: string | null
  source_followup_id: string | null
  owner_id: string
  status: string
  priority: string
  due_date: string | null
  completed_at: string | null
  verified_by: string | null
  verified_at: string | null
  created_at: string
  updated_at: string
}

export interface UseActionPlansReturn {
  createActionPlan: (payload: ActionPlanCreateRequest) => Promise<ActionPlanResponse>
  getLinkedActionPlan: (followUpId: string) => Promise<ActionPlanResponse | null>
  isLoading: boolean
  error: string | null
}

interface UseActionPlansOptions {
  apiUrl?: string
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function useActionPlans(options: UseActionPlansOptions = {}): UseActionPlansReturn {
  const { apiUrl = API_BASE_URL } = options

  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const mountedRef = useRef(true)

  useEffect(() => {
    mountedRef.current = true
    return () => { mountedRef.current = false }
  }, [])

  const createActionPlan = useCallback(async (payload: ActionPlanCreateRequest): Promise<ActionPlanResponse> => {
    setIsLoading(true)
    setError(null)

    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.access_token) {
        const errMsg = 'Session expired. Please log in again.'
        setError(errMsg)
        setIsLoading(false)
        throw new Error(errMsg)
      }

      const response = await fetch(`${apiUrl}/api/v1/action-plans`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}))
        const errMsg = errData.detail || `Failed to create action plan (${response.status})`
        setError(errMsg)
        setIsLoading(false)
        throw new Error(errMsg)
      }

      const data: ActionPlanResponse = await response.json()

      if (mountedRef.current) {
        setIsLoading(false)
        setError(null)
      }

      return data
    } catch (err) {
      if (mountedRef.current) {
        setIsLoading(false)
        if (!error) {
          setError(err instanceof Error ? err.message : 'Failed to create action plan.')
        }
      }
      throw err
    }
  }, [apiUrl, error])

  const getLinkedActionPlan = useCallback(async (followUpId: string): Promise<ActionPlanResponse | null> => {
    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.access_token) {
        return null
      }

      const response = await fetch(
        `${apiUrl}/api/v1/action-plans?source_followup_id=${encodeURIComponent(followUpId)}`,
        {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
            'Content-Type': 'application/json',
          },
        }
      )

      if (!response.ok) {
        return null
      }

      const data = await response.json()
      const items = data.items || []

      if (items.length === 0) {
        return null
      }

      return items[0] as ActionPlanResponse
    } catch {
      return null
    }
  }, [apiUrl])

  return {
    createActionPlan,
    getLinkedActionPlan,
    isLoading,
    error,
  }
}
