# Story 11.1: Workcenter Summary API Endpoint

Status: done

## Story

As a **Plant Manager**,
I want **an API endpoint that returns production data grouped by workcenter**,
so that **the frontend can display a plant-wide production scorecard**.

## Acceptance Criteria

1. **Given** daily summary data exists for multiple assets across workcenters, **When** `GET /api/v1/production/workcenter-summary?date={date}` is called, **Then** the response includes one entry per workcenter (grouped by `assets.area`) with:
   - Workcenter name (e.g., "Grinding")
   - Total actual output (sum of `daily_summaries.units_produced` for assets in that area)
   - Total target output (sum of `shift_targets.target_units` for assets in that area)
   - Attainment percentage (actual / target * 100)
   - Count of assets that hit target vs. missed
   - Per-asset breakdown array with: asset name, actual, target, OEE, downtime minutes

2. **Given** no daily summary data exists for the requested date, **When** the endpoint is called, **Then** the response returns an empty array with a 200 status **And** the response includes a message indicating no data available for that date.

3. **Given** a date parameter is not provided, **When** the endpoint is called, **Then** it defaults to yesterday (T-1).

## Tasks / Subtasks

- [ ] Task 1: Create Pydantic response schemas (AC: #1)
  - [ ] 1.1 Create `apps/api/app/schemas/production.py` with `AssetDetail`, `WorkcenterEntry`, and `WorkcenterSummaryResponse` models
  - [ ] 1.2 Add proper Field descriptions, validation constraints, and JSON schema examples
- [ ] Task 2: Implement workcenter summary endpoint (AC: #1, #2, #3)
  - [ ] 2.1 Add `GET /workcenter-summary` route handler to `apps/api/app/api/production.py`
  - [ ] 2.2 Implement Supabase query joining `assets` + `daily_summaries` + `shift_targets`
  - [ ] 2.3 Group results by `assets.area` and aggregate within each group
  - [ ] 2.4 Calculate attainment percentage, hit/miss counts per workcenter
  - [ ] 2.5 Build per-asset breakdown arrays within each workcenter entry
  - [ ] 2.6 Handle date parameter with T-1 default
  - [ ] 2.7 Handle empty data case (200 with empty array + message)
- [ ] Task 3: Register route (AC: #1)
  - [ ] 3.1 Verify endpoint is accessible under existing `/api/production` router prefix (already registered in `main.py`)
- [ ] Task 4: Write tests (AC: #1, #2, #3)
  - [ ] 4.1 Test normal response with multiple workcenters and assets
  - [ ] 4.2 Test empty data returns 200 with empty array and message
  - [ ] 4.3 Test date defaults to T-1 when not provided
  - [ ] 4.4 Test date parameter is respected when provided
  - [ ] 4.5 Test attainment calculation correctness (including zero target edge case)
  - [ ] 4.6 Test authentication requirement (401 without token)

## Dev Notes

### Architecture Patterns and Constraints

**API Framework:** FastAPI 0.109+ with async route handlers. All endpoints require JWT Bearer authentication via `get_current_user` dependency.

**Existing Production Router:** The endpoint MUST be added to the existing `apps/api/app/api/production.py` file which already has:
- `router = APIRouter()` (already instantiated)
- Router is already registered in `main.py` at prefix `/api/production` (line 68)
- So the new endpoint path should be `/workcenter-summary` which maps to `GET /api/production/workcenter-summary`

**IMPORTANT - Endpoint URL:** The epic specifies `/api/v1/production/workcenter-summary` but the existing production router is mounted at `/api/production` (NOT `/api/v1/production`). Two options:
1. Add the route to the existing `production.py` router -- endpoint becomes `/api/production/workcenter-summary`
2. Register a second alias in `main.py` at `/api/v1/production` (follows the pattern used for actions/v1/actions on lines 63-65)

**Recommendation:** Add to the existing production router AND register a `/api/v1/production` alias in `main.py` to match the epic spec while maintaining backward compatibility with the non-versioned path. This follows the exact pattern on main.py lines 63-65 where `actions.router` is registered at both `/api/actions` and `/api/v1/actions`.

### Supabase Query Pattern

Follow the existing pattern in `production.py` (see `get_throughput_data` function):

```python
async def get_supabase_client():
    from supabase import create_client
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_key:
        raise HTTPException(status_code=503, detail="Supabase not configured")
    return create_client(settings.supabase_url, settings.supabase_key)
```

The `get_supabase_client()` helper already exists in `production.py` -- reuse it, do NOT create a duplicate.

### Database Schema (Exact Column Names)

**`assets` table:**
- `id` (UUID), `name` (VARCHAR), `source_id` (VARCHAR), `area` (VARCHAR), `created_at`, `updated_at`
- The `area` column contains workcenter names: "Roasting", "Grinding", "Filling", "Packaging"

**`daily_summaries` table:**
- `id` (UUID), `asset_id` (UUID FK), `date` (DATE), `oee` (DECIMAL), `availability` (DECIMAL), `performance` (DECIMAL), `quality` (DECIMAL), `downtime_minutes` (INTEGER), `units_produced` (INTEGER), `created_at`
- NOTE: Column is `units_produced` NOT `actual_output` -- the improvements.md mentions `actual_output` but the data-models.md confirms `units_produced`

**`shift_targets` table:**
- `id` (UUID), `asset_id` (UUID FK), `shift` (VARCHAR), `target_units` (INTEGER), `created_at`, `updated_at`
- NOTE: There may be MULTIPLE shift_targets per asset (one per shift). Sum ALL target_units for an asset to get daily target.

### Pydantic Schema Design

Create `apps/api/app/schemas/production.py` (new file). Follow existing schema patterns from `apps/api/app/schemas/action.py`:

```python
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class AssetDetail(BaseModel):
    """Per-asset production detail within a workcenter."""
    asset_id: str = Field(..., description="Asset UUID")
    asset_name: str = Field(..., description="Asset display name")
    actual_output: int = Field(..., description="Units produced")
    target_output: int = Field(..., description="Sum of shift target units")
    attainment_pct: float = Field(..., description="Actual/target * 100")
    oee: Optional[float] = Field(None, description="OEE percentage")
    downtime_minutes: Optional[int] = Field(None, description="Total downtime minutes")
    hit_target: bool = Field(..., description="Whether actual >= target")

class WorkcenterEntry(BaseModel):
    """Aggregated production data for one workcenter."""
    workcenter: str = Field(..., description="Workcenter name (e.g., Grinding)")
    total_actual: int = Field(..., description="Sum of units_produced across assets")
    total_target: int = Field(..., description="Sum of target_units across assets")
    attainment_pct: float = Field(..., description="total_actual / total_target * 100")
    assets_hit: int = Field(..., description="Count of assets meeting target")
    assets_missed: int = Field(..., description="Count of assets below target")
    assets: List[AssetDetail] = Field(default_factory=list, description="Per-asset breakdown")

class WorkcenterSummaryResponse(BaseModel):
    """Response model for workcenter production summary."""
    workcenters: List[WorkcenterEntry] = Field(default_factory=list)
    report_date: date = Field(..., description="The date for this summary")
    message: Optional[str] = Field(None, description="Status message (e.g., no data available)")
```

### Query Strategy

The Supabase client does not support SQL JOINs directly. Use the same multi-query pattern as `get_throughput_data`:

1. **Query 1:** Fetch all assets with their `id`, `name`, `area`
2. **Query 2:** Fetch `daily_summaries` filtered by `date` parameter
3. **Query 3:** Fetch all `shift_targets` (sum per asset for daily total)
4. **Join in Python:** Map summaries and targets to assets by `asset_id`, then group by `area`

### Edge Cases

- **Zero target:** If an asset has no shift_targets entries, treat target as 0. Attainment should be 100.0 if actual > 0 and target is 0 (avoid division by zero). Use the existing `calculate_percentage` function already in production.py.
- **Missing area:** If an asset has `area = NULL`, skip it or group under "Unassigned". Do NOT let it crash the aggregation.
- **Partial data:** An asset may have a daily_summary but no shift_target, or vice versa. Handle gracefully.
- **Date format:** Accept ISO date string `YYYY-MM-DD`. Use Python `date` type in the query parameter.

### Authentication

All endpoints require JWT auth. Follow the existing pattern:
```python
current_user: CurrentUser = Depends(get_current_user)
```

Import from `app.core.security` and `app.models.user` (already imported at top of production.py).

### Error Handling

Follow existing pattern in production.py:
```python
try:
    # ... implementation
except HTTPException:
    raise
except Exception as e:
    logger.error(f"Error fetching workcenter summary: {e}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to fetch workcenter summary data"
    )
```

### Project Structure Notes

- **Schemas go in:** `apps/api/app/schemas/production.py` (new file, alongside existing `action.py`, `financial.py`, `summary.py`)
- **Endpoint goes in:** `apps/api/app/api/production.py` (existing file -- ADD to it, do NOT create a new router file)
- **main.py update:** Add versioned alias `app.include_router(production.router, prefix="/api/v1/production", tags=["Production V1"])` after the existing production router registration on line 68
- **Do NOT create** a separate service file for this. The query logic is straightforward enough to live in the route handler (matching the existing pattern in production.py)

### Testing Standards

- **Framework:** pytest with async support
- **Location:** `apps/api/tests/` directory
- **Test file:** `apps/api/tests/api/test_production_workcenter.py` (new file)
- Mock the Supabase client responses (do NOT require a live database for unit tests)
- Test the aggregation logic separately from the HTTP layer

### Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `apps/api/app/schemas/production.py` | CREATE | `AssetDetail`, `WorkcenterEntry`, `WorkcenterSummaryResponse` Pydantic models |
| `apps/api/app/api/production.py` | MODIFY | Add `GET /workcenter-summary` endpoint with date query param |
| `apps/api/app/main.py` | MODIFY | Add `/api/v1/production` versioned alias for production router |
| `apps/api/tests/api/test_production_workcenter.py` | CREATE | Unit tests for the new endpoint |

### References

- [Source: _bmad-output/planning-artifacts/epic-11.md#Story 11.1] - Story requirements and acceptance criteria
- [Source: docs/architecture-api.md#Directory Structure] - API file organization pattern
- [Source: docs/architecture-api.md#API Endpoints] - Router prefix conventions
- [Source: docs/data-models.md#daily_summaries] - Exact column names for daily_summaries table
- [Source: docs/data-models.md#shift_targets] - Exact column names for shift_targets table
- [Source: docs/data-models.md#assets] - Assets table schema with area column
- [Source: docs/api-contracts.md#Production Endpoints] - Existing production API contract pattern
- [Source: docs/improvements.md#Workcenter production summary] - Detailed feature requirements
- [Source: apps/api/app/api/production.py] - Existing production router with Supabase query patterns
- [Source: apps/api/app/main.py#line 68] - Production router registration and versioned alias pattern
- [Source: apps/api/app/schemas/action.py] - Schema design patterns (Field descriptions, enums, computed fields)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Implementation Summary

Implemented the Workcenter Summary API endpoint (`GET /workcenter-summary`) that returns production data grouped by workcenter (asset area). The endpoint queries assets, daily_summaries, and shift_targets from Supabase, joins them in Python by asset_id, groups by area, and returns aggregated totals with per-asset breakdowns. Registered a versioned alias at `/api/v1/production` alongside the existing `/api/production` prefix.

### Files Created
- `apps/api/app/schemas/production.py` - Pydantic response models (AssetDetail, WorkcenterEntry, WorkcenterSummaryResponse)
- `apps/api/tests/api/test_production_workcenter.py` - 14 unit tests covering auth, normal response, empty data, date defaulting, and edge cases

### Files Modified
- `apps/api/app/api/production.py` - Added GET /workcenter-summary endpoint with date query param, Supabase multi-query logic, Python-side aggregation by area
- `apps/api/app/main.py` - Added /api/v1/production versioned alias for production router

### Key Decisions
- Used `table.side_effect` pattern in tests for clean per-table mock setup instead of chained side_effect list
- Assets with NULL/empty area are silently excluded (not grouped under "Unassigned") to avoid clutter in response
- The endpoint only shows assets that have daily_summary data for the requested date; assets with only shift_targets but no summary are omitted
- Workcenter entries are sorted alphabetically by area name for consistent ordering

### Tests Added
- `apps/api/tests/api/test_production_workcenter.py` - 14 tests:
  - Auth: requires JWT on both v1 and legacy paths
  - Normal: grouped workcenters, aggregation math, per-asset breakdown, legacy path
  - Empty: 200 with empty array and message
  - Date: defaults to T-1, explicit date respected
  - Edge cases: zero target attainment, null area exclusion, partial data (summary without target, target without summary), null OEE/downtime

### Notes for Reviewer
- The endpoint reuses the existing `calculate_percentage()` helper for attainment calculation (returns 100.0 for zero target)
- The `date` query param uses FastAPI's alias feature (`alias="date"`) so the Python param name is `report_date` to avoid shadowing the built-in
- Both `/api/production/workcenter-summary` and `/api/v1/production/workcenter-summary` paths are functional

### Test Results
```
14 passed in 0.14s (new workcenter tests)
20 passed in 0.38s (existing production tests — no regressions)
```

### Acceptance Criteria Status
- [x] AC#1 - Workcenter-grouped response with aggregations — implemented in `apps/api/app/api/production.py:get_workcenter_summary()` + `apps/api/app/schemas/production.py`
- [x] AC#2 - Empty data returns 200 with message — implemented in `apps/api/app/api/production.py:get_workcenter_summary()` (empty summaries check)
- [x] AC#3 - Date defaults to T-1 — implemented in `apps/api/app/api/production.py:get_workcenter_summary()` (Optional[date] with None default)

## Code Review Record

**Reviewer**: Code Review Agent
**Date**: 2026-02-11
**Diff Size**: 678 lines (5 files)

### Checklist Results
- Acceptance Criteria: PASS
- Code Quality: PASS
- Test Coverage: PASS
- Security: PASS

### Issues Found

| # | Description | Severity | Status |
|---|-------------|----------|--------|
| 1 | Test file re-declares `mock_verify_jwt` fixture shadowing identical conftest.py version | MEDIUM | Fixed |
| 2 | No test for Supabase client error handling (500 response path) | MEDIUM | Fixed |
| 3 | `calculate_percentage(0, 0)` returns 100.0 (pre-existing shared helper behavior) | LOW | Documented |
| 4 | `summaries_map` silently overwrites duplicate daily_summary records for same asset_id | LOW | Documented |
| 5 | No test for invalid date format 422 validation (FastAPI handles automatically) | LOW | Documented |
| 6 | `hit_target` is True when both actual=0 and target=0 (consistent with calculate_percentage) | LOW | Documented |

**Totals**: 0 HIGH, 2 MEDIUM, 4 LOW

### Fixes Applied

| Issue # | Fix Description | Verified |
|---------|-----------------|----------|
| 1 | Removed duplicate `mock_verify_jwt` fixture from test file; now uses conftest.py version | 15 tests pass |
| 2 | Added `test_supabase_error_returns_500` test verifying error handler returns 500 with generic message | 15 tests pass |

### Remaining Issues (Low Severity)
- Issue 3: `calculate_percentage(0, 0)` returns 100.0 — pre-existing behavior in shared helper, consistent across codebase
- Issue 4: Duplicate daily_summary records for same asset_id would be last-write-wins — DB unique constraint should prevent this
- Issue 5: Invalid date format returns 422 automatically via FastAPI query param validation — no explicit test needed
- Issue 6: `0 >= 0 = True` for hit_target is logically correct (no target was missed) and consistent with attainment calc

### Final Status
Approved with fixes

## Test Quality Review

**Quality Score**: 100/100 (A+)
**Tests Reviewed**: 15
**Reviewer**: Test Architect (TEA)
**Date**: 2026-02-11

### Criteria Results

| # | Criterion | Rating | Notes |
|---|-----------|--------|-------|
| 1 | BDD Format | PASS | Clear AC references in docstrings, class-based grouping by scenario |
| 2 | Test ID Conventions | PASS | All 15 tests have formal IDs (11-1-UNIT-001 through 015) — fixed |
| 3 | Hard Waits | PASS | No hard waits — synchronous test client |
| 4 | Determinism | PASS | No conditionals, no random values |
| 5 | Isolation & Cleanup | PASS | Context manager mocks, no shared mutable state |
| 6 | Explicit Assertions | PASS | Every test has explicit assert statements |
| 7 | Test Length | WARN | 440 lines (>300 threshold) — well-organized, splitting not warranted |
| 8 | Test Duration | PASS | 15 tests in 0.14s (~9ms/test) |
| 9 | Fixture Patterns | PASS | Clean fixture architecture with _make_table_mock helper |
| 10 | Data Factories | WARN | Module-level constants adequate for scope; no formal factories |
| 11 | Network-First | N/A | Unit tests with mocked HTTP client |
| 12 | Flakiness Patterns | PASS | Fully deterministic mock-based tests |

### Issues Found
- 0 Critical
- 1 High: Missing formal test IDs — **Fixed**
- 1 Medium: File length 440 lines (documented, well-organized)
- 1 Low: No formal data factories (documented, adequate for scope)

### Fixes Applied
- Added formal test IDs (11-1-UNIT-001 through 11-1-UNIT-015) to all test docstrings — verified 15 tests pass
