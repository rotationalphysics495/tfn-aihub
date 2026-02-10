# Story 11.3: Workcenter Seed Data

Status: ready-for-dev

## Story

As a developer or demo user,
I want the seed data script to populate realistic workcenter-level production data,
so that the workcenter scorecard has meaningful data to display out of the box.

## Acceptance Criteria

1. **Given** the seed script runs successfully, **When** the workcenter summary endpoint is called for yesterday's date, **Then** data exists for all 4 workcenters (Roasting, Grinding, Filling, Packaging).

2. **Given** the seed script runs successfully, **When** the data is queried per workcenter, **Then** each workcenter has 2-4 assets with varied performance (some hit target, some miss).

3. **Given** the seed data populates all workcenters, **When** attainment is calculated per workcenter, **Then** attainment ranges from ~70% to ~100% across workcenters to show realistic variation.

4. **Given** the existing seed data assets already have `area` assignments, **When** the seed data is reviewed, **Then** all 14 assets are assigned to their correct workcenter area (Roasting: 3, Grinding: 5, Filling: 3, Packaging: 3).

5. **Given** all assets exist in the `assets` table with `area` values, **When** `shift_targets` are queried, **Then** every asset has at least one shift target record so the workcenter scorecard can compute attainment.

6. **Given** `daily_summaries` and `shift_targets` exist for all assets, **When** the `target_output` in `daily_summaries` is compared to `shift_targets.target_output`, **Then** the values are aligned so that the workcenter summary API endpoint (Story 11.1) can use either source consistently without conflicting numbers.

## Tasks / Subtasks

