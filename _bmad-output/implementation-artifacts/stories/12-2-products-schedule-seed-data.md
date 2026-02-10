# Story 12.2: Products & Schedule Seed Data

Status: ready-for-dev

## Story

As a developer or demo user,
I want realistic seed data for products, schedules, and actuals,
so that the schedule attainment features have meaningful data to display.

## Acceptance Criteria

1. **Given** the seed script runs after the migration, **When** the products table is queried, **Then** ~10 coffee manufacturing products exist:
   - Roasting products: Colombian Single Origin, Brazilian Santos, Ethiopian Yirgacheffe, House Blend, Dark Roast Blend
   - Grinding products: Espresso Grind, Medium Grind, Coarse Grind
   - Filling products: K-Cup, 12oz Bag, 5lb Bag

2. **Given** the production schedule is queried for the past 7 days, **When** results are returned, **Then** each asset has daily schedule entries with realistic product assignments, **And** products are logically mapped to workcenters (roasting products on roasters, grinding products on grinders, filling products on fillers).

3. **Given** the production actuals are queried, **When** compared against the schedule, **Then**:
   - Some assets show on-schedule production (actual matches scheduled product and quantity)
   - Some assets show product swaps (ran different product than scheduled)
   - Some assets show underproduction (correct product, fewer units than scheduled)
   - The data creates interesting variance patterns for the UI to display

## Tasks / Subtasks

