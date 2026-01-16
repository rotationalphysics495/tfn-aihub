---
stepsCompleted: ["step-01-validate-prerequisites", "step-02-design-epics", "step-03-create-stories"]
inputDocuments:
  - "_bmad/bmm/data/prd.md"
  - "_bmad/bmm/data/prd/prd-functional-requirements.md"
  - "_bmad/bmm/data/prd/prd-non-functional-requirements.md"
  - "_bmad/bmm/data/prd/prd-epics.md"
  - "_bmad/bmm/data/architecture.md"
  - "_bmad/bmm/data/architecture/voice-briefing.md"
  - "_bmad/bmm/data/ux-design.md"
epic: 9
status: "ready"
---

# Epic 9: Shift Handoff & EOD Summary

## Overview

**Goal:** Enable persistent shift handoffs and close the accountability loop with End of Day summaries, ensuring knowledge doesn't walk out the door when shifts change.

**Dependencies:** Epic 8 (Voice Briefing Foundation)

**User Value:** Outgoing supervisors can create comprehensive handoff records that incoming supervisors can review, question, and acknowledge. Plant Managers can compare morning predictions against actual outcomes, creating a continuous improvement feedback loop.

## Requirements Coverage

| Requirement | Coverage |
|-------------|----------|
| FR21-FR30 (Shift Handoff Workflow) | Full |
| FR31-FR34 (End of Day Summary) | Full |
| FR46-FR50 (Admin & Configuration) | Full |
| FR51-FR57 (Data Citations & Audit) | Full |
| NFR19 (99.9% uptime during shift changes) | Full |
| NFR20 (Offline caching) | Full |
| NFR21 (Auto-sync on reconnect) | Full |
| NFR24 (Immutable records) | Full |
| NFR25 (Audit retention 90 days) | Full |

## Stories

---

### Story 9.1: Shift Handoff Trigger

**As an** outgoing Supervisor,
**I want** to initiate a shift handoff process,
**So that** I can transfer knowledge to the incoming shift.

**Acceptance Criteria:**

**Given** an outgoing Supervisor is ending their shift
**When** they select "Create Shift Handoff" (FR21)
**Then** the handoff creation flow begins
**And** the system pre-populates with their assigned assets
**And** shift time range is auto-detected (last 8 hours)

**Given** the handoff flow starts
**When** the Supervisor views the handoff screen
**Then** they see:
  - Auto-generated shift summary (from tools)
  - Option to add voice notes
  - Option to add text notes
  - Confirmation button

**Given** the Supervisor has no assigned assets
**When** they try to create a handoff
**Then** the system displays "No assets assigned - contact your administrator"
**And** no handoff can be created

**Given** a handoff already exists for this shift
**When** the Supervisor tries to create another
**Then** they are prompted to edit the existing handoff
**Or** create a supplemental note

**Technical Notes:**
- Shift detection: based on current time vs standard shift windows
- Pre-population: query `supervisor_assignments` for user's assets
- Handoff uniqueness: one primary handoff per user per shift
- UI: wizard-style flow with steps

**Files to Create/Modify:**
- `apps/web/src/app/(main)/handoff/new/page.tsx` - Create handoff page
- `apps/web/src/components/handoff/HandoffCreator.tsx` - Creation wizard
- `apps/api/app/api/handoff.py` - Handoff API endpoints
- `apps/api/app/models/handoff.py` - ShiftHandoff schema

---

### Story 9.2: Shift Data Synthesis

**As a** system component,
**I want** to automatically synthesize shift data into a handoff summary,
**So that** Supervisors don't have to manually compile information.

**Acceptance Criteria:**

**Given** a handoff is initiated
**When** the system generates the summary (FR22)
**Then** it calls existing LangChain tools:
  - Production Status (shift output vs target)
  - Downtime Analysis (shift downtime reasons)
  - Safety Events (any incidents during shift)
  - Alert Check (active issues to watch)
**And** results are formatted into a narrative summary

**Given** synthesis completes
**When** the summary is displayed
**Then** it includes:
  - Shift performance overview
  - Issues encountered and status
  - Ongoing concerns (unresolved alerts)
  - Recommended focus for incoming shift
