/**
 * Push Notification Setup (Story 9.12)
 *
 * Provides functions for managing Web Push subscriptions:
 * - Request push permission from browser
 * - Subscribe to push notifications
 * - Store subscription in Supabase
 * - Unsubscribe and cleanup
 *
 * Task 4: Frontend Push Subscription Management (AC: 1)
 * - 4.1: Create apps/web/src/lib/notifications/push-setup.ts
 * - 4.2: Implement requestPushPermission() function
 * - 4.3: Implement subscribeToPush() to register with browser
 * - 4.4: Store subscription in Supabase push_subscriptions table
 * - 4.5: Implement unsubscribeFromPush() for cleanup
 * - 4.6: Handle permission denied gracefully
 *
 * References:
 * - [Source: architecture/voice-briefing.md#Push-Notifications-Architecture]
 * - [Source: epic-9.md#Story-9.12]
 */

import { createClient } from '@/lib/supabase/client';

/**
 * Push subscription status.
 */
export type PushPermissionStatus = 'granted' | 'denied' | 'default' | 'unsupported';

/**
 * Result of push subscription operations.
 */
export interface PushSubscriptionResult {
  success: boolean;
  status: PushPermissionStatus;
  subscription?: PushSubscription;
  error?: string;
}

/**
 * Convert a URL-safe base64 string to a Uint8Array.
 * Used for VAPID public key conversion.
 */
function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');

  const rawData = atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

/**
 * Check if push notifications are supported in the current browser.
 */
export function isPushSupported(): boolean {
  return (
    'serviceWorker' in navigator &&
    'PushManager' in window &&
    'Notification' in window
  );
}

/**
 * Get the current push permission status.
 */
export function getPushPermissionStatus(): PushPermissionStatus {
  if (!isPushSupported()) {
    return 'unsupported';
  }
  return Notification.permission as PushPermissionStatus;
}

/**
 * Request push notification permission from the browser.
 * Task 4.2: Implement requestPushPermission() function
 * Task 4.6: Handle permission denied gracefully
 *
 * @returns Promise resolving to the permission status
 */
export async function requestPushPermission(): Promise<PushPermissionStatus> {
  if (!isPushSupported()) {
    console.warn('Push notifications not supported in this browser');
    return 'unsupported';
  }

  // Check current status
  const currentStatus = Notification.permission;
  if (currentStatus === 'granted' || currentStatus === 'denied') {
    return currentStatus as PushPermissionStatus;
  }

  try {
    // Request permission
    const result = await Notification.requestPermission();
    return result as PushPermissionStatus;
  } catch (error) {
    console.error('Error requesting push permission:', error);
    return 'denied';
  }
}

/**
 * Get the existing push subscription from the service worker.
 */
export async function getExistingSubscription(): Promise<PushSubscription | null> {
  if (!isPushSupported()) {
    return null;
  }

  try {
    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();
    return subscription;
  } catch (error) {
    console.error('Error getting existing subscription:', error);
    return null;
  }
}

/**
 * Subscribe to push notifications.
 * Task 4.3: Implement subscribeToPush() to register with browser
 * Task 4.4: Store subscription in Supabase push_subscriptions table
 *
 * @param vapidPublicKey - The VAPID public key for authentication
 * @returns Promise resolving to the subscription result
 */
export async function subscribeToPush(
  vapidPublicKey: string
): Promise<PushSubscriptionResult> {
  // Check browser support
  if (!isPushSupported()) {
    return {
      success: false,
      status: 'unsupported',
      error: 'Push notifications are not supported in this browser',
    };
  }

  // Request permission if not already granted
  const permission = await requestPushPermission();
  if (permission !== 'granted') {
    return {
      success: false,
      status: permission,
      error:
        permission === 'denied'
          ? 'Push notification permission was denied. Please enable notifications in your browser settings.'
          : 'Push notification permission not granted',
    };
  }

  try {
    // Wait for service worker to be ready
    const registration = await navigator.serviceWorker.ready;

    // Check for existing subscription
    let subscription = await registration.pushManager.getSubscription();

    if (!subscription) {
      // Create new subscription
      subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(vapidPublicKey),
      });
    }

    // Store subscription in Supabase
    const stored = await storeSubscription(subscription);
    if (!stored.success) {
      return {
        success: false,
        status: 'granted',
        error: stored.error || 'Failed to store subscription',
      };
    }

    return {
      success: true,
      status: 'granted',
      subscription,
    };
  } catch (error) {
    console.error('Error subscribing to push:', error);
    return {
      success: false,
      status: 'granted',
      error: error instanceof Error ? error.message : 'Failed to subscribe to push notifications',
    };
  }
}