- [ ] Task 1: Add product seed data to `scripts/seed-data.mjs` (AC: #1)
  - [ ] 1.1: Define ~11 products with id, name, sku, product_family, unit_of_measure
  - [ ] 1.2: Upsert products into the `products` table using deterministic UUIDs
  - [ ] 1.3: Log product insertion results
- [ ] Task 2: Add production schedule seed data (AC: #2)
  - [ ] 2.1: Define schedule entries for 7 days across all relevant assets
  - [ ] 2.2: Map products to workcenters logically (roasting products to Roaster 1-3, grinding products to Grinder 1-5, filling products to Filler A-C)
  - [ ] 2.3: Create realistic scheduling patterns (e.g., Roaster 1 runs Colombian Mon-Wed, Brazilian Thu-Fri)
  - [ ] 2.4: Include shift assignments (Day, Night) where appropriate
  - [ ] 2.5: Upsert schedule entries into `production_schedule` table
- [ ] Task 3: Add production actuals seed data (AC: #3)
  - [ ] 3.1: Generate actuals that match schedule for ~60% of entries (on-schedule)
  - [ ] 3.2: Create product swap scenarios for ~15% of entries (ran different product)
  - [ ] 3.3: Create underproduction scenarios for ~25% of entries (correct product, fewer units)
  - [ ] 3.4: Ensure variance patterns are interesting for UI demos
  - [ ] 3.5: Upsert actuals into `production_actuals` table
- [ ] Task 4: Clear/reset products and schedule data on re-seed (AC: #1, #2, #3)
  - [ ] 4.1: Add delete statements for `production_actuals`, `production_schedule`, and `products` at the top of the seed section (respecting FK order)

## Dev Notes

### Critical Implementation Context

**Dependency on Story 12.1:** This story requires the migration from Story 12.1 (`supabase/migrations/0026_products_and_schedule.sql`) to have been run first. The three tables (`products`, `production_schedule`, `production_actuals`) must exist before seeding.

**Table Schemas (from Story 12.1):**

```sql
-- products
id UUID PK, name TEXT, sku TEXT, product_family TEXT,
unit_of_measure TEXT DEFAULT 'units', created_at, updated_at

-- production_schedule
id UUID PK, asset_id UUID FK(assets), product_id UUID FK(products),
scheduled_quantity INTEGER, scheduled_date DATE, shift TEXT,
production_order_ref TEXT (nullable), created_at, updated_at

-- production_actuals
id UUID PK, asset_id UUID FK(assets), product_id UUID FK(products),
actual_quantity INTEGER, production_date DATE, shift TEXT,
created_at, updated_at
```

### Existing Seed Script Patterns

The existing `scripts/seed-data.mjs` follows these patterns that MUST be replicated:

1. **Supabase client initialization:** Uses `createClient` with service role key (already configured at top of file)
2. **Date helpers:** Uses `daysAgo(n)` to generate dates relative to today -- reuse this exact helper
3. **Deterministic UUIDs:** Uses pattern `a0000001-0000-0000-0000-00000000XXXX` for assets -- use a similar deterministic pattern for products (e.g., `p0000001-0000-0000-0000-00000000XXXX`) so re-runs are idempotent
4. **Upsert with onConflict:** Uses `supabase.from('table').upsert(data, { onConflict: 'id' })` for idempotency
5. **Clear before insert:** Existing data cleared with `.delete().neq('id', '00000000-...')` pattern
6. **Console logging:** Uses emoji prefixed logs (e.g., `console.log('emoji Inserting...')`)

### Existing Asset IDs (MUST reference these)

```javascript
// Roasters
'a0000001-0000-0000-0000-000000000001' // Roaster 1 (area: Roasting)
'a0000001-0000-0000-0000-000000000002' // Roaster 2 (area: Roasting)
'a0000001-0000-0000-0000-000000000003' // Roaster 3 (area: Roasting)

// Grinders
'a0000001-0000-0000-0000-000000000004' // Grinder 1 (area: Grinding)
'a0000001-0000-0000-0000-000000000005' // Grinder 2 (area: Grinding)
'a0000001-0000-0000-0000-000000000006' // Grinder 3 (area: Grinding)
'a0000001-0000-0000-0000-000000000007' // Grinder 4 (area: Grinding)
'a0000001-0000-0000-0000-000000000014' // Grinder 5 (area: Grinding)

// Fillers
'a0000001-0000-0000-0000-000000000008' // Filler Line A (area: Filling)
'a0000001-0000-0000-0000-000000000009' // Filler Line B (area: Filling)
'a0000001-0000-0000-0000-000000000010' // Filler Line C (area: Filling)

// Packaging
'a0000001-0000-0000-0000-000000000011' // Packaging Line 1 (area: Packaging)
'a0000001-0000-0000-0000-000000000012' // Packaging Line 2 (area: Packaging)
'a0000001-0000-0000-0000-000000000013' // Packaging Line 3 (area: Packaging)
```

### Product-to-Workcenter Mapping Rules

Products MUST be logically mapped to the correct workcenters:

| Product Family | Valid Assets | Rationale |
|---------------|-------------|-----------|
| Roasting (Colombian, Brazilian, Ethiopian, House Blend, Dark Roast) | Roaster 1-3 | Raw beans are roasted on roasting equipment |
| Grinding (Espresso Grind, Medium Grind, Coarse Grind) | Grinder 1-5 | Roasted beans are ground on grinding equipment |
| Filling (K-Cup, 12oz Bag, 5lb Bag) | Filler Line A-C | Ground coffee is packaged on filling lines |

**Packaging Lines (11-13):** Do NOT assign products to packaging lines in this story. Packaging lines handle case-packing which is downstream and not tracked at the product level in this epic.

### Suggested Product Definitions

```javascript
const products = [
  { id: 'p0000001-0000-0000-0000-000000000001', name: 'Colombian Single Origin', sku: 'RST-COL-001', product_family: 'Roasting', unit_of_measure: 'lbs' },
  { id: 'p0000001-0000-0000-0000-000000000002', name: 'Brazilian Santos', sku: 'RST-BRZ-001', product_family: 'Roasting', unit_of_measure: 'lbs' },
  { id: 'p0000001-0000-0000-0000-000000000003', name: 'Ethiopian Yirgacheffe', sku: 'RST-ETH-001', product_family: 'Roasting', unit_of_measure: 'lbs' },
  { id: 'p0000001-0000-0000-0000-000000000004', name: 'House Blend', sku: 'RST-HBL-001', product_family: 'Roasting', unit_of_measure: 'lbs' },
  { id: 'p0000001-0000-0000-0000-000000000005', name: 'Dark Roast Blend', sku: 'RST-DRK-001', product_family: 'Roasting', unit_of_measure: 'lbs' },
  { id: 'p0000001-0000-0000-0000-000000000006', name: 'Espresso Grind', sku: 'GRN-ESP-001', product_family: 'Grinding', unit_of_measure: 'lbs' },
  { id: 'p0000001-0000-0000-0000-000000000007', name: 'Medium Grind', sku: 'GRN-MED-001', product_family: 'Grinding', unit_of_measure: 'lbs' },
  { id: 'p0000001-0000-0000-0000-000000000008', name: 'Coarse Grind', sku: 'GRN-CRS-001', product_family: 'Grinding', unit_of_measure: 'lbs' },
  { id: 'p0000001-0000-0000-0000-000000000009', name: 'K-Cup', sku: 'FIL-KCP-001', product_family: 'Filling', unit_of_measure: 'units' },
  { id: 'p0000001-0000-0000-0000-000000000010', name: '12oz Bag', sku: 'FIL-12B-001', product_family: 'Filling', unit_of_measure: 'units' },
  { id: 'p0000001-0000-0000-0000-000000000011', name: '5lb Bag', sku: 'FIL-5LB-001', product_family: 'Filling', unit_of_measure: 'units' },
];
```

### Scheduling Pattern Guidance

Create realistic weekly scheduling patterns. Example approach:

**Roasters (target ~130-143 lbs/day from existing daily_summaries):**
- Roaster 1: Colombian Mon-Wed (130 lbs/day), Brazilian Thu-Fri (135 lbs/day)
- Roaster 2: Dark Roast Blend Mon-Thu (130 lbs/day), House Blend Fri (128 lbs/day)
- Roaster 3: Ethiopian Yirgacheffe Mon-Wed (125 lbs/day), House Blend Thu-Fri (130 lbs/day)

**Grinders (target ~1,800-1,950 lbs/day from existing daily_summaries):**
- Grinder 1: Espresso Grind Mon-Fri (1,900 lbs/day)
- Grinder 2: Coarse Grind Mon-Fri (1,900 lbs/day)
- Grinder 3: Medium Grind Mon-Wed (1,850 lbs/day), Espresso Grind Thu-Fri (1,850 lbs/day)
- Grinder 4: Medium Grind Mon-Fri (1,850 lbs/day)
- Grinder 5: Espresso Grind Mon-Wed (1,900 lbs/day), Medium Grind Thu-Fri (1,850 lbs/day)

**Fillers (target ~4,200-4,600 units/day from existing daily_summaries):**
- Filler A: K-Cup Mon-Wed (4,400 units/day), 12oz Bag Thu-Fri (4,200 units/day)
- Filler B: 12oz Bag Mon-Fri (4,300 units/day)
- Filler C: 5lb Bag Mon-Wed (4,100 units/day), K-Cup Thu-Fri (4,400 units/day)

### Variance Pattern Examples for Actuals

Create these specific variance scenarios to make the UI interesting:

1. **On-schedule (60%):** actual_quantity within +/-5% of scheduled, same product_id
2. **Product swap (15%):** Different product_id than scheduled (e.g., Roaster 1 scheduled Colombian but ran Brazilian)
3. **Underproduction (25%):** Same product_id but actual_quantity is 60-85% of scheduled

Specific interesting scenarios to include:
- **Yesterday (daysAgo 1):** Roaster 1 ran Brazilian instead of scheduled Colombian (swap). Grinder 5 made only 1,608 of scheduled 1,900 (underproduction matching existing daily_summary data)
- **2 days ago:** Filler A had a great day, exceeded target on K-Cups
- **3 days ago:** Multiple product swaps across grinders due to bean availability issues
- **Shift-level variance:** Include at least one example where Day shift hit target but Night shift underproduced

### Data Consistency with Existing Seed Data

**CRITICAL:** The `actual_quantity` values in `production_actuals` should be broadly consistent with the `actual_output` values already in `daily_summaries` for the same asset and date. They don't need to match exactly (daily_summaries is an aggregate; actuals may be per-product), but the totals should be in the same ballpark.

For example, if `daily_summaries` shows Roaster 1 with `actual_output: 125` on daysAgo(1), then the sum of `production_actuals` for Roaster 1 on that date should be approximately 125.

### Seed Order and FK Safety

Insert in this order to respect foreign key constraints:
1. Products (no FK dependencies)
2. Production Schedule (depends on assets + products)
3. Production Actuals (depends on assets + products)

Delete in reverse order when clearing:
1. Production Actuals
2. Production Schedule
3. Products

### Project Structure Notes

- Only one file is modified: `scripts/seed-data.mjs`
- Add new seeding logic AFTER the existing safety events section (section 5) and BEFORE the test users section (section 6)
- The clear/delete for products+schedule tables should be added to the existing "Clear existing data" section at the top
- Follow the existing numbered section comment pattern: `// 5.5. Products, Schedule & Actuals (Epic 12)` or similar

### References

- [Source: _bmad-output/planning-artifacts/epic-12.md - Story 12.2]
- [Source: scripts/seed-data.mjs - Existing seed patterns and asset IDs]
- [Source: _bmad-output/planning-artifacts/epic-12.md - Story 12.1 table schemas]
- [Source: supabase/migrations/0002_plant_object_model.sql - Migration pattern reference]
- [Source: docs/data-models.md - Entity relationships]
- [Source: docs/architecture-api.md - API directory structure]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
