# Story 2.1: Batch Data Pipeline (T-1)

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Plant Manager**,
I want **a daily batch pipeline that automatically fetches yesterday's production data from MSSQL at 06:00 AM**,
so that **I can view the "Morning Report" with complete OEE metrics, throughput analysis, and financial impact when I start my shift**.

## Acceptance Criteria

1. **Railway Cron Job Configuration**
   - GIVEN the Railway deployment is active
   - WHEN the system clock reaches 06:00 AM local time
   - THEN a Railway Cron job triggers the batch pipeline execution
   - AND the trigger is logged with timestamp for audit purposes

2. **MSSQL Data Extraction (T-1)**
   - GIVEN the batch pipeline is triggered
   - WHEN the pipeline executes data extraction
   - THEN it queries MSSQL for the previous day's data (T-1, full 24-hour window)
   - AND uses the read-only MSSQL connection established in Story 1.5
   - AND extracts data for Output, OEE components, Downtime, Quality, and Labor
   - AND handles data extraction failures gracefully with retry logic

3. **Data Cleansing and Transformation**
   - GIVEN raw data is extracted from MSSQL
   - WHEN the transformation step runs
   - THEN NULL values are handled appropriately (defaulted or excluded)
   - AND zero values are validated (distinguish between "0" output vs missing data)
   - AND timestamps are normalized to consistent timezone (plant local time)
   - AND asset data is mapped to Plant Object Model `assets` table via `source_id`

4. **OEE Calculation**
   - GIVEN cleansed production data is available
   - WHEN OEE metrics are calculated
   - THEN the formula uses: OEE = Availability x Performance x Quality
   - AND Availability = (Run Time / Planned Production Time)
   - AND Performance = (Actual Output / Theoretical Maximum Output)
   - AND Quality = (Good Units / Total Units Produced)
   - AND each component is stored separately for drill-down analysis

5. **Financial Loss Calculation**
   - GIVEN OEE and downtime data is calculated
   - WHEN financial impact is computed
   - THEN downtime minutes are multiplied by `cost_centers.standard_hourly_rate / 60`
   - AND waste/scrap units are valued using standard cost per unit
   - AND total financial loss is aggregated per asset and per cost center

6. **Daily Summary Storage**
   - GIVEN all calculations are complete
   - WHEN the pipeline stores results
   - THEN data is written to `daily_summaries` table in Supabase
   - AND the record includes: date, asset_id, oee_overall, oee_availability, oee_performance, oee_quality, output_actual, output_target, downtime_minutes, financial_loss_dollars, created_at
   - AND existing records for the same date/asset are updated (upsert pattern)

7. **Safety Event Detection**
   - GIVEN downtime data is being processed
   - WHEN a record contains `reason_code = 'Safety Issue'` (or configured equivalent)
   - THEN an entry is created in `safety_events` table
   - AND the entry includes: asset_id, timestamp, duration_minutes, description, severity='critical', created_at
   - AND safety events trigger alert flag for FR4 Safety Alerting

8. **Pipeline Execution Logging**
   - GIVEN the pipeline runs (success or failure)
   - WHEN execution completes
   - THEN a log entry is created with: start_time, end_time, status, records_processed, errors_encountered
   - AND failures include detailed error messages for debugging
   - AND logs are accessible via API for monitoring

9. **Idempotency and Re-run Safety**
   - GIVEN the pipeline may need to be re-run (manual trigger or failure recovery)
   - WHEN the same date is processed multiple times
   - THEN the result is identical (idempotent execution)
   - AND no duplicate records are created
   - AND previous data for that date is cleanly replaced

## Tasks / Subtasks

