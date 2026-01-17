# Story 9.8: Handoff Notifications

Status: done

## Story

As an **outgoing Supervisor**,
I want to **be notified when my handoff is acknowledged**,
so that **I know the incoming shift received the information**.

## Acceptance Criteria

### AC1: Acknowledgment Notification Trigger
**Given** a handoff is acknowledged
**When** the acknowledgment is saved (FR28)
**Then** the outgoing Supervisor receives a notification
**And** notification includes: acknowledging user, timestamp, any notes

### AC2: In-App Notification (Real-time)
**Given** the outgoing Supervisor has the app open
**When** acknowledgment occurs
**Then** an in-app notification appears immediately
**And** the notification uses Supabase Realtime subscription

### AC3: Push Notification (Background)
**Given** the outgoing Supervisor has the app closed
**When** acknowledgment occurs
**Then** a push notification is sent (if enabled)
**And** notification links to the handoff detail

### AC4: Notification Preference Respect
**Given** notification preferences are disabled
**When** acknowledgment occurs
**Then** no push notification is sent
**And** in-app notification still appears on next visit

### AC5: Delivery Timing (NFR)
**Given** an acknowledgment is created
**When** notification is sent
**Then** delivery occurs within 60 seconds of acknowledgment

## Tasks / Subtasks

- [x] Task 1: Create Supabase Edge Function for push notifications (AC: 3, 5)
  - [x] 1.1 Create `supabase/functions/notify-handoff-ack/index.ts` Edge Function
  - [x] 1.2 Implement Web Push API via VAPID-signed request
  - [x] 1.3 Query `push_subscriptions` table for user's push endpoint
  - [x] 1.4 Build notification payload with acknowledging user, timestamp, notes
  - [x] 1.5 Handle delivery failures with logging (no retry, log only)
  - [x] 1.6 Implement 60-second delivery target (NFR compliance)

- [x] Task 2: Create in-app notification handler (AC: 1, 2, 4)
  - [x] 2.1 Create `apps/web/src/lib/notifications/handoff.ts` notification handler
  - [x] 2.2 Set up Supabase Realtime subscription for `notifications` table
  - [x] 2.3 Filter subscription to only notifications for current user
  - [x] 2.4 Handle incoming notification events and display via callbacks
  - [x] 2.5 Store pending notifications in `notifications` table for next visit
  - [x] 2.6 Implement notification dismiss and mark-as-read functionality

- [x] Task 3: Create backend notification trigger service (AC: 1, 5)
  - [x] 3.1 Create `apps/api/app/services/handoff/notifications.py` service
  - [x] 3.2 Add notification trigger to acknowledgment save workflow
  - [x] 3.3 Fetch outgoing supervisor's notification preferences from `user_preferences`
  - [x] 3.4 Call Edge Function for push notification if preferences allow
  - [x] 3.5 Insert notification record for in-app delivery tracking

- [x] Task 4: Add notification preferences support (AC: 4)
  - [x] 4.1 Add `handoff_notifications_enabled` column to `user_preferences` table
  - [x] 4.2 Update preferences models and service to include new field
  - [x] 4.3 Query preferences before sending push notifications

- [x] Task 5: Testing and validation
  - [x] 5.1 Unit test notification service (18 Python tests passing)
  - [x] 5.2 Unit test in-app notification handler subscription logic (18 TypeScript tests passing)
  - [x] 5.3 Unit test preference-disabled scenario (push blocked, in-app works)
  - [x] 5.4 Test timing: logging for <60 second delivery target verification

## Dev Notes

### Architecture Pattern Reference

This story implements the **Push Notifications Architecture** from the Voice Briefing extension:

```
Flow (from architecture/voice-briefing.md):
1. Acknowledgment saved -> Notification trigger service called
2. Service queries user preferences
3. If push enabled: call Edge Function -> Web Push to device
4. Supabase Realtime broadcasts to any open clients
5. Service Worker displays push notification (if app closed)
```

**Key Technical Decisions:**
- **In-app:** Supabase Realtime subscription (already used elsewhere in platform)
- **Push:** Web Push API via Supabase Edge Function (stays within Supabase ecosystem)
- **Preference storage:** `user_preferences` table (existing from Story 8.8)

### Relevant Existing Code Patterns

**Service Pattern** (from `apps/api/app/services/agent/tools/alert_check.py`):
- Use logging for all operations
- Handle errors gracefully without exposing internals
- Return structured responses with clear success/failure states

**Edge Function Pattern** (for new `notify-handoff-ack`):
```typescript
// supabase/functions/notify-handoff-ack/index.ts
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

serve(async (req) => {
  const { acknowledgment_id, outgoing_user_id } = await req.json()
  // 1. Query push_subscriptions for outgoing_user_id
  // 2. If subscription exists and preferences allow, send Web Push
  // 3. Return success/failure
})
```

