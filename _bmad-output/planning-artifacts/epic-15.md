---
stepsCompleted: ["step-01-validate-prerequisites", "step-02-design-epics", "step-03-create-stories"]
inputDocuments:
  - "docs/improvements.md"
  - "docs/architecture-api.md"
  - "docs/architecture-web.md"
  - "docs/data-models.md"
epic: 15
status: "ready"
---

# Epic 15: Email Notifications & Response Tracking

## Overview

**Goal:** When a follow-up is assigned, the assignee gets an email notification and can respond via a simple link — creating an auditable conversation thread visible to the manager without leaving the app.

**Dependencies:** Epic 13 (follow-up assignments must exist for notifications to trigger)

**User Value:** Meets assignees where they are (inbox). Eliminates "did you see my assignment?" conversations. Creates the audit trail that feeds action plans (Epic 16). The full conversation — what was sent, what was replied, when — is logged for accountability.

## Requirements Coverage

| Requirement | Coverage |
|-------------|----------|
| FR-I7 (Email Notifications with Response Tracking) | Full |
| NFR-I3 (Audit Trail) | Partial (email/response persistence) |
| NFR-I4 (Email Delivery < 60s) | Full |
| NFR-I8 (RLS Compliance) | Full |

## Stories

---

### Story 15.1: Follow-Up Messages Data Model

**As a** developer,
**I want** a `followup_messages` table that logs all outbound notifications and inbound responses,
**So that** the system maintains a complete conversation thread for each follow-up.

**Acceptance Criteria:**

**Given** the migration runs successfully
**When** the database is queried
**Then** the `followup_messages` table exists with columns:
  - `id` (UUID PK)
  - `followup_id` (UUID FK → action_followups)
  - `sender_id` (UUID FK → auth.users, nullable for email replies from non-app-users)
  - `sender_email` (TEXT)
  - `direction` (TEXT CHECK ('outbound', 'inbound'))
  - `message_type` (TEXT CHECK ('assignment', 'response', 'escalation', 'status_update'))
  - `subject` (TEXT)
  - `body` (TEXT)
  - `sent_at` (TIMESTAMPTZ)
  - `created_at` (TIMESTAMPTZ)
**And** indexes exist on `followup_id`, `direction`, `sent_at`
**And** RLS allows assigner and assignee to read messages for their follow-ups

**Technical Notes:**
- Migration: `supabase/migrations/0030_followup_messages.sql`
- RLS: visible to users where `followup_id` matches a follow-up they assigned or are assigned to

**Files to Create/Modify:**
- `supabase/migrations/0030_followup_messages.sql` - New table

---

### Story 15.2: Email Notification Service

**As a** system administrator,
**I want** an email service that sends notifications when follow-ups are assigned,
**So that** assignees are notified immediately without needing to check the app.

**Acceptance Criteria:**

**Given** a follow-up is created via the Assign Follow-Up dialog
**When** the assignment is saved to the database
**Then** an email is sent to the assignee within 60 seconds containing:
  - Subject: `[Action Required] {category} — {asset_name}: {action_summary}`
  - Body: action item details (recommendation, evidence summary, financial impact), who assigned it, the optional note, and a "Respond" button/link
**And** a record is created in `followup_messages` with direction='outbound', message_type='assignment'

**Given** the email provider is not configured (no SMTP credentials)
**When** a follow-up is assigned
**Then** the assignment is still saved successfully
**And** a warning is logged that email notification could not be sent
**And** the system does not block the assignment

**Given** the email send fails (network error, invalid address)
**When** the notification is attempted
**Then** the failure is logged with error details
**And** the follow-up assignment is not rolled back
**And** the `followup_messages` record is created with a `failed_at` indicator

