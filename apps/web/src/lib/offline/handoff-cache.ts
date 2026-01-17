/**
 * Handoff Cache (Story 9.9, Task 2)
 *
 * IndexedDB operations for caching handoffs offline.
 *
 * @see Story 9.9 - Offline Handoff Caching
 * @see AC#1 - Online Handoff Caching
 * @see AC#2 - Offline Handoff Access
 * @see AC#4 - Stale Cache Warning
 */

import type { Handoff, HandoffVoiceNote } from '@/types/handoff';

// ============================================================================
// Types
// ============================================================================

/**
 * Cached handoff record with metadata
 */
export interface CachedHandoff {
  id: string;
  data: Handoff;
  cachedAt: number;
  voiceNoteIds: string[];
}

/**
 * Cached voice note with audio blob
 */
export interface CachedVoiceNote {
  id: string;
  handoffId: string;
  metadata: HandoffVoiceNote;
  audioUrl: string;
  cachedAt: number;
}

/**
 * Cache entry metadata
 */
export interface CacheMetadata {
  id: string;
  cachedAt: number;
  isStale: boolean;
  ageMs: number;
}

// ============================================================================
// Constants
// ============================================================================

const DB_NAME = 'tfn-aihub-offline';
const DB_VERSION = 2; // Increment to add handoffs and voice_notes stores
const HANDOFFS_STORE = 'handoffs';
const VOICE_NOTES_STORE = 'voice_notes';
const PENDING_ACTIONS_STORE = 'pending_actions';

// Cache TTL: 48 hours
const CACHE_TTL_MS = 48 * 60 * 60 * 1000;

// ============================================================================
// IndexedDB Helpers
// ============================================================================

/**
 * Check if IndexedDB is available in the current environment
 */
function isIndexedDBAvailable(): boolean {
  try {
    return typeof indexedDB !== 'undefined' && indexedDB !== null;
  } catch {
    return false;
  }
}

/**
 * Open the IndexedDB database with proper error handling
 */
function openDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (!isIndexedDBAvailable()) {
      reject(new Error('IndexedDB is not available in this environment'));
      return;
    }

    try {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onerror = (event) => {
        const error = (event.target as IDBOpenDBRequest).error;
        if (error?.name === 'QuotaExceededError') {
          reject(new Error('Storage quota exceeded. Please free up space.'));
        } else if (error?.name === 'SecurityError') {
          reject(new Error('IndexedDB access denied. Check browser privacy settings.'));
        } else {
          reject(new Error(`Failed to open IndexedDB: ${error?.message || 'Unknown error'}`));
        }
      };

      request.onsuccess = () => {
        resolve(request.result);
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;

        // Create handoffs store (Task 2.2)
        if (!db.objectStoreNames.contains(HANDOFFS_STORE)) {
          const handoffsStore = db.createObjectStore(HANDOFFS_STORE, { keyPath: 'id' });
          handoffsStore.createIndex('cachedAt', 'cachedAt', { unique: false });
        }

        // Create voice_notes store (Task 2.3)
        if (!db.objectStoreNames.contains(VOICE_NOTES_STORE)) {
          const voiceNotesStore = db.createObjectStore(VOICE_NOTES_STORE, { keyPath: 'id' });
          voiceNotesStore.createIndex('handoffId', 'handoffId', { unique: false });
          voiceNotesStore.createIndex('cachedAt', 'cachedAt', { unique: false });
        }

        // Create pending_actions store if not exists (Task 2.4 - from sync-queue.ts)
        if (!db.objectStoreNames.contains(PENDING_ACTIONS_STORE)) {
          const actionsStore = db.createObjectStore(PENDING_ACTIONS_STORE, { keyPath: 'id' });
          actionsStore.createIndex('action_type', 'action_type', { unique: false });
          actionsStore.createIndex('synced', 'synced', { unique: false });
          actionsStore.createIndex('created_at', 'created_at', { unique: false });
        }
      };

      request.onblocked = () => {
        reject(new Error('Database upgrade blocked. Please close other tabs using this app.'));
      };
    } catch (err) {
      reject(new Error(`Failed to initialize IndexedDB: ${err instanceof Error ? err.message : 'Unknown error'}`));
    }
  });
}

