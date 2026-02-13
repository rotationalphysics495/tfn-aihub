TEST SPEC START
story_id: 14-6-ai-summary-with-trend-context
generated: 2026-02-11

test_specifications:

## AC1: Given the smart summary is generated for a date When trend data is available for the plant Then the summary includes a line like: "Overall plant OEE 81.2%, down 3.1 points from last week"

### 14-6-ai-summary-with-trend-context-UNIT-001: fetch_trend_data returns WoW OEE change when 7-day history exists
- Priority: P0
- Type: unit
- Given: daily_summaries table contains OEE data for target_date (2026-02-10) with 3 assets averaging 81.2% OEE, and for target_date - 7 (2026-02-03) with 3 assets averaging 84.3% OEE
- When: fetch_trend_data(target_date=date(2026, 2, 10)) is called on ContextBuilder
- Then: returns {"plant_oee_current": 81.2, "plant_oee_previous_week": 84.3, "plant_oee_wow_change": -3.1}
- Data: Mock Supabase query for daily_summaries with report_date = 2026-02-10 returning [{"oee_percentage": 78.0}, {"oee_percentage": 82.6}, {"oee_percentage": 83.0}]; report_date = 2026-02-03 returning [{"oee_percentage": 84.0}, {"oee_percentage": 85.0}, {"oee_percentage": 83.9}]

### 14-6-ai-summary-with-trend-context-UNIT-002: SummaryContext trend_data field is Optional with None default
- Priority: P0
- Type: unit
- Given: SummaryContext is constructed with only existing required fields (target_date, daily_summaries)
- When: SummaryContext is instantiated without passing trend_data
- Then: context.trend_data is None, and context.has_data still returns True if daily_summaries is non-empty
- Data: Minimal SummaryContext with target_date=date(2026, 2, 10), daily_summaries=[{"oee_percentage": 80.0}]

### 14-6-ai-summary-with-trend-context-UNIT-003: build_context populates trend_data when historical data is available
- Priority: P0
- Type: unit
- Given: Supabase daily_summaries has data for both target_date and target_date - 7 days
- When: build_context(target_date=date(2026, 2, 10)) is called
- Then: the returned SummaryContext has trend_data populated with plant_oee_current, plant_oee_previous_week, and plant_oee_wow_change
- Data: Mock daily_summaries returning OEE records for both 2026-02-10 and 2026-02-03

### 14-6-ai-summary-with-trend-context-UNIT-004: format_trend_context renders WoW OEE comparison line
- Priority: P0
- Type: unit
- Given: trend_data = {"plant_oee_current": 81.2, "plant_oee_previous_week": 84.3, "plant_oee_wow_change": -3.1}
- When: format_trend_context(trend_data=trend_data) is called
- Then: output contains "Week-over-Week OEE: Current 81.2% vs Last Week 84.3% (change: -3.1 points)"
- Data: trend_data dict as specified

### 14-6-ai-summary-with-trend-context-UNIT-005: render_data_prompt includes TREND CONTEXT section when trend data provided
- Priority: P0
- Type: unit
- Given: render_data_prompt is called with valid trend_data kwarg
- When: render_data_prompt(target_date=..., safety_events=[], daily_summaries=[], action_items=[], trend_data={"plant_oee_current": 81.2, "plant_oee_previous_week": 84.3, "plant_oee_wow_change": -3.1})
- Then: the returned prompt string contains "TREND CONTEXT" section header AND the WoW OEE comparison text
- Data: Standard render_data_prompt args plus trend_data

### 14-6-ai-summary-with-trend-context-UNIT-006: _generate_with_llm passes trend_data from context to render_data_prompt
- Priority: P0
- Type: unit
- Given: SummaryContext has trend_data={"plant_oee_current": 81.2, "plant_oee_previous_week": 84.3, "plant_oee_wow_change": -3.1}
- When: _generate_with_llm(context) is called with a mocked LLM client
- Then: render_data_prompt is called with trend_data kwarg matching context.trend_data
- Data: Mock LLM returning a valid response string; patch render_data_prompt to capture call args

### 14-6-ai-summary-with-trend-context-INT-001: End-to-end summary generation includes WoW OEE comparison in LLM prompt
- Priority: P0
- Type: integration
- Given: Supabase returns 7-day history of daily_summaries with OEE data, and LLM is mocked to echo back received data
- When: generate_smart_summary(target_date=date(2026, 2, 10)) is called
- Then: the prompt sent to the LLM contains "Week-over-Week OEE" and "change:" text, and the generated summary_text is non-empty
- Data: Full mock chain: Supabase daily_summaries for target_date and target_date - 7; mock LLM returning summary text containing "down 3.1 points from last week"

