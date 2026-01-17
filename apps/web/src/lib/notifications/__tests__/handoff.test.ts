/**
 * Handoff Notification Handler Tests (Story 9.8)
 *
 * Tests for the HandoffNotificationHandler class and utilities.
 *
 * AC#1: Acknowledgment Notification Trigger
 * AC#2: In-App Notification - immediate display
 * AC#4: Notification on next visit
 *
 * References:
 * - [Source: epic-9.md#Story 9.8]
 */

import { describe, it, expect, vi, beforeEach, afterEach, type Mock } from 'vitest';
import {
  HandoffNotificationHandler,
  createHandoffNotificationHandler,
  formatNotificationMessage,
  getNotificationUrl,
  type Notification,
  type NotificationHandlerConfig,
} from '../handoff';

// Mock Supabase client
const mockChannel = {
  on: vi.fn().mockReturnThis(),
  subscribe: vi.fn().mockImplementation((callback) => {
    callback?.('SUBSCRIBED');
    return mockChannel;
  }),
};

const mockSupabase = {
  channel: vi.fn().mockReturnValue(mockChannel),
  removeChannel: vi.fn(),
  from: vi.fn().mockReturnThis(),
  select: vi.fn().mockReturnThis(),
  eq: vi.fn().mockReturnThis(),
  order: vi.fn().mockReturnThis(),
  limit: vi.fn().mockReturnThis(),
  range: vi.fn().mockReturnThis(),
  update: vi.fn().mockReturnThis(),
};

vi.mock('@supabase/supabase-js', () => ({
  createClient: vi.fn(() => mockSupabase),
}));

