# Story 18.5: Escalation Nudge Notifications

Status: ready-for-dev

## Story

As a Plant Manager,
I want automatic escalation nudges when safety events go unacknowledged or follow-ups sit without updates,
so that critical items don't fall through the cracks.

## Acceptance Criteria

1. **Given** a safety action item has been on the report for 2+ hours without acknowledgment, **When** the escalation check runs (periodic background task), **Then** a Teams notification is posted: "Safety alert on {asset_name} has been unacknowledged for {hours}. Please review." **And** the notification includes a direct link to the morning report.

2. **Given** a follow-up has been in "assigned" status for 24+ hours with no status update, **When** the escalation check runs, **Then** a Teams notification is posted: "Follow-up for {asset_name} assigned to {assignee} has had no update for 24 hours."

3. **Given** a follow-up was recently updated (within 24 hours), **When** the escalation check runs, **Then** no nudge is sent for that follow-up.

4. **Given** Teams notifications are not configured (no `TEAMS_WEBHOOK_URL`), **When** escalation conditions are met, **Then** no nudge is sent and the system logs a notice at INFO level.

5. **Given** an escalation nudge was already sent for an item, **When** less than 4 hours have passed since the last nudge for that same item, **Then** no duplicate nudge is sent (rate limiting: max once per 4 hours per item).

## Tasks / Subtasks