### 14-6-ai-summary-with-trend-context-UNIT-007: format_trend_context handles positive WoW change correctly
- Priority: P1
- Type: unit
- Given: trend_data = {"plant_oee_current": 87.5, "plant_oee_previous_week": 84.3, "plant_oee_wow_change": 3.2}
- When: format_trend_context(trend_data=trend_data) is called
- Then: output contains "change: +3.2 points" (with plus sign for positive change)
- Data: Positive WoW change trend_data dict

### 14-6-ai-summary-with-trend-context-UNIT-008: fetch_trend_data computes correct plant-wide average across multiple assets
- Priority: P1
- Type: unit
- Given: daily_summaries for target_date has 5 assets with OEE values [72.0, 80.0, 85.0, 90.0, 78.0] (avg 81.0), and target_date - 7 has 5 assets with [75.0, 82.0, 88.0, 92.0, 80.0] (avg 83.4)
- When: fetch_trend_data(target_date) is called
- Then: returns plant_oee_current=81.0, plant_oee_previous_week=83.4, plant_oee_wow_change=-2.4
- Data: Mock Supabase returning 5 asset records for each date

### 14-6-ai-summary-with-trend-context-UNIT-009: SYSTEM_PROMPT_DEFAULT includes trend context instructions
- Priority: P1
- Type: unit
- Given: SYSTEM_PROMPT_DEFAULT is loaded (or get_system_prompt() called)
- When: the prompt text is inspected
- Then: it contains instructions to incorporate week-over-week trends, repeat offenders, and downtime drivers when available
- Data: None (static prompt inspection)


## AC2: Given an asset has been on the report for 3+ consecutive days When the smart summary is generated Then the summary mentions the pattern: "Grinder 5 has appeared on the report for 3 consecutive days -- consider escalating to maintenance planning"

### 14-6-ai-summary-with-trend-context-UNIT-010: fetch_repeat_offenders identifies asset below target for 3 consecutive days
- Priority: P0
- Type: unit
- Given: daily_summaries for trailing 7 days shows "Grinder 5" (asset-1) with OEE below target (85%) for the last 3 consecutive days ending on target_date
- When: fetch_repeat_offenders(target_date=date(2026, 2, 10)) is called
- Then: returns [{"asset_name": "Grinder 5", "consecutive_days": 3, "category": "oee"}]
- Data: Mock Supabase with 7 days of daily_summaries: asset-1 has OEE [86, 87, 85, 88, 78, 72, 75] for dates 2/4-2/10 (last 3 days below 85 target); assets dict mapping asset-1 to "Grinder 5"

### 14-6-ai-summary-with-trend-context-UNIT-011: fetch_repeat_offenders identifies asset below target for 4+ consecutive days
- Priority: P0
- Type: unit
- Given: daily_summaries shows "CAMA 2400" (asset-2) with OEE below target for 4 consecutive days ending on target_date
- When: fetch_repeat_offenders(target_date=date(2026, 2, 10)) is called
- Then: returns entry with {"asset_name": "CAMA 2400", "consecutive_days": 4, "category": "oee"}
- Data: Mock asset-2 below target for 4 of last 7 days (the trailing 4)

### 14-6-ai-summary-with-trend-context-UNIT-012: fetch_repeat_offenders excludes asset below target for only 2 consecutive days
- Priority: P0
- Type: unit
- Given: daily_summaries shows an asset with OEE below target for only 2 consecutive days ending on target_date
- When: fetch_repeat_offenders(target_date=date(2026, 2, 10)) is called
- Then: returns empty list (asset does not meet 3-day threshold)
- Data: Mock asset with OEE below target only on 2/9 and 2/10

### 14-6-ai-summary-with-trend-context-UNIT-013: fetch_repeat_offenders handles non-consecutive below-target days
- Priority: P1
- Type: unit
- Given: daily_summaries shows an asset below target on days 2/5, 2/6, 2/8, 2/9, 2/10 but NOT 2/7 (gap breaks consecutive streak to 3 ending on target_date)
- When: fetch_repeat_offenders(target_date=date(2026, 2, 10)) is called
- Then: returns entry with consecutive_days=3 (counts only 2/8, 2/9, 2/10 streak ending on target_date)
- Data: Mock daily_summaries with gap on 2/7