### Database Tables Involved

| Table | Usage |
|-------|-------|
| `handoff_acknowledgments` | Source of acknowledgment events (Realtime subscription) |
| `shift_handoffs` | Get outgoing supervisor user_id |
| `push_subscriptions` | Get user's push notification endpoint |
| `user_preferences` | Check if notifications enabled |
| `notifications` | In-app notification records for users |

### Dependencies on Other Stories

| Story | Dependency Type | Status |
|-------|----------------|--------|
| 9.4 (Persistent Handoff Records) | Required - `shift_handoffs` table | Complete |
| 9.7 (Acknowledgment Flow) | Required - `handoff_acknowledgments` table | Complete |
| 8.8 (User Preference Onboarding) | Optional - preferences table structure | Complete |
| 9.12 (EOD Push Notifications) | Shared - `push_subscriptions` table | Pending |

### Error Handling Strategy

1. **Push notification fails:** Log error, do NOT retry (to avoid spam). User will see in-app notification on next visit.
2. **Realtime subscription fails:** Fallback to polling or show "refresh for updates" message.
3. **Edge Function timeout:** Log and continue - notification is best-effort, not critical path.

### Testing Approach

**Unit Tests:**
- Edge Function: mock Web Push API, verify payload construction
- Notification handler: mock Supabase Realtime, verify event handling
- Notification service: mock database queries, verify preference checking

**Integration Tests:**
- Full flow: create acknowledgment -> verify notification delivered to subscribed client
- Preference disabled: verify no push sent, in-app still works
- Timing: measure time from acknowledgment INSERT to notification receipt

### References

- [Source: _bmad/bmm/data/architecture/voice-briefing.md#Push-Notifications-Architecture]
- [Source: _bmad-output/planning-artifacts/epic-9.md#Story-9.8]
- [Source: _bmad/bmm/data/architecture/implementation-patterns.md#Service-Worker-Organization]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- Python tests: `apps/api/tests/services/handoff/test_notifications.py` (18 tests passing)
- TypeScript tests: `apps/web/src/lib/notifications/__tests__/handoff.test.ts` (18 tests passing)

### Completion Notes List

1. **Task 1 Complete:** Created Supabase Edge Function at `supabase/functions/notify-handoff-ack/index.ts` implementing VAPID-signed Web Push API with CORS support, notification payload construction, and 60-second delivery timing logging.

2. **Task 2 Complete:** Created in-app notification handler at `apps/web/src/lib/notifications/handoff.ts` with `HandoffNotificationHandler` class providing Supabase Realtime subscription, unread/read/dismiss functionality, and React hook `useHandoffNotifications` at `apps/web/src/lib/hooks/useHandoffNotifications.ts`.

3. **Task 3 Complete:** Created backend notification service at `apps/api/app/services/handoff/notifications.py` with `HandoffNotificationService` class. Integrated into acknowledgment workflow in `apps/api/app/api/handoff.py:1929` to trigger notifications after successful acknowledgment.

4. **Task 4 Complete:** Added `handoff_notifications_enabled` boolean field to `user_preferences` table via migration `supabase/migrations/20260117_001_push_subscriptions.sql`. Updated `UserPreferencesBase` and `UpdateUserPreferencesRequest` models in `apps/api/app/models/preferences.py`. Updated `PreferenceService` in `apps/api/app/services/preferences/service.py` to handle the new field.

5. **Task 5 Complete:** Created comprehensive unit tests for `HandoffNotificationService` with 18 passing tests covering notification creation, preference checking, push delivery, and error handling.

### File List

**New Files Created:**
- `supabase/migrations/20260117_001_push_subscriptions.sql` - Database migration for push_subscriptions, notifications tables, and handoff_notifications_enabled column
- `supabase/functions/notify-handoff-ack/index.ts` - Supabase Edge Function for push notifications
- `apps/web/src/lib/notifications/handoff.ts` - In-app notification handler class
- `apps/web/src/lib/hooks/useHandoffNotifications.ts` - React hook for notification management
- `apps/api/app/services/handoff/notifications.py` - Backend notification trigger service
- `apps/api/tests/services/handoff/test_notifications.py` - Unit tests for notification service
- `apps/web/src/lib/notifications/__tests__/handoff.test.ts` - TypeScript tests for notification handler

**Modified Files:**
- `apps/api/app/api/handoff.py` - Added notification trigger to acknowledge endpoint (lines 1919-1937)
- `apps/api/app/models/preferences.py` - Added handoff_notifications_enabled field to UserPreferencesBase and UpdateUserPreferencesRequest
- `apps/api/app/services/preferences/service.py` - Updated DEFAULT_PREFERENCES, _format_response, get_preferences, save_preferences, and update_preferences to handle new field
