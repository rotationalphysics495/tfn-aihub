/**
 * DetailLevelToggle Component Tests (Story 8.8)
 *
 * Tests for the detail level toggle component.
 * AC#2 - Step 5: Detail level preference (Summary or Detailed)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { DetailLevelToggle, DetailLevel } from '../DetailLevelToggle'

describe('DetailLevelToggle', () => {
  const defaultProps = {
    value: 'summary' as DetailLevel,
    onChange: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders Summary and Detailed options', () => {
    render(<DetailLevelToggle {...defaultProps} />)

    expect(screen.getByText('Summary')).toBeInTheDocument()
    expect(screen.getByText('Detailed')).toBeInTheDocument()
  })

  it('displays descriptions for each level', () => {
    render(<DetailLevelToggle {...defaultProps} />)

    expect(screen.getByText(/quick overview with key metrics/i)).toBeInTheDocument()
    expect(screen.getByText(/in-depth analysis with full breakdowns/i)).toBeInTheDocument()
  })

  it('shows instruction text', () => {
    render(<DetailLevelToggle {...defaultProps} />)

    expect(
      screen.getByText(/choose how much detail you want/i)
    ).toBeInTheDocument()
  })

  it('shows selected state for Summary', () => {
    render(<DetailLevelToggle {...defaultProps} value="summary" />)

    const summaryButton = screen.getByText('Summary').closest('button')
    expect(summaryButton).toHaveClass('border-primary')
    expect(summaryButton).toHaveAttribute('aria-pressed', 'true')
  })

  it('shows selected state for Detailed', () => {
    render(<DetailLevelToggle {...defaultProps} value="detailed" />)

    const detailedButton = screen.getByText('Detailed').closest('button')
    expect(detailedButton).toHaveClass('border-primary')
    expect(detailedButton).toHaveAttribute('aria-pressed', 'true')
  })

  it('calls onChange with summary when Summary is clicked', () => {
    render(<DetailLevelToggle {...defaultProps} value="detailed" />)

    const summaryButton = screen.getByText('Summary').closest('button')
    fireEvent.click(summaryButton!)

    expect(defaultProps.onChange).toHaveBeenCalledWith('summary')
  })

  it('calls onChange with detailed when Detailed is clicked', () => {
    render(<DetailLevelToggle {...defaultProps} value="summary" />)

    const detailedButton = screen.getByText('Detailed').closest('button')
    fireEvent.click(detailedButton!)

    expect(defaultProps.onChange).toHaveBeenCalledWith('detailed')
  })

  it('applies custom className', () => {
    const { container } = render(
      <DetailLevelToggle {...defaultProps} className="custom-class" />
    )

    expect(container.firstChild).toHaveClass('custom-class')
  })

  it('shows checkmark on selected option', () => {
    const { container } = render(<DetailLevelToggle {...defaultProps} value="summary" />)

    // Find the summary button and check for checkmark icon
    const summaryButton = screen.getByText('Summary').closest('button')
    const checkmark = summaryButton?.querySelector('svg path[d*="M5 13l4 4L19 7"]')
    expect(checkmark).toBeInTheDocument()
  })
})
