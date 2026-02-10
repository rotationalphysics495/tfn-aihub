---
stepsCompleted: ["step-01-validate-prerequisites", "step-02-design-epics", "step-03-create-stories"]
inputDocuments:
  - "docs/improvements.md"
  - "docs/architecture-api.md"
  - "docs/architecture-web.md"
  - "docs/data-models.md"
epic: 18
status: "ready"
---

# Epic 18: Meeting Mode & Teams Integration

## Overview

**Goal:** Plant managers can run their morning standup directly from the app with a condensed talking-points view, and the app reaches out to them daily via Teams with a morning summary card.

**Dependencies:** Epic 13 (assignment visibility for meeting mode is enhanced but core functionality is standalone)

**User Value:** The app structures around the actual workflow (running a standup) and builds the daily habit via Teams push. The manager doesn't need to remember to open the app — it finds them in Teams every morning. Escalation nudges ensure nothing falls through the cracks.

## Requirements Coverage

| Requirement | Coverage |
|-------------|----------|
| FR-I12 (Morning Meeting Mode) | Full |
| FR-I13 (Teams Push Notifications) | Full |

## Stories

---

### Story 18.1: Meeting Mode Toggle & Talking Points View

**As a** Plant Manager running a morning standup,
**I want** a condensed "meeting mode" that shows only the top 3-5 items as large, scannable talking points,
**So that** I can run a 15-minute meeting without getting lost in report details.

**Acceptance Criteria:**

**Given** the morning report page is in normal mode
**When** the user clicks a "Meeting Mode" toggle button in the report header
**Then** the view switches to a condensed layout showing:
  - Top 3-5 action items displayed as large cards with only: headline, asset, priority, and who's assigned
  - Evidence detail is hidden (collapsed/removed)
  - Clear section headers: "Safety" / "Yesterday's Performance" / "Today's Priorities"
**And** the URL updates to include `?mode=meeting`

**Given** the meeting mode view is active
**When** the user views an action item
**Then** the "Assign Follow-Up" button is prominently visible (not discovered in a menu)
**And** assignment badges are visible by default showing who's already assigned

**Given** the user clicks the toggle again
**When** switching back to normal mode
**Then** the full report view is restored with all evidence and detail sections

**Given** the URL includes `?mode=meeting`
**When** the page loads
**Then** meeting mode is activated automatically

**Technical Notes:**
- Toggle button in the morning report header (Shadcn/UI `Toggle` or `Switch`)
- Conditional rendering: hide/show detail sections based on mode state
- URL state: add `mode` to search params alongside `date`
- Meeting mode is a view filter, not a separate page — same data, different layout

**Files to Create/Modify:**
- `apps/web/src/app/morning-report/page.tsx` - Add meeting mode state and toggle
- `apps/web/src/components/report/MeetingModeToggle.tsx` - Toggle button component
- `apps/web/src/components/action-list/MeetingTalkingPoint.tsx` - Condensed action card for meeting mode
- `apps/web/src/components/action-list/ActionListContainer.tsx` - Support meeting mode rendering

---

### Story 18.2: Teams Webhook Configuration

**As a** system administrator,
**I want** to configure a Teams Incoming Webhook URL for the plant,
**So that** the system can post morning summary cards to a Teams channel.

**Acceptance Criteria:**

**Given** an admin navigates to settings
**When** the Teams integration section is visible
**Then** a field for "Teams Webhook URL" is shown
**And** the admin can paste a webhook URL and save it

**Given** a webhook URL is configured
**When** the admin clicks "Test"
**Then** a test message is posted to the configured Teams channel
**And** the result (success/failure) is displayed to the admin

**Given** no webhook URL is configured
**When** the morning cron runs
**Then** no Teams notification is sent
**And** the morning report generation continues normally

**Technical Notes:**
- Store webhook URL in environment variable or settings table
- MVP: environment variable `TEAMS_WEBHOOK_URL` (simplest)
- Test endpoint: `POST /api/v1/notifications/teams/test`
- Teams Incoming Webhook format: JSON card with Adaptive Card schema

**Files to Create/Modify:**
- `apps/api/app/core/config.py` - Add `TEAMS_WEBHOOK_URL` setting
- `apps/api/app/api/notifications.py` - Test webhook endpoint
- `apps/api/app/services/notifications/__init__.py` - Notifications service module
- `apps/api/app/services/notifications/teams.py` - Teams webhook client

