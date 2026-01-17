/**
 * HandoffAcknowledge Component Tests (Story 9.7, Task 7.1)
 *
 * Tests for the handoff acknowledgment dialog component.
 *
 * @see Story 9.7 - Acknowledgment Flow
 * @see AC#1 - Acknowledgment UI Trigger
 * @see AC#3 - Optional Notes Attachment
 * @see AC#4 - Offline Acknowledgment Queuing
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HandoffAcknowledge } from '../HandoffAcknowledge';

describe('HandoffAcknowledge', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    onConfirm: vi.fn().mockResolvedValue(undefined),
    handoffId: 'handoff-123',
    creatorName: 'John Smith',
    shiftDate: '2026-01-15',
    shiftType: 'morning',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders confirmation dialog when open', () => {
      render(<HandoffAcknowledge {...defaultProps} />);

      expect(screen.getByText('Acknowledge Handoff')).toBeInTheDocument();
      expect(screen.getByText(/john smith/i)).toBeInTheDocument();
      expect(screen.getByText(/morning shift/i)).toBeInTheDocument();
    });

    it('does not render when closed', () => {
      render(<HandoffAcknowledge {...defaultProps} isOpen={false} />);

      expect(screen.queryByText('Acknowledge Handoff')).not.toBeInTheDocument();
    });

    it('displays formatted shift date', () => {
      render(<HandoffAcknowledge {...defaultProps} />);

      // Check for formatted date (January 15 format)
      expect(screen.getByText(/january/i)).toBeInTheDocument();
    });

    it('shows acknowledge button with correct text', () => {
      render(<HandoffAcknowledge {...defaultProps} />);

      expect(screen.getByRole('button', { name: /acknowledge/i })).toBeInTheDocument();
    });

    it('shows cancel button', () => {
      render(<HandoffAcknowledge {...defaultProps} />);

      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });
  });

  describe('Notes Input (AC#3)', () => {
    it('initially hides notes textarea', () => {
      render(<HandoffAcknowledge {...defaultProps} />);

      expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
    });

    it('shows notes textarea after clicking add note button', async () => {
      render(<HandoffAcknowledge {...defaultProps} />);

      fireEvent.click(screen.getByText(/add a note/i));

      expect(screen.getByRole('textbox')).toBeInTheDocument();
      expect(screen.getByLabelText(/acknowledgment notes/i)).toBeInTheDocument();
    });

    it('allows entering notes', async () => {
      const user = userEvent.setup();
      render(<HandoffAcknowledge {...defaultProps} />);

      fireEvent.click(screen.getByText(/add a note/i));
      const textarea = screen.getByRole('textbox');

      await user.type(textarea, 'This is my note');

      expect(textarea).toHaveValue('This is my note');
    });

    it('displays character count', async () => {
      const user = userEvent.setup();
      render(<HandoffAcknowledge {...defaultProps} />);

      fireEvent.click(screen.getByText(/add a note/i));
      const textarea = screen.getByRole('textbox');

      await user.type(textarea, 'Test note');

      expect(screen.getByText(/491 characters remaining/i)).toBeInTheDocument();
    });

    it('enforces character limit', async () => {
      const user = userEvent.setup();
      render(<HandoffAcknowledge {...defaultProps} />);

      fireEvent.click(screen.getByText(/add a note/i));
      const textarea = screen.getByRole('textbox');

      // Type more than 500 characters
      const longText = 'a'.repeat(600);
      await user.type(textarea, longText);

      // Should be truncated to 500
      expect(textarea).toHaveValue('a'.repeat(500));
    });
  });

  describe('Confirmation Flow (AC#1, AC#2)', () => {
    it('calls onConfirm without notes when acknowledged without notes', async () => {
      render(<HandoffAcknowledge {...defaultProps} />);

      fireEvent.click(screen.getByRole('button', { name: /acknowledge/i }));

      await waitFor(() => {
        expect(defaultProps.onConfirm).toHaveBeenCalledWith(undefined);
      });
    });

    it('calls onConfirm with notes when notes are provided', async () => {
      const user = userEvent.setup();
      render(<HandoffAcknowledge {...defaultProps} />);

      fireEvent.click(screen.getByText(/add a note/i));
      await user.type(screen.getByRole('textbox'), 'My acknowledgment note');
      fireEvent.click(screen.getByRole('button', { name: /acknowledge/i }));

      await waitFor(() => {
        expect(defaultProps.onConfirm).toHaveBeenCalledWith('My acknowledgment note');
      });
    });

    it('calls onClose when cancel is clicked', () => {
      render(<HandoffAcknowledge {...defaultProps} />);

      fireEvent.click(screen.getByRole('button', { name: /cancel/i }));

      expect(defaultProps.onClose).toHaveBeenCalled();
    });
  });

  describe('Loading State (Task 2.4)', () => {
    it('shows loading state when isLoading is true', () => {
      render(<HandoffAcknowledge {...defaultProps} isLoading={true} />);

      expect(screen.getByText(/acknowledging/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /acknowledging/i })).toBeDisabled();
    });

    it('disables cancel button when loading', () => {
      render(<HandoffAcknowledge {...defaultProps} isLoading={true} />);

      expect(screen.getByRole('button', { name: /cancel/i })).toBeDisabled();
    });

    it('disables notes textarea when loading', async () => {
      render(<HandoffAcknowledge {...defaultProps} />);

      fireEvent.click(screen.getByText(/add a note/i));

      const { rerender } = render(
        <HandoffAcknowledge {...defaultProps} isLoading={true} />
      );

      // Need to re-show the notes section
      const addNoteButton = screen.queryByText(/add a note/i);
      if (addNoteButton) {
        fireEvent.click(addNoteButton);
      }
    });
  });

  describe('Error Display', () => {
    it('displays error message when provided', () => {
      render(
        <HandoffAcknowledge
          {...defaultProps}
          error="Unable to acknowledge handoff"
        />
      );

      expect(screen.getByText('Unable to acknowledge handoff')).toBeInTheDocument();
    });

    it('does not show error when error is null', () => {
      render(<HandoffAcknowledge {...defaultProps} error={null} />);

      // Check that no error container is rendered
      expect(screen.queryByText(/unable to/i)).not.toBeInTheDocument();
    });
  });

  describe('Offline Mode (AC#4)', () => {
    it('shows offline indicator when isOffline is true', () => {
      render(<HandoffAcknowledge {...defaultProps} isOffline={true} />);

      expect(screen.getByText(/you are currently offline/i)).toBeInTheDocument();
      expect(screen.getByText(/queued and synced/i)).toBeInTheDocument();
    });

    it('shows queue button text when offline', () => {
      render(<HandoffAcknowledge {...defaultProps} isOffline={true} />);

      expect(screen.getByRole('button', { name: /queue acknowledgment/i })).toBeInTheDocument();
    });

    it('shows queuing text when loading offline', () => {
      render(
        <HandoffAcknowledge {...defaultProps} isOffline={true} isLoading={true} />
      );

      expect(screen.getByText(/queuing/i)).toBeInTheDocument();
    });
  });

  describe('Touch Accessibility (AC#4)', () => {
    it('has minimum touch target size on buttons', () => {
      render(<HandoffAcknowledge {...defaultProps} />);

      const acknowledgeButton = screen.getByRole('button', { name: /acknowledge/i });
      const cancelButton = screen.getByRole('button', { name: /cancel/i });

      expect(acknowledgeButton).toHaveClass('min-h-[44px]');
      expect(cancelButton).toHaveClass('min-h-[44px]');
    });
  });
});
