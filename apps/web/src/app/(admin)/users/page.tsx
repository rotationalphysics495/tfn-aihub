/**
 * User List Page (Story 9.14, Task 7)
 *
 * Admin page for viewing and managing user roles.
 *
 * AC#1: List of users with current roles displayed
 * AC#2: Admin changes role in dropdown, role is updated
 * AC#3: Cannot remove last admin
 * AC#4: New users get default Supervisor role
 *
 * References:
 * - [Source: architecture/voice-briefing.md#Admin UI Architecture]
 * - [Source: prd/prd-functional-requirements.md#FR47]
 */
'use client'

import { useState, useEffect, useCallback } from 'react'
import { UserRoleTable, type UserWithRole, type UserRole } from '@/components/admin/UserRoleTable'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { AlertTriangle, RefreshCw, Users, Shield, UserCog, User, CheckCircle, Loader2 } from 'lucide-react'

interface UserListResponse {
  users: UserWithRole[]
  total_count: number
}

interface RoleUpdateResponse {
  success: boolean
  user: UserWithRole
  message: string
}

export default function UsersPage() {
  // Data state
  const [users, setUsers] = useState<UserWithRole[]>([])
  const [totalCount, setTotalCount] = useState(0)

  // UI state
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  // Role counts for stats
  const [roleCounts, setRoleCounts] = useState({
    admin: 0,
    plant_manager: 0,
    supervisor: 0,
  })

  // Fetch all users
  const fetchUsers = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch('/api/v1/admin/users', {
        credentials: 'include',
      })

      if (!response.ok) {
        if (response.status === 403) {
          throw new Error('You do not have permission to access user management')
        }
        throw new Error(`Failed to fetch users: ${response.statusText}`)
      }

      const data: UserListResponse = await response.json()

      setUsers(data.users)
      setTotalCount(data.total_count)

      // Calculate role counts
      const counts = { admin: 0, plant_manager: 0, supervisor: 0 }
      data.users.forEach((user) => {
        if (user.role in counts) {
          counts[user.role as keyof typeof counts]++
        }
      })
      setRoleCounts(counts)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load users')
    } finally {
      setIsLoading(false)
    }
  }, [])

  // Initial fetch
  useEffect(() => {
    fetchUsers()
  }, [fetchUsers])

  // Handle role change
  const handleRoleChange = useCallback(async (userId: string, newRole: UserRole) => {
    const response = await fetch(`/api/v1/admin/users/${userId}/role`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ role: newRole }),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(errorData.detail || 'Failed to update role')
    }

    const data: RoleUpdateResponse = await response.json()

    // Update local state and recalculate role counts atomically
    setUsers((prev) => {
      const updatedUsers = prev.map((u) => (u.user_id === userId ? data.user : u))

      // Recalculate role counts from the updated users list
      const counts = { admin: 0, plant_manager: 0, supervisor: 0 }
      updatedUsers.forEach((user) => {
        if (user.role in counts) {
          counts[user.role as keyof typeof counts]++
        }
      })
      setRoleCounts(counts)

      return updatedUsers
    })

    // Show success message
    setSuccessMessage(data.message)
    setTimeout(() => setSuccessMessage(null), 3000)
  }, [])

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-6">
        <header>
          <h1 className="text-2xl font-bold text-slate-900">Role Management</h1>
          <p className="text-slate-500 mt-1">Loading...</p>
        </header>
        <Card>
          <CardContent className="py-12">
            <div className="flex items-center justify-center text-slate-500">
              <Loader2 className="w-6 h-6 animate-spin mr-2" />
              <span>Loading users...</span>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Error state
  if (error && users.length === 0) {
    return (
      <div className="space-y-6">
        <header>
          <h1 className="text-2xl font-bold text-slate-900">Role Management</h1>
        </header>
        <Card>
          <CardContent className="py-12">
            <div className="flex flex-col items-center justify-center text-center">
              <AlertTriangle className="w-12 h-12 text-red-500 mb-4" />
              <h2 className="text-lg font-medium text-slate-900 mb-2">Error Loading Users</h2>
              <p className="text-slate-500 mb-4">{error}</p>
              <Button onClick={fetchUsers}>
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
          <h1 className="text-2xl font-bold text-slate-900">Role Management</h1>
          <p className="text-slate-500 mt-1">
            Manage user roles and permissions across the platform
          </p>
        </div>
        <Button variant="outline" onClick={fetchUsers} disabled={isLoading}>
          <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </header>

      {/* Success Message */}
      {successMessage && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg flex items-center gap-2">
          <CheckCircle className="w-5 h-5" />
          <span>{successMessage}</span>
        </div>
      )}

      {/* Error Banner */}
      {error && users.length > 0 && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center gap-2">
          <AlertTriangle className="w-5 h-5" />
          <span>{error}</span>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-slate-100 rounded-lg">
                <Users className="w-5 h-5 text-slate-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{totalCount}</div>
                <div className="text-sm text-slate-500">Total Users</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-100 rounded-lg">
                <Shield className="w-5 h-5 text-red-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{roleCounts.admin}</div>
                <div className="text-sm text-slate-500">Admins</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <UserCog className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{roleCounts.plant_manager}</div>
                <div className="text-sm text-slate-500">Plant Managers</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <User className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{roleCounts.supervisor}</div>
                <div className="text-sm text-slate-500">Supervisors</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* User Table */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            Users
            <Badge variant="secondary" className="bg-slate-100">
              {users.length}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <UserRoleTable
            users={users}
            onRoleChange={handleRoleChange}
            isLoading={isLoading}
          />
        </CardContent>
      </Card>

      {/* Instructions */}
      <Card className="bg-slate-50 border-slate-200">
        <CardContent className="py-4">
          <h3 className="font-medium text-slate-700 mb-2">Role Permissions</h3>
          <ul className="text-sm text-slate-600 space-y-1">
            <li><strong>Admin:</strong> Full access to admin panel, user management, and all configuration</li>
            <li><strong>Plant Manager:</strong> View all assets, access reports, and manage supervisors</li>
            <li><strong>Supervisor:</strong> View assigned assets only, submit handoffs, access briefings</li>
          </ul>
          <p className="text-xs text-slate-500 mt-3">
            Note: New users are automatically assigned the Supervisor role. The system prevents removing the last admin.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
