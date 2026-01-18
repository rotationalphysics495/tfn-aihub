/**
 * Audit Log Filters Component (Story 9.15, Task 7)
 *
 * Filter controls for the audit log viewer.
 *
 * AC#2: Filters available - date range, action type, target user
 *
 * References:
 * - [Source: architecture/voice-briefing.md#Admin UI Architecture]
 */
'use client'

import { useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { X } from 'lucide-react'

// Action types for the dropdown filter
const ACTION_TYPES = [
  { value: 'role_change', label: 'Role Change' },
  { value: 'assignment_create', label: 'Assignment Created' },
  { value: 'assignment_update', label: 'Assignment Updated' },
  { value: 'assignment_delete', label: 'Assignment Deleted' },
  { value: 'batch_assignment', label: 'Batch Assignment' },
  { value: 'user_create', label: 'User Created' },
  { value: 'user_update', label: 'User Updated' },
  { value: 'preference_update', label: 'Preference Updated' },
]

export interface AuditLogFiltersState {
  startDate?: string
  endDate?: string
  actionType?: string
  targetUserId?: string
}

interface AuditLogFiltersProps {
  filters: AuditLogFiltersState
  onFiltersChange: (filters: AuditLogFiltersState) => void
  onClear: () => void
}

export function AuditLogFilters({
  filters,
  onFiltersChange,
  onClear,
}: AuditLogFiltersProps) {
  // Check if any filters are active
  const hasActiveFilters = !!(
    filters.startDate ||
    filters.endDate ||
    filters.actionType ||
    filters.targetUserId
  )

  // Handle individual filter changes
  const handleStartDateChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      onFiltersChange({
        ...filters,
        startDate: e.target.value || undefined,
      })
    },
    [filters, onFiltersChange]
  )

  const handleEndDateChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      onFiltersChange({
        ...filters,
        endDate: e.target.value || undefined,
      })
    },
    [filters, onFiltersChange]
  )

  const handleActionTypeChange = useCallback(
    (value: string) => {
      onFiltersChange({
        ...filters,
        actionType: value === 'all' ? undefined : value,
      })
    },
    [filters, onFiltersChange]
  )

  const handleTargetUserChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      onFiltersChange({
        ...filters,
        targetUserId: e.target.value || undefined,
      })
    },
    [filters, onFiltersChange]
  )

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Start Date Filter */}
        <div className="space-y-2">
          <Label htmlFor="start-date" className="text-sm font-medium">
            Start Date
          </Label>
          <Input
            id="start-date"
            type="datetime-local"
            value={filters.startDate || ''}
            onChange={handleStartDateChange}
            className="w-full"
          />
        </div>

        {/* End Date Filter */}
        <div className="space-y-2">
          <Label htmlFor="end-date" className="text-sm font-medium">
            End Date
          </Label>
          <Input
            id="end-date"
            type="datetime-local"
            value={filters.endDate || ''}
            onChange={handleEndDateChange}
            className="w-full"
          />
        </div>

        {/* Action Type Filter */}
        <div className="space-y-2">
          <Label htmlFor="action-type" className="text-sm font-medium">
            Action Type
          </Label>
          <Select
            value={filters.actionType || 'all'}
            onValueChange={handleActionTypeChange}
          >
            <SelectTrigger id="action-type" className="w-full">
              <SelectValue placeholder="All Actions" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Actions</SelectItem>
              {ACTION_TYPES.map((type) => (
                <SelectItem key={type.value} value={type.value}>
                  {type.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Target User Filter */}
        <div className="space-y-2">
          <Label htmlFor="target-user" className="text-sm font-medium">
            Target User ID
          </Label>
          <Input
            id="target-user"
            type="text"
            placeholder="Enter user ID"
            value={filters.targetUserId || ''}
            onChange={handleTargetUserChange}
            className="w-full"
          />
        </div>
      </div>

      {/* Clear Filters Button */}
      {hasActiveFilters && (
        <div className="flex justify-end">
          <Button
            variant="ghost"
            size="sm"
            onClick={onClear}
            className="text-slate-500 hover:text-slate-700"
          >
            <X className="w-4 h-4 mr-1" />
            Clear Filters
          </Button>
        </div>
      )}
    </div>
  )
}
