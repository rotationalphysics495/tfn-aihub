'use client';

/**
 * EOD Reminder Settings Component (Story 9.12)
 *
 * Provides UI for configuring End of Day summary reminder notifications:
 * - Toggle to enable/disable EOD reminders
 * - Time picker for reminder time (default 5:00 PM)
 * - Push permission status and request button
 *
 * Task 6: User Preference UI for EOD Reminders (AC: 1)
 * - 6.1: Add EOD reminder toggle to preferences page
 * - 6.2: Add time picker for reminder time (default 5:00 PM)
 * - 6.3: Show push permission status and request button if not granted
 * - 6.4: Save preferences to user_preferences table
 *
 * References:
 * - [Source: architecture/voice-briefing.md#Push-Notifications-Architecture]
 * - [Source: epic-9.md#Story-9.12]
 */

import { useState, useEffect, useCallback } from 'react';
import { cn } from '@/lib/utils';
import {
  isPushSupported,
  getPushPermissionStatus,
  subscribeToPush,
  type PushPermissionStatus,
} from '@/lib/notifications/push-setup';

interface EODReminderSettingsProps {
  /** Whether EOD reminders are enabled */
  enabled: boolean;
  /** Reminder time in HH:MM format (24-hour) */
  reminderTime: string;
  /** Called when enabled changes */
  onEnabledChange: (enabled: boolean) => void;
  /** Called when reminder time changes */
  onTimeChange: (time: string) => void;
  /** VAPID public key for push subscription */
  vapidPublicKey?: string;
  /** Optional CSS class name */
  className?: string;
}

/**
 * Time options for the reminder time picker.
 */
const TIME_OPTIONS = [
  { value: '15:00', label: '3:00 PM' },
  { value: '16:00', label: '4:00 PM' },
  { value: '17:00', label: '5:00 PM' },
  { value: '18:00', label: '6:00 PM' },
  { value: '19:00', label: '7:00 PM' },
  { value: '20:00', label: '8:00 PM' },
];

