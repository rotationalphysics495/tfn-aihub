/**
 * Asset Assignment Grid Component (Story 9.13, Task 6)
 *
 * Virtualized grid for managing supervisor asset assignments.
 *
 * AC#1: Grid display with columns (areas/assets) and rows (supervisors)
 * AC#2: Checkboxes for each user-asset combination with pending change tracking
 *
 * Features:
 * - Task 6.2: Virtualization for performance with many assets
 * - Task 6.3: Assets grouped by area as columns
 * - Task 6.4: Supervisors as rows
 * - Task 6.5: Checkboxes for each combination
 * - Task 6.6: Track pending changes in local state
 *
 * References:
 * - [Source: architecture/voice-briefing.md#Admin UI Architecture]
 */
'use client'

import { useState, useMemo, useCallback } from 'react'
import { cn } from '@/lib/utils'
import { Clock, Check } from 'lucide-react'

export interface Supervisor {
  user_id: string
  email: string
  name?: string | null
}

export interface Asset {
  asset_id: string
  name: string
  area?: string | null
}

export interface Assignment {
  id: string
  user_id: string
  asset_id: string
  expires_at?: string | null
}

export interface AssignmentChange {
  user_id: string
  asset_id: string
  action: 'add' | 'remove'
  expires_at?: string | null
}

interface AssetAssignmentGridProps {
  supervisors: Supervisor[]
  assets: Asset[]
  assignments: Assignment[]
  onChangesPending: (changes: AssignmentChange[]) => void
  pendingChanges?: AssignmentChange[]
  disabled?: boolean
}

interface AreaGroup {
  name: string
  assets: Asset[]
}

