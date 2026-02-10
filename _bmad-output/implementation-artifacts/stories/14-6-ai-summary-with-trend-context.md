# Story 14.6: AI Summary with Trend Context

Status: ready-for-dev

## Story

As a Plant Manager,
I want the smart summary to include week-over-week comparison and trend commentary,
so that the AI narrative provides historical context alongside today's data.

## Acceptance Criteria

1. **Given** the smart summary is generated for a date **When** trend data is available for the plant **Then** the summary includes a line like: "Overall plant OEE 81.2%, down 3.1 points from last week"

2. **Given** an asset has been on the report for 3+ consecutive days **When** the smart summary is generated **Then** the summary mentions the pattern: "Grinder 5 has appeared on the report for 3 consecutive days -- consider escalating to maintenance planning"

3. **Given** a downtime Pareto breakdown is available **When** the smart summary is generated **Then** the summary includes the top downtime driver: "Top downtime driver yesterday: Mechanical (187 min across 4 assets)"

4. **Given** trend data is not available (e.g., first day of operation) **When** the smart summary is generated **Then** the summary gracefully omits trend commentary without error and the rest of the summary is unaffected

5. **Given** the fallback summary is triggered (LLM unavailable) **When** trend context data is available **Then** the fallback template also includes trend lines (week-over-week OEE change, repeat offenders, top downtime driver)

## Tasks / Subtasks

