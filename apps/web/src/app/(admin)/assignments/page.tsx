/**
 * Asset Assignment Page (Story 9.13, Task 9)
 *
 * Admin page for managing supervisor asset assignments.
 *
 * AC#1: Grid display of assignments
 * AC#2: Preview impact before saving
 * AC#3: Save changes atomically with audit logging
 * AC#4: Support temporary assignments
 *
 * Features:
 * - Task 9.1: Page component
 * - Task 9.2: Fetch supervisors
 * - Task 9.3: Fetch assets grouped by area
 * - Task 9.4: Fetch current assignments
 * - Task 9.5: Wire up save with confirmation
 * - Task 9.6: Loading and error states
 *
 * References:
 * - [Source: architecture/voice-briefing.md#Admin UI Architecture]
 */
'use client'

import { useState, useEffect, useCallback } from 'react'
import { AssetAssignmentGrid, type AssignmentChange, type Supervisor, type Asset, type Assignment } from '@/components/admin/AssetAssignmentGrid'
import { AssignmentPreview } from '@/components/admin/AssignmentPreview'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { AlertTriangle, RefreshCw, Users, Grid3X3, CheckCircle, Loader2 } from 'lucide-react'

interface ApiResponse<T> {
  data?: T
  error?: string
}

interface AssignmentListResponse {
  assignments: Assignment[]
  total_count: number
  supervisors: Supervisor[]
  assets: Asset[]
}

interface PreviewResponse {
  changes_count: number
  users_affected: number
  impact_summary: string
  user_impacts: Array<{
    user_id: string
    user_email?: string | null
    current_asset_count: number
    current_area_count: number
    new_asset_count: number
    new_area_count: number
    assets_added: string[]
    assets_removed: string[]
  }>
  warnings: string[]
}

interface BatchResponse {
  success: boolean
  applied_count: number
  batch_id: string
  message: string
}

