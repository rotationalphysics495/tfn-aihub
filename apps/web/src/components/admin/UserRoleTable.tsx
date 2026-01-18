/**
 * User Role Table Component (Story 9.14, Task 9)
 *
 * Displays a table of users with their roles and inline role editing.
 *
 * AC#1: Render user list with role badges
 * AC#2: Add inline role change dropdown
 * AC#3: Display loading/error states
 *
 * References:
 * - [Source: architecture/voice-briefing.md#Admin UI Architecture]
 */
'use client'

import { useState, useCallback } from 'react'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Loader2, Shield, User, UserCog, AlertTriangle } from 'lucide-react'

export type UserRole = 'plant_manager' | 'supervisor' | 'admin'

export interface UserWithRole {
  user_id: string
  email: string | null
  role: UserRole
  created_at?: string | null
  updated_at?: string | null
}

interface UserRoleTableProps {
  users: UserWithRole[]
  onRoleChange: (userId: string, newRole: UserRole) => Promise<void>
  isLoading?: boolean
  disabled?: boolean
}

// Role display configuration
const ROLE_CONFIG: Record<UserRole, { label: string; icon: React.ReactNode; badgeClass: string }> = {
  admin: {
    label: 'Admin',
    icon: <Shield className="w-3 h-3" />,
    badgeClass: 'bg-red-100 text-red-700 border-red-200',
  },
  plant_manager: {
    label: 'Plant Manager',
    icon: <UserCog className="w-3 h-3" />,
    badgeClass: 'bg-blue-100 text-blue-700 border-blue-200',
  },
  supervisor: {
    label: 'Supervisor',
    icon: <User className="w-3 h-3" />,
    badgeClass: 'bg-green-100 text-green-700 border-green-200',
  },
}