- [ ] Task 1: Extend `SummaryContext` with trend and Pareto fields (AC: #1, #2, #3)
  - [ ] 1.1 Add `trend_data` field to `SummaryContext` in `context_builder.py` -- a dict containing `plant_oee_current`, `plant_oee_previous_week`, `plant_oee_wow_change`
  - [ ] 1.2 Add `repeat_offenders` field to `SummaryContext` -- a list of dicts `{ asset_name, consecutive_days, category }`
  - [ ] 1.3 Add `top_downtime_drivers` field to `SummaryContext` -- a list of dicts `{ reason_code, total_minutes, asset_count }`
  - [ ] 1.4 All new fields must be `Optional` with sensible defaults so existing code is unaffected if data is absent

- [ ] Task 2: Implement trend data fetching in `ContextBuilder` (AC: #1, #2, #3, #4)
  - [ ] 2.1 Add `fetch_trend_data()` method: query `daily_summaries` for T-7 through T-1, compute plant-wide average OEE for both the target date and 7 days prior, return `plant_oee_wow_change`
  - [ ] 2.2 Add `fetch_repeat_offenders()` method: query `daily_summaries` for trailing 7 days, identify assets that appear on the action list for 3+ consecutive days by checking which assets had OEE below target consecutively
  - [ ] 2.3 Add `fetch_top_downtime_drivers()` method: query `downtime_events` table for the target date, aggregate by `reason_code` with `SUM(duration_minutes)` and `COUNT(DISTINCT asset_id)`, return top 3 sorted descending
  - [ ] 2.4 Integrate all three fetch methods into `build_context()` with try/except so failures do not block summary generation (AC: #4)

- [ ] Task 3: Update LLM prompt template with trend context (AC: #1, #2, #3)
  - [ ] 3.1 Add `=== TREND CONTEXT ===` section to `DATA_TEMPLATE_DEFAULT` in `prompts.py`
  - [ ] 3.2 Create `format_trend_context()` function that renders: week-over-week OEE change, repeat offenders list, top downtime drivers
  - [ ] 3.3 Update `render_data_prompt()` signature and body to accept and format trend context data
  - [ ] 3.4 Update system prompt to instruct LLM to incorporate trend narrative when available

- [ ] Task 4: Update `_generate_with_llm` to pass trend data (AC: #1, #2, #3)
  - [ ] 4.1 Update the call to `render_data_prompt()` in `smart_summary.py` to pass new trend context fields from the `SummaryContext`

- [ ] Task 5: Update fallback summary template with trend lines (AC: #5)
  - [ ] 5.1 In `generate_fallback_summary()`, add week-over-week OEE comparison line after the opening paragraph
  - [ ] 5.2 Add repeat offender callouts in a new `**Recurring Issues**` section
  - [ ] 5.3 Add top downtime driver line in a new `**Downtime Drivers**` section
  - [ ] 5.4 Guard all trend lines with `if context.trend_data` / `if context.repeat_offenders` / `if context.top_downtime_drivers` so missing data is gracefully skipped

- [ ] Task 6: Provide trend aggregates from ActionEngine for summary (AC: #1, #2)
  - [ ] 6.1 Add `get_trend_aggregates()` method to `ActionEngine` in `action_engine.py` that returns plant-level week-over-week OEE change by querying trailing 7 days of `daily_summaries`
  - [ ] 6.2 This method is an optional data source -- `ContextBuilder.fetch_trend_data()` can call it or query Supabase directly (prefer direct Supabase query in `ContextBuilder` to avoid circular coupling)

- [ ] Task 7: Tests (AC: #1-#5)
  - [ ] 7.1 Unit test: `test_context_builder_trend_data` -- verify `build_context()` populates trend fields when 7-day data exists
  - [ ] 7.2 Unit test: `test_context_builder_no_trend_data` -- verify graceful degradation when no historical data exists
  - [ ] 7.3 Unit test: `test_format_trend_context` -- verify prompt formatting for all three trend categories
  - [ ] 7.4 Unit test: `test_fallback_summary_with_trends` -- verify fallback includes trend lines when data present
  - [ ] 7.5 Unit test: `test_fallback_summary_without_trends` -- verify fallback works unchanged when trend data absent
  - [ ] 7.6 Integration test: `test_smart_summary_includes_trend_narrative` -- verify end-to-end that generated summary text contains week-over-week comparison when data is available

## Dev Notes

### Architecture & Patterns

- **Service layer pattern**: All changes follow the existing singleton service pattern (`get_context_builder()`, `get_smart_summary_service()`). Do NOT create new service classes -- extend the existing `ContextBuilder` and `SmartSummaryService`.
- **Supabase client**: Reuse the existing `self._get_client()` pattern in `ContextBuilder`. Do NOT create new Supabase client instances.
- **Caching**: Trend data queries span 7 days and are not latency-sensitive. Use the existing 15min TTL "Daily" cache tier if caching is needed. The `SummaryContext` is already cached via the `smart_summaries` table upsert pattern -- no additional caching layer is required for trend data.
- **Error isolation**: Every new `fetch_*` method MUST wrap its body in `try/except` and return empty/default values on failure, matching the pattern in `fetch_daily_summaries()`, `fetch_safety_events()`, etc. Trend data is supplementary -- its absence must never block summary generation.

### Key Source Files

| File | Action | Notes |
|------|--------|-------|
| `apps/api/app/services/ai/context_builder.py` | **Modify** | Add trend fields to `SummaryContext`, add `fetch_trend_data()`, `fetch_repeat_offenders()`, `fetch_top_downtime_drivers()`, update `build_context()` |
| `apps/api/app/services/ai/prompts.py` | **Modify** | Add `format_trend_context()`, update `DATA_TEMPLATE_DEFAULT`, update `render_data_prompt()` signature |
| `apps/api/app/services/ai/smart_summary.py` | **Modify** | Update `_generate_with_llm()` to pass trend data to prompt, update `generate_fallback_summary()` with trend sections |
| `apps/api/app/services/action_engine.py` | **Modify (optional)** | Add `get_trend_aggregates()` if needed as helper, but prefer doing queries directly in `ContextBuilder` |

### Database Dependencies

- **`daily_summaries` table**: Already exists. Trend queries use `asset_id`, `report_date`, `oee_percentage` columns. No schema changes needed.
- **`downtime_events` table**: Created in Story 14.1. Must exist before this story runs. Queries use `reason_code`, `duration_minutes`, `asset_id`, `event_date` columns. If `downtime_events` does not exist (Story 14.1 not yet implemented), the `fetch_top_downtime_drivers()` method must gracefully return an empty list.
- **`assets` table**: Already exists. Used for asset name enrichment via existing `fetch_assets()`.

### SummaryContext Field Additions

```python
# In context_builder.py, add to SummaryContext:
trend_data: Optional[Dict[str, Any]] = Field(
    default=None,
    description="Plant-level week-over-week trend data"
)
# Expected shape: {
#   "plant_oee_current": 81.2,
#   "plant_oee_previous_week": 84.3,
#   "plant_oee_wow_change": -3.1
# }

repeat_offenders: List[Dict[str, Any]] = Field(
    default_factory=list,
    description="Assets appearing on report 3+ consecutive days"
)
# Expected shape: [
#   {"asset_name": "Grinder 5", "consecutive_days": 3, "category": "oee"},
#   ...
# ]

top_downtime_drivers: List[Dict[str, Any]] = Field(
    default_factory=list,
    description="Top downtime reason codes aggregated across plant"
)
# Expected shape: [
#   {"reason_code": "Mechanical", "total_minutes": 187, "asset_count": 4},
#   ...
# ]
```

### Prompt Template Addition

```python
# Add to DATA_TEMPLATE_DEFAULT after the ACTION ENGINE section:
"""
=== TREND CONTEXT ===
{trend_context}
"""

# The format_trend_context() function should produce output like:
"""
Week-over-Week OEE: Current 81.2% vs Last Week 84.3% (change: -3.1 points)

Repeat Offenders (3+ consecutive days on report):
- Grinder 5: 3 consecutive days (OEE below target)
- CAMA 2400: 4 consecutive days (OEE below target)

Top Downtime Drivers (yesterday):
- Mechanical: 187 min across 4 assets
- Changeover: 95 min across 6 assets
- Material Shortage: 42 min across 2 assets
"""
```

### Fallback Summary Enhancement

The fallback summary in `generate_fallback_summary()` currently has sections: opening paragraph, Safety, Productivity, Financial Impact. Add trend lines as follows:

1. **After the opening paragraph** (after `lines.append("")` at ~line 286): Insert week-over-week OEE comparison if `context.trend_data` exists
2. **New "Recurring Issues" section** (before Productivity): List repeat offenders if `context.repeat_offenders` is non-empty
3. **New "Downtime Drivers" section** (after Productivity, before Financial Impact): List top downtime drivers if `context.top_downtime_drivers` is non-empty

### Anti-Patterns to Avoid

- **Do NOT create a separate trend service class** -- add methods directly to `ContextBuilder`
- **Do NOT add new API endpoints** -- this story only enhances the existing smart summary generation pipeline
- **Do NOT modify the `SmartSummary` Pydantic model** -- the trend context is consumed during generation only, not stored separately
- **Do NOT query `downtime_events` without checking table existence** -- wrap in try/except to handle the case where Story 14.1 migrations have not run yet
- **Do NOT modify `ActionItem` or `ActionListResponse` schemas** -- trend data for summaries comes from direct Supabase queries in `ContextBuilder`, not from the action engine response schema
- **Do NOT change the `render_data_prompt` return type** -- it still returns a `str`, just with additional content

### Testing Standards

- Use `pytest` with `pytest-asyncio` for async tests
- Mock Supabase client using existing patterns from `apps/api/tests/`
- Test files go in `apps/api/tests/services/ai/` directory
- Follow the existing test naming convention: `test_<module>_<scenario>.py`
- Minimum: one test per AC, plus edge case tests for missing data

### Cross-Story Dependencies

| Story | Dependency Type | Impact |
|-------|----------------|--------|
| 14.1 (Downtime Events Data Model) | **Data dependency** | `downtime_events` table must exist for AC #3. Graceful degradation required if missing. |
| 14.2 (Trend Data API) | **Conceptual overlap** | Story 14.2 adds `trend_data` to the action items API response. This story (14.6) adds trend data to the *summary* context independently via `ContextBuilder`. They share similar queries but serve different consumers. Reuse query logic if 14.2 is implemented first. |
| 14.3 (Downtime Pareto API) | **Conceptual overlap** | Story 14.3 creates a Pareto API endpoint. This story queries `downtime_events` directly in `ContextBuilder` rather than calling that API, to avoid adding an HTTP dependency to the summary generation path. |
| 3.5 (Smart Summary Generator) | **Extends** | This story directly extends the smart summary system created in 3.5. All modifications must preserve existing behavior. |

### Project Structure Notes

- All modified files are within `apps/api/app/services/ai/` -- the established AI services directory
- No new files need to be created -- all changes are modifications to existing files
- Test files follow `apps/api/tests/services/ai/test_*.py` pattern
- No frontend changes required for this story

### References

- [Source: _bmad-output/planning-artifacts/epic-14.md#Story 14.6]
- [Source: apps/api/app/services/ai/smart_summary.py] - SmartSummaryService with generate_smart_summary() and generate_fallback_summary()
- [Source: apps/api/app/services/ai/context_builder.py] - ContextBuilder with SummaryContext model and build_context()
- [Source: apps/api/app/services/ai/prompts.py] - Prompt templates: SYSTEM_PROMPT_DEFAULT, DATA_TEMPLATE_DEFAULT, render_data_prompt()
- [Source: apps/api/app/services/action_engine.py] - ActionEngine with generate_action_list()
- [Source: apps/api/app/schemas/action.py] - ActionItem, ActionListResponse schemas
- [Source: apps/api/app/schemas/summary.py] - SmartSummaryResponse schema
- [Source: docs/architecture-api.md] - FastAPI backend architecture, caching tiers, service patterns
- [Source: docs/data-models.md] - daily_summaries, assets, safety_events table schemas

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
