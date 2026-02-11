'use client'

import { useState, useCallback, useRef, useMemo, useEffect } from 'react'
import { createClient } from '@/lib/supabase/client'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface AcknowledgmentInfo {
  user_id: string
  acknowledged_at: string
  note: string | null
}

interface ActionItemInput {
  id: string
  acknowledgment: AcknowledgmentInfo | null
}

interface UseActionAcknowledgmentOptions {
  items: ActionItemInput[]
  apiUrl?: string
  onError?: (message: string) => void
}

interface UseActionAcknowledgmentReturn {
  isAcknowledged: (actionId: string) => boolean
  getAcknowledgment: (actionId: string) => AcknowledgmentInfo | null
  acknowledge: (actionId: string, options?: { note?: string }) => Promise<void>
  acknowledgedCount: number
  totalCount: number
}

// Module-level session cache shared across hook instances
let _sessionToken: string | null = null
let _sessionPromise: Promise<string | null> | null = null

function getSessionToken(): Promise<string | null> {
  if (_sessionToken) return Promise.resolve(_sessionToken)
  if (_sessionPromise) return _sessionPromise
  const supabase = createClient()
  _sessionPromise = supabase.auth.getSession().then(({ data: { session } }) => {
    _sessionToken = session?.access_token ?? null
    return _sessionToken
  })
  return _sessionPromise
}

export function useActionAcknowledgment({
  items,
  apiUrl = API_BASE_URL,
  onError,
}: UseActionAcknowledgmentOptions): UseActionAcknowledgmentReturn {
  // Build initial state from items
  const initialState = useMemo(() => {
    const map = new Map<string, AcknowledgmentInfo | null>()
    for (const item of items) {
      map.set(item.id, item.acknowledgment ?? null)
    }
    return map
  }, [items])

  const [acknowledgments, setAcknowledgments] = useState<Map<string, AcknowledgmentInfo | null>>(
    () => initialState
  )

  // Use a ref to track current acknowledgment state for synchronous checks
  const ackRef = useRef(acknowledgments)
  ackRef.current = acknowledgments

  // Track in-flight requests to prevent duplicates
  const inFlightRef = useRef<Set<string>>(new Set())

  // Stable ref for onError to avoid dependency churn
  const onErrorRef = useRef(onError)
  onErrorRef.current = onError

  // Eagerly start fetching session on mount
  useEffect(() => {
    getSessionToken()
  }, [])

  const isAcknowledged = useCallback(
    (actionId: string): boolean => {
      return acknowledgments.get(actionId) != null
    },
    [acknowledgments]
  )

  const getAcknowledgment = useCallback(
    (actionId: string): AcknowledgmentInfo | null => {
      return acknowledgments.get(actionId) ?? null
    },
    [acknowledgments]
  )

  const acknowledge = useCallback(
    (actionId: string, options?: { note?: string }): Promise<void> => {
      // Skip if already acknowledged (read from ref for latest state)
      if (ackRef.current.get(actionId) != null) {
        return Promise.resolve()
      }

      // Skip if request already in-flight for this action
      if (inFlightRef.current.has(actionId)) {
        return Promise.resolve()
      }

      inFlightRef.current.add(actionId)

      // Optimistic update
      const optimisticAck: AcknowledgmentInfo = {
        user_id: 'current-user',
        acknowledged_at: new Date().toISOString(),
        note: options?.note ?? null,
      }

      setAcknowledgments(prev => {
        const next = new Map(prev)
        next.set(actionId, optimisticAck)
        return next
      })

      const doRollback = (error: unknown) => {
        setAcknowledgments(prev => {
          const next = new Map(prev)
          next.set(actionId, null)
          return next
        })
        const message = error instanceof Error
          ? error.message
          : 'Unable to acknowledge action'
        onErrorRef.current?.(message)
      }

      const doFetch = (token: string) => {
        return fetch(
          `${apiUrl}/api/v1/actions/${actionId}/acknowledge`,
          {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ note: options?.note }),
          }
        )
        .then((response) => {
          if (!response.ok) {
            throw new Error(`Failed to acknowledge action (${response.status})`)
          }
        })
        .catch(doRollback)
        .finally(() => {
          inFlightRef.current.delete(actionId)
        })
      }

      // If session token is cached synchronously, call fetch immediately
      if (_sessionToken) {
        return doFetch(_sessionToken)
      }

      // Otherwise, get session and then call fetch
      return getSessionToken()
        .then((token) => {
          if (!token) {
            throw new Error('Session expired. Please log in again.')
          }
          return doFetch(token)
        })
        .catch((error: unknown) => {
          doRollback(error)
        })
        .finally(() => {
          inFlightRef.current.delete(actionId)
        })
    },
    [apiUrl]
  )

  const acknowledgedCount = useMemo(() => {
    let count = 0
    for (const ack of acknowledgments.values()) {
      if (ack != null) count++
    }
    return count
  }, [acknowledgments])

  const totalCount = acknowledgments.size

  return {
    isAcknowledged,
    getAcknowledgment,
    acknowledge,
    acknowledgedCount,
    totalCount,
  }
}