### 14-6-ai-summary-with-trend-context-UNIT-014: format_trend_context renders repeat offenders section
- Priority: P0
- Type: unit
- Given: repeat_offenders = [{"asset_name": "Grinder 5", "consecutive_days": 3, "category": "oee"}, {"asset_name": "CAMA 2400", "consecutive_days": 4, "category": "oee"}]
- When: format_trend_context(repeat_offenders=repeat_offenders) is called
- Then: output contains "Repeat Offenders (3+ consecutive days on report):" AND "Grinder 5: 3 consecutive days" AND "CAMA 2400: 4 consecutive days"
- Data: repeat_offenders list as specified

### 14-6-ai-summary-with-trend-context-UNIT-015: SummaryContext repeat_offenders field defaults to empty list
- Priority: P1
- Type: unit
- Given: SummaryContext is constructed without passing repeat_offenders
- When: SummaryContext is instantiated
- Then: context.repeat_offenders equals [] (empty list)
- Data: Minimal SummaryContext

### 14-6-ai-summary-with-trend-context-UNIT-016: build_context populates repeat_offenders when trailing data exists
- Priority: P0
- Type: unit
- Given: Supabase has 7 days of daily_summaries with an asset below OEE target for 3+ consecutive days
- When: build_context(target_date) is called
- Then: returned SummaryContext has repeat_offenders list containing at least one entry
- Data: Mock daily_summaries with appropriate trailing data

### 14-6-ai-summary-with-trend-context-UNIT-017: fetch_repeat_offenders returns multiple repeat offenders sorted by consecutive_days descending
- Priority: P2
- Type: unit
- Given: Two assets both qualify as repeat offenders with different consecutive day counts (3 and 5)
- When: fetch_repeat_offenders(target_date) is called
- Then: returns both assets in list, ordered by consecutive_days descending (5-day first)
- Data: Mock two assets with different streak lengths


## AC3: Given a downtime Pareto breakdown is available When the smart summary is generated Then the summary includes the top downtime driver: "Top downtime driver yesterday: Mechanical (187 min across 4 assets)"

### 14-6-ai-summary-with-trend-context-UNIT-018: fetch_top_downtime_drivers aggregates by reason_code correctly
- Priority: P0
- Type: unit
- Given: downtime_events table has 6 rows for target_date: [Mechanical/asset-1/60min, Mechanical/asset-2/45min, Mechanical/asset-3/40min, Mechanical/asset-4/42min, Changeover/asset-1/50min, Changeover/asset-5/45min]
- When: fetch_top_downtime_drivers(target_date=date(2026, 2, 10)) is called
- Then: returns [{"reason_code": "Mechanical", "total_minutes": 187, "asset_count": 4}, {"reason_code": "Changeover", "total_minutes": 95, "asset_count": 2}]
- Data: Mock Supabase downtime_events with 6 rows as described, grouped and aggregated

### 14-6-ai-summary-with-trend-context-UNIT-019: fetch_top_downtime_drivers returns top 3 only when more than 3 reason codes exist
- Priority: P1
- Type: unit
- Given: downtime_events table has rows with 5 distinct reason_codes for target_date
- When: fetch_top_downtime_drivers(target_date) is called
- Then: returns exactly 3 entries, sorted by total_minutes descending
- Data: Mock 5 reason codes with varying totals

### 14-6-ai-summary-with-trend-context-UNIT-020: fetch_top_downtime_drivers counts distinct assets per reason_code
- Priority: P1
- Type: unit
- Given: downtime_events has Mechanical reason with multiple events for the SAME asset (asset-1: 30min, asset-1: 25min) and one event for asset-2 (40min)
- When: fetch_top_downtime_drivers(target_date) is called
- Then: Mechanical entry has total_minutes=95 and asset_count=2 (not 3 — distinct assets only)
- Data: Mock with duplicate asset_id within same reason_code