- [ ] Task 1: Create escalation check service (AC: #1, #2, #3, #5)
  - [ ] 1.1 Create `apps/api/app/services/notifications/__init__.py` (empty init, ensure module exists)
  - [ ] 1.2 Create `apps/api/app/services/notifications/escalation.py` with `EscalationChecker` class
  - [ ] 1.3 Implement `check_unacknowledged_safety_items()` — query `safety_events` for items older than 2 hours with status != 'resolved' and no matching acknowledgment
  - [ ] 1.4 Implement `check_stale_followups()` — query `action_followups` where `status = 'assigned'` and `updated_at` < NOW() - 24 hours
  - [ ] 1.5 Implement rate-limiting logic using an in-memory dict (`_last_nudge_times`) tracking `{item_type}:{item_id}` -> last nudge timestamp, with 4-hour cooldown
  - [ ] 1.6 Implement `run_escalation_check()` as the main orchestrator function that calls both checks, applies rate limits, and dispatches notifications

- [ ] Task 2: Create escalation card formatting in Teams service (AC: #1, #2)
  - [ ] 2.1 Create `apps/api/app/services/notifications/teams.py` with `TeamsWebhookClient` class (if not already created by Story 18.2)
  - [ ] 2.2 Add `format_safety_escalation_card()` — Adaptive Card JSON for unacknowledged safety alerts, including asset name, hours elapsed, severity, and "Open Report" action button linking to `/morning-report?date={date}`
  - [ ] 2.3 Add `format_followup_escalation_card()` — Adaptive Card JSON for stale follow-ups, including asset name, assignee name, hours since assignment, and "Open Report" action button
  - [ ] 2.4 Add `send_card()` method using `httpx` async POST to the configured webhook URL with error handling and logging

- [ ] Task 3: Register escalation background task with scheduler (AC: #1, #2)
  - [ ] 3.1 Update `apps/api/app/main.py` to import and register the escalation check job with the existing `PipelineScheduler`
  - [ ] 3.2 Add a new `IntervalTrigger` job (1-hour interval) for `run_escalation_check` alongside the existing `live_pulse_poll` job
  - [ ] 3.3 Add `ESCALATION_CHECK_INTERVAL_MINUTES` environment variable (default: 60)

- [ ] Task 4: Add Teams webhook configuration (AC: #4)
  - [ ] 4.1 Add `TEAMS_WEBHOOK_URL` setting to `apps/api/app/core/config.py` (empty string default)
  - [ ] 4.2 Add `teams_configured` property to `Settings` class that checks if `TEAMS_WEBHOOK_URL` is non-empty
  - [ ] 4.3 Ensure escalation checker gracefully skips when Teams is not configured, logging at INFO level

- [ ] Task 5: Create Supabase migration for escalation tracking (AC: #5)
  - [ ] 5.1 Create `supabase/migrations/NNNN_escalation_nudge_log.sql` with `escalation_nudge_log` table for persistent rate-limit tracking across restarts
  - [ ] 5.2 Table schema: `id UUID PK`, `item_type TEXT` ('safety_event' | 'followup'), `item_id TEXT`, `nudge_sent_at TIMESTAMPTZ`, `channel TEXT` ('teams'), plus index on `(item_type, item_id, nudge_sent_at)`
  - [ ] 5.3 Add RLS: service_role full access only (background task runs as service role)

- [ ] Task 6: Write tests (AC: #1-#5)
  - [ ] 6.1 Create `apps/api/tests/services/notifications/test_escalation.py`
  - [ ] 6.2 Test: unacknowledged safety item older than 2 hours triggers escalation
  - [ ] 6.3 Test: acknowledged safety item does NOT trigger escalation
  - [ ] 6.4 Test: stale follow-up (>24h in assigned status) triggers escalation
  - [ ] 6.5 Test: recently updated follow-up does NOT trigger escalation
  - [ ] 6.6 Test: rate limiting prevents duplicate nudges within 4-hour window
  - [ ] 6.7 Test: no notification sent when Teams webhook is not configured
  - [ ] 6.8 Test: Adaptive Card JSON is valid and contains required fields
  - [ ] 6.9 Test: `run_escalation_check()` orchestrates all checks correctly

## Dev Notes

### Architecture Patterns & Constraints

- **Scheduler:** The project uses APScheduler (`AsyncIOScheduler`) via a singleton `PipelineScheduler` in `apps/api/app/services/scheduler.py`. Currently it runs only the `live_pulse_poll` job. The escalation check must be registered as a second job on the same scheduler instance -- do NOT create a separate scheduler.
- **Supabase client pattern:** Use `create_client(settings.supabase_url, settings.supabase_key)` from `supabase-py`. The service role key provides full access bypassing RLS. See `morning_report.py` for the pattern.
- **HTTP client:** `httpx` (>=0.26.0) is already in `requirements.txt`. Use `httpx.AsyncClient` for webhook POSTs. Do NOT add `aiohttp` or `requests`.
- **Config pattern:** Use `pydantic-settings` `BaseSettings` in `apps/api/app/core/config.py`. Add new env vars as class attributes with defaults. Add a `@property` for `teams_configured`.
- **Logging:** Use `logging.getLogger(__name__)` consistently. Log escalation events at INFO, failures at ERROR. Never log webhook URLs or secrets.
- **Error handling:** Escalation checks must NEVER crash the scheduler or affect other jobs. Wrap everything in try/except and log failures. Fire-and-forget pattern -- don't block.

### Key Data Model Context

**`safety_events` table** (exists in Supabase):
- Columns: `id UUID`, `asset_id UUID`, `area TEXT`, `severity TEXT`, `status TEXT` (open/investigating/resolved), `description TEXT`, `occurred_at TIMESTAMPTZ`, `resolved_at TIMESTAMPTZ`, `created_at TIMESTAMPTZ`
- A safety event is "unacknowledged" if `status` is NOT 'resolved' AND it was created more than 2 hours ago. Note: there is no dedicated `action_acknowledgments` table yet (it is a planned feature per improvements.md). For this story, use `safety_events.status != 'resolved'` as the acknowledgment proxy.

**`action_followups` table** (exists, migration `0025_action_followups.sql`):
- Columns: `id UUID`, `action_item_id TEXT`, `action_summary TEXT`, `asset_name TEXT`, `category TEXT`, `assigned_to UUID`, `assigned_by UUID`, `note TEXT`, `status TEXT` (assigned/in_progress/resolved), `report_date DATE`, `created_at TIMESTAMPTZ`, `updated_at TIMESTAMPTZ`
- A follow-up is "stale" if `status = 'assigned'` AND `updated_at < NOW() - INTERVAL '24 hours'`
- The `updated_at` column is auto-updated by a trigger on any row change, so any status update resets the clock.

### Adaptive Card Format

Teams Incoming Webhooks accept Adaptive Card JSON. Use the following structure:

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
            "text": "Escalation: Safety Alert Unacknowledged",
            "weight": "Bolder",
            "size": "Medium"
          },
          {
            "type": "TextBlock",
            "text": "Safety alert on {asset_name} has been unacknowledged for {hours} hours. Please review.",
            "wrap": true
          }
        ],
        "actions": [
          {
            "type": "Action.OpenUrl",
            "title": "Open Report",
            "url": "{app_url}/morning-report?date={date}"
          }
        ]
      }
    }
  ]
}
```

### Rate Limiting Strategy

Use a dual approach for rate limiting:
1. **In-memory dict** (`_last_nudge_times: Dict[str, datetime]`) for fast lookups during the current process lifetime. Key format: `"{item_type}:{item_id}"`.
2. **Database table** (`escalation_nudge_log`) for persistence across restarts. On startup, the in-memory dict can be lazily populated from recent DB entries.
3. Before sending any nudge, check: was the last nudge for this item within the last 4 hours? If yes, skip.
4. After sending a nudge, write to both in-memory dict and database.

### Scheduler Registration Pattern

In `main.py`, the escalation job should be registered similarly to the live pulse job:

```python
# In lifespan() after existing scheduler setup:
from app.services.notifications.escalation import run_escalation_check

