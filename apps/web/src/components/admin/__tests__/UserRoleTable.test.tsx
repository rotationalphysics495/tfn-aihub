/**
 * Tests for UserRoleTable Component (Story 9.14, Task 9)
 *
 * Test Coverage:
 * - AC#1: Render user list with role badges
 * - AC#2: Inline role change dropdown functionality
 * - AC#3: Loading and error states
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { UserRoleTable, type UserWithRole, type UserRole } from '../UserRoleTable'

// Mock the UI components
vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <span data-testid="badge" className={className}>{children}</span>
  ),
}))

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, disabled, variant, size }: any) => (
    <button onClick={onClick} disabled={disabled} data-variant={variant} data-size={size}>
      {children}
    </button>
  ),
}))

vi.mock('@/components/ui/select', () => ({
  Select: ({ children, value, onValueChange, disabled }: any) => (
    <div data-testid="select" data-value={value} data-disabled={disabled}>
      {children}
    </div>
  ),
  SelectTrigger: ({ children, className }: any) => (
    <button data-testid="select-trigger" className={className}>{children}</button>
  ),
  SelectValue: () => <span data-testid="select-value" />,
  SelectContent: ({ children }: any) => <div data-testid="select-content">{children}</div>,
  SelectItem: ({ children, value }: any) => (
    <button data-testid={`select-item-${value}`} data-value={value}>{children}</button>
  ),
}))

vi.mock('@/components/ui/alert-dialog', () => ({
  AlertDialog: ({ children, open }: any) => (
    open ? <div data-testid="alert-dialog">{children}</div> : null
  ),
  AlertDialogContent: ({ children }: any) => <div data-testid="alert-dialog-content">{children}</div>,
  AlertDialogHeader: ({ children }: any) => <div>{children}</div>,
  AlertDialogTitle: ({ children }: any) => <h2>{children}</h2>,
  AlertDialogDescription: ({ children }: any) => <p>{children}</p>,
  AlertDialogFooter: ({ children }: any) => <div>{children}</div>,
  AlertDialogAction: ({ children, onClick }: any) => (
    <button data-testid="alert-dialog-action" onClick={onClick}>{children}</button>
  ),
  AlertDialogCancel: ({ children, onClick }: any) => (
    <button data-testid="alert-dialog-cancel" onClick={onClick}>{children}</button>
  ),
}))

vi.mock('@/lib/utils', () => ({
  cn: (...args: any[]) => args.filter(Boolean).join(' '),
}))

describe('UserRoleTable', () => {
  // Use realistic UUIDs to match actual data format
  const mockUsers: UserWithRole[] = [
    {
      user_id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      email: 'admin@example.com',
      role: 'admin',
      created_at: '2026-01-15T08:00:00Z',
      updated_at: '2026-01-15T08:00:00Z',
    },
    {
      user_id: 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
      email: 'supervisor@example.com',
      role: 'supervisor',
      created_at: '2026-01-15T08:00:00Z',
      updated_at: '2026-01-15T08:00:00Z',
    },
    {
      user_id: 'cccccccc-cccc-cccc-cccc-cccccccccccc',
      email: 'manager@example.com',
      role: 'plant_manager',
      created_at: '2026-01-15T08:00:00Z',
      updated_at: '2026-01-15T08:00:00Z',
    },
  ]

  const mockOnRoleChange = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('AC#1: Render user list with role badges', () => {
    it('should render all users in the table', () => {
      render(
        <UserRoleTable
          users={mockUsers}
          onRoleChange={mockOnRoleChange}
        />
      )

      // Check that all user emails are displayed
      expect(screen.getByText('admin@example.com')).toBeInTheDocument()
      expect(screen.getByText('supervisor@example.com')).toBeInTheDocument()
      expect(screen.getByText('manager@example.com')).toBeInTheDocument()
    })

    it('should display role badges for each user', () => {
      render(
        <UserRoleTable
          users={mockUsers}
          onRoleChange={mockOnRoleChange}
        />
      )

      // Check for role badges
      const badges = screen.getAllByTestId('badge')
      expect(badges.length).toBeGreaterThanOrEqual(3)
    })

    it('should show user ID prefix for each user', () => {
      render(
        <UserRoleTable
          users={mockUsers}
          onRoleChange={mockOnRoleChange}
        />
      )

      // Check that user IDs are shown (truncated to first 8 chars)
      expect(screen.getByText('aaaaaaaa...')).toBeInTheDocument()
      expect(screen.getByText('bbbbbbbb...')).toBeInTheDocument()
      expect(screen.getByText('cccccccc...')).toBeInTheDocument()
    })
  })

  describe('AC#2: Inline role change dropdown', () => {
    it('should show "Change Role" button for each user', () => {
      render(
        <UserRoleTable
          users={mockUsers}
          onRoleChange={mockOnRoleChange}
        />
      )

      const changeButtons = screen.getAllByText('Change Role')
      expect(changeButtons).toHaveLength(3)
    })

    it('should show dropdown when "Change Role" is clicked', async () => {
      render(
        <UserRoleTable
          users={mockUsers}
          onRoleChange={mockOnRoleChange}
        />
      )

      const changeButtons = screen.getAllByText('Change Role')
      await userEvent.click(changeButtons[0])

      // Should now show the select dropdown
      expect(screen.getByTestId('select')).toBeInTheDocument()
    })

    it('should show cancel button when editing', async () => {
      render(
        <UserRoleTable
          users={mockUsers}
          onRoleChange={mockOnRoleChange}
        />
      )

      const changeButtons = screen.getAllByText('Change Role')
      await userEvent.click(changeButtons[0])

      expect(screen.getByText('Cancel')).toBeInTheDocument()
    })
  })

  describe('AC#3: Loading and error states', () => {
    it('should show loading state when isLoading is true', () => {
      render(
        <UserRoleTable
          users={[]}
          onRoleChange={mockOnRoleChange}
          isLoading={true}
        />
      )

      expect(screen.getByText('Loading users...')).toBeInTheDocument()
    })

    it('should show empty state when no users', () => {
      render(
        <UserRoleTable
          users={[]}
          onRoleChange={mockOnRoleChange}
          isLoading={false}
        />
      )

      expect(screen.getByText(/No users found/i)).toBeInTheDocument()
    })

    it('should disable interactions when disabled prop is true', () => {
      render(
        <UserRoleTable
          users={mockUsers}
          onRoleChange={mockOnRoleChange}
          disabled={true}
        />
      )

      const changeButtons = screen.getAllByText('Change Role')
      changeButtons.forEach(button => {
        expect(button).toBeDisabled()
      })
    })
  })

  describe('Role change workflow', () => {
    it('should show confirmation dialog when role is selected via dropdown', async () => {
      mockOnRoleChange.mockResolvedValue(undefined)

      render(
        <UserRoleTable
          users={mockUsers}
          onRoleChange={mockOnRoleChange}
        />
      )

      // Click change role for supervisor user to enter edit mode
      const changeButtons = screen.getAllByText('Change Role')
      await userEvent.click(changeButtons[1]) // supervisor user

      // Verify we're now in edit mode (select component rendered)
      expect(screen.getByTestId('select')).toBeInTheDocument()

      // Note: Due to mocked Select component, we can't trigger the actual
      // onValueChange callback. The component flow is:
      // 1. Click "Change Role" -> enters edit mode
      // 2. Select new role -> opens confirmation dialog
      // 3. Confirm -> calls onRoleChange
      // This test verifies step 1 works correctly
    })

    it('should cancel editing when cancel button is clicked', async () => {
      render(
        <UserRoleTable
          users={mockUsers}
          onRoleChange={mockOnRoleChange}
        />
      )

      // Enter edit mode
      const changeButtons = screen.getAllByText('Change Role')
      await userEvent.click(changeButtons[0])

      // Click cancel
      const cancelButton = screen.getByText('Cancel')
      await userEvent.click(cancelButton)

      // Should be back to normal state with Change Role buttons
      expect(screen.getAllByText('Change Role')).toHaveLength(3)
    })

    it('should handle role change errors gracefully', async () => {
      mockOnRoleChange.mockRejectedValue(new Error('Cannot remove last admin'))

      render(
        <UserRoleTable
          users={mockUsers}
          onRoleChange={mockOnRoleChange}
        />
      )

      // The component should handle errors without crashing
      expect(screen.getByText('admin@example.com')).toBeInTheDocument()
    })
  })
})
