TEST SPEC START
story_id: 18-2-teams-webhook-configuration
generated: 2026-02-12

test_specifications:

## AC1: Given an admin navigates to settings, When the Teams integration section is visible, Then a field for "Teams Webhook URL" is shown And the admin can paste a webhook URL and save it.

### 18-2-teams-webhook-configuration-UNIT-001: Settings class has teams_webhook_url field with empty default
- Priority: P0
- Type: unit
- Given: A fresh Settings instance with no TEAMS_WEBHOOK_URL environment variable set
- When: The Settings object is instantiated with default values
- Then: `settings.teams_webhook_url` equals `""` (empty string)
- Data: No environment override needed; verify default field value

### 18-2-teams-webhook-configuration-UNIT-002: Settings teams_configured returns False when teams_webhook_url is empty
- Priority: P0
- Type: unit
- Given: A Settings instance with `teams_webhook_url=""` (empty string)
- When: The `teams_configured` property is accessed
- Then: It returns `False`
- Data: Explicit `Settings(teams_webhook_url="")` construction with required env vars patched (SUPABASE_URL, SUPABASE_KEY)

### 18-2-teams-webhook-configuration-UNIT-003: Settings teams_configured returns True when teams_webhook_url is set
- Priority: P0
- Type: unit
- Given: A Settings instance with `teams_webhook_url="https://outlook.office.com/webhook/abc123"`
- When: The `teams_configured` property is accessed
- Then: It returns `True`
- Data: Explicit `Settings(teams_webhook_url="https://outlook.office.com/webhook/abc123")` construction with required env vars patched

### 18-2-teams-webhook-configuration-UNIT-004: Settings reads TEAMS_WEBHOOK_URL from environment variable
- Priority: P0
- Type: unit
- Given: The `TEAMS_WEBHOOK_URL` environment variable is set to `"https://outlook.office.com/webhook/test-url"`
- When: A Settings instance is created (pydantic-settings reads from env)
- Then: `settings.teams_webhook_url` equals `"https://outlook.office.com/webhook/test-url"`
- Data: Use `patch.dict(os.environ, {"TEAMS_WEBHOOK_URL": "https://outlook.office.com/webhook/test-url"})` before constructing Settings

### 18-2-teams-webhook-configuration-UNIT-005: .env.example contains TEAMS_WEBHOOK_URL entry
- Priority: P1
- Type: unit
- Given: The `.env.example` file exists at `apps/api/.env.example`
- When: The file contents are inspected
- Then: The file contains a `TEAMS_WEBHOOK_URL=` entry (with empty value or documentation comment)
- Data: File read assertion

## AC2: Given a webhook URL is configured, When the admin clicks "Test", Then a test message is posted to the configured Teams channel And the result (success/failure) is displayed to the admin.

### 18-2-teams-webhook-configuration-UNIT-006: TeamsWebhookClient.is_configured returns True when webhook URL is set
- Priority: P0
- Type: unit
- Given: A TeamsWebhookClient initialized with `webhook_url="https://outlook.office.com/webhook/abc123"`
- When: The `is_configured` property is accessed
- Then: It returns `True`
- Data: Direct client instantiation with explicit webhook_url parameter

### 18-2-teams-webhook-configuration-UNIT-007: TeamsWebhookClient.is_configured returns False when webhook URL is empty
- Priority: P0
- Type: unit
- Given: A TeamsWebhookClient initialized with `webhook_url=""` (and settings also has empty URL)
- When: The `is_configured` property is accessed
- Then: It returns `False`
- Data: Patch `get_settings` to return Settings with empty teams_webhook_url

### 18-2-teams-webhook-configuration-UNIT-008: TeamsWebhookClient.send_card posts correct Adaptive Card envelope to webhook URL
- Priority: P0
- Type: unit
- Given: A TeamsWebhookClient with a configured webhook URL and a mock httpx.AsyncClient that returns HTTP 200
- When: `send_card(card_payload)` is called with a sample Adaptive Card dict
- Then: The mocked httpx client POSTs to the webhook URL with JSON body containing `{"type": "message", "attachments": [{"contentType": "application/vnd.microsoft.card.adaptive", "contentUrl": null, "content": <card_payload>}]}`
- And: The method returns `{"success": True, "message": "Message posted to Teams", "status_code": 200}`
- Data: card_payload = `{"$schema": "http://adaptivecards.io/schemas/adaptive-card.json", "type": "AdaptiveCard", "version": "1.4", "body": [{"type": "TextBlock", "text": "Test"}]}`

