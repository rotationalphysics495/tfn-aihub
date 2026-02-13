TEST SPEC START
story_id: 16-6-ai-summary-with-action-plan-context
generated: 2026-02-12

test_specifications:

## AC1: Active action plan mention in summary — Given the smart summary is generated for a date, when an asset in the action items has an active action plan (status = 'open' or 'in_progress'), then the summary mentions it contextually.

### 16-6-ai-summary-with-action-plan-context-UNIT-001: System prompt includes instruction for active plan contextual mentions
- Priority: P0
- Type: unit
- Given: The SYSTEM_PROMPT_DEFAULT is loaded from prompts.py
- When: The system prompt text is inspected
- Then: It contains an instruction telling the LLM to reference active action plans when discussing assets that have them (e.g., mentioning plan title, corrective action, and due date alongside the asset's issues)
- Data: SYSTEM_PROMPT_DEFAULT string constant

### 16-6-ai-summary-with-action-plan-context-INT-001: End-to-end summary generation includes action plan mention for active plan asset
- Priority: P0
- Type: integration
- Given: A SummaryContext with daily_summaries for "Grinder 5" (below target OEE), action_items referencing asset_id "asset-1", and action_plans containing one plan with status "in_progress", title "Bearing replacement", due_date "2026-02-14", and asset_id "asset-1"
- When: generate_smart_summary() is called with a mocked LLM that echoes back action plan references from the prompt
- Then: The rendered data prompt passed to the LLM includes the action plan data for "Grinder 5" with title "Bearing replacement", status "in_progress", and due date "2026-02-14" in the === ACTION PLAN STATUS === section
- Data: Mock LLM client, sample SummaryContext with one active action plan for a below-target asset

### 16-6-ai-summary-with-action-plan-context-UNIT-002: System prompt includes instruction for both open and in_progress statuses
- Priority: P1
- Type: unit
- Given: The SYSTEM_PROMPT_DEFAULT is loaded
- When: The instruction text for action plan mentions is examined
- Then: The instruction does not limit to a specific status — it applies to any asset with an active action plan (covering both 'open' and 'in_progress')
- Data: SYSTEM_PROMPT_DEFAULT string constant

## AC2: Recently verified plan correlation — Given an action plan was recently verified (completed within last 7 days), when the summary is generated and the asset's metric improved, then the summary may note the correlation.

### 16-6-ai-summary-with-action-plan-context-UNIT-003: System prompt includes instruction for verified plan correlation
- Priority: P0
- Type: unit
- Given: The SYSTEM_PROMPT_DEFAULT is loaded from prompts.py
- When: The system prompt text is inspected
- Then: It contains an instruction telling the LLM to correlate recently verified action plans with asset metric improvements (e.g., noting OEE improvement since corrective action was completed)
- Data: SYSTEM_PROMPT_DEFAULT string constant

### 16-6-ai-summary-with-action-plan-context-UNIT-004: format_action_plans renders recently verified plans with corrective action and verified date
- Priority: P0
- Type: unit
- Given: A recently_verified_plans list containing one plan with title "Bearing replacement", asset_name "Grinder 5", corrective_action "Replaced worn bearings on main shaft", verified_at "2026-02-08"
- When: format_action_plans(action_plans=[], recently_verified_plans=recently_verified_plans) is called
- Then: The returned string includes a "Recently completed action plans (last 7 days)" header and a line containing the asset name "Grinder 5", title "Bearing replacement", corrective action "Replaced worn bearings on main shaft", and verified date "2026-02-08"
- Data: One recently verified plan dict with all fields populated

### 16-6-ai-summary-with-action-plan-context-UNIT-005: fetch_active_action_plans queries verified plans within 7-day lookback window
- Priority: P0
- Type: unit
- Given: A ContextBuilder with a mocked Supabase client, target_date = 2026-02-10, and asset_ids = ["asset-1"]
- When: fetch_active_action_plans(target_date, asset_ids) is called
- Then: The Supabase client queries the action_plans table with status = "verified" and verified_at >= "2026-02-03" (target_date - 7 days) and asset_id IN ["asset-1"]
- Data: Mock Supabase client configured to return one verified plan

### 16-6-ai-summary-with-action-plan-context-UNIT-006: fetch_active_action_plans excludes verified plans older than 7 days
- Priority: P1
- Type: unit
- Given: A ContextBuilder with a mocked Supabase client, target_date = 2026-02-10, and a verified plan with verified_at = "2026-02-01" (9 days ago)
- When: fetch_active_action_plans(target_date, asset_ids) is called
- Then: The verified plans query uses .gte("verified_at", "2026-02-03"), so the plan from 2026-02-01 is excluded by the query filter, and the returned verified_plans list does not contain it
- Data: Mock Supabase client configured with .gte() filter verification

## AC3: Context builder fetches action plans — Given the ContextBuilder assembles data for summary generation, when action plans exist for assets appearing in today's action items, then the active action plans are included in the SummaryContext object passed to the LLM.

### 16-6-ai-summary-with-action-plan-context-UNIT-007: SummaryContext model includes action_plans field with empty list default
- Priority: P0
- Type: unit
- Given: No action_plans parameter is passed to SummaryContext constructor
- When: A SummaryContext is created with only required fields (target_date)
- Then: context.action_plans is an empty list ([]) and context.recently_verified_plans is an empty list ([])
- Data: Minimal SummaryContext with target_date only

### 16-6-ai-summary-with-action-plan-context-UNIT-008: SummaryContext model stores action plans when provided
- Priority: P0
- Type: unit
- Given: An action_plans list with 2 plans and a recently_verified_plans list with 1 plan
- When: A SummaryContext is created with these lists
- Then: context.action_plans contains the 2 active plans and context.recently_verified_plans contains the 1 verified plan
- Data: Two active plan dicts, one verified plan dict

### 16-6-ai-summary-with-action-plan-context-UNIT-009: fetch_active_action_plans returns active plans matching asset_ids
- Priority: P0
- Type: unit
- Given: A ContextBuilder with a mocked Supabase client, asset_ids = ["asset-1", "asset-2"], and the action_plans table contains 2 plans: one with status "open" for asset-1, one with status "in_progress" for asset-2
- When: fetch_active_action_plans(target_date, asset_ids) is called
- Then: The returned tuple contains (active_plans, verified_plans) where active_plans has 2 plans matching the given asset_ids and with statuses "open" and "in_progress"
- Data: Mock Supabase response with 2 active plan records

### 16-6-ai-summary-with-action-plan-context-UNIT-010: fetch_active_action_plans filters by status IN (open, in_progress) for active plans
- Priority: P0
- Type: unit
- Given: A ContextBuilder with a mocked Supabase client and asset_ids = ["asset-1"]
- When: fetch_active_action_plans(target_date, asset_ids) is called
- Then: The Supabase query chain includes .in_("status", ["open", "in_progress"]) for the active plans query
- Data: Mock Supabase client with call verification on .in_() method

### 16-6-ai-summary-with-action-plan-context-UNIT-011: fetch_active_action_plans returns empty tuple when asset_ids list is empty
- Priority: P1
- Type: unit
- Given: A ContextBuilder with a mocked Supabase client and asset_ids = []
- When: fetch_active_action_plans(target_date, asset_ids=[]) is called
- Then: The method returns ([], []) without making any Supabase queries (early return guard)
- Data: Empty asset_ids list, verify no Supabase client calls

### 16-6-ai-summary-with-action-plan-context-UNIT-012: build_context extracts asset_ids from action_items and passes to fetch_active_action_plans
- Priority: P0
- Type: unit
- Given: A ContextBuilder with mocked fetch methods, action_items containing items for asset_ids ["asset-1", "asset-2", "asset-1"] (with duplicates)
- When: build_context(target_date) is called
- Then: fetch_active_action_plans is called with deduplicated asset_ids (set of ["asset-1", "asset-2"]) and the resulting plans are stored in context.action_plans and context.recently_verified_plans
- Data: Mock action_items with duplicate asset_ids, mock fetch_active_action_plans returning sample plans

### 16-6-ai-summary-with-action-plan-context-UNIT-013: build_context enriches action plans with asset names
- Priority: P1
- Type: unit
- Given: A ContextBuilder with mocked fetch methods, fetch_active_action_plans returns plans with asset_id "asset-1", and assets dict contains {"asset-1": {"id": "asset-1", "name": "Grinder 5"}}
- When: build_context(target_date) is called
- Then: The stored action_plans in SummaryContext include "asset_name": "Grinder 5" added by _enrich_with_asset_names()
- Data: Mock assets lookup, mock action plans without asset_name

### 16-6-ai-summary-with-action-plan-context-UNIT-014: fetch_active_action_plans selects correct columns for active plans
- Priority: P2
- Type: unit
- Given: A ContextBuilder with a mocked Supabase client
- When: fetch_active_action_plans(target_date, asset_ids) is called
- Then: The active plans query selects id, title, asset_id, category, status, priority, due_date, corrective_action, and root_cause fields
- Data: Mock Supabase client with .select() call verification

## AC4: Prompt template updated — Given the prompt template is rendered with data, when action plan context is available, then a new === ACTION PLAN STATUS === section is included in the data prompt with plan titles, statuses, due dates, and associated asset names.

### 16-6-ai-summary-with-action-plan-context-UNIT-015: format_action_plans renders active plans with title, asset, category, status, due date
- Priority: P0
- Type: unit
- Given: An action_plans list with one plan: title "Bearing replacement", asset_name "Grinder 5", category "corrective", status "in_progress", due_date "2026-02-14"
- When: format_action_plans(action_plans=action_plans, recently_verified_plans=[]) is called
- Then: The returned string contains "Active action plans" header and a line with "Grinder 5", "Bearing replacement", "corrective", "in_progress", and "2026-02-14"
- Data: One active plan dict with all fields populated

### 16-6-ai-summary-with-action-plan-context-UNIT-016: format_action_plans renders both active and verified plans together
- Priority: P0
- Type: unit
- Given: action_plans with 1 active plan and recently_verified_plans with 1 verified plan
- When: format_action_plans(action_plans, recently_verified_plans) is called
- Then: The returned string contains both an "Active action plans" section and a "Recently completed action plans (last 7 days)" section
- Data: One active plan dict, one verified plan dict

### 16-6-ai-summary-with-action-plan-context-UNIT-017: format_action_plans returns no-plans message when both lists empty
- Priority: P0
- Type: unit
- Given: action_plans = [] and recently_verified_plans = []
- When: format_action_plans(action_plans=[], recently_verified_plans=[]) is called
- Then: The returned string equals "No active action plans for assets on today's report."
- Data: Empty lists

### 16-6-ai-summary-with-action-plan-context-UNIT-018: render_data_prompt includes ACTION PLAN STATUS section when plans exist
- Priority: P0
- Type: unit
- Given: render_data_prompt is called with action_plans containing one active plan and recently_verified_plans containing one verified plan, plus standard daily_summaries, safety_events, action_items, and target_date
- When: render_data_prompt(..., action_plans=action_plans, recently_verified_plans=recently_verified_plans) is called
- Then: The returned prompt string contains "=== ACTION PLAN STATUS ===" section with the formatted action plan data
- Data: Sample action plans, verified plans, and minimal context data for all required parameters

### 16-6-ai-summary-with-action-plan-context-UNIT-019: render_data_prompt omits action plan section content when no plans exist
- Priority: P0
- Type: unit
- Given: render_data_prompt is called with action_plans=None and recently_verified_plans=None (or empty lists)
- When: render_data_prompt(..., action_plans=None, recently_verified_plans=None) is called
- Then: The returned prompt string contains the "=== ACTION PLAN STATUS ===" header but with the "No active action plans for assets on today's report." message
- Data: Minimal context data, no action plans

### 16-6-ai-summary-with-action-plan-context-UNIT-020: DATA_TEMPLATE_DEFAULT contains action_plan_data placeholder
- Priority: P0
- Type: unit
- Given: DATA_TEMPLATE_DEFAULT is imported from prompts.py
- When: The template string is inspected
- Then: It contains "=== ACTION PLAN STATUS ===" header and "{action_plan_data}" placeholder
- Data: DATA_TEMPLATE_DEFAULT string constant

### 16-6-ai-summary-with-action-plan-context-UNIT-021: render_data_prompt backward compatible — works without action plan params
- Priority: P1
- Type: unit
- Given: render_data_prompt is called with only the pre-existing parameters (target_date, safety_events, daily_summaries, action_items) and no action plan parameters
- When: render_data_prompt(target_date=..., safety_events=[], daily_summaries=[], action_items=[]) is called
- Then: The function returns successfully without errors, and the prompt contains the no-plans fallback text in the ACTION PLAN STATUS section
- Data: Minimal required parameters only

### 16-6-ai-summary-with-action-plan-context-UNIT-022: render_data_prompt handles custom template missing action_plan_data placeholder
- Priority: P1
- Type: unit
- Given: A custom data template (via env var override) that does not contain the {action_plan_data} placeholder, and action_plans with one active plan
- When: render_data_prompt is called with the custom template and action plan data
- Then: The function does not raise a KeyError; instead it appends the action plan section to the end of the rendered prompt (following the existing backward-compat pattern for {trend_context})
- Data: Custom template string without {action_plan_data}, sample action plans

### 16-6-ai-summary-with-action-plan-context-UNIT-023: format_action_plans handles missing fields gracefully with defaults
- Priority: P1
- Type: unit
- Given: An action_plans list with one plan that has missing fields (no asset_name, no title, no due_date, no category)
- When: format_action_plans(action_plans=action_plans, recently_verified_plans=[]) is called
- Then: The returned string uses default values ("Unknown" for asset_name, "Untitled" for title, "no date" for due_date, empty for category) without raising exceptions
- Data: Sparse plan dict with only id and status fields

### 16-6-ai-summary-with-action-plan-context-UNIT-024: format_action_plans renders multiple active plans as separate lines
- Priority: P1
- Type: unit
- Given: An action_plans list with 3 active plans for different assets
- When: format_action_plans(action_plans=action_plans, recently_verified_plans=[]) is called
- Then: The returned string contains 3 separate bullet lines, each with the corresponding asset name and plan title
- Data: Three active plan dicts for assets "Grinder 5", "CAMA 2400", "Wrapper 1"

## AC5: Fallback summary includes action plan badges — Given the LLM is unavailable and a fallback summary is generated, when assets have active action plans, then the fallback summary includes a brief action plan note under the relevant asset entry.

### 16-6-ai-summary-with-action-plan-context-UNIT-025: Fallback summary appends action plan note to below-target asset bullet
- Priority: P0
- Type: unit
- Given: A SummaryContext with daily_summaries for "Grinder 5" (OEE 72.5%, below 85% target) and action_plans containing one plan with title "Bearing replacement", due_date "2026-02-14", asset_id "asset-1"
- When: SmartSummaryService.generate_fallback_summary(context) is called
- Then: The returned summary_text contains a productivity bullet for "Grinder 5" that includes the action plan note "Action plan: Bearing replacement (due 2026-02-14)" appended to the bullet
- Data: SummaryContext with one below-target asset and one matching action plan

### 16-6-ai-summary-with-action-plan-context-UNIT-026: Fallback summary does not append plan note for assets without action plans
- Priority: P0
- Type: unit
- Given: A SummaryContext with daily_summaries for "Grinder 5" (below target) and "CAMA 2400" (below target), action_plans containing one plan only for "Grinder 5" (asset_id "asset-1")
- When: SmartSummaryService.generate_fallback_summary(context) is called
- Then: The "Grinder 5" bullet includes the action plan note, but the "CAMA 2400" bullet does NOT include any action plan note
- Data: SummaryContext with two below-target assets, one with action plan, one without

### 16-6-ai-summary-with-action-plan-context-UNIT-027: Fallback summary handles empty action_plans list
- Priority: P0
- Type: unit
- Given: A SummaryContext with daily_summaries for below-target assets and action_plans = [] (empty list)
- When: SmartSummaryService.generate_fallback_summary(context) is called
- Then: The summary generates normally with productivity bullets but no action plan notes appended to any bullet; no errors raised
- Data: SummaryContext with below-target assets and empty action_plans

### 16-6-ai-summary-with-action-plan-context-UNIT-028: Fallback summary uses first plan when multiple plans exist for same asset
- Priority: P2
- Type: unit
- Given: A SummaryContext with action_plans containing 2 plans for the same asset_id "asset-1" (plan A: "Bearing replacement", plan B: "Lubrication schedule")
- When: SmartSummaryService.generate_fallback_summary(context) is called
- Then: The productivity bullet for "Grinder 5" includes the action plan note for the first plan in the list (plan A), not both
- Data: SummaryContext with one below-target asset and two matching action plans

### 16-6-ai-summary-with-action-plan-context-UNIT-029: Fallback summary action plan note includes due date or TBD fallback
- Priority: P1
- Type: unit
- Given: A SummaryContext with one action plan that has no due_date field (or due_date is None)
- When: SmartSummaryService.generate_fallback_summary(context) is called
- Then: The action plan note uses "TBD" as the due date fallback (e.g., "Action plan: Bearing replacement (due TBD)")
- Data: Action plan dict with due_date=None or missing

## AC6: No action plan data graceful handling — Given no action plans exist or the action_plans table query fails, when the summary is generated, then the summary generates normally without action plan references and no errors are raised.

### 16-6-ai-summary-with-action-plan-context-UNIT-030: fetch_active_action_plans returns empty lists on Supabase exception
- Priority: P0
- Type: unit
- Given: A ContextBuilder with a mocked Supabase client that raises an Exception when querying the action_plans table
- When: fetch_active_action_plans(target_date, asset_ids) is called
- Then: The method returns ([], []) without raising an exception, and the error is logged via logger.error()
- Data: Mock Supabase client configured to raise Exception("relation 'action_plans' does not exist")

### 16-6-ai-summary-with-action-plan-context-UNIT-031: build_context continues normally when fetch_active_action_plans fails
- Priority: P0
- Type: unit
- Given: A ContextBuilder where fetch_active_action_plans raises an exception
- When: build_context(target_date) is called
- Then: The SummaryContext is returned successfully with action_plans = [] and recently_verified_plans = [], and all other context fields (daily_summaries, safety_events, etc.) are populated normally
- Data: Mock ContextBuilder with failing fetch_active_action_plans but working other fetch methods

### 16-6-ai-summary-with-action-plan-context-UNIT-032: render_data_prompt produces valid output with None action plan parameters
- Priority: P0
- Type: unit
- Given: render_data_prompt is called with action_plans=None and recently_verified_plans=None
- When: The prompt is rendered
- Then: The prompt includes the ACTION PLAN STATUS section with the "No active action plans" fallback message, and no error is raised
- Data: None values for action plan parameters, valid data for all other parameters

### 16-6-ai-summary-with-action-plan-context-INT-002: End-to-end summary generation succeeds with no action plans
- Priority: P0
- Type: integration
- Given: A full SummaryContext with daily_summaries, safety_events, and action_items, but action_plans = [] and recently_verified_plans = []
- When: generate_smart_summary() is called (with mocked LLM)
- Then: The summary is generated successfully without any action plan references, the data prompt contains the "No active action plans" message, and no errors are raised
- Data: Full SummaryContext without action plan data, mock LLM client

### 16-6-ai-summary-with-action-plan-context-INT-003: End-to-end summary generation succeeds when action_plans table does not exist
- Priority: P0
- Type: integration
- Given: A ContextBuilder where the action_plans table does not exist (Supabase query raises "relation does not exist" error) and all other tables are functional
- When: The full generate_smart_summary() pipeline is executed
- Then: The summary is generated successfully using all other available data, with action_plans and recently_verified_plans defaulting to empty lists, and no errors propagate
- Data: Mock Supabase client with action_plans table failing, other tables working

### 16-6-ai-summary-with-action-plan-context-UNIT-033: SummaryContext has_data property unaffected by action plan fields
- Priority: P2
- Type: unit
- Given: A SummaryContext with empty daily_summaries, empty safety_events, empty action_items, but non-empty action_plans
- When: context.has_data is checked
- Then: has_data returns False (action_plans alone do not constitute "meaningful data" for the summary — matching existing behavior where only core fields count)
- Data: SummaryContext with only action_plans populated

## End-to-end integration (cross-AC)

### 16-6-ai-summary-with-action-plan-context-INT-004: Full pipeline with active and verified plans produces complete summary
- Priority: P0
- Type: integration
- Given: A full SummaryContext with daily_summaries (3 assets, 2 below target), safety_events (1 unresolved), action_items (2 items), action_plans with 2 active plans (one "open" for asset-1, one "in_progress" for asset-2), and recently_verified_plans with 1 plan (verified 3 days ago for asset-3)
- When: generate_smart_summary() is called with a mocked LLM
- Then: The rendered data prompt includes all standard sections plus the ACTION PLAN STATUS section containing both active plans and the recently verified plan with correct formatting; the LLM receives the complete context
- Data: Comprehensive SummaryContext with all fields populated, mock LLM

### 16-6-ai-summary-with-action-plan-context-INT-005: Fallback path with action plans produces complete summary
- Priority: P0
- Type: integration
- Given: A full SummaryContext with below-target assets and action_plans, and the LLM is unavailable (raises exception)
- When: generate_smart_summary() falls back to generate_fallback_summary()
- Then: The fallback summary includes productivity bullets with action plan notes for matching assets, and the summary is returned with is_fallback=True and model_used="fallback_template"
- Data: SummaryContext with action plans, LLM configured to fail

### 16-6-ai-summary-with-action-plan-context-UNIT-034: _generate_with_llm passes action plan context to render_data_prompt
- Priority: P0
- Type: unit
- Given: A SmartSummaryService with a mocked render_data_prompt function and a SummaryContext containing action_plans and recently_verified_plans
- When: _generate_with_llm(context) is called
- Then: render_data_prompt is called with action_plans=context.action_plans and recently_verified_plans=context.recently_verified_plans
- Data: Mock render_data_prompt, SummaryContext with action plan data

edge_cases:
  - Empty asset_ids extracted from action_items (all action_items lack asset_id field): fetch_active_action_plans should receive empty list and return ([], []) without querying Supabase
  - Action plan with None/missing due_date: format_action_plans should use "no date" default; fallback summary should use "TBD"
  - Action plan with None/missing title: format_action_plans should use "Untitled" default
  - Action plan with None/missing asset_name (enrichment failed): format_action_plans should use "Unknown" default
  - Action plan with None/missing corrective_action (for verified plans): format_action_plans should render empty corrective action gracefully
  - Multiple action plans for the same asset: format_action_plans should list all; fallback summary should use first one only
  - Action items with duplicate asset_ids: build_context should deduplicate before passing to fetch_active_action_plans
  - All assets at or above target OEE but have action plans: fallback summary productivity section may be empty, action plan notes do not appear (no below-target bullets to append to)
  - Custom data template env var without {action_plan_data} placeholder: backward-compat fallback appends section

error_scenarios:
  - Supabase action_plans table does not exist (migration not run): fetch returns ([], []) with logged error
  - Supabase connection error during action plan fetch: fetch returns ([], []) with logged error
  - Supabase returns null/None data instead of empty list: handled by `response.data or []` pattern
  - fetch_active_action_plans raises unexpected exception in build_context: isolated try/except catches it, logs error, defaults to empty lists
  - .in_("asset_id", []) call with empty list potentially causing SQL error: guarded by early return in fetch method
  - format_action_plans receives None instead of list: handled by `or []` pattern in render_data_prompt

test_file_mapping:
  - 16-6-ai-summary-with-action-plan-context-UNIT-*: apps/api/tests/test_smart_summary_action_plans.py
  - 16-6-ai-summary-with-action-plan-context-INT-*: apps/api/tests/test_smart_summary_action_plans.py
  - 16-6-ai-summary-with-action-plan-context-E2E-*: apps/api/tests/test_smart_summary_action_plans.py

TEST SPEC END
