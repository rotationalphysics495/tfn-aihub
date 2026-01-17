/**
 * HandoffCreator Component Tests (Story 9.1, Task 8)
 *
 * Tests for the shift handoff creation wizard.
 * AC#1, AC#2, AC#3, AC#4: Full handoff creation flow behavior
 *
 * References:
 * - [Source: architecture/voice-briefing.md#Shift-Handoff-Workflow]
 */

import { describe, it, expect, vi, beforeEach, Mock } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { HandoffCreator } from '@/components/handoff/HandoffCreator'

// Mock the Supabase client
vi.mock('@/lib/supabase/client', () => ({
  createClient: () => ({
    auth: {
      getSession: vi.fn().mockResolvedValue({
        data: { session: { access_token: 'mock-token' } },
      }),
    },
  }),
}))

// Mock fetch
global.fetch = vi.fn()

// Mock responses
const mockInitiateResponse = {
  shift_info: {
    shift_type: 'afternoon',
    start_time: '2026-01-17T14:00:00Z',
    end_time: '2026-01-17T22:00:00Z',
    shift_date: '2026-01-17',
  },
  assigned_assets: [
    {
      asset_id: '11111111-1111-1111-1111-111111111111',
      asset_name: 'Packaging Line 1',
      area_name: 'Packaging',
    },
    {
      asset_id: '22222222-2222-2222-2222-222222222222',
      asset_name: 'Packaging Line 2',
      area_name: 'Packaging',
    },
  ],
  existing_handoff: null,
  can_create: true,
  message: 'Ready to create handoff',
}

const mockCreateResponse = {
  id: 'handoff-123',
  user_id: 'user-123',
  shift_date: '2026-01-17',
  shift_type: 'afternoon',
  status: 'draft',
  assets_covered: [],
  summary: null,
  text_notes: null,
  created_at: '2026-01-17T14:30:00Z',
  updated_at: '2026-01-17T14:30:00Z',
}

