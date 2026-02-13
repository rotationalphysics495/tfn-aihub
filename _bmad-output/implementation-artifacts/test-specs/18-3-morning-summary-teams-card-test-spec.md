TEST SPEC START
story_id: 18-3-morning-summary-teams-card
generated: 2026-02-12

test_specifications:

## AC1: Given the morning data pipeline has completed and action items are generated, When 6:15 AM arrives (or the morning cron triggers), Then a Teams Adaptive Card is posted to the configured webhook with: Title "Morning Report -- {date}", Summary "{N} action items: {safety_count} safety, {oee_count} OEE misses, {financial_count} financial", Top 3 action items as bullet points with asset name and headline, "Open Report" button linking to /morning-report?date={date}

### 18-3-morning-summary-teams-card-UNIT-001: build_morning_summary_card produces valid Adaptive Card JSON structure
- Priority: P0
- Type: unit
- Given: An ActionListResponse with 5 action items (1 safety, 2 OEE, 2 financial) and report_date=2026-02-10
- When: build_morning_summary_card(action_list, report_date, base_url) is called
- Then: The returned dict contains "$schema": "http://adaptivecards.io/schemas/adaptive-card.json", "type": "AdaptiveCard", "version": "1.4", a "body" array with 3 TextBlock elements, and an "actions" array with 1 Action.OpenUrl element
- Data: ActionListResponse with total_count=5, counts_by_category={"safety": 1, "oee": 2, "financial": 2}, 5 ActionItem objects with distinct asset_name and recommendation_text values

### 18-3-morning-summary-teams-card-UNIT-002: Card title uses correct format "Morning Report -- {date}"
- Priority: P0
- Type: unit
- Given: A report_date of 2026-02-10
- When: build_morning_summary_card() is called
- Then: The first TextBlock in body has text "Morning Report -- 2026-02-10", weight "Bolder", size "Medium"
- Data: Any valid ActionListResponse with total_count > 0

### 18-3-morning-summary-teams-card-UNIT-003: Summary line shows correct category counts
- Priority: P0
- Type: unit
- Given: An ActionListResponse with total_count=5, counts_by_category={"safety": 1, "oee": 2, "financial": 2}
- When: build_morning_summary_card() is called
- Then: The second TextBlock has text "5 action items: 1 safety, 2 OEE misses, 2 financial" and wrap=true
- Data: ActionListResponse with specific category counts

### 18-3-morning-summary-teams-card-UNIT-004: Top 3 action items rendered as bullet points with asset name and headline
- Priority: P0
- Type: unit
- Given: An ActionListResponse with 5 actions where the first 3 are: (Grinder 5, "Safety event detected"), (CAMA 2400, "OEE at 72%"), (Rychiger 101, "$1,200 financial loss")
- When: build_morning_summary_card() is called
- Then: The third TextBlock contains "- Grinder 5: Safety event detected\n- CAMA 2400: OEE at 72%\n- Rychiger 101: $1,200 financial loss" and wrap=true
- Data: 5 ActionItem objects; only the first 3 should appear in the bullet list

### 18-3-morning-summary-teams-card-UNIT-005: Open Report button uses correct URL with date parameter
- Priority: P0
- Type: unit
- Given: base_url="https://app.example.com" and report_date=2026-02-10
- When: build_morning_summary_card() is called
- Then: The actions array contains one Action.OpenUrl with title "Open Report" and url "https://app.example.com/morning-report?date=2026-02-10"
- Data: Valid ActionListResponse, base_url, report_date

### 18-3-morning-summary-teams-card-UNIT-006: Card with exactly 3 action items shows all 3 in bullets (no truncation)
- Priority: P1
- Type: unit
- Given: An ActionListResponse with exactly 3 action items
- When: build_morning_summary_card() is called
- Then: The bullet point TextBlock contains exactly 3 lines (one per action), each with "- {asset_name}: {recommendation_text}"
- Data: ActionListResponse with total_count=3, 3 ActionItem objects

