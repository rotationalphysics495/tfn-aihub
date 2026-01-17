/**
 * Handoff Notification Handler (Story 9.8)
 *
 * Provides real-time subscription for handoff acknowledgment notifications
 * and in-app notification display.
 *
 * Task 2: Create in-app notification handler (AC: 1, 2, 4)
 * - 2.1: Create notification handler
 * - 2.2: Set up Supabase Realtime subscription
 * - 2.3: Filter subscription to handoffs created by current user
 * - 2.4: Handle incoming acknowledgment events and display toast
 * - 2.5: Store pending notifications for display on next app visit
 * - 2.6: Implement notification dismiss and mark-as-read
 *
 * References:
 * - [Source: architecture/voice-briefing.md#Push-Notifications-Architecture]
 * - [Source: epic-9.md#Story-9.8]
 */

import { createClient, RealtimeChannel, SupabaseClient } from '@supabase/supabase-js';

/**
 * Notification record from the database.
 */
export interface Notification {
  id: string;
  user_id: string;
  notification_type: string;
  title: string;
  message: string | null;
  entity_type: string | null;
  entity_id: string | null;
  metadata: Record<string, unknown>;
  is_read: boolean;
  read_at: string | null;
  is_dismissed: boolean;
  dismissed_at: string | null;
  created_at: string;
}

/**
 * Handoff acknowledgment event from realtime subscription.
 */
export interface HandoffAckEvent {
  id: string;
  handoff_id: string;
  acknowledged_by: string;
  acknowledged_at: string;
  notes: string | null;
  created_at: string;
}

/**
 * Notification display callback type.
 */
export type NotificationDisplayCallback = (notification: Notification) => void;

/**
 * Notification event handlers.
 */
export interface NotificationHandlers {
  onNotification?: NotificationDisplayCallback;
  onAcknowledgment?: (event: HandoffAckEvent) => void;
  onError?: (error: string) => void;
}

/**
 * Configuration for the notification handler.
 */
export interface NotificationHandlerConfig {
  supabaseUrl: string;
  supabaseKey: string;
  userId: string;
  handlers?: NotificationHandlers;
}

/**
 * Handoff Notification Handler
 *
 * Manages real-time subscriptions and in-app notifications for
 * handoff acknowledgments.
 */
export class HandoffNotificationHandler {
  private supabase: SupabaseClient;
  private userId: string;
  private handlers: NotificationHandlers;
  private notificationChannel: RealtimeChannel | null = null;
  private acknowledgmentChannel: RealtimeChannel | null = null;
  private isSubscribed = false;

  constructor(config: NotificationHandlerConfig) {
    this.supabase = createClient(config.supabaseUrl, config.supabaseKey);
    this.userId = config.userId;
    this.handlers = config.handlers || {};
  }