### 18-2-teams-webhook-configuration-UNIT-009: TeamsWebhookClient.send_card handles httpx.TimeoutException
- Priority: P0
- Type: unit
- Given: A TeamsWebhookClient with a configured webhook URL and a mock httpx.AsyncClient that raises `httpx.TimeoutException`
- When: `send_card(card_payload)` is called
- Then: The method returns `{"success": False, "message": "Request timed out", "status_code": None}`
- And: No unhandled exception is raised
- Data: Mock httpx.AsyncClient.post with `side_effect=httpx.TimeoutException("Timeout")`

### 18-2-teams-webhook-configuration-UNIT-010: TeamsWebhookClient.send_card handles httpx.HTTPStatusError (4xx)
- Priority: P0
- Type: unit
- Given: A TeamsWebhookClient with a configured webhook URL and a mock httpx response returning HTTP 400 that raises `httpx.HTTPStatusError`
- When: `send_card(card_payload)` is called
- Then: The method returns `{"success": False, "message": "HTTP 400: <error text>", "status_code": 400}`
- Data: Mock httpx response with status_code=400, text="Bad Request"

### 18-2-teams-webhook-configuration-UNIT-011: TeamsWebhookClient.send_card handles httpx.HTTPStatusError (5xx)
- Priority: P0
- Type: unit
- Given: A TeamsWebhookClient with a configured webhook URL and a mock httpx response returning HTTP 502 that raises `httpx.HTTPStatusError`
- When: `send_card(card_payload)` is called
- Then: The method returns `{"success": False, "message": "HTTP 502: <error text>", "status_code": 502}`
- Data: Mock httpx response with status_code=502, text="Bad Gateway"

### 18-2-teams-webhook-configuration-UNIT-012: TeamsWebhookClient.send_card handles httpx.ConnectError
- Priority: P0
- Type: unit
- Given: A TeamsWebhookClient with a configured webhook URL and a mock httpx.AsyncClient that raises `httpx.ConnectError`
- When: `send_card(card_payload)` is called
- Then: The method returns `{"success": False, "message": "Connection failed: <error details>", "status_code": None}`
- And: No unhandled exception is raised
- Data: Mock httpx.AsyncClient.post with `side_effect=httpx.ConnectError("Connection refused")`

### 18-2-teams-webhook-configuration-UNIT-013: TeamsWebhookClient.send_card returns early when not configured
- Priority: P0
- Type: unit
- Given: A TeamsWebhookClient with no webhook URL configured (empty string)
- When: `send_card(card_payload)` is called
- Then: The method returns `{"success": False, "message": "Teams webhook URL not configured", "status_code": None}`
- And: No HTTP request is attempted (httpx is never called)
- Data: Verify mock httpx.AsyncClient is NOT called

### 18-2-teams-webhook-configuration-UNIT-014: TeamsWebhookClient.send_test_message sends correct Adaptive Card structure
- Priority: P0
- Type: unit
- Given: A TeamsWebhookClient with a configured webhook URL and a mock httpx.AsyncClient that returns HTTP 200
- When: `send_test_message()` is called
- Then: The card payload posted contains `"$schema": "http://adaptivecards.io/schemas/adaptive-card.json"`, `"type": "AdaptiveCard"`, `"version": "1.4"`
- And: The card body contains a TextBlock with text "TFN AI Hub - Connection Test" (weight: Bolder, size: Medium)
- And: The card body contains a TextBlock with text "Teams webhook integration is working correctly." (wrap: True)
- Data: Capture the `json=` argument from the mocked httpx.AsyncClient.post call and validate structure

### 18-2-teams-webhook-configuration-UNIT-015: TeamsWebhookClient.send_card logs success on HTTP 200
- Priority: P2
- Type: unit
- Given: A TeamsWebhookClient with a configured webhook URL and a mock httpx.AsyncClient that returns HTTP 200
- When: `send_card(card_payload)` is called
- Then: A log message at INFO level is emitted containing "succeeded" and the status code
- Data: Use `caplog` or mock the logger to capture log output

