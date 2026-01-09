import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { FollowUpChips } from '../FollowUpChips'

/**
 * Tests for FollowUpChips Component
 *
 * Story: 5.7 - Agent Chat Integration
 * AC: #3 - Follow-Up Question Chips
 */

describe('FollowUpChips', () => {
  const mockQuestions = [
    'What caused the downtime?',
    'How does this compare to last week?',
    'Show me the trend',
  ]

  it('renders follow-up questions as clickable chips', () => {
    const onSelect = vi.fn()

    render(<FollowUpChips questions={mockQuestions} onSelect={onSelect} />)

    expect(screen.getByText('What caused the downtime?')).toBeInTheDocument()
    expect(screen.getByText('How does this compare to last week?')).toBeInTheDocument()
    expect(screen.getByText('Show me the trend')).toBeInTheDocument()
  })

  it('calls onSelect with the question when chip is clicked', () => {
    const onSelect = vi.fn()

    render(<FollowUpChips questions={mockQuestions} onSelect={onSelect} />)

    const chip = screen.getByText('What caused the downtime?').closest('button')
    if (chip) {
      fireEvent.click(chip)
      expect(onSelect).toHaveBeenCalledWith('What caused the downtime?')
    }
  })

  it('limits chips to maxChips (default 3)', () => {
    const onSelect = vi.fn()
    const manyQuestions = [
      'Question 1',
      'Question 2',
      'Question 3',
      'Question 4',
      'Question 5',
    ]

    render(<FollowUpChips questions={manyQuestions} onSelect={onSelect} />)

    expect(screen.getByText('Question 1')).toBeInTheDocument()
    expect(screen.getByText('Question 2')).toBeInTheDocument()
    expect(screen.getByText('Question 3')).toBeInTheDocument()
    expect(screen.queryByText('Question 4')).not.toBeInTheDocument()
    expect(screen.queryByText('Question 5')).not.toBeInTheDocument()
  })

  it('respects custom maxChips value', () => {
    const onSelect = vi.fn()
    const manyQuestions = [
      'Question 1',
      'Question 2',
      'Question 3',
      'Question 4',
    ]

    render(
      <FollowUpChips
        questions={manyQuestions}
        onSelect={onSelect}
        maxChips={2}
      />
    )

    expect(screen.getByText('Question 1')).toBeInTheDocument()
    expect(screen.getByText('Question 2')).toBeInTheDocument()
    expect(screen.queryByText('Question 3')).not.toBeInTheDocument()
  })

  it('returns null when questions array is empty', () => {
    const onSelect = vi.fn()

    const { container } = render(
      <FollowUpChips questions={[]} onSelect={onSelect} />
    )

    expect(container.firstChild).toBeNull()
  })

  it('returns null when questions is undefined', () => {
    const onSelect = vi.fn()

    // @ts-expect-error - Testing undefined behavior
    const { container } = render(
      <FollowUpChips questions={undefined} onSelect={onSelect} />
    )

    expect(container.firstChild).toBeNull()
  })

  it('has proper aria attributes for accessibility', () => {
    const onSelect = vi.fn()

    render(<FollowUpChips questions={mockQuestions} onSelect={onSelect} />)

    const container = screen.getByRole('group')
    expect(container).toHaveAttribute('aria-label', 'Suggested follow-up questions')
  })

  it('chips have proper aria-label', () => {
    const onSelect = vi.fn()

    render(<FollowUpChips questions={['Test question']} onSelect={onSelect} />)

    const chip = screen.getByRole('button')
    expect(chip).toHaveAttribute('aria-label', 'Ask: Test question')
  })

  it('applies animation classes', () => {
    const onSelect = vi.fn()

    render(<FollowUpChips questions={mockQuestions} onSelect={onSelect} />)

    const container = screen.getByRole('group')
    expect(container).toHaveClass('animate-in')
    expect(container).toHaveClass('fade-in')
  })

  it('applies custom className', () => {
    const onSelect = vi.fn()

    render(
      <FollowUpChips
        questions={mockQuestions}
        onSelect={onSelect}
        className="custom-class"
      />
    )

    const container = screen.getByRole('group')
    expect(container).toHaveClass('custom-class')
  })
})
