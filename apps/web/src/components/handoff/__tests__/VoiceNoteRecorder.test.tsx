/**
 * VoiceNoteRecorder Component Tests (Story 9.3, Task 8)
 *
 * Tests for the voice note recording component.
 * AC#1: Voice Note Recording Initiation
 * AC#2: Recording Completion and Transcription
 * AC#4: Recording Error Handling
 *
 * References:
 * - [Source: epic-9.md#Story 9.3]
 */

import { describe, it, expect, vi, beforeEach, afterEach, Mock } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { VoiceNoteRecorder } from '../VoiceNoteRecorder'

// Mock the Supabase client
vi.mock('@/lib/supabase/client', () => ({
  createClient: () => ({
    auth: {
      getSession: vi.fn().mockResolvedValue({
        data: { session: { access_token: 'mock-token' } },
      }),
    },
  }),
}))

// Mock the voice lib
vi.mock('@/lib/voice', () => ({
  isPushToTalkSupported: vi.fn().mockReturnValue(true),
  createPushToTalk: vi.fn(),
  PushToTalk: vi.fn(),
}))

// Mock MediaRecorder
const mockMediaRecorder = {
  start: vi.fn(),
  stop: vi.fn(),
  ondataavailable: null as any,
  onstop: null as any,
  onerror: null as any,
  state: 'inactive' as string,
}

// Mock navigator.mediaDevices
const mockMediaDevices = {
  getUserMedia: vi.fn(),
}

// Mock MediaRecorder.isTypeSupported
global.MediaRecorder = vi.fn().mockImplementation(() => mockMediaRecorder) as any
global.MediaRecorder.isTypeSupported = vi.fn().mockReturnValue(true)

// Mock fetch
global.fetch = vi.fn()

