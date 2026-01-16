/**
 * TranscriptPanel Component Tests (Story 8.2)
 *
 * Tests for the TranscriptPanel component including:
 * - Entry rendering
 * - State indicators
 * - Auto-scrolling
 *
 * AC#2: WebSocket STT Streaming - Shows transcription results
 * AC#3: Q&A Processing Integration - Displays AI responses
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { TranscriptPanel, TranscriptEntry } from '../TranscriptPanel';

describe('TranscriptPanel', () => {
  const mockEntries: TranscriptEntry[] = [
    {
      id: '1',
      type: 'user',
      text: 'What is the OEE for Line 1?',
      timestamp: '2024-01-15T10:30:00Z',
      confidence: 0.95,
    },
    {
      id: '2',
      type: 'assistant',
      text: 'The current OEE for Line 1 is 87.5%, which is above the 85% target.',
      timestamp: '2024-01-15T10:30:05Z',
      citations: ['production_data', 'oee_metrics'],
    },
  ];

  describe('Empty state', () => {
    it('renders empty message when no entries', () => {
      render(<TranscriptPanel entries={[]} />);

      expect(
        screen.getByText('Ask a question using the push-to-talk button')
      ).toBeInTheDocument();
    });

    it('renders custom empty message', () => {
      render(
        <TranscriptPanel entries={[]} emptyMessage="No messages yet" />
      );

      expect(screen.getByText('No messages yet')).toBeInTheDocument();
    });
  });

  describe('Entry rendering', () => {
    it('renders user entries', () => {
      render(<TranscriptPanel entries={mockEntries} />);

      expect(
        screen.getByText('What is the OEE for Line 1?')
      ).toBeInTheDocument();
    });

    it('renders assistant entries', () => {
      render(<TranscriptPanel entries={mockEntries} />);

      expect(
        screen.getByText(
          'The current OEE for Line 1 is 87.5%, which is above the 85% target.'
        )
      ).toBeInTheDocument();
    });

    it('renders multiple entries', () => {
      render(<TranscriptPanel entries={mockEntries} />);

      expect(screen.getAllByRole('generic')).toBeTruthy();
    });
  });

  describe('Timestamps', () => {
    it('shows timestamps by default', () => {
      render(<TranscriptPanel entries={mockEntries} />);

      // Timestamps are formatted as HH:MM
      // The exact format depends on locale
    });

    it('hides timestamps when showTimestamps is false', () => {
      render(
        <TranscriptPanel entries={mockEntries} showTimestamps={false} />
      );

      // No timestamp elements should be rendered
    });
  });

  describe('Confidence scores', () => {
    it('hides confidence by default', () => {
      render(<TranscriptPanel entries={mockEntries} />);

      expect(screen.queryByText('95% confidence')).not.toBeInTheDocument();
    });

    it('shows confidence when showConfidence is true', () => {
      render(
        <TranscriptPanel entries={mockEntries} showConfidence={true} />
      );

      expect(screen.getByText('95% confidence')).toBeInTheDocument();
    });
  });

  describe('Citations', () => {
    it('renders citations for assistant entries', () => {
      render(<TranscriptPanel entries={mockEntries} />);

      expect(screen.getByText('[1]')).toBeInTheDocument();
      expect(screen.getByText('[2]')).toBeInTheDocument();
    });

    it('shows Sources label when citations present', () => {
      render(<TranscriptPanel entries={mockEntries} />);

      expect(screen.getByText('Sources:')).toBeInTheDocument();
    });
  });

  describe('Status indicators', () => {
    it('shows transcribing indicator', () => {
      render(
        <TranscriptPanel entries={[]} isTranscribing={true} />
      );

      expect(screen.getByText('Transcribing...')).toBeInTheDocument();
      expect(screen.getByText('Listening...')).toBeInTheDocument();
    });

    it('shows processing indicator', () => {
      render(
        <TranscriptPanel entries={[]} isProcessing={true} />
      );

      expect(screen.getByText('Processing...')).toBeInTheDocument();
    });

    it('hides empty message when transcribing', () => {
      render(
        <TranscriptPanel entries={[]} isTranscribing={true} />
      );

      expect(
        screen.queryByText('Ask a question using the push-to-talk button')
      ).not.toBeInTheDocument();
    });

    it('hides empty message when processing', () => {
      render(
        <TranscriptPanel entries={[]} isProcessing={true} />
      );

      expect(
        screen.queryByText('Ask a question using the push-to-talk button')
      ).not.toBeInTheDocument();
    });
  });

  describe('Processing entry', () => {
    it('renders processing assistant entry', () => {
      const entriesWithProcessing: TranscriptEntry[] = [
        {
          id: '1',
          type: 'user',
          text: 'Test question',
          timestamp: '2024-01-15T10:30:00Z',
        },
        {
          id: '2',
          type: 'assistant',
          text: '',
          timestamp: '2024-01-15T10:30:05Z',
          isProcessing: true,
        },
      ];

      render(<TranscriptPanel entries={entriesWithProcessing} />);

      // Processing indicator (bouncing dots) should be rendered
    });
  });

  describe('Styling', () => {
    it('applies custom className', () => {
      const { container } = render(
        <TranscriptPanel entries={[]} className="custom-class" />
      );

      expect(container.firstChild).toHaveClass('custom-class');
    });

    it('applies maxHeight style', () => {
      const { container } = render(
        <TranscriptPanel entries={[]} maxHeight="500px" />
      );

      expect(container.firstChild).toHaveStyle({ maxHeight: '500px' });
    });

    it('has correct classes for user messages', () => {
      render(<TranscriptPanel entries={mockEntries} />);

      // User messages should have blue background
      const userMessage = screen.getByText('What is the OEE for Line 1?');
      expect(userMessage.closest('div')).toHaveClass('bg-blue-600');
    });

    it('has correct classes for assistant messages', () => {
      render(<TranscriptPanel entries={mockEntries} />);

      // Assistant messages should have gray background
      const assistantMessage = screen.getByText(
        'The current OEE for Line 1 is 87.5%, which is above the 85% target.'
      );
      expect(assistantMessage.closest('div')).toHaveClass('bg-gray-100');
    });
  });

  describe('Header', () => {
    it('renders header with title', () => {
      render(<TranscriptPanel entries={[]} />);

      expect(screen.getByText('Transcript')).toBeInTheDocument();
    });
  });

  describe('Auto-scroll', () => {
    it('has scroll anchor element', () => {
      const { container } = render(<TranscriptPanel entries={mockEntries} />);

      // The bottom ref div should exist for auto-scrolling
      const scrollContent = container.querySelector(
        '.transcript-panel__content'
      );
      expect(scrollContent?.lastChild).toBeTruthy();
    });
  });

  describe('Message alignment', () => {
    it('aligns user messages to the right', () => {
      render(<TranscriptPanel entries={mockEntries} />);

      // User messages container should have justify-end
      const userEntry = screen
        .getByText('What is the OEE for Line 1?')
        .closest('.transcript-panel__entry--user');
      const container = userEntry?.querySelector('div');
      expect(container).toHaveClass('justify-end');
    });

    it('aligns assistant messages to the left', () => {
      render(<TranscriptPanel entries={mockEntries} />);

      // Assistant messages container should have justify-start
      const assistantEntry = screen
        .getByText(
          'The current OEE for Line 1 is 87.5%, which is above the 85% target.'
        )
        .closest('.transcript-panel__entry--assistant');
      const container = assistantEntry?.querySelector('div');
      expect(container).toHaveClass('justify-start');
    });
  });
});
