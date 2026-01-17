/**
 * Tests for HandoffQA Component (Story 9.6)
 *
 * Tests the Q&A interface for shift handoffs.
 *
 * @see Story 9.6 - Handoff Q&A
 * @see AC#1 - Text/voice input for questions
 * @see AC#2 - AI responses with citations
 * @see AC#4 - Preserved Q&A thread
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HandoffQA } from '../HandoffQA';
import { useHandoffQA } from '@/lib/hooks/useHandoffQA';

// Mock the useHandoffQA hook
jest.mock('@/lib/hooks/useHandoffQA', () => ({
  useHandoffQA: jest.fn(),
}));

const mockUseHandoffQA = useHandoffQA as jest.Mock;

describe('HandoffQA', () => {
  const defaultState = {
    thread: null,
    isLoading: false,
    isSubmitting: false,
    error: null,
    hasNewEntry: false,
  };

  const defaultActions = {
    submitQuestion: jest.fn(),
    submitResponse: jest.fn(),
    refreshThread: jest.fn(),
    clearError: jest.fn(),
    acknowledgeNewEntry: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseHandoffQA.mockReturnValue([defaultState, defaultActions]);
  });

  describe('Rendering', () => {
    it('renders the Q&A component with title', () => {
      render(<HandoffQA handoffId="test-id" />);

      expect(screen.getByText('Questions & Answers')).toBeInTheDocument();
    });

    it('shows empty state when no Q&A entries', () => {
      mockUseHandoffQA.mockReturnValue([
        { ...defaultState, thread: { entries: [], count: 0 } },
        defaultActions,
      ]);

      render(<HandoffQA handoffId="test-id" />);

      expect(screen.getByText('No questions yet.')).toBeInTheDocument();
    });

    it('shows loading state', () => {
      mockUseHandoffQA.mockReturnValue([
        { ...defaultState, isLoading: true },
        defaultActions,
      ]);

      render(<HandoffQA handoffId="test-id" />);

      // Loading spinner should be present
      expect(document.querySelector('.animate-spin')).toBeInTheDocument();
    });

    it('shows error state with dismiss button', () => {
      mockUseHandoffQA.mockReturnValue([
        { ...defaultState, error: 'Failed to load Q&A' },
        defaultActions,
      ]);

      render(<HandoffQA handoffId="test-id" />);

      expect(screen.getByText('Failed to load Q&A')).toBeInTheDocument();
      expect(screen.getByText('Dismiss')).toBeInTheDocument();
    });
  });

  describe('Q&A Thread Display', () => {
    const mockThread = {
      handoff_id: 'test-id',
      entries: [
        {
          id: 'q1',
          handoff_id: 'test-id',
          user_id: 'user1',
          user_name: 'Test User',
          content_type: 'question',
          content: 'Why was there downtime?',
          citations: [],
          created_at: '2026-01-16T10:00:00Z',
        },
        {
          id: 'a1',
          handoff_id: 'test-id',
          user_id: 'system',
          user_name: 'AI Assistant',
          content_type: 'ai_answer',
          content: 'The downtime was due to scheduled maintenance.',
          citations: [
            {
              value: '2.5 hours',
              field: 'downtime_analysis',
              table: 'daily_summaries',
              context: 'Grinder 5',
            },
          ],
          created_at: '2026-01-16T10:00:05Z',
        },
      ],
      count: 2,
    };

    it('displays Q&A entries from thread', () => {
      mockUseHandoffQA.mockReturnValue([
        { ...defaultState, thread: mockThread },
        defaultActions,
      ]);

      render(<HandoffQA handoffId="test-id" />);

      expect(screen.getByText('Why was there downtime?')).toBeInTheDocument();
      expect(
        screen.getByText('The downtime was due to scheduled maintenance.')
      ).toBeInTheDocument();
    });

    it('displays entry count badge', () => {
      mockUseHandoffQA.mockReturnValue([
        { ...defaultState, thread: mockThread },
        defaultActions,
      ]);

      render(<HandoffQA handoffId="test-id" />);

      expect(screen.getByText('2')).toBeInTheDocument();
    });

    it('displays citations for AI responses', () => {
      mockUseHandoffQA.mockReturnValue([
        { ...defaultState, thread: mockThread },
        defaultActions,
      ]);

      render(<HandoffQA handoffId="test-id" />);

      expect(screen.getByText('2.5 hours')).toBeInTheDocument();
    });

    it('differentiates between user and AI messages', () => {
      mockUseHandoffQA.mockReturnValue([
        { ...defaultState, thread: mockThread },
        defaultActions,
      ]);

      render(<HandoffQA handoffId="test-id" />);

      expect(screen.getByText('Test User')).toBeInTheDocument();
      expect(screen.getByText('AI Assistant')).toBeInTheDocument();
    });
  });

  describe('Question Submission', () => {
    it('allows typing a question', async () => {
      const user = userEvent.setup();

      render(<HandoffQA handoffId="test-id" />);

      const input = screen.getByPlaceholderText(
        'Ask a question about this handoff...'
      );
      await user.type(input, 'Test question');

      expect(input).toHaveValue('Test question');
    });

    it('calls submitQuestion when form is submitted', async () => {
      const user = userEvent.setup();
      const mockSubmit = jest.fn().mockResolvedValue(undefined);

      mockUseHandoffQA.mockReturnValue([
        defaultState,
        { ...defaultActions, submitQuestion: mockSubmit },
      ]);

      render(<HandoffQA handoffId="test-id" />);

      const input = screen.getByPlaceholderText(
        'Ask a question about this handoff...'
      );
      await user.type(input, 'Why was production down?');

      const submitButton = screen.getByRole('button', { name: 'Send question' });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockSubmit).toHaveBeenCalledWith(
          'Why was production down?',
          undefined
        );
      });
    });

    it('disables submit button when input is empty', () => {
      render(<HandoffQA handoffId="test-id" />);

      const submitButton = screen.getByRole('button', { name: 'Send question' });
      expect(submitButton).toBeDisabled();
    });

    it('shows loading state during submission', () => {
      mockUseHandoffQA.mockReturnValue([
        { ...defaultState, isSubmitting: true },
        defaultActions,
      ]);

      render(<HandoffQA handoffId="test-id" />);

      expect(screen.getByText('Processing your question...')).toBeInTheDocument();
    });
  });

  describe('Push-to-Talk Integration', () => {
    it('renders push-to-talk button when onPushToTalk provided', () => {
      const mockPushToTalk = jest.fn();

      render(
        <HandoffQA handoffId="test-id" onPushToTalk={mockPushToTalk} />
      );

      const micButton = screen.getByRole('button', { name: 'Start recording' });
      expect(micButton).toBeInTheDocument();
    });

    it('does not render push-to-talk when not provided', () => {
      render(<HandoffQA handoffId="test-id" />);

      expect(
        screen.queryByRole('button', { name: 'Start recording' })
      ).not.toBeInTheDocument();
    });

    it('calls onPushToTalk when mic button clicked', async () => {
      const user = userEvent.setup();
      const mockPushToTalk = jest.fn();

      render(
        <HandoffQA handoffId="test-id" onPushToTalk={mockPushToTalk} />
      );

      const micButton = screen.getByRole('button', { name: 'Start recording' });
      await user.click(micButton);

      expect(mockPushToTalk).toHaveBeenCalled();
    });

    it('updates input when voice transcript changes', () => {
      const { rerender } = render(
        <HandoffQA
          handoffId="test-id"
          voiceTranscript=""
        />
      );

      rerender(
        <HandoffQA
          handoffId="test-id"
          voiceTranscript="spoken question here"
        />
      );

      const input = screen.getByPlaceholderText(
        'Ask a question about this handoff...'
      );
      expect(input).toHaveValue('spoken question here');
    });
  });

  describe('Refresh and Error Handling', () => {
    it('calls refreshThread when refresh button clicked', async () => {
      const user = userEvent.setup();
      const mockRefresh = jest.fn().mockResolvedValue(undefined);

      mockUseHandoffQA.mockReturnValue([
        defaultState,
        { ...defaultActions, refreshThread: mockRefresh },
      ]);

      render(<HandoffQA handoffId="test-id" />);

      const refreshButton = screen.getByRole('button', {
        name: 'Refresh Q&A thread',
      });
      await user.click(refreshButton);

      expect(mockRefresh).toHaveBeenCalled();
    });

    it('calls clearError when dismiss clicked', async () => {
      const user = userEvent.setup();
      const mockClearError = jest.fn();

      mockUseHandoffQA.mockReturnValue([
        { ...defaultState, error: 'Some error' },
        { ...defaultActions, clearError: mockClearError },
      ]);

      render(<HandoffQA handoffId="test-id" />);

      const dismissButton = screen.getByText('Dismiss');
      await user.click(dismissButton);

      expect(mockClearError).toHaveBeenCalled();
    });
  });

  describe('Creator vs Incoming Supervisor', () => {
    it('shows appropriate placeholder for creator', () => {
      render(<HandoffQA handoffId="test-id" isCreator={true} />);

      expect(
        screen.getByPlaceholderText('Type your response...')
      ).toBeInTheDocument();
    });

    it('shows appropriate placeholder for incoming supervisor', () => {
      render(<HandoffQA handoffId="test-id" isCreator={false} />);

      expect(
        screen.getByPlaceholderText('Ask a question about this handoff...')
      ).toBeInTheDocument();
    });
  });
});
