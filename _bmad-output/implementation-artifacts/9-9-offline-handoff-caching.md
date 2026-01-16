# Story 9.9: Offline Handoff Caching

Status: ready-for-dev

## Story

As a **Supervisor on the plant floor**,
I want **to review handoffs even without connectivity**,
So that **I can access critical information anywhere in the facility**.

## Acceptance Criteria

### AC1: Online Handoff Caching
**Given** a Supervisor views a handoff online
**When** the handoff loads (FR30)
**Then** it is cached to IndexedDB via Service Worker
**And** cache includes: summary, notes, voice note URLs

### AC2: Offline Handoff Access
**Given** a Supervisor goes offline
**When** they navigate to a cached handoff
**Then** the handoff displays from cache
**And** a banner indicates "Viewing offline - some features limited"

### AC3: Offline Voice Note Playback
**Given** voice notes are cached
**When** played offline
**Then** audio plays from local cache
**And** transcripts display normally

### AC4: Stale Cache Warning
**Given** cache is older than 48 hours
**When** handoff is accessed
**Then** stale data warning is shown
**And** cache is invalidated on next online access

### AC5: Connectivity Restoration Sync
**Given** connectivity is restored
**When** the app detects online status
**Then** cached data is revalidated
**And** any queued acknowledgments are synced (NFR21)

## Tasks / Subtasks

- [ ] **Task 1: Service Worker Setup** (AC: 1, 2)
  - [ ] 1.1: Create `apps/web/public/sw.js` service worker entry point
  - [ ] 1.2: Create `apps/web/src/lib/offline/sw-registration.ts` for Service Worker lifecycle management
  - [ ] 1.3: Implement SW install and activate event handlers
  - [ ] 1.4: Register Service Worker on app load (in app layout or root)
  - [ ] 1.5: Handle SW update notifications and prompt user to refresh

- [ ] **Task 2: IndexedDB Handoff Cache** (AC: 1, 2, 4)
  - [ ] 2.1: Create `apps/web/src/lib/offline/handoff-cache.ts`
  - [ ] 2.2: Define IndexedDB schema: `handoffs` object store with handoff data
  - [ ] 2.3: Define IndexedDB schema: `voice_notes` object store with audio blob references
  - [ ] 2.4: Define IndexedDB schema: `pending_actions` object store for queued acknowledgments
  - [ ] 2.5: Implement `cacheHandoff(handoff)` function to store handoff record
  - [ ] 2.6: Implement `getCachedHandoff(id)` function to retrieve cached handoff
  - [ ] 2.7: Implement `getCachedHandoffs()` function to list all cached handoffs
  - [ ] 2.8: Implement `isCacheStale(handoffId)` function with 48-hour TTL check
  - [ ] 2.9: Implement `invalidateCache(handoffId)` function
  - [ ] 2.10: Handle IndexedDB quota exceeded errors gracefully

- [ ] **Task 3: Voice Note Audio Caching** (AC: 3)
  - [ ] 3.1: Implement Cache API integration for audio files in Service Worker
  - [ ] 3.2: Cache voice note audio URLs when handoff is fetched
  - [ ] 3.3: Serve cached audio from Service Worker when offline
  - [ ] 3.4: Store transcript data alongside audio references in IndexedDB

- [ ] **Task 4: Offline Sync Queue** (AC: 5)
  - [ ] 4.1: Create `apps/web/src/lib/offline/sync-queue.ts`
  - [ ] 4.2: Implement `queueAction(action)` to add pending actions to IndexedDB
  - [ ] 4.3: Implement `getPendingActions()` to retrieve queued actions
  - [ ] 4.4: Implement `syncPendingActions()` to POST queued actions when online
  - [ ] 4.5: Implement `clearSyncedAction(actionId)` to remove synced actions
  - [ ] 4.6: Register Background Sync API handler in Service Worker
  - [ ] 4.7: Handle sync failures with retry logic (max 3 retries)

