TEST SPEC START
story_id: 18-5-escalation-nudge-notifications
generated: 2026-02-12

test_specifications:

## AC1: Given a safety action item has been on the report for 2+ hours without acknowledgment, When the escalation check runs, Then a Teams notification is posted with the unacknowledged message and a direct link to the morning report.

### 18-5-escalation-nudge-notifications-UNIT-001: Safety escalation card contains correct title and message body
- Priority: P0
- Type: unit
- Given: A safety event with asset_name="Mixer-01", hours_elapsed=3.5, severity="high", report_date=2026-02-12
- When: `build_safety_escalation_card()` is called with those parameters and base_url="https://app.example.com"
- Then: The returned card contains title "Escalation: Safety Alert Unacknowledged" and body text "Safety alert on Mixer-01 has been unacknowledged for 3.5 hours. Please review."
- Data: asset_name="Mixer-01", hours_elapsed=3.5, severity="high", report_date=date(2026, 2, 12), base_url="https://app.example.com"

### 18-5-escalation-nudge-notifications-UNIT-002: Safety escalation card contains Open Report action button with correct URL
- Priority: P0
- Type: unit
- Given: A safety event with report_date=2026-02-12 and base_url="https://app.example.com"
- When: `build_safety_escalation_card()` is called
- Then: The card has an actions array with one Action.OpenUrl titled "Open Report" pointing to "https://app.example.com/morning-report?date=2026-02-12"
- Data: report_date=date(2026, 2, 12), base_url="https://app.example.com"

### 18-5-escalation-nudge-notifications-UNIT-003: Safety escalation card has valid Adaptive Card v1.4 structure
- Priority: P0
- Type: unit
- Given: Valid input parameters for a safety escalation card
- When: `build_safety_escalation_card()` is called
- Then: The returned dict contains "$schema"="http://adaptivecards.io/schemas/adaptive-card.json", "type"="AdaptiveCard", "version"="1.4", a non-empty "body" array, and a non-empty "actions" array
- Data: Any valid safety event parameters

### 18-5-escalation-nudge-notifications-UNIT-004: Safety escalation card includes severity information
- Priority: P1
- Type: unit
- Given: A safety event with severity="critical"
- When: `build_safety_escalation_card()` is called
- Then: The card body contains the severity value "critical" in one of the TextBlock elements
- Data: severity="critical"

### 18-5-escalation-nudge-notifications-INT-001: Unacknowledged safety event older than 2 hours triggers Teams notification
- Priority: P0
- Type: integration
- Given: A safety event exists in `safety_events` with `is_resolved=FALSE` and `created_at` = 3 hours ago, and Teams webhook is configured, and no prior nudge has been sent for this item
- When: `run_escalation_check()` is called
- Then: `send_card()` is called exactly once with a safety escalation Adaptive Card payload containing the asset name and hours elapsed, and a nudge record is written to `escalation_nudge_log`
- Data: Mock Supabase returning one safety_event row: {id: "evt-1", asset_name: "Press-A", severity: "high", created_at: now - 3h, is_resolved: false}

### 18-5-escalation-nudge-notifications-INT-002: Acknowledged (resolved) safety event does NOT trigger escalation
- Priority: P0
- Type: integration
- Given: A safety event exists in `safety_events` with `is_resolved=TRUE` and `created_at` = 5 hours ago
- When: `run_escalation_check()` is called
- Then: No safety escalation card is sent via `send_card()` (the query filters out resolved events)
- Data: Mock Supabase returning empty result for safety items query (resolved items excluded by WHERE clause)

### 18-5-escalation-nudge-notifications-INT-003: Safety event younger than 2 hours does NOT trigger escalation
- Priority: P0
- Type: integration
- Given: A safety event exists in `safety_events` with `is_resolved=FALSE` and `created_at` = 30 minutes ago
- When: `run_escalation_check()` is called
- Then: No safety escalation card is sent (event is within the 2-hour threshold)
- Data: Mock Supabase returning empty result (event too recent to match threshold query)

### 18-5-escalation-nudge-notifications-INT-004: Multiple unacknowledged safety events each get separate notifications
- Priority: P1
- Type: integration
- Given: Three safety events exist, all with `is_resolved=FALSE` and `created_at` > 2 hours ago, no prior nudges
- When: `run_escalation_check()` is called
- Then: `send_card()` is called three times, once per event, and three nudge records are written
- Data: Mock Supabase returning three safety_event rows with distinct asset names