---

### Story 18.3: Morning Summary Teams Card

**As a** Plant Manager,
**I want** a summary card posted to my Teams channel at 6:15 AM each morning,
**So that** I'm reminded to check the report and can see the headline before opening the app.

**Acceptance Criteria:**

**Given** the morning data pipeline has completed and action items are generated
**When** 6:15 AM arrives (or the morning cron triggers)
**Then** a Teams card is posted to the configured webhook with:
  - Title: "Morning Report — {date}"
  - Summary: "{N} action items: {safety_count} safety, {oee_count} OEE misses, {financial_count} financial"
  - Top 3 action items as bullet points with asset name and headline
  - "Open Report" button linking to `/morning-report?date={date}`

**Given** there are no action items for the day
**When** the cron triggers
**Then** a card is posted: "Morning Report — {date}: All clear. No action items today."
**And** the "Open Report" link is still included

**Given** the Teams webhook fails (network error, invalid URL)
**When** the notification is attempted
**Then** the failure is logged with error details
**And** the morning report data is unaffected

**Technical Notes:**
- Trigger from the existing morning pipeline cron (Railway Cron at 06:00, teams card at 06:15 to allow data processing)
- Adaptive Card JSON format for rich Teams cards
- Use `httpx` or `aiohttp` for async webhook POST
- Fire-and-forget: don't block other morning processing

**Files to Create/Modify:**
- `apps/api/app/services/notifications/teams.py` - Morning card formatting and posting
- `apps/api/app/services/pipelines/morning_pipeline.py` (or relevant cron handler) - Trigger Teams notification after data processing

---

### Story 18.4: Follow-Up Assignment Teams Notification

**As a** team member assigned a follow-up,
**I want** to receive a Teams notification when a task is assigned to me,
**So that** I'm aware of the assignment immediately in my primary communication tool.

**Acceptance Criteria:**

**Given** a plant manager assigns a follow-up to a team member
**When** the assignment is saved
**Then** a Teams notification is posted mentioning the assignee (if channel webhook) or as a DM (if Graph API):
  - "{assigner_name} assigned you a follow-up: {action_summary} on {asset_name}"
  - Link to respond: "View in App →"

**Given** Teams notifications are not configured (no webhook URL)
**When** a follow-up is assigned
**Then** the assignment succeeds normally
**And** only email notification is sent (if configured in Epic 15)

**Technical Notes:**
- MVP: Post to the same channel webhook used for morning cards (mentions don't work with Incoming Webhooks, but the message is visible)
- Future: Microsoft Graph API for DMs/mentions (requires app registration)
- Trigger from the follow-up creation endpoint in `actions.py`

**Files to Create/Modify:**
- `apps/api/app/services/notifications/teams.py` - Follow-up assignment card formatting
- `apps/api/app/api/actions.py` - Trigger Teams notification on follow-up creation

---

### Story 18.5: Escalation Nudge Notifications

**As a** Plant Manager,
**I want** automatic escalation nudges when safety events go unacknowledged or follow-ups sit without updates,
**So that** critical items don't fall through the cracks.

**Acceptance Criteria:**

**Given** a safety action item has been on the report for 2+ hours without acknowledgment
**When** the escalation check runs (periodic background task)
**Then** a Teams notification is posted: "Safety alert on {asset_name} has been unacknowledged for {hours}. Please review."
**And** the notification includes a direct link to the morning report

**Given** a follow-up has been in "assigned" status for 24+ hours with no status update
**When** the escalation check runs
**Then** a Teams notification is posted: "Follow-up for {asset_name} assigned to {assignee} has had no update for 24 hours"

**Given** a follow-up was recently updated (within 24 hours)
**When** the escalation check runs
**Then** no nudge is sent for that follow-up

**Given** Teams notifications are not configured
**When** escalation conditions are met
**Then** no nudge is sent and the system logs a notice

**Technical Notes:**
- Background task: run every hour via the existing scheduler
- Check `action_acknowledgments` for unacknowledged safety items
- Check `action_followups.updated_at` for stale assignments
- Rate limiting: don't send the same escalation more than once per 4 hours

**Files to Create/Modify:**
- `apps/api/app/services/notifications/escalation.py` - Escalation check logic
- `apps/api/app/services/notifications/teams.py` - Escalation card formatting
- `apps/api/app/main.py` - Register escalation background task with scheduler
