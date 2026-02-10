# Story 15.2: Email Notification Service

Status: ready-for-dev

## Story

As a system administrator,
I want an email service that sends notifications when follow-ups are assigned,
so that assignees are notified immediately without needing to check the app.

## Acceptance Criteria

1. **AC1 - Email sent on follow-up assignment:** Given a follow-up is created via the Assign Follow-Up dialog, when the assignment is saved to the database, then an email is sent to the assignee within 60 seconds containing:
   - Subject: `[Action Required] {category} - {asset_name}: {action_summary}`
   - Body: action item details (recommendation, evidence summary, financial impact), who assigned it, the optional note, and a "Respond" button/link
   - And a record is created in `followup_messages` with `direction='outbound'`, `message_type='assignment'`

2. **AC2 - Graceful degradation when SMTP not configured:** Given the email provider is not configured (no SMTP credentials), when a follow-up is assigned, then the assignment is still saved successfully, and a warning is logged that email notification could not be sent, and the system does not block the assignment.

3. **AC3 - Graceful failure on send error:** Given the email send fails (network error, invalid address), when the notification is attempted, then the failure is logged with error details, and the follow-up assignment is not rolled back, and the `followup_messages` record is created with a `failed_at` indicator.

## Tasks / Subtasks

- [ ] Task 1: Add SMTP configuration settings to `config.py` (AC: #2)
  - [ ] 1.1 Add SMTP env vars to `Settings` class: `smtp_host`, `smtp_port`, `smtp_user`, `smtp_password`, `smtp_from`, `smtp_use_tls` (default True)
  - [ ] 1.2 Add `smtp_configured` property that checks all required SMTP fields are non-empty
  - [ ] 1.3 Add `app_base_url` setting for constructing response links (defaults to `http://localhost:3000`)
  - [ ] 1.4 Follow the exact pattern of existing `*_configured` properties (e.g., `elevenlabs_configured`, `mssql_configured`)

- [ ] Task 2: Create email service module with provider abstraction (AC: #1, #2, #3)
  - [ ] 2.1 Create `apps/api/app/services/email/__init__.py` with `get_email_service()` factory function (follow `get_action_engine()` pattern)
  - [ ] 2.2 Create `apps/api/app/services/email/provider.py` with `EmailProvider` Protocol and `SMTPEmailProvider` implementation
  - [ ] 2.3 Implement `SMTPEmailProvider.send()` using `aiosmtplib` for async SMTP (non-blocking, compatible with FastAPI's async event loop)
  - [ ] 2.4 Implement connection handling: connect per-send (no persistent connection pool for MVP) with configurable timeout (10s default)
  - [ ] 2.5 Implement TLS/STARTTLS support based on `smtp_use_tls` setting
  - [ ] 2.6 Return a `SendResult` dataclass with `success: bool`, `error: Optional[str]`, `sent_at: Optional[datetime]`

- [ ] Task 3: Create HTML email templates (AC: #1)
  - [ ] 3.1 Create `apps/api/app/services/email/templates.py` with `render_assignment_email()` function
  - [ ] 3.2 Build HTML email with inline styles only (no external CSS -- email client compatibility)
  - [ ] 3.3 Include in body: action item category, asset name, recommendation text, evidence summary, financial impact (if applicable), assigner name, optional note
  - [ ] 3.4 Include a "Respond" button/link pointing to `{app_base_url}/followups/{followup_id}/respond?token={token}` (token generation is Story 15.3 -- for now, link to the app without token)
  - [ ] 3.5 Use the project's "Industrial Clarity" color scheme: dark background header (#1a1a2e), white content area, blue CTA button (#3b82f6)
  - [ ] 3.6 Include a plain-text fallback version for email clients that don't render HTML

- [ ] Task 4: Create the notification orchestration service (AC: #1, #2, #3)
  - [ ] 4.1 Create `apps/api/app/services/email/notification_service.py` with `FollowUpNotificationService` class
  - [ ] 4.2 Implement `send_assignment_notification(followup_data)` method that:
    - Checks `smtp_configured` -- if false, log warning and return early (AC#2)
    - Renders the HTML email template
    - Calls `EmailProvider.send()`
    - Creates a `followup_messages` record (outbound, assignment type)
    - If send fails, still creates the `followup_messages` record with `failed_at` set (AC#3)
  - [ ] 4.3 Use fire-and-forget pattern via `asyncio.create_task()` so the API response is not blocked waiting for email delivery
  - [ ] 4.4 Wrap all email operations in try/except to never let email failures propagate to the API response

- [ ] Task 5: Integrate email trigger into follow-up creation flow (AC: #1)
  - [ ] 5.1 Identify where follow-ups are created -- currently the frontend `AssignFollowUpDialog.tsx` inserts directly into Supabase via the JS client
  - [ ] 5.2 Create a new API endpoint `POST /api/v1/followups` in a new `apps/api/app/api/followups.py` router that:
    - Accepts the follow-up data (action_item_id, action_summary, asset_name, category, assigned_to, note, report_date)
    - Inserts into `action_followups` table via Supabase
    - Triggers email notification asynchronously via `FollowUpNotificationService`
    - Returns the created follow-up record
  - [ ] 5.3 Register the new router in `main.py`: `app.include_router(followups.router, prefix="/api/v1/followups", tags=["Follow-Ups"])`
  - [ ] 5.4 Update `apps/web/src/components/action-engine/AssignFollowUpDialog.tsx` (or wherever follow-ups are created) to call the new API endpoint instead of inserting directly to Supabase
  - [ ] 5.5 Ensure the API endpoint resolves the assignee's email from `auth.users` table before sending

- [ ] Task 6: Create `followup_messages` record on notification send (AC: #1, #3)
  - [ ] 6.1 After email send attempt, insert into `followup_messages` table with:
    - `followup_id`: the created follow-up's UUID
    - `sender_id`: the assigner's user ID
    - `sender_email`: the assigner's email
    - `direction`: 'outbound'
    - `message_type`: 'assignment'
    - `subject`: the email subject line
    - `body`: the rendered email body (or summary)
    - `sent_at`: timestamp of successful send (or NULL if failed)
    - `failed_at`: timestamp of failure (or NULL if successful)
  - [ ] 6.2 Use Supabase service role client for this insert (not user-scoped, since this is a system operation)

- [ ] Task 7: Add `aiosmtplib` dependency (AC: #1)
  - [ ] 7.1 Add `aiosmtplib>=2.0` to `apps/api/requirements.txt`
  - [ ] 7.2 Verify compatibility with Python 3.11+ and existing dependencies

- [ ] Task 8: Write tests (AC: #1, #2, #3)
  - [ ] 8.1 Unit test: `SMTPEmailProvider.send()` with mocked SMTP connection
  - [ ] 8.2 Unit test: `render_assignment_email()` produces valid HTML with all required fields
  - [ ] 8.3 Unit test: `FollowUpNotificationService` creates `followup_messages` record on success
  - [ ] 8.4 Unit test: `FollowUpNotificationService` creates `followup_messages` record with `failed_at` on failure
  - [ ] 8.5 Unit test: `FollowUpNotificationService` logs warning and returns when SMTP not configured
  - [ ] 8.6 Integration test: `POST /api/v1/followups` creates follow-up and triggers notification
  - [ ] 8.7 Integration test: Email send failure does not roll back follow-up creation

## Dev Notes

### Critical Architecture Patterns

**Project structure:** TurboRepo monorepo with `apps/api` (Python FastAPI) and `apps/web` (Next.js 14). All backend code is under `apps/api/app/`. Services live in `apps/api/app/services/` organized in subdirectories (e.g., `agent/`, `briefing/`, `handoff/`, `voice/`, `memory/`, `preferences/`, `audit/`).

**Settings pattern (MUST follow):** All configuration is in `apps/api/app/core/config.py` using `pydantic_settings.BaseSettings`. Add SMTP fields following the exact pattern of existing groups (e.g., ElevenLabs, MSSQL). Add a `smtp_configured` property. The singleton is accessed via `get_settings()`.

**Service pattern (MUST follow):** Services in subdirectories use `__init__.py` with a `get_*()` factory function. See `services/agent/`, `services/briefing/`, `services/handoff/` for reference. The email service should follow this exact pattern.

**Router pattern (MUST follow):** API routers are in `apps/api/app/api/`. Each creates a `router = APIRouter()` and uses `Depends(get_current_user)` for authentication. Routers are registered in `main.py` with a prefix. The follow-ups router should be at `/api/v1/followups`.

**Supabase client pattern:** The existing codebase uses the Supabase Python client (`supabase-py`). For system operations (like logging followup_messages), use the service role key. For user-scoped operations (like creating follow-ups), either pass the user's JWT or use service role with manual authorization checks.

**Current follow-up creation flow:** The frontend `AssignFollowUpDialog.tsx` currently inserts directly into Supabase's `action_followups` table using the Supabase JS client. This story introduces a backend API endpoint that handles the insert AND triggers the email. The frontend must be updated to call this API instead of inserting directly.

### Data Model Dependency

**Story 15.1 creates the `followup_messages` table** (migration `0030_followup_messages.sql`) with columns: `id` (UUID PK), `followup_id` (UUID FK to action_followups), `sender_id` (UUID FK to auth.users, nullable), `sender_email` (TEXT), `direction` (TEXT CHECK outbound/inbound), `message_type` (TEXT CHECK assignment/response/escalation/status_update), `subject` (TEXT), `body` (TEXT), `sent_at` (TIMESTAMPTZ), `created_at` (TIMESTAMPTZ). Indexes on `followup_id`, `direction`, `sent_at`. RLS allows assigner and assignee to read messages.

**IMPORTANT:** The epic specifies a `failed_at` indicator for AC#3, but this column is NOT in Story 15.1's schema. You have two options:
1. Add a `failed_at TIMESTAMPTZ` column to the migration in Story 15.1 (preferred if 15.1 hasn't been implemented yet)
2. Create a small migration `0031_followup_messages_failed_at.sql` that adds the column
3. Alternatively, use `sent_at = NULL` to indicate failure and add a `status TEXT CHECK ('sent', 'failed', 'pending')` column

Choose option that best fits the implementation state when you start.

### Existing `action_followups` Table

The `action_followups` table (migration `0025`) has: `id` (UUID PK), `action_item_id` (TEXT), `action_summary` (TEXT), `asset_name` (TEXT), `category` (TEXT), `assigned_to` (UUID FK auth.users), `assigned_by` (UUID FK auth.users), `note` (TEXT), `status` (TEXT DEFAULT 'assigned'), `report_date` (DATE), `created_at`, `updated_at`. RLS policies allow SELECT for assigned_to/assigned_by, INSERT for assigned_by=auth.uid(), UPDATE for assigned_by=auth.uid(), and full access for service_role.

### Email Provider Choice

The epic notes MVP should use SMTP via `aiosmtplib` which works with M365, SendGrid, and AWS SES. Use `aiosmtplib` (not `smtplib`) because the API is async (FastAPI). The provider abstraction (`EmailProvider` Protocol) enables swapping to a direct SendGrid/SES SDK later without changing the notification service.

### Fire-and-Forget Pattern

The email must NOT block the API response. Use `asyncio.create_task()` to dispatch the notification asynchronously after the follow-up is persisted. The API response returns immediately with the created follow-up. If the email fails later, it logs the error and marks the `followup_messages` record accordingly. This is critical for meeting NFR-I4 (email delivery < 60s) while keeping the assignment API fast.

### Resolving Assignee Email

The `action_followups.assigned_to` is a UUID referencing `auth.users(id)`. To get the assignee's email, query the Supabase `auth.users` table. The service role client can access this. Note: The `team.py` router already implements team member lookup from auth.users -- reuse that pattern.

### HTML Email Design

Use inline styles only (external CSS is stripped by most email clients). Keep the design simple and readable:
- Dark header with app name and action category
- White content area with the action details
- Blue CTA button for "Respond" link
- Plain text fallback for clients that don't render HTML
- Test with common clients: Outlook, Gmail, Apple Mail

### Project Structure Notes

- New files align with the existing service subdirectory pattern (`services/email/` alongside `services/voice/`, `services/briefing/`, etc.)
- New API router (`api/followups.py`) follows the established pattern of one router per domain
- The router prefix `/api/v1/followups` is consistent with the versioned API pattern used by other recent endpoints
- Migration numbering continues from 0030 (Story 15.1)
- No conflicts with existing code paths detected

### References

- [Source: docs/improvements.md#Email notifications with response tracking] - Full feature description and design decisions
- [Source: docs/architecture-api.md#Directory Structure] - API service organization pattern
- [Source: docs/architecture-api.md#Core Architecture Components] - Service patterns and conventions
- [Source: docs/architecture-api.md#API Endpoints] - Router and endpoint conventions
- [Source: docs/data-models.md#Row Level Security] - RLS patterns for Supabase tables
- [Source: _bmad-output/planning-artifacts/epic-15.md#Story 15.2] - Full story requirements and acceptance criteria
- [Source: _bmad-output/planning-artifacts/epic-15.md#Story 15.1] - followup_messages data model dependency
- [Source: _bmad-output/planning-artifacts/epic-13.md] - Follow-up assignment flow and action_followups table context
- [Source: supabase/migrations/0025_action_followups.sql] - Existing follow-up table schema and RLS policies
- [Source: apps/api/app/core/config.py] - Settings pattern with pydantic_settings
- [Source: apps/api/app/main.py] - Router registration pattern
- [Source: apps/api/app/api/actions.py] - API endpoint pattern with auth and dependencies
- [Source: _bmad-output/implementation-artifacts/stories/13-3-followup-status-updates-rls.md] - Follow-up endpoint patterns, Supabase client usage for RLS

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