### 14-6-ai-summary-with-trend-context-UNIT-021: format_trend_context renders top downtime drivers section
- Priority: P0
- Type: unit
- Given: top_downtime_drivers = [{"reason_code": "Mechanical", "total_minutes": 187, "asset_count": 4}, {"reason_code": "Changeover", "total_minutes": 95, "asset_count": 6}]
- When: format_trend_context(top_downtime_drivers=top_downtime_drivers) is called
- Then: output contains "Top Downtime Drivers (yesterday):" AND "Mechanical: 187 min across 4 assets" AND "Changeover: 95 min across 6 assets"
- Data: top_downtime_drivers list as specified

### 14-6-ai-summary-with-trend-context-UNIT-022: SummaryContext top_downtime_drivers field defaults to empty list
- Priority: P1
- Type: unit
- Given: SummaryContext is constructed without passing top_downtime_drivers
- When: SummaryContext is instantiated
- Then: context.top_downtime_drivers equals [] (empty list)
- Data: Minimal SummaryContext

### 14-6-ai-summary-with-trend-context-UNIT-023: build_context populates top_downtime_drivers when downtime_events data exists
- Priority: P0
- Type: unit
- Given: Supabase downtime_events table has rows for target_date
- When: build_context(target_date) is called
- Then: returned SummaryContext has top_downtime_drivers list with aggregated entries
- Data: Mock downtime_events with multiple reason codes

### 14-6-ai-summary-with-trend-context-UNIT-024: fetch_top_downtime_drivers returns empty list when no downtime events for target_date
- Priority: P1
- Type: unit
- Given: downtime_events table exists but has no rows for target_date
- When: fetch_top_downtime_drivers(target_date) is called
- Then: returns empty list []
- Data: Mock Supabase returning empty data for query


## AC4: Given trend data is not available (e.g., first day of operation) When the smart summary is generated Then the summary gracefully omits trend commentary without error and the rest of the summary is unaffected

### 14-6-ai-summary-with-trend-context-UNIT-025: fetch_trend_data returns None when no historical data exists
- Priority: P0
- Type: unit
- Given: daily_summaries table has no data for target_date - 7 (first day of operation)
- When: fetch_trend_data(target_date) is called
- Then: returns None
- Data: Mock Supabase returning empty data for the previous week query

### 14-6-ai-summary-with-trend-context-UNIT-026: fetch_trend_data returns None on Supabase exception
- Priority: P0
- Type: unit
- Given: Supabase client raises an exception (e.g., connection error) during query
- When: fetch_trend_data(target_date) is called
- Then: returns None (does not raise), and error is logged
- Data: Mock Supabase to raise Exception("connection error")

### 14-6-ai-summary-with-trend-context-UNIT-027: fetch_repeat_offenders returns empty list on Supabase exception
- Priority: P0
- Type: unit
- Given: Supabase client raises an exception during repeat offenders query
- When: fetch_repeat_offenders(target_date) is called
- Then: returns [] (does not raise), and error is logged
- Data: Mock Supabase to raise Exception

### 14-6-ai-summary-with-trend-context-UNIT-028: fetch_top_downtime_drivers returns empty list when table does not exist
- Priority: P0
- Type: unit
- Given: downtime_events table does not exist (Story 14.1 migration not yet run), Supabase raises a table-not-found error
- When: fetch_top_downtime_drivers(target_date) is called
- Then: returns [] (does not raise), and error is logged
- Data: Mock Supabase to raise exception simulating missing table

### 14-6-ai-summary-with-trend-context-UNIT-029: build_context succeeds with all trend fetches failing
- Priority: P0
- Type: unit
- Given: fetch_trend_data, fetch_repeat_offenders, and fetch_top_downtime_drivers all raise exceptions internally
- When: build_context(target_date) is called
- Then: returns a valid SummaryContext with trend_data=None, repeat_offenders=[], top_downtime_drivers=[], and core fields (daily_summaries, safety_events, action_items) are populated normally
- Data: Mock all trend fetches to raise; mock core fetches to return valid data

### 14-6-ai-summary-with-trend-context-UNIT-030: format_trend_context with all None/empty inputs returns graceful message
- Priority: P0
- Type: unit
- Given: trend_data=None, repeat_offenders=[], top_downtime_drivers=[]
- When: format_trend_context(trend_data=None, repeat_offenders=[], top_downtime_drivers=[]) is called
- Then: returns "No trend data available for this period." or equivalent benign string (not empty, not error)
- Data: All-empty inputs