describe('HandoffCreator', () => {
  const defaultProps = {
    userId: 'user-123',
    onComplete: vi.fn(),
    onCancel: vi.fn(),
    onEditExisting: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
    ;(global.fetch as Mock).mockImplementation((url: string) => {
      if (url.includes('/initiate') || url === '/api/v1/handoff/initiate') {
        return Promise.resolve({
          ok: true,
          json: async () => mockInitiateResponse,
        })
      }
      if (url === '/api/v1/handoff/' || url.match(/\/api\/v1\/handoff\/$/)) {
        return Promise.resolve({
          ok: true,
          json: async () => mockCreateResponse,
        })
      }
      return Promise.resolve({
        ok: false,
        json: async () => ({ detail: 'Unknown endpoint' }),
      })
    })
  })

  it('shows loading state initially', () => {
    render(<HandoffCreator {...defaultProps} />)

    expect(screen.getByText(/loading shift information/i)).toBeInTheDocument()
  })

  it('displays shift confirmation step after loading', async () => {
    render(<HandoffCreator {...defaultProps} />)

    await waitFor(() => {
      expect(screen.getByText('Create Shift Handoff')).toBeInTheDocument()
    })

    // Should show shift type
    expect(screen.getByText('Afternoon')).toBeInTheDocument()

    // Should show assets
    expect(screen.getByText('Packaging Line 1')).toBeInTheDocument()
    expect(screen.getByText('Packaging Line 2')).toBeInTheDocument()
  })

  it('shows error state when no assets assigned (AC#3)', async () => {
    ;(global.fetch as Mock).mockImplementationOnce(() =>
      Promise.resolve({
        ok: true,
        json: async () => ({
          ...mockInitiateResponse,
          assigned_assets: [],
          can_create: false,
          message: 'No assets assigned - contact your administrator',
        }),
      })
    )

    render(<HandoffCreator {...defaultProps} />)

    await waitFor(() => {
      expect(screen.getByText('Unable to Create Handoff')).toBeInTheDocument()
    })

    expect(screen.getByText(/no assets assigned/i)).toBeInTheDocument()
  })

  it('shows existing handoff warning (AC#4)', async () => {
    ;(global.fetch as Mock).mockImplementationOnce(() =>
      Promise.resolve({
        ok: true,
        json: async () => ({
          ...mockInitiateResponse,
          existing_handoff: {
            exists: true,
            existing_handoff_id: 'existing-123',
            status: 'draft',
            message: 'A draft handoff exists for this shift. You can edit it.',
            can_edit: true,
            can_add_supplemental: false,
          },
        }),
      })
    )

    render(<HandoffCreator {...defaultProps} />)

    await waitFor(() => {
      expect(screen.getByText(/draft handoff exists/i)).toBeInTheDocument()
    })

    expect(screen.getByRole('button', { name: /edit existing/i })).toBeInTheDocument()
  })

  it('allows selecting and deselecting assets', async () => {
    render(<HandoffCreator {...defaultProps} />)

    await waitFor(() => {
      expect(screen.getByText('Create Shift Handoff')).toBeInTheDocument()
    })

    // All should be checked by default
    const checkboxes = screen.getAllByRole('checkbox')
    checkboxes.forEach(checkbox => {
      expect(checkbox).toBeChecked()
    })

    // Click deselect all
    fireEvent.click(screen.getByText('Deselect All'))

    // All should be unchecked
    checkboxes.forEach(checkbox => {
      expect(checkbox).not.toBeChecked()
    })

    // Click select all
    fireEvent.click(screen.getByText('Select All'))

    // All should be checked again
    checkboxes.forEach(checkbox => {
      expect(checkbox).toBeChecked()
    })
  })

  it('prevents navigation when no assets selected', async () => {
    render(<HandoffCreator {...defaultProps} />)

    await waitFor(() => {
      expect(screen.getByText('Create Shift Handoff')).toBeInTheDocument()
    })

    // Deselect all
    fireEvent.click(screen.getByText('Deselect All'))

    // Next button should be disabled
    expect(screen.getByRole('button', { name: /next/i })).toBeDisabled()
  })

  it('navigates through wizard steps', async () => {
    render(<HandoffCreator {...defaultProps} />)

    await waitFor(() => {
      expect(screen.getByText('Create Shift Handoff')).toBeInTheDocument()
    })

    // Step 1: Shift Confirmation -> Next
    fireEvent.click(screen.getByRole('button', { name: /next/i }))

    await waitFor(() => {
      expect(screen.getByText('Add Notes')).toBeInTheDocument()
    })

    // Step 2: Summary Notes -> Next
    fireEvent.click(screen.getByRole('button', { name: /next/i }))

    await waitFor(() => {
      expect(screen.getByText('Voice Notes')).toBeInTheDocument()
    })

    // Step 3: Voice Notes -> Next
    fireEvent.click(screen.getByRole('button', { name: /next/i }))

    await waitFor(() => {
      expect(screen.getByText('Review & Submit')).toBeInTheDocument()
    })
  })

  it('allows navigating back between steps', async () => {
    render(<HandoffCreator {...defaultProps} />)

    await waitFor(() => {
      expect(screen.getByText('Create Shift Handoff')).toBeInTheDocument()
    })

    // Go to step 2
    fireEvent.click(screen.getByRole('button', { name: /next/i }))

    await waitFor(() => {
      expect(screen.getByText('Add Notes')).toBeInTheDocument()
    })

    // Go back
    fireEvent.click(screen.getByRole('button', { name: /back/i }))

    await waitFor(() => {
      expect(screen.getByText('Create Shift Handoff')).toBeInTheDocument()
    })
  })

  it('allows adding text notes', async () => {
    render(<HandoffCreator {...defaultProps} />)

    await waitFor(() => {
      expect(screen.getByText('Create Shift Handoff')).toBeInTheDocument()
    })

    // Go to notes step
    fireEvent.click(screen.getByRole('button', { name: /next/i }))

    await waitFor(() => {
      expect(screen.getByText('Add Notes')).toBeInTheDocument()
    })

    // Add notes
    const textarea = screen.getByPlaceholderText(/add any important information/i)
    fireEvent.change(textarea, { target: { value: 'Test handoff notes' } })

    expect(textarea).toHaveValue('Test handoff notes')
  })

  it('shows voice notes placeholder (Story 9.3)', async () => {
    render(<HandoffCreator {...defaultProps} />)

    await waitFor(() => {
      expect(screen.getByText('Create Shift Handoff')).toBeInTheDocument()
    })

    // Navigate to voice notes step
    fireEvent.click(screen.getByRole('button', { name: /next/i }))
    await waitFor(() => {
      expect(screen.getByText('Add Notes')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: /next/i }))

    await waitFor(() => {
      expect(screen.getByText('Voice Notes')).toBeInTheDocument()
    })

    // Should show placeholder
    expect(screen.getByText(/voice note recording will be available/i)).toBeInTheDocument()

    // Button should be disabled
    expect(screen.getByRole('button', { name: /add voice note/i })).toBeDisabled()
  })

  it('shows confirmation summary before submission', async () => {
    render(<HandoffCreator {...defaultProps} />)

    await waitFor(() => {
      expect(screen.getByText('Create Shift Handoff')).toBeInTheDocument()
    })

    // Navigate to confirmation
    fireEvent.click(screen.getByRole('button', { name: /next/i }))
    await waitFor(() => {
      expect(screen.getByText('Add Notes')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: /next/i }))
    await waitFor(() => {
      expect(screen.getByText('Voice Notes')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: /next/i }))

    await waitFor(() => {
      expect(screen.getByText('Review & Submit')).toBeInTheDocument()
    })

    // Should show summary
    expect(screen.getByText(/shift information/i)).toBeInTheDocument()
    expect(screen.getByText(/assets covered/i)).toBeInTheDocument()
  })

  it('calls onComplete after successful creation', async () => {
    render(<HandoffCreator {...defaultProps} />)

    await waitFor(() => {
      expect(screen.getByText('Create Shift Handoff')).toBeInTheDocument()
    })

    // Navigate through all steps
    for (let i = 0; i < 3; i++) {
      fireEvent.click(screen.getByRole('button', { name: /next/i }))
      await waitFor(() => {
        // Wait for next step to render
      })
    }

    await waitFor(() => {
      expect(screen.getByText('Review & Submit')).toBeInTheDocument()
    })

    // Submit
    fireEvent.click(screen.getByRole('button', { name: /create handoff/i }))

    await waitFor(() => {
      expect(defaultProps.onComplete).toHaveBeenCalledWith('handoff-123')
    })
  })

  it('calls onCancel when cancel button is clicked', async () => {
    render(<HandoffCreator {...defaultProps} />)

    await waitFor(() => {
      expect(screen.getByText('Create Shift Handoff')).toBeInTheDocument()
    })

    // Click the "Cancel" text button in the card footer (not the X icon button)
    const cancelButtons = screen.getAllByRole('button', { name: /cancel/i })
    const cancelTextButton = cancelButtons.find(btn => btn.textContent === 'Cancel')
    fireEvent.click(cancelTextButton!)

    expect(defaultProps.onCancel).toHaveBeenCalled()
  })

  it('calls onEditExisting when edit button is clicked (AC#4)', async () => {
    ;(global.fetch as Mock).mockImplementationOnce(() =>
      Promise.resolve({
        ok: true,
        json: async () => ({
          ...mockInitiateResponse,
          existing_handoff: {
            exists: true,
            existing_handoff_id: 'existing-456',
            status: 'draft',
            message: 'A draft handoff exists for this shift.',
            can_edit: true,
            can_add_supplemental: false,
          },
        }),
      })
    )

    render(<HandoffCreator {...defaultProps} />)

    await waitFor(() => {
      expect(screen.getByText(/draft handoff exists/i)).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: /edit existing/i }))

    expect(defaultProps.onEditExisting).toHaveBeenCalledWith('existing-456')
  })

  it('shows error when API call fails', async () => {
    ;(global.fetch as Mock).mockImplementationOnce(() =>
      Promise.reject(new Error('Network error'))
    )

    render(<HandoffCreator {...defaultProps} />)

    await waitFor(() => {
      expect(screen.getByText('Unable to Create Handoff')).toBeInTheDocument()
    })

    expect(screen.getByText(/network error/i)).toBeInTheDocument()
  })

  it('shows step progress indicator', async () => {
    render(<HandoffCreator {...defaultProps} />)

    await waitFor(() => {
      expect(screen.getByText('Create Shift Handoff')).toBeInTheDocument()
    })

    expect(screen.getByText(/step 1 of 4/i)).toBeInTheDocument()
  })

  it('disables submit button while submitting', async () => {
    // Make fetch hang for create
    ;(global.fetch as Mock).mockImplementation((url: string) => {
      if (url.includes('/initiate')) {
        return Promise.resolve({
          ok: true,
          json: async () => mockInitiateResponse,
        })
      }
      // Never resolve create
      return new Promise(() => {})
    })

    render(<HandoffCreator {...defaultProps} />)

    await waitFor(() => {
      expect(screen.getByText('Create Shift Handoff')).toBeInTheDocument()
    })

    // Navigate to confirmation
    for (let i = 0; i < 3; i++) {
      fireEvent.click(screen.getByRole('button', { name: /next/i }))
      await waitFor(() => {})
    }

    await waitFor(() => {
      expect(screen.getByText('Review & Submit')).toBeInTheDocument()
    })

    // Click submit
    fireEvent.click(screen.getByRole('button', { name: /create handoff/i }))

    await waitFor(() => {
      expect(screen.getByText(/creating/i)).toBeInTheDocument()
    })
  })
})
