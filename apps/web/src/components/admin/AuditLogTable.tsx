/**
 * Audit Log Table Component (Story 9.15, Task 8)
 *
 * Displays audit log entries in a table with expandable rows.
 *
 * AC#2: Entries displayed in reverse chronological order
 * AC#3: Entries are tamper-evident (display-only)
 * AC#4: batch_id indicator for linked entries
 *
 * References:
 * - [Source: architecture/voice-briefing.md#Admin UI Architecture]
 */
'use client'

import React, { useState, useCallback } from 'react'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  ChevronDown,
  ChevronRight,
  Loader2,
  Link as LinkIcon,
  User,
  Shield,
  UserCog,
  ClipboardList,
  Settings,
} from 'lucide-react'

export interface AuditLogEntry {
  id: string
  timestamp: string
  admin_user_id: string
  admin_email?: string | null
  action_type: string
  target_type?: string | null
  target_id?: string | null
  target_user_id?: string | null
  target_user_email?: string | null
  target_asset_id?: string | null
  target_asset_name?: string | null
  before_value?: Record<string, unknown> | null
  after_value?: Record<string, unknown> | null
  batch_id?: string | null
  metadata?: Record<string, unknown> | null
}

interface AuditLogTableProps {
  entries: AuditLogEntry[]
  isLoading?: boolean
}

// Action type display configuration
const ACTION_TYPE_CONFIG: Record<
  string,
  { label: string; icon: React.ReactNode; badgeClass: string }
> = {
  role_change: {
    label: 'Role Change',
    icon: <Shield className="w-3 h-3" />,
    badgeClass: 'bg-purple-100 text-purple-700 border-purple-200',
  },
  assignment_create: {
    label: 'Assignment Created',
    icon: <ClipboardList className="w-3 h-3" />,
    badgeClass: 'bg-green-100 text-green-700 border-green-200',
  },
  assignment_update: {
    label: 'Assignment Updated',
    icon: <ClipboardList className="w-3 h-3" />,
    badgeClass: 'bg-blue-100 text-blue-700 border-blue-200',
  },
  assignment_delete: {
    label: 'Assignment Deleted',
    icon: <ClipboardList className="w-3 h-3" />,
    badgeClass: 'bg-red-100 text-red-700 border-red-200',
  },
  batch_assignment: {
    label: 'Batch Assignment',
    icon: <LinkIcon className="w-3 h-3" />,
    badgeClass: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  },
  user_create: {
    label: 'User Created',
    icon: <User className="w-3 h-3" />,
    badgeClass: 'bg-green-100 text-green-700 border-green-200',
  },
  user_update: {
    label: 'User Updated',
    icon: <UserCog className="w-3 h-3" />,
    badgeClass: 'bg-blue-100 text-blue-700 border-blue-200',
  },
  preference_update: {
    label: 'Preference Updated',
    icon: <Settings className="w-3 h-3" />,
    badgeClass: 'bg-slate-100 text-slate-700 border-slate-200',
  },
}

// Default config for unknown action types
const DEFAULT_CONFIG = {
  label: 'Unknown Action',
  icon: <Settings className="w-3 h-3" />,
  badgeClass: 'bg-slate-100 text-slate-700 border-slate-200',
}

// Format timestamp for display
function formatTimestamp(timestamp: string): string {
  try {
    const date = new Date(timestamp)
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  } catch {
    return timestamp
  }
}

// Generate summary text for an entry
function generateSummary(entry: AuditLogEntry): string {
  const { action_type, before_value, after_value, target_user_email, target_asset_name } = entry

  switch (action_type) {
    case 'role_change':
      const oldRole = before_value?.role || 'unknown'
      const newRole = after_value?.role || 'unknown'
      return `Changed role from ${oldRole} to ${newRole}${target_user_email ? ` for ${target_user_email}` : ''}`

    case 'assignment_create':
      return `Created assignment${target_asset_name ? ` for ${target_asset_name}` : ''}`

    case 'assignment_delete':
      return `Deleted assignment${target_asset_name ? ` for ${target_asset_name}` : ''}`

    case 'assignment_update':
      return `Updated assignment${target_asset_name ? ` for ${target_asset_name}` : ''}`

    case 'batch_assignment':
      const changeCount = after_value?.changes_applied || 'multiple'
      return `Batch operation: ${changeCount} changes applied`

    default:
      return `${action_type.replace(/_/g, ' ')}`
  }
}

// JSON Diff viewer component
function JsonDiff({
  before,
  after,
}: {
  before?: Record<string, unknown> | null
  after?: Record<string, unknown> | null
}) {
  return (
    <div className="grid grid-cols-2 gap-4">
      <div>
        <div className="text-xs font-medium text-slate-500 mb-1">Before</div>
        <pre className="bg-red-50 border border-red-100 rounded p-2 text-xs overflow-auto max-h-40">
          {before ? JSON.stringify(before, null, 2) : '(none)'}
        </pre>
      </div>
      <div>
        <div className="text-xs font-medium text-slate-500 mb-1">After</div>
        <pre className="bg-green-50 border border-green-100 rounded p-2 text-xs overflow-auto max-h-40">
          {after ? JSON.stringify(after, null, 2) : '(none)'}
        </pre>
      </div>
    </div>
  )
}

