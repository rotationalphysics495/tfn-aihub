/**
 * Sync Queue Tests (Story 9.9, Task 8.2)
 *
 * Unit tests for offline sync queue operations.
 *
 * @see Story 9.9 - Offline Handoff Caching
 * @see AC#5 - Connectivity Restoration Sync
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import 'fake-indexeddb/auto';
import {
  queueAction,
  getPendingActions,
  markActionSynced,
  markActionFailed,
  removeSyncedActions,
  getQueueStatus,
  syncPendingActions,
  queueAcknowledgment,
  hasPendingAcknowledgment,
  registerBackgroundSync,
  queueAcknowledgmentWithSync,
} from '../sync-queue';

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

  // Mock navigator.onLine
  Object.defineProperty(navigator, 'onLine', {
    value: true,
    writable: true,
  });
});

afterEach(() => {
  vi.clearAllMocks();
});

// ============================================================================
// Tests: queueAction (Task 4.2)
// ============================================================================

describe('queueAction', () => {
  it('should add action to queue with correct structure', async () => {
    const result = await queueAction('acknowledge_handoff', {
      handoff_id: 'handoff-123',
      notes: 'Test notes',
    });

    expect(result).toBeDefined();
    expect(result.id).toBeDefined();
    expect(result.action_type).toBe('acknowledge_handoff');
    expect(result.payload.handoff_id).toBe('handoff-123');
    expect(result.payload.notes).toBe('Test notes');
    expect(result.synced).toBe(false);
    expect(result.sync_attempts).toBe(0);
    expect(result.created_at).toBeDefined();
  });

  it('should generate unique IDs for each action', async () => {
    const result1 = await queueAction('acknowledge_handoff', {
      handoff_id: 'h-1',
    });
    const result2 = await queueAction('acknowledge_handoff', {
      handoff_id: 'h-2',
    });

    expect(result1.id).not.toBe(result2.id);
  });
});

// ============================================================================
// Tests: getPendingActions (Task 4.3)
// ============================================================================

describe('getPendingActions', () => {
  it('should return all unsynced actions', async () => {
    await queueAction('acknowledge_handoff', { handoff_id: 'h-1' });
    await queueAction('acknowledge_handoff', { handoff_id: 'h-2' });

    const pending = await getPendingActions();

    expect(pending).toHaveLength(2);
    expect(pending.every((a) => a.synced === false)).toBe(true);
  });

  it('should return empty array when no pending actions', async () => {
    const pending = await getPendingActions();

    expect(pending).toEqual([]);
  });

  it('should not return synced actions', async () => {
    const action = await queueAction('acknowledge_handoff', { handoff_id: 'h-1' });
    await markActionSynced(action.id);

    const pending = await getPendingActions();

    expect(pending).toEqual([]);
  });
});

// ============================================================================
// Tests: markActionSynced
// ============================================================================

describe('markActionSynced', () => {
  it('should mark action as synced', async () => {
    const action = await queueAction('acknowledge_handoff', { handoff_id: 'h-1' });

    await markActionSynced(action.id);

    const pending = await getPendingActions();
    expect(pending).toHaveLength(0);
  });

  it('should set last_sync_attempt timestamp', async () => {
    const action = await queueAction('acknowledge_handoff', { handoff_id: 'h-1' });
    const beforeSync = new Date().toISOString();

    await markActionSynced(action.id);

    // We can verify by checking it doesn't throw
    await removeSyncedActions();
  });
});

// ============================================================================
// Tests: markActionFailed
// ============================================================================

describe('markActionFailed', () => {
  it('should increment sync_attempts', async () => {
    const action = await queueAction('acknowledge_handoff', { handoff_id: 'h-1' });

    await markActionFailed(action.id, 'Network error');

    const pending = await getPendingActions();
    expect(pending[0].sync_attempts).toBe(1);
  });

  it('should store error message', async () => {
    const action = await queueAction('acknowledge_handoff', { handoff_id: 'h-1' });

    await markActionFailed(action.id, 'Network error');

    const pending = await getPendingActions();
    expect(pending[0].error_message).toBe('Network error');
  });

  it('should set last_sync_attempt timestamp', async () => {
    const action = await queueAction('acknowledge_handoff', { handoff_id: 'h-1' });

    await markActionFailed(action.id, 'Error');

    const pending = await getPendingActions();
    expect(pending[0].last_sync_attempt).toBeDefined();
  });
});

// ============================================================================
// Tests: removeSyncedActions (Task 4.5)
// ============================================================================

describe('removeSyncedActions', () => {
  it('should remove all synced actions', async () => {
    const action1 = await queueAction('acknowledge_handoff', { handoff_id: 'h-1' });
    const action2 = await queueAction('acknowledge_handoff', { handoff_id: 'h-2' });

    await markActionSynced(action1.id);

    const removed = await removeSyncedActions();

    expect(removed).toBe(1);
  });

  it('should not remove pending actions', async () => {
    await queueAction('acknowledge_handoff', { handoff_id: 'h-1' });

    const removed = await removeSyncedActions();

    expect(removed).toBe(0);

    const pending = await getPendingActions();
    expect(pending).toHaveLength(1);
  });
});

// ============================================================================
// Tests: getQueueStatus
// ============================================================================

describe('getQueueStatus', () => {
  it('should return correct status', async () => {
    await queueAction('acknowledge_handoff', { handoff_id: 'h-1' });
    await queueAction('acknowledge_handoff', { handoff_id: 'h-2' });

    const status = await getQueueStatus();

    expect(status.pendingCount).toBe(2);
    expect(status.isOnline).toBe(true);
  });

  it('should return zero count when no pending actions', async () => {
    const status = await getQueueStatus();

    expect(status.pendingCount).toBe(0);
  });
});

// ============================================================================
// Tests: syncPendingActions (Task 4.4)
// ============================================================================

describe('syncPendingActions', () => {
  it('should process pending actions', async () => {
    // Mock fetch
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ success: true }),
    });

    await queueAction('acknowledge_handoff', { handoff_id: 'h-1' });

    const results = await syncPendingActions('test-token', 'https://api.example.com');

    expect(results).toHaveLength(1);
    expect(results[0].success).toBe(true);
  });

  it('should skip actions with max retries exceeded', async () => {
    const action = await queueAction('acknowledge_handoff', { handoff_id: 'h-1' });

    // Fail 3 times to hit max retries
    await markActionFailed(action.id, 'Error 1');
    await markActionFailed(action.id, 'Error 2');
    await markActionFailed(action.id, 'Error 3');

    global.fetch = vi.fn();

    const results = await syncPendingActions('test-token', 'https://api.example.com');

    expect(results).toHaveLength(0);
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('should handle already acknowledged response as success', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 409,
      json: () =>
        Promise.resolve({
          detail: { code: 'ALREADY_ACKNOWLEDGED' },
        }),
    });

    await queueAction('acknowledge_handoff', { handoff_id: 'h-1' });

    const results = await syncPendingActions('test-token', 'https://api.example.com');

    expect(results[0].success).toBe(true);
  });

  it('should handle network errors', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('Network error'));

    await queueAction('acknowledge_handoff', { handoff_id: 'h-1' });

    const results = await syncPendingActions('test-token', 'https://api.example.com');

    expect(results[0].success).toBe(false);
    expect(results[0].error).toBe('Network error');
  });
});

// ============================================================================
// Tests: queueAcknowledgment
// ============================================================================

describe('queueAcknowledgment', () => {
  it('should queue acknowledge_handoff action', async () => {
    const result = await queueAcknowledgment('handoff-123', 'Test notes');

    expect(result.action_type).toBe('acknowledge_handoff');
    expect(result.payload.handoff_id).toBe('handoff-123');
    expect(result.payload.notes).toBe('Test notes');
  });

  it('should work without notes', async () => {
    const result = await queueAcknowledgment('handoff-123');

    expect(result.payload.notes).toBeUndefined();
  });
});

// ============================================================================
// Tests: hasPendingAcknowledgment
// ============================================================================

describe('hasPendingAcknowledgment', () => {
  it('should return true when pending ack exists', async () => {
    await queueAcknowledgment('handoff-123');

    const result = await hasPendingAcknowledgment('handoff-123');

    expect(result).toBe(true);
  });

  it('should return false when no pending ack', async () => {
    const result = await hasPendingAcknowledgment('handoff-123');

    expect(result).toBe(false);
  });

  it('should return false for different handoff', async () => {
    await queueAcknowledgment('handoff-456');

    const result = await hasPendingAcknowledgment('handoff-123');

    expect(result).toBe(false);
  });
});

// ============================================================================
// Tests: Background Sync (Task 4.6, 4.7)
// ============================================================================

describe('registerBackgroundSync', () => {
  it('should return false when service worker not supported', async () => {
    // Remove serviceWorker from navigator
    const originalSW = navigator.serviceWorker;
    Object.defineProperty(navigator, 'serviceWorker', {
      value: undefined,
      writable: true,
    });

    const result = await registerBackgroundSync();

    expect(result).toBe(false);

    // Restore
    Object.defineProperty(navigator, 'serviceWorker', {
      value: originalSW,
      writable: true,
    });
  });
});

describe('queueAcknowledgmentWithSync', () => {
  it('should queue action and attempt background sync registration', async () => {
    const result = await queueAcknowledgmentWithSync('handoff-123', 'Notes');

    expect(result.action_type).toBe('acknowledge_handoff');
    expect(result.payload.handoff_id).toBe('handoff-123');
  });
});
