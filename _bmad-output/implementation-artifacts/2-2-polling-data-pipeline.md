# Story 2.2: Polling Data Pipeline (T-15m)

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Plant Manager**,
I want **a polling data pipeline that fetches live production data every 15 minutes from MSSQL**,
so that **I can view near-real-time production status and receive immediate alerts for safety incidents as they happen during the shift**.

## Acceptance Criteria

1. **Background Scheduler Configuration**
   - GIVEN the FastAPI backend is running
   - WHEN the application starts
   - THEN a Python background scheduler (APScheduler) initializes
   - AND it schedules the polling job to run every 15 minutes
   - AND the first poll executes immediately on startup

2. **Data Polling Execution**
   - GIVEN an active MSSQL read-only connection (from Story 1.5)
   - WHEN the scheduled poll executes
   - THEN it fetches data from the last 30 minutes (rolling window) from MSSQL
   - AND it queries Output, OEE, Downtime, Quality, and Labor tables
   - AND it completes within 60 seconds (NFR2 latency requirement)

3. **Live Snapshots Storage**
   - GIVEN polled data from MSSQL
   - WHEN the data is processed
   - THEN it is written to the `live_snapshots` table in Supabase
   - AND the snapshot includes timestamp, asset_id, output_actual, output_target, oee_current
   - AND old snapshots beyond retention period are cleaned up (keep last 24h)

4. **Safety Incident Detection (FR4)**
   - GIVEN polled downtime data
   - WHEN any record has `reason_code = 'Safety Issue'`
   - THEN a safety event is immediately created in `safety_events` table
   - AND the event includes asset_id, timestamp, reason_code, and details
   - AND a log entry is created at WARNING level

5. **Output vs Target Calculation**
   - GIVEN polled output data
   - WHEN the snapshot is created
   - THEN output_actual is compared against shift_targets for each asset
   - AND variance_percent is calculated: `((actual - target) / target) * 100`
   - AND status is determined: 'on_target', 'below_target', 'above_target'

6. **Error Handling and Resilience**
   - GIVEN a scheduled poll execution
   - WHEN the poll encounters an error (connection timeout, query failure)
   - THEN the error is logged with full context
   - AND the scheduler continues running (single failure does not crash the service)
   - AND a retry is attempted on the next scheduled interval
   - AND metrics/health endpoint reflects the last successful poll timestamp

7. **Health and Monitoring**
   - GIVEN the polling pipeline is running
   - WHEN the `/health` endpoint is called
   - THEN it includes polling pipeline status (running/stopped)
   - AND last_poll_timestamp
   - AND last_poll_success (boolean)
   - AND next_poll_scheduled timestamp

## Tasks / Subtasks