- [ ] **Task 5: useOfflineSync Hook** (AC: 2, 4, 5)
  - [ ] 5.1: Create `apps/web/src/lib/hooks/useOfflineSync.ts`
  - [ ] 5.2: Implement online/offline status detection using `navigator.onLine`
  - [ ] 5.3: Listen to `online` and `offline` window events
  - [ ] 5.4: Expose `isOnline`, `isOffline`, `pendingSyncCount` state
  - [ ] 5.5: Trigger sync queue processing on `online` event
  - [ ] 5.6: Expose `queueAcknowledgment(handoffId, data)` for offline ack

- [ ] **Task 6: Offline UI Integration** (AC: 2, 4)
  - [ ] 6.1: Create `OfflineBanner` component for "Viewing offline" indicator
  - [ ] 6.2: Create `StaleCacheWarning` component for 48-hour warning
  - [ ] 6.3: Integrate `useOfflineSync` hook into handoff pages
  - [ ] 6.4: Show offline banner when `isOffline` is true
  - [ ] 6.5: Show stale warning when cache age > 48 hours
  - [ ] 6.6: Update `HandoffViewer.tsx` to use cached data when offline
  - [ ] 6.7: Update `HandoffAcknowledge.tsx` to queue offline acknowledgments

- [ ] **Task 7: Cache-Then-Network Strategy** (AC: 1, 5)
  - [ ] 7.1: Implement cache-then-network fetch strategy in Service Worker
  - [ ] 7.2: Return cached response immediately if available
  - [ ] 7.3: Fetch fresh data in background and update cache
  - [ ] 7.4: Notify frontend of data updates via `postMessage`
  - [ ] 7.5: Revalidate stale caches on reconnection

- [ ] **Task 8: Testing** (AC: 1-5)
  - [ ] 8.1: Unit tests for `handoff-cache.ts` IndexedDB operations
  - [ ] 8.2: Unit tests for `sync-queue.ts` queue operations
  - [ ] 8.3: Unit tests for `useOfflineSync.ts` hook
  - [ ] 8.4: Integration tests for offline handoff viewing
  - [ ] 8.5: Integration tests for offline acknowledgment queueing
  - [ ] 8.6: Integration tests for sync-on-reconnect behavior

## Dev Notes

### Critical Architecture Patterns

**From Architecture - Offline Caching (NFR20, NFR21):**
- **Scope:** Shift handoff records ONLY (Morning Briefing requires live data - never cache briefings)
- **Cache Strategy:** cache-then-network for handoffs
- **Cache TTL:** 48 hours for handoff records
- **Audio Caching:** Cache API for audio files (separate from IndexedDB text data)
- **Sync Strategy:** Acknowledgments queued in IndexedDB, synced on reconnect via Background Sync API

**From Implementation Patterns - Offline Rules:**
1. Only cache handoff records, never briefings
2. Acknowledgments queued offline MUST sync on reconnect
3. IndexedDB operations MUST handle quota exceeded errors
4. Service Worker MUST NOT cache API responses except handoffs

**Service Worker Registration Pattern:**
```typescript
// apps/web/src/lib/offline/sw-registration.ts
// Pattern: Register SW on app load, handle updates gracefully

export async function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    try {
      const registration = await navigator.serviceWorker.register('/sw.js');
      // Handle updates...
    } catch (error) {
      console.error('SW registration failed:', error);
    }
  }
}
```

**IndexedDB Schema Pattern:**
```typescript
// apps/web/src/lib/offline/handoff-cache.ts
// IndexedDB stores: handoffs, voice_notes, pending_actions

const DB_NAME = 'tfn-aihub-offline';
const DB_VERSION = 1;

interface CachedHandoff {
  id: string;
  data: ShiftHandoff;
  cachedAt: number; // timestamp
  voiceNoteIds: string[];
}

interface PendingAction {
  id: string;
  type: 'acknowledgment';
  handoffId: string;
  payload: AcknowledgmentPayload;
  createdAt: number;
  retryCount: number;
}
```

### Dependencies from Previous Stories

**From Story 9.4 (Persistent Handoff Records):**
- `shift_handoffs` table exists with handoff data
- `handoff_voice_notes` table links audio files
- Handoff data structure is defined in `apps/api/app/models/handoff.py`

