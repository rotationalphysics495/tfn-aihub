# Story 18.4: Follow-Up Assignment Teams Notification

Status: ready-for-dev

## Story

As a team member assigned a follow-up,
I want to receive a Teams notification when a task is assigned to me,
so that I'm aware of the assignment immediately in my primary communication tool.

## Acceptance Criteria

1. **AC1 - Teams notification on follow-up assignment:** Given a plant manager assigns a follow-up to a team member, when the assignment is saved, then a Teams notification is posted to the configured webhook channel containing:
   - Message: "{assigner_name} assigned you a follow-up: {action_summary} on {asset_name}"
   - An Adaptive Card with: action summary, asset name, category, priority, assigner name, optional note
   - A "View in App" button linking to the morning report page

2. **AC2 - Graceful degradation when Teams not configured:** Given Teams notifications are not configured (no `TEAMS_WEBHOOK_URL`), when a follow-up is assigned, then the assignment succeeds normally, and a debug-level log is emitted that Teams notification was skipped, and no error is raised.

3. **AC3 - Graceful failure on webhook error:** Given the Teams webhook POST fails (network error, invalid URL, non-2xx response), when the notification is attempted, then the failure is logged with error details, and the follow-up assignment is NOT rolled back, and the API response is not delayed or affected.

4. **AC4 - Fire-and-forget delivery:** Given a follow-up is being assigned, when the Teams notification is triggered, then the API response returns immediately with the created follow-up, and the Teams webhook POST happens asynchronously (does not block the response).

## Tasks / Subtasks

