/**
 * Offline Sync Queue (Story 9.7)
 *
 * IndexedDB-based queue for offline actions that sync when connectivity returns.
 *
 * @see Story 9.7 - Acknowledgment Flow
 * @see AC#4 - Offline Acknowledgment Queuing (NFR20, NFR21)
 */

// ============================================================================
// Types
// ============================================================================

/**
 * Supported action types for offline queue
 */
export type QueuedActionType = 'acknowledge_handoff';

/**
 * Payload for acknowledge_handoff action
 */
export interface AcknowledgeHandoffPayload {
  handoff_id: string;
  notes?: string;
}

/**
 * Queued action structure (matches Dev Notes schema)
 */
export interface QueuedAction {
  id: string;
  action_type: QueuedActionType;
  payload: AcknowledgeHandoffPayload;
  created_at: string;
  synced: boolean;
  sync_attempts: number;
  last_sync_attempt?: string;
  error_message?: string;
}

/**
 * Sync result from processing an action
 */
export interface SyncResult {
  success: boolean;
  action_id: string;
  error?: string;
}

/**
 * Queue status for UI feedback
 */
export interface QueueStatus {
  pendingCount: number;
  lastSyncAttempt?: string;
  isOnline: boolean;
}

// ============================================================================
// Constants
// ============================================================================

const DB_NAME = 'tfn-aihub-offline';
const DB_VERSION = 1;
const STORE_NAME = 'sync_queue';
const MAX_RETRY_ATTEMPTS = 3;

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
    // Check availability first (handles private browsing, SSR, etc.)
    if (!isIndexedDBAvailable()) {
      reject(new Error('IndexedDB is not available in this environment'));
      return;
    }

    try {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onerror = (event) => {
        const error = (event.target as IDBOpenDBRequest).error;
        // Provide specific error messages for common scenarios
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

        // Create object store for queued actions
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          const store = db.createObjectStore(STORE_NAME, { keyPath: 'id' });

          // Create indexes for efficient querying
          store.createIndex('action_type', 'action_type', { unique: false });
          store.createIndex('synced', 'synced', { unique: false });
          store.createIndex('created_at', 'created_at', { unique: false });
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

/**
 * Generate a UUID for queue items
 */
function generateId(): string {
  return crypto.randomUUID();
}

// ============================================================================
// Queue Operations (Task 5.2)
// ============================================================================

/**
 * Add an action to the offline queue
 */
export async function queueAction(
  actionType: QueuedActionType,
  payload: AcknowledgeHandoffPayload
): Promise<QueuedAction> {
  const db = await openDatabase();

  const action: QueuedAction = {
    id: generateId(),
    action_type: actionType,
    payload,
    created_at: new Date().toISOString(),
    synced: false,
    sync_attempts: 0,
  };

  return new Promise((resolve, reject) => {
    const transaction = db.transaction([STORE_NAME], 'readwrite');
    const store = transaction.objectStore(STORE_NAME);
    const request = store.add(action);

    request.onsuccess = () => {
      resolve(action);
    };

    request.onerror = () => {
      reject(new Error('Failed to queue action'));
    };

    transaction.oncomplete = () => {
      db.close();
    };
  });
}

/**
 * Get all pending (unsynced) actions
 */
export async function getPendingActions(): Promise<QueuedAction[]> {
  const db = await openDatabase();

  return new Promise((resolve, reject) => {
    const transaction = db.transaction([STORE_NAME], 'readonly');
    const store = transaction.objectStore(STORE_NAME);
    const index = store.index('synced');
    const request = index.getAll(IDBKeyRange.only(false));

    request.onsuccess = () => {
      resolve(request.result || []);
    };

    request.onerror = () => {
      reject(new Error('Failed to get pending actions'));
    };

    transaction.oncomplete = () => {
      db.close();
    };
  });
}

/**
 * Mark an action as synced (successful)
 */
export async function markActionSynced(actionId: string): Promise<void> {
  const db = await openDatabase();

  return new Promise((resolve, reject) => {
    const transaction = db.transaction([STORE_NAME], 'readwrite');
    const store = transaction.objectStore(STORE_NAME);
    const getRequest = store.get(actionId);

    getRequest.onsuccess = () => {
      const action = getRequest.result;
      if (action) {
        action.synced = true;
        action.last_sync_attempt = new Date().toISOString();
        const putRequest = store.put(action);

        putRequest.onerror = () => {
          reject(new Error('Failed to update action'));
        };
      }
      resolve();
    };

    getRequest.onerror = () => {
      reject(new Error('Failed to get action'));
    };

    transaction.oncomplete = () => {
      db.close();
    };
  });
}

/**
 * Update action with sync failure
 */
export async function markActionFailed(
  actionId: string,
  errorMessage: string
): Promise<void> {
  const db = await openDatabase();

  return new Promise((resolve, reject) => {
    const transaction = db.transaction([STORE_NAME], 'readwrite');
    const store = transaction.objectStore(STORE_NAME);
    const getRequest = store.get(actionId);

    getRequest.onsuccess = () => {
      const action = getRequest.result;
      if (action) {
        action.sync_attempts += 1;
        action.last_sync_attempt = new Date().toISOString();
        action.error_message = errorMessage;
        const putRequest = store.put(action);

        putRequest.onerror = () => {
          reject(new Error('Failed to update action'));
        };
      }
      resolve();
    };

    getRequest.onerror = () => {
      reject(new Error('Failed to get action'));
    };

    transaction.oncomplete = () => {
      db.close();
    };
  });
}

/**
 * Remove synced actions (cleanup)
 */
export async function removeSyncedActions(): Promise<number> {
  const db = await openDatabase();

  return new Promise((resolve, reject) => {
    const transaction = db.transaction([STORE_NAME], 'readwrite');
    const store = transaction.objectStore(STORE_NAME);
    const index = store.index('synced');
    const request = index.openCursor(IDBKeyRange.only(true));
    let deletedCount = 0;

    request.onsuccess = (event) => {
      const cursor = (event.target as IDBRequest).result;
      if (cursor) {
        cursor.delete();
        deletedCount++;
        cursor.continue();
      }
    };

    transaction.oncomplete = () => {
      db.close();
      resolve(deletedCount);
    };

    transaction.onerror = () => {
      reject(new Error('Failed to remove synced actions'));
    };
  });
}

/**
 * Get queue status for UI feedback
 */
export async function getQueueStatus(): Promise<QueueStatus> {
  const pending = await getPendingActions();
  const lastAction = pending.length > 0 ? pending[pending.length - 1] : null;

  return {
    pendingCount: pending.length,
    lastSyncAttempt: lastAction?.last_sync_attempt,
    isOnline: navigator.onLine,
  };
}

// ============================================================================
// Sync Operations (Task 5.4)
// ============================================================================

/**
 * Process a single queued action
 */
async function processAction(
  action: QueuedAction,
  accessToken: string,
  apiBaseUrl: string
): Promise<SyncResult> {
  if (action.action_type === 'acknowledge_handoff') {
    const payload = action.payload;

    try {
      const response = await fetch(
        `${apiBaseUrl}/api/v1/handoff/${payload.handoff_id}/acknowledge`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ notes: payload.notes }),
        }
      );

      if (response.ok) {
        return { success: true, action_id: action.id };
      }

      // Handle specific error cases
      const errorData = await response.json().catch(() => ({}));
      const errorCode = errorData?.detail?.code || 'UNKNOWN_ERROR';

      // If already acknowledged, treat as success (idempotent)
      if (errorCode === 'ALREADY_ACKNOWLEDGED') {
        return { success: true, action_id: action.id };
      }

      return {
        success: false,
        action_id: action.id,
        error: errorData?.detail?.error || `HTTP ${response.status}`,
      };
    } catch (error) {
      return {
        success: false,
        action_id: action.id,
        error: error instanceof Error ? error.message : 'Network error',
      };
    }
  }

  return {
    success: false,
    action_id: action.id,
    error: `Unknown action type: ${action.action_type}`,
  };
}

