# Story 14.1: Downtime Events Data Model & Seed Data

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer**,
I want **a `downtime_events` table that stores individual downtime events with reason codes**,
so that **the system can display Pareto breakdowns of why downtime occurred, transforming vague "go look at Grinder 5" into "go look at why Grinder 5 had 45 minutes of mechanical downtime for the 3rd day in a row."**

## Acceptance Criteria

1. **Database Migration Creates Table**
   - Given the migration `supabase/migrations/0029_downtime_events.sql` runs successfully
   - When the database is queried
   - Then the `downtime_events` table exists with these columns:
     - `id` (UUID PK, DEFAULT gen_random_uuid())
     - `asset_id` (UUID FK to assets(id) ON DELETE CASCADE)
     - `event_date` (DATE NOT NULL)
     - `shift` (TEXT CHECK (shift IN ('morning', 'afternoon', 'night')))
     - `reason_code` (TEXT NOT NULL)
     - `reason_detail` (TEXT, freeform description)
     - `duration_minutes` (INTEGER NOT NULL)
     - `is_planned` (BOOLEAN DEFAULT false)
     - `source_system` (TEXT DEFAULT 'manual')
     - `source_event_id` (TEXT, nullable)
     - `created_at` (TIMESTAMPTZ DEFAULT NOW())
     - `updated_at` (TIMESTAMPTZ DEFAULT NOW())

2. **Indexes Exist for Query Performance**
   - Given the migration has run
   - When the database indexes are queried
   - Then indexes exist on: `asset_id`, `event_date`, `reason_code`
   - And a composite index exists on `(asset_id, event_date)` for the primary query pattern

3. **RLS Follows Existing Patterns**
   - Given RLS is enabled on `downtime_events`
   - When an authenticated user queries the table
   - Then they can SELECT all rows (read access)
   - And only the service_role can INSERT, UPDATE, DELETE
   - And policies follow the naming convention: "Allow authenticated read access on downtime_events" and "Allow service_role full access on downtime_events"

4. **Seed Data Aligns with Existing daily_summaries**
   - Given the seed script runs
   - When downtime events are queried for the past 7 days
   - Then realistic downtime events exist for assets that have downtime in `daily_summaries`
   - And the sum of event durations per asset per day approximately matches `daily_summaries.downtime_minutes`
   - And reason codes are distributed realistically (Mechanical highest, then Changeover, etc.)

5. **Standard Reason Codes Used**
   - Given seed data is inserted
   - When reason codes are queried
   - Then they use these standard values: "Mechanical", "Changeover", "Material Shortage", "Quality Hold", "Operator Unavailable", "Planned Maintenance"
   - And `is_planned` is `true` for "Planned Maintenance" and "Changeover", `false` for others

6. **Seed Data Covers Multiple Assets and Days**
   - Given the seed script runs
   - When downtime events are queried
   - Then events exist for at least 6 assets across 7+ days
   - And each day has 2-5 events per asset (matching the granularity of `downtime_reasons` JSONB in daily_summaries)
   - And events are distributed across shifts (morning, afternoon, night)

## Tasks / Subtasks