### 14-6-ai-summary-with-trend-context-UNIT-031: render_data_prompt works without trend kwargs (backward compatible)
- Priority: P0
- Type: unit
- Given: render_data_prompt is called with only the existing positional/keyword args (no trend_data, no repeat_offenders, no top_downtime_drivers)
- When: render_data_prompt(target_date=..., safety_events=[], daily_summaries=[], action_items=[]) is called
- Then: returns a valid prompt string without errors; TREND CONTEXT section contains graceful "no data" text
- Data: Only pre-14.6 arguments

### 14-6-ai-summary-with-trend-context-INT-002: Full summary generation succeeds on first day of operation with no trend data
- Priority: P0
- Type: integration
- Given: Supabase has daily_summaries for target_date only (no prior history), no downtime_events data
- When: generate_smart_summary(target_date) is called with mocked LLM
- Then: summary is generated successfully, is_fallback=False, summary_text does not contain trend commentary, and no exceptions are raised
- Data: Mock only target_date data; LLM returns summary text without trend references

### 14-6-ai-summary-with-trend-context-UNIT-032: format_trend_context with partial data renders only available sections
- Priority: P1
- Type: unit
- Given: trend_data is populated but repeat_offenders=[] and top_downtime_drivers=[]
- When: format_trend_context(trend_data={"plant_oee_current": 81.2, "plant_oee_previous_week": 84.3, "plant_oee_wow_change": -3.1}, repeat_offenders=[], top_downtime_drivers=[])
- Then: output contains "Week-over-Week OEE" but does NOT contain "Repeat Offenders" or "Top Downtime Drivers" sections
- Data: Only trend_data populated

### 14-6-ai-summary-with-trend-context-UNIT-033: build_context isolates trend fetch failure from repeat offender fetch
- Priority: P1
- Type: unit
- Given: fetch_trend_data raises an exception but fetch_repeat_offenders and fetch_top_downtime_drivers succeed
- When: build_context(target_date) is called
- Then: SummaryContext has trend_data=None but repeat_offenders and top_downtime_drivers are populated correctly
- Data: Mock trend_data to fail; mock repeat_offenders and downtime_drivers to succeed


## AC5: Given the fallback summary is triggered (LLM unavailable) When trend context data is available Then the fallback template also includes trend lines (week-over-week OEE change, repeat offenders, top downtime driver)

### 14-6-ai-summary-with-trend-context-UNIT-034: Fallback summary includes WoW OEE comparison when trend_data is present
- Priority: P0
- Type: unit
- Given: SummaryContext has trend_data={"plant_oee_current": 81.2, "plant_oee_previous_week": 84.3, "plant_oee_wow_change": -3.1} and valid daily_summaries
- When: generate_fallback_summary(context) is called
- Then: the returned summary_text contains "Overall plant OEE 81.2%" and "down 3.1 points from last week"
- Data: SummaryContext with trend_data and basic daily_summaries

### 14-6-ai-summary-with-trend-context-UNIT-035: Fallback summary includes positive WoW OEE with "up" direction
- Priority: P1
- Type: unit
- Given: SummaryContext has trend_data with plant_oee_wow_change=2.5 (positive)
- When: generate_fallback_summary(context) is called
- Then: the returned summary_text contains "up 2.5 points from last week"
- Data: SummaryContext with positive wow_change

### 14-6-ai-summary-with-trend-context-UNIT-036: Fallback summary includes Recurring Issues section when repeat_offenders exist
- Priority: P0
- Type: unit
- Given: SummaryContext has repeat_offenders=[{"asset_name": "Grinder 5", "consecutive_days": 3, "category": "oee"}]
- When: generate_fallback_summary(context) is called
- Then: the returned summary_text contains "**Recurring Issues**" section header AND "Grinder 5" AND "3 consecutive days" AND "consider escalating to maintenance planning"
- Data: SummaryContext with one repeat offender

### 14-6-ai-summary-with-trend-context-UNIT-037: Fallback summary includes Downtime Drivers section when top_downtime_drivers exist
- Priority: P0
- Type: unit
- Given: SummaryContext has top_downtime_drivers=[{"reason_code": "Mechanical", "total_minutes": 187, "asset_count": 4}]
- When: generate_fallback_summary(context) is called
- Then: the returned summary_text contains "**Downtime Drivers**" section header AND "Mechanical: 187 min across 4 assets"
- Data: SummaryContext with one downtime driver

