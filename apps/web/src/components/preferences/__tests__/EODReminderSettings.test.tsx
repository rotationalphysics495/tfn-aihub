/**
 * EOD Reminder Settings Component Tests (Story 9.12)
 *
 * Tests for the EOD Reminder Settings preference component.
 *
 * Task 8: Testing (AC: 1, 2)
 * - 8.1: Test preference UI toggle behavior
 * - 8.2: Test time picker functionality
 *
 * References:
 * - [Source: epic-9.md#Story 9.12]
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { EODReminderSettings } from '../EODReminderSettings';

// Mock push-setup module
vi.mock('@/lib/notifications/push-setup', () => ({
  isPushSupported: vi.fn().mockReturnValue(true),
  getPushPermissionStatus: vi.fn().mockReturnValue('default'),
  subscribeToPush: vi.fn().mockResolvedValue({ success: true, status: 'granted' }),
}));

import {
  isPushSupported,
  getPushPermissionStatus,
  subscribeToPush,
} from '@/lib/notifications/push-setup';

describe('EODReminderSettings', () => {
  const defaultProps = {
    enabled: false,
    reminderTime: '17:00',
    onEnabledChange: vi.fn(),
    onTimeChange: vi.fn(),
    vapidPublicKey: 'test-vapid-key',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (isPushSupported as ReturnType<typeof vi.fn>).mockReturnValue(true);
    (getPushPermissionStatus as ReturnType<typeof vi.fn>).mockReturnValue('default');
    (subscribeToPush as ReturnType<typeof vi.fn>).mockResolvedValue({
      success: true,
      status: 'granted',
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('rendering', () => {
    it('renders toggle switch in off state', () => {
      render(<EODReminderSettings {...defaultProps} />);

      const toggle = screen.getByRole('switch');
      expect(toggle).toBeInTheDocument();
      expect(toggle).toHaveAttribute('aria-checked', 'false');
    });

    it('renders toggle switch in on state when enabled', () => {
      render(<EODReminderSettings {...defaultProps} enabled={true} />);

      const toggle = screen.getByRole('switch');
      expect(toggle).toHaveAttribute('aria-checked', 'true');
    });

    it('renders reminder description text', () => {
      render(<EODReminderSettings {...defaultProps} />);

      expect(
        screen.getByText(/Get a reminder to review your End of Day summary/i)
      ).toBeInTheDocument();
    });

    it('does not show time picker when disabled', () => {
      render(<EODReminderSettings {...defaultProps} enabled={false} />);

      expect(screen.queryByText('Reminder Time')).not.toBeInTheDocument();
    });

    it('shows time picker when enabled', () => {
      render(<EODReminderSettings {...defaultProps} enabled={true} />);

      expect(screen.getByText('Reminder Time')).toBeInTheDocument();
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });
  });

  describe('push not supported', () => {
    it('shows warning when push is not supported', () => {
      (isPushSupported as ReturnType<typeof vi.fn>).mockReturnValue(false);

      render(<EODReminderSettings {...defaultProps} />);

      expect(
        screen.getByText(/Push notifications not supported/i)
      ).toBeInTheDocument();
    });

    it('does not show toggle when push is not supported', () => {
      (isPushSupported as ReturnType<typeof vi.fn>).mockReturnValue(false);

      render(<EODReminderSettings {...defaultProps} />);

      expect(screen.queryByRole('switch')).not.toBeInTheDocument();
    });
  });

  describe('push permission denied', () => {
    it('shows blocked message when permission is denied', () => {
      (getPushPermissionStatus as ReturnType<typeof vi.fn>).mockReturnValue('denied');

      render(<EODReminderSettings {...defaultProps} />);

      expect(screen.getByText(/Notifications blocked/i)).toBeInTheDocument();
    });

    it('shows instructions to enable in browser settings', () => {
      (getPushPermissionStatus as ReturnType<typeof vi.fn>).mockReturnValue('denied');

      render(<EODReminderSettings {...defaultProps} />);

      expect(
        screen.getByText(/enable notifications.*browser.*settings/i)
      ).toBeInTheDocument();
    });
  });

  describe('toggle interaction', () => {
    it('calls onEnabledChange when toggle is clicked', async () => {
      const user = userEvent.setup();
      (getPushPermissionStatus as ReturnType<typeof vi.fn>).mockReturnValue('granted');

      render(<EODReminderSettings {...defaultProps} enabled={false} />);

      const toggle = screen.getByRole('switch');
      await user.click(toggle);

      expect(defaultProps.onEnabledChange).toHaveBeenCalledWith(true);
    });

    it('requests push permission when enabling and permission not granted', async () => {
      const user = userEvent.setup();
      (getPushPermissionStatus as ReturnType<typeof vi.fn>).mockReturnValue('default');
      (subscribeToPush as ReturnType<typeof vi.fn>).mockResolvedValue({
        success: true,
        status: 'granted',
      });

      render(<EODReminderSettings {...defaultProps} enabled={false} />);

      const toggle = screen.getByRole('switch');
      await user.click(toggle);

      await waitFor(() => {
        expect(subscribeToPush).toHaveBeenCalledWith('test-vapid-key');
      });
    });

    it('does not enable if permission request fails', async () => {
      const user = userEvent.setup();
      (getPushPermissionStatus as ReturnType<typeof vi.fn>)
        .mockReturnValueOnce('default')
        .mockReturnValueOnce('denied');
      (subscribeToPush as ReturnType<typeof vi.fn>).mockResolvedValue({
        success: false,
        status: 'denied',
        error: 'Permission denied',
      });

      render(<EODReminderSettings {...defaultProps} enabled={false} />);

      const toggle = screen.getByRole('switch');
      await user.click(toggle);

      await waitFor(() => {
        expect(defaultProps.onEnabledChange).not.toHaveBeenCalled();
      });
    });
  });

  describe('time picker interaction', () => {
    it('calls onTimeChange when time is changed', async () => {
      const user = userEvent.setup();

      render(<EODReminderSettings {...defaultProps} enabled={true} />);

      const select = screen.getByRole('combobox');
      await user.selectOptions(select, '18:00');

      expect(defaultProps.onTimeChange).toHaveBeenCalledWith('18:00');
    });

    it('displays correct time options', () => {
      render(<EODReminderSettings {...defaultProps} enabled={true} />);

      const options = screen.getAllByRole('option');

      expect(options).toHaveLength(6);
      expect(options.map((o) => o.textContent)).toEqual([
        '3:00 PM',
        '4:00 PM',
        '5:00 PM',
        '6:00 PM',
        '7:00 PM',
        '8:00 PM',
      ]);
    });

    it('shows selected time value', () => {
      render(<EODReminderSettings {...defaultProps} enabled={true} reminderTime="18:00" />);

      const select = screen.getByRole('combobox') as HTMLSelectElement;
      expect(select.value).toBe('18:00');
    });
  });

  describe('enabled state display', () => {
    it('shows reminder time in toggle description when enabled', () => {
      render(<EODReminderSettings {...defaultProps} enabled={true} reminderTime="17:00" />);

      expect(screen.getByText(/Reminder at 5:00 PM/i)).toBeInTheDocument();
    });

    it('shows generic message in toggle description when disabled', () => {
      render(<EODReminderSettings {...defaultProps} enabled={false} />);

      expect(screen.getByText(/Get reminded to review your day/i)).toBeInTheDocument();
    });
  });

  describe('permission request pending', () => {
    it('shows info message about permission request when permission is default', () => {
      (getPushPermissionStatus as ReturnType<typeof vi.fn>).mockReturnValue('default');

      render(<EODReminderSettings {...defaultProps} enabled={false} />);

      expect(
        screen.getByText(/asked to allow notifications when you enable/i)
      ).toBeInTheDocument();
    });
  });

  describe('error handling', () => {
    it('displays error message when permission request fails with error', async () => {
      const user = userEvent.setup();
      (getPushPermissionStatus as ReturnType<typeof vi.fn>).mockReturnValue('default');
      (subscribeToPush as ReturnType<typeof vi.fn>).mockResolvedValue({
        success: false,
        status: 'denied',
        error: 'Failed to subscribe',
      });

      render(<EODReminderSettings {...defaultProps} enabled={false} />);

      const toggle = screen.getByRole('switch');
      await user.click(toggle);

      await waitFor(() => {
        expect(screen.getByText(/Failed to subscribe/i)).toBeInTheDocument();
      });
    });
  });
});
