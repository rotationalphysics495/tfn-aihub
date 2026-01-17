/**
 * useBriefing Hook Tests (Story 8.7 Task 1.6)
 *
 * Tests for the useBriefing hook including:
 * - State initialization
 * - Section navigation
 * - Pause countdown timer logic
 * - Audio completion detection
 * - Partial completion tracking
 *
 * AC#1, #2, #3, #4: Full briefing state management
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach, type Mock } from 'vitest';
import { useBriefing, BriefingSection, BriefingStatus } from '../useBriefing';

// Mock fetch
global.fetch = vi.fn();

// Mock timers
vi.useFakeTimers();

// Mock sections for testing
const mockSections: BriefingSection[] = [
  {
    section_type: 'safety',
    title: 'Safety Update',
    content: 'No safety incidents reported.',
    area_id: 'grinding',
    status: 'completed',
    pause_point: true,
  },
  {
    section_type: 'production',
    title: 'Production Overview',
    content: 'Production is at 95% of target.',
    area_id: 'assembly',
    status: 'active',
    pause_point: true,
  },
  {
    section_type: 'quality',
    title: 'Quality Metrics',
    content: 'Quality rate is at 99.2%.',
    area_id: 'packaging',
    status: 'pending',
    pause_point: false, // No pause at this section
  },
];

// Mock API response
const mockBriefingResponse = {
  briefing_id: 'test-briefing-123',
  title: 'Morning Briefing',
  sections: mockSections,
  audio_stream_url: '/api/voice/tts/stream',
  total_duration_estimate: 180000,
};

describe('useBriefing', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.clearAllTimers();
    (global.fetch as Mock).mockReset();
  });

  afterEach(() => {
    vi.runOnlyPendingTimers();
  });

  describe('Initial state', () => {
    it('initializes with idle status', () => {
      const { result } = renderHook(() => useBriefing());
      const [state] = result.current;

      expect(state.status).toBe('idle');
    });

    it('initializes with empty sections', () => {
      const { result } = renderHook(() => useBriefing());
      const [state] = result.current;

      expect(state.sections).toEqual([]);
    });

    it('initializes with currentSectionIndex 0', () => {
      const { result } = renderHook(() => useBriefing());
      const [state] = result.current;

      expect(state.currentSectionIndex).toBe(0);
    });

    it('initializes with null silenceCountdown', () => {
      const { result } = renderHook(() => useBriefing());
      const [state] = result.current;

      expect(state.silenceCountdown).toBeNull();
    });

    it('initializes with empty transcript', () => {
      const { result } = renderHook(() => useBriefing());
      const [state] = result.current;

      expect(state.transcript).toEqual([]);
    });
  });

  describe('startBriefing', () => {
    it('sets loading status when starting', async () => {
      (global.fetch as Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockBriefingResponse,
      });

      const { result } = renderHook(() => useBriefing());
      const [, actions] = result.current;

      act(() => {
        actions.startBriefing('user-123');
      });

      expect(result.current[0].status).toBe('loading');
    });

    it('sets playing status after successful fetch', async () => {
      (global.fetch as Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockBriefingResponse,
      });

      const { result } = renderHook(() => useBriefing());
      const [, actions] = result.current;

      await act(async () => {
        await actions.startBriefing('user-123');
      });

      expect(result.current[0].status).toBe('playing');
    });

    it('populates sections from API response', async () => {
      (global.fetch as Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockBriefingResponse,
      });

      const { result } = renderHook(() => useBriefing());
      const [, actions] = result.current;

      await act(async () => {
        await actions.startBriefing('user-123');
      });

      expect(result.current[0].sections).toEqual(mockSections);
    });

    it('sets error status on fetch failure', async () => {
      (global.fetch as Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
      });

      const { result } = renderHook(() => useBriefing());
      const [, actions] = result.current;

      await act(async () => {
        await actions.startBriefing('user-123');
      });

      expect(result.current[0].status).toBe('error');
      expect(result.current[0].error).toContain('Failed to start briefing');
    });

    it('calls onError callback on failure', async () => {
      const onError = vi.fn();
      (global.fetch as Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
      });

      const { result } = renderHook(() => useBriefing({ onError }));
      const [, actions] = result.current;

      await act(async () => {
        await actions.startBriefing('user-123');
      });

      expect(onError).toHaveBeenCalled();
    });

    it('calls onSectionChange callback on start', async () => {
      const onSectionChange = vi.fn();
      (global.fetch as Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockBriefingResponse,
      });

      const { result } = renderHook(() => useBriefing({ onSectionChange }));
      const [, actions] = result.current;

      await act(async () => {
        await actions.startBriefing('user-123');
      });

      expect(onSectionChange).toHaveBeenCalledWith(0, mockSections[0]);
    });
  });

  describe('play/pause', () => {
    it('play changes paused to playing', async () => {
      (global.fetch as Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockBriefingResponse,
      });

      const { result } = renderHook(() => useBriefing());
      const [, actions] = result.current;

      await act(async () => {
        await actions.startBriefing('user-123');
      });

      act(() => {
        actions.pause();
      });

      expect(result.current[0].status).toBe('paused');

      act(() => {
        actions.play();
      });

      expect(result.current[0].status).toBe('playing');
    });

    it('pause changes playing to paused', async () => {
      (global.fetch as Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockBriefingResponse,
      });

      const { result } = renderHook(() => useBriefing());
      const [, actions] = result.current;

      await act(async () => {
        await actions.startBriefing('user-123');
      });

      expect(result.current[0].status).toBe('playing');

      act(() => {
        actions.pause();
      });

      expect(result.current[0].status).toBe('paused');
    });

    it('play clears silence timers', async () => {
      (global.fetch as Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockBriefingResponse,
      });

      const { result } = renderHook(() => useBriefing());
      const [, actions] = result.current;

      await act(async () => {
        await actions.startBriefing('user-123');
      });

      act(() => {
        actions.startSilenceDetection();
      });

      expect(result.current[0].silenceCountdown).not.toBeNull();

      act(() => {
        actions.play();
      });

      expect(result.current[0].silenceCountdown).toBeNull();
    });
  });

  describe('Section navigation (AC#3)', () => {
    beforeEach(async () => {
      (global.fetch as Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockBriefingResponse,
      });
    });

    it('nextSection increments currentSectionIndex', async () => {
      const { result } = renderHook(() => useBriefing());
      const [, actions] = result.current;

      await act(async () => {
        await actions.startBriefing('user-123');
      });

      expect(result.current[0].currentSectionIndex).toBe(0);

      act(() => {
        actions.nextSection();
      });

      expect(result.current[0].currentSectionIndex).toBe(1);
    });

    it('previousSection decrements currentSectionIndex', async () => {
      const { result } = renderHook(() => useBriefing());
      const [, actions] = result.current;

      await act(async () => {
        await actions.startBriefing('user-123');
      });

      act(() => {
        actions.nextSection();
      });

      expect(result.current[0].currentSectionIndex).toBe(1);

      act(() => {
        actions.previousSection();
      });

      expect(result.current[0].currentSectionIndex).toBe(0);
    });

    it('previousSection does nothing at first section', async () => {
      const { result } = renderHook(() => useBriefing());
      const [, actions] = result.current;

      await act(async () => {
        await actions.startBriefing('user-123');
      });

      expect(result.current[0].currentSectionIndex).toBe(0);

      act(() => {
        actions.previousSection();
      });

      expect(result.current[0].currentSectionIndex).toBe(0);
    });

    it('nextSection completes at last section', async () => {
      const onComplete = vi.fn();
      const { result } = renderHook(() => useBriefing({ onComplete }));
      const [, actions] = result.current;

      await act(async () => {
        await actions.startBriefing('user-123');
      });

      // Navigate to last section
      act(() => {
        actions.nextSection();
        actions.nextSection();
      });

      expect(result.current[0].currentSectionIndex).toBe(2);

      act(() => {
        actions.nextSection();
      });

      expect(result.current[0].status).toBe('complete');
      expect(onComplete).toHaveBeenCalled();
    });

    it('goToSection navigates to specific index', async () => {
      const { result } = renderHook(() => useBriefing());
      const [, actions] = result.current;

      await act(async () => {
        await actions.startBriefing('user-123');
      });

      act(() => {
        actions.goToSection(2);
      });

      expect(result.current[0].currentSectionIndex).toBe(2);
    });

    it('goToSection ignores invalid index', async () => {
      const { result } = renderHook(() => useBriefing());
      const [, actions] = result.current;

      await act(async () => {
        await actions.startBriefing('user-123');
      });

      act(() => {
        actions.goToSection(10); // Out of bounds
      });

      expect(result.current[0].currentSectionIndex).toBe(0);
    });

    it('goToSection ignores negative index', async () => {
      const { result } = renderHook(() => useBriefing());
      const [, actions] = result.current;

      await act(async () => {
        await actions.startBriefing('user-123');
      });

      act(() => {
        actions.goToSection(-1);
      });

      expect(result.current[0].currentSectionIndex).toBe(0);
    });

    it('navigation calls onSectionChange', async () => {
      const onSectionChange = vi.fn();
      const { result } = renderHook(() => useBriefing({ onSectionChange }));
      const [, actions] = result.current;

      await act(async () => {
        await actions.startBriefing('user-123');
      });

      onSectionChange.mockClear();

      act(() => {
        actions.nextSection();
      });

      expect(onSectionChange).toHaveBeenCalledWith(1, mockSections[1]);
    });

    it('navigation sets status to playing', async () => {
      const { result } = renderHook(() => useBriefing());
      const [, actions] = result.current;

      await act(async () => {
        await actions.startBriefing('user-123');
      });

      act(() => {
        actions.pause();
      });

      expect(result.current[0].status).toBe('paused');

      act(() => {
        actions.nextSection();
      });

      expect(result.current[0].status).toBe('playing');
    });
  });

  describe('Silence detection (AC#2)', () => {
    beforeEach(async () => {
      (global.fetch as Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockBriefingResponse,
      });
    });

    it('startSilenceDetection sets countdown', async () => {
      const { result } = renderHook(() => useBriefing());
      const [, actions] = result.current;

      await act(async () => {
        await actions.startBriefing('user-123');
      });

      act(() => {
        actions.startSilenceDetection();
      });

      expect(result.current[0].silenceCountdown).toBe(4); // Default 3500ms = 4 seconds
    });

    it('countdown decrements over time', async () => {
      const { result } = renderHook(() => useBriefing());
      const [, actions] = result.current;

      await act(async () => {
        await actions.startBriefing('user-123');
      });

      act(() => {
        actions.startSilenceDetection();
      });

      expect(result.current[0].silenceCountdown).toBe(4);

      act(() => {
        vi.advanceTimersByTime(1000);
      });

      expect(result.current[0].silenceCountdown).toBe(3);

      act(() => {
        vi.advanceTimersByTime(1000);
      });

      expect(result.current[0].silenceCountdown).toBe(2);
    });

    it('cancelSilenceDetection clears countdown', async () => {
      const { result } = renderHook(() => useBriefing());
      const [, actions] = result.current;

      await act(async () => {
        await actions.startBriefing('user-123');
      });

      act(() => {
        actions.startSilenceDetection();
      });

      expect(result.current[0].silenceCountdown).not.toBeNull();

      act(() => {
        actions.cancelSilenceDetection();
      });

      expect(result.current[0].silenceCountdown).toBeNull();
    });

    it('custom silence timeout is used', async () => {
      const { result } = renderHook(() =>
        useBriefing({ silenceTimeoutMs: 2000 })
      );
      const [, actions] = result.current;

      await act(async () => {
        await actions.startBriefing('user-123');
      });

      act(() => {
        actions.startSilenceDetection();
      });

      expect(result.current[0].silenceCountdown).toBe(2); // 2000ms = 2 seconds
    });
  });

  describe('continueAfterPause', () => {
    beforeEach(async () => {
      (global.fetch as Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockBriefingResponse,
      });
    });

    it('clears silence timers', async () => {
      const { result } = renderHook(() => useBriefing());
      const [, actions] = result.current;

      await act(async () => {
        await actions.startBriefing('user-123');
      });

      act(() => {
        actions.startSilenceDetection();
      });

      expect(result.current[0].silenceCountdown).not.toBeNull();

      act(() => {
        actions.continueAfterPause();
      });

      expect(result.current[0].silenceCountdown).toBeNull();
    });

    it('advances to next section', async () => {
      const { result } = renderHook(() => useBriefing());
      const [, actions] = result.current;

      await act(async () => {
        await actions.startBriefing('user-123');
      });

      expect(result.current[0].currentSectionIndex).toBe(0);

      act(() => {
        actions.continueAfterPause();
      });

      expect(result.current[0].currentSectionIndex).toBe(1);
    });
  });

  describe('endBriefing (AC#4)', () => {
    beforeEach(async () => {
      (global.fetch as Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockBriefingResponse,
      });
    });

    it('sets status to complete', async () => {
      const { result } = renderHook(() => useBriefing());
      const [, actions] = result.current;

      await act(async () => {
        await actions.startBriefing('user-123');
      });

      (global.fetch as Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      });

      await act(async () => {
        await actions.endBriefing();
      });

      expect(result.current[0].status).toBe('complete');
    });

    it('calls onComplete callback', async () => {
      const onComplete = vi.fn();
      const { result } = renderHook(() => useBriefing({ onComplete }));
      const [, actions] = result.current;

      await act(async () => {
        await actions.startBriefing('user-123');
      });

      (global.fetch as Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      });

      await act(async () => {
        await actions.endBriefing();
      });

      expect(onComplete).toHaveBeenCalled();
    });

    it('clears silence timers', async () => {
      const { result } = renderHook(() => useBriefing());
      const [, actions] = result.current;

      await act(async () => {
        await actions.startBriefing('user-123');
      });

      act(() => {
        actions.startSilenceDetection();
      });

      (global.fetch as Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      });

      await act(async () => {
        await actions.endBriefing();
      });

      expect(result.current[0].silenceCountdown).toBeNull();
    });
  });

  describe('reset', () => {
    beforeEach(async () => {
      (global.fetch as Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockBriefingResponse,
      });
    });

    it('resets to initial state', async () => {
      const { result } = renderHook(() => useBriefing());
      const [, actions] = result.current;

      await act(async () => {
        await actions.startBriefing('user-123');
      });

      act(() => {
        actions.nextSection();
      });

      expect(result.current[0].currentSectionIndex).toBe(1);
      expect(result.current[0].sections.length).toBe(3);

      act(() => {
        actions.reset();
      });

      expect(result.current[0].status).toBe('idle');
      expect(result.current[0].sections).toEqual([]);
      expect(result.current[0].currentSectionIndex).toBe(0);
    });
  });

  describe('Transcript management', () => {
    beforeEach(async () => {
      (global.fetch as Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockBriefingResponse,
      });
    });

    it('initializes with empty transcript', async () => {
      const { result } = renderHook(() => useBriefing());
      const [, actions] = result.current;

      await act(async () => {
        await actions.startBriefing('user-123');
      });

      expect(result.current[0].transcript).toEqual([]);
    });
  });

  describe('submitQuestion (Q&A)', () => {
    beforeEach(async () => {
      (global.fetch as Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockBriefingResponse,
      });
    });

    it('sets status to qa when submitting', async () => {
      const { result } = renderHook(() => useBriefing());

      await act(async () => {
        await result.current[1].startBriefing('user-123');
      });

      (global.fetch as Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          answer: 'The answer to your question.',
          citations: [],
          follow_up_prompt: 'Any other questions?',
        }),
      });

      // Start submitting question - don't await to capture intermediate state
      let questionPromise: Promise<void>;
      act(() => {
        questionPromise = result.current[1].submitQuestion('What is the OEE?');
      });

      // Status should be 'qa' during processing
      expect(result.current[0].status).toBe('qa');

      // Clean up promise
      await act(async () => {
        await questionPromise;
      });
    });

    it('adds user question to transcript', async () => {
      const { result } = renderHook(() => useBriefing());

      await act(async () => {
        await result.current[1].startBriefing('user-123');
      });

      (global.fetch as Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          answer: 'The answer.',
          citations: [],
          follow_up_prompt: 'Any other questions?',
        }),
      });

      await act(async () => {
        await result.current[1].submitQuestion('What is the OEE?');
      });

      const userEntry = result.current[0].transcript.find(
        (e) => e.type === 'user'
      );
      expect(userEntry?.text).toBe('What is the OEE?');
    });

    it('returns to awaiting_response after answer', async () => {
      const { result } = renderHook(() => useBriefing());

      await act(async () => {
        await result.current[1].startBriefing('user-123');
      });

      (global.fetch as Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          answer: 'The answer.',
          citations: [],
          follow_up_prompt: 'Any other questions?',
        }),
      });

      await act(async () => {
        await result.current[1].submitQuestion('What is the OEE?');
      });

      expect(result.current[0].status).toBe('awaiting_response');
    });
  });

  describe('Cleanup on unmount', () => {
    it('clears timers on unmount', async () => {
      (global.fetch as Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockBriefingResponse,
      });

      const { result, unmount } = renderHook(() => useBriefing());
      const [, actions] = result.current;

      await act(async () => {
        await actions.startBriefing('user-123');
      });

      act(() => {
        actions.startSilenceDetection();
      });

      // Unmount should not throw
      expect(() => unmount()).not.toThrow();
    });
  });
});
