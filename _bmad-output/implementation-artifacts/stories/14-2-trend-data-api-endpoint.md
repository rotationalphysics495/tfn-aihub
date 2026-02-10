# Story 14.2: Trend Data API Endpoint

Status: ready-for-dev

## Story

As a Plant Manager,
I want the action items API to include 7-day trend data for each asset,
so that I can see whether a problem is new or recurring.

## Acceptance Criteria

1. **Given** an action item exists for an asset with 7 days of history in `daily_summaries`, **When** `GET /api/v1/actions/daily?date={date}` is called, **Then** each action item includes a `trend_data` field containing:
   - 7-day array of the relevant metric (OEE for OEE items, downtime for downtime items, safety event count for safety items)
   - `days_on_report` -- number of days this asset+category appeared as an action item in the last 7 days
   - `consecutive_days` -- number of consecutive days this has been an issue
   - `week_over_week_change` -- percentage change vs. same metric 7 days ago

2. **Given** an asset has fewer than 7 days of history, **When** trend data is calculated, **Then** only available days are returned, **And** `days_on_report` and `consecutive_days` use available data.

3. **Given** an asset has no prior history (first appearance), **When** trend data is calculated, **Then** `days_on_report` = 1, `consecutive_days` = 1, `week_over_week_change` = null, **And** the 7-day array contains only today's value.

4. **Given** trend data is calculated, **When** the response is serialized, **Then** the `TrendData` schema validates correctly with all required fields.

5. **Given** multiple action items are returned, **When** trend data is computed, **Then** trend queries are batched per asset (not N+1 per action item) to maintain performance.

6. **Given** trend data has been computed for a date, **When** the same date is requested again within the cache TTL (15min), **Then** the cached trend data is returned.

## Tasks / Subtasks

