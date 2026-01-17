/**
 * VoiceControls Component Tests (Story 8.7 Task 4.5)
 *
 * Tests for the VoiceControls component including:
 * - Play/Pause/Resume button functionality
 * - Skip to Next button (AC#3)
 * - End Briefing with confirmation (AC#4)
 * - Keyboard shortcuts (Task 4.4)
 * - Silence countdown display
 *
 * AC#3: Skip to Next functionality
 * AC#4: End Briefing with confirmation
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { VoiceControls, VoiceControlsProps } from '../VoiceControls';
import { BriefingSection, BriefingStatus } from '@/lib/hooks/useBriefing';

// Mock section for testing
const mockSection: BriefingSection = {
  section_type: 'production',
  title: 'Production Overview',
  content: 'Production is at 95% of target.',
  area_id: 'grinding',
  status: 'active',
  pause_point: true,
};

describe('VoiceControls', () => {
  const defaultProps: VoiceControlsProps = {
    status: 'playing' as BriefingStatus,
    currentSectionIndex: 1,
    totalSections: 5,
    currentSection: mockSection,
    silenceCountdown: null,
    onPlay: vi.fn(),
    onPause: vi.fn(),
    onNext: vi.fn(),
    onPrevious: vi.fn(),
    onEnd: vi.fn(),
    onContinue: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    // Clean up any keyboard event listeners
  });

  describe('Rendering', () => {
    it('renders status display', () => {
      render(<VoiceControls {...defaultProps} />);

      expect(screen.getByText('Production Overview')).toBeInTheDocument();
    });

    it('renders section counter', () => {
      render(<VoiceControls {...defaultProps} />);

      expect(screen.getByText('Section 2 of 5')).toBeInTheDocument();
    });

    it('renders progress bar', () => {
      const { container } = render(<VoiceControls {...defaultProps} />);

      const progressBar = container.querySelector('.voice-controls__progress');
      expect(progressBar).toBeInTheDocument();
    });

    it('renders section markers', () => {
      const { container } = render(<VoiceControls {...defaultProps} />);

      const markers = container.querySelectorAll('[title^="Section"]');
      expect(markers).toHaveLength(5);
    });
  });

  describe('Play/Pause button (AC#1)', () => {
    it('shows pause icon when playing', () => {
      render(<VoiceControls {...defaultProps} status="playing" />);

      expect(screen.getByLabelText('Pause')).toBeInTheDocument();
    });

    it('shows play icon when paused', () => {
      render(<VoiceControls {...defaultProps} status="paused" />);

      expect(screen.getByLabelText('Play')).toBeInTheDocument();
    });

    it('calls onPause when pause button clicked', () => {
      const onPause = vi.fn();
      render(<VoiceControls {...defaultProps} status="playing" onPause={onPause} />);

      fireEvent.click(screen.getByLabelText('Pause'));
      expect(onPause).toHaveBeenCalled();
    });

    it('calls onPlay when play button clicked', () => {
      const onPlay = vi.fn();
      render(<VoiceControls {...defaultProps} status="paused" onPlay={onPlay} />);

      fireEvent.click(screen.getByLabelText('Play'));
      expect(onPlay).toHaveBeenCalled();
    });

    it('shows loading spinner when loading', () => {
      const { container } = render(<VoiceControls {...defaultProps} status="loading" />);

      const spinner = container.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });

    it('disables play button when complete', () => {
      render(<VoiceControls {...defaultProps} status="complete" />);

      const playButton = screen.queryByLabelText('Play') || screen.queryByLabelText('Pause');
      expect(playButton).toBeDisabled();
    });
  });

  describe('Skip to Next button (AC#3)', () => {
    it('renders next button', () => {
      render(<VoiceControls {...defaultProps} />);

      expect(screen.getByLabelText('Next section')).toBeInTheDocument();
    });

    it('calls onNext when next button clicked', () => {
      const onNext = vi.fn();
      render(<VoiceControls {...defaultProps} onNext={onNext} />);

      fireEvent.click(screen.getByLabelText('Next section'));
      expect(onNext).toHaveBeenCalled();
    });

    it('disables next button on last section', () => {
      render(
        <VoiceControls
          {...defaultProps}
          currentSectionIndex={4}
          totalSections={5}
        />
      );

      expect(screen.getByLabelText('Next section')).toBeDisabled();
    });

    it('enables next button when not on last section', () => {
      render(<VoiceControls {...defaultProps} />);

      expect(screen.getByLabelText('Next section')).not.toBeDisabled();
    });
  });

  describe('Previous button', () => {
    it('renders previous button', () => {
      render(<VoiceControls {...defaultProps} />);

      expect(screen.getByLabelText('Previous section')).toBeInTheDocument();
    });

    it('calls onPrevious when previous button clicked', () => {
      const onPrevious = vi.fn();
      render(<VoiceControls {...defaultProps} onPrevious={onPrevious} />);

      fireEvent.click(screen.getByLabelText('Previous section'));
      expect(onPrevious).toHaveBeenCalled();
    });

    it('disables previous button on first section', () => {
      render(<VoiceControls {...defaultProps} currentSectionIndex={0} />);

      expect(screen.getByLabelText('Previous section')).toBeDisabled();
    });

    it('enables previous button when not on first section', () => {
      render(<VoiceControls {...defaultProps} />);

      expect(screen.getByLabelText('Previous section')).not.toBeDisabled();
    });
  });

  describe('End Briefing button (AC#4)', () => {
    it('renders end briefing button when not complete', () => {
      render(<VoiceControls {...defaultProps} />);

      expect(screen.getByLabelText('End briefing')).toBeInTheDocument();
    });

    it('hides end briefing button when complete', () => {
      render(<VoiceControls {...defaultProps} status="complete" />);

      expect(screen.queryByLabelText('End briefing')).not.toBeInTheDocument();
    });

    it('shows confirmation dialog when end briefing clicked', () => {
      render(<VoiceControls {...defaultProps} />);

      fireEvent.click(screen.getByLabelText('End briefing'));

      expect(screen.getByText('End Briefing?')).toBeInTheDocument();
      expect(screen.getByText(/You've completed 2 of 5 sections/)).toBeInTheDocument();
    });

    it('closes confirmation dialog when Continue Briefing clicked', () => {
      render(<VoiceControls {...defaultProps} />);

      fireEvent.click(screen.getByLabelText('End briefing'));
      fireEvent.click(screen.getByText('Continue Briefing'));

      expect(screen.queryByText('End Briefing?')).not.toBeInTheDocument();
    });

    it('calls onEnd when End Briefing confirmed', () => {
      const onEnd = vi.fn();
      render(<VoiceControls {...defaultProps} onEnd={onEnd} />);

      fireEvent.click(screen.getByLabelText('End briefing'));
      fireEvent.click(screen.getByRole('button', { name: 'End Briefing' }));

      expect(onEnd).toHaveBeenCalled();
    });
  });

  describe('Keyboard shortcuts (Task 4.4)', () => {
    it('pauses on Space when playing', () => {
      const onPause = vi.fn();
      render(<VoiceControls {...defaultProps} status="playing" onPause={onPause} />);

      fireEvent.keyDown(window, { key: ' ' });

      expect(onPause).toHaveBeenCalled();
    });

    it('plays on Space when paused', () => {
      const onPlay = vi.fn();
      render(<VoiceControls {...defaultProps} status="paused" onPlay={onPlay} />);

      fireEvent.keyDown(window, { key: ' ' });

      expect(onPlay).toHaveBeenCalled();
    });

    it('continues on Space when awaiting response', () => {
      const onContinue = vi.fn();
      render(
        <VoiceControls
          {...defaultProps}
          status="awaiting_response"
          onContinue={onContinue}
        />
      );

      fireEvent.keyDown(window, { key: ' ' });

      expect(onContinue).toHaveBeenCalled();
    });

    it('goes to next on ArrowRight', () => {
      const onNext = vi.fn();
      render(<VoiceControls {...defaultProps} onNext={onNext} />);

      fireEvent.keyDown(window, { key: 'ArrowRight' });

      expect(onNext).toHaveBeenCalled();
    });

    it('goes to previous on ArrowLeft', () => {
      const onPrevious = vi.fn();
      render(<VoiceControls {...defaultProps} onPrevious={onPrevious} />);

      fireEvent.keyDown(window, { key: 'ArrowLeft' });

      expect(onPrevious).toHaveBeenCalled();
    });

    it('closes confirmation dialog on Escape', () => {
      render(<VoiceControls {...defaultProps} />);

      fireEvent.click(screen.getByLabelText('End briefing'));
      expect(screen.getByText('End Briefing?')).toBeInTheDocument();

      fireEvent.keyDown(window, { key: 'Escape' });

      expect(screen.queryByText('End Briefing?')).not.toBeInTheDocument();
    });

    it('disables keyboard shortcuts when enableKeyboardShortcuts is false', () => {
      const onPause = vi.fn();
      render(
        <VoiceControls
          {...defaultProps}
          status="playing"
          onPause={onPause}
          enableKeyboardShortcuts={false}
        />
      );

      fireEvent.keyDown(window, { key: ' ' });

      expect(onPause).not.toHaveBeenCalled();
    });

    it('does not trigger shortcuts when typing in input', () => {
      const onPause = vi.fn();
      render(<VoiceControls {...defaultProps} status="playing" onPause={onPause} />);

      // Simulate keydown on an input element
      const inputEvent = new KeyboardEvent('keydown', {
        key: ' ',
        bubbles: true,
      });
      Object.defineProperty(inputEvent, 'target', {
        value: document.createElement('input'),
      });
      window.dispatchEvent(inputEvent);

      expect(onPause).not.toHaveBeenCalled();
    });
  });

  describe('Silence countdown display (AC#2)', () => {
    it('shows countdown when silenceCountdown is set', () => {
      render(
        <VoiceControls
          {...defaultProps}
          status="awaiting_response"
          silenceCountdown={3}
        />
      );

      expect(screen.getByText('Auto-continuing in 3 seconds...')).toBeInTheDocument();
    });

    it('shows continue now button during countdown', () => {
      render(
        <VoiceControls
          {...defaultProps}
          status="awaiting_response"
          silenceCountdown={3}
        />
      );

      expect(screen.getByText('Continue now')).toBeInTheDocument();
    });

    it('calls onContinue when Continue now clicked', () => {
      const onContinue = vi.fn();
      render(
        <VoiceControls
          {...defaultProps}
          status="awaiting_response"
          silenceCountdown={3}
          onContinue={onContinue}
        />
      );

      fireEvent.click(screen.getByText('Continue now'));

      expect(onContinue).toHaveBeenCalled();
    });

    it('does not show countdown when not awaiting response', () => {
      render(
        <VoiceControls
          {...defaultProps}
          status="playing"
          silenceCountdown={3}
        />
      );

      expect(screen.queryByText(/Auto-continuing in/)).not.toBeInTheDocument();
    });
  });

  describe('Continue button in awaiting_response mode', () => {
    it('shows continue button when awaiting response', () => {
      render(<VoiceControls {...defaultProps} status="awaiting_response" />);

      expect(screen.getByLabelText('Continue to next section')).toBeInTheDocument();
    });

    it('calls onContinue when continue button clicked', () => {
      const onContinue = vi.fn();
      render(
        <VoiceControls
          {...defaultProps}
          status="awaiting_response"
          onContinue={onContinue}
        />
      );

      fireEvent.click(screen.getByLabelText('Continue to next section'));

      expect(onContinue).toHaveBeenCalled();
    });
  });

  describe('Status text', () => {
    it('shows "Preparing briefing..." when loading', () => {
      render(<VoiceControls {...defaultProps} status="loading" />);

      expect(screen.getByText('Preparing briefing...')).toBeInTheDocument();
    });

    it('shows current section title when playing', () => {
      render(<VoiceControls {...defaultProps} status="playing" />);

      expect(screen.getByText('Production Overview')).toBeInTheDocument();
    });

    it('shows "Paused" when paused', () => {
      render(<VoiceControls {...defaultProps} status="paused" />);

      expect(screen.getByText('Paused')).toBeInTheDocument();
    });

    it('shows countdown message when awaiting with countdown', () => {
      render(
        <VoiceControls
          {...defaultProps}
          status="awaiting_response"
          silenceCountdown={3}
        />
      );

      expect(screen.getByText('Continuing in 3s...')).toBeInTheDocument();
    });

    it('shows question prompt when awaiting without countdown', () => {
      render(
        <VoiceControls
          {...defaultProps}
          status="awaiting_response"
          silenceCountdown={null}
        />
      );

      expect(screen.getByText('Ask a question or say "Continue"')).toBeInTheDocument();
    });

    it('shows "Processing question..." when in QA mode', () => {
      render(<VoiceControls {...defaultProps} status="qa" />);

      expect(screen.getByText('Processing question...')).toBeInTheDocument();
    });

    it('shows "Briefing complete" when complete', () => {
      render(<VoiceControls {...defaultProps} status="complete" />);

      expect(screen.getByText('Briefing complete')).toBeInTheDocument();
    });

    it('shows "Error occurred" when error', () => {
      render(<VoiceControls {...defaultProps} status="error" />);

      expect(screen.getByText('Error occurred')).toBeInTheDocument();
    });
  });

  describe('Completion message', () => {
    it('shows completion message when status is complete', () => {
      render(<VoiceControls {...defaultProps} status="complete" />);

      expect(screen.getByText('Morning briefing complete')).toBeInTheDocument();
    });
  });

  describe('Keyboard shortcut hints', () => {
    it('shows shortcut hints when showShortcutHints is true', () => {
      render(<VoiceControls {...defaultProps} showShortcutHints={true} />);

      expect(screen.getByText('Pause/Play')).toBeInTheDocument();
      expect(screen.getByText('Skip')).toBeInTheDocument();
      expect(screen.getByText('Previous')).toBeInTheDocument();
    });

    it('hides shortcut hints when showShortcutHints is false', () => {
      render(<VoiceControls {...defaultProps} showShortcutHints={false} />);

      expect(screen.queryByText('Pause/Play')).not.toBeInTheDocument();
    });

    it('hides shortcut hints when complete', () => {
      render(<VoiceControls {...defaultProps} status="complete" showShortcutHints={true} />);

      expect(screen.queryByText('Pause/Play')).not.toBeInTheDocument();
    });
  });

  describe('Custom className', () => {
    it('applies custom className', () => {
      const { container } = render(
        <VoiceControls {...defaultProps} className="custom-controls-class" />
      );

      expect(container.firstChild).toHaveClass('custom-controls-class');
    });
  });

  describe('Compact mode', () => {
    it('applies compact class when compact is true', () => {
      const { container } = render(<VoiceControls {...defaultProps} compact={true} />);

      expect(container.firstChild).toHaveClass('voice-controls--compact');
    });
  });

  describe('Accessibility', () => {
    it('has accessible play/pause button', () => {
      render(<VoiceControls {...defaultProps} />);

      expect(screen.getByLabelText('Pause')).toBeInTheDocument();
    });

    it('has accessible next button', () => {
      render(<VoiceControls {...defaultProps} />);

      expect(screen.getByLabelText('Next section')).toBeInTheDocument();
    });

    it('has accessible previous button', () => {
      render(<VoiceControls {...defaultProps} />);

      expect(screen.getByLabelText('Previous section')).toBeInTheDocument();
    });

    it('has accessible end briefing button', () => {
      render(<VoiceControls {...defaultProps} />);

      expect(screen.getByLabelText('End briefing')).toBeInTheDocument();
    });

    it('confirmation dialog has proper role', () => {
      render(<VoiceControls {...defaultProps} />);

      fireEvent.click(screen.getByLabelText('End briefing'));

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByRole('dialog')).toHaveAttribute('aria-modal', 'true');
    });
  });
});