// ============================================================================
// Handoff Cache Operations (Task 2.5, 2.6, 2.7)
// ============================================================================

/**
 * Cache a handoff record (Task 2.5)
 *
 * @param handoff - Handoff data to cache
 * @returns The cached handoff record
 */
export async function cacheHandoff(handoff: Handoff): Promise<CachedHandoff> {
  const db = await openDatabase();

  const cachedHandoff: CachedHandoff = {
    id: handoff.id,
    data: handoff,
    cachedAt: Date.now(),
    voiceNoteIds: handoff.voice_notes.map((vn) => vn.id),
  };

  return new Promise((resolve, reject) => {
    const transaction = db.transaction([HANDOFFS_STORE], 'readwrite');
    const store = transaction.objectStore(HANDOFFS_STORE);
    const request = store.put(cachedHandoff);

    request.onsuccess = () => {
      resolve(cachedHandoff);
    };

    request.onerror = (event) => {
      const error = (event.target as IDBRequest).error;
      if (error?.name === 'QuotaExceededError') {
        reject(new Error('Storage quota exceeded. Try clearing old cached handoffs.'));
      } else {
        reject(new Error('Failed to cache handoff'));
      }
    };

    transaction.oncomplete = () => {
      db.close();
    };
  });
}

/**
 * Get a cached handoff by ID (Task 2.6)
 *
 * @param id - Handoff ID
 * @returns Cached handoff or null if not found
 */
export async function getCachedHandoff(id: string): Promise<CachedHandoff | null> {
  const db = await openDatabase();

  return new Promise((resolve, reject) => {
    const transaction = db.transaction([HANDOFFS_STORE], 'readonly');
    const store = transaction.objectStore(HANDOFFS_STORE);
    const request = store.get(id);

    request.onsuccess = () => {
      resolve(request.result || null);
    };

    request.onerror = () => {
      reject(new Error('Failed to get cached handoff'));
    };

    transaction.oncomplete = () => {
      db.close();
    };
  });
}

/**
 * Get all cached handoffs (Task 2.7)
 *
 * @returns Array of cached handoffs sorted by cachedAt (newest first)
 */
export async function getCachedHandoffs(): Promise<CachedHandoff[]> {
  const db = await openDatabase();

  return new Promise((resolve, reject) => {
    const transaction = db.transaction([HANDOFFS_STORE], 'readonly');
    const store = transaction.objectStore(HANDOFFS_STORE);
    const request = store.getAll();

    request.onsuccess = () => {
      const handoffs = request.result || [];
      // Sort by cachedAt descending (newest first)
      handoffs.sort((a, b) => b.cachedAt - a.cachedAt);
      resolve(handoffs);
    };

    request.onerror = () => {
      reject(new Error('Failed to get cached handoffs'));
    };

    transaction.oncomplete = () => {
      db.close();
    };
  });
}

// ============================================================================
// Cache Staleness Operations (Task 2.8, 2.9)
// ============================================================================

/**
 * Check if a cached handoff is stale (Task 2.8)
 *
 * @param handoffId - Handoff ID to check
 * @returns Whether the cache is stale (older than 48 hours)
 */
export async function isCacheStale(handoffId: string): Promise<boolean> {
  const cached = await getCachedHandoff(handoffId);

  if (!cached) {
    return true; // No cache = stale
  }

  const age = Date.now() - cached.cachedAt;
  return age > CACHE_TTL_MS;
}

/**
 * Get cache metadata including staleness info
 *
 * @param handoffId - Handoff ID
 * @returns Cache metadata or null if not cached
 */
