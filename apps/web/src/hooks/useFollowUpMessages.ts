'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { createClient } from '@/lib/supabase/client'

export interface FollowUpMessage {
  id: string
  direction: 'outbound' | 'inbound'
  message_type: 'assignment' | 'response' | 'status_update' | 'escalation'
  sender_email: string
  subject: string | null
  body: string
  sent_at: string
}

interface FollowUpMessagesResponse {
  followup_id: string
  action_summary: string
  assignee_name: string | null
  assignee_email: string | null
  status: string
  messages: FollowUpMessage[]
  has_unread: boolean
  last_viewed_at: string | null
}

export interface UseFollowUpMessagesReturn {
  messages: FollowUpMessage[]
  isLoading: boolean
  error: string | null
  assignee_name: string | null
  assignee_email: string | null
  status: string | null
  has_unread: boolean
  last_viewed_at: string | null
  refetch: () => Promise<void>
  markViewed: () => Promise<void>
}

interface UseFollowUpMessagesOptions {
  followUpId: string
  apiUrl?: string
  autoFetch?: boolean
}

const ERROR_MESSAGES = {
  AUTH_ERROR: 'Your session has expired. Please log in again.',
  SERVER_ERROR: "Something went wrong on our end. We're working on it.",
  NO_DATA: 'Follow-up not found.',
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function useFollowUpMessages(options: UseFollowUpMessagesOptions): UseFollowUpMessagesReturn {
  const {
    followUpId,
    autoFetch = true,
    apiUrl = API_BASE_URL,
  } = options

  const [messages, setMessages] = useState<FollowUpMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [assignee_name, setAssigneeName] = useState<string | null>(null)
  const [assignee_email, setAssigneeEmail] = useState<string | null>(null)
  const [status, setStatus] = useState<string | null>(null)
  const [has_unread, setHasUnread] = useState(false)
  const [last_viewed_at, setLastViewedAt] = useState<string | null>(null)

  const mountedRef = useRef(true)

  const fetchMessages = useCallback(async () => {
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

      const url = `${apiUrl}/api/v1/followups/${followUpId}/messages`

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

      const data: FollowUpMessagesResponse = await response.json()

      if (!mountedRef.current) return

      setMessages(data.messages)
      setAssigneeName(data.assignee_name)
      setAssigneeEmail(data.assignee_email)
      setStatus(data.status)
      setHasUnread(data.has_unread)
      setLastViewedAt(data.last_viewed_at)
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
  }, [apiUrl, followUpId])

  const markViewed = useCallback(async () => {
    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.access_token) return

      const url = `${apiUrl}/api/v1/followups/${followUpId}/viewed`

      await fetch(url, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      })
    } catch {
      // markViewed failure is non-blocking
    }
  }, [apiUrl, followUpId])

  useEffect(() => {
    mountedRef.current = true

    if (autoFetch) {
      fetchMessages()
    }

    return () => {
      mountedRef.current = false
    }
  }, [autoFetch, fetchMessages])

  return {
    messages,
    isLoading,
    error,
    assignee_name,
    assignee_email,
    status,
    has_unread,
    last_viewed_at,
    refetch: fetchMessages,
    markViewed,
  }
}
