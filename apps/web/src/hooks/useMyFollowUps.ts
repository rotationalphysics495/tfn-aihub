'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { createClient } from '@/lib/supabase/client'

export interface FollowUpItem {
  id: string
  action_item_id: string
  action_summary: string
  asset_name: string | null
  category: string | null
  assigned_to: string
  assigned_to_email: string | null
  assigned_by: string
  note: string | null
  status: 'assigned' | 'in_progress' | 'resolved'
  report_date: string
  created_at: string
  updated_at: string
  has_unread?: boolean
}

interface FollowUpListResponse {
  followups: FollowUpItem[]
  total_count: number
  counts_by_status: Record<string, number>
}

interface GroupedFollowUps {
  assigned: FollowUpItem[]
  in_progress: FollowUpItem[]
  resolved: FollowUpItem[]
}

export interface UseMyFollowUpsReturn {
  followups: FollowUpItem[]
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
  grouped: GroupedFollowUps
  totalCount: number
  hasFollowUps: boolean
}

interface UseMyFollowUpsOptions {
  apiUrl?: string
  autoFetch?: boolean
}

const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Unable to connect to server. Check your connection and try again.',
  AUTH_ERROR: 'Your session has expired. Please log in again.',
  SERVER_ERROR: "Something went wrong on our end. We're working on it.",
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

function groupByStatus(followups: FollowUpItem[]): GroupedFollowUps {
  return {
    assigned: followups.filter(f => f.status === 'assigned'),
    in_progress: followups.filter(f => f.status === 'in_progress'),
    resolved: followups.filter(f => f.status === 'resolved'),
  }
}

export function useMyFollowUps(options: UseMyFollowUpsOptions = {}): UseMyFollowUpsReturn {
  const {
    autoFetch = true,
    apiUrl = API_BASE_URL,
  } = options

  const [followups, setFollowups] = useState<FollowUpItem[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const mountedRef = useRef(true)

  const fetchFollowUps = useCallback(async () => {
    if (!mountedRef.current) return

    setIsLoading(true)
    setError(null)

    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.access_token) {
        setIsLoading(false)
        setError(ERROR_MESSAGES.AUTH_ERROR)
        return
      }

      const url = `${apiUrl}/api/v1/actions/followups?assigned_by=me&status=all`

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

      const data: FollowUpListResponse = await response.json()

      if (!mountedRef.current) return

      setFollowups(data.followups)
      setIsLoading(false)
      setError(null)
    } catch (err) {
      if (!mountedRef.current) return

      const message = err instanceof Error
        ? err.message
        : ERROR_MESSAGES.SERVER_ERROR

      setIsLoading(false)
      setError(message)
    }
  }, [apiUrl])

  useEffect(() => {
    mountedRef.current = true

    if (autoFetch) {
      fetchFollowUps()
    }

    return () => {
      mountedRef.current = false
    }
  }, [autoFetch, fetchFollowUps])

  const grouped = groupByStatus(followups)
  const totalCount = followups.length
  const hasFollowUps = totalCount > 0

  return {
    followups,
    isLoading,
    error,
    refetch: fetchFollowUps,
    grouped,
    totalCount,
    hasFollowUps,
  }
}

/**
 * Hook for the assignee's view: follow-ups assigned TO the current user.
 * Queries Supabase directly (RLS ensures only the assignee's rows are returned).
 */
export function useAssignedToMe(): UseMyFollowUpsReturn {
  const [followups, setFollowups] = useState<FollowUpItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const mountedRef = useRef(true)

  const fetchAssigned = useCallback(async () => {
    if (!mountedRef.current) return
    setIsLoading(true)
    setError(null)

    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.user?.id) {
        setIsLoading(false)
        setError(ERROR_MESSAGES.AUTH_ERROR)
        return
      }

      const { data, error: qError } = await supabase
        .from('action_followups')
        .select('id, action_item_id, action_summary, asset_name, category, assigned_to, assigned_by, note, status, report_date, created_at, updated_at')
        .eq('assigned_to', session.user.id)
        .order('created_at', { ascending: false })

      if (!mountedRef.current) return

      if (qError) {
        setError(ERROR_MESSAGES.SERVER_ERROR)
        setIsLoading(false)
        return
      }

      setFollowups((data ?? []) as FollowUpItem[])
      setIsLoading(false)
    } catch {
      if (!mountedRef.current) return
      setError(ERROR_MESSAGES.SERVER_ERROR)
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    mountedRef.current = true
    fetchAssigned()
    return () => { mountedRef.current = false }
  }, [fetchAssigned])

  const grouped = groupByStatus(followups)
  const totalCount = followups.length
  const hasFollowUps = totalCount > 0

  return {
    followups,
    isLoading,
    error,
    refetch: fetchAssigned,
    grouped,
    totalCount,
    hasFollowUps,
  }
}

/**
 * Update a follow-up status and/or note via PATCH /api/v1/actions/followups/{id}.
 */
export async function updateFollowUp(
  followupId: string,
  status: 'assigned' | 'in_progress' | 'resolved',
  note?: string
): Promise<void> {
  const supabase = createClient()
  const { data: { session } } = await supabase.auth.getSession()

  if (!session?.access_token) {
    throw new Error('Session expired. Please log in again.')
  }

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  const body: Record<string, string> = { status }
  if (note !== undefined) body.note = note

  const response = await fetch(`${apiUrl}/api/v1/actions/followups/${followupId}`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${session.access_token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    const errData = await response.json().catch(() => ({}))
    throw new Error(errData.detail || `Failed to update follow-up (${response.status})`)
  }
}
