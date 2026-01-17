/**
 * WelcomeStep Component Tests (Story 8.8)
 *
 * Tests for the welcome step of onboarding flow.
 * AC#2 - Step 1: Welcome + explain quick setup
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { WelcomeStep } from '../WelcomeStep'

describe('WelcomeStep', () => {
  const defaultProps = {
    onContinue: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders welcome message', () => {
    render(<WelcomeStep {...defaultProps} />)

    expect(screen.getByText('Welcome to TFN AI Hub')).toBeInTheDocument()
    expect(screen.getByText("Let's personalize your briefing experience")).toBeInTheDocument()
  })

  it('displays estimated completion time under 2 minutes', () => {
    render(<WelcomeStep {...defaultProps} />)

    expect(screen.getByText('Takes less than 2 minutes')).toBeInTheDocument()
  })

  it('shows what will be set up', () => {
    render(<WelcomeStep {...defaultProps} />)

    expect(screen.getByText('Your role and assigned areas')).toBeInTheDocument()
    expect(screen.getByText('Preferred area order for briefings')).toBeInTheDocument()
    expect(screen.getByText('Detail level and voice preferences')).toBeInTheDocument()
  })

  it('renders Get Started button', () => {
    render(<WelcomeStep {...defaultProps} />)

    const button = screen.getByRole('button', { name: /get started/i })
    expect(button).toBeInTheDocument()
  })

  it('calls onContinue when Get Started is clicked', () => {
    render(<WelcomeStep {...defaultProps} />)

    const button = screen.getByRole('button', { name: /get started/i })
    fireEvent.click(button)

    expect(defaultProps.onContinue).toHaveBeenCalledTimes(1)
  })

  it('applies custom className', () => {
    const { container } = render(<WelcomeStep {...defaultProps} className="custom-class" />)

    expect(container.firstChild).toHaveClass('custom-class')
  })
})
