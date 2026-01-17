/**
 * VoiceNotePlayer Component Tests (Story 9.3, Task 8)
 *
 * Tests for the voice note playback component.
 * AC#3: Multiple Voice Notes Management - Play button for review
 *
 * References:
 * - [Source: epic-9.md#Story 9.3]
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { VoiceNotePlayer } from '../VoiceNotePlayer'

describe('VoiceNotePlayer', () => {
  const defaultProps = {
    src: 'https://storage.example.com/audio.webm',
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Render', () => {
    it('renders play button', () => {
      render(<VoiceNotePlayer {...defaultProps} />)

      expect(screen.getByRole('button', { name: /play/i })).toBeInTheDocument()
    })

    it('renders progress bar', () => {
      render(<VoiceNotePlayer {...defaultProps} />)

      expect(screen.getByRole('slider', { name: /seek/i })).toBeInTheDocument()
    })

    it('renders time display', () => {
      render(<VoiceNotePlayer {...defaultProps} />)

      // Initial time should be 0:00 (appears twice: current time and duration)
      const timeElements = screen.getAllByText('0:00')
      expect(timeElements.length).toBe(2)
    })

    it('renders transcript when provided', () => {
      render(<VoiceNotePlayer {...defaultProps} transcript="Test transcript content" />)

      expect(screen.getByText('Test transcript content')).toBeInTheDocument()
    })

    it('does not render transcript when not provided', () => {
      render(<VoiceNotePlayer {...defaultProps} />)

      expect(screen.queryByText('Test transcript content')).not.toBeInTheDocument()
    })
  })

  describe('Time Formatting', () => {
    it('shows initial time as 0:00', () => {
      render(<VoiceNotePlayer {...defaultProps} />)
      // Both current time and duration show 0:00 initially
      const timeElements = screen.getAllByText('0:00')
      expect(timeElements.length).toBeGreaterThanOrEqual(1)
    })
  })

  describe('Props', () => {
    it('accepts custom className', () => {
      render(<VoiceNotePlayer {...defaultProps} className="custom-class" />)
      // Component should render without errors
      expect(screen.getByRole('button')).toBeInTheDocument()
    })

    it('accepts onEnded callback', () => {
      const onEnded = vi.fn()
      render(<VoiceNotePlayer {...defaultProps} onEnded={onEnded} />)
      // Component should render without errors
      expect(screen.getByRole('button')).toBeInTheDocument()
    })

    it('accepts onError callback', () => {
      const onError = vi.fn()
      render(<VoiceNotePlayer {...defaultProps} onError={onError} />)
      // Component should render without errors
      expect(screen.getByRole('button')).toBeInTheDocument()
    })
  })
})