/**
 * Sync all pending actions (Task 5.4)
 *
 * Called when connectivity is restored.
 */
export async function syncPendingActions(
  accessToken: string,
  apiBaseUrl: string
): Promise<SyncResult[]> {
  const pending = await getPendingActions();
  const results: SyncResult[] = [];

  for (const action of pending) {
    // Skip actions that have exceeded retry limit
    if (action.sync_attempts >= MAX_RETRY_ATTEMPTS) {
      continue;
    }

    const result = await processAction(action, accessToken, apiBaseUrl);
    results.push(result);

    if (result.success) {
      await markActionSynced(action.id);
    } else {
      await markActionFailed(action.id, result.error || 'Unknown error');
    }
  }

  // Cleanup synced actions
  await removeSyncedActions();

  return results;
}

// ============================================================================
// Online/Offline Event Handlers (Task 5.4)
// ============================================================================

type SyncCallback = (results: SyncResult[]) => void;
let syncCallback: SyncCallback | null = null;
let accessToken: string | null = null;
let apiBaseUrl: string | null = null;

/**
 * Initialize the sync queue with credentials and callback
 */
export function initializeSyncQueue(
  token: string,
  baseUrl: string,
  onSync?: SyncCallback
): void {
  accessToken = token;
  apiBaseUrl = baseUrl;
  syncCallback = onSync || null;

  // Add online event listener
  window.addEventListener('online', handleOnline);
}

/**
 * Cleanup sync queue listeners
 */
export function cleanupSyncQueue(): void {
  window.removeEventListener('online', handleOnline);
  accessToken = null;
  apiBaseUrl = null;
  syncCallback = null;
}

/**
 * Handle coming back online
 */
async function handleOnline(): Promise<void> {
  if (!accessToken || !apiBaseUrl) {
    console.warn('Sync queue not initialized with credentials');
    return;
  }

  try {
    const results = await syncPendingActions(accessToken, apiBaseUrl);

    if (syncCallback && results.length > 0) {
      syncCallback(results);
    }
  } catch (error) {
    console.error('Error syncing pending actions:', error);
  }
}

// ============================================================================
// Convenience Functions for Specific Actions
// ============================================================================

/**
 * Queue an acknowledgment action (Task 5.3)
 */
export async function queueAcknowledgment(
  handoffId: string,
  notes?: string
): Promise<QueuedAction> {
  return queueAction('acknowledge_handoff', {
    handoff_id: handoffId,
    notes,
  });
}

/**
 * Check if there are pending acknowledgments for a handoff
 */
export async function hasPendingAcknowledgment(
  handoffId: string
): Promise<boolean> {
  const pending = await getPendingActions();
  return pending.some(
    (action) =>
      action.action_type === 'acknowledge_handoff' &&
      action.payload.handoff_id === handoffId
  );
}