**From Story 9.7 (Acknowledgment Flow):**
- Acknowledgment API endpoint exists at `POST /api/v1/handoff/{id}/acknowledge`
- `HandoffAcknowledge.tsx` component exists for acknowledgment UI
- Offline acknowledgment queueing is explicitly mentioned in 9.7 AC

**From Story 9.3 (Voice Note Attachment):**
- Voice notes stored in Supabase Storage bucket `handoff-voice-notes`
- Audio URLs provided in handoff response
- Transcripts included with audio references

**From Story 9.5 (Handoff Review UI):**
- `HandoffViewer.tsx` component exists
- Audio player with play/pause controls exists
- Tablet-optimized layout exists

### File Structure Requirements

**New Files to Create:**
```
apps/web/
├── public/
│   └── sw.js                        # Service Worker entry point
├── src/
│   └── lib/
│       ├── offline/                 # NEW: Offline support module
│       │   ├── handoff-cache.ts     # IndexedDB operations for handoffs
│       │   ├── sync-queue.ts        # Offline action queue
│       │   └── sw-registration.ts   # Service Worker lifecycle management
│       └── hooks/
│           └── useOfflineSync.ts    # Offline sync status hook
```

**Files to Modify:**
```
apps/web/src/
├── app/
│   └── layout.tsx                   # Register Service Worker on app load
├── components/
│   └── handoff/
│       ├── HandoffViewer.tsx        # Add offline data fallback
│       └── HandoffAcknowledge.tsx   # Add offline queue support
```

### Technical Specifications

**Service Worker Fetch Strategy:**
```javascript
// sw.js - cache-then-network for handoff API routes
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Only cache handoff-related requests
  if (url.pathname.includes('/api/v1/handoff/')) {
    event.respondWith(
      caches.match(event.request).then((cachedResponse) => {
        // Return cached immediately, fetch fresh in background
        const fetchPromise = fetch(event.request).then((networkResponse) => {
          // Update cache with fresh data
          return networkResponse;
        });
        return cachedResponse || fetchPromise;
      })
    );
  }
});
```

**Background Sync Pattern:**
```javascript
// sw.js - Background Sync for offline acknowledgments
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-acknowledgments') {
    event.waitUntil(syncPendingAcknowledgments());
  }
});
```

**Online/Offline Detection Pattern:**
```typescript
// useOfflineSync.ts
export function useOfflineSync() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      // Trigger sync
      syncPendingActions();
    };
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return { isOnline, isOffline: !isOnline };
}
```

### NFR Compliance

- **NFR20 (Offline caching):** Handoffs cached to IndexedDB for offline access
- **NFR21 (Auto-sync on reconnect):** Background Sync API + online event listener
- **Cache TTL:** 48 hours as specified in architecture
- **Audio Caching:** Cache API for audio files, separate from IndexedDB text

### Error Handling Requirements

1. **Quota Exceeded:** Gracefully handle IndexedDB quota errors, prioritize recent handoffs
2. **Sync Failures:** Retry up to 3 times with exponential backoff
3. **Stale Data:** Clear warning to user, invalidate on next online access
4. **SW Registration Failure:** App continues to work, just without offline support

### Testing Considerations

1. Use `fake-indexeddb` for unit testing IndexedDB operations
2. Mock `navigator.onLine` and online/offline events for hook tests
3. Use Service Worker test harness for SW integration tests
4. Test offline scenarios in Chrome DevTools Network tab

### Project Structure Notes

- Alignment with unified project structure: New `lib/offline/` module follows established pattern
- Hooks location: `lib/hooks/` exists at `/apps/web/src/hooks/`, may need to move to `lib/hooks/` for consistency with architecture
- Service Worker: Must be in `public/` folder for Next.js to serve at root

### References

- [Source: _bmad/bmm/data/architecture/voice-briefing.md#Offline-Caching-Architecture]
- [Source: _bmad/bmm/data/architecture/implementation-patterns.md#Offline-Rules]
- [Source: _bmad-output/planning-artifacts/epic-9.md#Story-9.9]
- [Source: _bmad/bmm/data/prd.md#NFR20-NFR21]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
