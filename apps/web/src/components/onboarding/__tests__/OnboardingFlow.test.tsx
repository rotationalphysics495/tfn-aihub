/**
 * OnboardingFlow Component Tests (Story 8.8)
 *
 * Tests for the multi-step onboarding wizard.
 * AC#1, AC#2, AC#3, AC#4: Full onboarding flow behavior
 */

import { describe, it, expect, vi, beforeEach, Mock } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { OnboardingFlow } from '@/components/preferences/OnboardingFlow'

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

describe('OnboardingFlow', () => {
  const defaultProps = {
    userId: 'user-123',
    originalDestination: '/dashboard',
    onComplete: vi.fn(),
    onDismiss: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
    ;(global.fetch as Mock).mockResolvedValue({
      ok: true,
      json: async () => ({}),
    })
  })

  it('renders welcome step initially', () => {
    render(<OnboardingFlow {...defaultProps} />)

    expect(screen.getByText('Welcome to TFN AI Hub')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /get started/i })).toBeInTheDocument()
  })

  it('shows step progress indicator', () => {
    render(<OnboardingFlow {...defaultProps} />)

    expect(screen.getByText(/step 1 of/i)).toBeInTheDocument()
  })

  it('navigates to role step when clicking Get Started', () => {
    render(<OnboardingFlow {...defaultProps} />)

    fireEvent.click(screen.getByRole('button', { name: /get started/i }))

    expect(screen.getByText("What's your role?")).toBeInTheDocument()
  })

  it('shows dismiss button', () => {
    render(<OnboardingFlow {...defaultProps} />)

    expect(screen.getByRole('button', { name: /skip onboarding/i })).toBeInTheDocument()
  })

  it('calls onDismiss when dismiss button is clicked', async () => {
    render(<OnboardingFlow {...defaultProps} />)

    fireEvent.click(screen.getByRole('button', { name: /skip onboarding/i }))

    await waitFor(() => {
      expect(defaultProps.onDismiss).toHaveBeenCalled()
    })
  })

  it('navigates through plant manager flow (skips supervisor assets)', async () => {
    render(<OnboardingFlow {...defaultProps} />)

    // Step 1: Welcome
    fireEvent.click(screen.getByRole('button', { name: /get started/i }))

    // Step 2: Role - select Plant Manager
    fireEvent.click(screen.getByText('Plant Manager').closest('button')!)
    fireEvent.click(screen.getByRole('button', { name: /continue/i }))

    // Should skip supervisor assets and go to preferences
    await waitFor(() => {
      expect(screen.getByText('Customize Your Preferences')).toBeInTheDocument()
    })
  })

  it('navigates through supervisor flow (includes supervisor assets)', async () => {
    render(<OnboardingFlow {...defaultProps} />)

    // Step 1: Welcome
    fireEvent.click(screen.getByRole('button', { name: /get started/i }))

    // Step 2: Role - select Supervisor
    fireEvent.click(screen.getByText('Supervisor').closest('button')!)
    fireEvent.click(screen.getByRole('button', { name: /continue/i }))

    // Should show supervisor assets step
    await waitFor(() => {
      expect(screen.getByText('Your Assigned Assets')).toBeInTheDocument()
    })
  })

  it('allows navigating back between steps', () => {
    render(<OnboardingFlow {...defaultProps} />)

    // Go to role step
    fireEvent.click(screen.getByRole('button', { name: /get started/i }))
    expect(screen.getByText("What's your role?")).toBeInTheDocument()

    // Go back
    fireEvent.click(screen.getByRole('button', { name: /back/i }))
    expect(screen.getByText('Welcome to TFN AI Hub')).toBeInTheDocument()
  })

  it('shows confirmation step with preferences summary', async () => {
    render(<OnboardingFlow {...defaultProps} />)

    // Navigate through flow
    fireEvent.click(screen.getByRole('button', { name: /get started/i }))
    fireEvent.click(screen.getByText('Plant Manager').closest('button')!)
    fireEvent.click(screen.getByRole('button', { name: /continue/i }))

    // Wait for preferences step
    await waitFor(() => {
      expect(screen.getByText('Customize Your Preferences')).toBeInTheDocument()
    })

    // Continue to confirmation
    fireEvent.click(screen.getByRole('button', { name: /continue/i }))

    await waitFor(() => {
      expect(screen.getByText("You're All Set!")).toBeInTheDocument()
    })
  })

  it('calls onComplete after successful save', async () => {
    render(<OnboardingFlow {...defaultProps} />)

    // Navigate through flow quickly
    fireEvent.click(screen.getByRole('button', { name: /get started/i }))
    fireEvent.click(screen.getByText('Plant Manager').closest('button')!)
    fireEvent.click(screen.getByRole('button', { name: /continue/i }))

    await waitFor(() => {
      expect(screen.getByText('Customize Your Preferences')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: /continue/i }))

    await waitFor(() => {
      expect(screen.getByText("You're All Set!")).toBeInTheDocument()
    })

    // Click finish
    fireEvent.click(screen.getByRole('button', { name: /start briefing/i }))

    await waitFor(() => {
      expect(defaultProps.onComplete).toHaveBeenCalled()
    })
  })

  it('shows error message when save fails', async () => {
    ;(global.fetch as Mock).mockRejectedValueOnce(new Error('Network error'))

    render(<OnboardingFlow {...defaultProps} />)

    // Navigate to confirmation
    fireEvent.click(screen.getByRole('button', { name: /get started/i }))
    fireEvent.click(screen.getByText('Plant Manager').closest('button')!)
    fireEvent.click(screen.getByRole('button', { name: /continue/i }))

    await waitFor(() => {
      expect(screen.getByText('Customize Your Preferences')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: /continue/i }))

    await waitFor(() => {
      expect(screen.getByText("You're All Set!")).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: /start briefing/i }))

    await waitFor(() => {
      // Error message from rejected fetch is displayed
      expect(screen.getByText(/network error/i)).toBeInTheDocument()
    })
  })

  it('disables buttons while submitting', async () => {
    // Make fetch hang
    ;(global.fetch as Mock).mockImplementationOnce(
      () => new Promise(() => {}) // Never resolves
    )

    render(<OnboardingFlow {...defaultProps} />)

    // Navigate to confirmation
    fireEvent.click(screen.getByRole('button', { name: /get started/i }))
    fireEvent.click(screen.getByText('Plant Manager').closest('button')!)
    fireEvent.click(screen.getByRole('button', { name: /continue/i }))

    await waitFor(() => {
      expect(screen.getByText('Customize Your Preferences')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: /continue/i }))

    await waitFor(() => {
      expect(screen.getByText("You're All Set!")).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: /start briefing/i }))

    await waitFor(() => {
      expect(screen.getByText(/saving/i)).toBeInTheDocument()
    })
  })

  it('sends correct data to API on completion', async () => {
    render(<OnboardingFlow {...defaultProps} />)

    // Navigate and complete
    fireEvent.click(screen.getByRole('button', { name: /get started/i }))
    fireEvent.click(screen.getByText('Supervisor').closest('button')!)
    fireEvent.click(screen.getByRole('button', { name: /continue/i }))

    // Skip supervisor assets
    await waitFor(() => {
      expect(screen.getByText('Your Assigned Assets')).toBeInTheDocument()
    })
    fireEvent.click(screen.getByRole('button', { name: /continue/i }))

    await waitFor(() => {
      expect(screen.getByText('Customize Your Preferences')).toBeInTheDocument()
    })
    fireEvent.click(screen.getByRole('button', { name: /continue/i }))

    await waitFor(() => {
      expect(screen.getByText("You're All Set!")).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: /start briefing/i }))

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/v1/preferences',
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('"role":"supervisor"'),
        })
      )
    })
  })
})
