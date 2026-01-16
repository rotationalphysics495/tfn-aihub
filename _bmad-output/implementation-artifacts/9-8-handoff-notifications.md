# Story 9.8: Handoff Notifications

Status: ready-for-dev

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

- [ ] Task 1: Create Supabase Edge Function for push notifications (AC: 3, 5)
  - [ ] 1.1 Create `supabase/functions/notify-handoff-ack/index.ts` Edge Function
  - [ ] 1.2 Implement Web Push API via VAPID-signed request
  - [ ] 1.3 Query `push_subscriptions` table for user's push endpoint
  - [ ] 1.4 Build notification payload with acknowledging user, timestamp, notes
  - [ ] 1.5 Handle delivery failures with logging (no retry, log only)
  - [ ] 1.6 Implement 60-second delivery target (NFR compliance)

- [ ] Task 2: Create in-app notification handler (AC: 1, 2, 4)
  - [ ] 2.1 Create `apps/web/src/lib/notifications/handoff.ts` notification handler
  - [ ] 2.2 Set up Supabase Realtime subscription for `handoff_acknowledgments` table
  - [ ] 2.3 Filter subscription to only handoffs created by current user
  - [ ] 2.4 Handle incoming acknowledgment events and display toast/banner
  - [ ] 2.5 Store pending notifications for display on next app visit
  - [ ] 2.6 Implement notification dismiss and mark-as-read functionality

- [ ] Task 3: Create backend notification trigger service (AC: 1, 5)
  - [ ] 3.1 Create `apps/api/app/services/handoff/notifications.py` service
  - [ ] 3.2 Add notification trigger to acknowledgment save workflow
  - [ ] 3.3 Fetch outgoing supervisor's notification preferences from `user_preferences`
  - [ ] 3.4 Call Edge Function for push notification if preferences allow
  - [ ] 3.5 Insert notification record for in-app delivery tracking

- [ ] Task 4: Add notification preferences support (AC: 4)
  - [ ] 4.1 Add `handoff_notifications_enabled` column to `user_preferences` table (or verify exists)
  - [ ] 4.2 Add preference toggle to user settings UI
  - [ ] 4.3 Query preferences before sending push notifications

- [ ] Task 5: Testing and validation
  - [ ] 5.1 Unit test Edge Function notification delivery
  - [ ] 5.2 Unit test in-app notification handler subscription logic
  - [ ] 5.3 Integration test end-to-end: acknowledgment -> notification received
  - [ ] 5.4 Test preference-disabled scenario (push blocked, in-app works)
  - [ ] 5.5 Test timing: verify <60 second delivery target

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

**Note:** `push_subscriptions` table is defined in `20260115_008_push_subscriptions.sql` migration (from Story 9.12 planning). If not yet created, this story depends on that table existing.

### Supabase Realtime Subscription Pattern

```typescript
// apps/web/src/lib/notifications/handoff.ts
import { supabase } from '@/lib/supabase/client'

export function subscribeToHandoffAcknowledgments(userId: string) {
  return supabase
    .channel('handoff-acks')
    .on(
      'postgres_changes',
      {
        event: 'INSERT',
        schema: 'public',
        table: 'handoff_acknowledgments',
        filter: `handoff_id=in.(SELECT id FROM shift_handoffs WHERE created_by='${userId}')`
      },
      (payload) => {
        // Handle new acknowledgment notification
        showNotification(payload.new)
      }
    )
    .subscribe()
}
```

**Important:** The filter must ensure we only receive acknowledgments for handoffs the current user created.

### Dependencies on Other Stories

| Story | Dependency Type | Status |
|-------|----------------|--------|
| 9.4 (Persistent Handoff Records) | Required - `shift_handoffs` table | Planned |
| 9.7 (Acknowledgment Flow) | Required - `handoff_acknowledgments` table | Planned |
| 8.8 (User Preference Onboarding) | Optional - preferences table structure | Planned |
| 9.12 (EOD Push Notifications) | Shared - `push_subscriptions` table | Planned |

**Implementation Note:** This story can be developed in parallel with 9.7 if the acknowledgment table schema is agreed upon. The notification trigger can be added to the acknowledgment save workflow once 9.7 is complete.

### Project Structure Notes

**New Files to Create:**
```
supabase/functions/notify-handoff-ack/
  index.ts                              # Edge Function entry point

apps/web/src/lib/notifications/
  handoff.ts                            # In-app notification handler

apps/api/app/services/handoff/
  notifications.py                      # Backend notification trigger
```

**Files to Modify:**
```
apps/api/app/api/handoff.py            # Add notification trigger to acknowledge endpoint
apps/web/src/components/handoff/       # Add notification display components
```

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

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

