/**
 * Audit Log Viewer Page (Story 9.15, Task 6)
 *
 * Admin page for viewing audit log entries.
 *
 * AC#2: Entries displayed in reverse chronological order
 * AC#2: Filters available - date range, action type, target user
 *
 * References:
 * - [Source: architecture/voice-briefing.md#Admin UI Architecture]
 * - [Source: prd/prd-functional-requirements.md#FR50, FR56]
 */
'use client'

import { useState, useEffect, useCallback } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { AuditLogTable, type AuditLogEntry } from '@/components/admin/AuditLogTable'
import { AuditLogFilters, type AuditLogFiltersState } from '@/components/admin/AuditLogFilters'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { AlertTriangle, RefreshCw, Shield, Loader2, FileText } from 'lucide-react'

interface AuditLogListResponse {
  entries: AuditLogEntry[]
  total: number
  page: number
  page_size: number
}

export default function AuditLogPage() {
  // Router for URL state management
  const router = useRouter()
  const searchParams = useSearchParams()

  // Data state
  const [entries, setEntries] = useState<AuditLogEntry[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(50)

  // Filter state from URL params
  const [filters, setFilters] = useState<AuditLogFiltersState>({
    startDate: searchParams.get('start_date') || undefined,
    endDate: searchParams.get('end_date') || undefined,
    actionType: searchParams.get('action_type') || undefined,
    targetUserId: searchParams.get('target_user_id') || undefined,
  })

  // UI state
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch audit logs
  const fetchAuditLogs = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      // Build query parameters
      const params = new URLSearchParams()
      params.set('page', page.toString())
      params.set('page_size', pageSize.toString())

      if (filters.startDate) params.set('start_date', filters.startDate)
      if (filters.endDate) params.set('end_date', filters.endDate)
      if (filters.actionType) params.set('action_type', filters.actionType)
      if (filters.targetUserId) params.set('target_user_id', filters.targetUserId)

      const response = await fetch(`/api/v1/admin/audit-logs?${params.toString()}`, {
        credentials: 'include',
      })

      if (!response.ok) {
        if (response.status === 403) {
          throw new Error('You do not have permission to access audit logs')
        }
        throw new Error(`Failed to fetch audit logs: ${response.statusText}`)
      }

      const data: AuditLogListResponse = await response.json()

      setEntries(data.entries)
      setTotal(data.total)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load audit logs')
    } finally {
      setIsLoading(false)
    }
  }, [page, pageSize, filters])

  // Initial fetch and on filter change
  useEffect(() => {
    fetchAuditLogs()
  }, [fetchAuditLogs])

  // Update URL when filters change
  const handleFiltersChange = useCallback((newFilters: AuditLogFiltersState) => {
    setFilters(newFilters)
    setPage(1) // Reset to page 1 when filters change

    // Update URL params for shareable links
    const params = new URLSearchParams()
    if (newFilters.startDate) params.set('start_date', newFilters.startDate)
    if (newFilters.endDate) params.set('end_date', newFilters.endDate)
    if (newFilters.actionType) params.set('action_type', newFilters.actionType)
    if (newFilters.targetUserId) params.set('target_user_id', newFilters.targetUserId)

    const newUrl = params.toString() ? `?${params.toString()}` : '/admin/audit'
    router.replace(newUrl)
  }, [router])

  // Clear all filters
  const handleClearFilters = useCallback(() => {
    handleFiltersChange({})
  }, [handleFiltersChange])

  // Pagination handlers
  const handleNextPage = useCallback(() => {
    if ((page * pageSize) < total) {
      setPage((p) => p + 1)
    }
  }, [page, pageSize, total])

  const handlePrevPage = useCallback(() => {
    if (page > 1) {
      setPage((p) => p - 1)
    }
  }, [page])

  // Calculate pagination info
  const startItem = (page - 1) * pageSize + 1
  const endItem = Math.min(page * pageSize, total)
  const hasNextPage = endItem < total
  const hasPrevPage = page > 1

  // Check if any filters are active
  const hasActiveFilters = !!(filters.startDate || filters.endDate || filters.actionType || filters.targetUserId)

  // Loading state
  if (isLoading && entries.length === 0) {
    return (
      <div className="space-y-6">
        <header>
          <h1 className="text-2xl font-bold text-slate-900">Audit Log</h1>
          <p className="text-slate-500 mt-1">Loading...</p>
        </header>
        <Card>
          <CardContent className="py-12">
            <div className="flex items-center justify-center text-slate-500">
              <Loader2 className="w-6 h-6 animate-spin mr-2" />
              <span>Loading audit logs...</span>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Error state with no data
  if (error && entries.length === 0) {
    return (
      <div className="space-y-6">
        <header>
          <h1 className="text-2xl font-bold text-slate-900">Audit Log</h1>
        </header>
        <Card>
          <CardContent className="py-12">
            <div className="flex flex-col items-center justify-center text-center">
              <AlertTriangle className="w-12 h-12 text-red-500 mb-4" />
              <h2 className="text-lg font-medium text-slate-900 mb-2">Error Loading Audit Logs</h2>
              <p className="text-slate-500 mb-4">{error}</p>
              <Button onClick={fetchAuditLogs}>
                <RefreshCw className="w-4 h-4 mr-2" />
                Try Again
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <header className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Audit Log</h1>
          <p className="text-slate-500 mt-1">
            View admin configuration changes and system events
          </p>
        </div>
        <Button variant="outline" onClick={fetchAuditLogs} disabled={isLoading}>
          <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </header>

      {/* Error Banner */}
      {error && entries.length > 0 && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center gap-2">
          <AlertTriangle className="w-5 h-5" />
          <span>{error}</span>
        </div>
      )}

      {/* Stats Card */}
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-slate-100 rounded-lg">
                <FileText className="w-5 h-5 text-slate-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{total}</div>
                <div className="text-sm text-slate-500">
                  {hasActiveFilters ? 'Matching Entries' : 'Total Entries'}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Shield className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">90</div>
                <div className="text-sm text-slate-500">Day Retention</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg">Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <AuditLogFilters
            filters={filters}
            onFiltersChange={handleFiltersChange}
            onClear={handleClearFilters}
          />
        </CardContent>
      </Card>

      {/* Audit Log Table */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg flex items-center gap-2">
              Audit Entries
              <Badge variant="secondary" className="bg-slate-100">
                {total}
              </Badge>
            </CardTitle>
            {/* Pagination Info */}
            {total > 0 && (
              <div className="text-sm text-slate-500">
                Showing {startItem}-{endItem} of {total}
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <AuditLogTable
            entries={entries}
            isLoading={isLoading}
          />

          {/* Pagination Controls */}
          {total > pageSize && (
            <div className="flex items-center justify-between mt-4 pt-4 border-t">
              <Button
                variant="outline"
                onClick={handlePrevPage}
                disabled={!hasPrevPage || isLoading}
              >
                Previous
              </Button>
              <span className="text-sm text-slate-500">
                Page {page} of {Math.ceil(total / pageSize)}
              </span>
              <Button
                variant="outline"
                onClick={handleNextPage}
                disabled={!hasNextPage || isLoading}
              >
                Next
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Info Box */}
      <Card className="bg-slate-50 border-slate-200">
        <CardContent className="py-4">
          <h3 className="font-medium text-slate-700 mb-2">About Audit Logs</h3>
          <ul className="text-sm text-slate-600 space-y-1">
            <li><strong>Retention:</strong> Audit logs are retained for a minimum of 90 days per NFR25</li>
            <li><strong>Tamper-evident:</strong> Logs are append-only and cannot be modified or deleted</li>
            <li><strong>Tracked actions:</strong> Role changes, asset assignments, and other admin configuration changes</li>
          </ul>
          <p className="text-xs text-slate-500 mt-3">
            All admin actions are automatically logged for accountability and troubleshooting purposes.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