### 18-3-morning-summary-teams-card-UNIT-007: Card with fewer than 3 action items shows only available items
- Priority: P1
- Type: unit
- Given: An ActionListResponse with 1 action item (1 safety, 0 OEE, 0 financial)
- When: build_morning_summary_card() is called
- Then: The summary line reads "1 action items: 1 safety, 0 OEE misses, 0 financial" and the bullet TextBlock contains exactly 1 bullet line
- Data: ActionListResponse with total_count=1, 1 ActionItem

### 18-3-morning-summary-teams-card-UNIT-008: Long recommendation text is truncated in bullet points
- Priority: P1
- Type: unit
- Given: An ActionListResponse where the first action has recommendation_text longer than 100 characters
- When: build_morning_summary_card() is called
- Then: The bullet text for that item is truncated to ~100 characters with "..." suffix
- Data: ActionItem with recommendation_text of 150+ characters

### 18-3-morning-summary-teams-card-UNIT-009: Summary line handles zero counts for some categories
- Priority: P1
- Type: unit
- Given: An ActionListResponse with counts_by_category={"safety": 0, "oee": 3, "financial": 0}
- When: build_morning_summary_card() is called
- Then: Summary line reads "3 action items: 0 safety, 3 OEE misses, 0 financial"
- Data: ActionListResponse with total_count=3, all OEE category

### 18-3-morning-summary-teams-card-INT-001: _trigger_teams_notification sends summary card after pipeline success
- Priority: P0
- Type: integration
- Given: settings.teams_configured returns True, the action engine returns an ActionListResponse with 5 action items, and the TeamsWebhookClient is mocked
- When: _trigger_teams_notification(target_date=date(2026, 2, 10)) is called
- Then: get_teams_client().send_card() is called once with a dict containing the Adaptive Card payload built by build_morning_summary_card()
- Data: Mocked ActionListResponse with 5 items, mocked settings with teams_configured=True

### 18-3-morning-summary-teams-card-INT-002: run_morning_report calls _trigger_teams_notification after smart summary
- Priority: P0
- Type: integration
- Given: Pipeline returns SUCCESS, smart summary generation succeeds, teams_configured=True, action engine returns items
- When: run_morning_report(target_date=date(2026, 2, 10), generate_smart_summary=True) is called
- Then: _trigger_teams_notification is called after _trigger_smart_summary_generation, and the PipelineResult is returned correctly
- Data: Mocked pipeline, mocked smart summary service, mocked action engine, mocked teams client

### 18-3-morning-summary-teams-card-INT-003: _trigger_teams_notification queries action engine with correct date
- Priority: P1
- Type: integration
- Given: settings.teams_configured returns True
- When: _trigger_teams_notification(target_date=date(2026, 2, 10)) is called
- Then: get_action_engine().generate_action_list() is called with report_date=date(2026, 2, 10)
- Data: Mocked action engine returning valid ActionListResponse

### 18-3-morning-summary-teams-card-INT-004: _trigger_teams_notification uses app_base_url from settings for Open Report link
- Priority: P1
- Type: integration
- Given: settings.app_base_url="https://prod.example.com", settings.teams_configured=True, action engine returns items
- When: _trigger_teams_notification(target_date=date(2026, 2, 10)) is called
- Then: The card payload passed to send_card() contains Action.OpenUrl with url "https://prod.example.com/morning-report?date=2026-02-10"
- Data: Mocked settings, mocked action engine, mocked teams client


## AC2: Given there are no action items for the day, When the cron triggers, Then a card is posted "Morning Report -- {date}: All clear. No action items today." And the "Open Report" link is still included.

### 18-3-morning-summary-teams-card-UNIT-010: build_all_clear_card produces correct all-clear message
- Priority: P0
- Type: unit
- Given: report_date=2026-02-10 and base_url="https://app.example.com"
- When: build_all_clear_card(report_date, base_url) is called
- Then: The returned dict is a valid Adaptive Card with body containing a TextBlock with text "Morning Report -- 2026-02-10: All clear. No action items today." with weight "Bolder" and size "Medium"
- Data: report_date=date(2026, 2, 10), base_url string

### 18-3-morning-summary-teams-card-UNIT-011: All-clear card includes Open Report button
- Priority: P0
- Type: unit
- Given: report_date=2026-02-10 and base_url="https://app.example.com"
- When: build_all_clear_card(report_date, base_url) is called
- Then: The actions array contains one Action.OpenUrl with title "Open Report" and url "https://app.example.com/morning-report?date=2026-02-10"
- Data: report_date and base_url