### 18-5-escalation-nudge-notifications-UNIT-005: Safety escalation card handles trailing slash in base_url
- Priority: P2
- Type: unit
- Given: base_url="https://app.example.com/" (with trailing slash)
- When: `build_safety_escalation_card()` is called
- Then: The "Open Report" URL is "https://app.example.com/morning-report?date=2026-02-12" (no double slash)
- Data: base_url="https://app.example.com/", report_date=date(2026, 2, 12)


## AC2: Given a follow-up has been in "assigned" status for 24+ hours with no status update, When the escalation check runs, Then a Teams notification is posted with the stale follow-up message.

### 18-5-escalation-nudge-notifications-UNIT-006: Follow-up escalation card contains correct title and message body
- Priority: P0
- Type: unit
- Given: A stale follow-up with asset_name="Boiler-3", assignee_name="John Doe", hours_since_update=36
- When: `build_followup_escalation_card()` is called with base_url="https://app.example.com" and report_date=2026-02-12
- Then: The returned card contains title "Escalation: Follow-Up Stale" and body text "Follow-up for Boiler-3 assigned to John Doe has had no update for 36 hours."
- Data: asset_name="Boiler-3", assignee_name="John Doe", hours_since_update=36

### 18-5-escalation-nudge-notifications-UNIT-007: Follow-up escalation card contains Open Report action button
- Priority: P0
- Type: unit
- Given: A follow-up escalation card with report_date=2026-02-10 and base_url="https://app.example.com"
- When: `build_followup_escalation_card()` is called
- Then: The card has an Action.OpenUrl titled "Open Report" with URL "https://app.example.com/morning-report?date=2026-02-10"
- Data: report_date=date(2026, 2, 10), base_url="https://app.example.com"

### 18-5-escalation-nudge-notifications-UNIT-008: Follow-up escalation card has valid Adaptive Card v1.4 structure
- Priority: P0
- Type: unit
- Given: Valid input parameters for a follow-up escalation card
- When: `build_followup_escalation_card()` is called
- Then: The returned dict contains "$schema", "type"="AdaptiveCard", "version"="1.4", non-empty "body" and "actions" arrays
- Data: Any valid follow-up parameters

### 18-5-escalation-nudge-notifications-INT-005: Stale follow-up in assigned status for 24+ hours triggers Teams notification
- Priority: P0
- Type: integration
- Given: An action_followup exists with `status='assigned'` and `updated_at` = 30 hours ago, Teams is configured, no prior nudge
- When: `run_escalation_check()` is called
- Then: `send_card()` is called with a follow-up escalation card containing the asset name and assignee name, and a nudge record is written
- Data: Mock Supabase returning one action_followup row: {id: "fu-1", asset_name: "Oven-2", assigned_to: "user-uuid-1", status: "assigned", updated_at: now - 30h}

### 18-5-escalation-nudge-notifications-INT-006: Follow-up in "in_progress" status does NOT trigger escalation
- Priority: P1
- Type: integration
- Given: An action_followup exists with `status='in_progress'` and `updated_at` = 48 hours ago
- When: `run_escalation_check()` is called
- Then: No follow-up escalation card is sent (query only matches status='assigned')
- Data: Mock Supabase returning empty result for stale followups query

### 18-5-escalation-nudge-notifications-INT-007: Follow-up in "resolved" status does NOT trigger escalation
- Priority: P1
- Type: integration
- Given: An action_followup exists with `status='resolved'` and `updated_at` = 72 hours ago
- When: `run_escalation_check()` is called
- Then: No follow-up escalation card is sent
- Data: Mock Supabase returning empty result for stale followups query

### 18-5-escalation-nudge-notifications-INT-008: Multiple stale follow-ups each get separate notifications
- Priority: P1
- Type: integration
- Given: Two action_followups exist, both with `status='assigned'` and `updated_at` > 24 hours ago, no prior nudges
- When: `run_escalation_check()` is called
- Then: `send_card()` is called twice, once per follow-up
- Data: Mock Supabase returning two stale followup rows

### 18-5-escalation-nudge-notifications-UNIT-009: Follow-up escalation card handles unknown assignee gracefully
- Priority: P2
- Type: unit
- Given: Assignee name resolution fails and falls back to "Unknown"
- When: `build_followup_escalation_card()` is called with assignee_name="Unknown"
- Then: The card body text reads "Follow-up for {asset_name} assigned to Unknown has had no update for {hours} hours."
- Data: assignee_name="Unknown"