**And** all data includes citations (FR51, FR52)

**Given** a tool fails during synthesis
**When** the failure is detected
**Then** the summary continues with available data
**And** missing sections are noted

**Given** synthesis takes longer than expected
**When** 15 seconds elapse
**Then** partial results are shown
**And** background continues to populate remaining sections

**Technical Notes:**
- Reuse `BriefingService` pattern from Epic 8
- Filter to supervisor's assigned assets only (FR54)
- Time range: shift start to current time
- Narrative style: concise, action-focused

**Files to Create/Modify:**
- `apps/api/app/services/briefing/handoff.py` - Handoff synthesis logic
- `apps/api/app/services/briefing/service.py` - Add handoff synthesis method

---

### Story 9.3: Voice Note Attachment

**As an** outgoing Supervisor,
**I want** to add voice notes to my handoff,
**So that** I can quickly convey context that's hard to type.

**Acceptance Criteria:**

**Given** the Supervisor is creating a handoff
**When** they select "Add Voice Note" (FR23)
**Then** push-to-talk recording begins
**And** visual indicator shows recording active

**Given** recording completes
**When** the Supervisor releases the button
**Then** the audio is transcribed for searchability
**And** both audio and transcript are attached to handoff
**And** Supervisor can review and re-record if needed

**Given** multiple voice notes are added
**When** the handoff is saved
**Then** all notes are preserved in order
**And** each note shows duration and timestamp

**Given** recording fails (permissions, hardware)
**When** the error is detected
**Then** the system suggests text input as fallback
**And** error is logged for troubleshooting

**Technical Notes:**
- Reuse push-to-talk infrastructure from Story 8.2
- Audio storage: Supabase Storage bucket
- Transcription: ElevenLabs Scribe v2
- Max note duration: 60 seconds per note
- Max notes per handoff: 5

**Files to Create/Modify:**
- `apps/web/src/components/handoff/VoiceNoteRecorder.tsx` - Recording component
- `apps/api/app/api/handoff.py` - Add voice note upload endpoint
- `supabase/migrations/20260115_006_handoff_voice_notes.sql` - Voice notes table

---

### Story 9.4: Persistent Handoff Records

**As a** system component,
**I want** handoff records persisted securely,
**So that** incoming Supervisors can access them reliably.

**Acceptance Criteria:**

**Given** a Supervisor submits a handoff
**When** the save operation completes (FR24)
**Then** the handoff is stored in `shift_handoffs` table
**And** record includes: created_by, shift_date, shift_type, assets_covered
**And** status is set to "pending_acknowledgment"

**Given** a handoff is saved
**When** queried later
**Then** the record is immutable (NFR24)
**And** only supplemental notes can be appended
**And** original content cannot be modified

**Given** the handoff includes voice notes
**When** saved
**Then** voice files are stored in Supabase Storage
**And** references are stored in `handoff_voice_notes` table

**Given** database write fails
**When** error is detected
**Then** user is notified with retry option
**And** draft is preserved locally until successful save

**Technical Notes:**
- Table: `shift_handoffs` with RLS policies
- RLS: users can read handoffs they created or are assigned to receive
- Immutability: no UPDATE allowed on core fields, only INSERT to notes
- Voice storage: `handoff-voice-notes` bucket with user_id path prefix

**Files to Create/Modify:**
- `supabase/migrations/20260115_004_shift_handoffs.sql` - Handoffs table
- `supabase/migrations/20260115_009_rls_policies.sql` - RLS policies
- `apps/api/app/services/handoff/storage.py` - Storage operations

---

### Story 9.5: Handoff Review UI

**As an** incoming Supervisor,
**I want** to review the handoff from the previous shift,
**So that** I understand what happened and what to watch.

**Acceptance Criteria:**

**Given** an incoming Supervisor logs in
**When** a pending handoff exists for their assigned assets (FR25)
**Then** a notification/banner indicates "Handoff available from [Name]"
**And** they can click to view the full handoff