export async function getCacheMetadata(handoffId: string): Promise<CacheMetadata | null> {
  const cached = await getCachedHandoff(handoffId);

  if (!cached) {
    return null;
  }

  const ageMs = Date.now() - cached.cachedAt;

  return {
    id: handoffId,
    cachedAt: cached.cachedAt,
    isStale: ageMs > CACHE_TTL_MS,
    ageMs,
  };
}

/**
 * Invalidate a cached handoff (Task 2.9)
 *
 * @param handoffId - Handoff ID to invalidate
 */
export async function invalidateCache(handoffId: string): Promise<void> {
  const db = await openDatabase();

  return new Promise((resolve, reject) => {
    const transaction = db.transaction([HANDOFFS_STORE, VOICE_NOTES_STORE], 'readwrite');

    // Delete handoff
    const handoffsStore = transaction.objectStore(HANDOFFS_STORE);
    handoffsStore.delete(handoffId);

    // Delete associated voice notes
    const voiceNotesStore = transaction.objectStore(VOICE_NOTES_STORE);
    const voiceNotesIndex = voiceNotesStore.index('handoffId');
    const request = voiceNotesIndex.openCursor(IDBKeyRange.only(handoffId));

    request.onsuccess = (event) => {
      const cursor = (event.target as IDBRequest).result;
      if (cursor) {
        cursor.delete();
        cursor.continue();
      }
    };

    transaction.oncomplete = () => {
      db.close();
      resolve();
    };

    transaction.onerror = () => {
      reject(new Error('Failed to invalidate cache'));
    };
  });
}

/**
 * Invalidate all stale caches
 *
 * @returns Number of invalidated entries
 */
export async function invalidateStaleCaches(): Promise<number> {
  const handoffs = await getCachedHandoffs();
  let invalidatedCount = 0;

  for (const handoff of handoffs) {
    const age = Date.now() - handoff.cachedAt;
    if (age > CACHE_TTL_MS) {
      await invalidateCache(handoff.id);
      invalidatedCount++;
    }
  }

  return invalidatedCount;
}

// ============================================================================
// Voice Note Cache Operations (Task 2.3)
// ============================================================================

/**
 * Cache a voice note
 *
 * @param voiceNote - Voice note metadata
 * @param handoffId - Parent handoff ID
 * @returns The cached voice note record
 */
export async function cacheVoiceNote(
  voiceNote: HandoffVoiceNote,
  handoffId: string
): Promise<CachedVoiceNote> {
  const db = await openDatabase();

  const cachedVoiceNote: CachedVoiceNote = {
    id: voiceNote.id,
    handoffId,
    metadata: voiceNote,
    audioUrl: voiceNote.storage_url || '',
    cachedAt: Date.now(),
  };

  return new Promise((resolve, reject) => {
    const transaction = db.transaction([VOICE_NOTES_STORE], 'readwrite');
    const store = transaction.objectStore(VOICE_NOTES_STORE);
    const request = store.put(cachedVoiceNote);

    request.onsuccess = () => {
      resolve(cachedVoiceNote);
    };

    request.onerror = () => {
      reject(new Error('Failed to cache voice note'));
    };

    transaction.oncomplete = () => {
      db.close();
    };
  });
}

/**
 * Get cached voice notes for a handoff
 *
 * @param handoffId - Handoff ID
 * @returns Array of cached voice notes
 */
export async function getCachedVoiceNotes(handoffId: string): Promise<CachedVoiceNote[]> {
  const db = await openDatabase();

  return new Promise((resolve, reject) => {
    const transaction = db.transaction([VOICE_NOTES_STORE], 'readonly');
    const store = transaction.objectStore(VOICE_NOTES_STORE);
    const index = store.index('handoffId');
    const request = index.getAll(IDBKeyRange.only(handoffId));

    request.onsuccess = () => {
      resolve(request.result || []);
    };

    request.onerror = () => {
      reject(new Error('Failed to get cached voice notes'));
    };

    transaction.oncomplete = () => {
      db.close();
    };
  });
}