### 18-2-teams-webhook-configuration-UNIT-016: TeamsWebhookClient.send_card logs failure on error
- Priority: P2
- Type: unit
- Given: A TeamsWebhookClient with a configured webhook URL and a mock httpx.AsyncClient that raises TimeoutException
- When: `send_card(card_payload)` is called
- Then: A log message at ERROR level is emitted containing "timed out"
- Data: Use `caplog` or mock the logger to capture log output

### 18-2-teams-webhook-configuration-INT-001: POST /api/v1/notifications/teams/test returns success when webhook configured
- Priority: P0
- Type: integration
- Given: An authenticated user (mock_verify_jwt) and TEAMS_WEBHOOK_URL is configured
- When: POST request is sent to `/api/v1/notifications/teams/test` with Authorization header
- Then: Response status code is 200
- And: Response JSON contains `{"success": true, "message": "Message posted to Teams", "status_code": 200}`
- Data: Mock TeamsWebhookClient or httpx.AsyncClient to return success; use `client` and `mock_verify_jwt` fixtures from conftest.py

### 18-2-teams-webhook-configuration-INT-002: POST /api/v1/notifications/teams/test returns 400 when webhook not configured
- Priority: P0
- Type: integration
- Given: An authenticated user (mock_verify_jwt) and TEAMS_WEBHOOK_URL is empty/not set
- When: POST request is sent to `/api/v1/notifications/teams/test` with Authorization header
- Then: Response status code is 400
- And: Response JSON `detail` contains "not configured" or similar message about missing webhook URL
- Data: Ensure settings return empty teams_webhook_url; use `client` and `mock_verify_jwt` fixtures

### 18-2-teams-webhook-configuration-INT-003: POST /api/v1/notifications/teams/test returns 401 when unauthenticated
- Priority: P0
- Type: integration
- Given: No authentication token is provided (no Authorization header)
- When: POST request is sent to `/api/v1/notifications/teams/test`
- Then: Response status code is 401
- Data: Use `client` fixture only, no `mock_verify_jwt`

### 18-2-teams-webhook-configuration-INT-004: POST /api/v1/notifications/teams/test returns 401 with expired token
- Priority: P1
- Type: integration
- Given: An expired JWT token is provided (mock_verify_jwt_expired)
- When: POST request is sent to `/api/v1/notifications/teams/test` with Authorization header containing expired token
- Then: Response status code is 401
- And: Response JSON `detail` contains "expired"
- Data: Use `client` and `mock_verify_jwt_expired` fixtures from conftest.py

### 18-2-teams-webhook-configuration-INT-005: POST /api/v1/notifications/teams/test returns failure result when Teams webhook rejects
- Priority: P1
- Type: integration
- Given: An authenticated user and TEAMS_WEBHOOK_URL is configured, but the Teams endpoint returns HTTP 403
- When: POST request is sent to `/api/v1/notifications/teams/test`
- Then: Response status code is 200 (endpoint itself succeeds)
- And: Response JSON contains `{"success": false, "status_code": 403}` and message includes "HTTP 403"
- Data: Mock httpx.AsyncClient to raise HTTPStatusError with 403 response; use `client` and `mock_verify_jwt` fixtures

### 18-2-teams-webhook-configuration-INT-006: POST /api/v1/notifications/teams/test returns failure result on timeout
- Priority: P1
- Type: integration
- Given: An authenticated user and TEAMS_WEBHOOK_URL is configured, but the Teams endpoint times out
- When: POST request is sent to `/api/v1/notifications/teams/test`
- Then: Response status code is 200 (endpoint itself succeeds)
- And: Response JSON contains `{"success": false, "message": "Request timed out", "status_code": null}`
- Data: Mock httpx.AsyncClient to raise TimeoutException; use `client` and `mock_verify_jwt` fixtures

### 18-2-teams-webhook-configuration-INT-007: Notifications router is registered in main.py at correct prefix
- Priority: P0
- Type: integration
- Given: The FastAPI application is loaded
- When: The registered routes are inspected
- Then: A route exists at `/api/v1/notifications/teams/test` with POST method
- Data: Use `client` fixture, verify 404 is NOT returned for the endpoint path (or inspect app.routes)

## AC3: Given no webhook URL is configured, When the morning cron runs, Then no Teams notification is sent And the morning report generation continues normally.

