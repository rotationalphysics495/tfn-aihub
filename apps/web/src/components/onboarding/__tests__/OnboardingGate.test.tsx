/**
 * OnboardingGate Component Tests (Story 8.8)
 *
 * Tests for the onboarding gate wrapper component.
 * AC#1: Trigger onboarding for first-time users
 * AC#4: Handle abandonment and re-trigger
 */

import { describe, it, expect, vi, beforeEach, Mock } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { OnboardingGate } from '../OnboardingGate'

// Mock the hooks and components
vi.mock('@/lib/hooks/useOnboardingRequired', () => ({
  useOnboardingRequired: vi.fn(),
}))

vi.mock('@/components/preferences/OnboardingFlow', () => ({
  OnboardingFlow: ({ onComplete, onDismiss }: { onComplete: () => void; onDismiss: () => void }) => (
    <div data-testid="onboarding-flow">
      <button onClick={onComplete} data-testid="complete-button">Complete</button>
      <button onClick={onDismiss} data-testid="dismiss-button">Dismiss</button>
    </div>
  ),
}))

import { useOnboardingRequired } from '@/lib/hooks/useOnboardingRequired'

const mockUseOnboardingRequired = useOnboardingRequired as Mock

describe('OnboardingGate', () => {
  const mockRecheck = vi.fn().mockResolvedValue(undefined)

  beforeEach(() => {
    vi.clearAllMocks()
    // Mock window.location
    Object.defineProperty(window, 'location', {
      writable: true,
      value: { reload: vi.fn(), href: '' },
    })
  })

  it('shows loading state while checking onboarding status', () => {
    mockUseOnboardingRequired.mockReturnValue({
      isRequired: false,
      isLoading: true,
      originalDestination: null,
      userId: null,
      recheck: mockRecheck,
    })

    render(
      <OnboardingGate>
        <div>Child Content</div>
      </OnboardingGate>
    )

    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })

  it('renders children when onboarding is not required', () => {
    mockUseOnboardingRequired.mockReturnValue({
      isRequired: false,
      isLoading: false,
      originalDestination: null,
      userId: 'user-123',
      recheck: mockRecheck,
    })

    render(
      <OnboardingGate>
        <div>Child Content</div>
      </OnboardingGate>
    )

    expect(screen.getByText('Child Content')).toBeInTheDocument()
    expect(screen.queryByTestId('onboarding-flow')).not.toBeInTheDocument()
  })

  it('shows onboarding flow when required', () => {
    mockUseOnboardingRequired.mockReturnValue({
      isRequired: true,
      isLoading: false,
      originalDestination: '/dashboard',
      userId: 'user-123',
      recheck: mockRecheck,
    })

    render(
      <OnboardingGate>
        <div>Child Content</div>
      </OnboardingGate>
    )

    expect(screen.getByTestId('onboarding-flow')).toBeInTheDocument()
  })

  it('dims children when onboarding is shown', () => {
    mockUseOnboardingRequired.mockReturnValue({
      isRequired: true,
      isLoading: false,
      originalDestination: '/dashboard',
      userId: 'user-123',
      recheck: mockRecheck,
    })

    const { container } = render(
      <OnboardingGate>
        <div>Child Content</div>
      </OnboardingGate>
    )

    // The parent wrapper div should have the dimming classes
    const dimmedContainer = container.querySelector('.opacity-20')
    expect(dimmedContainer).toBeInTheDocument()
    expect(dimmedContainer).toHaveClass('pointer-events-none')
    // Child content should still be rendered inside the dimmed container
    expect(screen.getByText('Child Content')).toBeInTheDocument()
  })

  it('does not show onboarding when userId is null', () => {
    mockUseOnboardingRequired.mockReturnValue({
      isRequired: true,
      isLoading: false,
      originalDestination: '/dashboard',
      userId: null,
      recheck: mockRecheck,
    })

    render(
      <OnboardingGate>
        <div>Child Content</div>
      </OnboardingGate>
    )

    expect(screen.queryByTestId('onboarding-flow')).not.toBeInTheDocument()
    expect(screen.getByText('Child Content')).toBeInTheDocument()
  })

  it('reloads page on complete', async () => {
    mockUseOnboardingRequired.mockReturnValue({
      isRequired: true,
      isLoading: false,
      originalDestination: '/dashboard',
      userId: 'user-123',
      recheck: mockRecheck,
    })

    render(
      <OnboardingGate>
        <div>Child Content</div>
      </OnboardingGate>
    )

    screen.getByTestId('complete-button').click()

    await waitFor(() => {
      expect(mockRecheck).toHaveBeenCalled()
    })
  })

  it('navigates to dashboard on dismiss', () => {
    mockUseOnboardingRequired.mockReturnValue({
      isRequired: true,
      isLoading: false,
      originalDestination: '/some-page',
      userId: 'user-123',
      recheck: mockRecheck,
    })

    render(
      <OnboardingGate>
        <div>Child Content</div>
      </OnboardingGate>
    )

    screen.getByTestId('dismiss-button').click()

    expect(window.location.href).toBe('/dashboard')
  })
})