### 14-6-ai-summary-with-trend-context-UNIT-038: Fallback summary includes all three trend sections simultaneously
- Priority: P0
- Type: unit
- Given: SummaryContext has trend_data, repeat_offenders (2 entries), and top_downtime_drivers (3 entries) all populated
- When: generate_fallback_summary(context) is called
- Then: summary_text contains WoW OEE line, **Recurring Issues** section with both offenders, and **Downtime Drivers** section with all 3 drivers; existing sections (**Safety**, **Productivity**) are also present and unaffected
- Data: Fully populated SummaryContext with all trend fields and existing fields

### 14-6-ai-summary-with-trend-context-UNIT-039: Fallback summary without trend data is unchanged from pre-14.6 behavior
- Priority: P0
- Type: unit
- Given: SummaryContext has trend_data=None, repeat_offenders=[], top_downtime_drivers=[] (no trend data), but has valid daily_summaries and safety_events
- When: generate_fallback_summary(context) is called
- Then: summary_text does NOT contain "Recurring Issues", "Downtime Drivers", or "points from last week"; existing sections are present and correctly formatted; output matches pre-14.6 format
- Data: SummaryContext with only pre-14.6 fields populated

### 14-6-ai-summary-with-trend-context-UNIT-040: Fallback summary with partial trend data includes only available sections
- Priority: P1
- Type: unit
- Given: SummaryContext has trend_data populated but repeat_offenders=[] and top_downtime_drivers=[]
- When: generate_fallback_summary(context) is called
- Then: summary_text contains WoW OEE line but does NOT contain "Recurring Issues" or "Downtime Drivers" sections
- Data: SummaryContext with only trend_data populated

### 14-6-ai-summary-with-trend-context-UNIT-041: Fallback summary is_fallback flag is True and model_used is "fallback_template"
- Priority: P1
- Type: unit
- Given: SummaryContext with all trend fields populated
- When: generate_fallback_summary(context) is called
- Then: returned SmartSummary has is_fallback=True and model_used="fallback_template" (trend data does not change these metadata fields)
- Data: SummaryContext with trend data


edge_cases:
  - fetch_trend_data when target_date has data but target_date - 7 returns empty (partial data) — should return None since comparison is incomplete
  - fetch_trend_data when only 1 asset has OEE on target_date but 10 assets on target_date - 7 — average should still be computed per-date independently
  - fetch_repeat_offenders when an asset is below target on days 1-3 and 5-7 (gap on day 4) — should report consecutive_days=3 for the trailing streak ending on target_date
  - fetch_repeat_offenders when asset has OEE exactly equal to target_oee — it should NOT count as below target (strictly less than)
  - fetch_top_downtime_drivers when all events have the same reason_code — should return single entry with total across all assets
  - fetch_top_downtime_drivers when duration_minutes varies widely (e.g., 1 min vs 500 min) — sort by total_minutes not event count
  - format_trend_context when plant_oee_wow_change is exactly 0.0 — should display "change: +0.0 points" or handle zero-change case gracefully
  - Fallback summary section ordering — Recurring Issues and Downtime Drivers appear in correct positions relative to existing Safety, Productivity, Financial Impact sections
  - Very large trend data (e.g., 50+ assets in daily_summaries) — ensure averaging is correct and no performance issues

error_scenarios:
  - Supabase connection timeout during fetch_trend_data — returns None, logged, does not block summary
  - Supabase connection timeout during fetch_repeat_offenders — returns [], logged, does not block summary
  - downtime_events table does not exist (14.1 not deployed) — fetch_top_downtime_drivers returns [], logged, does not block summary
  - Malformed data in daily_summaries (e.g., oee_percentage is null) — fetch_trend_data handles gracefully, skips null values or returns None
  - fetch_trend_data, fetch_repeat_offenders, and fetch_top_downtime_drivers all fail simultaneously — build_context still returns valid SummaryContext
  - render_data_prompt called with custom DATA_TEMPLATE_DEFAULT env override missing {trend_context} placeholder — should not crash (catch KeyError)
  - LLM receives trend context in prompt but returns summary without mentioning trends — system should not fail or retry (LLM output is best-effort)

test_file_mapping:
  - 14-6-ai-summary-with-trend-context-UNIT-*: apps/api/tests/test_smart_summary.py
  - 14-6-ai-summary-with-trend-context-INT-*: apps/api/tests/test_smart_summary.py
  - 14-6-ai-summary-with-trend-context-E2E-*: apps/api/tests/test_smart_summary.py

TEST SPEC END