- [ ] Task 1: Add `TEAMS_WEBHOOK_URL` to config (AC: #2)
  - [ ] 1.1 Add `teams_webhook_url: str = ""` to `Settings` class in `apps/api/app/core/config.py`
  - [ ] 1.2 Add `teams_webhook_configured` property returning `bool(self.teams_webhook_url)`
  - [ ] 1.3 Follow exact pattern of existing `*_configured` properties (e.g., `elevenlabs_configured`, `mssql_configured`)

- [ ] Task 2: Create Teams notification service module (AC: #1, #2, #3)
  - [ ] 2.1 Create `apps/api/app/services/notifications/__init__.py` with `get_teams_service()` factory function
  - [ ] 2.2 Create `apps/api/app/services/notifications/teams.py` with `TeamsNotificationService` class
  - [ ] 2.3 Implement `send_followup_assignment_card(followup_data)` method that:
    - Checks `teams_webhook_configured` -- if false, log debug message and return early (AC#2)
    - Builds an Adaptive Card JSON payload
    - POSTs to `TEAMS_WEBHOOK_URL` using `httpx.AsyncClient`
    - Logs success or failure (AC#3)
  - [ ] 2.4 Implement `_build_followup_card(followup_data) -> dict` that returns the Adaptive Card JSON structure with:
    - Header: category icon + "Follow-Up Assigned"
    - Body: action summary, asset name, assigner name, optional note
    - Action button: "View in App" linking to `{app_base_url}/morning-report?date={report_date}`
  - [ ] 2.5 Use `httpx.AsyncClient` with a 10-second timeout for the webhook POST
  - [ ] 2.6 Wrap all webhook operations in try/except to never let failures propagate (AC#3)

- [ ] Task 3: Create or extend the follow-up creation API endpoint (AC: #1, #4)
  - [ ] 3.1 Check if `apps/api/app/api/followups.py` exists from Story 15.2. If yes, add Teams notification trigger to existing endpoint. If not, create the endpoint (see Dev Notes for details).
  - [ ] 3.2 After the follow-up is persisted to `action_followups`, trigger `TeamsNotificationService.send_followup_assignment_card()` via `asyncio.create_task()` (fire-and-forget, AC#4)
  - [ ] 3.3 Resolve assigner display name: query the assigner's email from `auth.users` using Supabase service role client. Use the email local part (before @) as display name.
  - [ ] 3.4 Pass all required data to the notification service: action_summary, asset_name, category, assigner_name, assigned_to display name, note, report_date

- [ ] Task 4: Update frontend to use API endpoint (AC: #1)
  - [ ] 4.1 Check if `AssignFollowUpDialog.tsx` was already updated in Story 15.2 to call `POST /api/v1/followups` instead of direct Supabase insert. If yes, no frontend changes needed. If not, update `handleSubmit` in `AssignFollowUpDialog.tsx` to call the API endpoint instead of inserting directly to Supabase.

- [ ] Task 5: Add `httpx` dependency (AC: #1)
  - [ ] 5.1 Add `httpx>=0.27` to `apps/api/requirements.txt` (if not already present)
  - [ ] 5.2 Verify no conflicts with existing dependencies

- [ ] Task 6: Write tests (AC: #1, #2, #3, #4)
  - [ ] 6.1 Unit test: `TeamsNotificationService.send_followup_assignment_card()` sends correct Adaptive Card JSON to webhook URL
  - [ ] 6.2 Unit test: `_build_followup_card()` produces valid Adaptive Card with all required fields
  - [ ] 6.3 Unit test: When `teams_webhook_configured` is False, notification is skipped with debug log (AC#2)
  - [ ] 6.4 Unit test: When webhook POST fails (httpx error), failure is logged and no exception propagates (AC#3)
  - [ ] 6.5 Integration test: `POST /api/v1/followups` creates follow-up and triggers Teams notification asynchronously
  - [ ] 6.6 Integration test: Webhook failure does not roll back follow-up creation

## Dev Notes

### Critical Architecture Patterns

**Project structure:** TurboRepo monorepo with `apps/api` (Python FastAPI) and `apps/web` (Next.js 14). All backend code is under `apps/api/app/`. Services live in `apps/api/app/services/` organized by domain in subdirectories (e.g., `agent/`, `briefing/`, `handoff/`, `voice/`, `memory/`, `preferences/`, `audit/`).

**Settings pattern (MUST follow):** All configuration is in `apps/api/app/core/config.py` using `pydantic_settings.BaseSettings`. Add `teams_webhook_url` following the exact pattern of existing env var groups. Add a `teams_webhook_configured` property. The singleton is accessed via `get_settings()`.

**Service pattern (MUST follow):** Services in subdirectories use `__init__.py` with a `get_*()` factory function. See `services/agent/`, `services/briefing/`, `services/handoff/` for reference. The notifications service MUST follow this pattern.

**Router pattern (MUST follow):** API routers are in `apps/api/app/api/`. Each creates a `router = APIRouter()` and uses `Depends(get_current_user)` for authentication. Routers are registered in `main.py` with a prefix.

**Supabase client pattern:** Use the Supabase Python client (`supabase-py`). For system operations, use the service role key. The `team.py` router shows how to get a Supabase client and query `auth.users` for email lookup.

### Story 18.2 and 18.3 Dependency

Stories 18.2 (Teams Webhook Configuration) and 18.3 (Morning Summary Teams Card) should be implemented before this story. They establish:
- `TEAMS_WEBHOOK_URL` in config.py (Story 18.2)
- `teams_webhook_configured` property (Story 18.2)
- `apps/api/app/services/notifications/teams.py` module (Story 18.2)
- Adaptive Card formatting patterns (Story 18.3)
- The `httpx` dependency (Story 18.2/18.3)

**If Stories 18.2/18.3 are already implemented:** Extend the existing `teams.py` service with a new `send_followup_assignment_card()` method. Reuse the existing `TeamsNotificationService` class, Adaptive Card builder pattern, and httpx client. DO NOT create a duplicate service or reinvent the webhook posting logic.

**If Stories 18.2/18.3 are NOT yet implemented:** Create the notifications service module from scratch, but structure it so 18.2/18.3 can reuse the same module later. Create `apps/api/app/services/notifications/__init__.py` and `teams.py` with the `TeamsNotificationService` class.

### Story 15.2 Dependency (Follow-Up API Endpoint)

Story 15.2 (Email Notification Service) creates a `POST /api/v1/followups` endpoint in `apps/api/app/api/followups.py` that:
- Accepts follow-up data and inserts into `action_followups`
- Triggers email notification asynchronously
- Returns the created follow-up record

**If Story 15.2 is already implemented:** Add Teams notification trigger alongside the email trigger in the existing `followups.py` endpoint. The fire-and-forget pattern with `asyncio.create_task()` is already established.

**If Story 15.2 is NOT yet implemented:** Create the `POST /api/v1/followups` endpoint yourself. The current flow has the frontend `AssignFollowUpDialog.tsx` inserting directly to Supabase via the JS client. You need to:
1. Create `apps/api/app/api/followups.py` with `POST /api/v1/followups`
2. Register in `main.py`: `app.include_router(followups.router, prefix="/api/v1/followups", tags=["Follow-Ups"])`
3. Update `AssignFollowUpDialog.tsx` to call the API instead of direct Supabase insert
4. Follow the exact pattern from `apps/api/app/api/actions.py` for router structure

### Current Follow-Up Creation Flow

The frontend `AssignFollowUpDialog.tsx` currently inserts directly into Supabase:
```typescript
const { error: insertError } = await supabase
  .from('action_followups')
  .insert({
    action_item_id: actionItem.id,
    action_summary: actionItem.recommendationText,
    asset_name: actionItem.assetName,
    category: actionItem.category.toLowerCase(),
    assigned_to: selectedUserId,
    assigned_by: session.user.id,
    note: note.trim() || null,
    report_date: actionItem.reportDate,
  })
```

This MUST be routed through the backend API so that server-side notifications (Teams, email) can be triggered. The API endpoint should accept the same fields and handle the insert plus notification dispatch.

### Adaptive Card JSON Format for Teams

Teams Incoming Webhooks accept Adaptive Card payloads. The card format:

```json
{
  "type": "message",
  "attachments": [
    {
      "contentType": "application/vnd.microsoft.card.adaptive",
      "content": {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
          {
            "type": "TextBlock",
            "text": "Follow-Up Assigned",
            "weight": "Bolder",
            "size": "Medium"
          },
          {
            "type": "FactSet",
            "facts": [
              { "title": "Action:", "value": "{action_summary}" },
              { "title": "Asset:", "value": "{asset_name}" },
              { "title": "Category:", "value": "{category}" },
              { "title": "Assigned by:", "value": "{assigner_name}" },
              { "title": "Note:", "value": "{note}" }
            ]
          }
        ],
        "actions": [
          {
            "type": "Action.OpenUrl",
            "title": "View in App",
            "url": "{app_base_url}/morning-report?date={report_date}"
          }
        ]
      }
    }
  ]
}
```

**Key constraints:**
- Teams Incoming Webhooks do NOT support @mentions (mentions require Graph API, which is out of scope for MVP)
- The card is posted to the channel, not as a DM
- Adaptive Card version 1.4 is the safe choice for broad Teams client compatibility
- The POST must include `Content-Type: application/json` header

### `httpx` Usage Pattern

Use `httpx.AsyncClient` for the webhook POST (async, non-blocking, compatible with FastAPI):

```python
import httpx

async def _post_to_webhook(self, payload: dict) -> bool:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            return True
    except httpx.HTTPError as e:
        logger.error(f"Teams webhook POST failed: {e}")
        return False
```

### Fire-and-Forget Pattern

The Teams notification MUST NOT block the API response. Use `asyncio.create_task()`:

```python
import asyncio

# In the followups endpoint, after persisting the follow-up:
asyncio.create_task(
    teams_service.send_followup_assignment_card(followup_data)
)
# Return immediately
return created_followup
```

Wrap in try/except within the task so unhandled exceptions don't crash the event loop.

### Resolving Assigner Display Name

The `action_followups.assigned_by` is a UUID referencing `auth.users(id)`. To get a display name:
1. Use Supabase service role client to query `auth.users`
2. Extract the email from the user record
3. Use the email local part (before `@`) as the display name
4. The `team.py` router already implements this pattern -- reuse it

### `app_base_url` Configuration

The "View in App" link needs the app's base URL. Check if `app_base_url` setting exists in `config.py` (Story 15.2 may add it). If not, add `app_base_url: str = "http://localhost:3000"` to the Settings class.

### `action_followups` Table Schema

Table from migration `0025_action_followups.sql`:
- `id` UUID PK (auto-generated)
- `action_item_id` TEXT NOT NULL
- `action_summary` TEXT NOT NULL
- `asset_name` TEXT
- `category` TEXT CHECK (safety, oee, financial)
- `assigned_to` UUID NOT NULL FK auth.users
- `assigned_by` UUID NOT NULL FK auth.users
- `note` TEXT
- `status` TEXT DEFAULT 'assigned' CHECK (assigned, in_progress, resolved)
- `report_date` DATE NOT NULL
- `created_at` TIMESTAMPTZ
- `updated_at` TIMESTAMPTZ

RLS: SELECT for assigned_to/assigned_by, INSERT for assigned_by=auth.uid(), UPDATE for assigned_by, full access for service_role.

### Project Structure Notes

- New files: `apps/api/app/services/notifications/__init__.py`, `apps/api/app/services/notifications/teams.py` (if not created by 18.2/18.3)
- Potentially new: `apps/api/app/api/followups.py` (if not created by Story 15.2)
- Modified files: `apps/api/app/core/config.py` (if 18.2 hasn't added Teams config), `apps/api/app/main.py` (if registering new followups router)
- Frontend modification: `apps/web/src/components/action-engine/AssignFollowUpDialog.tsx` (if not already updated by Story 15.2)
- No conflicts with existing code paths detected
- The notifications service directory (`services/notifications/`) aligns with existing service subdirectory pattern

### Testing Standards

- Tests in `apps/api/tests/` following pytest conventions
- Use `pytest-asyncio` for async test functions
- Mock `httpx.AsyncClient` for webhook POST tests
- Mock `get_settings()` to control `teams_webhook_configured` in tests
- Follow existing test patterns in `apps/api/tests/services/` subdirectories

### References

- [Source: _bmad-output/planning-artifacts/epic-18.md#Story 18.4] - Full story requirements and acceptance criteria
- [Source: _bmad-output/planning-artifacts/epic-18.md#Story 18.2] - Teams webhook configuration dependency
- [Source: _bmad-output/planning-artifacts/epic-18.md#Story 18.3] - Morning summary card pattern dependency
- [Source: _bmad-output/implementation-artifacts/stories/15-2-email-notification-service.md] - Follow-up API endpoint pattern, fire-and-forget notification pattern
- [Source: docs/architecture-api.md#Directory Structure] - API service organization pattern
- [Source: docs/architecture-api.md#Core Architecture Components] - Service patterns and conventions
- [Source: docs/architecture-api.md#API Endpoints] - Router and endpoint conventions
- [Source: docs/data-models.md#Row Level Security] - RLS patterns for Supabase tables
- [Source: supabase/migrations/0025_action_followups.sql] - Follow-up table schema and RLS policies
- [Source: apps/api/app/core/config.py] - Settings pattern with pydantic_settings
- [Source: apps/api/app/main.py] - Router registration pattern and app lifecycle
- [Source: apps/api/app/api/team.py] - Team member lookup and auth.users email resolution pattern
- [Source: apps/web/src/components/action-engine/AssignFollowUpDialog.tsx] - Current frontend follow-up creation flow

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