export function UserRoleTable({
  users,
  onRoleChange,
  isLoading = false,
  disabled = false,
}: UserRoleTableProps) {
  // Track which user is being edited
  const [editingUserId, setEditingUserId] = useState<string | null>(null)
  const [pendingRole, setPendingRole] = useState<UserRole | null>(null)
  const [savingUserId, setSavingUserId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Confirmation dialog state
  const [confirmDialog, setConfirmDialog] = useState<{
    open: boolean
    userId: string
    currentRole: UserRole
    newRole: UserRole
    userEmail: string | null
  } | null>(null)

  // Handle role selection change
  const handleRoleSelect = useCallback(
    (userId: string, currentRole: UserRole, userEmail: string | null, newRole: UserRole) => {
      if (newRole === currentRole) {
        setEditingUserId(null)
        setPendingRole(null)
        return
      }

      // Show confirmation dialog
      setConfirmDialog({
        open: true,
        userId,
        currentRole,
        newRole,
        userEmail,
      })
    },
    []
  )

  // Handle confirmation
  const handleConfirmRoleChange = useCallback(async () => {
    if (!confirmDialog) return

    const { userId, newRole } = confirmDialog

    setConfirmDialog(null)
    setSavingUserId(userId)
    setError(null)

    try {
      await onRoleChange(userId, newRole)
      setEditingUserId(null)
      setPendingRole(null)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update role'
      setError(errorMessage)
    } finally {
      setSavingUserId(null)
    }
  }, [confirmDialog, onRoleChange])

  // Handle cancel
  const handleCancelDialog = useCallback(() => {
    setConfirmDialog(null)
    setEditingUserId(null)
    setPendingRole(null)
  }, [])

  // Start editing a user's role
  const startEditing = useCallback((userId: string, currentRole: UserRole) => {
    setEditingUserId(userId)
    setPendingRole(currentRole)
    setError(null)
  }, [])

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 animate-spin text-slate-400 mr-2" />
        <span className="text-slate-500">Loading users...</span>
      </div>
    )
  }

  // Empty state
  if (users.length === 0) {
    return (
      <div className="text-center py-12 text-slate-500">
        No users found. Users will appear here once they sign up.
      </div>
    )
  }

  return (
    <>
      {/* Error banner */}
      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
          <button
            onClick={() => setError(null)}
            className="ml-auto text-red-500 hover:text-red-700"
          >
            &times;
          </button>
        </div>
      )}

      <div className="overflow-auto border rounded-lg bg-white">
        <table className="min-w-full border-collapse">
          <thead>
            <tr className="bg-slate-100">
              <th className="border-b px-4 py-3 text-left font-medium text-slate-700">
                User
              </th>
              <th className="border-b px-4 py-3 text-left font-medium text-slate-700">
                Current Role
              </th>
              <th className="border-b px-4 py-3 text-left font-medium text-slate-700">
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => {
              const isEditing = editingUserId === user.user_id
              const isSaving = savingUserId === user.user_id
              const roleConfig = ROLE_CONFIG[user.role]

              return (
                <tr
                  key={user.user_id}
                  className={cn(
                    'hover:bg-slate-50 transition-colors',
                    isSaving && 'opacity-50'
                  )}
                >
                  {/* User Info */}
                  <td className="border-b px-4 py-3">
                    <div className="font-medium text-slate-900">
                      {user.email || 'Unknown'}
                    </div>
                    <div className="text-xs text-slate-500 font-mono">
                      {user.user_id.slice(0, 8)}...
                    </div>
                  </td>

                  {/* Current Role Badge */}
                  <td className="border-b px-4 py-3">
                    <Badge
                      variant="outline"
                      className={cn(
                        'flex items-center gap-1 w-fit',
                        roleConfig.badgeClass
                      )}
                    >
                      {roleConfig.icon}
                      {roleConfig.label}
                    </Badge>
                  </td>

                  {/* Actions */}
                  <td className="border-b px-4 py-3">
                    {isEditing ? (
                      <div className="flex items-center gap-2">
                        <Select
                          value={pendingRole || user.role}
                          onValueChange={(value) =>
                            handleRoleSelect(
                              user.user_id,
                              user.role,
                              user.email,
                              value as UserRole
                            )
                          }
                          disabled={isSaving || disabled}
                        >
                          <SelectTrigger className="w-40">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="supervisor">Supervisor</SelectItem>
                            <SelectItem value="plant_manager">Plant Manager</SelectItem>
                            <SelectItem value="admin">Admin</SelectItem>
                          </SelectContent>
                        </Select>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setEditingUserId(null)
                            setPendingRole(null)
                          }}
                          disabled={isSaving}
                        >
                          Cancel
                        </Button>
                      </div>
                    ) : (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => startEditing(user.user_id, user.role)}
                        disabled={isSaving || disabled}
                      >
                        {isSaving ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin mr-1" />
                            Saving...
                          </>
                        ) : (
                          'Change Role'
                        )}
                      </Button>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Confirmation Dialog */}
      <AlertDialog
        open={confirmDialog?.open ?? false}
        onOpenChange={(open) => {
          if (!open) handleCancelDialog()
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Confirm Role Change</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to change the role for{' '}
              <strong>{confirmDialog?.userEmail || 'this user'}</strong> from{' '}
              <Badge
                variant="outline"
                className={cn(
                  'mx-1',
                  confirmDialog && ROLE_CONFIG[confirmDialog.currentRole].badgeClass
                )}
              >
                {confirmDialog && ROLE_CONFIG[confirmDialog.currentRole].label}
              </Badge>{' '}
              to{' '}
              <Badge
                variant="outline"
                className={cn(
                  'mx-1',
                  confirmDialog && ROLE_CONFIG[confirmDialog.newRole].badgeClass
                )}
              >
                {confirmDialog && ROLE_CONFIG[confirmDialog.newRole].label}
              </Badge>
              ?
              <br />
              <br />
              This change will take effect immediately.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={handleCancelDialog}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmRoleChange}>
              Confirm Change
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
