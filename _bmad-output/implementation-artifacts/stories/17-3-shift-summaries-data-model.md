# Story 17.3: Shift Summaries Data Model

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want shift-level performance data alongside the existing daily aggregates,
so that the report can show which shift contributed to a daily miss.

## Acceptance Criteria

1. **Given** the migration runs successfully **When** the database is queried **Then** the `shift_summaries` table exists with all specified columns: `id` (UUID PK), `asset_id` (UUID FK to assets), `date` (DATE), `shift` (TEXT with CHECK constraint for 'morning', 'afternoon', 'night'), `oee` (DECIMAL(5,2)), `availability` (DECIMAL(5,2)), `performance` (DECIMAL(5,2)), `quality` (DECIMAL(5,2)), `downtime_minutes` (INTEGER), `units_produced` (INTEGER), `created_at` (TIMESTAMPTZ).

2. **Given** the migration runs successfully **When** the constraints are inspected **Then** a unique constraint exists on `(asset_id, date, shift)` preventing duplicate records for the same asset, date, and shift combination.

3. **Given** the migration runs successfully **When** the indexes are inspected **Then** indexes exist on `asset_id` and `date` for query performance, plus a composite index on `(asset_id, date)` for the most common query pattern.

4. **Given** the migration runs successfully **When** RLS policies are inspected **Then** RLS is enabled on `shift_summaries` with policies matching the existing `daily_summaries` pattern: authenticated users can SELECT, service_role has full access (INSERT, UPDATE, DELETE, SELECT).

5. **Given** the seed script runs **When** shift summaries are queried **Then** each asset has 3 shift records per day (morning, afternoon, night) for the same date range as existing `daily_summaries` seed data (7 days + today).

6. **Given** the seed script runs **When** shift summary values are aggregated per asset per day **Then** the sum of shift `units_produced` approximately matches the `daily_summaries.actual_output` for the same asset and date, and weighted-average shift OEE approximately matches `daily_summaries.oee_percentage`.

7. **Given** the seed script runs **When** individual shift records are examined **Then** shifts have realistic variance (e.g., afternoon shift shows lower performance on some assets, night shift shows different patterns) rather than uniform distribution.

8. **Given** the existing `daily_summaries` table and all views that query it **When** the migration and seed run **Then** existing daily views continue working unchanged with no schema or data modifications to `daily_summaries`.

## Tasks / Subtasks