**Given** the Supervisor opens a handoff
**When** viewing the handoff detail
**Then** they see:
  - Shift summary (auto-generated)
  - Voice notes (with play buttons)
  - Text notes
  - Timestamp and outgoing supervisor name
  - Acknowledgment button

**Given** voice notes exist
**When** the Supervisor plays them
**Then** audio plays with transcript displayed below
**And** playback controls (play/pause, seek) are available

**Given** the Supervisor views on a tablet
**When** the UI renders
**Then** layout is optimized for tablet viewing
**And** touch targets are appropriately sized

**Technical Notes:**
- Query: `shift_handoffs` WHERE status = 'pending_acknowledgment'
- Filter: assets must overlap with incoming supervisor's assignments
- Audio player: HTML5 audio with custom controls
- Responsive: tablet-first design

**Files to Create/Modify:**
- `apps/web/src/app/(main)/handoff/page.tsx` - Handoff list page
- `apps/web/src/app/(main)/handoff/[id]/page.tsx` - Handoff detail page
- `apps/web/src/components/handoff/HandoffViewer.tsx` - Viewer component
- `apps/web/src/components/handoff/HandoffCard.tsx` - List item card
- `apps/web/src/components/handoff/HandoffList.tsx` - List component

---

### Story 9.6: Handoff Q&A

**As an** incoming Supervisor,
**I want** to ask follow-up questions about the handoff content,
**So that** I can clarify anything unclear before taking over.

**Acceptance Criteria:**

**Given** a Supervisor is viewing a handoff
**When** they have a question (FR26)
**Then** they can type or speak their question
**And** the AI processes it with handoff context

**Given** a question is asked
**When** the AI responds
**Then** the response references specific handoff content where relevant
**And** includes citations to source data (FR52)
**And** response is added to a Q&A thread on the handoff

**Given** the outgoing Supervisor is still online
**When** a question is asked
**Then** they are notified of the question
**And** can respond directly if desired

**Given** the Q&A thread grows
**When** viewed later
**Then** all questions and answers are preserved
**And** visible to both supervisors

**Technical Notes:**
- Q&A context: inject handoff summary into LangChain prompt
- Thread storage: append to handoff record (preserves immutability)
- Real-time: Supabase Realtime for live updates if both online
- AI context: include shift time range and assets for accurate data retrieval

**Files to Create/Modify:**
- `apps/web/src/components/handoff/HandoffQA.tsx` - Q&A component
- `apps/api/app/services/handoff/qa.py` - Q&A processing
- `apps/api/app/api/handoff.py` - Add Q&A endpoint

---

### Story 9.7: Acknowledgment Flow

**As an** incoming Supervisor,
**I want** to acknowledge receipt of the handoff,
**So that** there's a clear record of knowledge transfer.

**Acceptance Criteria:**

**Given** a Supervisor has reviewed a handoff
**When** they click "Acknowledge Handoff" (FR27)
**Then** a confirmation dialog appears
**And** they can optionally add notes (FR29)

**Given** acknowledgment is confirmed
**When** the action completes
**Then** a record is created in `handoff_acknowledgments`
**And** handoff status changes to "acknowledged"
**And** timestamp and acknowledging user are recorded
**And** audit trail is created (FR55)

**Given** acknowledgment includes notes
**When** saved
**Then** notes are attached to the acknowledgment record
**And** visible to both supervisors

**Given** a Supervisor tries to acknowledge offline
**When** the action is triggered
**Then** acknowledgment is queued locally (NFR20)
**And** syncs when connectivity is restored (NFR21)
**And** user sees "Acknowledgment pending sync"

**Technical Notes:**
- Table: `handoff_acknowledgments` with FK to `shift_handoffs`
- Audit: INSERT to `audit_logs` table
- Offline queue: IndexedDB via Service Worker
- Sync: background sync API with retry

**Files to Create/Modify:**
- `apps/web/src/components/handoff/HandoffAcknowledge.tsx` - Acknowledgment form
- `supabase/migrations/20260115_005_handoff_acknowledgments.sql` - Acknowledgments table
- `apps/web/src/lib/offline/sync-queue.ts` - Offline action queue

