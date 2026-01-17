/**
 * Service Worker for Offline Handoff Caching (Story 9.9)
 *
 * Provides offline access to shift handoffs with cache-then-network strategy.
 *
 * @see Story 9.9 - Offline Handoff Caching
 * @see AC#1 - Online Handoff Caching
 * @see AC#2 - Offline Handoff Access
 * @see AC#3 - Offline Voice Note Playback
 * @see AC#5 - Connectivity Restoration Sync
 */

// ============================================================================
// Constants
// ============================================================================

const CACHE_NAME = 'tfn-aihub-handoff-v1';
const AUDIO_CACHE_NAME = 'tfn-aihub-audio-v1';

// Routes to cache (handoff-related only)
const HANDOFF_API_PATTERN = /\/api\/v1\/handoff\//;
const AUDIO_URL_PATTERN = /handoff-voice-notes/;

// Cache TTL: 48 hours
const CACHE_TTL_MS = 48 * 60 * 60 * 1000;

// ============================================================================
// Install Event
// ============================================================================

self.addEventListener('install', (event) => {
  // Skip waiting to activate immediately
  self.skipWaiting();
});

// ============================================================================
// Activate Event
// ============================================================================

self.addEventListener('activate', (event) => {
  event.waitUntil(
    (async () => {
      // Clean up old caches
      const cacheNames = await caches.keys();
      await Promise.all(
        cacheNames
          .filter((name) => name.startsWith('tfn-aihub-') && name !== CACHE_NAME && name !== AUDIO_CACHE_NAME)
          .map((name) => caches.delete(name))
      );

      // Take control of all clients
      await self.clients.claim();
    })()
  );
});

// ============================================================================
// Fetch Event - Cache-Then-Network Strategy
// ============================================================================

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Only cache GET requests
  if (event.request.method !== 'GET') {
    return;
  }

  // Handle handoff API requests (AC#1, AC#2)
  if (HANDOFF_API_PATTERN.test(url.pathname)) {
    event.respondWith(handleHandoffRequest(event.request));
    return;
  }

  // Handle voice note audio files (AC#3)
  if (AUDIO_URL_PATTERN.test(url.pathname) || AUDIO_URL_PATTERN.test(url.href)) {
    event.respondWith(handleAudioRequest(event.request));
    return;
  }
});

// ============================================================================
// Handoff Request Handler (Cache-Then-Network)
// ============================================================================

/**
 * Handle handoff API requests with cache-then-network strategy
 *
 * @param {Request} request - The fetch request
 * @returns {Promise<Response>}
 */
async function handleHandoffRequest(request) {
  const cache = await caches.open(CACHE_NAME);

  // Try to get cached response first
  const cachedResponse = await cache.match(request);

  // Fetch from network in background
  const networkPromise = fetch(request)
    .then(async (networkResponse) => {
      if (networkResponse.ok) {
        // Clone response before caching (response can only be consumed once)
        const responseToCache = networkResponse.clone();

        // Add timestamp header for TTL tracking
        const headers = new Headers(responseToCache.headers);
        headers.set('sw-cached-at', Date.now().toString());

        const body = await responseToCache.blob();
        const cachedResponseWithTimestamp = new Response(body, {
          status: responseToCache.status,
          statusText: responseToCache.statusText,
          headers,
        });

        await cache.put(request, cachedResponseWithTimestamp);

        // Notify clients of cache update
        notifyClients('cache-updated', { url: request.url });
      }
      return networkResponse;
    })
    .catch((error) => {
      console.warn('[SW] Network fetch failed:', error);
      return null;
    });

  // Return cached response immediately if available
  if (cachedResponse) {
    // Check if cache is stale (AC#4)
    const cachedAt = cachedResponse.headers.get('sw-cached-at');
    if (cachedAt) {
      const age = Date.now() - parseInt(cachedAt, 10);
      if (age > CACHE_TTL_MS) {
        // Cache is stale - notify clients
        notifyClients('cache-stale', { url: request.url, age });
      }
    }

    return cachedResponse;
  }

  // No cache, wait for network
  const networkResponse = await networkPromise;
  if (networkResponse) {
    return networkResponse;
  }

  // Both cache and network failed
  return new Response(
    JSON.stringify({
      error: 'Offline and no cached data available',
      offline: true,
    }),
    {
      status: 503,
      headers: { 'Content-Type': 'application/json' },
    }
  );
}

