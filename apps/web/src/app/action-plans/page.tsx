'use client'

import { Suspense, useState, useEffect, useCallback, useRef } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { AlertCircle, RefreshCw, ClipboardList } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { createClient } from '@/lib/supabase/client'
import { ActionPlanCard } from '@/components/action-plans/ActionPlanCard'
import { ActionPlanDetail } from '@/components/action-plans/ActionPlanDetail'
import { groupPlans } from '@/components/action-plans/types'
import type { ActionPlan, ActionPlanStatus, ActionPlanUpdate, GroupedPlans } from '@/components/action-plans/types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const ERROR_MESSAGES = {
  AUTH_ERROR: 'Your session has expired. Please log in again.',
  SERVER_ERROR: 'Failed to load action plans. Please try again.',
}

interface ActionPlanWithUpdates extends ActionPlan {
  updates: ActionPlanUpdate[]
}

const STATUS_SECTIONS: Array<{ key: ActionPlanStatus; label: string }> = [
  { key: 'open', label: 'Open' },
  { key: 'in_progress', label: 'In Progress' },
  { key: 'completed', label: 'Completed' },
  { key: 'verified', label: 'Verified' },
]

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      {[1, 2, 3].map((i) => (
        <div key={i} className="space-y-3">
          <div className="h-6 w-32 bg-muted rounded animate-pulse" />
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {[1, 2].map((j) => (
              <div key={j} className="rounded-lg border p-4 space-y-2 animate-pulse">
                <div className="h-4 w-3/4 bg-muted rounded" />
                <div className="h-3 w-1/2 bg-muted rounded" />
                <div className="h-3 w-1/3 bg-muted rounded" />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

export default function ActionPlansDashboardPage() {
  return (
    <Suspense fallback={
      <div className="p-6 space-y-6">
        <DashboardSkeleton />
      </div>
    }>
      <ActionPlansDashboardContent />
    </Suspense>
  )
}

function ActionPlansDashboardContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const mountedRef = useRef(true)
  const initialLoadRef = useRef(true)

  const [statusFilter, setStatusFilter] = useState(searchParams.get('status') || 'all')
  const [priorityFilter, setPriorityFilter] = useState(searchParams.get('priority') || 'all')
  const [assetFilter, setAssetFilter] = useState(searchParams.get('asset_id') || 'all')
  const [ownerFilter, setOwnerFilter] = useState(searchParams.get('owner_id') || 'all')

  const [plans, setPlans] = useState<ActionPlan[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedPlan, setSelectedPlan] = useState<ActionPlanWithUpdates | null>(null)

  const fetchPlans = useCallback(async (
    status: string,
    priority: string,
    asset_id: string,
    owner_id: string,
  ) => {
    if (!mountedRef.current) return

    // Only show full loading on initial load
    if (initialLoadRef.current) {
      setIsLoading(true)
    }
    setError(null)

    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.access_token) {
        setIsLoading(false)
        initialLoadRef.current = false
        setError(ERROR_MESSAGES.AUTH_ERROR)
        return
      }

      const params = new URLSearchParams()
      params.set('page_size', '100')
      if (status && status !== 'all') params.set('status', status)
      if (priority && priority !== 'all') params.set('priority', priority)
      if (asset_id && asset_id !== 'all') params.set('asset_id', asset_id)
      if (owner_id && owner_id !== 'all') params.set('owner_id', owner_id)

      const url = `${API_BASE_URL}/api/v1/action-plans?${params.toString()}`

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        if (response.status === 401) throw new Error(ERROR_MESSAGES.AUTH_ERROR)
        throw new Error(ERROR_MESSAGES.SERVER_ERROR)
      }

      const data = await response.json()

      if (!mountedRef.current) return

      const fetchedPlans: ActionPlan[] = data.plans || data.items || []
      setPlans(fetchedPlans)
      setIsLoading(false)
      initialLoadRef.current = false
      setError(null)
    } catch (err) {
      if (!mountedRef.current) return
      setIsLoading(false)
      initialLoadRef.current = false
      setError(err instanceof Error ? err.message : ERROR_MESSAGES.SERVER_ERROR)
    }
  }, [])

  useEffect(() => {
    mountedRef.current = true
    fetchPlans(statusFilter, priorityFilter, assetFilter, ownerFilter)
    return () => { mountedRef.current = false }
  }, [fetchPlans, statusFilter, priorityFilter, assetFilter, ownerFilter])

  const updateFilter = useCallback((key: string, value: string) => {
    // Compute new filter values (including the change being made)
    const newStatus = key === 'status' ? value : statusFilter
    const newPriority = key === 'priority' ? value : priorityFilter
    const newAsset = key === 'asset_id' ? value : assetFilter
    const newOwner = key === 'owner_id' ? value : ownerFilter

    // Update local state (triggers re-fetch via useEffect)
    if (key === 'status') setStatusFilter(value)
    else if (key === 'priority') setPriorityFilter(value)
    else if (key === 'asset_id') setAssetFilter(value)
    else if (key === 'owner_id') setOwnerFilter(value)

    // Build URL from current filter state
    const params = new URLSearchParams()
    if (newStatus && newStatus !== 'all') params.set('status', newStatus)
    if (newPriority && newPriority !== 'all') params.set('priority', newPriority)
    if (newAsset && newAsset !== 'all') params.set('asset_id', newAsset)
    if (newOwner && newOwner !== 'all') params.set('owner_id', newOwner)
    const qs = params.toString()
    router.replace(qs ? `/action-plans?${qs}` : '/action-plans')
  }, [statusFilter, priorityFilter, assetFilter, ownerFilter, router])

  const refetch = useCallback(() => {
    fetchPlans(statusFilter, priorityFilter, assetFilter, ownerFilter)
  }, [fetchPlans, statusFilter, priorityFilter, assetFilter, ownerFilter])

  const grouped = groupPlans(plans)
  const totalCount = plans.length
  const activeCount = grouped.open.length + grouped.in_progress.length

  const handleCardClick = useCallback(async (plan: ActionPlan) => {
    // Show dialog immediately with plan data, then fetch updates
    setSelectedPlan({ ...plan, updates: [] } as ActionPlanWithUpdates)

    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()
      if (!session?.access_token) return

      const response = await fetch(`${API_BASE_URL}/api/v1/action-plans/${plan.id}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      })

      if (response.ok) {
        const data = await response.json()
        if (mountedRef.current) {
          setSelectedPlan(prev => prev?.id === plan.id ? { ...prev, updates: data.updates || [] } : prev)
        }
      }
    } catch {
      // Silently fail — updates just won't load
    }
  }, [])

  const handleDetailClose = () => {
    setSelectedPlan(null)
  }

  const handleStatusChange = () => {
    setSelectedPlan(null)
    refetch()
  }

  // Initial loading state - skeleton only
  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <DashboardSkeleton />
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold">Action Plans</h1>
        </div>
        <div className="flex flex-col items-center justify-center py-12 space-y-4">
          <AlertCircle className="w-10 h-10 text-warning-amber" />
          <p className="text-sm text-muted-foreground">{error}</p>
          <Button variant="outline" onClick={refetch} size="sm">
            <RefreshCw className="w-4 h-4 mr-1" />
            Try Again
          </Button>
        </div>
      </div>
    )
  }

  // Empty state
  if (totalCount === 0) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold">Action Plans</h1>
        </div>
        <div className="flex flex-col items-center justify-center py-12 space-y-3">
          <ClipboardList className="w-10 h-10 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">
            No action plans found. Create action plans from follow-up investigations.
          </p>
        </div>
      </div>
    )
  }

  // Data loaded with plans
  return (
    <div className="p-6 space-y-6">
      {/* Page Header with active count badge */}
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-semibold">Action Plans</h1>
        <Badge variant="info">{activeCount}</Badge>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap gap-3">
        <div>
          <label htmlFor="filter-status" className="sr-only">Status</label>
          <select
            id="filter-status"
            aria-label="Status"
            value={statusFilter}
            onChange={(e) => updateFilter('status', e.target.value)}
            className="flex h-9 rounded-md border border-input bg-background px-3 py-1 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <option value="all">All Statuses</option>
            <option value="open">Open</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="verified">Verified</option>
          </select>
        </div>
        <div>
          <label htmlFor="filter-priority" className="sr-only">Priority</label>
          <select
            id="filter-priority"
            aria-label="Priority"
            value={priorityFilter}
            onChange={(e) => updateFilter('priority', e.target.value)}
            className="flex h-9 rounded-md border border-input bg-background px-3 py-1 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <option value="all">All Priorities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
        <div>
          <label htmlFor="filter-asset" className="sr-only">Asset</label>
          <input
            id="filter-asset"
            aria-label="Asset"
            placeholder="Filter by asset..."
            value={assetFilter === 'all' ? '' : assetFilter}
            onChange={(e) => updateFilter('asset_id', e.target.value || 'all')}
            className="flex h-9 rounded-md border border-input bg-background px-3 py-1 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />
        </div>
        <div>
          <label htmlFor="filter-owner" className="sr-only">Owner</label>
          <input
            id="filter-owner"
            aria-label="Owner"
            placeholder="Filter by owner..."
            value={ownerFilter === 'all' ? '' : ownerFilter}
            onChange={(e) => updateFilter('owner_id', e.target.value || 'all')}
            className="flex h-9 rounded-md border border-input bg-background px-3 py-1 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />
        </div>
      </div>

      {/* Grouped Plans */}
      <div className="space-y-6">
        {STATUS_SECTIONS.map(({ key, label }) => {
          const sectionPlans = grouped[key]
          if (sectionPlans.length === 0) return null

          return (
            <div key={key}>
              <h2 className="text-lg font-medium mb-3">
                {label} ({sectionPlans.length})
              </h2>
              <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
                {sectionPlans.map((plan) => (
                  <ActionPlanCard
                    key={plan.id}
                    plan={plan}
                    onClick={handleCardClick}
                    hideStatusBadge
                  />
                ))}
              </div>
            </div>
          )
        })}
      </div>

      {/* Detail Dialog */}
      {selectedPlan && (
        <ActionPlanDetail
          plan={selectedPlan}
          open={!!selectedPlan}
          onClose={handleDetailClose}
          onStatusChange={handleStatusChange}
        />
      )}
    </div>
  )
}
