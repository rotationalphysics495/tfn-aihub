'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { createClient } from '@/lib/supabase/client'
import type { FollowUpData } from '@/components/action-engine/types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface UseFollowUpsOptions {
  reportDate: string | undefined | null
}

interface UseFollowUpsReturn {
  followUps: Map<string, FollowUpData>
  isLoading: boolean
  error: string | null
  refetch: () => void
}

interface FollowUpRow {
  id: string
  action_item_id: string
  assigned_to: string
  status: 'assigned' | 'in_progress' | 'resolved'
  note: string | null
  created_at: string
  updated_at: string
}

/**
 * Select the most relevant follow-up for a given action item.
 * Prefers active (non-resolved) follow-ups over resolved ones.
 * Within the same category, takes the first (most recent by created_at DESC from query).
 */
function getMostRelevantFollowUp(followUps: FollowUpRow[]): FollowUpRow | null {
  if (followUps.length === 0) return null
  const active = followUps.filter(f => f.status !== 'resolved')
  if (active.length > 0) return active[0]
  return followUps[0]
}

/**
 * Truncate a UUID to a short display format.
 */
function truncateUUID(uuid: string): string {
  return uuid.substring(0, 8) + '...'
}

export function useFollowUps({ reportDate }: UseFollowUpsOptions): UseFollowUpsReturn {
  const [followUps, setFollowUps] = useState<Map<string, FollowUpData>>(new Map())
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const teamMembersCacheRef = useRef<Map<string, string> | null>(null)
  const [fetchKey, setFetchKey] = useState(0)

  const refetch = useCallback(() => {
    setFetchKey(prev => prev + 1)
  }, [])

  useEffect(() => {
    if (!reportDate) {
      setFollowUps(new Map())
      setIsLoading(false)
      setError(null)
      return
    }

    let cancelled = false

    async function fetchFollowUps() {
      setIsLoading(true)
      setError(null)

      try {
        const supabase = createClient()

        // Fetch follow-ups from Supabase
        const queryResult = await supabase
          .from('action_followups')
          .select('id, action_item_id, assigned_to, status, note, created_at, updated_at')
          .eq('report_date', reportDate!)
          .order('created_at', { ascending: false })

        if (cancelled) return

        if (queryResult.error) {
          setError(queryResult.error.message)
          setFollowUps(new Map())
          setIsLoading(false)
          return
        }

        const rows: FollowUpRow[] = queryResult.data ?? []

        if (rows.length === 0) {
          setFollowUps(new Map())
          setIsLoading(false)
          return
        }

        // Fetch team members for email resolution
        let memberMap: Map<string, string>
        if (teamMembersCacheRef.current) {
          memberMap = teamMembersCacheRef.current
        } else {
          memberMap = await fetchTeamMembers(supabase)
          if (!cancelled) {
            teamMembersCacheRef.current = memberMap
          }
        }

        if (cancelled) return

        // Group by action_item_id
        const grouped = new Map<string, FollowUpRow[]>()
        for (const row of rows) {
          const existing = grouped.get(row.action_item_id) ?? []
          existing.push(row)
          grouped.set(row.action_item_id, existing)
        }

        // Select most relevant follow-up per action item and resolve emails
        const result = new Map<string, FollowUpData>()
        grouped.forEach((group, actionItemId) => {
          const best = getMostRelevantFollowUp(group)
          if (best) {
            const email = memberMap.get(best.assigned_to) ?? truncateUUID(best.assigned_to)
            result.set(actionItemId, {
              id: best.id,
              action_item_id: best.action_item_id,
              assigned_to: best.assigned_to,
              assignee_email: email,
              status: best.status,
              note: best.note,
              created_at: best.created_at,
              updated_at: best.updated_at,
            })
          }
        })

        if (!cancelled) {
          setFollowUps(result)
          setIsLoading(false)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to fetch follow-ups')
          setFollowUps(new Map())
          setIsLoading(false)
        }
      }
    }

    fetchFollowUps()

    return () => {
      cancelled = true
    }
  }, [reportDate, fetchKey])

  return { followUps, isLoading, error, refetch }
}

async function fetchTeamMembers(
  supabase: ReturnType<typeof createClient>
): Promise<Map<string, string>> {
  const memberMap = new Map<string, string>()

  try {
    const { data: { session } } = await supabase.auth.getSession()
    if (!session?.access_token) return memberMap

    const response = await fetch(`${API_BASE_URL}/api/v1/team/members`, {
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) return memberMap

    const json = await response.json()
    const members = json.members ?? []
    for (const member of members) {
      if (member.user_id && member.email) {
        memberMap.set(member.user_id, member.email)
      }
    }
  } catch {
    // Soft failure — return empty map, caller will use truncated UUIDs
  }

  return memberMap
}