describe('HandoffNotificationHandler', () => {
  let handler: HandoffNotificationHandler;
  const testConfig: NotificationHandlerConfig = {
    supabaseUrl: 'https://test.supabase.co',
    supabaseKey: 'test-key',
    userId: 'test-user-123',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    handler = createHandoffNotificationHandler(testConfig);
  });

  afterEach(async () => {
    await handler.unsubscribe();
  });

  describe('subscribe', () => {
    it('creates realtime subscription for notifications', async () => {
      await handler.subscribe();

      expect(mockSupabase.channel).toHaveBeenCalledWith('notifications:test-user-123');
      expect(mockChannel.on).toHaveBeenCalledWith(
        'postgres_changes',
        expect.objectContaining({
          event: 'INSERT',
          schema: 'public',
          table: 'notifications',
          filter: 'user_id=eq.test-user-123',
        }),
        expect.any(Function)
      );
      expect(mockChannel.subscribe).toHaveBeenCalled();
    });

    it('does not create duplicate subscriptions', async () => {
      await handler.subscribe();
      await handler.subscribe();

      expect(mockSupabase.channel).toHaveBeenCalledTimes(1);
    });
  });

  describe('unsubscribe', () => {
    it('removes realtime channels', async () => {
      await handler.subscribe();
      await handler.unsubscribe();

      expect(mockSupabase.removeChannel).toHaveBeenCalled();
    });
  });

  describe('getUnreadNotifications', () => {
    it('fetches unread notifications for user', async () => {
      const mockNotifications: Notification[] = [
        {
          id: 'notif-1',
          user_id: 'test-user-123',
          notification_type: 'handoff_acknowledged',
          title: 'Handoff Acknowledged',
          message: 'John acknowledged your handoff',
          entity_type: 'shift_handoff',
          entity_id: 'handoff-123',
          metadata: {},
          is_read: false,
          read_at: null,
          is_dismissed: false,
          dismissed_at: null,
          created_at: new Date().toISOString(),
        },
      ];

      mockSupabase.from.mockReturnThis();
      mockSupabase.select.mockReturnThis();
      mockSupabase.eq.mockReturnThis();
      mockSupabase.order.mockReturnThis();
      mockSupabase.limit.mockResolvedValue({ data: mockNotifications, error: null });

      const notifications = await handler.getUnreadNotifications();

      expect(mockSupabase.from).toHaveBeenCalledWith('notifications');
      expect(notifications).toHaveLength(1);
      expect(notifications[0].notification_type).toBe('handoff_acknowledged');
    });

    it('returns empty array on error', async () => {
      mockSupabase.from.mockReturnThis();
      mockSupabase.select.mockReturnThis();
      mockSupabase.eq.mockReturnThis();
      mockSupabase.order.mockReturnThis();
      mockSupabase.limit.mockResolvedValue({ data: null, error: { message: 'DB error' } });

      const notifications = await handler.getUnreadNotifications();

      expect(notifications).toEqual([]);
    });
  });

  describe('markAsRead', () => {
    it('updates notification read status', async () => {
      // Chain mock for: from().update().eq().eq()
      let eqCallCount = 0;
      const mockChain: any = {
        update: vi.fn().mockImplementation(() => mockChain),
        eq: vi.fn().mockImplementation(() => {
          eqCallCount++;
          if (eqCallCount >= 2) {
            return Promise.resolve({ data: [{}], error: null });
          }
          return mockChain;
        }),
      };
      mockSupabase.from.mockReturnValue(mockChain);

      const success = await handler.markAsRead('notif-123');

      expect(mockSupabase.from).toHaveBeenCalledWith('notifications');
      expect(mockChain.update).toHaveBeenCalledWith(expect.objectContaining({
        is_read: true,
      }));
      expect(success).toBe(true);
    });

    it('returns false on error', async () => {
      let eqCallCount = 0;
      const mockChain: any = {
        update: vi.fn().mockImplementation(() => mockChain),
        eq: vi.fn().mockImplementation(() => {
          eqCallCount++;
          if (eqCallCount >= 2) {
            return Promise.resolve({ data: null, error: { message: 'Update failed' } });
          }
          return mockChain;
        }),
      };
      mockSupabase.from.mockReturnValue(mockChain);

      const success = await handler.markAsRead('notif-123');

      expect(success).toBe(false);
    });
  });

  describe('dismissNotification', () => {
    it('updates notification dismissed status', async () => {
      let eqCallCount = 0;
      const mockChain: any = {
        update: vi.fn().mockImplementation(() => mockChain),
        eq: vi.fn().mockImplementation(() => {
          eqCallCount++;
          if (eqCallCount >= 2) {
            return Promise.resolve({ data: [{}], error: null });
          }
          return mockChain;
        }),
      };
      mockSupabase.from.mockReturnValue(mockChain);

      const success = await handler.dismissNotification('notif-123');

      expect(mockChain.update).toHaveBeenCalledWith(expect.objectContaining({
        is_dismissed: true,
      }));
      expect(success).toBe(true);
    });
  });

  describe('getUnreadCount', () => {
    it('returns count of unread notifications', async () => {
      // Chain mock for: from().select().eq().eq().eq()
      // Build a chain where .eq() returns itself until the last call
      let eqCallCount = 0;
      const mockChain: any = {
        select: vi.fn().mockImplementation(() => mockChain),
        eq: vi.fn().mockImplementation(() => {
          eqCallCount++;
          // After 3 eq() calls (user_id, is_read, is_dismissed), return the result
          if (eqCallCount >= 3) {
            return Promise.resolve({ count: 5, error: null });
          }
          return mockChain;
        }),
      };
      mockSupabase.from.mockReturnValue(mockChain);

      const count = await handler.getUnreadCount();

      expect(count).toBe(5);
    });

    it('returns 0 on error', async () => {
      // Chain mock for error case
      let eqCallCount = 0;
      const mockChain: any = {
        select: vi.fn().mockImplementation(() => mockChain),
        eq: vi.fn().mockImplementation(() => {
          eqCallCount++;
          if (eqCallCount >= 3) {
            return Promise.resolve({ count: null, error: { message: 'Error' } });
          }
          return mockChain;
        }),
      };
      mockSupabase.from.mockReturnValue(mockChain);

      const count = await handler.getUnreadCount();

      expect(count).toBe(0);
    });
  });
});