## AC3: Given a follow-up was recently updated (within 24 hours), When the escalation check runs, Then no nudge is sent for that follow-up.

### 18-5-escalation-nudge-notifications-INT-009: Recently updated follow-up is excluded by database query
- Priority: P0
- Type: integration
- Given: An action_followup exists with `status='assigned'` and `updated_at` = 6 hours ago (within 24h)
- When: `run_escalation_check()` is called
- Then: No follow-up escalation card is sent; `send_card()` is not called for follow-ups
- Data: Mock Supabase returning empty result for stale followups query (updated_at within threshold)

### 18-5-escalation-nudge-notifications-INT-010: Follow-up updated exactly at 24-hour boundary is NOT escalated
- Priority: P1
- Type: integration
- Given: An action_followup exists with `status='assigned'` and `updated_at` = exactly 24 hours ago
- When: `run_escalation_check()` is called
- Then: No follow-up escalation card is sent (boundary condition: 24h is the threshold, requires > 24h)
- Data: Mock Supabase returning empty result at exact boundary

### 18-5-escalation-nudge-notifications-INT-011: Mix of stale and recently-updated follow-ups — only stale ones trigger
- Priority: P1
- Type: integration
- Given: Two follow-ups: one with `updated_at` = 48 hours ago (stale), one with `updated_at` = 2 hours ago (recent), both `status='assigned'`
- When: `run_escalation_check()` is called
- Then: `send_card()` is called exactly once for the stale follow-up; the recently updated one is skipped
- Data: Mock Supabase returning only the stale followup (DB query filters out recent)


## AC4: Given Teams notifications are not configured (no TEAMS_WEBHOOK_URL), When escalation conditions are met, Then no nudge is sent and the system logs a notice at INFO level.

### 18-5-escalation-nudge-notifications-INT-012: Teams not configured — escalation check skips entirely with INFO log
- Priority: P0
- Type: integration
- Given: `TEAMS_WEBHOOK_URL` is empty ("") and escalation-eligible items exist in the database
- When: `run_escalation_check()` is called
- Then: No `send_card()` is called, no database queries are made for safety_events or action_followups, and an INFO-level log message is emitted containing "not configured" or similar
- Data: Mock settings with teams_configured=False; use `caplog` fixture to capture log output

### 18-5-escalation-nudge-notifications-INT-013: Teams not configured — no Supabase queries are executed
- Priority: P1
- Type: integration
- Given: `TEAMS_WEBHOOK_URL` is empty
- When: `run_escalation_check()` is called
- Then: The Supabase client is never instantiated or queried (early return before any DB access)
- Data: Verify `create_client` is never called

### 18-5-escalation-nudge-notifications-UNIT-010: Settings.teams_configured returns False for empty string
- Priority: P1
- Type: unit
- Given: `teams_webhook_url=""` in Settings
- When: `teams_configured` property is accessed
- Then: Returns False
- Data: Settings(teams_webhook_url="")

### 18-5-escalation-nudge-notifications-UNIT-011: Settings.teams_configured returns False for whitespace-only string
- Priority: P2
- Type: unit
- Given: `teams_webhook_url="   "` in Settings
- When: `teams_configured` property is accessed
- Then: Returns False
- Data: Settings(teams_webhook_url="   ")


## AC5: Given an escalation nudge was already sent for an item, When less than 4 hours have passed since the last nudge, Then no duplicate nudge is sent (rate limiting: max once per 4 hours per item).

### 18-5-escalation-nudge-notifications-INT-014: Rate limiting prevents duplicate nudge within 4-hour window
- Priority: P0
- Type: integration
- Given: A safety event is eligible for escalation AND an entry exists in `escalation_nudge_log` with `item_type='safety_event'`, `item_id='evt-1'`, and `nudge_sent_at` = 2 hours ago
- When: `run_escalation_check()` is called
- Then: No `send_card()` is called for that item (rate-limited)
- Data: Mock Supabase returning one safety_event row AND returning a recent nudge log entry for _was_recently_nudged()

### 18-5-escalation-nudge-notifications-INT-015: Rate limiting allows nudge after 4-hour cooldown expires
- Priority: P0
- Type: integration
- Given: A safety event is eligible for escalation AND an entry exists in `escalation_nudge_log` with `nudge_sent_at` = 5 hours ago (past the 4-hour cooldown)
- When: `run_escalation_check()` is called
- Then: `send_card()` IS called for that item AND a new nudge record is written to `escalation_nudge_log`
- Data: Mock Supabase returning one safety_event row AND returning no recent nudge log entry (past cooldown)

