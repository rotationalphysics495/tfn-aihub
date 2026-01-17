/**
 * PauseCountdown Component Tests (Story 8.7 Task 3.4)
 *
 * Tests for the PauseCountdown overlay component including:
 * - Countdown display and progress ring
 * - Next section information
 * - Continue now button
 * - Overlay vs inline modes
 *
 * AC#2: Pause prompt with countdown timer showing silence detection progress
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { PauseCountdown, PauseCountdownProps } from '../PauseCountdown';
import { BriefingSection } from '@/lib/hooks/useBriefing';

// Mock next section for testing
const mockNextSection: BriefingSection = {
  section_type: 'quality',
  title: 'Quality Metrics',
  content: 'Quality rate is at 99.2%.',
  area_id: 'packaging',
  status: 'pending',
  pause_point: true,
};

describe('PauseCountdown', () => {
  const defaultProps: PauseCountdownProps = {
    countdown: 3,
    nextSection: mockNextSection,
    pausePrompt: 'Any questions on Production?',
    onContinue: vi.fn(),
    onAskQuestion: vi.fn(),
    overlay: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Countdown display (AC#2)', () => {
    it('renders countdown number', () => {
      render(<PauseCountdown {...defaultProps} />);

      expect(screen.getByText('3')).toBeInTheDocument();
    });

    it('shows next section name in message', () => {
      render(<PauseCountdown {...defaultProps} />);

      expect(screen.getByText(/Quality Metrics/)).toBeInTheDocument();
      expect(screen.getByText(/3 seconds/)).toBeInTheDocument();
    });

    it('uses singular "second" for countdown of 1', () => {
      render(<PauseCountdown {...defaultProps} countdown={1} />);

      expect(screen.getByText(/1 second\.\.\./)).toBeInTheDocument();
    });

    it('applies pulse animation when countdown is 1', () => {
      const { container } = render(<PauseCountdown {...defaultProps} countdown={1} />);

      const countdownNumber = container.querySelector('.animate-pulse');
      expect(countdownNumber).toBeInTheDocument();
    });

    it('shows completing message when no next section', () => {
      render(<PauseCountdown {...defaultProps} nextSection={undefined} />);

      expect(screen.getByText(/Completing briefing in 3 seconds/)).toBeInTheDocument();
    });
  });

  describe('Pause prompt display', () => {
    it('shows pause prompt when provided', () => {
      render(<PauseCountdown {...defaultProps} />);

      expect(screen.getByText('Any questions on Production?')).toBeInTheDocument();
    });

    it('does not show prompt when not provided', () => {
      render(<PauseCountdown {...defaultProps} pausePrompt={undefined} />);

      expect(screen.queryByText('Any questions on Production?')).not.toBeInTheDocument();
    });
  });

  describe('Continue button', () => {
    it('renders Continue Now button', () => {
      render(<PauseCountdown {...defaultProps} />);

      expect(screen.getByText('Continue Now')).toBeInTheDocument();
    });

    it('calls onContinue when Continue Now clicked', () => {
      const onContinue = vi.fn();
      render(<PauseCountdown {...defaultProps} onContinue={onContinue} />);

      fireEvent.click(screen.getByText('Continue Now'));

      expect(onContinue).toHaveBeenCalled();
    });
  });

  describe('Ask Question button', () => {
    it('renders Ask a Question button when handler provided', () => {
      render(<PauseCountdown {...defaultProps} />);

      expect(screen.getByText('Ask a Question')).toBeInTheDocument();
    });

    it('does not render Ask a Question button when handler not provided', () => {
      render(<PauseCountdown {...defaultProps} onAskQuestion={undefined} />);

      expect(screen.queryByText('Ask a Question')).not.toBeInTheDocument();
    });

    it('calls onAskQuestion when Ask a Question clicked', () => {
      const onAskQuestion = vi.fn();
      render(<PauseCountdown {...defaultProps} onAskQuestion={onAskQuestion} />);

      fireEvent.click(screen.getByText('Ask a Question'));

      expect(onAskQuestion).toHaveBeenCalled();
    });
  });

  describe('Hint text', () => {
    it('shows keyboard hint', () => {
      render(<PauseCountdown {...defaultProps} />);

      expect(screen.getByText(/Say "Continue" or press Space to proceed/)).toBeInTheDocument();
    });
  });

  describe('Progress ring', () => {
    it('renders SVG progress ring', () => {
      const { container } = render(<PauseCountdown {...defaultProps} />);

      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });

    it('renders progress circles', () => {
      const { container } = render(<PauseCountdown {...defaultProps} />);

      const circles = container.querySelectorAll('circle');
      expect(circles.length).toBeGreaterThanOrEqual(2); // At least background and progress circles
    });
  });

  describe('Overlay mode', () => {
    it('applies overlay styling when overlay is true', () => {
      const { container } = render(<PauseCountdown {...defaultProps} overlay={true} />);

      expect(container.firstChild).toHaveClass('fixed');
      expect(container.firstChild).toHaveClass('inset-0');
      expect(container.firstChild).toHaveClass('backdrop-blur-sm');
    });

    it('has dialog role in overlay mode', () => {
      render(<PauseCountdown {...defaultProps} overlay={true} />);

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByRole('dialog')).toHaveAttribute('aria-modal', 'true');
    });

    it('has alert role in inline mode', () => {
      render(<PauseCountdown {...defaultProps} overlay={false} />);

      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('applies correct button styling in overlay mode', () => {
      render(<PauseCountdown {...defaultProps} overlay={true} />);

      const continueButton = screen.getByText('Continue Now').closest('button');
      expect(continueButton).toHaveClass('bg-white');
    });

    it('applies correct button styling in inline mode', () => {
      render(<PauseCountdown {...defaultProps} overlay={false} />);

      // In inline mode, the button uses default variant styling
      const continueButton = screen.getByText('Continue Now').closest('button');
      expect(continueButton).toBeInTheDocument();
    });
  });

  describe('Inline mode', () => {
    it('applies inline styling when overlay is false', () => {
      const { container } = render(<PauseCountdown {...defaultProps} overlay={false} />);

      expect(container.firstChild).toHaveClass('bg-yellow-50');
      expect(container.firstChild).toHaveClass('border');
      expect(container.firstChild).toHaveClass('rounded-xl');
    });

    it('has aria-live polite for inline mode', () => {
      render(<PauseCountdown {...defaultProps} overlay={false} />);

      const alert = screen.getByRole('alert');
      expect(alert).toHaveAttribute('aria-live', 'polite');
    });
  });

  describe('Custom className', () => {
    it('applies custom className', () => {
      const { container } = render(
        <PauseCountdown {...defaultProps} className="custom-countdown-class" />
      );

      expect(container.firstChild).toHaveClass('custom-countdown-class');
    });
  });

  describe('Countdown values', () => {
    it('handles countdown of 4', () => {
      render(<PauseCountdown {...defaultProps} countdown={4} />);

      expect(screen.getByText('4')).toBeInTheDocument();
      expect(screen.getByText(/4 seconds/)).toBeInTheDocument();
    });

    it('handles countdown of 2', () => {
      render(<PauseCountdown {...defaultProps} countdown={2} />);

      expect(screen.getByText('2')).toBeInTheDocument();
      expect(screen.getByText(/2 seconds/)).toBeInTheDocument();
    });

    it('handles countdown of 0', () => {
      render(<PauseCountdown {...defaultProps} countdown={0} />);

      expect(screen.getByText('0')).toBeInTheDocument();
      expect(screen.getByText(/0 seconds/)).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper dialog labeling in overlay mode', () => {
      render(<PauseCountdown {...defaultProps} overlay={true} />);

      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-label', 'Pause countdown');
    });

    it('Continue Now button is focusable', () => {
      render(<PauseCountdown {...defaultProps} />);

      const button = screen.getByText('Continue Now').closest('button');
      expect(button).not.toBeDisabled();
    });

    it('Ask a Question button is focusable', () => {
      render(<PauseCountdown {...defaultProps} />);

      const button = screen.getByText('Ask a Question').closest('button');
      expect(button).not.toBeDisabled();
    });
  });

  describe('Text color in different modes', () => {
    it('uses light text in overlay mode', () => {
      render(<PauseCountdown {...defaultProps} overlay={true} />);

      // Pause prompt should have white text in overlay mode
      const promptText = screen.getByText('Any questions on Production?');
      expect(promptText).toHaveClass('text-white');
    });

    it('uses dark text in inline mode', () => {
      render(<PauseCountdown {...defaultProps} overlay={false} />);

      // Pause prompt should have dark text in inline mode
      const promptText = screen.getByText('Any questions on Production?');
      expect(promptText).toHaveClass('text-gray-700');
    });
  });
});
