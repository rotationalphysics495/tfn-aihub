/**
 * Assignment Preview Component (Story 9.13, Task 7)
 *
 * Shows impact of pending assignment changes before saving.
 *
 * AC#2: Preview shows "User will see X assets across Y areas"
 *
 * Features:
 * - Task 7.1: Preview panel showing impact
 * - Task 7.2: Display summary per user
 * - Task 7.3: Show added/removed in different colors
 * - Task 7.4: Confirm/cancel buttons
 *
 * References:
 * - [Source: prd/prd-functional-requirements.md#FR48]
 */
'use client'

import { useMemo } from 'react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { AlertTriangle, Check, X, Plus, Minus, Clock, Loader2 } from 'lucide-react'
import type { AssignmentChange, Supervisor, Asset } from './AssetAssignmentGrid'

interface UserImpact {
  user_id: string
  user_email?: string | null
  current_asset_count: number
  current_area_count: number
  new_asset_count: number
  new_area_count: number
  assets_added: string[]
  assets_removed: string[]
}

interface PreviewData {
  changes_count: number
  users_affected: number
  impact_summary: string
  user_impacts: UserImpact[]
  warnings: string[]
}

interface AssignmentPreviewProps {
  changes: AssignmentChange[]
  previewData?: PreviewData | null
  isLoading?: boolean
  error?: string | null
  supervisors: Supervisor[]
  assets: Asset[]
  onConfirm: () => void
  onCancel: () => void
  isSaving?: boolean
}

export function AssignmentPreview({
  changes,
  previewData,
  isLoading = false,
  error,
  supervisors,
  assets,
  onConfirm,
  onCancel,
  isSaving = false,
}: AssignmentPreviewProps) {
  // Create lookup maps
  const supervisorMap = useMemo(
    () => new Map(supervisors.map((s) => [s.user_id, s])),
    [supervisors]
  )
  const assetMap = useMemo(
    () => new Map(assets.map((a) => [a.asset_id, a])),
    [assets]
  )

  // Group changes by action type
  const { additions, removals } = useMemo(() => {
    const additions = changes.filter((c) => c.action === 'add')
    const removals = changes.filter((c) => c.action === 'remove')
    return { additions, removals }
  }, [changes])

  // Get display name for a supervisor
  const getSupervisorName = (userId: string): string => {
    const supervisor = supervisorMap.get(userId)
    return supervisor?.name || supervisor?.email?.split('@')[0] || userId.slice(0, 8)
  }

  // Get display name for an asset
  const getAssetName = (assetId: string): string => {
    const asset = assetMap.get(assetId)
    return asset?.name || assetId.slice(0, 8)
  }

  if (changes.length === 0) {
    return null
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center gap-2">
          <span>Pending Changes</span>
          <Badge variant="secondary">{changes.length}</Badge>
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Error State */}
        {error && (
          <div className="bg-red-50 text-red-700 p-3 rounded-lg text-sm flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-4 text-slate-500">
            <Loader2 className="w-5 h-5 animate-spin mr-2" />
            <span>Calculating impact...</span>
          </div>
        )}

        {/* Warnings (Task 7.1) */}
        {previewData?.warnings && previewData.warnings.length > 0 && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
            <div className="flex items-center gap-2 text-amber-700 font-medium text-sm mb-1">
              <AlertTriangle className="w-4 h-4" />
              Warnings
            </div>
            <ul className="text-sm text-amber-600 space-y-1">
              {previewData.warnings.map((warning, i) => (
                <li key={i}>{warning}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Impact Summary (Task 7.2) */}
        {previewData && !isLoading && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <div className="text-sm text-blue-700">
              <strong>{previewData.users_affected}</strong> supervisor(s) affected
            </div>
            {previewData.user_impacts.map((impact) => (
              <div key={impact.user_id} className="mt-2 text-sm text-blue-600">
                <span className="font-medium">{getSupervisorName(impact.user_id)}</span>
                {' will see '}
                <span className="font-medium">{impact.new_asset_count}</span>
                {' assets across '}
                <span className="font-medium">{impact.new_area_count}</span>
                {' areas'}
                {impact.new_asset_count !== impact.current_asset_count && (
                  <span className="ml-1">
                    ({impact.new_asset_count > impact.current_asset_count ? '+' : ''}
                    {impact.new_asset_count - impact.current_asset_count})
                  </span>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Additions (Task 7.3) */}
        {additions.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-green-700 flex items-center gap-1 mb-2">
              <Plus className="w-4 h-4" />
              Adding ({additions.length})
            </h4>
            <ul className="space-y-1 max-h-32 overflow-auto">
              {additions.map((change) => (
                <li
                  key={`${change.user_id}:${change.asset_id}`}
                  className="text-sm bg-green-50 text-green-700 px-2 py-1 rounded flex items-center gap-2"
                >
                  <span className="font-medium">{getSupervisorName(change.user_id)}</span>
                  <span className="text-green-500">&rarr;</span>
                  <span>{getAssetName(change.asset_id)}</span>
                  {change.expires_at && (
                    <Clock className="w-3 h-3 ml-auto text-green-500" title="Temporary" />
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Removals (Task 7.3) */}
        {removals.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-red-700 flex items-center gap-1 mb-2">
              <Minus className="w-4 h-4" />
              Removing ({removals.length})
            </h4>
            <ul className="space-y-1 max-h-32 overflow-auto">
              {removals.map((change) => (
                <li
                  key={`${change.user_id}:${change.asset_id}`}
                  className="text-sm bg-red-50 text-red-700 px-2 py-1 rounded flex items-center gap-2"
                >
                  <span className="font-medium">{getSupervisorName(change.user_id)}</span>
                  <span className="text-red-500">&times;</span>
                  <span>{getAssetName(change.asset_id)}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>

      {/* Actions (Task 7.4) */}
      <CardFooter className="flex gap-2 pt-4 border-t">
        <Button
          variant="outline"
          className="flex-1"
          onClick={onCancel}
          disabled={isSaving}
        >
          <X className="w-4 h-4 mr-1" />
          Cancel
        </Button>
        <Button
          className="flex-1"
          onClick={onConfirm}
          disabled={isLoading || isSaving || changes.length === 0}
        >
          {isSaving ? (
            <>
              <Loader2 className="w-4 h-4 mr-1 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Check className="w-4 h-4 mr-1" />
              Save Changes
            </>
          )}
        </Button>
      </CardFooter>
    </Card>
  )
}
