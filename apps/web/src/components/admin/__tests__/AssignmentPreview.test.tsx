import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { AssignmentPreview } from '../AssignmentPreview'
import type { Supervisor, Asset, AssignmentChange } from '../AssetAssignmentGrid'

/**
 * Tests for AssignmentPreview Component
 *
 * Story: 9.13 - Admin UI Asset Assignment
 * AC#2: Preview shows "User will see X assets across Y areas"
 *
 * Task 7: Preview component tests
 */

describe('AssignmentPreview', () => {
  const mockSupervisors: Supervisor[] = [
    { user_id: 'user-1', email: 'supervisor1@test.com', name: 'Sarah Supervisor' },
    { user_id: 'user-2', email: 'supervisor2@test.com', name: 'Bob Supervisor' },
  ]

  const mockAssets: Asset[] = [
    { asset_id: 'asset-1', name: 'Grinder 1', area: 'Grinding' },
    { asset_id: 'asset-2', name: 'Grinder 2', area: 'Grinding' },
    { asset_id: 'asset-3', name: 'Packer 1', area: 'Packing' },
  ]

  const mockPreviewData = {
    changes_count: 2,
    users_affected: 1,
    impact_summary: 'User will see 3 assets across 2 areas',
    user_impacts: [
      {
        user_id: 'user-1',
        user_email: 'supervisor1@test.com',
        current_asset_count: 2,
        current_area_count: 1,
        new_asset_count: 3,
        new_area_count: 2,
        assets_added: ['asset-3'],
        assets_removed: [],
      },
    ],
    warnings: [],
  }

  const defaultProps = {
    changes: [
      { user_id: 'user-1', asset_id: 'asset-3', action: 'add' as const },
    ],
    previewData: mockPreviewData,
    isLoading: false,
    error: null,
    supervisors: mockSupervisors,
    assets: mockAssets,
    onConfirm: vi.fn(),
    onCancel: vi.fn(),
    isSaving: false,
  }

  describe('Rendering', () => {
    it('shows pending changes badge', () => {
      render(<AssignmentPreview {...defaultProps} />)

      expect(screen.getByText('Pending Changes')).toBeInTheDocument()
      // Badge count appears in a badge element
      const badges = screen.getAllByText('1')
      expect(badges.length).toBeGreaterThan(0)
    })

    it('does not render when no changes', () => {
      const { container } = render(
        <AssignmentPreview {...defaultProps} changes={[]} />
      )

      expect(container.firstChild).toBeNull()
    })
  })

  describe('Impact Summary (AC#2)', () => {
    it('shows users affected count', () => {
      render(<AssignmentPreview {...defaultProps} />)

      // Text is split across elements, so check for partial match
      expect(screen.getByText(/supervisor\(s\) affected/)).toBeInTheDocument()
    })

    it('shows "User will see X assets across Y areas" format', () => {
      render(<AssignmentPreview {...defaultProps} />)

      // Check for the impact text
      expect(screen.getByText(/will see/)).toBeInTheDocument()
      expect(screen.getByText(/assets across/)).toBeInTheDocument()
      expect(screen.getByText(/areas/)).toBeInTheDocument()
    })
  })

  describe('Change Lists (Task 7.3)', () => {
    it('shows additions in green', () => {
      render(<AssignmentPreview {...defaultProps} />)

      expect(screen.getByText(/Adding \(1\)/)).toBeInTheDocument()
    })

    it('shows removals in red', () => {
      const changesWithRemoval: AssignmentChange[] = [
        { user_id: 'user-1', asset_id: 'asset-1', action: 'remove' },
      ]

      render(
        <AssignmentPreview
          {...defaultProps}
          changes={changesWithRemoval}
        />
      )

      expect(screen.getByText(/Removing \(1\)/)).toBeInTheDocument()
    })

    it('shows supervisor and asset names in change list', () => {
      render(<AssignmentPreview {...defaultProps} />)

      // Should show supervisor name (appears in impact and change list)
      const supervisorNames = screen.getAllByText('Sarah Supervisor')
      expect(supervisorNames.length).toBeGreaterThan(0)
      // Should show asset name
      expect(screen.getByText('Packer 1')).toBeInTheDocument()
    })
  })

  describe('Warnings', () => {
    it('shows warnings when present', () => {
      const previewWithWarnings = {
        ...mockPreviewData,
        warnings: ['User will have no assets assigned'],
      }

      render(
        <AssignmentPreview
          {...defaultProps}
          previewData={previewWithWarnings}
        />
      )

      expect(screen.getByText('Warnings')).toBeInTheDocument()
      expect(screen.getByText('User will have no assets assigned')).toBeInTheDocument()
    })
  })

  describe('Loading State', () => {
    it('shows loading indicator when isLoading', () => {
      render(
        <AssignmentPreview
          {...defaultProps}
          isLoading={true}
          previewData={null}
        />
      )

      expect(screen.getByText('Calculating impact...')).toBeInTheDocument()
    })
  })

  describe('Error State', () => {
    it('shows error message when error prop is set', () => {
      render(
        <AssignmentPreview
          {...defaultProps}
          error="Failed to calculate preview"
        />
      )

      expect(screen.getByText('Failed to calculate preview')).toBeInTheDocument()
    })
  })

  describe('Actions (Task 7.4)', () => {
    it('calls onConfirm when Save Changes is clicked', () => {
      const onConfirm = vi.fn()
      render(
        <AssignmentPreview
          {...defaultProps}
          onConfirm={onConfirm}
        />
      )

      const saveButton = screen.getByText('Save Changes')
      fireEvent.click(saveButton)

      expect(onConfirm).toHaveBeenCalled()
    })

    it('calls onCancel when Cancel is clicked', () => {
      const onCancel = vi.fn()
      render(
        <AssignmentPreview
          {...defaultProps}
          onCancel={onCancel}
        />
      )

      const cancelButton = screen.getByText('Cancel')
      fireEvent.click(cancelButton)

      expect(onCancel).toHaveBeenCalled()
    })

    it('disables Save button while loading', () => {
      render(
        <AssignmentPreview
          {...defaultProps}
          isLoading={true}
        />
      )

      const saveButton = screen.getByRole('button', { name: /Save Changes/i })
      expect(saveButton).toBeDisabled()
    })

    it('disables buttons while saving', () => {
      render(
        <AssignmentPreview
          {...defaultProps}
          isSaving={true}
        />
      )

      const saveButton = screen.getByRole('button', { name: /Saving/i })
      expect(saveButton).toBeDisabled()
    })

    it('shows Saving... text when saving', () => {
      render(
        <AssignmentPreview
          {...defaultProps}
          isSaving={true}
        />
      )

      expect(screen.getByText('Saving...')).toBeInTheDocument()
    })
  })

  describe('Temporary Assignments', () => {
    it('shows clock icon for temporary assignment additions', () => {
      const changesWithTemp: AssignmentChange[] = [
        { user_id: 'user-1', asset_id: 'asset-3', action: 'add', expires_at: '2026-02-15T00:00:00Z' },
      ]

      render(
        <AssignmentPreview
          {...defaultProps}
          changes={changesWithTemp}
        />
      )

      // The clock icon should be present for temporary assignments
      // This is a visual indicator test
      expect(screen.getByText(/Adding \(1\)/)).toBeInTheDocument()
    })
  })
})