describe('formatNotificationMessage', () => {
  it('formats handoff_acknowledged with user name', () => {
    const notification: Notification = {
      id: 'notif-1',
      user_id: 'user-1',
      notification_type: 'handoff_acknowledged',
      title: 'Handoff Acknowledged',
      message: null,
      entity_type: 'shift_handoff',
      entity_id: 'handoff-1',
      metadata: { acknowledging_user_name: 'Jane Doe' },
      is_read: false,
      read_at: null,
      is_dismissed: false,
      dismissed_at: null,
      created_at: '2026-01-17T10:30:00Z',
    };

    const message = formatNotificationMessage(notification);

    expect(message).toContain('Jane Doe');
    expect(message).toContain('acknowledged');
  });

  it('formats handoff_acknowledged without user name', () => {
    const notification: Notification = {
      id: 'notif-1',
      user_id: 'user-1',
      notification_type: 'handoff_acknowledged',
      title: 'Handoff Acknowledged',
      message: null,
      entity_type: 'shift_handoff',
      entity_id: 'handoff-1',
      metadata: {},
      is_read: false,
      read_at: null,
      is_dismissed: false,
      dismissed_at: null,
      created_at: '2026-01-17T10:30:00Z',
    };

    const message = formatNotificationMessage(notification);

    expect(message).toContain('Your handoff was acknowledged');
  });

  it('returns message field for other notification types', () => {
    const notification: Notification = {
      id: 'notif-1',
      user_id: 'user-1',
      notification_type: 'other_type',
      title: 'Other Notification',
      message: 'Custom message here',
      entity_type: null,
      entity_id: null,
      metadata: {},
      is_read: false,
      read_at: null,
      is_dismissed: false,
      dismissed_at: null,
      created_at: '2026-01-17T10:30:00Z',
    };

    const message = formatNotificationMessage(notification);

    expect(message).toBe('Custom message here');
  });
});

describe('getNotificationUrl', () => {
  it('returns handoff URL for handoff_acknowledged notifications', () => {
    const notification: Notification = {
      id: 'notif-1',
      user_id: 'user-1',
      notification_type: 'handoff_acknowledged',
      title: 'Handoff Acknowledged',
      message: null,
      entity_type: 'shift_handoff',
      entity_id: 'handoff-456',
      metadata: {},
      is_read: false,
      read_at: null,
      is_dismissed: false,
      dismissed_at: null,
      created_at: '2026-01-17T10:30:00Z',
    };

    const url = getNotificationUrl(notification);

    expect(url).toBe('/handoff/handoff-456');
  });

  it('returns null for notifications without entity_id', () => {
    const notification: Notification = {
      id: 'notif-1',
      user_id: 'user-1',
      notification_type: 'handoff_acknowledged',
      title: 'Handoff Acknowledged',
      message: null,
      entity_type: 'shift_handoff',
      entity_id: null,
      metadata: {},
      is_read: false,
      read_at: null,
      is_dismissed: false,
      dismissed_at: null,
      created_at: '2026-01-17T10:30:00Z',
    };

    const url = getNotificationUrl(notification);

    expect(url).toBeNull();
  });

  it('returns null for other notification types', () => {
    const notification: Notification = {
      id: 'notif-1',
      user_id: 'user-1',
      notification_type: 'other_type',
      title: 'Other',
      message: null,
      entity_type: null,
      entity_id: 'some-id',
      metadata: {},
      is_read: false,
      read_at: null,
      is_dismissed: false,
      dismissed_at: null,
      created_at: '2026-01-17T10:30:00Z',
    };

    const url = getNotificationUrl(notification);

    expect(url).toBeNull();
  });
});

describe('createHandoffNotificationHandler', () => {
  it('creates handler instance with config', () => {
    const config: NotificationHandlerConfig = {
      supabaseUrl: 'https://test.supabase.co',
      supabaseKey: 'test-key',
      userId: 'user-123',
    };

    const handler = createHandoffNotificationHandler(config);

    expect(handler).toBeInstanceOf(HandoffNotificationHandler);
  });

  it('accepts optional handlers in config', () => {
    const onNotification = vi.fn();
    const onError = vi.fn();

    const config: NotificationHandlerConfig = {
      supabaseUrl: 'https://test.supabase.co',
      supabaseKey: 'test-key',
      userId: 'user-123',
      handlers: {
        onNotification,
        onError,
      },
    };

    const handler = createHandoffNotificationHandler(config);

    expect(handler).toBeInstanceOf(HandoffNotificationHandler);
  });
});
