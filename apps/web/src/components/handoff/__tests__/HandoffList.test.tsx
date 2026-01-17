/**
 * HandoffList Component Tests (Story 9.5, Task 8.1)
 *
 * Tests for the handoff list component.
 *
 * @see Story 9.5 - Handoff Review UI
 * @see AC#1 - Handoff Notification Banner
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { HandoffList } from '../HandoffList';
import type { HandoffListItem } from '@/types/handoff';

// Mock Next.js router
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
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

describe('HandoffList', () => {
  it('renders pending handoffs section when data exists', () => {
    const handoffs: HandoffListItem[] = [
      createMockHandoff({ id: 'handoff-1', creator_name: 'Alice' }),
      createMockHandoff({ id: 'handoff-2', creator_name: 'Bob' }),
    ];

    render(<HandoffList handoffs={handoffs} showSections />);

    expect(screen.getByText('Pending Review')).toBeInTheDocument();
    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.getByText('Bob')).toBeInTheDocument();
  });

  it('shows empty state when no pending handoffs', () => {
    render(<HandoffList handoffs={[]} showSections />);

    expect(screen.getByText('No handoffs yet')).toBeInTheDocument();
    expect(
      screen.getByText(/handoffs from previous shifts will appear here/i)
    ).toBeInTheDocument();
  });

  it('separates pending and completed handoffs into sections', () => {
    const handoffs: HandoffListItem[] = [
      createMockHandoff({
        id: 'pending-1',
        creator_name: 'Pending User',
        status: 'pending_acknowledgment',
      }),
      createMockHandoff({
        id: 'completed-1',
        creator_name: 'Completed User',
        status: 'acknowledged',
      }),
    ];

    render(<HandoffList handoffs={handoffs} showSections />);

    expect(screen.getByText('Pending Review')).toBeInTheDocument();
    expect(screen.getByText('Previously Reviewed')).toBeInTheDocument();
    expect(screen.getByText('Pending User')).toBeInTheDocument();
    expect(screen.getByText('Completed User')).toBeInTheDocument();
  });

  it('shows pending count badge', () => {
    const handoffs: HandoffListItem[] = [
      createMockHandoff({ id: 'handoff-1' }),
      createMockHandoff({ id: 'handoff-2' }),
      createMockHandoff({ id: 'handoff-3' }),
    ];

    render(<HandoffList handoffs={handoffs} showSections />);

    // Badge should show count
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('renders without sections when showSections is false', () => {
    const handoffs: HandoffListItem[] = [
      createMockHandoff({ id: 'handoff-1', status: 'pending_acknowledgment' }),
      createMockHandoff({ id: 'handoff-2', status: 'acknowledged' }),
    ];

    render(<HandoffList handoffs={handoffs} showSections={false} />);

    expect(screen.queryByText('Pending Review')).not.toBeInTheDocument();
    expect(screen.queryByText('Previously Reviewed')).not.toBeInTheDocument();
  });

  it('shows loading skeleton when isLoading is true', () => {
    render(<HandoffList handoffs={[]} isLoading />);

    // Should not show empty state
    expect(screen.queryByText('No handoffs yet')).not.toBeInTheDocument();
  });

  it('renders handoff cards with correct information', () => {
    const handoffs: HandoffListItem[] = [
      createMockHandoff({
        id: 'handoff-1',
        creator_name: 'Test User',
        shift_type: 'afternoon',
        summary_preview: 'This is the summary preview',
        voice_note_count: 3,
        assets_covered: ['asset-1', 'asset-2', 'asset-3'],
      }),
    ];

    render(<HandoffList handoffs={handoffs} />);

    expect(screen.getByText('Test User')).toBeInTheDocument();
    expect(screen.getByText('Afternoon Shift')).toBeInTheDocument();
    expect(screen.getByText('This is the summary preview')).toBeInTheDocument();
    expect(screen.getByText('3 voice notes')).toBeInTheDocument();
    expect(screen.getByText('3 assets')).toBeInTheDocument();
  });

  it('only shows completed section when no pending handoffs', () => {
    const handoffs: HandoffListItem[] = [
      createMockHandoff({ id: 'completed-1', status: 'acknowledged' }),
      createMockHandoff({ id: 'completed-2', status: 'acknowledged' }),
    ];

    render(<HandoffList handoffs={handoffs} showSections />);

    expect(screen.queryByText('Pending Review')).not.toBeInTheDocument();
    expect(screen.getByText('Previously Reviewed')).toBeInTheDocument();
  });

  it('only shows pending section when no completed handoffs', () => {
    const handoffs: HandoffListItem[] = [
      createMockHandoff({ id: 'pending-1', status: 'pending_acknowledgment' }),
      createMockHandoff({ id: 'pending-2', status: 'pending_acknowledgment' }),
    ];

    render(<HandoffList handoffs={handoffs} showSections />);

    expect(screen.getByText('Pending Review')).toBeInTheDocument();
    expect(screen.queryByText('Previously Reviewed')).not.toBeInTheDocument();
  });
});