### 18-3-morning-summary-teams-card-UNIT-012: All-clear card has valid Adaptive Card structure
- Priority: P1
- Type: unit
- Given: report_date=2026-02-10 and base_url="https://app.example.com"
- When: build_all_clear_card(report_date, base_url) is called
- Then: The returned dict contains "$schema", "type": "AdaptiveCard", "version": "1.4", a "body" array, and an "actions" array
- Data: Valid date and base_url

### 18-3-morning-summary-teams-card-INT-005: _trigger_teams_notification sends all-clear card when zero action items
- Priority: P0
- Type: integration
- Given: settings.teams_configured=True, action engine returns ActionListResponse with total_count=0 and empty actions list
- When: _trigger_teams_notification(target_date=date(2026, 2, 10)) is called
- Then: get_teams_client().send_card() is called with the all-clear card payload (not the summary card), containing "All clear. No action items today."
- Data: Mocked ActionListResponse with total_count=0, counts_by_category={"safety": 0, "oee": 0, "financial": 0}

### 18-3-morning-summary-teams-card-INT-006: run_morning_report posts all-clear card when pipeline succeeds with no action items
- Priority: P1
- Type: integration
- Given: Pipeline returns SUCCESS, action engine returns zero action items, teams_configured=True
- When: run_morning_report(target_date=date(2026, 2, 10)) is called
- Then: send_card() is called with the all-clear card payload, and PipelineResult with SUCCESS status is returned
- Data: Mocked pipeline, mocked action engine with empty results


## AC3: Given the Teams webhook fails (network error, invalid URL), When the notification is attempted, Then the failure is logged with error details And the morning report data is unaffected (fire-and-forget).

### 18-3-morning-summary-teams-card-UNIT-013: send_card handles httpx.TimeoutException gracefully
- Priority: P0
- Type: unit
- Given: A valid card payload and httpx.AsyncClient.post raises httpx.TimeoutException
- When: send_card(card_payload) is called
- Then: The method returns {"success": False, ...} without raising an exception, and the error is logged
- Data: Any valid Adaptive Card dict, mocked httpx raising TimeoutException

### 18-3-morning-summary-teams-card-UNIT-014: send_card handles httpx.ConnectError gracefully
- Priority: P0
- Type: unit
- Given: A valid card payload and httpx.AsyncClient.post raises httpx.ConnectError (e.g., invalid URL, DNS failure)
- When: send_card(card_payload) is called
- Then: The method returns {"success": False, ...} without raising, and the error is logged
- Data: Any valid Adaptive Card dict, mocked httpx raising ConnectError

### 18-3-morning-summary-teams-card-UNIT-015: send_card handles HTTP 4xx/5xx responses gracefully
- Priority: P0
- Type: unit
- Given: A valid card payload and the webhook returns HTTP 400 (Bad Request) or HTTP 500 (Server Error)
- When: send_card(card_payload) is called
- Then: The method returns {"success": False, "status_code": 400 or 500, ...} without raising
- Data: Mocked httpx response with status_code=400 or 500

### 18-3-morning-summary-teams-card-UNIT-016: send_card returns early when webhook not configured
- Priority: P1
- Type: unit
- Given: TeamsWebhookClient instantiated with empty webhook_url=""
- When: send_card(card_payload) is called
- Then: The method returns {"success": False, "message": contains "not configured"} without attempting an HTTP request
- Data: Empty webhook URL, any card payload

### 18-3-morning-summary-teams-card-INT-007: _trigger_teams_notification skips silently when teams_configured is False
- Priority: P0
- Type: integration
- Given: settings.teams_configured returns False (teams_webhook_url is empty)
- When: _trigger_teams_notification(target_date=date(2026, 2, 10)) is called
- Then: No call is made to get_action_engine() or send_card(), the function returns None without error
- Data: Mocked settings with teams_webhook_url=""