- [ ] Task 1: Create Pipeline Service Structure (AC: #1, #8)
  - [ ] Create `apps/api/app/services/pipelines/` directory
  - [ ] Create `apps/api/app/services/pipelines/__init__.py`
  - [ ] Create `apps/api/app/services/pipelines/morning_report.py` - main pipeline orchestrator
  - [ ] Create `apps/api/app/services/pipelines/data_extractor.py` - MSSQL query logic
  - [ ] Create `apps/api/app/services/pipelines/transformer.py` - cleansing and transformation
  - [ ] Create `apps/api/app/services/pipelines/calculator.py` - OEE and financial calculations

- [ ] Task 2: Implement MSSQL Data Extraction (AC: #2)
  - [ ] Define SQL queries for T-1 production data extraction
  - [ ] Create parameterized date range queries (start_date, end_date)
  - [ ] Implement extraction for each data domain (Output, Downtime, Quality, Labor)
  - [ ] Use existing MSSQL connection from `app/core/database.py` (Story 1.5)
  - [ ] Implement retry logic with exponential backoff (3 retries, 1s/2s/4s)

- [ ] Task 3: Implement Data Transformation (AC: #3)
  - [ ] Create data cleansing functions for NULL handling
  - [ ] Implement timestamp normalization to plant local timezone
  - [ ] Create asset mapping function (MSSQL `locationName` -> Supabase `assets.source_id`)
  - [ ] Handle zero-value validation (distinguish actual zero vs missing)
  - [ ] Create Pydantic models for validated pipeline data structures

- [ ] Task 4: Implement OEE Calculator (AC: #4)
  - [ ] Create OEE calculation service with component breakdown
  - [ ] Implement Availability calculation (handle edge cases: no planned time)
  - [ ] Implement Performance calculation (handle edge cases: zero output)
  - [ ] Implement Quality calculation (handle edge cases: no production)
  - [ ] Unit test all edge cases and boundary conditions

- [ ] Task 5: Implement Financial Calculator (AC: #5)
  - [ ] Create financial loss calculation service
  - [ ] Query `cost_centers` table for hourly rates
  - [ ] Calculate downtime cost (minutes * hourly_rate / 60)
  - [ ] Calculate waste cost (scrap_units * unit_cost)
  - [ ] Aggregate totals per asset and per cost center

- [ ] Task 6: Implement Daily Summary Storage (AC: #6, #9)
  - [ ] Create Supabase upsert function for `daily_summaries`
  - [ ] Implement idempotent write (ON CONFLICT UPDATE)
  - [ ] Create Pydantic model for `DailySummary` schema
  - [ ] Verify table schema matches Story 1.4 Analytical Cache

- [ ] Task 7: Implement Safety Event Detection (AC: #7)
  - [ ] Create safety event detection during downtime processing
  - [ ] Configure safety reason code pattern (env var or config)
  - [ ] Create Supabase insert for `safety_events` table
  - [ ] Set severity='critical' for all safety incidents

- [ ] Task 8: Create Pipeline Orchestrator (AC: #1, #8, #9)
  - [ ] Create main `run_morning_report()` function
  - [ ] Implement pipeline step orchestration with error handling
  - [ ] Create execution logging (start/end times, status, counts)
  - [ ] Implement graceful failure with partial completion tracking
  - [ ] Add manual trigger capability via API endpoint

- [ ] Task 9: Configure Railway Cron (AC: #1)
  - [ ] Add cron configuration to Railway service (railway.json or dashboard)
  - [ ] Set schedule: "0 6 * * *" (06:00 AM daily)
  - [ ] Create cron entry point script/command
  - [ ] Document Railway Cron setup in README

- [ ] Task 10: Create API Endpoints (AC: #8)
  - [ ] Create `POST /api/pipelines/morning-report/trigger` - manual trigger
  - [ ] Create `GET /api/pipelines/morning-report/status` - last run status
  - [ ] Create `GET /api/pipelines/morning-report/logs` - execution history
  - [ ] Protect endpoints with authentication (Supabase JWT)

- [ ] Task 11: Write Tests (AC: All)
  - [ ] Unit tests for OEE calculations (all edge cases)
  - [ ] Unit tests for financial calculations
  - [ ] Unit tests for data transformation/cleansing
  - [ ] Integration test for full pipeline (mock MSSQL data)
  - [ ] Test idempotency (multiple runs same date)

## Dev Notes

### Architecture Compliance

This story implements **Pipeline A: The "Morning Report"** from the architecture document. It is the first data pipeline story and establishes patterns for Epic 2.

**Location:** `apps/api/` (Python FastAPI Backend)
**Module:** `app/services/pipelines/` for pipeline logic
**Pattern:** Service-layer orchestration with dependency injection

### Technical Requirements

**Pipeline Architecture:**
```
Railway Cron (06:00 AM)
    |
    v
morning_report.py (Orchestrator)
    |
    +---> data_extractor.py (MSSQL Queries)
    |         |
    |         v
    |     [Raw Data]
    |
    +---> transformer.py (Cleanse & Map)
    |         |
    |         v
    |     [Clean Data]
    |
    +---> calculator.py (OEE & Financial)
    |         |
    |         v
    |     [Calculated Metrics]
    |
    +---> Supabase Write
          - daily_summaries (upsert)
          - safety_events (insert)
```

**OEE Calculation Reference:**
```python
# OEE = Availability x Performance x Quality

# Availability
run_time = planned_production_time - downtime
availability = run_time / planned_production_time  # Handle div by zero

# Performance
performance = actual_output / (run_time * ideal_cycle_rate)  # Handle div by zero

# Quality
quality = good_units / total_units  # Handle div by zero

# Overall OEE (as decimal 0-1, display as percentage)
oee = availability * performance * quality
```

**Financial Calculation Reference:**
```python
# Downtime Cost
downtime_cost = downtime_minutes * (hourly_rate / 60)

# Waste Cost
waste_cost = scrap_units * unit_cost

# Total Loss
total_loss = downtime_cost + waste_cost
```

### Database Schema Reference (from Story 1.4)

**daily_summaries table:**
```sql
CREATE TABLE daily_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL,
    asset_id UUID NOT NULL REFERENCES assets(id),
    oee_overall DECIMAL(5,4),  -- 0.0000 to 1.0000
    oee_availability DECIMAL(5,4),
    oee_performance DECIMAL(5,4),
    oee_quality DECIMAL(5,4),
    output_actual INTEGER,
    output_target INTEGER,
    downtime_minutes INTEGER,
    financial_loss_dollars DECIMAL(10,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(date, asset_id)
);
```

**safety_events table:**
```sql
CREATE TABLE safety_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES assets(id),
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_minutes INTEGER,
    reason_code VARCHAR(100),
    description TEXT,
    severity VARCHAR(20) DEFAULT 'critical',
    acknowledged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### MSSQL Query Patterns

**CRITICAL:** All queries must be SELECT only (NFR3 Read-Only compliance).

**Example T-1 Query Pattern:**
```python
from datetime import date, timedelta

yesterday = date.today() - timedelta(days=1)
start_datetime = datetime.combine(yesterday, time.min)  # 00:00:00
end_datetime = datetime.combine(yesterday, time.max)    # 23:59:59

# Query production output
query = """
SELECT
    locationName as source_id,
    production_date,
    units_produced,
    units_scrapped,
    planned_units
FROM production_output
WHERE production_date >= :start_date
  AND production_date <= :end_date
"""
```

### Railway Cron Configuration

**railway.json:**
```json
{
  "build": {
    "builder": "DOCKERFILE"
  },
  "deploy": {
    "cronSchedule": "0 6 * * *"
  }
}
```

**Alternative: Railway Dashboard**
1. Go to Service Settings
2. Under "Cron", set schedule: `0 6 * * *`
3. Set command: `python -m app.services.pipelines.morning_report`

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `PIPELINE_TIMEZONE` | Plant local timezone | No | "America/Chicago" |
| `SAFETY_REASON_CODE` | Pattern for safety incidents | No | "Safety Issue" |
| `PIPELINE_RETRY_COUNT` | Max retries on failure | No | 3 |
| `PIPELINE_LOG_LEVEL` | Logging verbosity | No | "INFO" |

### Project Structure Notes

**Files to create:**
```
apps/api/
├── app/
│   ├── services/
│   │   └── pipelines/
│   │       ├── __init__.py
│   │       ├── morning_report.py   # Orchestrator
│   │       ├── data_extractor.py   # MSSQL queries
│   │       ├── transformer.py      # Data cleansing
│   │       └── calculator.py       # OEE & financial
│   ├── api/
│   │   └── pipelines.py            # API endpoints
│   └── models/
│       └── pipeline.py             # Pydantic models
```

**Dependencies to add to requirements.txt:**
- `apscheduler` (optional, for local testing without Railway Cron)
- `tenacity` (for retry logic with exponential backoff)

### Dependencies

**Story Dependencies:**
- Story 1.1 (TurboRepo Monorepo Scaffold) - Must have FastAPI structure
- Story 1.4 (Analytical Cache Schema) - Must have `daily_summaries`, `safety_events` tables
- Story 1.5 (MSSQL Read-Only Connection) - Must have working MSSQL connection

**Blocked By:** Stories 1.1, 1.4, 1.5 must be complete

**Enables:**
- Story 2.2 (Polling Pipeline T-15m) - Shares extraction patterns
- Story 2.3 (Throughput Dashboard) - Consumes `daily_summaries` data
- Story 2.4 (OEE Metrics View) - Consumes OEE calculations
- Story 2.6 (Safety Alert System) - Consumes `safety_events` data
- Story 2.7 (Financial Impact Calculator) - Extends financial calculations
- Epic 3 (Action Engine) - Uses `daily_summaries` and `safety_events`

### Testing Strategy

1. **Unit Tests:**
   - OEE calculations with edge cases (zero values, null handling)
   - Financial calculations with various cost center configurations
   - Data transformation functions
   - Asset mapping logic

2. **Integration Tests:**
   - Mock MSSQL data extraction
   - Full pipeline execution with test database
   - Verify Supabase writes are correct
   - Test idempotency (run twice, same result)

3. **Manual Testing:**
   - Trigger pipeline via API endpoint
   - Verify data appears in `daily_summaries`
   - Test with actual MSSQL connection (dev environment)
   - Verify Railway Cron triggers correctly

### Error Handling Patterns

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4)
)
async def extract_production_data(date: date) -> List[ProductionRecord]:
    """Extract with automatic retry on transient failures."""
    try:
        # ... extraction logic
    except SQLAlchemyError as e:
        logger.error(f"MSSQL extraction failed: {e}")
        raise  # Will trigger retry
```

### NFR Compliance

- **NFR1 (Accuracy):** OEE calculations use industry-standard formulas with proper edge case handling
- **NFR2 (Latency):** Batch pipeline has no latency requirement (runs at 06:00 AM)
- **NFR3 (Read-Only):** All MSSQL operations are SELECT queries only

### References

- [Source: _bmad/bmm/data/architecture.md#6. Data Pipelines] - Pipeline A specification
- [Source: _bmad/bmm/data/architecture.md#5. Data Models] - daily_summaries, safety_events schemas
- [Source: _bmad/bmm/data/prd.md#Functional] - FR1 Data Ingestion requirement
- [Source: _bmad-output/planning-artifacts/epic-2.md] - Epic 2 context
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 2] - Story scope

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

### Completion Notes List

### File List
