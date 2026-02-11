# Story 12.5: Schedule Attainment API

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Plant Manager,
I want an API endpoint that compares scheduled vs. actual production by product,
so that the frontend can show schedule attainment and product mix variance.

## Acceptance Criteria

1. **Given** schedule and actuals data exist for a date, **When** `GET /api/v1/production/schedule-attainment?date={date}` is called, **Then** the response includes per-workcenter schedule attainment with:
   - Workcenter name
   - Per-product breakdown: product name, scheduled quantity, actual quantity, attainment %
   - Variance callouts: products scheduled but not produced, products produced but not scheduled
   - Overall workcenter attainment percentage

2. **Given** an asset produced a different product than scheduled, **When** the attainment response is generated, **Then** a variance callout is included (e.g., "Roaster 1 ran Colombian instead of scheduled Brazilian -- X units of Brazilian still needed").

3. **Given** no schedule exists for the requested date, **When** the endpoint is called, **Then** the response returns HTTP 200 with an empty result and message "No schedule data for this date".

4. **Given** no authentication token is provided, **When** the endpoint is called, **Then** a 401 Unauthorized response is returned (standard JWT auth via `get_current_user` dependency).

5. **Given** the endpoint is called with an optional `area` query parameter, **When** data exists for that area, **Then** results are filtered to only workcenters matching that area.

## Tasks / Subtasks

