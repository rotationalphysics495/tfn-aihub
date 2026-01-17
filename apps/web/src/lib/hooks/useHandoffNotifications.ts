/**
 * useHandoffNotifications Hook (Story 9.8)
 *
 * React hook for managing handoff acknowledgment notifications.
 * Provides real-time updates, unread counts, and notification management.
 *
 * AC#1: Acknowledgment Notification Trigger - real-time subscription
 * AC#2: In-App Notification - immediate display on acknowledgment
 * AC#4: Notification on next visit - fetch pending notifications
 *
 * References:
 * - [Source: architecture/voice-briefing.md#Push-Notifications-Architecture]
 * - [Source: epic-9.md#Story-9.8]
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import {
  HandoffNotificationHandler,
  createHandoffNotificationHandler,
  Notification,
  HandoffAckEvent,
  formatNotificationMessage,
  getNotificationUrl,
} from '../notifications/handoff';

/**
 * Hook state.
 */
export interface UseHandoffNotificationsState {
  notifications: Notification[];
  unreadCount: number;
  isLoading: boolean;
  error: string | null;
  hasNewNotification: boolean;
  latestNotification: Notification | null;
}

/**
 * Hook configuration.
 */
export interface UseHandoffNotificationsConfig {
  /** Supabase URL */
  supabaseUrl?: string;
  /** Supabase anon key */
  supabaseKey?: string;
  /** User ID to subscribe for */
  userId: string | null;
  /** Auto-subscribe on mount */
  autoSubscribe?: boolean;
  /** Callback when new notification arrives */
  onNotification?: (notification: Notification) => void;
  /** Callback when acknowledgment event occurs */
  onAcknowledgment?: (event: HandoffAckEvent) => void;
  /** Callback for errors */
  onError?: (error: string) => void;
}

/**
 * Hook actions.
 */
export interface UseHandoffNotificationsActions {
  /** Subscribe to notifications */
  subscribe: () => Promise<void>;
  /** Unsubscribe from notifications */
  unsubscribe: () => Promise<void>;
  /** Refresh notifications list */
  refresh: () => Promise<void>;
  /** Mark notification as read */
  markAsRead: (notificationId: string) => Promise<void>;
  /** Mark all as read */
  markAllAsRead: () => Promise<void>;
  /** Dismiss notification */
  dismiss: (notificationId: string) => Promise<void>;
  /** Clear new notification flag */
  acknowledgeNew: () => void;
  /** Format notification message */
  formatMessage: (notification: Notification) => string;
  /** Get notification URL */
  getUrl: (notification: Notification) => string | null;
}

/**
 * Initial state.
 */
const initialState: UseHandoffNotificationsState = {
  notifications: [],
  unreadCount: 0,
  isLoading: false,
  error: null,
  hasNewNotification: false,
  latestNotification: null,
};

/**
 * useHandoffNotifications hook.
 *
 * Provides real-time notification management for handoff acknowledgments.
 *
 * @param config - Configuration options
 * @returns [state, actions] tuple
 */
