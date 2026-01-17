/**
 * Service Worker Registration (Story 9.9, Task 1)
 *
 * Handles Service Worker lifecycle management including registration,
 * updates, and error handling.
 *
 * @see Story 9.9 - Offline Handoff Caching
 * @see AC#1 - Online Handoff Caching
 * @see AC#2 - Offline Handoff Access
 */

// ============================================================================
// Types
// ============================================================================

export interface SWUpdateInfo {
  /** Whether an update is available */
  updateAvailable: boolean;
  /** Registration object if available */
  registration: ServiceWorkerRegistration | null;
}

export type SWMessageType =
  | 'skip-waiting'
  | 'cache-audio'
  | 'invalidate-cache'
  | 'clear-stale-cache';

export interface SWMessage {
  type: SWMessageType;
  payload?: Record<string, unknown>;
}

type UpdateCallback = (info: SWUpdateInfo) => void;
type MessageCallback = (event: MessageEvent) => void;

// ============================================================================
// Module State
// ============================================================================

let registration: ServiceWorkerRegistration | null = null;
let updateCallback: UpdateCallback | null = null;
let messageCallbacks: Set<MessageCallback> = new Set();

// ============================================================================
// Registration Functions (Task 1.2, 1.3, 1.4)
// ============================================================================

/**
 * Check if Service Worker is supported in the current environment
 */
export function isServiceWorkerSupported(): boolean {
  return 'serviceWorker' in navigator;
}

/**
 * Register the Service Worker
 *
 * @returns Promise that resolves to the registration or null if not supported
 */
export async function registerServiceWorker(): Promise<ServiceWorkerRegistration | null> {
  if (!isServiceWorkerSupported()) {
    console.warn('[SW] Service Workers are not supported in this browser');
    return null;
  }

  try {
    registration = await navigator.serviceWorker.register('/sw.js', {
      scope: '/',
    });

    // Listen for updates
    registration.addEventListener('updatefound', handleUpdateFound);

    // Check for existing updates
    if (registration.waiting) {
      notifyUpdateAvailable(registration);
    }

    // Set up message handler
    navigator.serviceWorker.addEventListener('message', handleMessage);

    console.log('[SW] Service Worker registered successfully');
    return registration;
  } catch (error) {
    console.error('[SW] Service Worker registration failed:', error);
    return null;
  }
}

/**
 * Unregister the Service Worker
 */
export async function unregisterServiceWorker(): Promise<boolean> {
  if (!registration) {
    return false;
  }

  try {
    const success = await registration.unregister();
    if (success) {
      registration = null;
      console.log('[SW] Service Worker unregistered');
    }
    return success;
  } catch (error) {
    console.error('[SW] Failed to unregister Service Worker:', error);
    return false;
  }
}

// ============================================================================
// Update Handling (Task 1.5)
// ============================================================================

/**
 * Handle when a new Service Worker is found
 */
function handleUpdateFound(): void {
  if (!registration?.installing) return;

  const installingWorker = registration.installing;

  installingWorker.addEventListener('statechange', () => {
    if (installingWorker.state === 'installed' && navigator.serviceWorker.controller) {
      // New version available
      notifyUpdateAvailable(registration!);
    }
  });
}

/**
 * Notify that an update is available
 */
function notifyUpdateAvailable(reg: ServiceWorkerRegistration): void {
  if (updateCallback) {
    updateCallback({
      updateAvailable: true,
      registration: reg,
    });
  }
}

/**
 * Set callback for update notifications
 *
 * @param callback - Called when an update is available
 */
export function onServiceWorkerUpdate(callback: UpdateCallback): void {
  updateCallback = callback;

  // Check if there's already a waiting worker
  if (registration?.waiting) {
    callback({
      updateAvailable: true,
      registration,
    });
  }
}

/**
 * Activate the waiting Service Worker
 *
 * Call this when the user confirms they want to update.
 */
export function activateUpdate(): void {
  if (registration?.waiting) {
    registration.waiting.postMessage({ type: 'skip-waiting' });
  }
}

/**
 * Reload the page when the Service Worker takes over
 */
export function setupReloadOnControllerChange(): void {
  if (!isServiceWorkerSupported()) return;

  let refreshing = false;

  navigator.serviceWorker.addEventListener('controllerchange', () => {
    if (!refreshing) {
      refreshing = true;
      window.location.reload();
    }
  });
}

// ============================================================================
// Message Handling
// ============================================================================

/**
 * Handle messages from the Service Worker
 */
function handleMessage(event: MessageEvent): void {
  messageCallbacks.forEach((callback) => callback(event));
}

/**
 * Subscribe to messages from the Service Worker
 *
 * @param callback - Called when a message is received
 * @returns Unsubscribe function
 */
export function onServiceWorkerMessage(callback: MessageCallback): () => void {
  messageCallbacks.add(callback);

  return () => {
    messageCallbacks.delete(callback);
  };
}

/**
 * Send a message to the active Service Worker
 *
 * @param message - Message to send
 */
export function postMessageToServiceWorker(message: SWMessage): void {
  if (navigator.serviceWorker.controller) {
    navigator.serviceWorker.controller.postMessage(message);
  }
}

// ============================================================================
// Cache Control Functions
// ============================================================================

/**
 * Request caching of audio URLs
 *
 * @param urls - Audio URLs to cache
 */
export function cacheAudioUrls(urls: string[]): void {
  postMessageToServiceWorker({
    type: 'cache-audio',
    payload: { urls },
  });
}

/**
 * Invalidate a cached URL
 *
 * @param url - URL to invalidate
 */
export function invalidateCacheUrl(url: string): void {
  postMessageToServiceWorker({
    type: 'invalidate-cache',
    payload: { url },
  });
}

/**
 * Clear all stale cache entries
 */
export function clearStaleCache(): void {
  postMessageToServiceWorker({
    type: 'clear-stale-cache',
  });
}

// ============================================================================
// Status Functions
// ============================================================================

/**
 * Get the current Service Worker registration
 */
export function getRegistration(): ServiceWorkerRegistration | null {
  return registration;
}

/**
 * Check if the Service Worker is ready and controlling the page
 */
export function isServiceWorkerActive(): boolean {
  return !!navigator.serviceWorker?.controller;
}

/**
 * Wait for the Service Worker to be ready
 */
export async function waitForServiceWorkerReady(): Promise<ServiceWorkerRegistration | null> {
  if (!isServiceWorkerSupported()) return null;

  try {
    return await navigator.serviceWorker.ready;
  } catch (error) {
    console.error('[SW] Error waiting for Service Worker:', error);
    return null;
  }
}