- [ ] Task 1: Create database migration (AC: #1, #2, #3)
  - [ ] 1.1 Create `supabase/migrations/0029_downtime_events.sql`
  - [ ] 1.2 Define `downtime_events` table with all columns per AC #1
  - [ ] 1.3 Add CHECK constraint on `shift` column: `('morning', 'afternoon', 'night')`
  - [ ] 1.4 Add `updated_at` auto-update trigger reusing existing `update_updated_at_column()` function
  - [ ] 1.5 Create indexes:
    - `idx_downtime_events_asset_id` on `(asset_id)`
    - `idx_downtime_events_event_date` on `(event_date)`
    - `idx_downtime_events_reason_code` on `(reason_code)`
    - `idx_downtime_events_asset_event_date` on `(asset_id, event_date)` (composite for Pareto queries)
  - [ ] 1.6 Enable RLS and create policies:
    - SELECT: `authenticated` users USING (true)
    - ALL: `service_role` full access USING (true) WITH CHECK (true)
  - [ ] 1.7 Add table and column COMMENTs for documentation

- [ ] Task 2: Add downtime events to seed script (AC: #4, #5, #6)
  - [ ] 2.1 Add `downtime_events` clear step at top of seed function (after existing clears)
  - [ ] 2.2 Generate downtime events for Grinder 5 (7 days + today) aligned to its `daily_summaries.downtime_reasons`
  - [ ] 2.3 Generate downtime events for Grinder 1 (7 days + today)
  - [ ] 2.4 Generate downtime events for Grinder 2 (7 days + today)
  - [ ] 2.5 Generate downtime events for Grinder 3 (7 days + today)
  - [ ] 2.6 Generate downtime events for Roaster 1 (7 days + today)
  - [ ] 2.7 Generate downtime events for Roaster 2 (7 days + today)
  - [ ] 2.8 Generate downtime events for Filler Line A (7 days + today)
  - [ ] 2.9 Generate downtime events for Packaging Line 1 (7 days + today)
  - [ ] 2.10 Insert downtime events via Supabase client using service role key
  - [ ] 2.11 Map `downtime_reasons` JSONB keys from daily_summaries to standard reason codes
  - [ ] 2.12 Distribute events across shifts and set `is_planned` appropriately

## Dev Notes

### Architecture Patterns

- **Database:** Supabase (PostgreSQL) with UUID primary keys, `gen_random_uuid()` for PK defaults
- **Migrations:** SQL files in `supabase/migrations/` with sequential numbering (current latest: 0025, reserved through 0028)
- **RLS:** All tables use Row Level Security with authenticated read + service_role full access
- **Seed Script:** Node.js (ESM) using `@supabase/supabase-js` client with service role key
- **Trigger Function:** `update_updated_at_column()` already exists from migration 0002 -- reuse it, DO NOT recreate

### Migration Design

The `downtime_events` table is a new entity that stores individual downtime event records, decomposing the aggregate `downtime_minutes` and `downtime_reasons` JSONB from `daily_summaries` into discrete, queryable rows. This enables:
- Pareto analysis by reason code (Story 14.3)
- Shift-level granularity (morning/afternoon/night)
- Planned vs. unplanned distinction
- Future Redzone integration via `source_system` and `source_event_id`

**Relationship to `daily_summaries.downtime_reasons`:** The existing `downtime_reasons` JSONB column (added in migration 0024) stores aggregated reason-to-minutes mappings. The new `downtime_events` table stores the same data at event-level granularity. Seed data MUST ensure consistency: `SUM(duration_minutes) WHERE asset_id=X AND event_date=Y` should approximately equal `daily_summaries.downtime_minutes` for that asset/date.

### Existing Migration Patterns to Follow Exactly

Follow `0025_action_followups.sql` and `0002_plant_object_model.sql` for:

```sql
-- Table creation with gen_random_uuid()
CREATE TABLE downtime_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ...
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index naming: idx_{table}_{column}
CREATE INDEX idx_downtime_events_asset_id ON downtime_events(asset_id);

-- Trigger reuse (DO NOT recreate the function)
CREATE TRIGGER update_downtime_events_updated_at
    BEFORE UPDATE ON downtime_events
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- RLS pattern
ALTER TABLE downtime_events ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow authenticated read access on downtime_events" ON downtime_events;
DROP POLICY IF EXISTS "Allow service_role full access on downtime_events" ON downtime_events;

CREATE POLICY "Allow authenticated read access on downtime_events"
    ON downtime_events FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Allow service_role full access on downtime_events"
    ON downtime_events FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
```

### Seed Data Design

**Reason Code Mapping:** The existing `daily_summaries` seed data uses freeform reason keys in `downtime_reasons` JSONB. Map them to the standard reason codes:

| daily_summaries Key | Standard Reason Code | is_planned |
|---------------------|---------------------|------------|
| "Mechanical Failure" | "Mechanical" | false |
| "Changeover" | "Changeover" | true |
| "Material Shortage" / "Material Issue" | "Material Shortage" | false |
| "Quality Hold" / "QA Hold" | "Quality Hold" | false |
| "Operator Unavailable" / "Operator Break" | "Operator Unavailable" | false |
| "Planned Maintenance" / "Cleanup" | "Planned Maintenance" | true |
| "Safety Stop" / "Inspection" | "Mechanical" | false |
| "Cooling System" / "Sensor Malfunction" / "Burner Issue" | "Mechanical" | false |
| "Valve Issue" / "Jam" / "Pressure Issue" | "Mechanical" | false |
| "Label Changeover" / "Startup Delay" | "Changeover" | true |
| "Case Erector Jam" / "Carton Issue" | "Mechanical" | false |
| "Chaff Collection" / "Calibration" | "Planned Maintenance" | true |

**Event Decomposition Strategy:** For each asset/day in `daily_summaries`, decompose the `downtime_reasons` JSONB entries into individual `downtime_events` rows. Each JSONB key-value pair becomes one event. Distribute across shifts:
- Most events in "morning" shift (primary production shift)
- Some in "afternoon" for higher-downtime days
- Occasional "night" shift events for 24/7 assets (Roasters)

**Asset IDs (from seed-data.mjs):**

| Asset | UUID |
|-------|------|
| Roaster 1 | a0000001-0000-0000-0000-000000000001 |
| Roaster 2 | a0000001-0000-0000-0000-000000000002 |
| Grinder 1 | a0000001-0000-0000-0000-000000000004 |
| Grinder 2 | a0000001-0000-0000-0000-000000000005 |
| Grinder 3 | a0000001-0000-0000-0000-000000000006 |
| Grinder 5 | a0000001-0000-0000-0000-000000000014 |
| Filler Line A | a0000001-0000-0000-0000-000000000008 |
| Packaging Line 1 | a0000001-0000-0000-0000-000000000011 |

**Seed Script Pattern:** Follow the existing pattern in `scripts/seed-data.mjs`:

```javascript
// Add after existing clear steps (around line 43)
await supabase.from('downtime_events').delete().neq('id', '00000000-0000-0000-0000-000000000000');
console.log('  ✓ Cleared downtime_events');

// Add after daily summaries section (around line 900)
console.log('🔧 Inserting downtime events...');
const downtimeEvents = [
  // Grinder 5 - daysAgo(1): 72 min total
  // Maps from downtime_reasons: { "Mechanical Failure": 35, "Changeover": 22, "Material Shortage": 15 }
  {
    asset_id: 'a0000001-0000-0000-0000-000000000014',
    event_date: daysAgo(1),
    shift: 'morning',
    reason_code: 'Mechanical',
    reason_detail: 'Burr assembly vibration causing uneven grind. Required adjustment.',
    duration_minutes: 35,
    is_planned: false,
    source_system: 'manual',
  },
  {
    asset_id: 'a0000001-0000-0000-0000-000000000014',
    event_date: daysAgo(1),
    shift: 'afternoon',
    reason_code: 'Changeover',
    reason_detail: 'Switched from medium to espresso grind profile.',
    duration_minutes: 22,
    is_planned: true,
    source_system: 'manual',
  },
  // ... continue for all assets and days
];

const { error: downtimeErr } = await supabase.from('downtime_events').insert(downtimeEvents);
if (downtimeErr) console.error('  Downtime events error:', downtimeErr.message);
else console.log(`  ✓ ${downtimeEvents.length} downtime events inserted`);
```

### Critical Guardrails

- **DO NOT** modify the existing `daily_summaries` table or its `downtime_reasons` column. The new `downtime_events` table is a parallel, event-level representation -- not a replacement.
- **DO NOT** recreate the `update_updated_at_column()` trigger function. It already exists from migration 0002. Only create the TRIGGER on the new table.
- **DO NOT** add any API endpoints or Pydantic schemas in this story. The API layer is Story 14.3.
- **DO NOT** use `gen_random_uuid()` for `source_event_id` -- this field is reserved for external system event IDs (e.g., future Redzone integration) and should be NULL for manually-seeded data.
- **DO** use `CREATE TABLE IF NOT EXISTS` for idempotency.
- **DO** use `DROP POLICY IF EXISTS` before `CREATE POLICY` for idempotency.
- **DO** use `CREATE INDEX IF NOT EXISTS` for idempotency.
- **DO** ensure seed data duration sums match `daily_summaries.downtime_minutes` per asset per day. Cross-reference the exact values from the existing `dailySummaries` array in `seed-data.mjs`.
- **DO** add the downtime_events clear/insert to the existing `seed()` function flow -- not as a separate script.
- **DO** keep the shift CHECK constraint values lowercase: `'morning'`, `'afternoon'`, `'night'`.
- **DO** add table-level COMMENT and column-level COMMENTs for all columns (project pattern from 0002 and 0003 migrations).

### Seed Data Cross-Reference (Grinder 5 Example)

The following shows how to decompose `daily_summaries` data into `downtime_events` for Grinder 5:

| Day | daily_summaries.downtime_minutes | downtime_reasons JSONB | downtime_events to Create |
|-----|---|----|---|
| daysAgo(0) | 48 | Mechanical Failure: 30, Material Shortage: 18 | 2 events (30 + 18 = 48) |
| daysAgo(1) | 72 | Mechanical Failure: 35, Changeover: 22, Material Shortage: 15 | 3 events (35 + 22 + 15 = 72) |
| daysAgo(2) | 45 | Mechanical Failure: 25, Operator Break: 20 | 2 events (25 + 20 = 45) |
| daysAgo(3) | 98 | Mechanical Failure: 55, Safety Stop: 28, Changeover: 15 | 3 events (55 + 28 + 15 = 98) |
| daysAgo(4) | 32 | Changeover: 18, Operator Break: 14 | 2 events (18 + 14 = 32) |
| daysAgo(5) | 58 | Material Shortage: 30, Mechanical Failure: 18, Cleanup: 10 | 3 events (30 + 18 + 10 = 58) |
| daysAgo(6) | 40 | Changeover: 25, Cleanup: 15 | 2 events (25 + 15 = 40) |
| daysAgo(7) | 52 | Mechanical Failure: 32, Operator Break: 20 | 2 events (32 + 20 = 52) |

Repeat this pattern for all 8 assets. The `reason_detail` field should contain realistic freeform descriptions (e.g., "Burr assembly vibration", "Bean hopper ran empty", "Espresso grind profile changeover").

### Project Structure Notes

```
supabase/migrations/
  0025_action_followups.sql          # REFERENCE - follow this pattern exactly
  0029_downtime_events.sql           # CREATE - new migration (this story)

scripts/
  seed-data.mjs                      # MODIFY - add downtime_events seed data
```

- No API files are created or modified in this story
- No frontend files are created or modified in this story
- This is a data-layer-only story

### References

- [Source: _bmad-output/planning-artifacts/epic-14.md#Story 14.1] - Story requirements, acceptance criteria, column definitions, and file list
- [Source: _bmad-output/planning-artifacts/epic-14.md#Overview] - Epic 14 goals: trend intelligence and downtime Pareto for targeted investigations
- [Source: supabase/migrations/0025_action_followups.sql] - Reference migration pattern for table creation, indexes, triggers, and RLS
- [Source: supabase/migrations/0002_plant_object_model.sql] - Foundation migration with `update_updated_at_column()` trigger function and COMMENT patterns
- [Source: supabase/migrations/0003_analytical_cache.sql] - `daily_summaries` table definition (the table whose data this story decomposes)
- [Source: supabase/migrations/0024_add_downtime_reasons.sql] - `downtime_reasons` JSONB column added to daily_summaries (the aggregate data this story granularizes)
- [Source: scripts/seed-data.mjs] - Existing seed script with asset IDs, daily_summaries data with downtime_reasons, and the insertion patterns to follow
- [Source: docs/data-models.md] - Database schema patterns, RLS conventions, and entity relationships
- [Source: docs/architecture-api.md] - Technology stack (Supabase PostgreSQL, supabase-py 2.0+)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