### 18-5-escalation-nudge-notifications-INT-016: Rate limiting applies independently per item
- Priority: P1
- Type: integration
- Given: Two safety events (evt-1 and evt-2) are eligible, evt-1 was nudged 1 hour ago, evt-2 has never been nudged
- When: `run_escalation_check()` is called
- Then: `send_card()` is called once for evt-2 only; evt-1 is rate-limited
- Data: Mock Supabase returning two safety_events AND nudge log entry for evt-1 only

### 18-5-escalation-nudge-notifications-INT-017: Rate limiting applies to follow-up items independently from safety events
- Priority: P1
- Type: integration
- Given: One safety event (evt-1) and one follow-up (fu-1) are eligible; evt-1 was nudged 1 hour ago; fu-1 has never been nudged
- When: `run_escalation_check()` is called
- Then: `send_card()` is called once for fu-1; evt-1 is rate-limited
- Data: item_type distinction in nudge log prevents cross-type interference

### 18-5-escalation-nudge-notifications-UNIT-012: _was_recently_nudged returns True when nudge is within cooldown
- Priority: P0
- Type: unit
- Given: `escalation_nudge_log` has an entry for item_type="safety_event", item_id="evt-1" with nudge_sent_at = 1 hour ago, cooldown = 4 hours
- When: `_was_recently_nudged("safety_event", "evt-1")` is called
- Then: Returns True
- Data: Mock Supabase query returning one matching row

### 18-5-escalation-nudge-notifications-UNIT-013: _was_recently_nudged returns False when no prior nudge exists
- Priority: P0
- Type: unit
- Given: `escalation_nudge_log` has no entries for item_type="safety_event", item_id="evt-new"
- When: `_was_recently_nudged("safety_event", "evt-new")` is called
- Then: Returns False
- Data: Mock Supabase query returning empty result

### 18-5-escalation-nudge-notifications-UNIT-014: _record_nudge inserts entry into escalation_nudge_log
- Priority: P1
- Type: unit
- Given: A successful escalation nudge was sent for item_type="followup", item_id="fu-1"
- When: `_record_nudge("followup", "fu-1")` is called
- Then: A row is inserted into `escalation_nudge_log` with item_type="followup", item_id="fu-1", channel="teams", and nudge_sent_at close to now
- Data: Verify Supabase insert call arguments

### 18-5-escalation-nudge-notifications-INT-018: Rate limiting at exact 4-hour boundary
- Priority: P2
- Type: integration
- Given: A safety event is eligible AND the last nudge was exactly 4 hours ago
- When: `run_escalation_check()` is called
- Then: The behavior depends on whether the query uses `<` or `<=` for the cooldown check; test documents the expected boundary behavior (nudge should be allowed at exactly 4h)
- Data: Mock nudge_sent_at = now - 4h exactly


## Cross-cutting: Error handling and orchestration

### 18-5-escalation-nudge-notifications-INT-019: run_escalation_check orchestrates safety and follow-up checks
- Priority: P0
- Type: integration
- Given: Both safety events and stale follow-ups exist, Teams is configured, no prior nudges
- When: `run_escalation_check()` is called
- Then: Both `check_unacknowledged_safety_items()` and `check_stale_followups()` are called, and `send_card()` is invoked for each eligible item
- Data: Mock Supabase returning items from both queries

### 18-5-escalation-nudge-notifications-INT-020: Supabase query failure does not crash the scheduler
- Priority: P0
- Type: integration
- Given: Teams is configured AND the Supabase client raises an exception during safety_events query
- When: `run_escalation_check()` is called
- Then: The exception is caught and logged at ERROR level; the function returns without raising; the scheduler continues to run
- Data: Mock Supabase `select().execute()` raising `Exception("Connection refused")`; verify via `caplog`

### 18-5-escalation-nudge-notifications-INT-021: send_card failure does not crash the scheduler or prevent subsequent checks
- Priority: P0
- Type: integration
- Given: Multiple eligible items exist AND `send_card()` fails (returns success=False) for the first item
- When: `run_escalation_check()` is called
- Then: The failure is logged, but subsequent items are still processed; the function does not raise
- Data: Mock send_card returning {"success": False, "message": "HTTP 500"} for first call, then succeeding

### 18-5-escalation-nudge-notifications-INT-022: No items found — no notifications sent, no errors
- Priority: P1
- Type: integration
- Given: No safety events are unacknowledged and no follow-ups are stale, Teams is configured
- When: `run_escalation_check()` is called
- Then: `send_card()` is never called; no errors are logged; function completes normally
- Data: Mock Supabase returning empty lists for both queries