- [ ] Task 1: Audit existing seed data for workcenter coverage gaps (AC: #1, #2, #4)
  - [ ] 1.1 Verify all 14 assets have correct `area` assignments in both `seed-data.mjs` and `0021_seed_data.sql`
  - [ ] 1.2 Identify which assets are missing `daily_summaries` for T-1 through T-7
  - [ ] 1.3 Identify which assets are missing `shift_targets` entries

- [ ] Task 2: Fix target value alignment between `daily_summaries` and `shift_targets` (AC: #6)
  - [ ] 2.1 Reconcile the mismatch: `daily_summaries.target_output` uses full-day values (e.g., Grinder = 1950) while `shift_targets.target_output` uses per-shift values (e.g., Grinder morning = 1000). Decide on one canonical approach and align both.
  - [ ] 2.2 Update `seed-data.mjs` to use consistent target values
  - [ ] 2.3 Update `0021_seed_data.sql` to match if needed

- [ ] Task 3: Add missing `daily_summaries` for all assets across 7 days (AC: #1, #2, #3)
  - [ ] 3.1 Add Roaster 3 daily summaries for T-1 through T-7 (currently missing in `.mjs`)
  - [ ] 3.2 Add Grinder 4 daily summaries for T-1 through T-7 (currently missing in `.mjs`)
  - [ ] 3.3 Add Filler Line B daily summaries for T-3 through T-7 (only T-1 and T-2 exist in `.mjs`)
  - [ ] 3.4 Add Filler Line C daily summaries for T-1 through T-7 (currently missing in `.mjs`)
  - [ ] 3.5 Add Packaging Line 2 daily summaries for T-3 through T-7 (only T-1 and T-2 exist in `.mjs`)
  - [ ] 3.6 Add Packaging Line 3 daily summaries for T-1 through T-7 (currently missing in `.mjs`)
  - [ ] 3.7 Also update `0021_seed_data.sql` with the same missing data

- [ ] Task 4: Add `shift_targets` seeding to `seed-data.mjs` (AC: #5)
  - [ ] 4.1 Add shift_targets upsert block to the `.mjs` script (currently completely absent from the script)
  - [ ] 4.2 Ensure all 14 assets have at least one shift target entry

- [ ] Task 5: Ensure realistic performance variation per workcenter (AC: #3)
  - [ ] 5.1 Roasting: Target ~88-92% attainment overall (high performer)
  - [ ] 5.2 Grinding: Target ~80-88% attainment overall (mixed -- Grinder 5 drags the average down)
  - [ ] 5.3 Filling: Target ~75-85% attainment overall (Filler A has valve issues, others are decent)
  - [ ] 5.4 Packaging: Target ~85-92% attainment overall (generally reliable)
  - [ ] 5.5 Within each workcenter, ensure at least 1 asset hits target and at least 1 misses for realistic distribution

- [ ] Task 6: Validate end-to-end (AC: #1, #2, #3, #4, #5, #6)
  - [ ] 6.1 Run `node scripts/seed-data.mjs` and verify no errors
  - [ ] 6.2 Query `SELECT area, COUNT(*) FROM assets GROUP BY area` and confirm 4 workcenters with correct counts
  - [ ] 6.3 Query `SELECT a.area, COUNT(DISTINCT ds.asset_id) FROM daily_summaries ds JOIN assets a ON a.id = ds.asset_id WHERE ds.report_date = CURRENT_DATE - 1 GROUP BY a.area` and confirm all 4 workcenters have data
  - [ ] 6.4 Query `SELECT a.area, SUM(ds.actual_output) as actual, SUM(ds.target_output) as target FROM daily_summaries ds JOIN assets a ON a.id = ds.asset_id WHERE ds.report_date = CURRENT_DATE - 1 GROUP BY a.area` and verify attainment ranges are realistic
  - [ ] 6.5 Query `SELECT a.area, COUNT(*) FROM shift_targets st JOIN assets a ON a.id = st.asset_id GROUP BY a.area` and confirm all workcenters have shift targets

## Dev Notes

### Critical Issue: Target Value Mismatch

The biggest risk in this story is the **target_output mismatch** between `daily_summaries` and `shift_targets`:

| Asset Type | `daily_summaries.target_output` | `shift_targets.target_output` (morning) | `shift_targets.target_output` (afternoon) |
|---|---|---|---|
| Grinders | 1950 | 1000 | 950 |
| Fillers | 4600 | 2400 | 2200 |
| Packaging | 6200 | 3200 | 3000 |
| Roasters | 143 | 48 | 45 |

The `daily_summaries.target_output` appears to represent the full-day total (morning + afternoon shifts combined), while `shift_targets` stores per-shift values. This is **intentionally correct** -- `daily_summaries` aggregates across shifts. However, the Story 11.1 API endpoint will need to decide which table to use for targets:

- **Option A**: Use `daily_summaries.target_output` directly (simpler, already the full-day number)
- **Option B**: Sum `shift_targets.target_output` across shifts for the day (more "correct" from a data model perspective)

**For this story**: Ensure the relationship is clear and documented. The `daily_summaries.target_output` value should equal the sum of all `shift_targets.target_output` for that asset on that day. If that relationship doesn't hold, fix it.

**Current state of the math:**
- Roasters: shift targets sum = 48 + 45 = 93, but `daily_summaries.target_output` = 143 (MISMATCH)
- Grinders: shift targets sum = 1000 + 950 = 1950, matches `daily_summaries.target_output` = 1950 (OK)
- Fillers: shift targets sum = 2400 + 2200 = 4600, matches `daily_summaries.target_output` = 4600 (OK)
- Packaging: shift targets sum = 3200 + 3000 = 6200, matches `daily_summaries.target_output` = 6200 (OK)
- Roaster 3 has shift targets of 42 + 42 = 84, but its daily_summaries target_output is unknown (no rows exist yet)

**Action**: Fix the Roaster shift_targets to sum to 143 (e.g., morning=48, afternoon=48, night=47 for Roaster 1 and 2; adjust Roaster 3 similarly). Alternatively, adjust `daily_summaries.target_output` for roasters to match the shift target sums. Pick one direction and be consistent.

### Existing Seed Data Architecture

There are **two parallel seed mechanisms** in this project:

1. **`scripts/seed-data.mjs`** -- Node.js script using Supabase client. Uses `daysAgo()` for dynamic date generation relative to "today." This is the **primary mechanism** for developers running `node scripts/seed-data.mjs`. It seeds: assets, cost_centers, daily_summaries, live_snapshots, safety_events, test users.

2. **`supabase/migrations/0021_seed_data.sql`** -- SQL migration that runs as part of `supabase db reset`. Uses `CURRENT_DATE - N` for relative dates. Seeds the same tables plus shift_targets and supervisor_assignments.

**CRITICAL**: Both mechanisms must stay in sync. Any data added to one should be added to the other. The `.mjs` script is missing `shift_targets` entirely -- this story must add them.

### Data Coverage Gaps (What Needs Adding)

**Assets with FULL 7-day `daily_summaries` in `seed-data.mjs`:**
- Roaster 1 (7 days)
- Roaster 2 (7 days)
- Grinder 1 (7 days)
- Grinder 2 (7 days)
- Grinder 3 (7 days)
- Grinder 5 (7 days)
- Filler Line A (7 days)
- Packaging Line 1 (7 days)

**Assets with PARTIAL data in `seed-data.mjs`:**
- Grinder 4 -- 0 days (only live_snapshots)
- Filler Line B -- 2 days (T-1, T-2 only)
- Filler Line C -- 0 days (only live_snapshots)
- Packaging Line 2 -- 2 days (T-1, T-2 only)
- Packaging Line 3 -- 0 days (only live_snapshots)
- Roaster 3 -- 0 days (only live_snapshots)

**In `0021_seed_data.sql`, the same gaps exist** -- Roaster 3, Grinder 4, Filler Line C, and Packaging Line 3 have no daily_summaries. Filler Line B and Packaging Line 2 only have 2 days each.

For the workcenter scorecard to show all assets, every asset needs at least T-1 data. For a realistic demo, 7 days per asset is ideal.

### Performance Variation Guidelines

Design new seed data to create interesting scorecard visuals:

- **Roasting** (3 assets): Overall strong. Roaster 1 had a rough day 3 days ago (sensor issue, 65.5% OEE). Roaster 2 is the star. Roaster 3 should be middle-of-the-road. Workcenter attainment ~88%.
- **Grinding** (5 assets): Mixed. Grinder 2 is consistently excellent (95%+). Grinder 5 and Grinder 3 drag the average. Grinder 1 is decent. Grinder 4 should be moderate. Workcenter attainment ~83%.
- **Filling** (3 assets): Filler A is the problem child (valve issues, 72% OEE yesterday). Filler B and C should be solid performers. Workcenter attainment ~80%.
- **Packaging** (3 assets): Generally reliable. Line 1 had a case erector jam issue 3 days ago. Lines 2 and 3 should be consistent. Workcenter attainment ~88%.

### Project Structure Notes

- Seed data script: `scripts/seed-data.mjs` (Node.js, uses `@supabase/supabase-js`)
- SQL seed migration: `supabase/migrations/0021_seed_data.sql`
- Keep both in sync
- The `.mjs` script uses `upsert` with `onConflict` for idempotency
- Daily summaries have a unique constraint on `(asset_id, report_date)`
- Shift targets do NOT have a unique constraint -- use care when inserting to avoid duplicates (the SQL migration uses `ON CONFLICT DO NOTHING` but there's no specific conflict target)

### References

- [Source: `_bmad-output/planning-artifacts/epic-11.md` -- Story 11.3 definition and acceptance criteria]
- [Source: `scripts/seed-data.mjs` -- Existing seed data script (primary modification target)]
- [Source: `supabase/migrations/0021_seed_data.sql` -- SQL seed data migration (secondary modification target)]
- [Source: `supabase/migrations/0002_plant_object_model.sql` -- `assets`, `cost_centers`, `shift_targets` schema]
- [Source: `supabase/migrations/0003_analytical_cache.sql` -- `daily_summaries`, `live_snapshots`, `safety_events` schema]
- [Source: `docs/data-models.md` -- Data model documentation]
- [Source: `docs/architecture-api.md` -- API architecture and directory structure]
- [Source: `docs/improvements.md` -- "Workcenter production summary" section describes the feature context]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
