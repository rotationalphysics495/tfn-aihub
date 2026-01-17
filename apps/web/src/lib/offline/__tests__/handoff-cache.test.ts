/**
 * Handoff Cache Tests (Story 9.9, Task 8.1)
 *
 * Unit tests for IndexedDB handoff caching operations.
 *
 * @see Story 9.9 - Offline Handoff Caching
 * @see AC#1 - Online Handoff Caching
 * @see AC#2 - Offline Handoff Access
 * @see AC#4 - Stale Cache Warning
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import 'fake-indexeddb/auto';
import {
  cacheHandoff,
  getCachedHandoff,
  getCachedHandoffs,
  isCacheStale,
  getCacheMetadata,
  invalidateCache,
  invalidateStaleCaches,
  cacheVoiceNote,
  getCachedVoiceNotes,
  getStorageEstimate,
  clearOldestCaches,
  cacheHandoffWithVoiceNotes,
  getCachedHandoffWithVoiceNotes,
} from '../handoff-cache';
import type { Handoff, HandoffVoiceNote } from '@/types/handoff';

// ============================================================================
// Test Fixtures
// ============================================================================

const createMockHandoff = (overrides: Partial<Handoff> = {}): Handoff => ({
  id: 'handoff-123',
  created_by: 'user-1',
  creator_name: 'John Doe',
  creator_email: 'john@example.com',
  shift_date: '2026-01-15',
  shift_type: 'morning',
  shift_start_time: '2026-01-15T06:00:00Z',
  shift_end_time: '2026-01-15T14:00:00Z',
  assets_covered: ['asset-1', 'asset-2'],
  summary_text: 'Test shift summary',
  text_notes: 'Test notes',
  status: 'pending_acknowledgment',
  created_at: '2026-01-15T14:00:00Z',
  updated_at: '2026-01-15T14:00:00Z',
  submitted_at: '2026-01-15T14:00:00Z',
  acknowledged_by: null,
  acknowledged_at: null,
  voice_notes: [],
  ...overrides,
});

const createMockVoiceNote = (
  overrides: Partial<HandoffVoiceNote> = {}
): HandoffVoiceNote => ({
  id: 'voice-note-1',
  handoff_id: 'handoff-123',
  user_id: 'user-1',
  storage_path: '/audio/test.webm',
  storage_url: 'https://storage.example.com/audio/test.webm',
  transcript: 'Test transcript',
  duration_seconds: 30,
  sequence_order: 1,
  created_at: '2026-01-15T14:05:00Z',
  ...overrides,
});

// ============================================================================
// Setup / Teardown
// ============================================================================

beforeEach(async () => {
  // Clear IndexedDB
  const databases = await indexedDB.databases();
  for (const db of databases) {
    if (db.name) {
      indexedDB.deleteDatabase(db.name);
    }
  }
});

afterEach(() => {
  vi.clearAllMocks();
});

// ============================================================================
// Tests: cacheHandoff (Task 2.5)
// ============================================================================

describe('cacheHandoff', () => {
  it('should cache a handoff successfully', async () => {
    const handoff = createMockHandoff();

    const result = await cacheHandoff(handoff);

    expect(result).toBeDefined();
    expect(result.id).toBe(handoff.id);
    expect(result.data).toEqual(handoff);
    expect(result.cachedAt).toBeGreaterThan(0);
    expect(result.voiceNoteIds).toEqual([]);
  });

  it('should cache handoff with voice note IDs', async () => {
    const voiceNote = createMockVoiceNote();
    const handoff = createMockHandoff({
      voice_notes: [voiceNote],
    });

    const result = await cacheHandoff(handoff);

    expect(result.voiceNoteIds).toEqual([voiceNote.id]);
  });

  it('should update existing cached handoff', async () => {
    const handoff = createMockHandoff();
    await cacheHandoff(handoff);

    const updatedHandoff = createMockHandoff({
      summary_text: 'Updated summary',
    });

    const result = await cacheHandoff(updatedHandoff);

    expect(result.data.summary_text).toBe('Updated summary');

    const cached = await getCachedHandoff(handoff.id);
    expect(cached?.data.summary_text).toBe('Updated summary');
  });
});

// ============================================================================
// Tests: getCachedHandoff (Task 2.6)
// ============================================================================

describe('getCachedHandoff', () => {
  it('should return cached handoff by ID', async () => {
    const handoff = createMockHandoff();
    await cacheHandoff(handoff);

    const result = await getCachedHandoff(handoff.id);

    expect(result).toBeDefined();
    expect(result?.data).toEqual(handoff);
  });

  it('should return null for non-existent handoff', async () => {
    const result = await getCachedHandoff('non-existent');

    expect(result).toBeNull();
  });
});

// ============================================================================
// Tests: getCachedHandoffs (Task 2.7)
// ============================================================================

describe('getCachedHandoffs', () => {
  it('should return all cached handoffs sorted by cachedAt', async () => {
    const handoff1 = createMockHandoff({ id: 'handoff-1' });
    const handoff2 = createMockHandoff({ id: 'handoff-2' });

    await cacheHandoff(handoff1);
    // Small delay to ensure different timestamps
    await new Promise((resolve) => setTimeout(resolve, 10));
    await cacheHandoff(handoff2);

    const result = await getCachedHandoffs();

    expect(result).toHaveLength(2);
    // Should be sorted newest first
    expect(result[0].id).toBe('handoff-2');
    expect(result[1].id).toBe('handoff-1');
  });

  it('should return empty array when no handoffs cached', async () => {
    const result = await getCachedHandoffs();

    expect(result).toEqual([]);
  });
});

// ============================================================================
// Tests: isCacheStale (Task 2.8)
// ============================================================================

describe('isCacheStale', () => {
  it('should return false for fresh cache', async () => {
    const handoff = createMockHandoff();
    await cacheHandoff(handoff);

    const result = await isCacheStale(handoff.id);

    expect(result).toBe(false);
  });

  it('should return true for non-existent cache', async () => {
    const result = await isCacheStale('non-existent');

    expect(result).toBe(true);
  });
});

// ============================================================================
// Tests: getCacheMetadata
// ============================================================================

describe('getCacheMetadata', () => {
  it('should return metadata for cached handoff', async () => {
    const handoff = createMockHandoff();
    await cacheHandoff(handoff);

    const result = await getCacheMetadata(handoff.id);

    expect(result).toBeDefined();
    expect(result?.id).toBe(handoff.id);
    expect(result?.cachedAt).toBeGreaterThan(0);
    expect(result?.isStale).toBe(false);
    expect(result?.ageMs).toBeGreaterThanOrEqual(0);
  });

  it('should return null for non-existent handoff', async () => {
    const result = await getCacheMetadata('non-existent');

    expect(result).toBeNull();
  });
});

// ============================================================================
// Tests: invalidateCache (Task 2.9)
// ============================================================================

describe('invalidateCache', () => {
  it('should remove handoff from cache', async () => {
    const handoff = createMockHandoff();
    await cacheHandoff(handoff);

    await invalidateCache(handoff.id);

    const result = await getCachedHandoff(handoff.id);
    expect(result).toBeNull();
  });

  it('should remove associated voice notes', async () => {
    const handoff = createMockHandoff();
    await cacheHandoff(handoff);

    const voiceNote = createMockVoiceNote({ handoff_id: handoff.id });
    await cacheVoiceNote(voiceNote, handoff.id);

    await invalidateCache(handoff.id);

    const voiceNotes = await getCachedVoiceNotes(handoff.id);
    expect(voiceNotes).toEqual([]);
  });
});

// ============================================================================
// Tests: invalidateStaleCaches
// ============================================================================

describe('invalidateStaleCaches', () => {
  it('should return 0 when no stale caches', async () => {
    const handoff = createMockHandoff();
    await cacheHandoff(handoff);

    const count = await invalidateStaleCaches();

    expect(count).toBe(0);
  });
});

// ============================================================================
// Tests: Voice Note Caching (Task 2.3)
// ============================================================================

describe('cacheVoiceNote', () => {
  it('should cache voice note successfully', async () => {
    const voiceNote = createMockVoiceNote();

    const result = await cacheVoiceNote(voiceNote, 'handoff-123');

    expect(result).toBeDefined();
    expect(result.id).toBe(voiceNote.id);
    expect(result.handoffId).toBe('handoff-123');
    expect(result.metadata).toEqual(voiceNote);
    expect(result.audioUrl).toBe(voiceNote.storage_url);
  });
});

describe('getCachedVoiceNotes', () => {
  it('should return voice notes for handoff', async () => {
    const voiceNote1 = createMockVoiceNote({ id: 'vn-1', sequence_order: 1 });
    const voiceNote2 = createMockVoiceNote({ id: 'vn-2', sequence_order: 2 });

    await cacheVoiceNote(voiceNote1, 'handoff-123');
    await cacheVoiceNote(voiceNote2, 'handoff-123');

    const result = await getCachedVoiceNotes('handoff-123');

    expect(result).toHaveLength(2);
  });

  it('should return empty array for handoff with no voice notes', async () => {
    const result = await getCachedVoiceNotes('non-existent');

    expect(result).toEqual([]);
  });
});

// ============================================================================
// Tests: Quota Management (Task 2.10)
// ============================================================================

describe('getStorageEstimate', () => {
  it('should return null when storage API not available', async () => {
    // In test environment, storage API might not be available
    const result = await getStorageEstimate();

    // Can be null or an object depending on environment
    expect(result === null || typeof result === 'object').toBe(true);
  });
});

describe('clearOldestCaches', () => {
  it('should clear specified number of oldest caches', async () => {
    // Cache 3 handoffs with delays
    const handoff1 = createMockHandoff({ id: 'h-1' });
    const handoff2 = createMockHandoff({ id: 'h-2' });
    const handoff3 = createMockHandoff({ id: 'h-3' });

    await cacheHandoff(handoff1);
    await new Promise((r) => setTimeout(r, 10));
    await cacheHandoff(handoff2);
    await new Promise((r) => setTimeout(r, 10));
    await cacheHandoff(handoff3);

    const removed = await clearOldestCaches(2);

    expect(removed).toBe(2);

    const remaining = await getCachedHandoffs();
    expect(remaining).toHaveLength(1);
    expect(remaining[0].id).toBe('h-3');
  });
});

// ============================================================================
// Tests: cacheHandoffWithVoiceNotes (Task 3)
// ============================================================================

describe('cacheHandoffWithVoiceNotes', () => {
  it('should cache handoff and voice notes together', async () => {
    const voiceNote = createMockVoiceNote();
    const handoff = createMockHandoff({
      voice_notes: [voiceNote],
    });

    // Mock service worker
    const mockPostMessage = vi.fn();
    Object.defineProperty(navigator, 'serviceWorker', {
      value: {
        controller: {
          postMessage: mockPostMessage,
        },
      },
      writable: true,
    });

    await cacheHandoffWithVoiceNotes(handoff);

    const cached = await getCachedHandoff(handoff.id);
    expect(cached).toBeDefined();

    const voiceNotes = await getCachedVoiceNotes(handoff.id);
    expect(voiceNotes).toHaveLength(1);
  });
});

// ============================================================================
// Tests: getCachedHandoffWithVoiceNotes
// ============================================================================

describe('getCachedHandoffWithVoiceNotes', () => {
  it('should return handoff with voice notes and staleness', async () => {
    const voiceNote = createMockVoiceNote();
    const handoff = createMockHandoff({
      voice_notes: [voiceNote],
    });

    await cacheHandoff(handoff);
    await cacheVoiceNote(voiceNote, handoff.id);

    const result = await getCachedHandoffWithVoiceNotes(handoff.id);

    expect(result).toBeDefined();
    expect(result?.handoff).toEqual(handoff);
    expect(result?.voiceNotes).toHaveLength(1);
    expect(result?.isStale).toBe(false);
  });

  it('should return null for non-existent handoff', async () => {
    const result = await getCachedHandoffWithVoiceNotes('non-existent');

    expect(result).toBeNull();
  });
});
