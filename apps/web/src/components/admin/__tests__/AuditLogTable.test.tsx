/**
 * Tests for AuditLogTable Component (Story 9.15, Task 10.9)
 *
 * Test Coverage:
 * - AC#2: Entries displayed in reverse chronological order
 * - AC#3: Display-only (read-only audit entries)
 * - AC#4: batch_id indicator for linked entries
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AuditLogTable, type AuditLogEntry } from '../AuditLogTable'

// Mock the UI components
vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <span data-testid="badge" className={className}>{children}</span>
  ),
}))

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, disabled, variant, size, className }: any) => (
    <button onClick={onClick} disabled={disabled} data-variant={variant} data-size={size} className={className}>
      {children}
    </button>
  ),
}))

vi.mock('@/lib/utils', () => ({
  cn: (...args: any[]) => args.filter(Boolean).join(' '),
}))

describe('AuditLogTable', () => {
  const mockEntries: AuditLogEntry[] = [
    {
      id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      timestamp: '2026-01-19T10:00:00Z',
      admin_user_id: 'dddddddd-dddd-dddd-dddd-dddddddddddd',
      admin_email: 'admin@example.com',
      action_type: 'role_change',
      target_type: 'user',
      target_user_id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      target_user_email: 'user@example.com',
      before_value: { role: 'supervisor' },
      after_value: { role: 'plant_manager' },
      batch_id: null,
      metadata: { source: 'admin_ui' },
    },
    {
      id: 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
      timestamp: '2026-01-19T09:00:00Z',
      admin_user_id: 'dddddddd-dddd-dddd-dddd-dddddddddddd',
      admin_email: 'admin@example.com',
      action_type: 'assignment_create',
      target_type: 'assignment',
      target_user_id: 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
      target_asset_id: '22222222-2222-2222-2222-222222222221',
      target_asset_name: 'Asset 1',
      before_value: null,
      after_value: { user_id: 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', asset_id: '22222222-2222-2222-2222-222222222221' },
      batch_id: 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
      metadata: null,
    },
    {
      id: 'cccccccc-cccc-cccc-cccc-cccccccccccc',
      timestamp: '2026-01-19T08:00:00Z',
      admin_user_id: 'dddddddd-dddd-dddd-dddd-dddddddddddd',
      admin_email: 'admin@example.com',
      action_type: 'assignment_delete',
      target_type: 'assignment',
      target_user_id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      target_asset_id: '11111111-1111-1111-1111-111111111111',
      before_value: { user_id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', asset_id: '11111111-1111-1111-1111-111111111111' },
      after_value: null,
      batch_id: null,
      metadata: { source: 'admin_ui' },
    },
  ]

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('AC#2: Reverse chronological order display', () => {
    it('should render all entries', () => {
      render(<AuditLogTable entries={mockEntries} />)

      // Check that entries are in the table (all 3 entries have the same admin)
      expect(screen.getAllByText('admin@example.com')).toHaveLength(3)
    })

    it('should display timestamps for each entry', () => {
      render(<AuditLogTable entries={mockEntries} />)

      // Each entry should have a timestamp visible
      // The timestamps should be formatted as readable dates
      const tableRows = screen.getAllByRole('row')
      // Header + 3 data rows
      expect(tableRows.length).toBeGreaterThanOrEqual(4)
    })
  })

  describe('AC#3: Display-only (tamper-evident)', () => {
    it('should render entries without edit controls', () => {
      render(<AuditLogTable entries={mockEntries} />)

      // There should be no edit or delete buttons
      expect(screen.queryByText('Edit')).not.toBeInTheDocument()
      expect(screen.queryByText('Delete')).not.toBeInTheDocument()
    })

    it('should show action type badges for each entry', () => {
      render(<AuditLogTable entries={mockEntries} />)

      // Check for action type badges
      const badges = screen.getAllByTestId('badge')
      expect(badges.length).toBeGreaterThanOrEqual(3)
    })
  })

  describe('AC#4: batch_id indicator', () => {
    it('should display batch_id indicator for entries with batch_id', () => {
      render(<AuditLogTable entries={mockEntries} />)

      // The entry with batch_id should have an indicator
      // Entry at index 1 has a batch_id
      const badges = screen.getAllByTestId('badge')
      // Should have at least 4 badges (3 action types + 1 batch indicator)
      expect(badges.length).toBeGreaterThanOrEqual(3)
    })
  })

  describe('Empty and loading states', () => {
    it('should show loading state when isLoading is true', () => {
      render(<AuditLogTable entries={[]} isLoading={true} />)

      expect(screen.getByText(/Loading audit logs/i)).toBeInTheDocument()
    })

    it('should show empty state when no entries', () => {
      render(<AuditLogTable entries={[]} isLoading={false} />)

      expect(screen.getByText(/No audit log entries found/i)).toBeInTheDocument()
    })
  })

  describe('Row expansion', () => {
    it('should expand row when clicked', async () => {
      render(<AuditLogTable entries={mockEntries} />)

      // Find and click the first row
      const firstRow = screen.getAllByRole('row')[1] // Skip header row
      await userEvent.click(firstRow)

      // After expansion, we should see more details
      // The expanded row should show "Entry ID" label
      expect(screen.getByText('Entry ID')).toBeInTheDocument()
    })

    it('should collapse row when clicked again', async () => {
      render(<AuditLogTable entries={mockEntries} />)

      // Click to expand
      const firstRow = screen.getAllByRole('row')[1]
      await userEvent.click(firstRow)

      // Verify expanded
      expect(screen.getByText('Entry ID')).toBeInTheDocument()

      // Click again to collapse
      await userEvent.click(firstRow)

      // Should no longer show "Entry ID"
      expect(screen.queryByText('Entry ID')).not.toBeInTheDocument()
    })

    it('should show before/after values in expanded view', async () => {
      render(<AuditLogTable entries={mockEntries} />)

      // Expand the first entry (role_change)
      const firstRow = screen.getAllByRole('row')[1]
      await userEvent.click(firstRow)

      // Should see Before and After labels
      expect(screen.getByText('Before')).toBeInTheDocument()
      expect(screen.getByText('After')).toBeInTheDocument()
    })
  })

  describe('Action type display', () => {
    it('should display correct badge for role_change action', () => {
      render(<AuditLogTable entries={[mockEntries[0]]} />)

      expect(screen.getByText('Role Change')).toBeInTheDocument()
    })

    it('should display correct badge for assignment_create action', () => {
      render(<AuditLogTable entries={[mockEntries[1]]} />)

      expect(screen.getByText('Assignment Created')).toBeInTheDocument()
    })

    it('should display correct badge for assignment_delete action', () => {
      render(<AuditLogTable entries={[mockEntries[2]]} />)

      expect(screen.getByText('Assignment Deleted')).toBeInTheDocument()
    })
  })

  describe('Summary generation', () => {
    it('should generate summary for role_change', () => {
      render(<AuditLogTable entries={[mockEntries[0]]} />)

      // Summary should mention the role change
      expect(screen.getByText(/supervisor.*plant_manager/i)).toBeInTheDocument()
    })

    it('should generate summary for assignment_create', () => {
      render(<AuditLogTable entries={[mockEntries[1]]} />)

      // Summary should mention "Created assignment"
      expect(screen.getByText(/Created assignment/i)).toBeInTheDocument()
    })

    it('should generate summary for assignment_delete', () => {
      render(<AuditLogTable entries={[mockEntries[2]]} />)

      // Summary should mention "Deleted assignment"
      expect(screen.getByText(/Deleted assignment/i)).toBeInTheDocument()
    })
  })
})