---

### Story 9.8: Handoff Notifications

**As an** outgoing Supervisor,
**I want** to be notified when my handoff is acknowledged,
**So that** I know the incoming shift received the information.

**Acceptance Criteria:**

**Given** a handoff is acknowledged
**When** the acknowledgment is saved (FR28)
**Then** the outgoing Supervisor receives a notification
**And** notification includes: acknowledging user, timestamp, any notes

**Given** the outgoing Supervisor has the app open
**When** acknowledgment occurs
**Then** an in-app notification appears immediately

**Given** the outgoing Supervisor has the app closed
**When** acknowledgment occurs
**Then** a push notification is sent (if enabled)
**And** notification links to the handoff detail

**Given** notification preferences are disabled
**When** acknowledgment occurs
**Then** no push notification is sent
**And** in-app notification still appears on next visit

**Technical Notes:**
- In-app: Supabase Realtime subscription
- Push: Web Push API via Supabase Edge Function
- User preference: `notification_preferences` in user settings
- Delivery timing: within 60 seconds of acknowledgment

**Files to Create/Modify:**
- `supabase/functions/notify-handoff-ack/index.ts` - Edge Function
- `apps/web/src/lib/notifications/handoff.ts` - In-app notification handler
- `apps/api/app/services/handoff/notifications.py` - Notification trigger

---

### Story 9.9: Offline Handoff Caching

**As a** Supervisor on the plant floor,
**I want** to review handoffs even without connectivity,
**So that** I can access critical information anywhere in the facility.

**Acceptance Criteria:**

**Given** a Supervisor views a handoff online
**When** the handoff loads (FR30)
**Then** it is cached to IndexedDB via Service Worker
**And** cache includes: summary, notes, voice note URLs

**Given** a Supervisor goes offline
**When** they navigate to a cached handoff
**Then** the handoff displays from cache
**And** a banner indicates "Viewing offline - some features limited"

**Given** voice notes are cached
**When** played offline
**Then** audio plays from local cache
**And** transcripts display normally

**Given** cache is older than 48 hours
**When** handoff is accessed
**Then** stale data warning is shown
**And** cache is invalidated on next online access

**Given** connectivity is restored
**When** the app detects online status
**Then** cached data is revalidated
**And** any queued acknowledgments are synced (NFR21)

**Technical Notes:**
- Service Worker: registered on app load
- Cache strategy: cache-then-network for handoffs
- IndexedDB schema: handoffs, voice_notes, pending_actions
- Cache TTL: 48 hours for handoff records
- Audio caching: Cache API for audio files

**Files to Create/Modify:**
- `apps/web/public/sw.js` - Service Worker
- `apps/web/src/lib/offline/handoff-cache.ts` - IndexedDB operations
- `apps/web/src/lib/offline/sw-registration.ts` - SW lifecycle management
- `apps/web/src/lib/hooks/useOfflineSync.ts` - Sync status hook

---

### Story 9.10: End of Day Summary Trigger

**As a** Plant Manager,
**I want** to trigger an end of day summary,
**So that** I can review actual outcomes vs morning expectations.

**Acceptance Criteria:**

**Given** a Plant Manager is ending their day
**When** they select "End of Day Summary" (FR31)
**Then** the EOD summary generation begins
**And** covers the full day's production data

**Given** the summary is generated
**When** displayed to the user
**Then** it includes:
  - Day's overall performance vs target
  - Comparison to morning briefing highlights
  - Wins that materialized
  - Concerns that escalated or resolved
  - Tomorrow's outlook

**Given** no morning briefing was generated today
**When** EOD summary is requested
**Then** the summary shows day's performance without comparison
**And** notes "No morning briefing to compare"

**Technical Notes:**
- Reuse BriefingService with EOD mode
- Time range: 06:00 AM to current time (or shift end)
- Reference: store morning briefing ID for comparison
- All areas covered (Plant Manager scope)