- [ ] Task 1: Create Supabase migration file (AC: #1, #2, #3, #4, #8)
  - [ ] 1.1 Create `supabase/migrations/0032_shift_summaries.sql`
  - [ ] 1.2 Define `shift_summaries` table with all columns per AC #1
  - [ ] 1.3 Add unique constraint on `(asset_id, date, shift)`
  - [ ] 1.4 Add indexes on `asset_id`, `date`, and composite `(asset_id, date)`
  - [ ] 1.5 Enable RLS with policies matching `daily_summaries` pattern
  - [ ] 1.6 Add table and column comments for documentation
  - [ ] 1.7 Add verification queries as SQL comments at bottom of migration

- [ ] Task 2: Add shift-level seed data to `scripts/seed-data.mjs` (AC: #5, #6, #7)
  - [ ] 2.1 Create shift distribution helper function
  - [ ] 2.2 Generate 3 shift records per asset per day from existing daily summaries data
  - [ ] 2.3 Ensure shift totals approximately match daily aggregates
  - [ ] 2.4 Add realistic variance across shifts (afternoon lower on some, night different patterns)
  - [ ] 2.5 Insert shift_summaries records via Supabase client
  - [ ] 2.6 Add cleanup step for shift_summaries in the clear section

- [ ] Task 3: Verify backward compatibility (AC: #8)
  - [ ] 3.1 Confirm migration does NOT alter `daily_summaries` table
  - [ ] 3.2 Confirm seed script upsert logic for `daily_summaries` remains unchanged

## Dev Notes

### Architecture & Design Decisions

- **Option B approach (from improvements.md):** New `shift_summaries` table alongside `daily_summaries` rather than modifying daily_summaries grain. This is the safer, backward-compatible approach specified in the epic. The `daily_summaries` table remains the source of truth for daily aggregates. Shift data is additive.
- **No FK cascade delete needed** beyond asset_id, since shift_summaries should be cleaned up when an asset is deleted (matching `daily_summaries` pattern which uses `ON DELETE CASCADE`).
- **Three shifts:** morning, afternoon, night -- this is the standard 3-shift pattern for this coffee manufacturing plant. The CHECK constraint enforces these exact values.

### Migration Pattern to Follow

Follow the exact pattern established in `supabase/migrations/0003_analytical_cache.sql` (which created `daily_summaries`):

1. `CREATE TABLE IF NOT EXISTS` with UUID PK via `gen_random_uuid()`
2. FK to `assets(id)` with `ON DELETE CASCADE`
3. Column comments via `COMMENT ON COLUMN`
4. Table comment via `COMMENT ON TABLE`
5. Individual and composite indexes with `IF NOT EXISTS`
6. RLS enable + drop/recreate policy pattern (idempotent)
7. Verification queries as SQL comments at bottom

**RLS Policy Pattern (from `daily_summaries`):**
```sql
-- Authenticated users can SELECT
CREATE POLICY "Allow authenticated read access on shift_summaries"
    ON shift_summaries FOR SELECT
    TO authenticated
    USING (true);

-- Service role has full access
CREATE POLICY "Allow service_role full access on shift_summaries"
    ON shift_summaries FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
```

### Migration File Naming

- The latest existing migration is `0025_action_followups.sql`
- Epic 17 spec says `0032_shift_summaries.sql` -- use this number per the epic specification
- If other migrations have been added between 0025 and 0032, adjust accordingly, but default to `0032` as specified

### Column Design Rationale

| Column | Type | Why |
|--------|------|-----|
| `id` | UUID PK | Standard pattern across all tables |
| `asset_id` | UUID FK | Links to `assets.id`, same as `daily_summaries` |
| `date` | DATE | Matches `daily_summaries.report_date` semantics (note: epic uses `date` as column name, not `report_date`) |
| `shift` | TEXT CHECK | Constrained to exactly 3 values; TEXT (not ENUM) matches project pattern (`action_followups.status` uses TEXT CHECK) |
| `oee` | DECIMAL(5,2) | Matches `daily_summaries.oee_percentage` precision (0.00-100.00) |
| `availability` | DECIMAL(5,2) | OEE sub-component, new to shift level |
| `performance` | DECIMAL(5,2) | OEE sub-component, new to shift level |
| `quality` | DECIMAL(5,2) | OEE sub-component, new to shift level |
| `downtime_minutes` | INTEGER | Matches `daily_summaries.downtime_minutes` type |
| `units_produced` | INTEGER | Matches `daily_summaries.actual_output` semantics |
| `created_at` | TIMESTAMPTZ | Standard pattern; no `updated_at` since shift data is immutable once written |

### Seed Data Strategy

The seed script (`scripts/seed-data.mjs`) already has 14 assets with 7 days + today of `daily_summaries` data. For each existing daily summary record:

1. **Split daily totals into 3 shifts** using a distribution function:
   - Morning: ~35-40% of daily output (stable shift, fewer changeovers)
   - Afternoon: ~30-35% of daily output (sometimes lower due to shift change disruptions)
   - Night: ~25-30% of daily output (reduced staffing, more maintenance windows)

2. **Add realistic variance:**
   - Apply +/- 5-15% random variance to each shift's base allocation
   - Ensure sum of shift units approximately equals daily `actual_output` (within 2-3%)
   - Calculate shift-level OEE from the distributed metrics
   - Afternoon shift should occasionally show distinctly lower performance (to support Story 17.4's "which shift had the problem?" use case)

3. **OEE sub-components:**
   - Generate availability, performance, quality breakdowns that combine to the shift OEE
   - Use manufacturing-realistic ranges: availability (85-98%), performance (80-100%), quality (95-100%)

4. **Downtime distribution:**
   - Split daily `downtime_minutes` across shifts weighted toward shifts with lower OEE
   - Night shift may have more planned maintenance downtime

### Existing Assets in Seed Data (14 total)

| Asset ID | Name | Area |
|----------|------|------|
| `a0..01` | Roaster 1 | Roasting |
| `a0..02` | Roaster 2 | Roasting |
| `a0..03` | Roaster 3 | Roasting |
| `a0..04` | Grinder 1 | Grinding |
| `a0..05` | Grinder 2 | Grinding |
| `a0..06` | Grinder 3 | Grinding |
| `a0..07` | Grinder 4 | Grinding |
| `a0..14` | Grinder 5 | Grinding |
| `a0..08` | Filler Line A | Filling |
| `a0..09` | Filler Line B | Filling |
| `a0..10` | Filler Line C | Filling |
| `a0..11` | Packaging Line 1 | Packaging |
| `a0..12` | Packaging Line 2 | Packaging |
| `a0..13` | Packaging Line 3 | Packaging |

**Note:** Only 8 of these 14 assets have daily_summaries seed data (Roaster 1, Roaster 2, Grinder 1-3, Grinder 5, Filler Line A, Packaging Line 1). Generate shift records ONLY for assets that have existing `daily_summaries` records.

### Project Structure Notes

- **Migration path:** `supabase/migrations/0032_shift_summaries.sql` (per epic specification)
- **Seed script path:** `scripts/seed-data.mjs` (modify existing file, do NOT create new file)
- Supabase migrations are plain SQL files, not using any ORM or migration framework
- The seed script uses `@supabase/supabase-js` client with service role key to bypass RLS
- The seed script uses `upsert` for most operations with `onConflict` for idempotency

### Anti-Patterns to Avoid

1. **DO NOT modify `daily_summaries` table** -- this story creates a NEW table alongside it (NFR-I6 backward compatibility)
2. **DO NOT use ENUM type** for `shift` -- use `TEXT CHECK` to match project convention (see `action_followups.status`)
3. **DO NOT add `updated_at` column** -- shift performance data is append-only/immutable (no trigger needed)
4. **DO NOT create a separate seed script** -- add shift seed logic to the existing `scripts/seed-data.mjs`
5. **DO NOT add an `update_updated_at` trigger** -- no `updated_at` column means no trigger needed
6. **DO NOT generate shift records for assets that have no daily_summaries** -- only seed shifts for assets with existing daily data
7. **DO NOT use `gen_random_uuid()` directly in JS** -- let the database handle UUID generation (omit `id` from inserts)

### References

- [Source: _bmad-output/planning-artifacts/epic-17.md#Story-17.3] -- Story definition and acceptance criteria
- [Source: docs/improvements.md#Shift-level-granularity] -- Design rationale, Option A vs Option B analysis
- [Source: supabase/migrations/0003_analytical_cache.sql] -- Pattern for `daily_summaries` table creation, RLS policies, and indexes
- [Source: supabase/migrations/0025_action_followups.sql] -- Pattern for TEXT CHECK constraints and RLS
- [Source: scripts/seed-data.mjs] -- Existing seed data structure, asset IDs, daily_summaries records
- [Source: docs/data-models.md] -- Full schema reference for `daily_summaries`, `assets`, `shift_targets` tables
- [Source: _bmad-output/planning-artifacts/epics-improvements.md#FR-I11] -- FR-I11 (Shift-Level Granularity) and NFR-I6 (Backward Compatibility)

### Cross-Story Context

- **Story 17.4 (Shift Breakdown API & UI)** depends on this story's table and seed data. Story 17.4 will query `shift_summaries` to show per-shift breakdown in the workcenter scorecard and attribute action item misses to specific shifts.
- **Story 17.1 (Date Picker)** and **Story 17.2 (Smart Summary On-Demand)** are independent frontend stories that do NOT depend on this story.
- The `shift_targets` table already exists with per-shift targets per asset -- Story 17.4 will join `shift_summaries` with `shift_targets` for shift-level attainment calculations.

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
