# Story 14.3: Downtime Pareto API Endpoint

Status: ready-for-dev

## Story

As a Plant Manager,
I want an API endpoint that returns downtime reason code breakdown for an asset or workcenter,
so that the frontend can display a Pareto chart showing top downtime drivers.

## Acceptance Criteria

1. **Given** downtime events exist for an asset on a given date, **When** `GET /api/v1/downtime/pareto?date={date}&asset_id={id}` is called, **Then** the response includes:
   - Array of reason codes sorted by total duration (descending)
   - Each entry: `reason_code`, `total_minutes`, `percentage` of total, `event_count`, `is_planned`
   - `total_downtime_minutes`
   - Planned vs. unplanned split

2. **Given** an `area` parameter is provided instead of `asset_id`, **When** the Pareto endpoint is called, **Then** downtime is aggregated across all assets in that workcenter area.

3. **Given** no downtime events exist for the query, **When** the endpoint is called, **Then** the response returns an empty array with `total_minutes = 0`.

## Tasks / Subtasks

- [ ] Task 1: Extend `ParetoItem` model with `is_planned` field and `ParetoResponse` with planned/unplanned split (AC: #1)
  - [ ] 1.1 Add `is_planned` boolean field to `ParetoItem` in `app/models/downtime.py`
  - [ ] 1.2 Add `planned_minutes` and `unplanned_minutes` fields to `ParetoResponse`
  - [ ] 1.3 Create `DowntimeParetoResponse` schema in `app/schemas/downtime.py` (new file) if a distinct API schema is needed, or extend existing `ParetoResponse`
- [ ] Task 2: Add `downtime_events` query method to `DowntimeAnalysisService` (AC: #1, #2, #3)
  - [ ] 2.1 Add `get_downtime_from_events_table()` method querying the new `downtime_events` table
  - [ ] 2.2 Support filtering by `asset_id`, `area`, and `date` (single date via `event_date`)
  - [ ] 2.3 Handle empty result set returning empty array
- [ ] Task 3: Update Pareto calculation to use `downtime_events` data (AC: #1)
  - [ ] 3.1 Add `transform_downtime_events_to_pareto()` method or update existing `calculate_pareto()` to handle `downtime_events` records with `is_planned` field
  - [ ] 3.2 Compute `planned_minutes` and `unplanned_minutes` aggregates
  - [ ] 3.3 Include `is_planned` in per-reason-code aggregation
- [ ] Task 4: Update `/pareto` endpoint to prefer `downtime_events` table (AC: #1, #2, #3)
  - [ ] 4.1 Add `date` query parameter (single date, defaults to yesterday)
  - [ ] 4.2 Check if `downtime_events` data exists for the query; if yes, use it; if no, fall back to existing `daily_summaries` behavior
  - [ ] 4.3 Return enhanced `ParetoResponse` with planned/unplanned split
- [ ] Task 5: Add caching with 15min TTL (AC: #1)
  - [ ] 5.1 Apply `cache_daily_ttl` (15min) caching to the Pareto endpoint response using the existing `cachetools` pattern
- [ ] Task 6: Write tests (all ACs)
  - [ ] 6.1 Test Pareto with `downtime_events` data for a single asset
  - [ ] 6.2 Test Pareto with `area` aggregation
  - [ ] 6.3 Test empty result set returns empty array with `total_minutes = 0`
  - [ ] 6.4 Test planned vs. unplanned split calculation
  - [ ] 6.5 Test fallback to `daily_summaries` when no `downtime_events` exist

## Dev Notes

### CRITICAL: Existing Pareto Endpoint Already Exists

There is an **existing** `/api/v1/downtime/pareto` endpoint created in Story 2.5. This story **extends** it -- do NOT create a new endpoint or router. The existing infrastructure is:

- **Router:** `apps/api/app/api/downtime.py` -- already has `get_downtime_pareto()` at line 200
- **Models:** `apps/api/app/models/downtime.py` -- `ParetoItem`, `ParetoResponse`, `DowntimeEvent`
- **Service:** `apps/api/app/services/downtime_analysis.py` -- `DowntimeAnalysisService` with `calculate_pareto()` method
- **Router registration:** `apps/api/app/main.py` line 70 -- `app.include_router(downtime.router, prefix="/api/v1/downtime", tags=["Downtime"])`

The current implementation queries `daily_summaries` (which has only a single `downtime_minutes` number per asset per day with no reason code breakdown) or `live_snapshots`. Story 14.1 introduces the `downtime_events` table with individual events including `reason_code`, `duration_minutes`, `is_planned`, `shift`, `reason_detail`, and `source_system`.

**The goal of this story is to make the Pareto endpoint use `downtime_events` when available, with graceful fallback to the existing `daily_summaries` behavior.**

### Dependency: Story 14.1 Must Be Complete

Story 14.1 creates the `downtime_events` table with this schema:
- `id` UUID PK
- `asset_id` UUID FK -> assets
- `event_date` DATE
- `shift` TEXT CHECK ('morning', 'afternoon', 'night')
- `reason_code` TEXT (Mechanical, Changeover, Material Shortage, Quality Hold, Operator Unavailable, Planned Maintenance)
- `reason_detail` TEXT (freeform)
- `duration_minutes` INTEGER
- `is_planned` BOOLEAN
- `source_system` TEXT DEFAULT 'manual'
- `source_event_id` TEXT nullable
- `created_at` TIMESTAMPTZ

Indexes: `asset_id`, `event_date`, `reason_code`
RLS: enabled following existing patterns
Migration file: `supabase/migrations/0029_downtime_events.sql`

### Architecture Compliance

| Requirement | How to Comply |
|-------------|---------------|
| FastAPI 0.109+ async patterns | All endpoint handlers and service methods MUST be `async` |
| Pydantic BaseModel (v2 style) | Use `model_config = ConfigDict(...)` for schema config, not `class Config` |
| Supabase client pattern | Use `get_supabase_client()` helper in `downtime.py` (already exists at line 45) |
| Caching: Daily tier = 15min TTL | Use `cachetools` with `cache_daily_ttl` (900s) from Settings |
| RLS enabled | Queries run through Supabase client which enforces RLS via service role |
| Error handling pattern | Use `try/except HTTPException: raise / except Exception as e: logger.error(...); raise HTTPException(500)` |
| Auth dependency | All endpoints require `current_user: CurrentUser = Depends(get_current_user)` |

### Existing Service Pattern to Follow

The `DowntimeAnalysisService` in `apps/api/app/services/downtime_analysis.py`:
- Accepts a Supabase client in constructor: `def __init__(self, supabase_client)`
- Has internal caching: `self._assets_cache`, `self._cost_centers_cache`
- Uses `self.client.table("table_name").select("*").eq("field", value).execute()` pattern
- Calculates financial impact via `calculate_financial_impact()` using `cost_centers.standard_hourly_rate`
- `calculate_pareto()` method groups by reason_code, sorts descending, computes cumulative percentages and 80% threshold index

### New Method Required in DowntimeAnalysisService

Add a method like:

```python
async def get_downtime_from_events_table(
    self,
    event_date: Optional[date] = None,
    asset_id: Optional[str] = None,
    area: Optional[str] = None,
) -> List[dict]:
    """Query downtime_events table for granular reason code data."""
    if event_date is None:
        event_date = date.today() - timedelta(days=1)

    query = self.client.table("downtime_events").select("*")
    query = query.eq("event_date", event_date.isoformat())

    if asset_id:
        query = query.eq("asset_id", asset_id)

    response = query.execute()
    records = response.data or []

    # Filter by area if specified (requires asset lookup)
    if area:
        assets_map = await self.get_assets_map()
        records = [
            r for r in records
            if r.get("asset_id") in assets_map and
            assets_map[r["asset_id"]].get("area", "").lower() == area.lower()
        ]

    return records
```

### Updated Pareto Calculation

The existing `calculate_pareto()` method already groups by `reason_code` and computes percentages. It needs to be extended to:

1. Track `is_planned` per reason code group (a reason code is "planned" if any event in that group has `is_planned=True` -- or preferably, aggregate planned vs unplanned minutes separately)
2. Compute `planned_minutes` and `unplanned_minutes` totals for the response

### Endpoint Update Strategy

Modify the existing `get_downtime_pareto()` in `apps/api/app/api/downtime.py`:

1. Add a `date` query parameter (single date, for `downtime_events` query)
2. First try to fetch from `downtime_events` table via new service method
3. If `downtime_events` returns data, use that for Pareto calculation
4. If no `downtime_events` exist, fall back to existing `daily_summaries`/`live_snapshots` logic
5. Return enhanced `ParetoResponse` with `planned_minutes` and `unplanned_minutes`

### Response Schema Additions

Add to `ParetoItem` in `app/models/downtime.py`:
```python
is_planned: bool = Field(False, description="Whether this reason code is primarily planned downtime")
```

Add to `ParetoResponse` in `app/models/downtime.py`:
```python
planned_minutes: int = Field(0, description="Total planned downtime minutes")
unplanned_minutes: int = Field(0, description="Total unplanned downtime minutes")
```

These additions are backward-compatible -- existing consumers receive the new fields with sensible defaults.

### Caching Implementation

Follow the existing pattern from Story 5.8. The caching should be at the endpoint level or service level using `cachetools.TTLCache`:

```python
from cachetools import TTLCache

_pareto_cache = TTLCache(maxsize=100, ttl=900)  # 15min = daily tier

def _cache_key(date_val, asset_id, area):
    return f"pareto:{date_val}:{asset_id or 'all'}:{area or 'all'}"
```

Check cache before querying. Store result after computation.

### Project Structure Notes

- All changes are in the `apps/api/` directory
- No new routers or files need to be created (extend existing)
- No frontend changes in this story (that is Story 14.5)
- No migration changes (Story 14.1 handles the table)

**Files to Modify:**
| File | Change |
|------|--------|
| `apps/api/app/models/downtime.py` | Add `is_planned` to `ParetoItem`, add `planned_minutes`/`unplanned_minutes` to `ParetoResponse` |
| `apps/api/app/services/downtime_analysis.py` | Add `get_downtime_from_events_table()` method, extend `calculate_pareto()` for planned/unplanned |
| `apps/api/app/api/downtime.py` | Update `get_downtime_pareto()` to use `downtime_events` with fallback |

**Files to Create:**
| File | Purpose |
|------|---------|
| `apps/api/app/schemas/downtime.py` | Only if a distinct API-layer schema is needed (optional -- existing `ParetoResponse` model may suffice) |
| `apps/api/tests/test_downtime_pareto.py` | Tests for the updated Pareto endpoint |

### Anti-Patterns to Avoid

1. **DO NOT create a new router or new endpoint path** -- extend the existing `/api/v1/downtime/pareto`
2. **DO NOT remove the `daily_summaries` fallback** -- the system must work even if `downtime_events` is empty
3. **DO NOT create synchronous methods** -- all DB queries must be async
4. **DO NOT duplicate the Pareto calculation logic** -- extend `calculate_pareto()` rather than creating a parallel method
5. **DO NOT hard-code reason codes** -- they come from the data; the standard list (Mechanical, Changeover, etc.) is in the seed data
6. **DO NOT skip the `area` filter** -- workcenter-level aggregation (AC #2) requires filtering events by asset area

### References

- [Source: _bmad-output/planning-artifacts/epic-14.md#Story 14.3] - Story requirements and AC
- [Source: docs/architecture-api.md#API Endpoints] - Router registration and endpoint patterns
- [Source: docs/architecture-api.md#Caching Strategy] - TTL tiers (Daily = 15min)
- [Source: docs/data-models.md#daily_summaries] - Current schema (no reason code breakdown)
- [Source: apps/api/app/api/downtime.py] - Existing Pareto endpoint (Story 2.5)
- [Source: apps/api/app/models/downtime.py] - ParetoItem, ParetoResponse models
- [Source: apps/api/app/services/downtime_analysis.py] - DowntimeAnalysisService
- [Source: apps/api/app/core/config.py] - Settings including cache_daily_ttl=900
- [Source: docs/improvements.md#Downtime Pareto] - Full feature rationale and design

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