### 18-2-teams-webhook-configuration-UNIT-017: TeamsWebhookClient.send_card does not make HTTP request when not configured
- Priority: P0
- Type: unit
- Given: A TeamsWebhookClient with empty/unset webhook URL
- When: `send_card({"type": "AdaptiveCard", "body": [...]})` is called
- Then: No HTTP POST request is attempted (httpx.AsyncClient is never instantiated or called)
- And: Returns `{"success": False, "message": "Teams webhook URL not configured", "status_code": None}`
- Data: Spy on httpx.AsyncClient to assert it was NOT called

### 18-2-teams-webhook-configuration-UNIT-018: TeamsWebhookClient.is_configured returns False when URL is None
- Priority: P1
- Type: unit
- Given: A TeamsWebhookClient initialized with `webhook_url=None` and settings also has empty teams_webhook_url
- When: The `is_configured` property is accessed
- Then: It returns `False`
- Data: Patch `get_settings` to return Settings with `teams_webhook_url=""`; construct client with no explicit URL

### 18-2-teams-webhook-configuration-UNIT-019: Settings teams_configured returns False when teams_webhook_url is whitespace-only
- Priority: P1
- Type: unit
- Given: A Settings instance with `teams_webhook_url="   "` (whitespace only)
- When: The `teams_configured` property is accessed
- Then: It returns `False` (since `bool("   ")` is `True`, this tests if the implementation accounts for whitespace — if current design uses `bool()` this will return True, documenting expected behavior)
- Data: Note: This is a boundary test. If `bool()` is used, whitespace-only strings are truthy. The spec documents this behavior; implementation may choose to `.strip()` or not.

### 18-2-teams-webhook-configuration-UNIT-020: TeamsWebhookClient constructed from settings when no explicit URL provided
- Priority: P1
- Type: unit
- Given: Settings has `teams_webhook_url="https://outlook.office.com/webhook/from-settings"`
- When: A TeamsWebhookClient is instantiated with no `webhook_url` parameter
- Then: `client.webhook_url` equals `"https://outlook.office.com/webhook/from-settings"` (read from settings)
- Data: Patch `get_settings` to return appropriate Settings mock

### 18-2-teams-webhook-configuration-UNIT-021: TeamsWebhookClient explicit webhook_url overrides settings
- Priority: P1
- Type: unit
- Given: Settings has `teams_webhook_url="https://outlook.office.com/webhook/from-settings"`
- When: A TeamsWebhookClient is instantiated with `webhook_url="https://outlook.office.com/webhook/override"`
- Then: `client.webhook_url` equals `"https://outlook.office.com/webhook/override"` (explicit overrides settings)
- Data: Patch `get_settings` and verify explicit URL takes precedence

edge_cases:
  - Webhook URL contains trailing whitespace — should be handled gracefully (either stripped or used as-is)
  - Webhook URL is a non-HTTPS URL (http://) — should still attempt POST (no URL validation in this story)
  - Webhook URL is a malformed URL (e.g., "not-a-url") — httpx.ConnectError should be caught and returned gracefully
  - Very long error response text from Teams (>200 chars) — message should be truncated per design (`:200` slice)
  - Concurrent send_card calls — each should create its own httpx.AsyncClient context (no shared state issues)
  - Teams returns HTTP 200 but unexpected body (not "1") — should still be treated as success (status code based)
  - Empty card_payload dict passed to send_card — should still wrap in envelope and POST (Teams may reject)

error_scenarios:
  - httpx.TimeoutException during webhook POST — returns graceful failure dict, no crash
  - httpx.HTTPStatusError with 4xx (400, 401, 403, 404) — returns failure with status code
  - httpx.HTTPStatusError with 5xx (500, 502, 503) — returns failure with status code
  - httpx.ConnectError (DNS failure, connection refused) — returns failure with connection error message
  - No TEAMS_WEBHOOK_URL env var set — settings default to empty string, teams_configured is False, send_card returns early
  - Authentication failure on /teams/test endpoint — returns 401 before any webhook logic runs
  - Expired JWT token on /teams/test endpoint — returns 401 with expiry message

test_file_mapping:
  - 18-2-teams-webhook-configuration-UNIT-001 to UNIT-005: apps/api/tests/test_teams_config.py
  - 18-2-teams-webhook-configuration-UNIT-006 to UNIT-021: apps/api/tests/test_teams_webhook_client.py
  - 18-2-teams-webhook-configuration-INT-001 to INT-007: apps/api/tests/test_notifications_api.py

TEST SPEC END
