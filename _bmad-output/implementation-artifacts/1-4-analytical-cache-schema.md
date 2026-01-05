# Story 1.4: Analytical Cache Schema

Status: ready-for-dev

## Story

As a **backend developer**,
I want **to create the analytical cache database schema in Supabase PostgreSQL**,
so that **the data pipelines can store processed T-1 daily summaries, T-15m live snapshots, and safety events for efficient querying by the frontend**.

## Acceptance Criteria

1. **daily_summaries table exists** with all required columns for storing T-1 processed reports including OEE metrics, waste data, and financial loss calculations
2. **live_snapshots table exists** with columns for 15-minute polling data including current output vs target, timestamp, and asset references
3. **safety_events table exists** as a persistent log with columns for safety incident tracking including timestamp, asset reference, reason code, severity, and resolution status
4. **All tables have proper foreign key relationships** to the assets table (created in Story 1.3)
5. **Appropriate indexes exist** for common query patterns (date ranges, asset lookups, status filters)
6. **Row Level Security (RLS) policies** are configured for authenticated user access
7. **Database migration file** is created and can be run successfully via Supabase CLI

## Tasks / Subtasks

- [ ] Task 1: Create daily_summaries table migration (AC: #1)
  - [ ] 1.1 Define table schema with id (UUID), asset_id (FK), report_date, oee_percentage, actual_output, target_output, downtime_minutes, waste_count, financial_loss_dollars, smart_summary_text, created_at, updated_at
  - [ ] 1.2 Add constraint for unique (asset_id, report_date) combination
  - [ ] 1.3 Create indexes on (report_date), (asset_id, report_date)

- [ ] Task 2: Create live_snapshots table migration (AC: #2)
  - [ ] 2.1 Define table schema with id (UUID), asset_id (FK), snapshot_timestamp, current_output, target_output, output_variance, status (enum: on_target, behind, ahead), created_at
  - [ ] 2.2 Create indexes on (snapshot_timestamp), (asset_id, snapshot_timestamp)
  - [ ] 2.3 Consider partitioning strategy for time-series data or TTL policy for ephemeral snapshots

- [ ] Task 3: Create safety_events table migration (AC: #3)
  - [ ] 3.1 Define table schema with id (UUID), asset_id (FK), event_timestamp, reason_code, severity (enum: low, medium, high, critical), description, is_resolved, resolved_at, resolved_by, created_at
  - [ ] 3.2 Add index on (event_timestamp), (asset_id, is_resolved), (severity)

- [ ] Task 4: Configure foreign key relationships (AC: #4)
  - [ ] 4.1 Add FK constraints referencing assets.id with ON DELETE CASCADE or RESTRICT as appropriate
  - [ ] 4.2 Verify referential integrity with test data

- [ ] Task 5: Configure Row Level Security (AC: #6)
  - [ ] 5.1 Enable RLS on all three tables
  - [ ] 5.2 Create policies for authenticated users to SELECT
  - [ ] 5.3 Create policies for service role to INSERT/UPDATE/DELETE (for backend pipelines)

- [ ] Task 6: Create and test migration (AC: #7)
  - [ ] 6.1 Generate migration file using Supabase CLI
  - [ ] 6.2 Test migration on local Supabase instance
  - [ ] 6.3 Verify rollback capability

## Dev Notes

### Architecture Constraints

- **Database Platform**: Supabase PostgreSQL 15+
- **Migration Tool**: Supabase CLI (`supabase migration new`, `supabase db push`)
- **Security Model**: Row Level Security (RLS) required for all user-facing tables
- **Naming Convention**: snake_case for tables and columns

### Data Flow Context

These tables serve as the **Analytical Cache** layer in the system architecture:
- **daily_summaries**: Populated by Pipeline A ("Morning Report") - daily batch at 06:00 AM via Railway Cron
- **live_snapshots**: Populated by Pipeline B ("Live Pulse") - 15-minute polling via Python Background Scheduler
- **safety_events**: Populated by Pipeline B when `reason_code = 'Safety Issue'` is detected

### Schema Design Rationale

From Architecture Document Section 5.B:
> **Analytical Cache (Supabase)**
> - **`daily_summaries`**: Stores the T-1 processed report (OEE, Waste, Financial Loss).
> - **`live_snapshots`**: Stores the latest 15-min poll data (ephemeral or time-series).
> - **`safety_events`**: Persistent log of all detected "Safety Issue" codes.

### Dependency on Story 1.3

This story requires the `assets` table from Story 1.3 (Plant Object Model Schema) to be completed first. The analytical cache tables reference `assets.id` via foreign keys.

### Project Structure Notes

- Migration files location: `apps/api/supabase/migrations/` (following TurboRepo structure)
- Alternative: If using Supabase project directly, migrations at project root
- Ensure migration naming follows timestamp convention: `YYYYMMDDHHMMSS_create_analytical_cache.sql`

### Technical Specifications

**daily_summaries table columns:**
```sql
id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
asset_id UUID NOT NULL REFERENCES assets(id),
report_date DATE NOT NULL,
oee_percentage DECIMAL(5,2),
actual_output INTEGER,
target_output INTEGER,
downtime_minutes INTEGER,
waste_count INTEGER,
financial_loss_dollars DECIMAL(12,2),
smart_summary_text TEXT,
created_at TIMESTAMPTZ DEFAULT NOW(),
updated_at TIMESTAMPTZ DEFAULT NOW(),
UNIQUE(asset_id, report_date)
```

**live_snapshots table columns:**
```sql
id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
asset_id UUID NOT NULL REFERENCES assets(id),
snapshot_timestamp TIMESTAMPTZ NOT NULL,
current_output INTEGER,
target_output INTEGER,
output_variance INTEGER GENERATED ALWAYS AS (current_output - target_output) STORED,
status TEXT CHECK (status IN ('on_target', 'behind', 'ahead')),
created_at TIMESTAMPTZ DEFAULT NOW()
```

**safety_events table columns:**
```sql
id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
asset_id UUID NOT NULL REFERENCES assets(id),
event_timestamp TIMESTAMPTZ NOT NULL,
reason_code TEXT NOT NULL,
severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
description TEXT,
is_resolved BOOLEAN DEFAULT FALSE,
resolved_at TIMESTAMPTZ,
resolved_by UUID REFERENCES auth.users(id),
created_at TIMESTAMPTZ DEFAULT NOW()
```

### NFR Compliance

- **NFR2 (Latency)**: live_snapshots indexes designed for fast temporal queries to support <60s data reflection
- **NFR3 (Read-Only)**: These tables are WRITE targets for the backend; source MSSQL remains read-only

### Testing Requirements

1. Migration applies successfully to clean Supabase instance
2. Migration rolls back cleanly
3. RLS policies correctly restrict anonymous access
4. RLS policies allow authenticated user SELECT
5. RLS policies allow service role full access
6. Foreign key constraints prevent orphan records
7. Unique constraint on daily_summaries(asset_id, report_date) enforced

### References

- [Source: _bmad/bmm/data/architecture.md#5. Data Models & Plant Object Model]
- [Source: _bmad/bmm/data/architecture.md#6. Data Pipelines]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 1]
- [Source: _bmad/bmm/data/prd.md#FR2 (Plant Object Model)]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