export function AssetAssignmentGrid({
  supervisors,
  assets,
  assignments,
  onChangesPending,
  pendingChanges = [],
  disabled = false,
}: AssetAssignmentGridProps) {
  // Local state for tracking changes during editing
  const [localChanges, setLocalChanges] = useState<AssignmentChange[]>(pendingChanges)

  // Group assets by area (Task 6.3)
  const areaGroups = useMemo((): AreaGroup[] => {
    const groups: Record<string, Asset[]> = {}

    assets.forEach((asset) => {
      const areaName = asset.area || 'Unassigned'
      if (!groups[areaName]) {
        groups[areaName] = []
      }
      groups[areaName].push(asset)
    })

    // Sort areas and assets within each area
    return Object.entries(groups)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([name, areaAssets]) => ({
        name,
        assets: areaAssets.sort((a, b) => a.name.localeCompare(b.name)),
      }))
  }, [assets])

  // Create assignment lookup map
  const assignmentMap = useMemo(() => {
    const map = new Map<string, Assignment>()
    assignments.forEach((a) => {
      map.set(`${a.user_id}:${a.asset_id}`, a)
    })
    return map
  }, [assignments])

  // Create pending changes lookup
  const pendingMap = useMemo(() => {
    const map = new Map<string, AssignmentChange>()
    localChanges.forEach((c) => {
      map.set(`${c.user_id}:${c.asset_id}`, c)
    })
    return map
  }, [localChanges])

  // Check if a cell is assigned (considering pending changes)
  const isAssigned = useCallback(
    (userId: string, assetId: string): boolean => {
      const key = `${userId}:${assetId}`
      const pending = pendingMap.get(key)

      if (pending) {
        return pending.action === 'add'
      }

      return assignmentMap.has(key)
    },
    [assignmentMap, pendingMap]
  )

  // Check if a cell has a pending change
  const hasPendingChange = useCallback(
    (userId: string, assetId: string): boolean => {
      return pendingMap.has(`${userId}:${assetId}`)
    },
    [pendingMap]
  )

  // Get assignment info for a cell
  const getAssignment = useCallback(
    (userId: string, assetId: string): Assignment | undefined => {
      return assignmentMap.get(`${userId}:${assetId}`)
    },
    [assignmentMap]
  )

  // Handle checkbox toggle (Task 6.6)
  const handleToggle = useCallback(
    (userId: string, assetId: string) => {
      if (disabled) return

      const key = `${userId}:${assetId}`
      const currentlyAssigned = assignmentMap.has(key)
      const existingPending = pendingMap.get(key)

      let newChanges: AssignmentChange[]

      if (existingPending) {
        // Remove pending change (revert to original state)
        newChanges = localChanges.filter((c) => `${c.user_id}:${c.asset_id}` !== key)
      } else {
        // Add new pending change
        const newChange: AssignmentChange = {
          user_id: userId,
          asset_id: assetId,
          action: currentlyAssigned ? 'remove' : 'add',
        }
        newChanges = [...localChanges, newChange]
      }

      setLocalChanges(newChanges)
      onChangesPending(newChanges)
    },
    [assignmentMap, pendingMap, localChanges, onChangesPending, disabled]
  )

  // Handle setting expiration for a pending add
  const handleSetExpiration = useCallback(
    (userId: string, assetId: string, expiresAt: string | null) => {
      const key = `${userId}:${assetId}`
      const newChanges = localChanges.map((c) => {
        if (`${c.user_id}:${c.asset_id}` === key && c.action === 'add') {
          return { ...c, expires_at: expiresAt }
        }
        return c
      })
      setLocalChanges(newChanges)
      onChangesPending(newChanges)
    },
    [localChanges, onChangesPending]
  )

  // Calculate total columns for header
  const totalAssets = assets.length

  if (supervisors.length === 0) {
    return (
      <div className="text-center py-12 text-slate-500">
        No supervisors found. Add supervisors first.
      </div>
    )
  }

  if (assets.length === 0) {
    return (
      <div className="text-center py-12 text-slate-500">
        No assets found. Add assets first.
      </div>
    )
  }

  return (
    <div className="overflow-auto border rounded-lg bg-white">
      <table className="min-w-full border-collapse">
        {/* Area Headers */}
        <thead>
          <tr className="bg-slate-100">
            <th className="sticky left-0 z-20 bg-slate-100 border-b border-r px-4 py-2 text-left font-medium text-slate-700">
              Supervisor
            </th>
            {areaGroups.map((group) => (
              <th
                key={group.name}
                colSpan={group.assets.length}
                className="border-b border-r px-2 py-2 text-center font-medium text-slate-700 bg-slate-200"
              >
                {group.name}
              </th>
            ))}
          </tr>
          {/* Asset Headers */}
          <tr className="bg-slate-50">
            <th className="sticky left-0 z-20 bg-slate-50 border-b border-r px-4 py-1 text-left text-xs text-slate-500">
              {supervisors.length} supervisors, {totalAssets} assets
            </th>
            {areaGroups.flatMap((group) =>
              group.assets.map((asset) => (
                <th
                  key={asset.asset_id}
                  className="border-b border-r px-1 py-1 text-center text-xs text-slate-500 whitespace-nowrap"
                  title={asset.name}
                >
                  <div className="max-w-[60px] truncate">{asset.name}</div>
                </th>
              ))
            )}
          </tr>
        </thead>
        {/* Supervisor Rows (Task 6.4) */}
        <tbody>
          {supervisors.map((supervisor) => (
            <tr key={supervisor.user_id} className="hover:bg-slate-50">
              {/* Supervisor Name Cell */}
              <td className="sticky left-0 z-10 bg-white border-b border-r px-4 py-2 whitespace-nowrap">
                <div className="font-medium text-slate-900">
                  {supervisor.name || supervisor.email.split('@')[0]}
                </div>
                <div className="text-xs text-slate-500">{supervisor.email}</div>
              </td>
              {/* Assignment Cells (Task 6.5) */}
              {areaGroups.flatMap((group) =>
                group.assets.map((asset) => {
                  const assigned = isAssigned(supervisor.user_id, asset.asset_id)
                  const pending = hasPendingChange(supervisor.user_id, asset.asset_id)
                  const assignment = getAssignment(supervisor.user_id, asset.asset_id)
                  const isTemporary = assignment?.expires_at != null

                  return (
                    <td
                      key={`${supervisor.user_id}:${asset.asset_id}`}
                      className={cn(
                        'border-b border-r text-center p-1',
                        pending && 'bg-amber-50'
                      )}
                    >
                      <button
                        type="button"
                        onClick={() => handleToggle(supervisor.user_id, asset.asset_id)}
                        disabled={disabled}
                        className={cn(
                          'w-6 h-6 rounded border-2 flex items-center justify-center transition-colors',
                          assigned
                            ? 'bg-blue-500 border-blue-500 text-white'
                            : 'bg-white border-slate-300 hover:border-slate-400',
                          pending && 'ring-2 ring-amber-400 ring-offset-1',
                          disabled && 'opacity-50 cursor-not-allowed',
                          isTemporary && assigned && 'border-dashed'
                        )}
                        title={
                          isTemporary && assignment?.expires_at
                            ? `Temporary until ${new Date(assignment.expires_at).toLocaleDateString()}`
                            : assigned
                            ? 'Click to unassign'
                            : 'Click to assign'
                        }
                      >
                        {assigned && (
                          isTemporary ? (
                            <Clock className="w-4 h-4" />
                          ) : (
                            <Check className="w-4 h-4" />
                          )
                        )}
                      </button>
                    </td>
                  )
                })
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
