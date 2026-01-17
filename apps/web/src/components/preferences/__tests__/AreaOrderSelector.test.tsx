/**
 * AreaOrderSelector Component Tests (Story 8.8)
 *
 * Tests for the area order selector component.
 * AC#2 - Step 4: Area order preference (drag-to-reorder or numbered selection)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { AreaOrderSelector, DEFAULT_AREA_ORDER, AREA_DESCRIPTIONS } from '../AreaOrderSelector'

describe('AreaOrderSelector', () => {
  const defaultProps = {
    value: DEFAULT_AREA_ORDER,
    onChange: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('displays all 7 production areas', () => {
    render(<AreaOrderSelector {...defaultProps} />)

    DEFAULT_AREA_ORDER.forEach((area) => {
      expect(screen.getByText(area)).toBeInTheDocument()
    })
  })

  it('shows position numbers', () => {
    render(<AreaOrderSelector {...defaultProps} />)

    for (let i = 1; i <= 7; i++) {
      expect(screen.getByText(i.toString())).toBeInTheDocument()
    }
  })

  it('shows area descriptions in non-compact mode', () => {
    render(<AreaOrderSelector {...defaultProps} />)

    Object.values(AREA_DESCRIPTIONS).forEach((description) => {
      expect(screen.getByText(description)).toBeInTheDocument()
    })
  })

  it('hides area descriptions in compact mode', () => {
    render(<AreaOrderSelector {...defaultProps} compact />)

    Object.values(AREA_DESCRIPTIONS).forEach((description) => {
      expect(screen.queryByText(description)).not.toBeInTheDocument()
    })
  })

  it('shows instruction text', () => {
    render(<AreaOrderSelector {...defaultProps} />)

    expect(
      screen.getByText(/drag to reorder or use the arrows/i)
    ).toBeInTheDocument()
  })

  it('has up and down arrow buttons for each area', () => {
    render(<AreaOrderSelector {...defaultProps} />)

    const upButtons = screen.getAllByRole('button', { name: /move .* up/i })
    const downButtons = screen.getAllByRole('button', { name: /move .* down/i })

    expect(upButtons).toHaveLength(7)
    expect(downButtons).toHaveLength(7)
  })

  it('disables up button for first item', () => {
    render(<AreaOrderSelector {...defaultProps} />)

    const upButton = screen.getByRole('button', { name: /move packing up/i })
    expect(upButton).toBeDisabled()
  })

  it('disables down button for last item', () => {
    render(<AreaOrderSelector {...defaultProps} />)

    const downButton = screen.getByRole('button', { name: /move flavor room down/i })
    expect(downButton).toBeDisabled()
  })

  it('calls onChange when moving item up', () => {
    render(<AreaOrderSelector {...defaultProps} />)

    // Move Rychigers (index 1) up
    const upButton = screen.getByRole('button', { name: /move rychigers up/i })
    fireEvent.click(upButton)

    expect(defaultProps.onChange).toHaveBeenCalledWith([
      'Rychigers',
      'Packing',
      'Grinding',
      'Powder',
      'Roasting',
      'Green Bean',
      'Flavor Room',
    ])
  })

  it('calls onChange when moving item down', () => {
    render(<AreaOrderSelector {...defaultProps} />)

    // Move Packing (index 0) down
    const downButton = screen.getByRole('button', { name: /move packing down/i })
    fireEvent.click(downButton)

    expect(defaultProps.onChange).toHaveBeenCalledWith([
      'Rychigers',
      'Packing',
      'Grinding',
      'Powder',
      'Roasting',
      'Green Bean',
      'Flavor Room',
    ])
  })

  it('uses default order when value is empty', () => {
    render(<AreaOrderSelector {...defaultProps} value={[]} />)

    DEFAULT_AREA_ORDER.forEach((area) => {
      expect(screen.getByText(area)).toBeInTheDocument()
    })
  })

  it('highlights first position', () => {
    const { container } = render(<AreaOrderSelector {...defaultProps} />)

    // First position number should have primary background color
    const firstNumber = container.querySelector('.bg-primary')
    expect(firstNumber).toHaveTextContent('1')
  })

  it('applies custom className', () => {
    const { container } = render(
      <AreaOrderSelector {...defaultProps} className="custom-class" />
    )

    expect(container.firstChild).toHaveClass('custom-class')
  })
})