### 18-3-morning-summary-teams-card-INT-008: _trigger_teams_notification catches and logs send_card failure
- Priority: P0
- Type: integration
- Given: settings.teams_configured=True, action engine returns valid items, but send_card() returns {"success": False, "message": "Connection refused"}
- When: _trigger_teams_notification(target_date=date(2026, 2, 10)) is called
- Then: The failure is logged at ERROR level with error details, and the function returns None (does not raise)
- Data: Mocked action engine, mocked teams client returning failure result

### 18-3-morning-summary-teams-card-INT-009: _trigger_teams_notification catches exception from send_card if it raises
- Priority: P0
- Type: integration
- Given: settings.teams_configured=True, action engine returns valid items, but get_teams_client().send_card() raises an unexpected Exception
- When: _trigger_teams_notification(target_date=date(2026, 2, 10)) is called
- Then: The exception is caught, logged at ERROR level with "Pipeline result is not affected" message, and the function returns None
- Data: Mocked send_card raising RuntimeError("unexpected failure")

### 18-3-morning-summary-teams-card-INT-010: _trigger_teams_notification catches exception from generate_action_list
- Priority: P0
- Type: integration
- Given: settings.teams_configured=True, but get_action_engine().generate_action_list() raises an Exception
- When: _trigger_teams_notification(target_date=date(2026, 2, 10)) is called
- Then: The exception is caught, logged at ERROR level, and the function returns None without calling send_card()
- Data: Mocked action engine raising Exception("database error")

### 18-3-morning-summary-teams-card-INT-011: run_morning_report returns PipelineResult even when Teams notification fails
- Priority: P0
- Type: integration
- Given: Pipeline returns SUCCESS with valid PipelineResult, but _trigger_teams_notification raises an unhandled Exception (simulating catastrophic failure)
- When: run_morning_report(target_date=date(2026, 2, 10)) is called
- Then: The PipelineResult with SUCCESS status is returned to the caller, and no exception propagates
- Data: Mocked pipeline returning SUCCESS, mocked _trigger_teams_notification raising Exception

### 18-3-morning-summary-teams-card-INT-012: run_morning_report returns PipelineResult when PARTIAL status and notification fails
- Priority: P1
- Type: integration
- Given: Pipeline returns PARTIAL status, smart summary succeeds, but Teams notification fails
- When: run_morning_report(target_date=date(2026, 2, 10)) is called
- Then: PipelineResult with PARTIAL status is returned correctly
- Data: Mocked pipeline returning PARTIAL, mocked failing Teams notification


edge_cases:
  - Action items list has exactly 0 items (triggers all-clear card path)
  - Action items list has exactly 1 item (single bullet point, no truncation)
  - Action items list has exactly 3 items (all shown, no "more" indicator)
  - Action items list has more than 3 items (only top 3 shown in bullet points)
  - Action item recommendation_text exceeds 100 characters (truncation with "...")
  - counts_by_category has zero for all categories except one
  - counts_by_category keys may be missing (defensive access with .get())
  - target_date is None in run_morning_report (defaults to yesterday)
  - app_base_url contains trailing slash (URL construction should handle)
  - teams_webhook_url contains whitespace only (teams_configured should return False)
  - Date formatting uses ISO format (YYYY-MM-DD) in title and URL

error_scenarios:
  - httpx.TimeoutException during webhook POST
  - httpx.ConnectError (DNS failure, connection refused)
  - HTTP 400 Bad Request from webhook endpoint
  - HTTP 401 Unauthorized (expired or invalid webhook URL)
  - HTTP 500 Internal Server Error from Teams service
  - generate_action_list raises database connection error
  - generate_action_list raises unexpected exception
  - send_card raises unexpected RuntimeError
  - Webhook URL is malformed (not a valid URL)
  - Network completely unreachable

test_file_mapping:
  - 18-3-morning-summary-teams-card-UNIT-001 through UNIT-012: apps/api/tests/services/notifications/test_morning_summary_card.py
  - 18-3-morning-summary-teams-card-UNIT-013 through UNIT-016: apps/api/tests/services/notifications/test_morning_summary_card.py
  - 18-3-morning-summary-teams-card-INT-001 through INT-006: apps/api/tests/services/notifications/test_trigger_teams_notification.py
  - 18-3-morning-summary-teams-card-INT-007 through INT-012: apps/api/tests/services/notifications/test_trigger_teams_notification.py

TEST SPEC END