/**
 * Store a push subscription in the Supabase database.
 * Task 4.4: Store subscription in Supabase push_subscriptions table
 */
async function storeSubscription(
  subscription: PushSubscription
): Promise<{ success: boolean; error?: string }> {
  try {
    const supabase = createClient();

    // Get current user
    const {
      data: { user },
      error: authError,
    } = await supabase.auth.getUser();

    if (authError || !user) {
      return {
        success: false,
        error: 'You must be logged in to enable push notifications',
      };
    }

    // Extract subscription data
    const subscriptionJson = subscription.toJSON();
    const keys = subscriptionJson.keys as Record<string, string>;

    if (!keys?.p256dh || !keys?.auth) {
      return {
        success: false,
        error: 'Invalid subscription: missing encryption keys',
      };
    }

    // Upsert subscription (update if endpoint exists, insert if new)
    const { error: dbError } = await supabase.from('push_subscriptions').upsert(
      {
        user_id: user.id,
        endpoint: subscription.endpoint,
        p256dh: keys.p256dh,
        auth_key: keys.auth,
        user_agent: navigator.userAgent,
        device_id: generateDeviceId(),
        updated_at: new Date().toISOString(),
      },
      {
        onConflict: 'user_id,endpoint',
      }
    );

    if (dbError) {
      console.error('Error storing subscription:', dbError);
      return {
        success: false,
        error: 'Failed to save push subscription',
      };
    }

    return { success: true };
  } catch (error) {
    console.error('Error storing subscription:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Generate a simple device identifier for managing multiple devices.
 */
function generateDeviceId(): string {
  // Use stored device ID if available
  const stored = localStorage.getItem('tfn_device_id');
  if (stored) {
    return stored;
  }

  // Generate new device ID
  const deviceId = `device_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
  localStorage.setItem('tfn_device_id', deviceId);
  return deviceId;
}

/**
 * Unsubscribe from push notifications.
 * Task 4.5: Implement unsubscribeFromPush() for cleanup
 *
 * @returns Promise resolving to success status
 */
export async function unsubscribeFromPush(): Promise<{ success: boolean; error?: string }> {
  if (!isPushSupported()) {
    return {
      success: false,
      error: 'Push notifications are not supported',
    };
  }

  try {
    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();

    if (!subscription) {
      // No subscription to remove
      return { success: true };
    }

    // Unsubscribe from browser
    const unsubscribed = await subscription.unsubscribe();
    if (!unsubscribed) {
      return {
        success: false,
        error: 'Failed to unsubscribe from push notifications',
      };
    }

    // Remove from database
    const supabase = createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (user) {
      await supabase
        .from('push_subscriptions')
        .delete()
        .eq('user_id', user.id)
        .eq('endpoint', subscription.endpoint);
    }

    return { success: true };
  } catch (error) {
    console.error('Error unsubscribing from push:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Check if the current user has an active push subscription.
 */
export async function hasPushSubscription(): Promise<boolean> {
  if (!isPushSupported()) {
    return false;
  }

  try {
    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();
    return subscription !== null;
  } catch {
    return false;
  }
}

/**
 * Get push subscription status including database sync status.
 */
export async function getPushSubscriptionStatus(): Promise<{
  supported: boolean;
  permission: PushPermissionStatus;
  subscribed: boolean;
  syncedToDb: boolean;
}> {
  const supported = isPushSupported();
  const permission = getPushPermissionStatus();

  if (!supported) {
    return {
      supported: false,
      permission: 'unsupported',
      subscribed: false,
      syncedToDb: false,
    };
  }

  try {
    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();
    const subscribed = subscription !== null;

    // Check if synced to database
    let syncedToDb = false;
    if (subscribed && subscription) {
      const supabase = createClient();
      const { data: { user } } = await supabase.auth.getUser();

      if (user) {
        const { data } = await supabase
          .from('push_subscriptions')
          .select('id')
          .eq('user_id', user.id)
          .eq('endpoint', subscription.endpoint)
          .single();

        syncedToDb = data !== null;
      }
    }

    return {
      supported,
      permission,
      subscribed,
      syncedToDb,
    };
  } catch {
    return {
      supported,
      permission,
      subscribed: false,
      syncedToDb: false,
    };
  }
}

export default {
  isPushSupported,
  getPushPermissionStatus,
  requestPushPermission,
  subscribeToPush,
  unsubscribeFromPush,
  hasPushSubscription,
  getPushSubscriptionStatus,
  getExistingSubscription,
};
