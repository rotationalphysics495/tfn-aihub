# Story 2.7: Financial Impact Calculator

Status: Done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Plant Manager**,
I want **downtime and waste events translated into dollar values using cost_centers data**,
so that **I can understand the financial impact of operational issues and prioritize actions based on business value**.

## Acceptance Criteria

1. **Financial Impact Service Exists**
   - GIVEN the FastAPI backend is running
   - WHEN a financial impact calculation is requested
   - THEN a dedicated service calculates dollar values for downtime and waste
   - AND the calculation uses the `cost_centers.standard_hourly_rate` from Supabase

2. **Downtime Financial Calculation**
   - GIVEN downtime data with duration in minutes for an asset
   - WHEN the financial impact is calculated
   - THEN the system retrieves the asset's `standard_hourly_rate` from `cost_centers`
   - AND calculates: `financial_loss = (downtime_minutes / 60) * standard_hourly_rate`
   - AND stores the result in `daily_summaries.financial_loss_dollars`

3. **Waste/Scrap Financial Calculation**
   - GIVEN waste/scrap count data for an asset
   - WHEN the financial impact is calculated
   - THEN the system applies a configurable cost-per-unit multiplier (from cost_centers or env config)
   - AND adds waste-related losses to the total financial impact
   - AND the calculation formula is: `waste_loss = waste_count * cost_per_unit`

4. **Combined Financial Impact**
   - GIVEN both downtime and waste data exist for an asset/period
   - WHEN the total financial impact is calculated
   - THEN the system combines: `total_loss = downtime_loss + waste_loss`
   - AND returns a breakdown showing individual components

5. **API Endpoint for Financial Data**
   - GIVEN the API is running
   - WHEN a GET request is made to `/api/financial/impact/{asset_id}` with date parameters
   - THEN it returns JSON with: `downtime_loss`, `waste_loss`, `total_loss`, `currency`, `period`
   - AND the response includes the `standard_hourly_rate` used in calculation

6. **Batch Integration with Daily Pipeline**
   - GIVEN the Morning Report pipeline (Pipeline A) runs at 06:00 AM
   - WHEN T-1 data is processed
   - THEN financial impact is automatically calculated for each asset
   - AND results are stored in `daily_summaries.financial_loss_dollars`

7. **Live Integration with Polling Pipeline**
   - GIVEN the Live Pulse pipeline (Pipeline B) polls every 15 minutes
   - WHEN live data is processed
   - THEN accumulated financial impact for current shift is calculated
   - AND stored/updated in `live_snapshots` (or returned via API)

8. **Error Handling for Missing Cost Data**
   - GIVEN an asset without a corresponding `cost_centers` entry
   - WHEN financial calculation is attempted
   - THEN the system logs a warning
   - AND uses a configurable default hourly rate (env: `DEFAULT_HOURLY_RATE`)
   - AND marks the calculation as "estimated" in the response

## Tasks / Subtasks

