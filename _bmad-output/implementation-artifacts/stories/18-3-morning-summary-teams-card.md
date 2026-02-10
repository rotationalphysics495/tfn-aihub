# Story 18.3: Morning Summary Teams Card

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Plant Manager,
I want a summary card posted to my Teams channel at 6:15 AM each morning,
so that I'm reminded to check the report and can see the headline before opening the app.

## Acceptance Criteria

1. **Given** the morning data pipeline has completed and action items are generated, **When** 6:15 AM arrives (or the morning cron triggers), **Then** a Teams Adaptive Card is posted to the configured webhook with:
   - Title: "Morning Report -- {date}"
   - Summary: "{N} action items: {safety_count} safety, {oee_count} OEE misses, {financial_count} financial"
   - Top 3 action items as bullet points with asset name and headline
   - "Open Report" button linking to `/morning-report?date={date}`

2. **Given** there are no action items for the day, **When** the cron triggers, **Then** a card is posted: "Morning Report -- {date}: All clear. No action items today." **And** the "Open Report" link is still included.

3. **Given** the Teams webhook fails (network error, invalid URL), **When** the notification is attempted, **Then** the failure is logged with error details **And** the morning report data is unaffected (fire-and-forget).

## Tasks / Subtasks

- [ ] Task 1: Create Teams notification service module (AC: #1, #2, #3)
  - [ ] 1.1 Create `apps/api/app/services/notifications/__init__.py` package
  - [ ] 1.2 Create `apps/api/app/services/notifications/teams.py` with `TeamsNotificationService` class
  - [ ] 1.3 Implement `build_morning_summary_card()` method that produces Adaptive Card JSON
  - [ ] 1.4 Implement `build_all_clear_card()` method for zero-action-item case (AC: #2)
  - [ ] 1.5 Implement `send_card()` method using `httpx.AsyncClient` to POST to webhook URL
  - [ ] 1.6 Add error handling: log failures, never raise to caller (fire-and-forget) (AC: #3)
- [ ] Task 2: Add `TEAMS_WEBHOOK_URL` configuration (AC: #1)
  - [ ] 2.1 Add `teams_webhook_url: str = ""` to `Settings` in `apps/api/app/core/config.py`
  - [ ] 2.2 Add `teams_webhook_configured` property that checks `bool(self.teams_webhook_url)`
  - [ ] 2.3 Add `WEBAPP_BASE_URL` setting (for "Open Report" link in card)
- [ ] Task 3: Integrate Teams notification into morning pipeline (AC: #1, #2, #3)
  - [ ] 3.1 Add `_trigger_teams_notification()` async function in `morning_report.py`
  - [ ] 3.2 Call it from `run_morning_report()` after smart summary generation succeeds
  - [ ] 3.3 Query action items for the report date to build card content
  - [ ] 3.4 Guard with `if settings.teams_webhook_configured` check (skip silently if not configured)
  - [ ] 3.5 Wrap in try/except to ensure pipeline is never blocked by notification failures
- [ ] Task 4: Write unit tests
  - [ ] 4.1 Test `build_morning_summary_card()` produces valid Adaptive Card JSON with correct structure
  - [ ] 4.2 Test `build_all_clear_card()` produces correct zero-items card
  - [ ] 4.3 Test `send_card()` handles network errors gracefully (mock httpx)
  - [ ] 4.4 Test `send_card()` handles non-200 responses gracefully
  - [ ] 4.5 Test integration: `_trigger_teams_notification()` skips when webhook not configured
  - [ ] 4.6 Test integration: pipeline completes successfully even when Teams notification fails

## Dev Notes

### Architecture & Patterns

- **Service location:** Create new `apps/api/app/services/notifications/` package. This module will be reused by Stories 18.4 (follow-up notifications) and 18.5 (escalation nudges), so design the `TeamsNotificationService` class for extensibility.
- **HTTP client:** Use `httpx` (already in `requirements.txt` at `>=0.26.0`). Use `httpx.AsyncClient` for async HTTP POST to the webhook URL. Do NOT use `requests` or `aiohttp`.
- **Fire-and-forget pattern:** The Teams notification MUST NOT block or fail the morning pipeline. Wrap the entire notification flow in try/except and log errors. The `run_morning_report()` function must return its `PipelineResult` regardless of notification outcome.
- **Singleton pattern:** Follow the existing pattern in `morning_report.py` with module-level singleton (`_service_instance`) and `get_teams_notification_service()` factory function.
- **Config pattern:** Follow the existing `pydantic-settings` pattern in `apps/api/app/core/config.py`. Use `get_settings()` to access configuration. The `TEAMS_WEBHOOK_URL` environment variable is the MVP approach (no database storage needed).

### Adaptive Card Format

Teams Incoming Webhooks accept Adaptive Card JSON. The card payload must follow this structure:

```json
{
  "type": "message",
  "attachments": [
    {
      "contentType": "application/vnd.microsoft.card.adaptive",
      "contentUrl": null,
      "content": {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
          {
            "type": "TextBlock",
            "text": "Morning Report -- 2026-02-10",
            "weight": "Bolder",
            "size": "Medium"
          },
          {
            "type": "TextBlock",
            "text": "5 action items: 1 safety, 2 OEE misses, 2 financial",
            "wrap": true
          },
          {
            "type": "TextBlock",
            "text": "- Grinder 5: Safety event detected\n- CAMA 2400: OEE at 72%\n- Rychiger 101: $1,200 financial loss",
            "wrap": true
          }
        ],
        "actions": [
          {
            "type": "Action.OpenUrl",
            "title": "Open Report",
            "url": "https://app.example.com/morning-report?date=2026-02-10"
          }
        ]
      }
    }
  ]
}
```

**Key constraints:**
- Adaptive Card version must be `1.4` (widely supported in Teams)
- The outer wrapper MUST use `"type": "message"` with `"attachments"` array
- The `contentType` MUST be exactly `"application/vnd.microsoft.card.adaptive"`
- Text blocks must have `"wrap": true` for long content
- The "Open Report" button uses `Action.OpenUrl`

### Action Item Data Source

To populate the card, query the action engine for the report date:

```python
from app.services.action_engine import get_action_engine

engine = get_action_engine()
action_list = await engine.generate_action_list(report_date=target_date)
```

The `ActionListResponse` schema (in `apps/api/app/schemas/action.py`) provides:
- `actions: List[ActionItem]` -- each has `asset_name`, `recommendation_text`, `category`, `priority_level`
- `total_count: int`
- `counts_by_category: Dict[str, int]` -- keys: `"safety"`, `"oee"`, `"financial"`

Use `counts_by_category` directly for the summary line. Take `actions[:3]` for the top 3 bullet points.

### Integration Point in Morning Pipeline

The notification trigger goes in `apps/api/app/services/pipelines/morning_report.py`, inside the `run_morning_report()` function. Insert the call AFTER the smart summary generation (line ~466), following the same pattern:

```python
async def run_morning_report(...) -> PipelineResult:
    pipeline = get_pipeline()
    result = await pipeline.run(target_date, force)

    if generate_smart_summary and result.status in (...):
        await _trigger_smart_summary_generation(...)

    # NEW: Trigger Teams notification after pipeline + summary complete
    await _trigger_teams_notification(
        target_date or (date.today() - timedelta(days=1))
    )

    return result
```

The `_trigger_teams_notification()` function should:
1. Check `settings.teams_webhook_configured` -- return silently if False
2. Get action items via `get_action_engine().generate_action_list(report_date=target_date)`
3. Build the Adaptive Card (morning summary or all-clear depending on `total_count`)
4. Call `TeamsNotificationService.send_card(card_payload)`
5. Catch ALL exceptions, log them, and return (never re-raise)

### Configuration Settings to Add

Add to `apps/api/app/core/config.py` in the `Settings` class:

```python
# Teams Integration (Story 18.2 / 18.3)
teams_webhook_url: str = ""  # Teams Incoming Webhook URL
webapp_base_url: str = "http://localhost:3000"  # Base URL for "Open Report" links

@property
def teams_webhook_configured(self) -> bool:
    """Check if Teams webhook is configured (Story 18.2)."""
    return bool(self.teams_webhook_url)
```

The `webapp_base_url` is needed to construct the "Open Report" link: `f"{settings.webapp_base_url}/morning-report?date={target_date.isoformat()}"`.

### Project Structure Notes

- The `apps/api/app/services/notifications/` directory does NOT exist yet -- it must be created
- The notifications module structure should support future stories:
  - `__init__.py` -- package init, exports `get_teams_notification_service()`
  - `teams.py` -- `TeamsNotificationService` class (this story)
  - Future: `escalation.py` (Story 18.5)
- All new files follow the existing pattern: module docstring with Story/AC references, logging via `logging.getLogger(__name__)`, type hints throughout
- Tests go in `apps/api/tests/services/notifications/` directory (create it)

### References

- [Source: _bmad-output/planning-artifacts/epic-18.md#Story 18.3] -- Story requirements and AC
- [Source: _bmad-output/planning-artifacts/epic-18.md#Story 18.2] -- Predecessor: Teams webhook config (TEAMS_WEBHOOK_URL setting)
- [Source: apps/api/app/services/pipelines/morning_report.py] -- Integration point: `run_morning_report()` function
- [Source: apps/api/app/core/config.py] -- Settings class for adding TEAMS_WEBHOOK_URL and WEBAPP_BASE_URL
- [Source: apps/api/app/schemas/action.py] -- `ActionListResponse`, `ActionItem`, `ActionCategory` schemas
- [Source: apps/api/app/services/action_engine.py] -- `get_action_engine()` singleton factory
- [Source: apps/api/requirements.txt] -- `httpx>=0.26.0` already available
- [Source: docs/architecture-api.md] -- API directory structure, service patterns, testing approach
- [Source: Microsoft Adaptive Cards docs] -- Card schema v1.4 format for Teams webhooks

### Dependencies

- **Story 18.2 (Teams Webhook Configuration):** This story assumes `TEAMS_WEBHOOK_URL` is available as an environment variable. If Story 18.2 is not yet implemented, this story can add the config setting directly (it is just a `str` field in `Settings`). The test endpoint from 18.2 is NOT required for this story.
- **Action Engine (Story 3.1, already done):** The `get_action_engine()` and `ActionListResponse` are already implemented and available.
- **Morning Pipeline (Story 2.1, already done):** The `run_morning_report()` function in `morning_report.py` is the integration point.
- **Smart Summary (Story 3.5, already done):** The notification fires after smart summary generation.

### Anti-Patterns to Avoid

- **DO NOT** create a new cron job or scheduler entry for the Teams notification. It piggybacks on the existing morning pipeline cron (Railway Cron at 06:00). The 15-minute delay (data at 06:00, card at ~06:15) is naturally achieved because the pipeline + summary generation takes several minutes.
- **DO NOT** use `requests` library. Use `httpx` which is already a dependency and supports async.
- **DO NOT** store the webhook URL in the database for MVP. Environment variable is sufficient.
- **DO NOT** let any notification failure propagate -- the pipeline result must be returned to the caller regardless.
- **DO NOT** import or use the `notifications` router (from Story 18.2) -- this story only needs the service layer, not the test API endpoint.

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