scheduler.add_job(
    run_escalation_check,
    IntervalTrigger(minutes=int(os.getenv("ESCALATION_CHECK_INTERVAL_MINUTES", "60"))),
    id="escalation_check",
    name="Escalation Nudge Check",
    replace_existing=True,
    misfire_grace_time=120,
)
```

Note: The current `PipelineScheduler` only supports a single poll job via `set_poll_job()`. You will need to either:
- **Option A (recommended):** Add escalation job directly on `scheduler._scheduler` (the underlying `AsyncIOScheduler`) after `scheduler.start()` is called. This avoids modifying the PipelineScheduler class.
- **Option B:** Extend `PipelineScheduler` to support multiple jobs. This is cleaner but higher scope.

Choose Option A for minimal scope. The escalation job is independent of the live pulse cycle.

### Environment Variables to Add

| Variable | Default | Description |
|----------|---------|-------------|
| `TEAMS_WEBHOOK_URL` | `""` | Teams Incoming Webhook URL for the plant channel |
| `ESCALATION_CHECK_INTERVAL_MINUTES` | `60` | How often the escalation check runs (minutes) |
| `ESCALATION_SAFETY_THRESHOLD_HOURS` | `2` | Hours before safety event triggers nudge |
| `ESCALATION_FOLLOWUP_THRESHOLD_HOURS` | `24` | Hours before stale follow-up triggers nudge |
| `ESCALATION_COOLDOWN_HOURS` | `4` | Minimum hours between nudges for same item |
| `APP_BASE_URL` | `http://localhost:3000` | Base URL for deep links in notifications |

### Dependencies on Prior Stories

- **Story 18.2 (Teams Webhook Configuration):** Provides `TEAMS_WEBHOOK_URL` config and possibly the `TeamsWebhookClient`. If 18.2 is not yet implemented, this story must create the Teams client from scratch. The code should be structured so 18.2's implementation can be reused or this story's client can be shared.
- **Story 18.3 (Morning Summary Card):** May share the `TeamsWebhookClient` and Adaptive Card formatting utilities. Design the `teams.py` module to be reusable.
- **Story 18.4 (Follow-Up Assignment Notification):** Also uses the Teams client. Ensure the `teams.py` module supports multiple card types.

### Testing Approach

- Use `pytest` with `pytest-asyncio` for async test functions.
- Mock Supabase client responses using `unittest.mock.patch` or `pytest-mock`.
- Mock `httpx.AsyncClient.post` to verify webhook payloads without making real HTTP calls.
- Test rate limiting by manipulating timestamps in the in-memory dict.
- Test the "Teams not configured" path by setting `TEAMS_WEBHOOK_URL` to empty string.

### Project Structure Notes

- New files follow existing service module pattern: `apps/api/app/services/notifications/` is a new service module (does not exist yet -- must create `__init__.py`).
- The `notifications` service module will be shared across Stories 18.2-18.5. Structure it with:
  - `__init__.py` (empty or with convenience imports)
  - `teams.py` (Teams webhook client and card formatting)
  - `escalation.py` (escalation check logic)
- Test files go in `apps/api/tests/services/notifications/` (create directory and `__init__.py`).
- Migration files follow the pattern `NNNN_descriptive_name.sql` in `supabase/migrations/`. Use the next available number after the highest existing migration.

### References

- [Source: docs/architecture-api.md#Application Lifecycle] - Scheduler initialization and lifespan pattern
- [Source: docs/architecture-api.md#Technology Stack] - httpx, APScheduler, FastAPI async patterns
- [Source: docs/data-models.md#Safety & Alert Tables] - safety_events table schema
- [Source: supabase/migrations/0025_action_followups.sql] - action_followups table schema and RLS
- [Source: apps/api/app/services/scheduler.py] - PipelineScheduler implementation and job registration
- [Source: apps/api/app/core/config.py] - Settings class pattern with pydantic-settings
- [Source: apps/api/app/main.py] - Lifespan handler and router registration
- [Source: _bmad-output/planning-artifacts/epic-18.md#Story 18.5] - Epic story requirements
- [Source: docs/improvements.md#Teams push notifications] - Escalation nudge concept and timing rules

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