// ============================================================================
// Quota Management (Task 2.10)
// ============================================================================

/**
 * Get estimated storage usage
 *
 * @returns Storage estimate in bytes or null if not available
 */
export async function getStorageEstimate(): Promise<{ usage: number; quota: number } | null> {
  if ('storage' in navigator && 'estimate' in navigator.storage) {
    try {
      const estimate = await navigator.storage.estimate();
      return {
        usage: estimate.usage || 0,
        quota: estimate.quota || 0,
      };
    } catch {
      return null;
    }
  }
  return null;
}

/**
 * Clear oldest cached handoffs to free space
 *
 * @param count - Number of handoffs to remove (default: 5)
 * @returns Number of removed entries
 */
export async function clearOldestCaches(count: number = 5): Promise<number> {
  const handoffs = await getCachedHandoffs();

  // Sort by cachedAt ascending (oldest first)
  const oldest = [...handoffs].sort((a, b) => a.cachedAt - b.cachedAt).slice(0, count);

  for (const handoff of oldest) {
    await invalidateCache(handoff.id);
  }

  return oldest.length;
}

/**
 * Check if storage is running low and clear if necessary
 *
 * @param thresholdPercent - Threshold percentage (default: 80%)
 * @returns Whether cleanup was performed
 */
export async function checkAndCleanStorage(thresholdPercent: number = 80): Promise<boolean> {
  const estimate = await getStorageEstimate();

  if (!estimate) {
    return false;
  }

  const usagePercent = (estimate.usage / estimate.quota) * 100;

  if (usagePercent >= thresholdPercent) {
    // First, clear stale caches
    await invalidateStaleCaches();

    // If still over threshold, clear oldest
    const newEstimate = await getStorageEstimate();
    if (newEstimate && (newEstimate.usage / newEstimate.quota) * 100 >= thresholdPercent) {
      await clearOldestCaches(5);
    }

    return true;
  }

  return false;
}

// ============================================================================
// Full Handoff Caching with Voice Notes (Task 3)
// ============================================================================

/**
 * Cache a handoff with all its voice notes and audio (Task 3.2, 3.4)
 *
 * This caches:
 * 1. Handoff data to IndexedDB
 * 2. Voice note metadata to IndexedDB
 * 3. Voice note audio URLs to Service Worker Cache API
 *
 * @param handoff - Handoff to cache
 */
export async function cacheHandoffWithVoiceNotes(handoff: Handoff): Promise<void> {
  // 1. Cache handoff data
  await cacheHandoff(handoff);

  // 2. Cache voice note metadata and request audio caching
  const audioUrls: string[] = [];

  for (const voiceNote of handoff.voice_notes) {
    await cacheVoiceNote(voiceNote, handoff.id);

    if (voiceNote.storage_url) {
      audioUrls.push(voiceNote.storage_url);
    }
  }

  // 3. Request Service Worker to cache audio files
  if (audioUrls.length > 0 && 'serviceWorker' in navigator && navigator.serviceWorker.controller) {
    navigator.serviceWorker.controller.postMessage({
      type: 'cache-audio',
      payload: { urls: audioUrls },
    });
  }
}

/**
 * Get a cached handoff with voice notes for offline display
 *
 * @param handoffId - Handoff ID
 * @returns Handoff with voice notes or null
 */
export async function getCachedHandoffWithVoiceNotes(
  handoffId: string
): Promise<{ handoff: Handoff; voiceNotes: CachedVoiceNote[]; isStale: boolean } | null> {
  const cached = await getCachedHandoff(handoffId);

  if (!cached) {
    return null;
  }

  const voiceNotes = await getCachedVoiceNotes(handoffId);
  const isStale = await isCacheStale(handoffId);

  return {
    handoff: cached.data,
    voiceNotes,
    isStale,
  };
}
