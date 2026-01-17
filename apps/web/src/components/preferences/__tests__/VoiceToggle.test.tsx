/**
 * VoiceToggle Component Tests (Story 8.8)
 *
 * Tests for the voice toggle component.
 * AC#2 - Step 6: Voice preference (On/Off)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { VoiceToggle } from '../VoiceToggle'

describe('VoiceToggle', () => {
  const defaultProps = {
    value: true,
    onChange: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders voice toggle switch', () => {
    render(<VoiceToggle {...defaultProps} />)

    const toggle = screen.getByRole('switch')
    expect(toggle).toBeInTheDocument()
  })

  it('shows Voice Briefings label', () => {
    render(<VoiceToggle {...defaultProps} />)

    expect(screen.getByText('Voice Briefings')).toBeInTheDocument()
  })

  it('shows enabled state description when voice is on', () => {
    render(<VoiceToggle {...defaultProps} value={true} />)

    expect(screen.getByText('Briefings will be read aloud')).toBeInTheDocument()
  })

  it('shows disabled state description when voice is off', () => {
    render(<VoiceToggle {...defaultProps} value={false} />)

    expect(screen.getByText('Text-only briefings')).toBeInTheDocument()
  })

  it('sets aria-checked to true when value is true', () => {
    render(<VoiceToggle {...defaultProps} value={true} />)

    const toggle = screen.getByRole('switch')
    expect(toggle).toHaveAttribute('aria-checked', 'true')
  })

  it('sets aria-checked to false when value is false', () => {
    render(<VoiceToggle {...defaultProps} value={false} />)

    const toggle = screen.getByRole('switch')
    expect(toggle).toHaveAttribute('aria-checked', 'false')
  })

  it('calls onChange with false when clicking toggle that is on', () => {
    render(<VoiceToggle {...defaultProps} value={true} />)

    const toggle = screen.getByRole('switch')
    fireEvent.click(toggle)

    expect(defaultProps.onChange).toHaveBeenCalledWith(false)
  })

  it('calls onChange with true when clicking toggle that is off', () => {
    render(<VoiceToggle {...defaultProps} value={false} />)

    const toggle = screen.getByRole('switch')
    fireEvent.click(toggle)

    expect(defaultProps.onChange).toHaveBeenCalledWith(true)
  })

  it('shows Q&A information tip', () => {
    render(<VoiceToggle {...defaultProps} />)

    expect(
      screen.getByText(/you can always pause and ask follow-up questions/i)
    ).toBeInTheDocument()
  })

  it('applies custom className', () => {
    const { container } = render(
      <VoiceToggle {...defaultProps} className="custom-class" />
    )

    expect(container.firstChild).toHaveClass('custom-class')
  })

  it('has accessible name for toggle', () => {
    render(<VoiceToggle {...defaultProps} />)

    const toggle = screen.getByRole('switch', { name: /enable voice briefings/i })
    expect(toggle).toBeInTheDocument()
  })
})