// ============================================================================
// Audio Request Handler (AC#3)
// ============================================================================

/**
 * Handle voice note audio requests
 *
 * @param {Request} request - The fetch request
 * @returns {Promise<Response>}
 */
async function handleAudioRequest(request) {
  const cache = await caches.open(AUDIO_CACHE_NAME);

  // Try cache first
  const cachedResponse = await cache.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }

  // Fetch from network and cache
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      await cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    console.warn('[SW] Audio fetch failed:', error);
    return new Response(null, {
      status: 503,
      statusText: 'Audio not available offline',
    });
  }
}

// ============================================================================
// Background Sync for Acknowledgments (AC#5)
// ============================================================================

self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-acknowledgments') {
    event.waitUntil(syncPendingAcknowledgments());
  }
});

/**
 * Sync pending acknowledgments from IndexedDB
 */
async function syncPendingAcknowledgments() {
  // Notify clients to trigger sync (main thread has IndexedDB access)
  notifyClients('sync-requested', { type: 'acknowledgments' });
}

// ============================================================================
// Push Notification Handling
// ============================================================================

self.addEventListener('push', (event) => {
  if (!event.data) return;

  const data = event.data.json();

  event.waitUntil(
    self.registration.showNotification(data.title || 'TFN AIHub', {
      body: data.body,
      icon: '/icon-192.png',
      badge: '/badge-72.png',
      data: data.data,
    })
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  const url = event.notification.data?.url || '/';

  event.waitUntil(
    self.clients.matchAll({ type: 'window' }).then((clients) => {
      // Try to focus existing window
      for (const client of clients) {
        if (client.url === url && 'focus' in client) {
          return client.focus();
        }
      }
      // Open new window
      if (self.clients.openWindow) {
        return self.clients.openWindow(url);
      }
    })
  );
});

// ============================================================================
// Message Handler
// ============================================================================

self.addEventListener('message', (event) => {
  const { type, payload } = event.data || {};

  switch (type) {
    case 'skip-waiting':
      self.skipWaiting();
      break;

    case 'cache-audio':
      // Pre-cache audio URLs for offline access (AC#3)
      cacheAudioUrls(payload.urls);
      break;

    case 'invalidate-cache':
      // Invalidate specific cache entry (AC#4)
      invalidateCache(payload.url);
      break;

    case 'clear-stale-cache':
      // Clear all stale cache entries
      clearStaleCache();
      break;
  }
});

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Notify all clients with a message
 */
async function notifyClients(type, payload) {
  const clients = await self.clients.matchAll({ type: 'window' });
  clients.forEach((client) => {
    client.postMessage({ type, payload });
  });
}

/**
 * Pre-cache audio URLs for offline access
 *
 * @param {string[]} urls - Audio URLs to cache
 */
async function cacheAudioUrls(urls) {
  if (!urls || urls.length === 0) return;

  const cache = await caches.open(AUDIO_CACHE_NAME);

  for (const url of urls) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        await cache.put(url, response);
      }
    } catch (error) {
      console.warn('[SW] Failed to cache audio:', url, error);
    }
  }
}

/**
 * Invalidate a specific cache entry
 *
 * @param {string} url - URL to invalidate
 */
async function invalidateCache(url) {
  const cache = await caches.open(CACHE_NAME);
  await cache.delete(url);
}

/**
 * Clear all stale cache entries (older than 48 hours)
 */
async function clearStaleCache() {
  const cache = await caches.open(CACHE_NAME);
  const requests = await cache.keys();

  for (const request of requests) {
    const response = await cache.match(request);
    if (response) {
      const cachedAt = response.headers.get('sw-cached-at');
      if (cachedAt) {
        const age = Date.now() - parseInt(cachedAt, 10);
        if (age > CACHE_TTL_MS) {
          await cache.delete(request);
        }
      }
    }
  }
}
