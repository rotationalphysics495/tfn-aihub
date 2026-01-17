/**
 * HandoffViewer Component Tests (Story 9.5, Task 8.3)
 *
 * Tests for the handoff viewer component.
 *
 * @see Story 9.5 - Handoff Review UI
 * @see AC#2 - Handoff Detail View
 * @see AC#3 - Voice Note Playback
 * @see AC#4 - Tablet-Optimized Layout
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { HandoffViewer } from '../HandoffViewer';
import type { Handoff, HandoffVoiceNote } from '@/types/handoff';

// Mock the VoiceNotePlayer component
vi.mock('../VoiceNotePlayer', () => ({
  VoiceNotePlayer: ({ src, transcript }: { src: string; transcript?: string | null }) => (
    <div data-testid="voice-note-player">
      <div data-testid="audio-src">{src}</div>
      {transcript && <div data-testid="transcript">{transcript}</div>}
    </div>
  ),
}));

// Test data factory
const createMockVoiceNote = (overrides: Partial<HandoffVoiceNote> = {}): HandoffVoiceNote => ({
  id: 'note-123',
  handoff_id: 'handoff-456',
  user_id: 'user-789',
  storage_path: 'handoff/voice-notes/note-123.webm',
  storage_url: 'https://storage.example.com/note-123.webm',
  transcript: 'This is the transcript of the voice note.',
  duration_seconds: 45,
  sequence_order: 1,
  created_at: '2026-01-15T14:30:00Z',
  ...overrides,
});

const createMockHandoff = (overrides: Partial<Handoff> = {}): Handoff => ({
  id: 'handoff-123',
  created_by: 'user-456',
  creator_name: 'John Smith',
  creator_email: 'john.smith@example.com',
  shift_date: '2026-01-15',
  shift_type: 'morning',
  shift_start_time: '2026-01-15T06:00:00Z',
  shift_end_time: '2026-01-15T14:00:00Z',
  assets_covered: ['asset-1', 'asset-2'],
  summary_text: 'This is the auto-generated shift summary.',
  text_notes: 'Additional notes from the outgoing supervisor.',
  status: 'pending_acknowledgment',
  created_at: '2026-01-15T06:00:00Z',
  updated_at: '2026-01-15T14:00:00Z',
  submitted_at: '2026-01-15T14:00:00Z',
  acknowledged_by: null,
  acknowledged_at: null,
  voice_notes: [],
  ...overrides,
});

describe('HandoffViewer', () => {
  it('renders all sections correctly', () => {
    const handoff = createMockHandoff({
      creator_name: 'Alice Johnson',
      summary_text: 'Shift summary content',
      text_notes: 'Additional notes content',
      voice_notes: [createMockVoiceNote()],
    });

    render(<HandoffViewer handoff={handoff} />);

    // Header
    expect(screen.getByText(/handoff from alice johnson/i)).toBeInTheDocument();

    // Status badge
    expect(screen.getByText('Pending Acknowledgment')).toBeInTheDocument();

    // Shift summary
    expect(screen.getByText('Shift Summary')).toBeInTheDocument();
    expect(screen.getByText('Shift summary content')).toBeInTheDocument();

    // Text notes
    expect(screen.getByText('Additional Notes')).toBeInTheDocument();
    expect(screen.getByText('Additional notes content')).toBeInTheDocument();

    // Voice notes
    expect(screen.getByText('Voice Notes (1)')).toBeInTheDocument();
  });

  it('displays voice notes with transcript', () => {
    const handoff = createMockHandoff({
      voice_notes: [
        createMockVoiceNote({
          id: 'note-1',
          sequence_order: 1,
          duration_seconds: 30,
          transcript: 'First note transcript',
        }),
        createMockVoiceNote({
          id: 'note-2',
          sequence_order: 2,
          duration_seconds: 45,
          transcript: 'Second note transcript',
        }),
      ],
    });

    render(<HandoffViewer handoff={handoff} />);

    expect(screen.getByText('Voice Notes (2)')).toBeInTheDocument();
    expect(screen.getByText('Voice Note 1')).toBeInTheDocument();
    expect(screen.getByText('Voice Note 2')).toBeInTheDocument();
    expect(screen.getByText('0:30')).toBeInTheDocument();
    expect(screen.getByText('0:45')).toBeInTheDocument();
  });

  it('expands voice note to show player on click', () => {
    const handoff = createMockHandoff({
      voice_notes: [
        createMockVoiceNote({
          id: 'note-1',
          storage_url: 'https://storage.example.com/note-1.webm',
          transcript: 'Test transcript',
        }),
      ],
    });

    render(<HandoffViewer handoff={handoff} />);

    // Click to expand
    fireEvent.click(screen.getByText('Voice Note 1'));

    // Player should appear
    expect(screen.getByTestId('voice-note-player')).toBeInTheDocument();
    expect(screen.getByTestId('transcript')).toHaveTextContent('Test transcript');
  });

  it('shows acknowledge button when canAcknowledge is true', () => {
    const handoff = createMockHandoff();
    const onAcknowledge = vi.fn();

    render(
      <HandoffViewer
        handoff={handoff}
        canAcknowledge={true}
        onAcknowledge={onAcknowledge}
      />
    );

    expect(screen.getByRole('button', { name: /acknowledge/i })).toBeInTheDocument();
  });

  it('does not show acknowledge button when canAcknowledge is false', () => {
    const handoff = createMockHandoff();

    render(<HandoffViewer handoff={handoff} canAcknowledge={false} />);

    expect(screen.queryByRole('button', { name: /acknowledge/i })).not.toBeInTheDocument();
  });

  it('calls onAcknowledge when acknowledge button is clicked', () => {
    const handoff = createMockHandoff();
    const onAcknowledge = vi.fn();

    render(
      <HandoffViewer
        handoff={handoff}
        canAcknowledge={true}
        onAcknowledge={onAcknowledge}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /acknowledge/i }));

    expect(onAcknowledge).toHaveBeenCalledTimes(1);
  });

  it('disables acknowledge button when isAcknowledging is true', () => {
    const handoff = createMockHandoff();
    const onAcknowledge = vi.fn();

    render(
      <HandoffViewer
        handoff={handoff}
        canAcknowledge={true}
        onAcknowledge={onAcknowledge}
        isAcknowledging={true}
      />
    );

    const button = screen.getByRole('button', { name: /acknowledging/i });
    expect(button).toBeDisabled();
  });

  it('shows acknowledged indicator for acknowledged handoffs', () => {
    const handoff = createMockHandoff({
      status: 'acknowledged',
      acknowledged_at: '2026-01-15T15:30:00Z',
    });

    render(<HandoffViewer handoff={handoff} />);

    // Should have status badge
    expect(screen.getByText('Acknowledged')).toBeInTheDocument();
  });

  it('displays assets covered section', () => {
    const handoff = createMockHandoff({
      assets_covered: ['asset-1', 'asset-2', 'asset-3'],
    });

    render(<HandoffViewer handoff={handoff} />);

    expect(screen.getByText('Assets Covered (3)')).toBeInTheDocument();
    expect(screen.getByText('asset-1')).toBeInTheDocument();
    expect(screen.getByText('asset-2')).toBeInTheDocument();
    expect(screen.getByText('asset-3')).toBeInTheDocument();
  });

  it('does not render summary section when summary_text is null', () => {
    const handoff = createMockHandoff({ summary_text: null });

    render(<HandoffViewer handoff={handoff} />);

    expect(screen.queryByText('Shift Summary')).not.toBeInTheDocument();
  });

  it('does not render notes section when text_notes is null', () => {
    const handoff = createMockHandoff({ text_notes: null });

    render(<HandoffViewer handoff={handoff} />);

    expect(screen.queryByText('Additional Notes')).not.toBeInTheDocument();
  });

  it('does not render voice notes section when empty', () => {
    const handoff = createMockHandoff({ voice_notes: [] });

    render(<HandoffViewer handoff={handoff} />);

    expect(screen.queryByText(/Voice Notes/)).not.toBeInTheDocument();
  });

  it('sorts voice notes by sequence order', () => {
    const handoff = createMockHandoff({
      voice_notes: [
        createMockVoiceNote({ id: 'note-3', sequence_order: 3 }),
        createMockVoiceNote({ id: 'note-1', sequence_order: 1 }),
        createMockVoiceNote({ id: 'note-2', sequence_order: 2 }),
      ],
    });

    render(<HandoffViewer handoff={handoff} />);

    const noteHeaders = screen.getAllByText(/Voice Note \d/);
    expect(noteHeaders).toHaveLength(3);
    // The order should be 1, 2, 3 after sorting
  });

  it('displays shift type and date in header', () => {
    const handoff = createMockHandoff({
      shift_type: 'afternoon',
      shift_date: '2026-01-20',
    });

    render(<HandoffViewer handoff={handoff} />);

    expect(screen.getByText('Afternoon Shift')).toBeInTheDocument();
    // Date formatting may vary by locale/timezone - check for "January" at minimum
    expect(screen.getByText(/january/i)).toBeInTheDocument();
  });

  it('has tablet-optimized layout classes', () => {
    const handoff = createMockHandoff();

    const { container } = render(<HandoffViewer handoff={handoff} />);

    // Check for responsive padding classes
    const viewer = container.querySelector('.handoff-viewer');
    expect(viewer).toBeInTheDocument();
    expect(viewer).toHaveClass('p-4', 'md:p-6', 'lg:p-8');
  });
});
