'use client'

import { useState, useCallback, useRef, useEffect } from 'react'
import { createClient } from '@/lib/supabase/client'

export interface RowValidationError {
  row_number: number
  field: string
  message: string
}

export interface ScheduleRowPreview {
  row_number: number
  date: string
  shift: string
  asset_name: string
  product_name: string
  scheduled_quantity: string
  asset_match_status: 'matched' | 'suggested' | 'unmatched'
  asset_id: string | null
  suggestions: string[]
  product_id: string | null
  is_new_product: boolean
  errors: RowValidationError[]
}

export interface SchedulePreviewResponse {
  parsed_rows_count: number
  rows: ScheduleRowPreview[]
  has_errors: boolean
  matched_assets: string[]
  matched_products: string[]
  new_products: string[]
}

export interface ScheduleConfirmRow {
  asset_id: string
  product_name: string
  scheduled_date: string
  shift: string
  scheduled_quantity: number
}

export interface ScheduleConfirmResponse {
  rows_inserted: number
  products_created: number
  total_processed: number
}

interface UseScheduleUploadOptions {
  apiUrl?: string
}

const ERROR_MESSAGES = {
  AUTH_ERROR: 'Your session has expired. Please log in again.',
  SERVER_ERROR: "Something went wrong on our end. We're working on it.",
  NETWORK_ERROR: 'Unable to connect to server. Check your connection and try again.',
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function useScheduleUpload(options: UseScheduleUploadOptions = {}) {
  const { apiUrl = API_BASE_URL } = options

  const [isUploading, setIsUploading] = useState(false)
  const [isConfirming, setIsConfirming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [previewData, setPreviewData] = useState<SchedulePreviewResponse | null>(null)
  const [confirmResult, setConfirmResult] = useState<ScheduleConfirmResponse | null>(null)

  const mountedRef = useRef(true)

  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
    }
  }, [])

  const uploadForPreview = useCallback(async (file: File) => {
    if (!mountedRef.current) return

    setIsUploading(true)
    setError(null)

    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.access_token) {
        if (!mountedRef.current) return
        setIsUploading(false)
        setError(ERROR_MESSAGES.AUTH_ERROR)
        return
      }

      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch(`${apiUrl}/api/v1/schedule/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
        },
        body: formData,
      })

      if (!mountedRef.current) return

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error(ERROR_MESSAGES.AUTH_ERROR)
        }
        throw new Error(ERROR_MESSAGES.SERVER_ERROR)
      }

      const data: SchedulePreviewResponse = await response.json()

      if (!mountedRef.current) return

      setPreviewData(data)
      setIsUploading(false)
    } catch (err) {
      if (!mountedRef.current) return

      const message = err instanceof Error
        ? err.message
        : ERROR_MESSAGES.SERVER_ERROR

      setError(message)
      setIsUploading(false)
    }
  }, [apiUrl])

  const confirmUpload = useCallback(async () => {
    if (!mountedRef.current || !previewData) return

    setIsConfirming(true)
    setError(null)

    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.access_token) {
        if (!mountedRef.current) return
        setIsConfirming(false)
        setError(ERROR_MESSAGES.AUTH_ERROR)
        return
      }

      const confirmRows: ScheduleConfirmRow[] = previewData.rows
        .filter(row => row.asset_match_status === 'matched' && row.errors.length === 0)
        .map(row => ({
          asset_id: row.asset_id!,
          product_name: row.product_name,
          scheduled_date: row.date,
          shift: row.shift,
          scheduled_quantity: parseInt(row.scheduled_quantity, 10) || 0,
        }))

      const response = await fetch(`${apiUrl}/api/v1/schedule/upload/confirm`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ rows: confirmRows }),
      })

      if (!mountedRef.current) return

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error(ERROR_MESSAGES.AUTH_ERROR)
        }
        throw new Error(ERROR_MESSAGES.SERVER_ERROR)
      }

      const data: ScheduleConfirmResponse = await response.json()

      if (!mountedRef.current) return

      setConfirmResult(data)
      setIsConfirming(false)
    } catch (err) {
      if (!mountedRef.current) return

      const message = err instanceof Error
        ? err.message
        : ERROR_MESSAGES.SERVER_ERROR

      setError(message)
      setIsConfirming(false)
    }
  }, [apiUrl, previewData])

  const reset = useCallback(() => {
    setPreviewData(null)
    setConfirmResult(null)
    setError(null)
    setIsUploading(false)
    setIsConfirming(false)
  }, [])

  return {
    isUploading,
    isConfirming,
    error,
    previewData,
    confirmResult,
    uploadForPreview,
    confirmUpload,
    reset,
  }
}
