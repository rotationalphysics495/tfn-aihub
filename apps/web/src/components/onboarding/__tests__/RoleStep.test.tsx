/**
 * RoleStep Component Tests (Story 8.8)
 *
 * Tests for the role selection step of onboarding flow.
 * AC#2 - Step 2: Role selection (Plant Manager or Supervisor)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { RoleStep, UserRole } from '../RoleStep'

describe('RoleStep', () => {
  const defaultProps = {
    selectedRole: null as UserRole | null,
    onSelect: vi.fn(),
    onBack: vi.fn(),
    onContinue: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders role selection options', () => {
    render(<RoleStep {...defaultProps} />)

    expect(screen.getByText('Plant Manager')).toBeInTheDocument()
    expect(screen.getByText('Supervisor')).toBeInTheDocument()
  })

  it('displays role descriptions', () => {
    render(<RoleStep {...defaultProps} />)

    expect(screen.getByText('Full visibility across the entire plant')).toBeInTheDocument()
    expect(screen.getByText('Focused view on your assigned assets')).toBeInTheDocument()
  })

  it('displays scope differences', () => {
    render(<RoleStep {...defaultProps} />)

    expect(screen.getByText('See all 7 production areas in your briefings')).toBeInTheDocument()
    expect(screen.getByText('Briefings filtered to your specific responsibilities')).toBeInTheDocument()
  })

  it('calls onSelect with plant_manager when Plant Manager is clicked', () => {
    render(<RoleStep {...defaultProps} />)

    const plantManagerCard = screen.getByText('Plant Manager').closest('button')
    fireEvent.click(plantManagerCard!)

    expect(defaultProps.onSelect).toHaveBeenCalledWith('plant_manager')
  })

  it('calls onSelect with supervisor when Supervisor is clicked', () => {
    render(<RoleStep {...defaultProps} />)

    const supervisorCard = screen.getByText('Supervisor').closest('button')
    fireEvent.click(supervisorCard!)

    expect(defaultProps.onSelect).toHaveBeenCalledWith('supervisor')
  })

  it('shows selected state when role is selected', () => {
    render(<RoleStep {...defaultProps} selectedRole="plant_manager" />)

    const plantManagerCard = screen.getByText('Plant Manager').closest('button')
    expect(plantManagerCard).toHaveClass('border-primary')
    expect(plantManagerCard).toHaveAttribute('aria-pressed', 'true')
  })

  it('disables Continue button when no role is selected', () => {
    render(<RoleStep {...defaultProps} />)

    const continueButton = screen.getByRole('button', { name: /continue/i })
    expect(continueButton).toBeDisabled()
  })

  it('enables Continue button when role is selected', () => {
    render(<RoleStep {...defaultProps} selectedRole="supervisor" />)

    const continueButton = screen.getByRole('button', { name: /continue/i })
    expect(continueButton).not.toBeDisabled()
  })

  it('calls onBack when Back button is clicked', () => {
    render(<RoleStep {...defaultProps} />)

    const backButton = screen.getByRole('button', { name: /back/i })
    fireEvent.click(backButton)

    expect(defaultProps.onBack).toHaveBeenCalledTimes(1)
  })

  it('calls onContinue when Continue button is clicked', () => {
    render(<RoleStep {...defaultProps} selectedRole="supervisor" />)

    const continueButton = screen.getByRole('button', { name: /continue/i })
    fireEvent.click(continueButton)

    expect(defaultProps.onContinue).toHaveBeenCalledTimes(1)
  })
})