- [x] Task 1: Create Financial Impact Service Module (AC: #1, #2, #3, #4)
  - [x] 1.1 Create `apps/api/app/services/financial.py` service module
  - [x] 1.2 Implement `calculate_downtime_loss(asset_id, downtime_minutes)` function
  - [x] 1.3 Implement `calculate_waste_loss(asset_id, waste_count, cost_per_unit=None)` function
  - [x] 1.4 Implement `calculate_total_impact(asset_id, downtime_minutes, waste_count)` function
  - [x] 1.5 Add cost_centers lookup with caching for performance

- [x] Task 2: Create Financial API Endpoints (AC: #5)
  - [x] 2.1 Create `apps/api/app/api/financial.py` router
  - [x] 2.2 Implement `GET /api/financial/impact/{asset_id}` endpoint
  - [x] 2.3 Add query parameters for `start_date`, `end_date`, `period` (day/shift/hour)
  - [x] 2.4 Implement response schema with Pydantic models
  - [x] 2.5 Register router in main.py

- [x] Task 3: Integrate with Morning Report Pipeline (AC: #6)
  - [x] 3.1 Modify Pipeline A processing to call financial service after data aggregation
  - [x] 3.2 Update `daily_summaries` INSERT to include `financial_loss_dollars`
  - [x] 3.3 Add financial context to "Smart Summary" generation input

- [x] Task 4: Integrate with Live Pulse Pipeline (AC: #7)
  - [x] 4.1 Add accumulated financial loss calculation to Pipeline B
  - [x] 4.2 Store current-shift financial impact in `live_snapshots` or dedicated field
  - [x] 4.3 Ensure calculation resets appropriately per shift

- [x] Task 5: Add Configuration and Error Handling (AC: #8)
  - [x] 5.1 Add `DEFAULT_HOURLY_RATE` and `DEFAULT_COST_PER_UNIT` to environment config
  - [x] 5.2 Implement graceful fallback when cost_centers data is missing
  - [x] 5.3 Add logging for missing cost center warnings
  - [x] 5.4 Add `is_estimated` flag to financial response models

- [x] Task 6: Database Schema Updates (if needed) (AC: #6, #7)
  - [x] 6.1 Verify `daily_summaries.financial_loss_dollars` column exists (from Story 1.4)
  - [x] 6.2 Add `financial_loss_dollars` to `live_snapshots` if not present
  - [x] 6.3 Create migration if schema changes needed

- [x] Task 7: Write Tests (AC: All)
  - [x] 7.1 Unit tests for financial calculation functions
  - [x] 7.2 Unit tests for edge cases (zero values, missing data, null rates)
  - [x] 7.3 Integration tests for API endpoints
  - [x] 7.4 Integration tests for pipeline integration
  - [x] 7.5 Test default rate fallback behavior

## Dev Notes

### Architecture Compliance

This story implements **FR5 (Financial Context)** from the PRD:
> "Translate operational losses (waste, downtime) into estimated dollar values using standard costs."

**Location:** `apps/api/` (Python FastAPI Backend)
- **Service Module:** `app/services/financial.py` - Core calculation logic
- **API Endpoints:** `app/api/endpoints/financial.py` - REST API
- **Pipeline Integration:** Modify existing Pipeline A and B services

### Technical Requirements

**Financial Calculation Formulas:**

```python
# Downtime loss calculation
def calculate_downtime_loss(downtime_minutes: int, hourly_rate: Decimal) -> Decimal:
    hours = Decimal(downtime_minutes) / Decimal(60)
    return hours * hourly_rate

# Waste loss calculation
def calculate_waste_loss(waste_count: int, cost_per_unit: Decimal) -> Decimal:
    return Decimal(waste_count) * cost_per_unit

# Total impact
def calculate_total_impact(downtime_loss: Decimal, waste_loss: Decimal) -> Decimal:
    return downtime_loss + waste_loss
```

**Response Schema Example:**

```python
from pydantic import BaseModel
from decimal import Decimal
from datetime import date
from typing import Optional

class FinancialImpactResponse(BaseModel):
    asset_id: str
    period_start: date
    period_end: date
    downtime_minutes: int
    downtime_loss: Decimal
    waste_count: int
    waste_loss: Decimal
    total_loss: Decimal
    currency: str = "USD"
    standard_hourly_rate: Decimal
    cost_per_unit: Decimal
    is_estimated: bool = False  # True if default rates used
```

### Data Model Dependencies

**From Story 1.3 (Plant Object Model) - cost_centers table:**
```sql
cost_centers:
  - id: UUID
  - asset_id: FK -> assets.id
  - standard_hourly_rate: Decimal (used for financial calc)
```

**From Story 1.4 (Analytical Cache) - daily_summaries table:**
```sql
daily_summaries:
  - financial_loss_dollars: DECIMAL(12,2)  # Target field for batch results
```

### Integration Points

1. **Pipeline A (Morning Report):**
   - Called AFTER OEE and downtime aggregation
   - Calculates T-1 financial impact per asset
   - Stores in `daily_summaries.financial_loss_dollars`
   - Feeds into "Smart Summary" text generation

2. **Pipeline B (Live Pulse):**
   - Calculates running financial impact for current shift
   - Updates every 15 minutes
   - Used by Live Pulse Ticker (Story 2.9) and Cost of Loss Widget (Story 2.8)

3. **Action Engine (Epic 3):**
   - Uses `financial_loss_dollars` for prioritization
   - Sort by Financial Impact ($) after Safety

### Environment Configuration

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DEFAULT_HOURLY_RATE` | Fallback hourly rate when cost_centers missing | No | 100.00 |
| `DEFAULT_COST_PER_UNIT` | Fallback cost per waste unit | No | 10.00 |
| `FINANCIAL_CURRENCY` | Display currency code | No | "USD" |

### Project Structure Notes

Files to create/modify:
```
apps/api/
├── app/
│   ├── services/
│   │   └── financial.py      # NEW: Financial calculation service
│   ├── api/
│   │   └── endpoints/
│   │       └── financial.py  # NEW: Financial API endpoints
│   ├── schemas/
│   │   └── financial.py      # NEW: Pydantic models for financial data
│   └── core/
│       └── config.py         # ADD: Default rate settings
├── requirements.txt          # Verify decimal handling libraries
└── .env.example              # ADD: Financial config vars
```

### NFR Compliance

- **NFR1 (Accuracy):** Calculations must use Decimal type for precision, not floats
- **NFR2 (Latency):** Financial calculations must complete within the 60-second data reflection window
- **NFR3 (Read-Only):** All source data from MSSQL remains read-only; calculations use cached data in Supabase

### Testing Strategy

1. **Unit Tests:**
   - Test calculation accuracy with known inputs
   - Test edge cases: zero downtime, zero waste, both zero
   - Test large numbers (precision verification)
   - Test missing cost_centers fallback

2. **Integration Tests:**
   - Test API endpoint with real Supabase data
   - Test pipeline integration (mock or test DB)
   - Verify `daily_summaries` is updated correctly

3. **Test Data Scenarios:**
   ```python
   # Scenario 1: Normal calculation
   asset_hourly_rate = Decimal("150.00")
   downtime_minutes = 45
   expected_loss = Decimal("112.50")  # (45/60) * 150

   # Scenario 2: With waste
   waste_count = 10
   cost_per_unit = Decimal("25.00")
   expected_waste_loss = Decimal("250.00")
   expected_total = Decimal("362.50")
   ```

### Dependencies

**Story Dependencies:**
- Story 1.3 (Plant Object Model Schema) - Provides `cost_centers` table
- Story 1.4 (Analytical Cache Schema) - Provides `daily_summaries.financial_loss_dollars` column
- Story 1.5 (MSSQL Read-Only Connection) - Source data connection
- Story 2.1 (Batch Data Pipeline) - Pipeline A integration point
- Story 2.2 (Polling Data Pipeline) - Pipeline B integration point

**Enables:**
- Story 2.8 (Cost of Loss Widget) - Uses this service for display
- Story 2.9 (Live Pulse Ticker) - Uses live financial context
- Epic 3 (Action Engine) - Uses financial impact for prioritization

### References

- [Source: _bmad/bmm/data/prd.md#FR5 (Financial Context)] - Functional requirement
- [Source: _bmad/bmm/data/architecture.md#5. Data Models - cost_centers] - Cost center schema
- [Source: _bmad/bmm/data/architecture.md#7. AI & Memory Architecture - Action Engine Logic] - Financial sorting
- [Source: _bmad-output/planning-artifacts/epic-2.md#Story 2.7] - Story definition
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 2] - Epic context

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Implementation Summary

Implemented the Financial Impact Calculator service and API endpoints for Story 2.7. The implementation provides financial impact calculations based on downtime and waste data, using cost_centers data from Supabase with configurable fallback defaults.

Key components:
1. **Financial Service Module** (`app/services/financial.py`) - Core calculation logic with Decimal precision
2. **Financial Schemas** (`app/schemas/financial.py`) - Pydantic models for API responses
3. **Financial API** (`app/api/financial.py`) - REST endpoints for financial data
4. **Pipeline Integration** - Updated both Morning Report and Live Pulse pipelines
5. **Configuration** - Added DEFAULT_HOURLY_RATE, DEFAULT_COST_PER_UNIT, FINANCIAL_CURRENCY settings

### Files Created/Modified

**Created:**
- `apps/api/app/services/financial.py` - Financial calculation service (AC #1, #2, #3, #4)
- `apps/api/app/schemas/__init__.py` - Schemas package init
- `apps/api/app/schemas/financial.py` - Pydantic response models (AC #5)
- `apps/api/app/api/financial.py` - REST API endpoints (AC #5)
- `apps/api/tests/test_financial_service.py` - Unit tests for financial service
- `apps/api/tests/test_financial_api.py` - Integration tests for API

**Modified:**
- `apps/api/app/main.py` - Added financial router registration
- `apps/api/app/core/config.py` - Added financial configuration settings (AC #8)
- `apps/api/.env.example` - Added financial environment variables
- `apps/api/app/services/pipelines/calculator.py` - Enhanced with cost_per_unit from cost_centers (AC #6)
- `apps/api/app/services/pipelines/live_pulse.py` - Added financial_loss_dollars to snapshots (AC #7)
- `apps/api/tests/test_pipeline_calculator.py` - Updated tests for new signature

### Key Decisions

1. **Decimal Precision**: Used Python's Decimal type for all financial calculations to ensure precision (NFR1)
2. **Caching Strategy**: Implemented 5-minute TTL cache for cost_centers data to minimize database queries
3. **Fallback Defaults**: Configurable via environment variables (DEFAULT_HOURLY_RATE=100.00, DEFAULT_COST_PER_UNIT=10.00)
4. **is_estimated Flag**: Added to all responses to indicate when default rates were used (AC #8)
5. **API Structure**: Created `/api/financial/impact/{asset_id}` for per-asset queries and `/api/financial/summary` for aggregated data

### Tests Added

- `test_financial_service.py` - 26 unit tests covering:
  - Downtime loss calculation (AC #2)
  - Waste loss calculation (AC #3)
  - Total impact calculation (AC #4)
  - Default rate fallback (AC #8)
  - Edge cases (zero values, negative values, large numbers)
  - Cache behavior
  - Pipeline integration methods

- `test_financial_api.py` - 13 integration tests covering:
  - API authentication requirements
  - Financial impact endpoint (AC #5)
  - Live financial impact endpoint
  - Financial summary endpoint
  - Date validation
  - Error handling

### Test Results

```
tests/test_financial_service.py: 26 passed
tests/test_financial_api.py: 13 passed
All existing tests: 435 passed
Total: 435 tests passed
```

### Notes for Reviewer

1. The Calculator class in `calculator.py` was modified to return tuples from `get_hourly_rate` and `get_cost_per_unit` to include `is_estimated` flag
2. The LiveSnapshotData class now includes `financial_loss_dollars` field for live financial tracking
3. The financial service uses a singleton pattern for efficient caching
4. All calculations use Decimal with 2 decimal place precision for currency values

### Acceptance Criteria Status

| AC | Status | File Reference |
|----|--------|----------------|
| #1 Financial Impact Service Exists | ✅ | `app/services/financial.py:48-412` |
| #2 Downtime Financial Calculation | ✅ | `app/services/financial.py:125-145` |
| #3 Waste/Scrap Financial Calculation | ✅ | `app/services/financial.py:147-169` |
| #4 Combined Financial Impact | ✅ | `app/services/financial.py:171-218` |
| #5 API Endpoint for Financial Data | ✅ | `app/api/financial.py:74-143` |
| #6 Batch Integration with Daily Pipeline | ✅ | `app/services/pipelines/calculator.py:366-422` |
| #7 Live Integration with Polling Pipeline | ✅ | `app/services/pipelines/live_pulse.py:294-336` |
| #8 Error Handling for Missing Cost Data | ✅ | `app/services/financial.py:85-123`, `app/core/config.py:44-47` |

### File List

```
apps/api/app/services/financial.py        # NEW - Financial service module
apps/api/app/schemas/__init__.py          # NEW - Schemas package
apps/api/app/schemas/financial.py         # NEW - Pydantic models
apps/api/app/api/financial.py             # NEW - API endpoints
apps/api/app/main.py                      # MODIFIED - Router registration
apps/api/app/core/config.py               # MODIFIED - Financial settings
apps/api/.env.example                     # MODIFIED - Env vars
apps/api/app/services/pipelines/calculator.py    # MODIFIED - Enhanced cost_per_unit
apps/api/app/services/pipelines/live_pulse.py    # MODIFIED - Financial in snapshots
apps/api/tests/test_financial_service.py  # NEW - Service tests
apps/api/tests/test_financial_api.py      # NEW - API tests
apps/api/tests/test_pipeline_calculator.py # MODIFIED - Updated for new API
```

## Code Review Record

**Reviewer**: Code Review Agent
**Date**: 2026-01-06

### Issues Found

| # | Description | Severity | Status |
|---|-------------|----------|--------|
| 1 | Unused import `List` in `app/api/financial.py:12` | LOW | Not fixed (per policy) |
| 2 | Unused imports `List`, `timedelta` in `app/services/financial.py:16,18` | LOW | Not fixed (per policy) |
| 3 | Import inside loop `from decimal import Decimal` in `app/api/financial.py:342` | LOW | Not fixed (per policy) |

**Totals**: 0 HIGH, 0 MEDIUM, 3 LOW

### Acceptance Criteria Verification

| AC | Description | Status | Evidence |
|----|-------------|--------|----------|
| #1 | Financial Impact Service Exists | ✅ PASS | `app/services/financial.py` with `FinancialService` class; 26 unit tests passing |
| #2 | Downtime Financial Calculation | ✅ PASS | `calculate_downtime_loss()` at line 216-238 implements formula; 5 tests in `TestDowntimeLossCalculation` |
| #3 | Waste/Scrap Financial Calculation | ✅ PASS | `calculate_waste_loss()` at line 240-261 implements formula; 4 tests in `TestWasteLossCalculation` |
| #4 | Combined Financial Impact | ✅ PASS | `calculate_total_impact()` at line 263-313; `FinancialImpactBreakdown` returns component breakdown |
| #5 | API Endpoint for Financial Data | ✅ PASS | `GET /api/financial/impact/{asset_id}` implemented; returns required JSON fields; 4 API tests |
| #6 | Batch Integration with Daily Pipeline | ✅ PASS | `calculator.py` enhanced with `get_hourly_rate()` and `get_cost_per_unit()` returning tuples |
| #7 | Live Integration with Polling Pipeline | ✅ PASS | `LiveSnapshotData.financial_loss_dollars` field added; `_calculate_financial_loss()` method in live_pulse.py |
| #8 | Error Handling for Missing Cost Data | ✅ PASS | `DEFAULT_HOURLY_RATE`, `DEFAULT_COST_PER_UNIT` in config; warning logged; `is_estimated` flag in responses |

### Test Results

```
tests/test_financial_service.py: 26 passed
tests/test_financial_api.py: 13 passed
tests/test_pipeline_calculator.py: 27 passed
Total: 66 tests passed, 0 failures
```

### Code Quality Assessment

- **Security**: All endpoints require authentication via `get_current_user` dependency. No SQL injection risks (uses Supabase client methods).
- **Patterns**: Follows existing codebase patterns for API structure, Supabase client usage, and error handling.
- **Decimal Precision**: Uses Python `Decimal` type for all financial calculations per NFR1 (Accuracy).
- **Caching**: 5-minute TTL cache for cost_centers data to minimize database queries.
- **Error Handling**: Graceful fallback to default rates with logging and `is_estimated` flag.

### Fixes Applied

None required - all issues are LOW severity. Per review policy, LOW severity issues are documented only.

### Remaining Issues

Low severity cleanup opportunities for future:
1. Remove unused `List` import from `app/api/financial.py`
2. Remove unused `List` and `timedelta` imports from `app/services/financial.py`
3. Move `from decimal import Decimal` import to top of file in `app/api/financial.py`

### Final Status

**Approved** - All acceptance criteria verified and passing. Implementation follows codebase patterns. No HIGH or MEDIUM severity issues found.
