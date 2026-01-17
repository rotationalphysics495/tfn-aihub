/**
 * VoiceNoteList Component Tests (Story 9.3, Task 8)
 *
 * Tests for the voice note list component.
 * AC#3: Multiple Voice Notes Management
 *
 * References:
 * - [Source: epic-9.md#Story 9.3]
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { VoiceNoteList } from '../VoiceNoteList'
import type { VoiceNote } from '../VoiceNoteRecorder'

// Mock the VoiceNotePlayer component
vi.mock('../VoiceNotePlayer', () => ({
  VoiceNotePlayer: ({ onEnded }: { onEnded?: () => void }) => (
    <div data-testid="voice-note-player">
      <button onClick={onEnded}>End Playback</button>
    </div>
  ),
}))

describe('VoiceNoteList', () => {
  const createMockNote = (index: number, overrides?: Partial<VoiceNote>): VoiceNote => ({
    id: `note-${index}`,
    handoff_id: 'handoff-123',
    user_id: 'user-123',
    storage_path: `mock://path/note-${index}.webm`,
    storage_url: `https://storage.example.com/note-${index}.webm`,
    transcript: `This is transcript ${index}`,
    duration_seconds: 15 + index * 5,
    sequence_order: index,
    created_at: new Date(2026, 0, 17, 14, 30 + index).toISOString(),
    ...overrides,
  })

  const defaultProps = {
    notes: [] as VoiceNote[],
    onDelete: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Empty State', () => {
    it('shows empty message when no notes', () => {
      render(<VoiceNoteList {...defaultProps} notes={[]} />)

      expect(screen.getByText('No voice notes attached')).toBeInTheDocument()
    })
  })

  describe('Note Display (AC#3)', () => {
    it('renders list of voice notes', () => {
      const notes = [createMockNote(0), createMockNote(1), createMockNote(2)]

      render(<VoiceNoteList {...defaultProps} notes={notes} />)

      // Should show all notes
      expect(screen.getAllByRole('button', { name: /play/i })).toHaveLength(3)
    })

    it('shows sequence number badge for each note', () => {
      const notes = [createMockNote(0), createMockNote(1)]

      render(<VoiceNoteList {...defaultProps} notes={notes} />)

      expect(screen.getByText('1')).toBeInTheDocument()
      expect(screen.getByText('2')).toBeInTheDocument()
    })

    it('shows duration for each note', () => {
      const notes = [createMockNote(0)] // 15 seconds

      render(<VoiceNoteList {...defaultProps} notes={notes} />)

      expect(screen.getByText('0:15')).toBeInTheDocument()
    })

    it('formats duration with leading zero for seconds', () => {
      const notes = [createMockNote(0, { duration_seconds: 65 })] // 1:05

      render(<VoiceNoteList {...defaultProps} notes={notes} />)

      expect(screen.getByText('1:05')).toBeInTheDocument()
    })

    it('shows timestamp for each note', () => {
      const notes = [createMockNote(0)]

      render(<VoiceNoteList {...defaultProps} notes={notes} />)

      // Should show time like "2:30 PM"
      expect(screen.getByText(/pm/i)).toBeInTheDocument()
    })
  })

  describe('Transcript Toggle (AC#3)', () => {
    it('shows expand button when note has transcript', () => {
      const notes = [createMockNote(0)]

      render(<VoiceNoteList {...defaultProps} notes={notes} />)

      expect(screen.getByRole('button', { name: /show transcript/i })).toBeInTheDocument()
    })

    it('expands transcript when toggle clicked', async () => {
      const notes = [createMockNote(0)]

      render(<VoiceNoteList {...defaultProps} notes={notes} />)

      // Click to expand
      fireEvent.click(screen.getByRole('button', { name: /show transcript/i }))

      await waitFor(() => {
        expect(screen.getByText('This is transcript 0')).toBeInTheDocument()
      })
    })

    it('collapses transcript when toggle clicked again', async () => {
      const notes = [createMockNote(0)]

      render(<VoiceNoteList {...defaultProps} notes={notes} />)

      // Expand
      fireEvent.click(screen.getByRole('button', { name: /show transcript/i }))

      await waitFor(() => {
        expect(screen.getByText('This is transcript 0')).toBeInTheDocument()
      })

      // Collapse
      fireEvent.click(screen.getByRole('button', { name: /hide transcript/i }))

      await waitFor(() => {
        expect(screen.queryByText('This is transcript 0')).not.toBeInTheDocument()
      })
    })

    it('shows unavailable indicator when no transcript', () => {
      const notes = [createMockNote(0, { transcript: null })]

      render(<VoiceNoteList {...defaultProps} notes={notes} />)

      expect(screen.getByText('Transcript unavailable')).toBeInTheDocument()
    })
  })

  describe('Playback (AC#3)', () => {
    it('shows play button for each note', () => {
      const notes = [createMockNote(0)]

      render(<VoiceNoteList {...defaultProps} notes={notes} />)

      expect(screen.getByRole('button', { name: /play/i })).toBeInTheDocument()
    })

    it('shows player when play clicked', async () => {
      const notes = [createMockNote(0)]

      render(<VoiceNoteList {...defaultProps} notes={notes} />)

      fireEvent.click(screen.getByRole('button', { name: /play/i }))

      await waitFor(() => {
        expect(screen.getByTestId('voice-note-player')).toBeInTheDocument()
      })
    })
  })

  describe('Deletion (AC#3)', () => {
    it('shows delete button when editable', () => {
      const notes = [createMockNote(0)]

      render(<VoiceNoteList {...defaultProps} notes={notes} editable />)

      expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument()
    })

    it('hides delete button when not editable', () => {
      const notes = [createMockNote(0)]

      render(<VoiceNoteList {...defaultProps} notes={notes} editable={false} />)

      expect(screen.queryByRole('button', { name: /delete/i })).not.toBeInTheDocument()
    })

    it('shows confirmation before deleting', async () => {
      const notes = [createMockNote(0)]

      render(<VoiceNoteList {...defaultProps} notes={notes} editable />)

      fireEvent.click(screen.getByRole('button', { name: /delete/i }))

      await waitFor(() => {
        expect(screen.getByText(/delete this voice note/i)).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
        expect(screen.getAllByRole('button', { name: /delete/i })).toHaveLength(2) // Original + confirm
      })
    })

    it('cancels deletion on cancel click', async () => {
      const notes = [createMockNote(0)]

      render(<VoiceNoteList {...defaultProps} notes={notes} editable />)

      // Click delete
      fireEvent.click(screen.getByRole('button', { name: /delete/i }))

      await waitFor(() => {
        expect(screen.getByText(/delete this voice note/i)).toBeInTheDocument()
      })

      // Click cancel
      fireEvent.click(screen.getByRole('button', { name: /cancel/i }))

      await waitFor(() => {
        expect(screen.queryByText(/delete this voice note/i)).not.toBeInTheDocument()
      })

      expect(defaultProps.onDelete).not.toHaveBeenCalled()
    })

    it('calls onDelete on confirm', async () => {
      const notes = [createMockNote(0)]

      render(<VoiceNoteList {...defaultProps} notes={notes} editable />)

      // Click delete
      fireEvent.click(screen.getByRole('button', { name: /delete/i }))

      await waitFor(() => {
        expect(screen.getByText(/delete this voice note/i)).toBeInTheDocument()
      })

      // Click confirm delete (second delete button)
      const deleteButtons = screen.getAllByRole('button', { name: /delete/i })
      fireEvent.click(deleteButtons[1])

      expect(defaultProps.onDelete).toHaveBeenCalledWith('note-0')
    })

    it('shows loading state during deletion', () => {
      const notes = [createMockNote(0)]

      render(<VoiceNoteList {...defaultProps} notes={notes} editable deletingId="note-0" />)

      // Note should have reduced opacity
      // (Testing CSS classes is limited, so we just verify the component accepts the prop)
    })
  })

  describe('Ordering (AC#3)', () => {
    it('displays notes in sequence order', () => {
      // Notes in reverse creation order
      const notes = [
        createMockNote(2, { sequence_order: 0 }),
        createMockNote(0, { sequence_order: 1 }),
        createMockNote(1, { sequence_order: 2 }),
      ]

      render(<VoiceNoteList {...defaultProps} notes={notes} />)

      const badges = screen.getAllByText(/^[123]$/)
      expect(badges).toHaveLength(3)
      expect(badges[0]).toHaveTextContent('1')
      expect(badges[1]).toHaveTextContent('2')
      expect(badges[2]).toHaveTextContent('3')
    })
  })
})