export function useHandoffNotifications(
  config: UseHandoffNotificationsConfig
): [UseHandoffNotificationsState, UseHandoffNotificationsActions] {
  const {
    supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '',
    supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '',
    userId,
    autoSubscribe = true,
    onNotification,
    onAcknowledgment,
    onError,
  } = config;

  // State
  const [state, setState] = useState<UseHandoffNotificationsState>(initialState);

  // Handler ref
  const handlerRef = useRef<HandoffNotificationHandler | null>(null);

  /**
   * Handle new notification event.
   */
  const handleNotification = useCallback(
    (notification: Notification) => {
      setState((prev) => ({
        ...prev,
        notifications: [notification, ...prev.notifications],
        unreadCount: prev.unreadCount + 1,
        hasNewNotification: true,
        latestNotification: notification,
      }));

      onNotification?.(notification);
    },
    [onNotification]
  );

  /**
   * Handle acknowledgment event.
   */
  const handleAcknowledgment = useCallback(
    (event: HandoffAckEvent) => {
      onAcknowledgment?.(event);
    },
    [onAcknowledgment]
  );

  /**
   * Handle errors.
   */
  const handleError = useCallback(
    (error: string) => {
      setState((prev) => ({ ...prev, error }));
      onError?.(error);
    },
    [onError]
  );

  /**
   * Initialize handler.
   */
  const initHandler = useCallback(() => {
    if (!userId || !supabaseUrl || !supabaseKey) {
      return null;
    }

    if (handlerRef.current) {
      return handlerRef.current;
    }

    const handler = createHandoffNotificationHandler({
      supabaseUrl,
      supabaseKey,
      userId,
      handlers: {
        onNotification: handleNotification,
        onAcknowledgment: handleAcknowledgment,
        onError: handleError,
      },
    });

    handlerRef.current = handler;
    return handler;
  }, [
    userId,
    supabaseUrl,
    supabaseKey,
    handleNotification,
    handleAcknowledgment,
    handleError,
  ]);

  /**
   * Subscribe to notifications.
   */
  const subscribe = useCallback(async () => {
    const handler = initHandler();
    if (!handler) return;

    await handler.subscribe();
  }, [initHandler]);

  /**
   * Unsubscribe from notifications.
   */
  const unsubscribe = useCallback(async () => {
    if (handlerRef.current) {
      await handlerRef.current.unsubscribe();
    }
  }, []);

  /**
   * Refresh notifications list.
   */
  const refresh = useCallback(async () => {
    const handler = initHandler();
    if (!handler) return;

    setState((prev) => ({ ...prev, isLoading: true, error: null }));

    try {
      const { notifications, total } = await handler.getNotifications(50, 0);
      const unreadCount = await handler.getUnreadCount();

      setState((prev) => ({
        ...prev,
        notifications,
        unreadCount,
        isLoading: false,
      }));
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Failed to fetch notifications';
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }));
    }
  }, [initHandler]);

  /**
   * Mark notification as read.
   */
  const markAsRead = useCallback(async (notificationId: string) => {
    const handler = handlerRef.current;
    if (!handler) return;

    const success = await handler.markAsRead(notificationId);

    if (success) {
      setState((prev) => ({
        ...prev,
        notifications: prev.notifications.map((n) =>
          n.id === notificationId
            ? { ...n, is_read: true, read_at: new Date().toISOString() }
            : n
        ),
        unreadCount: Math.max(0, prev.unreadCount - 1),
      }));
    }
  }, []);

  /**
   * Mark all notifications as read.
   */
  const markAllAsRead = useCallback(async () => {
    const handler = handlerRef.current;
    if (!handler) return;

    const success = await handler.markAllAsRead();

    if (success) {
      setState((prev) => ({
        ...prev,
        notifications: prev.notifications.map((n) => ({
          ...n,
          is_read: true,
          read_at: new Date().toISOString(),
        })),
        unreadCount: 0,
      }));
    }
  }, []);

  /**
   * Dismiss notification.
   */
  const dismiss = useCallback(async (notificationId: string) => {
    const handler = handlerRef.current;
    if (!handler) return;

    const success = await handler.dismissNotification(notificationId);

    if (success) {
      setState((prev) => ({
        ...prev,
        notifications: prev.notifications.filter((n) => n.id !== notificationId),
        unreadCount: prev.notifications.find((n) => n.id === notificationId)?.is_read
          ? prev.unreadCount
          : Math.max(0, prev.unreadCount - 1),
      }));
    }
  }, []);

  /**
   * Acknowledge new notification.
   */
  const acknowledgeNew = useCallback(() => {
    setState((prev) => ({
      ...prev,
      hasNewNotification: false,
    }));
  }, []);

  /**
   * Format notification message.
   */
  const formatMessage = useCallback((notification: Notification) => {
    return formatNotificationMessage(notification);
  }, []);

  /**
   * Get notification URL.
   */
  const getUrl = useCallback((notification: Notification) => {
    return getNotificationUrl(notification);
  }, []);

  /**
   * Effect: Auto-subscribe and fetch on mount.
   */
  useEffect(() => {
    if (!userId) {
      setState(initialState);
      return;
    }

    if (autoSubscribe) {
      subscribe();
      refresh();
    }

    return () => {
      unsubscribe();
    };
  }, [userId, autoSubscribe, subscribe, refresh, unsubscribe]);

  /**
   * Effect: Clean up handler on unmount.
   */
  useEffect(() => {
    return () => {
      if (handlerRef.current) {
        handlerRef.current.unsubscribe();
        handlerRef.current = null;
      }
    };
  }, []);

  // Actions object
  const actions: UseHandoffNotificationsActions = {
    subscribe,
    unsubscribe,
    refresh,
    markAsRead,
    markAllAsRead,
    dismiss,
    acknowledgeNew,
    formatMessage,
    getUrl,
  };

  return [state, actions];
}

export default useHandoffNotifications;