export function AuditLogTable({ entries, isLoading = false }: AuditLogTableProps) {
  // Track which rows are expanded
  const [expandedId, setExpandedId] = useState<string | null>(null)

  // Toggle row expansion
  const toggleExpand = useCallback((id: string) => {
    setExpandedId((prev) => (prev === id ? null : id))
  }, [])

  // Loading state
  if (isLoading && entries.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 animate-spin text-slate-400 mr-2" />
        <span className="text-slate-500">Loading audit logs...</span>
      </div>
    )
  }

  // Empty state
  if (entries.length === 0) {
    return (
      <div className="text-center py-12 text-slate-500">
        No audit log entries found. Actions will appear here once admin changes are made.
      </div>
    )
  }

  return (
    <div className="overflow-auto border rounded-lg bg-white">
      <table className="min-w-full border-collapse">
        <thead>
          <tr className="bg-slate-100">
            <th className="border-b px-4 py-3 text-left font-medium text-slate-700 w-8"></th>
            <th className="border-b px-4 py-3 text-left font-medium text-slate-700">
              Timestamp
            </th>
            <th className="border-b px-4 py-3 text-left font-medium text-slate-700">
              Admin
            </th>
            <th className="border-b px-4 py-3 text-left font-medium text-slate-700">
              Action
            </th>
            <th className="border-b px-4 py-3 text-left font-medium text-slate-700">
              Summary
            </th>
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) => {
            const isExpanded = expandedId === entry.id
            const config = ACTION_TYPE_CONFIG[entry.action_type] || DEFAULT_CONFIG
            const hasBatchId = !!entry.batch_id

            return (
              <React.Fragment key={entry.id}>
                <tr
                  className={cn(
                    'hover:bg-slate-50 transition-colors cursor-pointer',
                    isExpanded && 'bg-slate-50'
                  )}
                  onClick={() => toggleExpand(entry.id)}
                >
                  {/* Expand Icon */}
                  <td className="border-b px-4 py-3">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="p-0 h-6 w-6"
                      onClick={(e) => {
                        e.stopPropagation()
                        toggleExpand(entry.id)
                      }}
                    >
                      {isExpanded ? (
                        <ChevronDown className="w-4 h-4" />
                      ) : (
                        <ChevronRight className="w-4 h-4" />
                      )}
                    </Button>
                  </td>

                  {/* Timestamp */}
                  <td className="border-b px-4 py-3">
                    <div className="text-sm text-slate-900">
                      {formatTimestamp(entry.timestamp)}
                    </div>
                  </td>

                  {/* Admin */}
                  <td className="border-b px-4 py-3">
                    <div className="text-sm text-slate-900">
                      {entry.admin_email || 'Unknown'}
                    </div>
                    <div className="text-xs text-slate-500 font-mono">
                      {entry.admin_user_id.slice(0, 8)}...
                    </div>
                  </td>

                  {/* Action Type Badge */}
                  <td className="border-b px-4 py-3">
                    <div className="flex items-center gap-2">
                      <Badge
                        variant="outline"
                        className={cn('flex items-center gap-1 w-fit', config.badgeClass)}
                      >
                        {config.icon}
                        {config.label}
                      </Badge>
                      {/* Batch ID indicator */}
                      {hasBatchId && (
                        <Badge
                          variant="outline"
                          className="bg-yellow-50 text-yellow-700 border-yellow-200"
                          title={`Batch ID: ${entry.batch_id}`}
                        >
                          <LinkIcon className="w-3 h-3" />
                        </Badge>
                      )}
                    </div>
                  </td>

                  {/* Summary */}
                  <td className="border-b px-4 py-3">
                    <div className="text-sm text-slate-700">
                      {generateSummary(entry)}
                    </div>
                  </td>
                </tr>

                {/* Expanded Row Detail */}
                {isExpanded && (
                  <tr key={`${entry.id}-detail`}>
                    <td colSpan={5} className="border-b bg-slate-50 px-4 py-4">
                      <div className="space-y-4">
                        {/* Entry Details */}
                        <div className="grid grid-cols-3 gap-4 text-sm">
                          <div>
                            <div className="text-xs font-medium text-slate-500 mb-1">
                              Entry ID
                            </div>
                            <div className="font-mono text-slate-700">{entry.id}</div>
                          </div>
                          {entry.target_user_id && (
                            <div>
                              <div className="text-xs font-medium text-slate-500 mb-1">
                                Target User
                              </div>
                              <div className="font-mono text-slate-700">
                                {entry.target_user_email || entry.target_user_id}
                              </div>
                            </div>
                          )}
                          {entry.target_asset_id && (
                            <div>
                              <div className="text-xs font-medium text-slate-500 mb-1">
                                Target Asset
                              </div>
                              <div className="text-slate-700">
                                {entry.target_asset_name || entry.target_asset_id}
                              </div>
                            </div>
                          )}
                          {entry.batch_id && (
                            <div>
                              <div className="text-xs font-medium text-slate-500 mb-1">
                                Batch ID
                              </div>
                              <div className="font-mono text-slate-700">
                                {entry.batch_id}
                              </div>
                            </div>
                          )}
                        </div>

                        {/* Before/After Values */}
                        {(entry.before_value || entry.after_value) && (
                          <div>
                            <div className="text-xs font-medium text-slate-500 mb-2">
                              Changes
                            </div>
                            <JsonDiff
                              before={entry.before_value}
                              after={entry.after_value}
                            />
                          </div>
                        )}

                        {/* Metadata */}
                        {entry.metadata && Object.keys(entry.metadata).length > 0 && (
                          <div>
                            <div className="text-xs font-medium text-slate-500 mb-1">
                              Metadata
                            </div>
                            <pre className="bg-slate-100 border rounded p-2 text-xs overflow-auto max-h-20">
                              {JSON.stringify(entry.metadata, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