  /**
   * Subscribe to notifications and acknowledgment events.
   * Task 2.2: Set up Supabase Realtime subscription
   */
  async subscribe(): Promise<void> {
    if (this.isSubscribed) {
      return;
    }

    // Task 2.2: Subscribe to notifications table for this user
    this.notificationChannel = this.supabase
      .channel(`notifications:${this.userId}`)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'notifications',
          filter: `user_id=eq.${this.userId}`,
        },
        (payload) => this.handleNotificationInsert(payload.new as Notification)
      )
      .subscribe((status) => {
        if (status === 'SUBSCRIBED') {
          console.log('Subscribed to notifications');
        } else if (status === 'CHANNEL_ERROR') {
          this.handlers.onError?.('Failed to subscribe to notifications');
        }
      });

    // Task 2.3: Subscribe to acknowledgments for handoffs created by current user
    // This requires a more complex query that we handle via notifications table instead
    // The Edge Function creates the notification record

    this.isSubscribed = true;
  }

  /**
   * Unsubscribe from all channels.
   */
  async unsubscribe(): Promise<void> {
    if (this.notificationChannel) {
      await this.supabase.removeChannel(this.notificationChannel);
      this.notificationChannel = null;
    }

    if (this.acknowledgmentChannel) {
      await this.supabase.removeChannel(this.acknowledgmentChannel);
      this.acknowledgmentChannel = null;
    }

    this.isSubscribed = false;
  }

  /**
   * Handle notification insert event.
   * Task 2.4: Handle incoming events and display toast
   */
  private handleNotificationInsert(notification: Notification): void {
    // Filter for handoff acknowledgment notifications
    if (notification.notification_type === 'handoff_acknowledged') {
      // AC#1: Notification received for acknowledgment
      this.handlers.onNotification?.(notification);

      // If there's an onAcknowledgment handler, extract the event data
      if (this.handlers.onAcknowledgment && notification.metadata) {
        const event: HandoffAckEvent = {
          id: notification.metadata.acknowledgment_id as string,
          handoff_id: notification.entity_id as string,
          acknowledged_by: notification.metadata.acknowledging_user_id as string,
          acknowledged_at: notification.metadata.acknowledged_at as string,
          notes: notification.metadata.has_notes ? 'Notes attached' : null,
          created_at: notification.created_at,
        };
        this.handlers.onAcknowledgment(event);
      }
    }
  }

  /**
   * Fetch unread notifications for the user.
   * Task 2.5: Store pending notifications for display on next app visit
   */
  async getUnreadNotifications(): Promise<Notification[]> {
    const { data, error } = await this.supabase
      .from('notifications')
      .select('*')
      .eq('user_id', this.userId)
      .eq('is_read', false)
      .eq('is_dismissed', false)
      .order('created_at', { ascending: false })
      .limit(50);

    if (error) {
      console.error('Error fetching unread notifications:', error);
      this.handlers.onError?.(`Failed to fetch notifications: ${error.message}`);
      return [];
    }

    return data as Notification[];
  }

  /**
   * Get all notifications for the user (paginated).
   */
  async getNotifications(
    limit = 20,
    offset = 0
  ): Promise<{ notifications: Notification[]; total: number }> {
    // Get total count
    const { count, error: countError } = await this.supabase
      .from('notifications')
      .select('*', { count: 'exact', head: true })
      .eq('user_id', this.userId);

    if (countError) {
      console.error('Error counting notifications:', countError);
      return { notifications: [], total: 0 };
    }

    // Get notifications
    const { data, error } = await this.supabase
      .from('notifications')
      .select('*')
      .eq('user_id', this.userId)
      .order('created_at', { ascending: false })
      .range(offset, offset + limit - 1);

    if (error) {
      console.error('Error fetching notifications:', error);
      this.handlers.onError?.(`Failed to fetch notifications: ${error.message}`);
      return { notifications: [], total: 0 };
    }

    return {
      notifications: data as Notification[],
      total: count || 0,
    };
  }

  /**
   * Mark a notification as read.
   * Task 2.6: Implement mark-as-read functionality
   */
  async markAsRead(notificationId: string): Promise<boolean> {
    const { error } = await this.supabase
      .from('notifications')
      .update({
        is_read: true,
        read_at: new Date().toISOString(),
      })
      .eq('id', notificationId)
      .eq('user_id', this.userId);

    if (error) {
      console.error('Error marking notification as read:', error);
      this.handlers.onError?.(`Failed to mark as read: ${error.message}`);
      return false;
    }

    return true;
  }

  /**
   * Mark all notifications as read.
   */
  async markAllAsRead(): Promise<boolean> {
    const { error } = await this.supabase
      .from('notifications')
      .update({
        is_read: true,
        read_at: new Date().toISOString(),
      })
      .eq('user_id', this.userId)
      .eq('is_read', false);

    if (error) {
      console.error('Error marking all notifications as read:', error);
      this.handlers.onError?.(`Failed to mark all as read: ${error.message}`);
      return false;
    }

    return true;
  }

  /**
   * Dismiss a notification (hide from display).
   * Task 2.6: Implement notification dismiss functionality
   */
  async dismissNotification(notificationId: string): Promise<boolean> {
    const { error } = await this.supabase
      .from('notifications')
      .update({
        is_dismissed: true,
        dismissed_at: new Date().toISOString(),
      })
      .eq('id', notificationId)
      .eq('user_id', this.userId);

    if (error) {
      console.error('Error dismissing notification:', error);
      this.handlers.onError?.(`Failed to dismiss: ${error.message}`);
      return false;
    }

    return true;
  }

  /**
   * Get the count of unread notifications.
   */
  async getUnreadCount(): Promise<number> {
    const { count, error } = await this.supabase
      .from('notifications')
      .select('*', { count: 'exact', head: true })
      .eq('user_id', this.userId)
      .eq('is_read', false)
      .eq('is_dismissed', false);

    if (error) {
      console.error('Error getting unread count:', error);
      return 0;
    }

    return count || 0;
  }
}

/**
 * Create a handoff notification handler instance.
 */
export function createHandoffNotificationHandler(
  config: NotificationHandlerConfig
): HandoffNotificationHandler {
  return new HandoffNotificationHandler(config);
}

/**
 * Format a notification for display.
 */
export function formatNotificationMessage(notification: Notification): string {
  if (notification.notification_type === 'handoff_acknowledged') {
    const userName = notification.metadata?.acknowledging_user_name as string;
    const time = new Date(notification.created_at).toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });

    return userName
      ? `${userName} acknowledged your handoff at ${time}`
      : `Your handoff was acknowledged at ${time}`;
  }

  return notification.message || notification.title;
}

/**
 * Get the URL to navigate to for a notification.
 */
export function getNotificationUrl(notification: Notification): string | null {
  if (
    notification.notification_type === 'handoff_acknowledged' &&
    notification.entity_id
  ) {
    return `/handoff/${notification.entity_id}`;
  }

  return null;
}

export default HandoffNotificationHandler;