export default function AssignmentsPage() {
  // Data state
  const [supervisors, setSupervisors] = useState<Supervisor[]>([])
  const [assets, setAssets] = useState<Asset[]>([])
  const [assignments, setAssignments] = useState<Assignment[]>([])

  // UI state
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [pendingChanges, setPendingChanges] = useState<AssignmentChange[]>([])
  const [previewData, setPreviewData] = useState<PreviewResponse | null>(null)
  const [isPreviewLoading, setIsPreviewLoading] = useState(false)
  const [previewError, setPreviewError] = useState<string | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)

  // Fetch all data (Task 9.2, 9.3, 9.4)
  const fetchData = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch('/api/v1/admin/assignments', {
        credentials: 'include',
      })

      if (!response.ok) {
        if (response.status === 403) {
          throw new Error('You do not have permission to access the admin panel')
        }
        throw new Error(`Failed to fetch assignments: ${response.statusText}`)
      }

      const data: AssignmentListResponse = await response.json()

      setSupervisors(data.supervisors)
      setAssets(data.assets)
      setAssignments(data.assignments)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data')
    } finally {
      setIsLoading(false)
    }
  }, [])

  // Initial fetch
  useEffect(() => {
    fetchData()
  }, [fetchData])

  // Fetch preview when changes are made (debounced)
  useEffect(() => {
    if (pendingChanges.length === 0) {
      setPreviewData(null)
      return
    }

    const fetchPreview = async () => {
      setIsPreviewLoading(true)
      setPreviewError(null)

      try {
        const response = await fetch('/api/v1/admin/assignments/preview', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ changes: pendingChanges }),
        })

        if (!response.ok) {
          throw new Error('Failed to calculate preview')
        }

        const data: PreviewResponse = await response.json()
        setPreviewData(data)
      } catch (err) {
        setPreviewError(err instanceof Error ? err.message : 'Preview failed')
      } finally {
        setIsPreviewLoading(false)
      }
    }

    // Debounce preview requests
    const timer = setTimeout(fetchPreview, 300)
    return () => clearTimeout(timer)
  }, [pendingChanges])

  // Handle pending changes from grid
  const handleChangesPending = useCallback((changes: AssignmentChange[]) => {
    setPendingChanges(changes)
    setSaveSuccess(false)
  }, [])

  // Cancel all pending changes
  const handleCancel = useCallback(() => {
    setPendingChanges([])
    setPreviewData(null)
    setPreviewError(null)
  }, [])

  // Save changes (Task 9.5)
  const handleConfirm = useCallback(async () => {
    if (pendingChanges.length === 0) return

    setIsSaving(true)
    setSaveSuccess(false)

    try {
      const response = await fetch('/api/v1/admin/assignments/batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ changes: pendingChanges }),
      })

      if (!response.ok) {
        throw new Error('Failed to save changes')
      }

      const data: BatchResponse = await response.json()

      // Success - refresh data and clear pending
      setSaveSuccess(true)
      setPendingChanges([])
      setPreviewData(null)

      // Refresh assignments to get updated state
      await fetchData()

      // Clear success message after delay
      setTimeout(() => setSaveSuccess(false), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save changes')
    } finally {
      setIsSaving(false)
    }
  }, [pendingChanges, fetchData])

  // Loading state (Task 9.6)
  if (isLoading) {
    return (
      <div className="space-y-6">
        <header>
          <h1 className="text-2xl font-bold text-slate-900">Asset Assignments</h1>
          <p className="text-slate-500 mt-1">Loading...</p>
        </header>
        <Card>
          <CardContent className="py-12">
            <div className="flex items-center justify-center text-slate-500">
              <Loader2 className="w-6 h-6 animate-spin mr-2" />
              <span>Loading assignments...</span>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Error state (Task 9.6)
  if (error && !supervisors.length) {
    return (
      <div className="space-y-6">
        <header>
          <h1 className="text-2xl font-bold text-slate-900">Asset Assignments</h1>
        </header>
        <Card>
          <CardContent className="py-12">
            <div className="flex flex-col items-center justify-center text-center">
              <AlertTriangle className="w-12 h-12 text-red-500 mb-4" />
              <h2 className="text-lg font-medium text-slate-900 mb-2">Error Loading Data</h2>
              <p className="text-slate-500 mb-4">{error}</p>
              <Button onClick={fetchData}>
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
          <h1 className="text-2xl font-bold text-slate-900">Asset Assignments</h1>
          <p className="text-slate-500 mt-1">
            Assign supervisors to assets for scoped briefings and handoffs
          </p>
        </div>
        <Button variant="outline" onClick={fetchData} disabled={isLoading || isSaving}>
          <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </header>

      {/* Success Message */}
      {saveSuccess && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg flex items-center gap-2">
          <CheckCircle className="w-5 h-5" />
          <span>Changes saved successfully!</span>
        </div>
      )}

      {/* Error Banner */}
      {error && supervisors.length > 0 && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center gap-2">
          <AlertTriangle className="w-5 h-5" />
          <span>{error}</span>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Users className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{supervisors.length}</div>
                <div className="text-sm text-slate-500">Supervisors</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <Grid3X3 className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{assets.length}</div>
                <div className="text-sm text-slate-500">Assets</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <CheckCircle className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{assignments.length}</div>
                <div className="text-sm text-slate-500">Active Assignments</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <div className="flex gap-6">
        {/* Grid */}
        <Card className="flex-1">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              Assignment Grid
              {pendingChanges.length > 0 && (
                <Badge variant="secondary" className="bg-amber-100 text-amber-700">
                  {pendingChanges.length} pending
                </Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <AssetAssignmentGrid
              supervisors={supervisors}
              assets={assets}
              assignments={assignments}
              onChangesPending={handleChangesPending}
              pendingChanges={pendingChanges}
              disabled={isSaving}
            />
          </CardContent>
        </Card>

        {/* Preview Panel */}
        {pendingChanges.length > 0 && (
          <div className="w-80 shrink-0">
            <AssignmentPreview
              changes={pendingChanges}
              previewData={previewData}
              isLoading={isPreviewLoading}
              error={previewError}
              supervisors={supervisors}
              assets={assets}
              onConfirm={handleConfirm}
              onCancel={handleCancel}
              isSaving={isSaving}
            />
          </div>
        )}
      </div>

      {/* Instructions */}
      <Card className="bg-slate-50 border-slate-200">
        <CardContent className="py-4">
          <h3 className="font-medium text-slate-700 mb-2">How to use</h3>
          <ul className="text-sm text-slate-600 space-y-1">
            <li>• Click on a cell to toggle assignment (checkmark = assigned)</li>
            <li>• Changes are highlighted in amber until saved</li>
            <li>• Review the preview panel to see the impact of your changes</li>
            <li>• All changes are logged for audit purposes</li>
            <li>• Dashed border indicates a temporary assignment with expiration</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}