export function EODReminderSettings({
  enabled,
  reminderTime,
  onEnabledChange,
  onTimeChange,
  vapidPublicKey,
  className,
}: EODReminderSettingsProps) {
  const [pushSupported, setPushSupported] = useState(true);
  const [pushPermission, setPushPermission] = useState<PushPermissionStatus>('default');
  const [isRequestingPermission, setIsRequestingPermission] = useState(false);
  const [permissionError, setPermissionError] = useState<string | null>(null);

  // Check push support and permission on mount
  useEffect(() => {
    setPushSupported(isPushSupported());
    setPushPermission(getPushPermissionStatus());
  }, []);

  /**
   * Handle push permission request.
   * Task 6.3: Show push permission status and request button if not granted
   */
  const handleRequestPermission = useCallback(async () => {
    if (!vapidPublicKey) {
      setPermissionError('Push notifications are not configured');
      return;
    }

    setIsRequestingPermission(true);
    setPermissionError(null);

    try {
      const result = await subscribeToPush(vapidPublicKey);
      setPushPermission(result.status);

      if (!result.success && result.error) {
        setPermissionError(result.error);
      }
    } catch (error) {
      setPermissionError(
        error instanceof Error ? error.message : 'Failed to request permission'
      );
    } finally {
      setIsRequestingPermission(false);
    }
  }, [vapidPublicKey]);

  /**
   * Handle toggle change.
   * Task 6.1: Add EOD reminder toggle to preferences page
   */
  const handleToggle = useCallback(async () => {
    const newEnabled = !enabled;

    // If enabling and permission not granted, request it first
    if (newEnabled && pushPermission !== 'granted') {
      await handleRequestPermission();
      // Only enable if permission was granted
      const newPermission = getPushPermissionStatus();
      if (newPermission !== 'granted') {
        return; // Don't enable if permission wasn't granted
      }
    }

    onEnabledChange(newEnabled);
  }, [enabled, pushPermission, handleRequestPermission, onEnabledChange]);

  // Format time for display
  const formatTimeDisplay = (time: string) => {
    const option = TIME_OPTIONS.find((opt) => opt.value === time);
    return option?.label || time;
  };

  // Push not supported message
  if (!pushSupported) {
    return (
      <div className={cn('space-y-4', className)}>
        <div className="p-4 rounded-lg border border-amber-200 bg-amber-50">
          <div className="flex items-start gap-3">
            <svg
              className="w-5 h-5 text-amber-600 mt-0.5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <div>
              <p className="font-medium text-amber-800">
                Push notifications not supported
              </p>
              <p className="text-sm text-amber-700 mt-1">
                Your browser does not support push notifications. EOD reminders are
                unavailable on this device.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={cn('space-y-4', className)}>
      <div className="text-sm text-muted-foreground">
        Get a reminder to review your End of Day summary at your preferred time.
      </div>

      {/* Main toggle card */}
      <div className="p-4 rounded-lg border bg-card">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className={cn(
                'w-10 h-10 rounded-full flex items-center justify-center',
                enabled ? 'bg-primary/10' : 'bg-muted'
              )}
            >
              <svg
                className={cn('w-5 h-5', enabled ? 'text-primary' : 'text-muted-foreground')}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                />
              </svg>
            </div>
            <div>
              <p className="font-medium">EOD Summary Reminder</p>
              <p className="text-sm text-muted-foreground">
                {enabled
                  ? `Reminder at ${formatTimeDisplay(reminderTime)}`
                  : 'Get reminded to review your day'}
              </p>
            </div>
          </div>

          {/* Toggle switch - Task 6.1 */}
          <button
            type="button"
            role="switch"
            aria-checked={enabled}
            onClick={handleToggle}
            disabled={isRequestingPermission}
            className={cn(
              'relative inline-flex h-7 w-12 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent',
              'transition-colors duration-200 ease-in-out',
              'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              enabled ? 'bg-primary' : 'bg-muted'
            )}
          >
            <span className="sr-only">Enable EOD reminders</span>
            <span
              aria-hidden="true"
              className={cn(
                'pointer-events-none inline-block h-6 w-6 transform rounded-full bg-background shadow ring-0',
                'transition duration-200 ease-in-out',
                enabled ? 'translate-x-5' : 'translate-x-0'
              )}
            />
          </button>
        </div>

        {/* Time picker - Task 6.2 */}
        {enabled && (
          <div className="mt-4 pt-4 border-t">
            <label className="block text-sm font-medium text-foreground mb-2">
              Reminder Time
            </label>
            <select
              value={reminderTime}
              onChange={(e) => onTimeChange(e.target.value)}
              className={cn(
                'w-full px-3 py-2 rounded-md border bg-background',
                'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2'
              )}
            >
              {TIME_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <p className="mt-2 text-xs text-muted-foreground">
              You&apos;ll receive a notification at this time each day (your local time)
            </p>
          </div>
        )}
      </div>

      {/* Push permission status - Task 6.3 */}
      {pushPermission === 'denied' && (
        <div className="p-4 rounded-lg border border-destructive/30 bg-destructive/10">
          <div className="flex items-start gap-3">
            <svg
              className="w-5 h-5 text-destructive mt-0.5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"
              />
            </svg>
            <div>
              <p className="font-medium text-destructive">Notifications blocked</p>
              <p className="text-sm text-destructive/80 mt-1">
                Push notifications are blocked in your browser settings. To receive
                EOD reminders, please enable notifications for this site in your
                browser&apos;s settings.
              </p>
            </div>
          </div>
        </div>
      )}

      {pushPermission === 'default' && !enabled && (
        <div className="p-4 rounded-lg bg-muted/50">
          <p className="text-sm text-muted-foreground flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            You&apos;ll be asked to allow notifications when you enable reminders.
          </p>
        </div>
      )}

      {permissionError && (
        <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/30">
          <p className="text-sm text-destructive">{permissionError}</p>
        </div>
      )}
    </div>
  );
}

export default EODReminderSettings;
