'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { createClient } from '@/lib/supabase/client'

/**
 * Smart Summary Hook
 *
 * Fetches the AI-generated smart summary for a given date from the
 * Smart Summary API. If no cached summary exists, triggers generation
 * automatically.
 *
 * @see Story 3.5 - Smart Summary Generator
 */

export interface SmartSummaryData {
  id: string | null
  date: string
  summary_text: string
  citations: Array<{
    asset_name?: string
    metric_name: string
    metric_value: string
    source_table: string
    timestamp?: string
  }>
  model_used: string
  prompt_tokens: number
  completion_tokens: number
  generation_duration_ms: number
  is_fallback: boolean
  created_at: string | null
}

interface SmartSummaryState {
  data: SmartSummaryData | null
  isLoading: boolean
  isGenerating: boolean
  error: string | null
}

interface UseSmartSummaryOptions {
  /** Auto-fetch on mount (default: true) */
  autoFetch?: boolean
  /** API base URL (default: process.env.NEXT_PUBLIC_API_URL) */
  apiUrl?: string
  /** Report date override (YYYY-MM-DD, defaults to T-1/yesterday) */
  reportDate?: string
  /** Auto-generate if no cached summary on 404 (default: true for T-1, set false for historical) */
  autoGenerate?: boolean
}

export interface UseSmartSummaryReturn extends SmartSummaryState {
  /** Manually refetch the summary (from cache) */
  refetch: () => Promise<void>
  /** Force regenerate the summary (bypasses cache) */
  regenerate: () => Promise<void>
  /** Manually trigger summary generation (for historical dates) */
  generate: () => Promise<void>
  /** Whether a real AI summary is available */
  hasSummary: boolean
  /** Whether the user can trigger on-demand generation (no summary, not loading) */
  canGenerate: boolean
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

function getYesterdayDate(): string {
  const d = new Date()
  d.setDate(d.getDate() - 1)
  return d.toISOString().split('T')[0]
}

export function useSmartSummary(options: UseSmartSummaryOptions = {}): UseSmartSummaryReturn {
  const {
    autoFetch = true,
    apiUrl = API_BASE_URL,
    reportDate,
    autoGenerate = true,
  } = options

  const [state, setState] = useState<SmartSummaryState>({
    data: null,
    isLoading: false,
    isGenerating: false,
    error: null,
  })

  const mountedRef = useRef(true)

  const fetchSummary = useCallback(async () => {
    if (!mountedRef.current) return

    setState(prev => ({ ...prev, isLoading: true, error: null }))

    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.access_token) {
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: 'Session expired. Please log in again.',
        }))
        return
      }

      const date = reportDate || getYesterdayDate()
      const headers = {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json',
      }

      // Try to get cached summary first
      const getUrl = `${apiUrl}/api/summaries/smart/${date}`
      const response = await fetch(getUrl, { method: 'GET', headers })

      if (response.ok) {
        const data: SmartSummaryData = await response.json()
        if (mountedRef.current) {
          setState({ data, isLoading: false, isGenerating: false, error: null })
        }
        return
      }

      // 404 = no cached summary
      if (response.status === 404) {
        if (!mountedRef.current) return

        // When autoGenerate is false (historical dates), don't auto-trigger generation
        if (!autoGenerate) {
          setState(prev => ({ ...prev, isLoading: false, isGenerating: false, error: null }))
          return
        }

        // Auto-trigger generation for T-1 (default behavior)
        setState(prev => ({ ...prev, isGenerating: true }))

        const generateUrl = `${apiUrl}/api/summaries/generate`
        const genResponse = await fetch(generateUrl, {
          method: 'POST',
          headers,
          body: JSON.stringify({ target_date: date, regenerate: false }),
        })

        if (genResponse.ok || genResponse.status === 201) {
          const data: SmartSummaryData = await genResponse.json()
          if (mountedRef.current) {
            setState({ data, isLoading: false, isGenerating: false, error: null })
          }
          return
        }

        // Generation failed — surface a user-friendly error
        if (mountedRef.current) {
          setState(prev => ({
            ...prev,
            isLoading: false,
            isGenerating: false,
            error: 'Unable to generate AI summary. Using fallback.',
          }))
        }
        return
      }

      if (response.status === 401) {
        throw new Error('Session expired. Please log in again.')
      }

      throw new Error('Unable to load AI summary.')
    } catch (error) {
      if (!mountedRef.current) return
      const message = error instanceof Error ? error.message : 'Unable to load AI summary.'
      setState(prev => ({
        ...prev,
        isLoading: false,
        isGenerating: false,
        error: message,
      }))
    }
  }, [apiUrl, reportDate, autoGenerate])

  const regenerateSummary = useCallback(async () => {
    if (!mountedRef.current) return

    setState(prev => ({ ...prev, isLoading: true, isGenerating: true, error: null }))

    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.access_token) {
        setState(prev => ({ ...prev, isLoading: false, isGenerating: false, error: 'Session expired. Please log in again.' }))
        return
      }

      const date = reportDate || getYesterdayDate()
      const headers = {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json',
      }

      const url = `${apiUrl}/api/summaries/smart/${date}?regenerate=true`
      const response = await fetch(url, { method: 'GET', headers })

      if (response.ok) {
        const data: SmartSummaryData = await response.json()
        if (mountedRef.current) {
          setState({ data, isLoading: false, isGenerating: false, error: null })
        }
        return
      }

      throw new Error('Unable to regenerate AI summary.')
    } catch (error) {
      if (!mountedRef.current) return
      const message = error instanceof Error ? error.message : 'Unable to regenerate AI summary.'
      setState(prev => ({ ...prev, isLoading: false, isGenerating: false, error: message }))
    }
  }, [apiUrl, reportDate])

  const generateSummary = useCallback(async () => {
    if (!mountedRef.current) return

    setState(prev => ({ ...prev, isGenerating: true, error: null }))

    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.access_token) {
        setState(prev => ({ ...prev, isGenerating: false, error: 'Session expired. Please log in again.' }))
        return
      }

      const date = reportDate || getYesterdayDate()
      const headers = {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json',
      }

      const generateUrl = `${apiUrl}/api/summaries/generate`
      const response = await fetch(generateUrl, {
        method: 'POST',
        headers,
        body: JSON.stringify({ target_date: date, regenerate: false }),
      })

      if (response.ok || response.status === 201) {
        const data: SmartSummaryData = await response.json()
        if (mountedRef.current) {
          setState({ data, isLoading: false, isGenerating: false, error: null })
        }
        return
      }

      if (response.status === 401) {
        throw new Error('Session expired. Please log in again.')
      }

      if (mountedRef.current) {
        setState(prev => ({
          ...prev,
          isGenerating: false,
          error: 'Unable to generate AI summary. Please try again.',
        }))
      }
    } catch (error) {
      if (!mountedRef.current) return
      const message = error instanceof Error ? error.message : 'Unable to generate AI summary.'
      setState(prev => ({ ...prev, isGenerating: false, error: message }))
    }
  }, [apiUrl, reportDate])

  useEffect(() => {
    mountedRef.current = true
    if (autoFetch) {
      fetchSummary()
    }
    return () => { mountedRef.current = false }
  }, [autoFetch, fetchSummary])

  return {
    ...state,
    refetch: fetchSummary,
    regenerate: regenerateSummary,
    generate: generateSummary,
    hasSummary: state.data !== null,
    canGenerate: !state.data && !state.isLoading && !state.isGenerating,
  }
}