**Technical Notes:**
- Email service abstraction: `apps/api/app/services/email/` with provider interface
- MVP provider: SMTP via `smtplib` or `aiosmtplib` (works with M365, SendGrid, SES)
- Configuration via env vars: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`
- Fire-and-forget pattern: don't block the API response waiting for email delivery
- HTML email template with inline styles for cross-client compatibility

**Files to Create/Modify:**
- `apps/api/app/services/email/__init__.py` - Email service module
- `apps/api/app/services/email/provider.py` - SMTP provider implementation
- `apps/api/app/services/email/templates.py` - HTML email templates
- `apps/api/app/core/config.py` - Add SMTP configuration settings
- `apps/api/app/api/actions.py` - Trigger email on follow-up creation

---

### Story 15.3: Response Capture via Token Link

**As a** team member assigned a follow-up,
**I want** to click a link in the notification email and submit my response without logging into the app,
**So that** I can respond quickly with minimal friction.

**Acceptance Criteria:**

**Given** the assignee receives the notification email
**When** they click the "Respond" link
**Then** they are taken to `{app_url}/followups/{id}/respond?token={one_time_token}`
**And** the page shows the original action item context and a text response field

**Given** the assignee submits a response via the form
**When** the response is submitted
**Then** a record is created in `followup_messages` with direction='inbound', message_type='response'
**And** the follow-up status is updated to 'in_progress' (if currently 'assigned')
**And** a success confirmation is shown

**Given** the response token has already been used or is expired (>72 hours)
**When** the assignee clicks the link
**Then** a message is shown: "This link has expired. Please log in to the app to respond."

**Given** the response token is invalid
**When** the link is accessed
**Then** a 404 or "invalid link" message is shown

**Technical Notes:**
- Generate a unique token (UUID or JWT with expiry) when the notification email is sent
- Store token in `followup_messages` or a separate `response_tokens` table
- Public endpoint (no auth required): `POST /api/v1/followups/respond`
- Token validates: not expired, not already used, maps to valid followup_id
- Page: simple standalone page at `apps/web/src/app/followups/[id]/respond/page.tsx`

**Files to Create/Modify:**
- `apps/api/app/api/followups.py` - Response submission endpoint (public, token-authenticated)
- `apps/api/app/services/email/tokens.py` - Token generation and validation
- `apps/web/src/app/followups/[id]/respond/page.tsx` - Response form page

---

### Story 15.4: Message Thread UI

**As a** Plant Manager,
**I want** to see the full conversation thread for a follow-up (what was sent, what was replied, when),
**So that** I can review the assignee's findings without leaving the app.

**Acceptance Criteria:**

**Given** a follow-up has messages (outbound notification + inbound response)
**When** the manager views the follow-up detail (from My Assignments panel or action card)
**Then** a chronological message thread is displayed showing:
  - Assignment notification: "Sent to Carlos at 6:15 AM" with the original message
  - Response: "Carlos replied at 8:42 AM" with the response text
  - Status updates: "Carlos marked as in-progress at 9:00 AM"

**Given** a response has come in that the manager hasn't viewed
**When** the My Assignments panel shows
**Then** an unread indicator (badge/dot) appears on the follow-up entry

**Given** a follow-up has no responses yet
**When** the thread view is opened
**Then** only the outbound notification is shown
**And** a note appears: "Awaiting response from {assignee_name}"

**Technical Notes:**
- Fetch messages via `GET /api/v1/followups/{id}/messages`
- Display as a chat-style thread with alternating alignment (sent/received)
- Unread tracking: compare `followup_messages.sent_at` of latest inbound vs. a `last_viewed_at` field
- Integrate into the existing follow-up detail within My Assignments panel

**Files to Create/Modify:**
- `apps/web/src/components/action-list/MessageThread.tsx` - Thread display component
- `apps/web/src/hooks/useFollowUpMessages.ts` - Messages fetch hook
- `apps/api/app/api/followups.py` - Messages list endpoint
- `apps/web/src/components/action-list/FollowUpEntry.tsx` - Add unread indicator