describe('VoiceNoteRecorder', () => {
  const defaultProps = {
    handoffId: 'handoff-123',
    onNoteAdded: vi.fn(),
    onError: vi.fn(),
    noteCount: 0,
    maxNotes: 5,
  }

  const mockVoiceNoteResponse = {
    note: {
      id: 'note-123',
      handoff_id: 'handoff-123',
      user_id: 'user-123',
      storage_path: 'mock://user-123/handoff-123/note-123.webm',
      storage_url: 'https://mock-storage.example.com/audio.webm',
      transcript: 'Test transcription',
      duration_seconds: 5,
      sequence_order: 0,
      created_at: '2026-01-17T14:30:00Z',
    },
    total_notes: 1,
    can_add_more: true,
    message: 'Voice note uploaded successfully',
  }

  beforeEach(() => {
    vi.clearAllMocks()
    Object.defineProperty(navigator, 'mediaDevices', {
      value: mockMediaDevices,
      writable: true,
    })

    // Reset MediaRecorder mock state
    mockMediaRecorder.state = 'inactive'
    mockMediaRecorder.start.mockClear()
    mockMediaRecorder.stop.mockClear()

    // Mock successful media stream
    mockMediaDevices.getUserMedia.mockResolvedValue({
      getTracks: () => [{ stop: vi.fn() }],
    })

    // Mock successful upload
    ;(global.fetch as Mock).mockResolvedValue({
      ok: true,
      json: async () => mockVoiceNoteResponse,
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Initial Render', () => {
    it('renders the recorder button', () => {
      render(<VoiceNoteRecorder {...defaultProps} />)

      expect(screen.getByRole('button', { name: /press and hold to record/i })).toBeInTheDocument()
    })

    it('shows hint text when ready', () => {
      render(<VoiceNoteRecorder {...defaultProps} />)

      expect(screen.getByText(/press and hold to record/i)).toBeInTheDocument()
    })

    it('disables button when limit reached', () => {
      render(<VoiceNoteRecorder {...defaultProps} noteCount={5} />)

      expect(screen.getByRole('button')).toBeDisabled()
      expect(screen.getByText(/maximum 5 voice notes reached/i)).toBeInTheDocument()
    })

    it('disables button when disabled prop is true', () => {
      render(<VoiceNoteRecorder {...defaultProps} disabled />)

      expect(screen.getByRole('button')).toBeDisabled()
    })
  })

  describe('Recording Flow (AC#1)', () => {
    it('requests microphone permission on press', async () => {
      render(<VoiceNoteRecorder {...defaultProps} />)

      const button = screen.getByRole('button')

      await act(async () => {
        fireEvent.mouseDown(button)
      })

      // Wait for permission request
      await waitFor(() => {
        expect(mockMediaDevices.getUserMedia).toHaveBeenCalledWith(
          expect.objectContaining({
            audio: expect.any(Object),
          })
        )
      })
    })

    it('shows recording state while pressed', async () => {
      render(<VoiceNoteRecorder {...defaultProps} />)

      const button = screen.getByRole('button')

      await act(async () => {
        fireEvent.mouseDown(button)
      })

      // Wait for recording to start
      await waitFor(() => {
        expect(screen.queryByText(/recording/i)).toBeInTheDocument()
      })
    })

    it('shows duration while recording', async () => {
      vi.useFakeTimers()
      render(<VoiceNoteRecorder {...defaultProps} />)

      const button = screen.getByRole('button')

      await act(async () => {
        fireEvent.mouseDown(button)
      })

      // Fast forward 3 seconds
      await act(async () => {
        vi.advanceTimersByTime(3000)
      })

      vi.useRealTimers()
    })
  })

  describe('Upload Flow (AC#2)', () => {
    it('uploads audio when recording stops', async () => {
      render(<VoiceNoteRecorder {...defaultProps} />)

      const button = screen.getByRole('button')

      // Start recording
      await act(async () => {
        fireEvent.mouseDown(button)
      })

      // Wait for MediaRecorder to be created
      await waitFor(() => {
        expect(mockMediaRecorder.start).toHaveBeenCalled()
      })

      // Simulate audio data
      await act(async () => {
        mockMediaRecorder.ondataavailable?.({ data: new Blob(['audio'], { type: 'audio/webm' }) })
      })

      // Stop recording
      await act(async () => {
        fireEvent.mouseUp(button)
        mockMediaRecorder.onstop?.()
      })

      // Should call the upload endpoint
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          '/api/v1/handoff/handoff-123/voice-notes',
          expect.objectContaining({
            method: 'POST',
          })
        )
      })
    })

    it('calls onNoteAdded after successful upload', async () => {
      render(<VoiceNoteRecorder {...defaultProps} />)

      const button = screen.getByRole('button')

      // Start recording
      await act(async () => {
        fireEvent.mouseDown(button)
      })

      await waitFor(() => {
        expect(mockMediaRecorder.start).toHaveBeenCalled()
      })

      // Simulate audio data
      await act(async () => {
        mockMediaRecorder.ondataavailable?.({ data: new Blob(['audio'], { type: 'audio/webm' }) })
      })

      // Stop recording
      await act(async () => {
        fireEvent.mouseUp(button)
        mockMediaRecorder.onstop?.()
      })

      await waitFor(() => {
        expect(defaultProps.onNoteAdded).toHaveBeenCalledWith(mockVoiceNoteResponse.note)
      })
    })
  })

  describe('Error Handling (AC#4)', () => {
    it('shows error when microphone permission denied', async () => {
      mockMediaDevices.getUserMedia.mockRejectedValue(
        new DOMException('Permission denied', 'NotAllowedError')
      )

      render(<VoiceNoteRecorder {...defaultProps} />)

      const button = screen.getByRole('button')

      await act(async () => {
        fireEvent.mouseDown(button)
      })

      await waitFor(() => {
        expect(screen.getByText(/microphone access required/i)).toBeInTheDocument()
      })

      expect(defaultProps.onError).toHaveBeenCalled()
    })

    it('shows error when upload fails', async () => {
      ;(global.fetch as Mock).mockResolvedValue({
        ok: false,
        json: async () => ({ detail: { error: 'Upload failed' } }),
      })

      render(<VoiceNoteRecorder {...defaultProps} />)

      const button = screen.getByRole('button')

      await act(async () => {
        fireEvent.mouseDown(button)
      })

      await waitFor(() => {
        expect(mockMediaRecorder.start).toHaveBeenCalled()
      })

      await act(async () => {
        mockMediaRecorder.ondataavailable?.({ data: new Blob(['audio'], { type: 'audio/webm' }) })
        fireEvent.mouseUp(button)
        mockMediaRecorder.onstop?.()
      })

      await waitFor(() => {
        expect(screen.getByText(/upload failed/i)).toBeInTheDocument()
      })
    })

    it('shows retry button on error', async () => {
      mockMediaDevices.getUserMedia.mockRejectedValue(new Error('Test error'))

      render(<VoiceNoteRecorder {...defaultProps} />)

      const button = screen.getByRole('button')

      await act(async () => {
        fireEvent.mouseDown(button)
      })

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument()
      })
    })
  })

  describe('Browser Support', () => {
    it('shows not supported message when MediaRecorder unavailable', async () => {
      const { isPushToTalkSupported } = await import('@/lib/voice')
      ;(isPushToTalkSupported as Mock).mockReturnValue(false)

      render(<VoiceNoteRecorder {...defaultProps} />)

      expect(screen.getByText(/voice recording not supported/i)).toBeInTheDocument()
    })
  })
})