**Files to Create/Modify:**
- `apps/api/app/services/briefing/eod.py` - End of day logic
- `apps/web/src/app/(main)/briefing/eod/page.tsx` - EOD summary page

---

### Story 9.11: Morning vs Actual Comparison

**As a** Plant Manager,
**I want** the EOD summary to compare morning predictions to actual outcomes,
**So that** I can assess prediction accuracy and learn from variances.

**Acceptance Criteria:**

**Given** a morning briefing was generated today
**When** the EOD summary is generated (FR32)
**Then** it retrieves the morning briefing record
**And** compares flagged concerns to actual outcomes

**Given** a concern was flagged in the morning
**When** comparing to actuals (FR33)
**Then** the summary indicates:
  - "Materialized" - issue occurred as predicted
  - "Averted" - issue was prevented/resolved
  - "Escalated" - worse than predicted
  - "Unexpected" - new issue not predicted

**Given** comparison data is available
**When** displayed
**Then** accuracy metrics are shown:
  - Prediction accuracy percentage
  - False positives (flagged but didn't occur)
  - Misses (occurred but not flagged)

**Given** this is tracked over time (FR57)
**When** queried
**Then** prediction accuracy trends are available
**And** inform Action Engine tuning

**Technical Notes:**
- Storage: link morning briefing ID to EOD summary
- Comparison logic: match concerns by asset/issue type
- Accuracy tracking: aggregate stats in analytics table
- Feedback loop: inform Action Engine weights

**Files to Create/Modify:**
- `apps/api/app/services/briefing/eod.py` - Add comparison logic
- `apps/api/app/models/briefing.py` - EODComparisonResult schema

---

### Story 9.12: EOD Push Notification Reminders

**As a** Plant Manager,
**I want** optional reminder notifications for EOD summary,
**So that** I don't forget to review the day's outcomes.

**Acceptance Criteria:**

**Given** a Plant Manager has EOD reminders enabled
**When** the configured reminder time arrives (FR34)
**Then** a push notification is sent
**And** notification says "Ready to review your End of Day summary?"

**Given** the notification is tapped
**When** the app opens
**Then** the EOD summary page is displayed

**Given** the Plant Manager has already viewed EOD today
**When** reminder time arrives
**Then** no notification is sent
**And** system notes "Already reviewed"

**Given** push notification delivery fails
**When** retry threshold is reached
**Then** delivery is logged as failed
**And** no further retries for that day

**Technical Notes:**
- Edge Function: `send-eod-reminder`
- Trigger: Supabase scheduled job (cron)
- Default time: 5:00 PM local time
- User preference: enable/disable + custom time
- Delivery: Web Push API within 60 seconds

**Files to Create/Modify:**
- `supabase/functions/send-eod-reminder/index.ts` - Edge Function
- `supabase/migrations/20260115_008_push_subscriptions.sql` - Subscriptions table
- `apps/web/src/lib/notifications/push-setup.ts` - Push subscription management

---

### Story 9.13: Admin UI - Asset Assignment

**As an** Admin,
**I want** to assign supervisors to specific assets and areas,
**So that** they receive appropriately scoped briefings and handoffs.

**Acceptance Criteria:**

**Given** an Admin navigates to the assignment page
**When** the page loads (FR46)
**Then** they see a grid of:
  - Columns: Areas and Assets
  - Rows: Supervisors
  - Cells: Checkboxes for assignments

**Given** an Admin checks/unchecks an assignment
**When** the change is made
**Then** preview shows impact: "User will see X assets across Y areas" (FR48)
**And** change is not saved until confirmed

**Given** an Admin saves assignments
**When** confirmed
**Then** changes are written to `supervisor_assignments` table
**And** audit log entry is created (FR50, FR56)
**And** affected supervisors see updated scope immediately

**Given** an Admin needs temporary coverage
**When** they make a temporary assignment (FR49)
**Then** an expiration date can be set
**And** assignment auto-reverts after expiration

**Technical Notes:**
- Table: `supervisor_assignments` with optional `expires_at`
- Grid: virtualized for performance with many assets
- Preview: query assets and aggregate
- Audit: INSERT to `audit_logs` with change details

**Files to Create/Modify:**
- `apps/web/src/app/(admin)/assignments/page.tsx` - Assignment page
- `apps/web/src/components/admin/AssetAssignmentGrid.tsx` - Grid component
- `apps/api/app/api/admin.py` - Admin endpoints
- `supabase/migrations/20260115_002_supervisor_assignments.sql` - Add expires_at

---

### Story 9.14: Admin UI - Role Management

**As an** Admin,
**I want** to assign roles to users,
**So that** they have appropriate access and features.

**Acceptance Criteria:**

**Given** an Admin navigates to user management
**When** the page loads (FR47)
**Then** they see a list of users with current roles
**And** roles shown: Plant Manager, Supervisor, Admin

**Given** an Admin changes a user's role
**When** the change is saved
**Then** the `user_roles` table is updated
**And** audit log entry is created (FR56)
**And** user's access changes immediately

**Given** an Admin tries to remove the last Admin
**When** the action is attempted
**Then** the system prevents it
**And** displays "Cannot remove last admin"

**Given** a new user is created (via Supabase Auth)
**When** they first log in
**Then** default role is "Supervisor"
**And** Admin must explicitly promote to Plant Manager or Admin

**Technical Notes:**
- Table: `user_roles` with FK to auth.users
- Role hierarchy: Admin > Plant Manager > Supervisor
- Protection: at least one Admin must exist
- Default: new users get Supervisor role

**Files to Create/Modify:**
- `apps/web/src/app/(admin)/users/page.tsx` - User list page
- `apps/web/src/app/(admin)/users/[id]/page.tsx` - User detail/edit page
- `apps/web/src/components/admin/UserRoleTable.tsx` - User table component
- `supabase/migrations/20260115_001_user_roles.sql` - Roles table

---

### Story 9.15: Admin Audit Logging

**As an** Admin,
**I want** all configuration changes logged,
**So that** we have accountability and can troubleshoot issues.

**Acceptance Criteria:**

**Given** any admin action is taken
**When** the action completes
**Then** an audit log entry is created with:
  - Timestamp
  - Admin user ID
  - Action type (create, update, delete)
  - Target (user_id, asset_id, etc.)
  - Before/after values (for updates)

**Given** an Admin views audit logs
**When** the log page loads
**Then** entries are displayed in reverse chronological order
**And** filters available: date range, action type, target user

**Given** audit log entries exist
**When** 90 days pass (NFR25)
**Then** entries remain available
**And** entries are tamper-evident (append-only)

**Given** bulk actions are performed
**When** logged
**Then** each individual change has its own log entry
**And** entries are linked by a batch ID

**Technical Notes:**
- Table: `audit_logs` with append-only policy (no UPDATE/DELETE)
- Retention: 90 days minimum, configurable
- Index: timestamp, user_id, action_type for efficient queries
- Tamper-evident: hash chain or similar mechanism

**Files to Create/Modify:**
- `supabase/migrations/20260115_007_audit_logs.sql` - Audit table with policies
- `apps/api/app/services/audit/logger.py` - Audit logging service
- `apps/web/src/app/(admin)/audit/page.tsx` - Audit log viewer (optional)

---

## Epic Acceptance Criteria

- [ ] Outgoing supervisors can trigger handoff and add voice notes
- [ ] Handoff records persist and are viewable by incoming supervisor
- [ ] Incoming supervisors can ask follow-up questions with cited answers
- [ ] Acknowledgment creates audit trail; outgoing supervisor notified
- [ ] Handoffs cached locally for offline review (NFR20)
- [ ] Acknowledgment syncs automatically when connectivity restored (NFR21)
- [ ] EOD summary compares morning briefing to actual outcomes
- [ ] Push notification reminders delivered within 60 seconds
- [ ] Admins can assign supervisors to assets with preview (FR48)
- [ ] All admin changes logged with audit trail (FR56)
- [ ] 99.9% uptime during shift change windows (5-7 AM, 5-7 PM) (NFR19)
- [ ] Audit logs retained for 90 days minimum (NFR25)