### 18-5-escalation-nudge-notifications-INT-023: _record_nudge failure does not prevent notification delivery
- Priority: P1
- Type: integration
- Given: An eligible safety event exists, Teams is configured, send_card succeeds, but _record_nudge raises an exception
- When: `run_escalation_check()` is called
- Then: The notification is still sent (card was already delivered), the error is logged, and subsequent items continue processing
- Data: Mock _record_nudge raising Exception; verify send_card was still called

### 18-5-escalation-nudge-notifications-UNIT-015: EscalationChecker uses configurable threshold from settings
- Priority: P1
- Type: unit
- Given: Settings has `escalation_safety_threshold_hours=4` (non-default value)
- When: `check_unacknowledged_safety_items()` constructs its query
- Then: The query uses a 4-hour threshold instead of the default 2 hours
- Data: Mock settings with custom threshold; verify Supabase query includes correct interval

### 18-5-escalation-nudge-notifications-UNIT-016: EscalationChecker uses configurable follow-up threshold from settings
- Priority: P1
- Type: unit
- Given: Settings has `escalation_followup_threshold_hours=48` (non-default value)
- When: `check_stale_followups()` constructs its query
- Then: The query uses a 48-hour threshold instead of the default 24 hours
- Data: Mock settings with custom threshold

### 18-5-escalation-nudge-notifications-UNIT-017: EscalationChecker uses configurable cooldown from settings
- Priority: P1
- Type: unit
- Given: Settings has `escalation_cooldown_hours=8` (non-default value)
- When: `_was_recently_nudged()` constructs its query
- Then: The query checks for nudges within the last 8 hours instead of the default 4
- Data: Mock settings with custom cooldown


## Migration and schema

### 18-5-escalation-nudge-notifications-UNIT-018: escalation_nudge_log migration creates correct table schema
- Priority: P1
- Type: unit
- Given: The SQL migration file `0036_escalation_nudge_log.sql` exists
- When: The migration SQL is reviewed
- Then: It creates a table `escalation_nudge_log` with columns: id UUID PK, item_type TEXT NOT NULL, item_id TEXT NOT NULL, nudge_sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), channel TEXT NOT NULL DEFAULT 'teams'; it creates a composite index on (item_type, item_id, nudge_sent_at DESC); it enables RLS with service_role-only full access
- Data: Static SQL file review


edge_cases:
  - Safety event created exactly 2 hours ago (boundary condition for threshold)
  - Follow-up updated exactly 24 hours ago (boundary condition for staleness)
  - Nudge sent exactly 4 hours ago (boundary condition for rate limiting)
  - Very long asset_name or assignee_name in card text (potential rendering issues)
  - Multiple safety events for the same asset (each should get independent nudges)
  - Follow-up with NULL asset_name (column is nullable per schema)
  - Concurrent escalation check runs (scheduler fires overlapping executions)
  - Supabase returns partial failure (e.g., safety query succeeds but followup query fails)
  - Teams webhook returns HTTP 429 (rate limited by Teams itself)
  - System clock skew affecting threshold calculations

error_scenarios:
  - Supabase client creation fails (invalid URL or key)
  - Supabase query times out
  - Teams webhook URL is malformed
  - Teams webhook returns 500 Internal Server Error
  - Teams webhook connection refused
  - Teams webhook times out (>10s)
  - escalation_nudge_log insert fails (DB constraint violation)
  - escalation_nudge_log query fails during rate-limit check
  - Assignee UUID resolution fails (user deleted from auth.users)
  - Settings object cannot be loaded (configuration error)

test_file_mapping:
  - 18-5-escalation-nudge-notifications-UNIT-001 to UNIT-005: apps/api/tests/services/notifications/test_escalation_cards.py
  - 18-5-escalation-nudge-notifications-UNIT-006 to UNIT-009: apps/api/tests/services/notifications/test_escalation_cards.py
  - 18-5-escalation-nudge-notifications-UNIT-010 to UNIT-011: apps/api/tests/services/notifications/test_escalation_cards.py (or config test file)
  - 18-5-escalation-nudge-notifications-UNIT-012 to UNIT-018: apps/api/tests/services/notifications/test_escalation.py
  - 18-5-escalation-nudge-notifications-INT-001 to INT-023: apps/api/tests/services/notifications/test_escalation.py

TEST SPEC END
