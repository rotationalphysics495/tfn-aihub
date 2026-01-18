/**
 * Service Worker for Offline Handoff Caching and Push Notifications
 *
 * Provides:
 * - Offline access to shift handoffs with cache-then-network strategy (Story 9.9)
 * - Push notification handling for EOD reminders (Story 9.12)
 *
 * @see Story 9.9 - Offline Handoff Caching
 * @see Story 9.12 - EOD Push Notification Reminders
 * @see AC#1 - Online Handoff Caching
 * @see AC#2 - Offline Handoff Access / Notification Tap Navigation
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
// Push Notification Handling (Story 9.8, 9.12)
// ============================================================================

/**
 * Handle incoming push notifications
 * Task 5.1-5.4: Push event listener with EOD support (Story 9.12)
 * AC#1: Push Notification Trigger - display notification
 */
self.addEventListener('push', (event) => {
  if (!event.data) return;

  let data;
  try {
    data = event.data.json();
  } catch (e) {
    console.warn('[SW] Failed to parse push data:', e);
    return;
  }

  // Build notification options based on notification type
  const notificationType = data.data?.type || 'general';
  const options = buildNotificationOptions(data, notificationType);

  event.waitUntil(
    self.registration.showNotification(data.title || 'TFN AIHub', options)
  );
});

/**
 * Build notification options based on type.
 * Task 5.3: Display notification with title and body
 * Task 5.4: Include EOD deep link in notification data
 *
 * @param {Object} data - Push notification data
 * @param {string} notificationType - Type of notification
 * @returns {Object} Notification options
 */
function buildNotificationOptions(data, notificationType) {
  const baseOptions = {
    body: data.body,
    icon: data.icon || '/icon-192.png',
    badge: data.badge || '/badge-72.png',
    data: data.data || {},
    tag: data.tag,
  };

  // EOD reminder specific options (Story 9.12)
  if (notificationType === 'eod_reminder') {
    return {
      ...baseOptions,
      icon: '/icons/eod-reminder-192.png',
      requireInteraction: true, // Keep visible until user interacts
      actions: [
        { action: 'view', title: 'View Summary' },
        { action: 'dismiss', title: 'Dismiss' },
      ],
      // Ensure URL is set for EOD page
      data: {
        ...baseOptions.data,
        url: data.data?.url || '/briefing/eod',
      },
    };
  }

  // Handoff acknowledgment specific options (Story 9.8)
  if (notificationType === 'handoff_acknowledged') {
    return {
      ...baseOptions,
      icon: '/icons/handoff-ack-192.png',
      actions: data.actions || [{ action: 'view', title: 'View Details' }],
    };
  }

  return baseOptions;
}

/**
 * Handle notification click events.
 * Task 5.5: Handle notification click to navigate to /briefing/eod
 * AC#2: Notification Tap Navigation - EOD summary page displayed directly
 */
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  // Handle action buttons
  const action = event.action;
  const notificationType = event.notification.data?.type;

  // If user clicked dismiss action, just close
  if (action === 'dismiss') {
    return;
  }

  // Get URL to navigate to
  let url = event.notification.data?.url || '/';

  // For EOD reminders, always navigate to EOD page
  if (notificationType === 'eod_reminder') {
    url = '/briefing/eod';
  }

  // For handoff notifications, navigate to specific handoff
  if (notificationType === 'handoff_acknowledged' && event.notification.data?.handoff_id) {
    url = `/handoff/${event.notification.data.handoff_id}`;
  }

  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windowClients) => {
      // Try to find existing window with matching URL
      for (const client of windowClients) {
        const clientUrl = new URL(client.url);
        if (clientUrl.pathname === url || clientUrl.pathname.startsWith(url)) {
          // Focus existing window and navigate if needed
          return client.focus().then((focusedClient) => {
            if (focusedClient && 'navigate' in focusedClient) {
              return focusedClient.navigate(url);
            }
            return focusedClient;
          });
        }
      }

      // Try to find any existing app window
      for (const client of windowClients) {
        if ('focus' in client) {
          return client.focus().then((focusedClient) => {
            if (focusedClient && 'navigate' in focusedClient) {
              return focusedClient.navigate(url);
            }
            return focusedClient;
          });
        }
      }

      // No existing window, open new one
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
