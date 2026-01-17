/**
 * HandoffCard Component Tests (Story 9.5, Task 8.2)
 *
 * Tests for the handoff card component.
 *
 * @see Story 9.5 - Handoff Review UI
 * @see AC#1 - Handoff Notification Banner
 * @see AC#2 - Handoff Detail View (preview)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { HandoffCard } from '../HandoffCard';
import type { HandoffListItem } from '@/types/handoff';

// Mock Next.js router
const mockPush = vi.fn();
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: vi.fn(),
  }),
}));

// Test data factory
const createMockHandoff = (overrides: Partial<HandoffListItem> = {}): HandoffListItem => ({
  id: 'handoff-123',
  created_by: 'user-456',
  creator_name: 'John Smith',
  shift_date: '2026-01-15',
  shift_type: 'morning',
  status: 'pending_acknowledgment',
  assets_covered: ['asset-1', 'asset-2'],
  summary_preview: 'Shift summary preview text...',
  voice_note_count: 2,
  created_at: '2026-01-15T06:00:00Z',
  submitted_at: '2026-01-15T14:00:00Z',
  ...overrides,
});

describe('HandoffCard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('displays correct information', () => {
    const handoff = createMockHandoff({
      creator_name: 'Jane Doe',
      shift_type: 'afternoon',
      summary_preview: 'Production summary for the shift',
      voice_note_count: 3,
      assets_covered: ['asset-1', 'asset-2', 'asset-3'],
    });

    render(<HandoffCard handoff={handoff} />);

    expect(screen.getByText('Jane Doe')).toBeInTheDocument();
    expect(screen.getByText('Afternoon Shift')).toBeInTheDocument();
    expect(screen.getByText('Production summary for the shift')).toBeInTheDocument();
    expect(screen.getByText('3 voice notes')).toBeInTheDocument();
    expect(screen.getByText('3 assets')).toBeInTheDocument();
  });

  it('shows pending status badge for pending handoffs', () => {
    const handoff = createMockHandoff({ status: 'pending_acknowledgment' });

    render(<HandoffCard handoff={handoff} />);

    expect(screen.getByText('Pending')).toBeInTheDocument();
  });

  it('shows acknowledged status badge for acknowledged handoffs', () => {
    const handoff = createMockHandoff({ status: 'acknowledged' });

    render(<HandoffCard handoff={handoff} />);

    expect(screen.getByText('Acknowledged')).toBeInTheDocument();
  });

  it('shows draft status badge for draft handoffs', () => {
    const handoff = createMockHandoff({ status: 'draft' });

    render(<HandoffCard handoff={handoff} />);

    expect(screen.getByText('Draft')).toBeInTheDocument();
  });

  it('navigates to detail page on click', () => {
    const handoff = createMockHandoff({ id: 'handoff-xyz' });

    render(<HandoffCard handoff={handoff} />);

    fireEvent.click(screen.getByRole('button'));

    expect(mockPush).toHaveBeenCalledWith('/handoff/handoff-xyz');
  });

  it('navigates on Enter key press', () => {
    const handoff = createMockHandoff({ id: 'handoff-abc' });

    render(<HandoffCard handoff={handoff} />);

    fireEvent.keyDown(screen.getByRole('button'), { key: 'Enter' });

    expect(mockPush).toHaveBeenCalledWith('/handoff/handoff-abc');
  });

  it('navigates on Space key press', () => {
    const handoff = createMockHandoff({ id: 'handoff-def' });

    render(<HandoffCard handoff={handoff} />);

    fireEvent.keyDown(screen.getByRole('button'), { key: ' ' });

    expect(mockPush).toHaveBeenCalledWith('/handoff/handoff-def');
  });

  it('shows singular voice note text for one note', () => {
    const handoff = createMockHandoff({ voice_note_count: 1 });

    render(<HandoffCard handoff={handoff} />);

    expect(screen.getByText('1 voice note')).toBeInTheDocument();
  });

  it('shows singular asset text for one asset', () => {
    const handoff = createMockHandoff({ assets_covered: ['asset-1'] });

    render(<HandoffCard handoff={handoff} />);

    expect(screen.getByText('1 asset')).toBeInTheDocument();
  });

  it('does not show voice notes indicator when count is zero', () => {
    const handoff = createMockHandoff({ voice_note_count: 0 });

    render(<HandoffCard handoff={handoff} />);

    expect(screen.queryByText(/voice note/i)).not.toBeInTheDocument();
  });

  it('applies left border for pending handoffs', () => {
    const handoff = createMockHandoff({ status: 'pending_acknowledgment' });

    const { container } = render(<HandoffCard handoff={handoff} />);

    // Check for the border-l-4 class on the card
    const card = container.querySelector('.border-l-4');
    expect(card).toBeInTheDocument();
  });

  it('has proper aria-label for accessibility', () => {
    const handoff = createMockHandoff({
      creator_name: 'Test User',
      shift_date: '2026-01-20',
    });

    render(<HandoffCard handoff={handoff} />);

    expect(
      screen.getByRole('button', { name: /handoff from test user/i })
    ).toBeInTheDocument();
  });

  it('renders formatted date correctly', () => {
    const handoff = createMockHandoff({
      shift_date: '2026-01-15',
    });

    render(<HandoffCard handoff={handoff} />);

    // Date should be formatted - check for "Jan" at minimum since day may vary by timezone
    expect(screen.getByText(/jan/i)).toBeInTheDocument();
  });

  it('shows summary preview when provided', () => {
    const handoff = createMockHandoff({
      summary_preview: 'This is the shift summary preview text',
    });

    render(<HandoffCard handoff={handoff} />);

    expect(screen.getByText('This is the shift summary preview text')).toBeInTheDocument();
  });

  it('does not show summary when not provided', () => {
    const handoff = createMockHandoff({
      summary_preview: null,
    });

    render(<HandoffCard handoff={handoff} />);

    // Only the creator name should appear, not undefined or null
    expect(screen.queryByText('undefined')).not.toBeInTheDocument();
    expect(screen.queryByText('null')).not.toBeInTheDocument();
  });
});