- [ ] Task 1: Install APScheduler and Configure Dependencies (AC: #1)
  - [ ] Add APScheduler to requirements.txt
  - [ ] Add asyncio-compatible scheduler support
  - [ ] Document scheduler configuration options

- [ ] Task 2: Create Background Scheduler Module (AC: #1)
  - [ ] Create `apps/api/app/services/scheduler.py`
  - [ ] Implement AsyncIOScheduler initialization
  - [ ] Configure scheduler to start on FastAPI lifespan startup
  - [ ] Implement graceful shutdown on application termination

- [ ] Task 3: Implement MSSQL Data Fetcher (AC: #2)
  - [ ] Create `apps/api/app/services/pipelines/live_pulse.py`
  - [ ] Implement query for 30-minute rolling window data
  - [ ] Query Output data from MSSQL (actual production counts)
  - [ ] Query Downtime data (reason codes, duration)
  - [ ] Query current OEE metrics
  - [ ] Ensure all queries use read-only connection from Story 1.5

- [ ] Task 4: Implement Safety Event Detection (AC: #4)
  - [ ] Create safety event detection logic
  - [ ] Filter downtime records for `reason_code = 'Safety Issue'`
  - [ ] Insert detected events into `safety_events` table in Supabase
  - [ ] Add WARNING level logging for all safety detections
  - [ ] Implement deduplication to avoid duplicate alerts for same incident

- [ ] Task 5: Implement Live Snapshot Writer (AC: #3, #5)
  - [ ] Create Supabase client for `live_snapshots` table
  - [ ] Calculate output vs target variance
  - [ ] Determine status based on variance threshold (+/- 5%)
  - [ ] Write snapshot records to Supabase
  - [ ] Implement cleanup of old snapshots (24h retention)

- [ ] Task 6: Implement Scheduled Job (AC: #1, #2, #6)
  - [ ] Create the main polling job function
  - [ ] Wire together: fetch -> detect safety -> calculate metrics -> store
  - [ ] Add comprehensive error handling with try/catch
  - [ ] Ensure job failures don't crash scheduler
  - [ ] Add timing metrics for job execution

- [ ] Task 7: Update Health Endpoint (AC: #7)
  - [ ] Add polling pipeline status to health check
  - [ ] Track and expose last_poll_timestamp
  - [ ] Track and expose last_poll_success
  - [ ] Calculate and expose next_poll_scheduled

- [ ] Task 8: Write Tests (AC: All)
  - [ ] Unit tests for data transformation logic
  - [ ] Unit tests for safety detection
  - [ ] Integration tests for scheduler startup/shutdown
  - [ ] Mock tests for MSSQL data fetching
  - [ ] Test error handling scenarios

## Dev Notes

### Architecture Compliance

This story implements **Pipeline B: The "Live Pulse" (Polling)** from the Architecture document:

- **Location:** `apps/api/app/services/` (Python FastAPI Backend)
- **Pattern:** Background worker using APScheduler within the FastAPI process
- **Trigger:** Every 15 minutes via Python Background Scheduler
- **Data Flow:** MSSQL (read-only) -> Processing -> Supabase (write)

### Technical Requirements

**Scheduler Stack (APScheduler):**
```
FastAPI Lifespan -> APScheduler (AsyncIOScheduler) -> Job Functions -> MSSQL/Supabase
```

**APScheduler Configuration:**
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

scheduler = AsyncIOScheduler()

# Add the live pulse job
scheduler.add_job(
    live_pulse_poll,
    IntervalTrigger(minutes=15),
    id='live_pulse_poll',
    name='Live Pulse Data Pipeline',
    replace_existing=True,
    misfire_grace_time=60  # Allow 60 second grace for misfired jobs
)
```

**FastAPI Lifespan Integration:**
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    scheduler.start()
    yield
    # Shutdown
    scheduler.shutdown(wait=True)

app = FastAPI(lifespan=lifespan)
```

### Database Schema Requirements

**`live_snapshots` Table (Supabase):**
```sql
CREATE TABLE live_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID REFERENCES assets(id),
    snapshot_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    output_actual INTEGER NOT NULL,
    output_target INTEGER NOT NULL,
    variance_percent DECIMAL(5,2),
    status VARCHAR(20) CHECK (status IN ('on_target', 'below_target', 'above_target')),
    oee_current DECIMAL(5,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for efficient queries
CREATE INDEX idx_live_snapshots_timestamp ON live_snapshots(snapshot_timestamp DESC);
CREATE INDEX idx_live_snapshots_asset ON live_snapshots(asset_id);

-- Cleanup policy (RLS or scheduled function)
-- Keep only last 24 hours
```

**`safety_events` Table (Supabase) - Reference from Story 1.4:**
```sql
-- Verify this table exists from Analytical Cache Schema (Story 1.4)
-- Fields needed: id, asset_id, event_timestamp, reason_code, details, acknowledged
```

### NFR Compliance

**NFR2 (Latency - 60 seconds):**
- Poll execution must complete within 60 seconds
- Add timeout configuration to MSSQL queries
- Monitor and log execution times
- Alert if poll exceeds 45 second warning threshold

**NFR3 (Read-Only MSSQL):**
- All MSSQL queries use the read-only connection from Story 1.5
- No write operations to MSSQL - only Supabase
- Connection reuses existing pool configuration

### MSSQL Query Templates

**Rolling Window Query (30 minutes):**
```sql
-- Example query structure - adapt to actual MSSQL schema
SELECT
    locationName as asset_source_id,
    SUM(output_count) as output_actual,
    MAX(timestamp) as last_reading
FROM production_data
WHERE timestamp >= DATEADD(MINUTE, -30, GETDATE())
GROUP BY locationName;
```

**Downtime with Safety Detection:**
```sql
SELECT
    locationName as asset_source_id,
    reason_code,
    downtime_minutes,
    timestamp,
    notes
FROM downtime_records
WHERE timestamp >= DATEADD(MINUTE, -30, GETDATE())
    AND reason_code = 'Safety Issue';
```

### Project Structure Notes

**Files to create/modify:**
```
apps/api/
├── app/
│   ├── services/
│   │   ├── scheduler.py           # NEW: APScheduler setup
│   │   └── pipelines/
│   │       └── live_pulse.py      # NEW: Live Pulse pipeline logic
│   ├── api/
│   │   └── health.py              # MODIFY: Add pipeline status
│   └── main.py                    # MODIFY: Add scheduler lifespan
├── requirements.txt               # MODIFY: Add APScheduler
└── tests/
    └── services/
        └── test_live_pulse.py     # NEW: Pipeline tests
```

### Dependencies

**Story Dependencies:**
- Story 1.5 (MSSQL Read-Only Connection) - REQUIRED for database access
- Story 1.4 (Analytical Cache Schema) - REQUIRED for `live_snapshots` and `safety_events` tables
- Story 1.3 (Plant Object Model Schema) - REQUIRED for `assets` and `shift_targets` tables

**Blocked By:**
- Epic 1 must be substantially complete
- MSSQL connection must be verified working
- Supabase tables must exist

**Enables:**
- Story 2.3 (Throughput Dashboard) - Uses `live_snapshots` data
- Story 2.6 (Safety Alert System) - Uses `safety_events` data
- Story 2.9 (Live Pulse Ticker) - Uses `live_snapshots` data

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `POLL_INTERVAL_MINUTES` | Polling frequency | No | 15 |
| `POLL_WINDOW_MINUTES` | Rolling window for queries | No | 30 |
| `SNAPSHOT_RETENTION_HOURS` | How long to keep snapshots | No | 24 |
| `POLL_TIMEOUT_SECONDS` | Maximum poll execution time | No | 60 |

### Error Handling Strategy

1. **Connection Errors:**
   - Log full error with traceback
   - Continue scheduler - retry on next interval
   - Update health status to reflect failure

2. **Query Timeouts:**
   - Configured via SQLAlchemy execution options
   - Log timeout with query context
   - Partial data should not be written

3. **Data Validation Errors:**
   - Log malformed records but continue processing valid ones
   - Track error counts in metrics

4. **Supabase Write Failures:**
   - Implement retry with exponential backoff (3 attempts)
   - Log failures for investigation
   - Do not lose safety events - queue for retry if needed

### Testing Strategy

1. **Unit Tests:**
   - Test data transformation functions (variance calculation, status determination)
   - Test safety event detection logic
   - Test snapshot cleanup logic

2. **Integration Tests:**
   - Test scheduler startup and job registration
   - Test graceful shutdown behavior
   - Test job execution with mocked database responses

3. **Mock Tests:**
   - Mock MSSQL responses for various data scenarios
   - Mock Supabase client for write operations
   - Test error scenarios (timeouts, connection failures)

4. **Manual Testing:**
   - Verify actual data flow from dev MSSQL to Supabase
   - Confirm 15-minute polling interval
   - Test safety event detection with test data
   - Verify health endpoint reflects pipeline status

### Performance Considerations

- Use connection pooling (already configured in Story 1.5)
- Limit query result sets with TOP/LIMIT clauses
- Use parameterized queries to leverage query plan caching
- Consider batch inserts for multiple snapshots
- Monitor memory usage during poll execution

### References

- [Source: _bmad/bmm/data/architecture.md#6. Data Pipelines] - Pipeline B specification
- [Source: _bmad/bmm/data/architecture.md#5. Data Models] - live_snapshots, safety_events tables
- [Source: _bmad/bmm/data/prd.md#Non-Functional] - NFR2 (60 second latency), NFR3 (read-only)
- [Source: _bmad/bmm/data/prd.md#Functional] - FR1 (Data Ingestion), FR4 (Safety Alerting)
- [Source: _bmad-output/planning-artifacts/epic-2.md#Story 2.2] - Story definition
- [Source: _bmad-output/implementation-artifacts/1-5-mssql-readonly-connection.md] - MSSQL connection implementation

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

### Completion Notes List

### File List