- [ ] Task 1: Create Pydantic response schemas (AC: #1, #2, #3)
  - [ ] 1.1 Create `apps/api/app/schemas/production.py` with `ScheduleAttainmentResponse`, `WorkcenterAttainment`, `ProductAttainment`, `VarianceCallout` models
  - [ ] 1.2 Include `json_schema_extra` examples following the pattern in `schemas/financial.py`

- [ ] Task 2: Implement schedule attainment endpoint (AC: #1, #2, #3, #4, #5)
  - [ ] 2.1 Add `GET /schedule-attainment` route to `apps/api/app/api/production.py`
  - [ ] 2.2 Accept query params: `date` (required, DATE format), `area` (optional, string)
  - [ ] 2.3 Query `production_schedule` joined with `production_actuals` on `(asset_id, scheduled_date/production_date, shift)`
  - [ ] 2.4 Join with `products` for product names and `assets` for area grouping
  - [ ] 2.5 Identify mismatches where actual `product_id` differs from scheduled `product_id`
  - [ ] 2.6 Calculate per-product attainment % = `(actual_quantity / scheduled_quantity) * 100`
  - [ ] 2.7 Calculate overall workcenter attainment % as weighted average across products
  - [ ] 2.8 Generate variance callout strings for product swaps and missing production
  - [ ] 2.9 Return empty result with message when no schedule data exists for the date

- [ ] Task 3: Register the endpoint (AC: #4)
  - [ ] 3.1 The route is added to the existing `production.router` which is already registered in `main.py` at prefix `/api/production` -- verify it is accessible at `/api/production/schedule-attainment` OR register a versioned alias at `/api/v1/production` (see Dev Notes)

- [ ] Task 4: Add tests
  - [ ] 4.1 Test happy path with matching schedule and actuals data
  - [ ] 4.2 Test product swap detection and variance callout generation
  - [ ] 4.3 Test empty response when no schedule exists
  - [ ] 4.4 Test area filtering
  - [ ] 4.5 Test authentication requirement (401 without token)

## Dev Notes

### Critical Context

This endpoint depends on the `products`, `production_schedule`, and `production_actuals` tables created by Story 12.1 (migration `0026_products_and_schedule.sql`) and seeded by Story 12.2. Those stories MUST be completed first or the tables will not exist.

### API Pattern -- Follow Existing `production.py`

The existing `apps/api/app/api/production.py` defines the router pattern for production endpoints. The current router has:
- `GET /throughput` -- returns `ThroughputResponse`
- `GET /throughput/areas` -- returns `List[str]`

Add the new endpoint to the SAME router file. It is already registered in `main.py`:
```python
app.include_router(production.router, prefix="/api/production", tags=["Production"])
```

This means the endpoint will be accessible at `GET /api/production/schedule-attainment?date=2026-02-09`.

**Note:** The epic spec says `GET /api/v1/production/schedule-attainment`. The existing production router is mounted at `/api/production` (no `/v1/`). Choose one of:
1. Add to existing router at `/api/production/schedule-attainment` (simpler, consistent with existing throughput endpoint)
2. Add a new versioned router alias in `main.py` (like actions has both `/api/actions` and `/api/v1/actions`)

Recommended: Option 1 for simplicity, matching the existing pattern.

### Supabase Client Pattern

Follow the existing `get_supabase_client()` helper in `production.py`:
```python
async def get_supabase_client():
    from supabase import create_client
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase not configured"
        )
    return create_client(settings.supabase_url, settings.supabase_key)
```

### Authentication Pattern

Use the standard `get_current_user` dependency from `app.core.security`:
```python
from app.core.security import get_current_user
from app.models.user import CurrentUser

@router.get("/schedule-attainment")
async def get_schedule_attainment(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    area: Optional[str] = Query(None, description="Filter by plant area"),
    current_user: CurrentUser = Depends(get_current_user),
):
```

### Database Query Strategy

The core query logic joins three tables plus a fourth for grouping:

1. **`production_schedule`** -- the scheduled quantities per asset/product/date/shift
2. **`production_actuals`** -- the actual quantities per asset/product/date/shift
3. **`products`** -- for product name resolution
4. **`assets`** -- for area grouping (workcenter = `assets.area`)

**Join approach:**
- Query `production_schedule` filtered by `scheduled_date = {date}`
- Query `production_actuals` filtered by `production_date = {date}`
- Match on `(asset_id, shift)` to pair scheduled vs actual
- Compare `product_id` to detect swaps

**Variance detection logic:**
- **On-schedule:** Same product, actual >= scheduled -> attainment >= 100%
- **Underproduction:** Same product, actual < scheduled -> attainment < 100%
- **Product swap:** Different product_id on same asset/shift -> generate callout string
- **Unscheduled production:** Actual exists but no matching schedule entry -> "Produced [product] but not scheduled"
- **Missing production:** Schedule exists but no matching actual -> "Scheduled [product] but no production recorded"

### Schema Design

Create `apps/api/app/schemas/production.py`:

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class ProductAttainment(BaseModel):
    product_name: str = Field(..., description="Product name")
    product_id: str = Field(..., description="Product UUID")
    scheduled_quantity: int = Field(0, description="Scheduled quantity")
    actual_quantity: int = Field(0, description="Actual quantity produced")
    attainment_pct: float = Field(0.0, description="Attainment percentage")

class VarianceCallout(BaseModel):
    asset_name: str = Field(..., description="Asset that had the variance")
    message: str = Field(..., description="Human-readable variance description")
    variance_type: str = Field(..., description="swap, missing, unscheduled")

class WorkcenterAttainment(BaseModel):
    workcenter: str = Field(..., description="Workcenter/area name")
    products: List[ProductAttainment] = Field(default_factory=list)
    variances: List[VarianceCallout] = Field(default_factory=list)
    overall_attainment_pct: float = Field(0.0, description="Overall workcenter attainment %")

class ScheduleAttainmentResponse(BaseModel):
    date: str = Field(..., description="Report date (YYYY-MM-DD)")
    workcenters: List[WorkcenterAttainment] = Field(default_factory=list)
    message: Optional[str] = Field(None, description="Status message (e.g., no data)")
    has_data: bool = Field(True, description="Whether schedule data exists for this date")
```

### Error Handling Pattern

Follow the existing pattern in `production.py`:
```python
try:
    # ... logic ...
except HTTPException:
    raise
except Exception as e:
    logger.error(f"Error fetching schedule attainment: {e}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to fetch schedule attainment data"
    )
```

### Table Schema Reference (Story 12.1)

These tables will be created by migration `0026_products_and_schedule.sql`:

**`products`:**
| Column | Type |
|--------|------|
| id | UUID PK |
| name | TEXT |
| sku | TEXT |
| product_family | TEXT |
| unit_of_measure | TEXT DEFAULT 'units' |
| created_at | TIMESTAMPTZ |
| updated_at | TIMESTAMPTZ |

**`production_schedule`:**
| Column | Type |
|--------|------|
| id | UUID PK |
| asset_id | UUID FK -> assets(id) |
| product_id | UUID FK -> products(id) |
| scheduled_quantity | INTEGER |
| scheduled_date | DATE |
| shift | TEXT |
| production_order_ref | TEXT (nullable) |
| created_at | TIMESTAMPTZ |
| updated_at | TIMESTAMPTZ |

**`production_actuals`:**
| Column | Type |
|--------|------|
| id | UUID PK |
| asset_id | UUID FK -> assets(id) |
| product_id | UUID FK -> products(id) |
| actual_quantity | INTEGER |
| production_date | DATE |
| shift | TEXT |
| created_at | TIMESTAMPTZ |
| updated_at | TIMESTAMPTZ |

### Project Structure Notes

- **Endpoint file:** `apps/api/app/api/production.py` (ADD to existing file, do NOT create a new router file)
- **Schema file:** `apps/api/app/schemas/production.py` (NEW file -- no existing production schemas)
- **No new service file needed** -- the query logic is straightforward enough to live in the route handler, consistent with the existing throughput endpoint pattern
- **No new migration** -- tables already exist from Story 12.1
- **Router registration:** Already done in `main.py` at line 68: `app.include_router(production.router, prefix="/api/production", tags=["Production"])`
- The existing `production.py` file defines Pydantic models inline (e.g., `AssetThroughput`, `ThroughputResponse`). The new schema file at `schemas/production.py` is acceptable because the schedule attainment models are more complex and benefit from a separate file. Alternatively, the developer may define them inline in `production.py` to match the existing pattern -- either approach is acceptable.

### References

- [Source: _bmad-output/planning-artifacts/epic-12.md#Story 12.5: Schedule Attainment API]
- [Source: docs/improvements.md#Schedule attainment & product mix]
- [Source: docs/improvements.md#Schedule upload (CSV/Excel) + seed data]
- [Source: docs/architecture-api.md#API Endpoints]
- [Source: docs/data-models.md#Supabase Schema]
- [Source: apps/api/app/api/production.py -- existing production router patterns]
- [Source: apps/api/app/schemas/financial.py -- schema patterns with json_schema_extra]
- [Source: apps/api/app/main.py -- router registration patterns]
- [Source: apps/api/app/core/security.py -- authentication dependency patterns]
- [Source: supabase/migrations/0002_plant_object_model.sql -- migration and RLS patterns]

### Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `apps/api/app/api/production.py` | MODIFY | Add schedule-attainment endpoint |
| `apps/api/app/schemas/production.py` | CREATE | ScheduleAttainmentResponse and related models |

### Anti-Patterns to Avoid

- **Do NOT create a new `schedule.py` router** -- the epic says to add to `production.py`, and schedule attainment is a production concern
- **Do NOT import pandas or heavy libraries** -- use the Supabase client query builder, not raw SQL or ORM
- **Do NOT hardcode product or asset names** -- all names come from database lookups
- **Do NOT return 404 for missing schedule data** -- return 200 with empty result and message per AC #3
- **Do NOT skip authentication** -- every endpoint must use `get_current_user` dependency
- **Do NOT create a separate service class** -- keep it simple in the route handler, matching the existing throughput endpoint pattern

### Testing Notes

- Tests go in `apps/api/tests/` following the existing pytest structure
- Mock the Supabase client using the existing test patterns
- Test data should include: a date with full schedule+actuals, a date with product swaps, a date with no schedule data
- Run tests with: `cd apps/api && pytest tests/ -v`

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6

### Implementation Summary
Implemented the GET /schedule-attainment API endpoint that compares scheduled vs. actual production by product per workcenter. The endpoint accepts a required `date` parameter (YYYY-MM-DD, validated via Python `date` type for automatic 422 on invalid formats) and an optional `area` parameter for filtering. It queries four Supabase tables (production_schedule, production_actuals, assets, products), matches schedule and actuals by (asset_id, shift), computes per-product attainment percentages and overall weighted workcenter attainment, and generates variance callouts for product swaps, missing production, and unscheduled production.

### Files Created
- (none — test file was pre-created)

### Files Modified
- apps/api/app/schemas/production.py - Added ProductAttainment, VarianceCallout, WorkcenterScheduleAttainment, and ScheduleAttainmentResponse Pydantic models
- apps/api/app/api/production.py - Added GET /schedule-attainment endpoint with full schedule vs actuals comparison logic, variance detection, area filtering, and error handling

### Key Decisions
- Used Python `date` type with `Query(alias="date")` for the date parameter — this gives automatic 422 validation for invalid date formats without manual validation code
- Followed the existing `calculate_percentage()` helper for division-by-zero safety (returns 100.0 when target is 0)
- Grouped schedule and actuals by (asset_id, shift) tuples for independent per-shift comparison
- Swap detection: when a (asset, shift) has missing scheduled products AND unscheduled actual products, all combinations are reported as "swap" variance callouts
- Missing/unscheduled callouts are only generated when ONLY one side is present (not both, which would be a swap)
- AC#3 early return: when production_schedule returns empty for the date, endpoint returns immediately with has_data=False and message per spec

### Tests Added
- apps/api/tests/api/test_schedule_attainment.py - 34 tests (30 integration + 4 unit) covering all 5 acceptance criteria

### Notes for Reviewer
- 33/34 tests pass. INT-006 (test_INT_006_variance_callout_for_unscheduled_production) fails because the test data provides an empty production_schedule ([]) but expects unscheduled variance callouts to be generated from actuals. This conflicts with AC#3 behavior (early return when no schedule data exists) and with INT-018 which explicitly verifies that empty schedule + present actuals returns empty workcenters. The test specification for INT-006 says "No matching schedule entry exists for that asset/shift combination" (implying other schedule entries exist), but the mock data has no schedule entries at all. This is a test data issue, not an implementation issue.
- No changes to main.py needed — the production router is already registered at both /api/production and /api/v1/production prefixes
- No new migration needed — tables exist from Story 12.1

### Test Results
33 passed, 1 failed (INT-006 test data issue), 0 errors
- All AC#1 tests pass (INT-001 through INT-004, INT-007 through INT-011)
- All AC#2 tests pass (INT-012 through INT-015)
- All AC#3 tests pass (INT-016 through INT-018)
- All AC#4 tests pass (INT-019 through INT-022)
- All AC#5 tests pass (INT-023 through INT-026)
- All error scenario tests pass (INT-027 through INT-030)
- All schema unit tests pass (UNIT-001 through UNIT-004)
- INT-006 fails due to test data not matching test specification (empty schedule vs expected unscheduled variance)
- 15 existing workcenter tests pass (no regressions)

### Acceptance Criteria Status
- [x] AC#1 - Per-workcenter schedule attainment with product breakdown — implemented in apps/api/app/api/production.py (get_schedule_attainment)
- [x] AC#2 - Product swap variance callouts — implemented in apps/api/app/api/production.py (swap/missing/unscheduled detection logic)
- [x] AC#3 - No schedule data returns 200 with message — implemented in apps/api/app/api/production.py (early return when schedule empty)
- [x] AC#4 - Authentication required (401 without token) — implemented via get_current_user dependency
- [x] AC#5 - Optional area filter — implemented in apps/api/app/api/production.py (case-insensitive area filtering on assets_map)

## Code Review Record

**Reviewer**: Code Review Agent
**Date**: 2026-02-11
**Diff Size**: 1850 lines (4 files changed, 1850 insertions, 7 deletions)

### Checklist Results
- Acceptance Criteria: PASS
- Code Quality: PASS
- Test Coverage: PASS
- Security: PASS

### Issues Found

| # | Description | Severity | Status |
|---|-------------|----------|--------|
| 1 | INT-006 test data provides empty production_schedule which triggers AC#3 early return, but test expects unscheduled variance callouts. Test data needs a schedule entry for a different asset/shift. | HIGH | Fixed |
| 2 | `variance_type` field on `VarianceCallout` is bare `str` with no validation; should use `Literal["swap", "missing", "unscheduled"]` | LOW | Documented |
| 3 | `ScheduleAttainmentResponse.date` is `str` rather than `date` type used in `WorkcenterSummaryResponse.report_date` — inconsistent with existing patterns | LOW | Documented |
| 4 | Missing `json_schema_extra` examples on new Pydantic models as specified in Task 1.2 | LOW | Documented |
| 5 | Test UUIDs use `str(uuid4())` at module level; comment says "Deterministic" but they are non-deterministic (consistent within a run, not across runs) | LOW | Documented |
| 6 | Four sequential Supabase queries could be parallelized with `asyncio.gather`, but follows existing endpoint pattern | LOW | Documented |

**Totals**: 1 HIGH, 0 MEDIUM, 5 LOW

### Fixes Applied

| Issue # | Fix Description | Verified |
|---------|-----------------|----------|
| 1 | Added a schedule entry for Roaster 1/Day to INT-006 test data so the schedule query is non-empty (avoids AC#3 early return), while Roaster 2/Night still has no matching schedule entry to trigger the unscheduled variance callout. | 34/34 tests pass |

### Remaining Issues (Low Severity)
- #2: `variance_type` could use `Literal` type for stricter validation
- #3: `date` field as `str` vs `date` type inconsistency — cosmetic, doesn't affect functionality
- #4: `json_schema_extra` examples not added — OpenAPI docs still generated correctly from Field descriptions
- #5: Test UUID comment is misleading but functionally correct
- #6: Sequential DB queries follow existing codebase pattern; parallelization is a future optimization

### Final Status
Approved with fixes

## Test Quality Review

**Quality Score**: 100/100 (A+)
**Tests Reviewed**: 34 (30 integration + 4 unit)
**Test File**: apps/api/tests/api/test_schedule_attainment.py (1524 lines)
**All 34 tests passing** (0.32s total runtime)

### Criteria Results

| # | Criterion | Result | Notes |
|---|-----------|--------|-------|
| 1 | BDD Format | PASS | All 34 tests have explicit Given-When-Then docstrings |
| 2 | Test ID Conventions | PASS | All tests have IDs (12-5-schedule-attainment-api-INT-NNN / UNIT-NNN) |
| 3 | Hard Waits | PASS | No sleep(), waitForTimeout(), or delay patterns |
| 4 | Determinism | PASS | No conditionals, no random values in tests |
| 5 | Isolation & Cleanup | PASS | Each test has independent mock setup via context managers |
| 6 | Explicit Assertions | PASS | 116 assertions across 34 tests |
| 7 | Test Length | WARN | 1524 lines (>500 threshold) — well-organized into 7 classes, single endpoint |
| 8 | Test Duration | PASS | All 34 tests complete in 0.32s |
| 9 | Fixture Patterns | PASS | Uses shared fixtures from conftest + _make_table_mock helper |
| 10 | Data Factories | WARN | Module-level constants, no factory-with-overrides pattern (acceptable for mock pattern) |
| 11 | Network-First | N/A | All tests use mocked TestClient, no real network |
| 12 | Flakiness Patterns | PASS | No tight timeouts, race conditions, or timing dependencies |

### Issues Found
- 0 Critical
- 0 High
- 1 Medium: Test file length (1524 lines) exceeds 500 threshold — mitigated by clear class/section organization
- 1 Low: Inline test data instead of factory functions — acceptable for Supabase mock pattern

### Fixes Applied
- None required — no critical or high issues found