- [ ] Task 1: Add `TrendData` Pydantic schema to `app/schemas/action.py` (AC: #1, #4)
  - [ ] 1.1 Create `TrendData` model with fields: `metric_values` (List[Optional[float]]), `days_on_report` (int), `consecutive_days` (int), `week_over_week_change` (Optional[float])
  - [ ] 1.2 Add optional `trend_data: Optional[TrendData]` field to `ActionItem` model
  - [ ] 1.3 Verify Pydantic serialization and JSON schema output

- [ ] Task 2: Implement trend data calculation in `app/services/action_engine.py` (AC: #1, #2, #3, #5)
  - [ ] 2.1 Add `_load_trailing_summaries(target_date, asset_ids, lookback_days=7)` method that batch-queries `daily_summaries` for trailing 7 days for all relevant asset IDs in a single query
  - [ ] 2.2 Add `_calculate_trend_data(asset_id, category, target_date, trailing_summaries)` method that computes the `TrendData` fields for a single action item
  - [ ] 2.3 Add `_calculate_days_on_report(asset_id, category, trailing_summaries, config)` helper that counts how many of the trailing days would have triggered an action item for this asset+category
  - [ ] 2.4 Add `_calculate_consecutive_days(asset_id, category, trailing_summaries, config)` helper that counts consecutive days backward from target_date
  - [ ] 2.5 Integrate trend calculation into `generate_action_list()` -- after merge/prioritize, call trend calculation for all action items in batch
  - [ ] 2.6 Handle edge cases: fewer than 7 days of history, first appearance, null metric values

- [ ] Task 3: Add caching for trend data (AC: #6)
  - [ ] 3.1 Cache the trailing summaries query result with a key based on `target_date` and sorted asset_ids hash
  - [ ] 3.2 Use existing `_action_list_cache` pattern (the trend data is part of the ActionItem already cached)

- [ ] Task 4: Write tests for trend data calculation (AC: #1, #2, #3, #4, #5)
  - [ ] 4.1 Test: asset with full 7 days of history returns correct metric array and trend fields
  - [ ] 4.2 Test: asset with fewer than 7 days returns partial array with correct counts
  - [ ] 4.3 Test: first-appearance asset returns `days_on_report=1`, `consecutive_days=1`, `week_over_week_change=null`
  - [ ] 4.4 Test: `TrendData` schema validates correctly
  - [ ] 4.5 Test: batch query loads trailing summaries for multiple assets in single query
  - [ ] 4.6 Test: OEE trend uses `oee_percentage` metric, downtime uses `downtime_minutes`, safety uses event count
  - [ ] 4.7 Test: `week_over_week_change` computes correctly as percentage change
  - [ ] 4.8 Test: API response includes `trend_data` field on action items

## Dev Notes

### Architecture Context

- **FastAPI 0.109+** / **Python 3.11+** backend
- **Supabase (PostgreSQL)** via `supabase-py 2.0+` for all data queries
- **Pydantic v2** with `BaseModel`, `Field`, `computed_field`, `ConfigDict` patterns
- **cachetools 5.3+** for in-memory TTL caching
- This story enhances the existing Action Engine (Story 3.1/3.2) -- do NOT create a new service

### Existing Code to Modify (NOT Create New)

**`apps/api/app/schemas/action.py`** -- Add `TrendData` schema:
- Follow the existing pattern: use `BaseModel` with `Field(...)` descriptors and `model_config = ConfigDict(...)` with `json_schema_extra` examples
- Add `TrendData` class BEFORE the `ActionItem` class definition
- Add `trend_data: Optional[TrendData] = Field(None, ...)` to `ActionItem`
- Reference existing patterns: `EvidenceRef`, `ActionItem`, `ActionListResponse` in this file

**`apps/api/app/services/action_engine.py`** -- Add trend calculation methods:
- Add methods to the existing `ActionEngine` class -- do NOT create a separate service
- The `generate_action_list()` method already gathers safety/oee/financial actions then merges; add trend calculation AFTER the merge step
- Follow existing async/await patterns for Supabase queries
- Follow existing caching patterns (the `_action_list_cache` already caches the full `ActionListResponse` which will include trend_data)

### Database Query Pattern

The trailing summaries query should look like:
```python
# Batch query: get 7 days of daily_summaries for all relevant assets
client.table("daily_summaries").select(
    "id, asset_id, report_date, oee_percentage, downtime_minutes, "
    "financial_loss_dollars, actual_output, target_output"
).in_("asset_id", asset_ids_list)
.gte("report_date", (target_date - timedelta(days=6)).isoformat())
.lte("report_date", target_date.isoformat())
.execute()
```

For safety event counting in the trailing window:
```python
client.table("safety_events").select("asset_id, event_timestamp")
.in_("asset_id", asset_ids_list)
.gte("event_timestamp", start_of_lookback.isoformat())
.lte("event_timestamp", end_of_target_day.isoformat())
.eq("is_resolved", False)
.execute()
```

### Metric Mapping by Category

| ActionCategory | Metric Source | Column | Trend Array Values |
|---------------|--------------|--------|-------------------|
| `OEE` | `daily_summaries` | `oee_percentage` | Float 0-100 |
| `FINANCIAL` | `daily_summaries` | `financial_loss_dollars` | Float USD |
| `SAFETY` | `safety_events` | count per day | Integer count |

### Key Implementation Details

1. **`days_on_report` logic**: For OEE items, count days where `oee_percentage < target_oee`. For financial items, count days where `financial_loss_dollars > threshold`. For safety items, count days with unresolved safety events for that asset.

2. **`consecutive_days` logic**: Starting from `target_date`, count backward. For OEE: consecutive days where `oee_percentage < target_oee`. Stop counting at first day that does NOT meet the condition. Minimum is 1 (today counts).

3. **`week_over_week_change` logic**: Compare today's metric value to the value 7 days ago. Formula: `((today - week_ago) / week_ago) * 100`. Return `null` if no data 7 days ago. For safety, compare event counts. Note: for OEE, a negative change means OEE dropped (worse). For downtime/financial, a positive change means MORE downtime/loss (worse).

4. **Batch loading**: Extract all unique `asset_id` values from the merged action list BEFORE computing trends. Make ONE query to `daily_summaries` for all assets, then distribute results per-asset in Python. This prevents N+1 query patterns.

5. **Cache integration**: The trend data is embedded in `ActionItem.trend_data`. Since `generate_action_list()` already caches the full `ActionListResponse`, trend data is automatically cached. The existing 5-minute `_action_list_cache` plus the 15-minute daily cache tier both apply.

### TrendData Schema Design

```python
class TrendData(BaseModel):
    """7-day trend data for an action item's asset+metric."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "metric_values": [78.5, 76.2, 74.8, 80.1, 72.5, None, 71.3],
                "days_on_report": 5,
                "consecutive_days": 3,
                "week_over_week_change": -9.2,
            }
        }
    )

    metric_values: List[Optional[float]] = Field(
        ...,
        description="7-day array of metric values (index 0 = oldest, 6 = target_date). None for missing days.",
        max_length=7,
    )
    days_on_report: int = Field(
        ...,
        ge=0,
        le=7,
        description="Number of days this asset+category appeared as an action item in the last 7 days",
    )
    consecutive_days: int = Field(
        ...,
        ge=0,
        le=7,
        description="Number of consecutive days this has been an issue (counting backward from target_date)",
    )
    week_over_week_change: Optional[float] = Field(
        None,
        description="Percentage change vs. same metric 7 days ago. Null if no data 7 days ago.",
    )
```

### Testing Patterns

Follow the existing test patterns in `apps/api/tests/test_action_engine.py`:
- Use `pytest` fixtures with `ActionEngine()` instances
- Mock `supabase` client responses with `MagicMock` / `AsyncMock`
- Use `uuid4()` for test asset IDs
- Use `date.today() - timedelta(days=1)` for target dates
- Test file: `apps/api/tests/test_action_engine.py` (extend existing, do not create separate)

### Performance Guardrails

- Trailing summaries query MUST be batched (single query for all assets) -- verified in AC #5
- Maximum 2 additional Supabase queries per `generate_action_list()` call (1 for trailing daily_summaries, 1 for trailing safety_events if safety items exist)
- No additional queries for financial items (they use the same daily_summaries data)

### Project Structure Notes

- All changes are in `apps/api/` -- NO frontend changes in this story
- Schema file: `apps/api/app/schemas/action.py`
- Service file: `apps/api/app/services/action_engine.py`
- Test file: `apps/api/tests/test_action_engine.py`
- API router file `apps/api/app/api/actions.py` does NOT need changes -- the existing `/daily` endpoint already returns `ActionListResponse` which will automatically include the new `trend_data` field
- Do NOT modify `apps/api/app/api/downtime.py` -- that is for Story 14.3

### Dependencies

- **Story 14.1** (Downtime Events Data Model) is NOT required for this story -- trend data queries `daily_summaries` and `safety_events`, not `downtime_events`
- This story depends only on existing tables: `daily_summaries`, `safety_events`, `assets`
- Stories 14.4-14.6 (frontend trend indicators, Pareto chart, AI summary) depend on THIS story's API output

### References

- [Source: _bmad-output/planning-artifacts/epic-14.md#Story 14.2]
- [Source: docs/architecture-api.md#Caching Strategy]
- [Source: docs/architecture-api.md#Directory Structure]
- [Source: docs/data-models.md#daily_summaries]
- [Source: docs/data-models.md#safety_events]
- [Source: docs/improvements.md#Trend indicators on action items]
- [Source: apps/api/app/schemas/action.py -- existing ActionItem schema]
- [Source: apps/api/app/services/action_engine.py -- existing ActionEngine class]
- [Source: apps/api/app/services/agent/cache.py -- caching patterns]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
