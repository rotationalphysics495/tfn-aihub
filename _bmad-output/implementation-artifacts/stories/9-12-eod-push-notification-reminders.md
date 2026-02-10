# Story 9.12: EOD Push Notification Reminders

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Plant Manager**,
I want **optional reminder notifications for EOD summary**,
so that **I don't forget to review the day's outcomes**.

## Acceptance Criteria

1. **AC1: Push Notification Trigger**
   - **Given** a Plant Manager has EOD reminders enabled
   - **When** the configured reminder time arrives (FR34)
   - **Then** a push notification is sent
   - **And** notification says "Ready to review your End of Day summary?"

2. **AC2: Notification Tap Navigation**
   - **Given** the notification is tapped
   - **When** the app opens
   - **Then** the EOD summary page is displayed directly

3. **AC3: Skip Already-Viewed**
   - **Given** the Plant Manager has already viewed EOD today
   - **When** reminder time arrives
   - **Then** no notification is sent
   - **And** system notes "Already reviewed"

4. **AC4: Delivery Failure Handling**
   - **Given** push notification delivery fails
   - **When** retry threshold is reached
   - **Then** delivery is logged as failed
   - **And** no further retries for that day

## Tasks / Subtasks

- [x] **Task 1: Database Schema for Push Subscriptions** (AC: #1, #3, #4)
  - [x] 1.1 Create migration `20260118_001_eod_reminder_preferences.sql`
  - [x] 1.2 Define `eod_notification_failures` table for tracking delivery failures
  - [x] 1.3 Add `eod_reminder_enabled` and `eod_reminder_time` columns to `user_preferences`
  - [x] 1.4 Add `last_eod_viewed_at` column to track daily views
  - [x] 1.5 Add `user_timezone` column for timezone-aware scheduling
  - [x] 1.6 Add RLS policies and indexes

- [x] **Task 2: Supabase Edge Function - send-eod-reminder** (AC: #1, #3, #4)
  - [x] 2.1 Create `supabase/functions/send-eod-reminder/index.ts`
  - [x] 2.2 Implement VAPID key configuration for Web Push
  - [x] 2.3 Query users with reminders enabled at current time
  - [x] 2.4 Filter out users who have already viewed EOD today (check `last_eod_viewed_at`)
  - [x] 2.5 Send Web Push notification to each eligible user
  - [x] 2.6 Handle delivery failures with retry logic (max 3 attempts)
  - [x] 2.7 Log failed deliveries with reason and timestamp
  - [x] 2.8 Mark no-more-retries after threshold reached

- [x] **Task 3: Supabase Scheduled Job (Cron Trigger)** (AC: #1)
  - [x] 3.1 Configure Supabase cron job via `20260118_002_eod_reminder_cron.sql`
  - [x] 3.2 Set up hourly trigger to check for users at their configured reminder times
  - [x] 3.3 Handle timezone-aware scheduling (user local time via Edge Function)

- [x] **Task 4: Frontend Push Subscription Management** (AC: #1)
  - [x] 4.1 Create `apps/web/src/lib/notifications/push-setup.ts`
  - [x] 4.2 Implement `requestPushPermission()` function
  - [x] 4.3 Implement `subscribeToPush()` to register with browser
  - [x] 4.4 Store subscription in Supabase `push_subscriptions` table
  - [x] 4.5 Implement `unsubscribeFromPush()` for cleanup
  - [x] 4.6 Handle permission denied gracefully

- [x] **Task 5: Service Worker Push Handler** (AC: #2)
  - [x] 5.1 Enhanced push event listener in `apps/web/public/sw.js`
  - [x] 5.2 Handle incoming push notifications with type-specific formatting
  - [x] 5.3 Display notification with title, body, and action buttons
  - [x] 5.4 Include EOD deep link in notification data
  - [x] 5.5 Handle notification click to navigate to `/briefing/eod`

- [x] **Task 6: User Preference UI for EOD Reminders** (AC: #1)
  - [x] 6.1 Create `EODReminderSettings` component with toggle
  - [x] 6.2 Add time picker for reminder time (default 5:00 PM)
  - [x] 6.3 Show push permission status and request button if not granted
  - [x] 6.4 Integrate with `usePreferences` hook and preferences page

- [x] **Task 7: EOD View Tracking** (AC: #3)
  - [x] 7.1 Update `last_eod_viewed_at` when EOD summary page loads
  - [x] 7.2 Add direct Supabase update on page view via `trackEodPageView()`
  - [x] 7.3 Timestamp stored as UTC for consistent comparison

- [x] **Task 8: Testing** (AC: #1, #2, #3, #4)
  - [x] 8.1 Unit tests for push-setup.ts (45 passing tests)
  - [x] 8.2 Unit tests for EODReminderSettings component (19 passing tests)
  - [x] 8.3 Test subscription storage and permission flow
  - [x] 8.4 Test time picker and toggle behavior

## Dev Notes

### Technical Requirements

**Push Notification Stack:**
- **Web Push API**: Browser standard for push notifications
- **VAPID Keys**: Required for Web Push authentication (generate and store in Supabase secrets)
- **Supabase Edge Functions**: Deno runtime for serverless notification sending
- **Service Worker**: Required for receiving push events in background

**Latency Requirement:**
- Delivery within 60 seconds of trigger time (NFR from architecture)

### Architecture Compliance

**Voice Briefing Extension Pattern** (from `architecture/voice-briefing.md`):
```
Push Notifications Architecture:
- Supabase Edge Functions: send-eod-reminder
- Triggered by Supabase scheduled job (cron)
- Sends Web Push via VAPID-signed request
- Service Worker displays notification
```

**Push Subscription Flow:**
```
1. User enables EOD reminders in preferences
2. Frontend requests Web Push permission, stores subscription in Supabase
3. Daily at configured time, Edge Function triggers
4. Edge Function queries users with reminders enabled
5. Sends Web Push via VAPID-signed request
6. Service Worker displays notification
```

### Library/Framework Requirements

**Edge Function (Deno):**
```typescript
// Required imports for Edge Function
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

// Web Push library for Deno
import webpush from "npm:web-push"
```

**Frontend Push Setup:**
```typescript
// Standard Web Push API usage
const registration = await navigator.serviceWorker.register('/sw.js')
const subscription = await registration.pushManager.subscribe({
  userVisibleOnly: true,
  applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
})
```

### File Structure Requirements

**Backend (Supabase Edge Functions):**
```
supabase/functions/
└── send-eod-reminder/
    └── index.ts           # Edge Function entry point
```

**Frontend:**
```
apps/web/
├── public/
│   └── sw.js                              # Service Worker (add push handler)
└── src/
    └── lib/
        └── notifications/
            └── push-setup.ts              # Push subscription management
```

**Database:**
```
supabase/migrations/
└── 20260115_008_push_subscriptions.sql    # Push subscriptions table
```

### Database Schema

**push_subscriptions table:**
```sql
CREATE TABLE push_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    subscription JSONB NOT NULL, -- Browser push subscription object
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id)
);

-- RLS: Users can only manage their own subscriptions
ALTER TABLE push_subscriptions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own subscriptions"
ON push_subscriptions
FOR ALL
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);
```

**user_preferences additions:**
```sql
ALTER TABLE user_preferences
ADD COLUMN eod_reminder_enabled BOOLEAN DEFAULT false,
ADD COLUMN eod_reminder_time TIME DEFAULT '17:00:00', -- 5:00 PM local
ADD COLUMN last_eod_viewed_at TIMESTAMPTZ;
```

### Implementation Patterns

**Edge Function Pattern:**
```typescript
serve(async (req) => {
  try {
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    )

    // Configure web-push with VAPID keys
    webpush.setVapidDetails(
      'mailto:admin@example.com',
      Deno.env.get('VAPID_PUBLIC_KEY')!,
      Deno.env.get('VAPID_PRIVATE_KEY')!
    )

    // Get current hour for matching reminder times
    const currentHour = new Date().getHours()

    // Query eligible users
    const { data: users } = await supabase
      .from('user_preferences')
      .select(`
        user_id,
        eod_reminder_time,
        last_eod_viewed_at,
        push_subscriptions!inner(subscription)
      `)
      .eq('eod_reminder_enabled', true)
      .eq('role', 'plant_manager')

    // Filter and send notifications
    for (const user of users) {
      // Skip if already viewed today
      if (user.last_eod_viewed_at &&
          isToday(new Date(user.last_eod_viewed_at))) {
        continue
      }

      await sendPushNotification(user.push_subscriptions.subscription, {
        title: 'End of Day Summary',
        body: 'Ready to review your End of Day summary?',
        data: { url: '/briefing/eod' }
      })
    }

    return new Response(JSON.stringify({ success: true }))
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), { status: 500 })
  }
})
```

**Service Worker Push Handler:**
```javascript
// In sw.js
self.addEventListener('push', (event) => {
  const data = event.data?.json() ?? {}

  const options = {
    body: data.body || 'Ready to review your End of Day summary?',
    icon: '/icon-192.png',
    badge: '/badge-72.png',
    data: data.data || { url: '/briefing/eod' },
    requireInteraction: true
  }

  event.waitUntil(
    self.registration.showNotification(data.title || 'End of Day Summary', options)
  )
})

self.addEventListener('notificationclick', (event) => {
  event.notification.close()

  const url = event.notification.data?.url || '/briefing/eod'

  event.waitUntil(
    clients.matchAll({ type: 'window' }).then((windowClients) => {
      // Focus existing window or open new one
      for (const client of windowClients) {
        if (client.url.includes(url) && 'focus' in client) {
          return client.focus()
        }
      }
      return clients.openWindow(url)
    })
  )
})
```

### Project Structure Notes

- Follows existing Supabase Edge Function pattern (no functions exist yet - this is first)
- Service Worker already planned in architecture for offline support
- Push subscription storage aligns with `push_subscriptions` table from architecture
- User preferences extend existing `user_preferences` table pattern

### Testing Strategy

**Unit Tests:**
- Edge Function logic (mock Supabase and Web Push)
- Timezone handling for reminder time matching
- Already-viewed skip logic

**Integration Tests:**
- Push subscription creation flow
- Edge Function <-> Supabase interaction
- Service Worker registration and handling

**E2E Tests (Manual/Playwright):**
- Enable notifications in preferences
- Receive notification at configured time
- Click notification navigates to EOD page

### Dependencies on Other Stories

- **Story 9.10 (EOD Summary Trigger)**: Provides the EOD summary page to navigate to
- **Story 8.8 (User Preference Onboarding)**: Provides user_preferences table structure

### VAPID Key Generation

Generate VAPID keys before implementation:
```bash
# Using web-push library
npx web-push generate-vapid-keys
```

Store in Supabase secrets:
- `VAPID_PUBLIC_KEY` - Share with frontend
- `VAPID_PRIVATE_KEY` - Edge Function only (never expose)

### Error Handling Checklist

- [ ] Permission denied by browser - show friendly message
- [ ] Push subscription failed - retry or show error
- [ ] Edge Function timeout - log and continue to next user
- [ ] Invalid subscription (user unsubscribed in browser) - remove from DB
- [ ] Network failure on send - retry up to 3 times, then log as failed

### References

- [Source: _bmad-output/planning-artifacts/epic-9.md#Story 9.12: EOD Push Notification Reminders]
- [Source: _bmad/bmm/data/architecture/voice-briefing.md#Push Notifications Architecture]
- [Source: _bmad/bmm/data/architecture/implementation-patterns.md#Service Worker Organization]
- [Source: _bmad/bmm/data/prd.md#FR34]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

