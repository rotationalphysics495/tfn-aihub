# Story 2.7: Financial Impact Calculator

Status: ready-for-dev

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

- [ ] Task 1: Create Financial Impact Service Module (AC: #1, #2, #3, #4)
  - [ ] 1.1 Create `apps/api/app/services/financial.py` service module
  - [ ] 1.2 Implement `calculate_downtime_loss(asset_id, downtime_minutes)` function
  - [ ] 1.3 Implement `calculate_waste_loss(asset_id, waste_count, cost_per_unit=None)` function
  - [ ] 1.4 Implement `calculate_total_impact(asset_id, downtime_minutes, waste_count)` function
  - [ ] 1.5 Add cost_centers lookup with caching for performance

- [ ] Task 2: Create Financial API Endpoints (AC: #5)
  - [ ] 2.1 Create `apps/api/app/api/endpoints/financial.py` router
  - [ ] 2.2 Implement `GET /api/financial/impact/{asset_id}` endpoint
  - [ ] 2.3 Add query parameters for `start_date`, `end_date`, `period` (day/shift/hour)
  - [ ] 2.4 Implement response schema with Pydantic models
  - [ ] 2.5 Register router in main.py

- [ ] Task 3: Integrate with Morning Report Pipeline (AC: #6)
  - [ ] 3.1 Modify Pipeline A processing to call financial service after data aggregation
  - [ ] 3.2 Update `daily_summaries` INSERT to include `financial_loss_dollars`
  - [ ] 3.3 Add financial context to "Smart Summary" generation input

- [ ] Task 4: Integrate with Live Pulse Pipeline (AC: #7)
  - [ ] 4.1 Add accumulated financial loss calculation to Pipeline B
  - [ ] 4.2 Store current-shift financial impact in `live_snapshots` or dedicated field
  - [ ] 4.3 Ensure calculation resets appropriately per shift

- [ ] Task 5: Add Configuration and Error Handling (AC: #8)
  - [ ] 5.1 Add `DEFAULT_HOURLY_RATE` and `DEFAULT_COST_PER_UNIT` to environment config
  - [ ] 5.2 Implement graceful fallback when cost_centers data is missing
  - [ ] 5.3 Add logging for missing cost center warnings
  - [ ] 5.4 Add `is_estimated` flag to financial response models

- [ ] Task 6: Database Schema Updates (if needed) (AC: #6, #7)
  - [ ] 6.1 Verify `daily_summaries.financial_loss_dollars` column exists (from Story 1.4)
  - [ ] 6.2 Add `financial_loss_dollars` to `live_snapshots` if not present
  - [ ] 6.3 Create migration if schema changes needed

- [ ] Task 7: Write Tests (AC: All)
  - [ ] 7.1 Unit tests for financial calculation functions
  - [ ] 7.2 Unit tests for edge cases (zero values, missing data, null rates)
  - [ ] 7.3 Integration tests for API endpoints
  - [ ] 7.4 Integration tests for pipeline integration
  - [ ] 7.5 Test default rate fallback behavior

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

### Debug Log References

### Completion Notes List

### File List
