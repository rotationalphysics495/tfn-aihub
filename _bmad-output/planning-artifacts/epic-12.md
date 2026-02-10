---
stepsCompleted: ["step-01-validate-prerequisites", "step-02-design-epics", "step-03-create-stories"]
inputDocuments:
  - "docs/improvements.md"
  - "docs/architecture-api.md"
  - "docs/architecture-web.md"
  - "docs/data-models.md"
epic: 12
status: "ready"
---

# Epic 12: Products, Schedule & Attainment

## Overview

**Goal:** Plant managers can upload a weekly production schedule and see "did we make the right stuff?" — schedule attainment by product, variance callouts for wrong-product runs, and overall product mix comparison.

**Dependencies:** None (standalone, though it naturally complements Epic 11's workcenter scorecard)

**User Value:** Answers "did we make what was scheduled?" with product-level detail. Producing 100% of target quantity means nothing if you ran the wrong product. Unblocks schedule intelligence without waiting for AX/D365 integration.

## Requirements Coverage

| Requirement | Coverage |
|-------------|----------|
| FR-I2 (Schedule Attainment & Product Mix) | Full |
| FR-I3 (Schedule Upload) | Full |
| NFR-I2 (Upload Validation) | Full |
| NFR-I5 (Data Integration Flexibility) | Full |

## Stories

---

### Story 12.1: Products & Schedule Data Model

**As a** developer,
**I want** database tables for products, production schedules, and production actuals,
**So that** the system can track what should have been produced vs. what was actually produced.

**Acceptance Criteria:**

**Given** the migration runs successfully
**When** the database is queried
**Then** the following tables exist:
  - `products` with columns: `id` (UUID PK), `name` (TEXT), `sku` (TEXT), `product_family` (TEXT), `unit_of_measure` (TEXT DEFAULT 'units'), `created_at`, `updated_at`
  - `production_schedule` with columns: `id` (UUID PK), `asset_id` (UUID FK), `product_id` (UUID FK), `scheduled_quantity` (INTEGER), `scheduled_date` (DATE), `shift` (TEXT), `production_order_ref` (TEXT nullable), `created_at`, `updated_at`
  - `production_actuals` with columns: `id` (UUID PK), `asset_id` (UUID FK), `product_id` (UUID FK), `actual_quantity` (INTEGER), `production_date` (DATE), `shift` (TEXT), `created_at`, `updated_at`

**And** RLS is enabled on all three tables following existing patterns
**And** appropriate indexes exist on `asset_id`, `product_id`, `scheduled_date`, `production_date`
**And** foreign key constraints reference `assets(id)` and `products(id)` with CASCADE DELETE

**Technical Notes:**
- Migration file: `supabase/migrations/0026_products_and_schedule.sql`
- Follow existing migration patterns from `0002_plant_object_model.sql`
- Include `update_updated_at_column()` trigger on all tables

**Files to Create/Modify:**
- `supabase/migrations/0026_products_and_schedule.sql` - New migration

---

### Story 12.2: Products & Schedule Seed Data

**As a** developer or demo user,
**I want** realistic seed data for products, schedules, and actuals,
**So that** the schedule attainment features have meaningful data to display.

**Acceptance Criteria:**

**Given** the seed script runs after the migration
**When** the products table is queried
**Then** ~10 coffee manufacturing products exist:
  - Roasting: Colombian Single Origin, Brazilian Santos, Ethiopian Yirgacheffe, House Blend, Dark Roast Blend
  - Grinding: Espresso Grind, Medium Grind, Coarse Grind
  - Filling: K-Cup, 12oz Bag, 5lb Bag

**Given** the production schedule is queried for the past 7 days
**When** results are returned
**Then** each asset has daily schedule entries with realistic product assignments
**And** products are logically mapped to workcenters (roasting products on roasters, etc.)

**Given** the production actuals are queried
**When** compared against the schedule
**Then** some assets show on-schedule production (actual matches scheduled product and quantity)
**And** some assets show product swaps (ran different product than scheduled)
**And** some assets show underproduction (correct product, fewer units than scheduled)
**And** the data creates interesting variance patterns for the UI to display

**Technical Notes:**
- Update `scripts/seed-data.mjs` to seed products, schedule, and actuals
- Use `daysAgo()` helper for date generation
- Create realistic patterns (e.g., Roaster 1 runs Colombian Mon-Wed, Brazilian Thu-Fri)

**Files to Create/Modify:**
- `scripts/seed-data.mjs` - Add products, schedule, and actuals seeding

---

### Story 12.3: Schedule Upload API

**As a** Plant Manager or Planner,
**I want** to upload a CSV or Excel file with the weekly production schedule,
**So that** the system knows what should be produced without waiting for AX/D365 integration.

**Acceptance Criteria:**

**Given** a user uploads a valid CSV file with columns: date, shift, asset_name, product_name, scheduled_quantity
**When** `POST /api/v1/schedule/upload` is called with multipart form data
**Then** the file is parsed, validated, and a preview response is returned with:
  - Parsed rows count
  - Matched assets (fuzzy match against `assets.name`)
  - Matched products (exact match or new products to create)
  - Validation errors (if any) highlighted per row
**And** no data is committed to the database yet (preview only)

**Given** a user confirms the preview by calling `POST /api/v1/schedule/upload/confirm`
**When** the confirmation request includes the parsed data
**Then** matched products are inserted (or found) in the `products` table
**And** new products that don't exist are auto-created with a confirmation note
**And** schedule rows are upserted into `production_schedule` (replacing existing rows for same date range)
**And** a success response includes count of rows inserted/updated

**Given** a user uploads an Excel (.xlsx) file
**When** the file is parsed
**Then** the same validation and preview flow applies as CSV

**Given** a CSV with an asset name that doesn't match any existing asset
**When** the preview is generated
**Then** the row is flagged with an error and suggestions for near-matches (fuzzy matching)
**And** the user can correct or skip the row before confirming

**Given** a CSV with invalid data (negative quantities, invalid dates, missing required columns)
**When** the preview is generated
**Then** each invalid row is flagged with a specific error message
**And** the upload cannot be confirmed until errors are resolved

**Technical Notes:**
- Use `openpyxl` for Excel parsing, Python `csv` module for CSV
- Fuzzy matching: `difflib.get_close_matches()` for asset name suggestions
- Two-step flow: preview (parse + validate) → confirm (commit to DB)
- Endpoint group: `/api/v1/schedule/`

**Files to Create/Modify:**
- `apps/api/app/api/schedule.py` - Upload and confirm endpoints
- `apps/api/app/services/schedule_parser.py` - CSV/Excel parsing and validation logic
- `apps/api/app/schemas/schedule.py` - Request/response schemas
- `apps/api/app/main.py` - Register schedule router

---

### Story 12.4: Schedule Upload UI

**As a** Plant Manager or Planner,
**I want** a page where I can drag-and-drop or browse for a schedule file and preview it before committing,
**So that** I can verify the data is correct before it enters the system.

**Acceptance Criteria:**

**Given** a user navigates to `/settings/schedule-upload`
**When** the page loads
**Then** a drag-and-drop zone is displayed with "Drop CSV or Excel file here" and a file picker button
**And** accepted formats are shown: .csv, .xlsx

**Given** a user drops or selects a valid file
**When** the file is uploaded to the preview endpoint
**Then** a preview table is shown with all parsed rows
**And** matched assets show with a green checkmark
**And** unmatched assets show with a red warning and suggested matches
**And** new products show with a blue "will be created" indicator
**And** validation errors are highlighted in red with specific messages

**Given** the preview has no errors
**When** the user clicks "Confirm Upload"
**Then** the data is committed to the database
**And** a success toast shows with count of rows inserted
**And** the user is redirected to the morning report

**Given** the preview has errors
**When** the user views the preview
**Then** the "Confirm Upload" button is disabled
**And** error rows are clearly highlighted with fix suggestions

**Technical Notes:**
- New page at `apps/web/src/app/settings/schedule-upload/page.tsx`
- Use Shadcn/UI `Table` for preview display
- File upload via `FormData` to the API
- Add navigation link in settings or morning report header

**Files to Create/Modify:**
- `apps/web/src/app/settings/schedule-upload/page.tsx` - Upload page
- `apps/web/src/components/schedule/ScheduleUploadZone.tsx` - Drag-and-drop component
- `apps/web/src/components/schedule/SchedulePreviewTable.tsx` - Preview table with validation
- `apps/web/src/hooks/useScheduleUpload.ts` - Upload and confirm hooks

---

### Story 12.5: Schedule Attainment API

**As a** Plant Manager,
**I want** an API endpoint that compares scheduled vs. actual production by product,
**So that** the frontend can show schedule attainment and product mix variance.

**Acceptance Criteria:**

**Given** schedule and actuals data exist for a date
**When** `GET /api/v1/production/schedule-attainment?date={date}` is called
**Then** the response includes per-workcenter schedule attainment:
  - Workcenter name
  - Per-product breakdown: product name, scheduled quantity, actual quantity, attainment %
  - Variance callouts: products that were scheduled but not produced, products produced but not scheduled
  - Overall workcenter attainment percentage

**Given** an asset produced a different product than scheduled
**When** the attainment response is generated
**Then** a variance callout is included: "Roaster 1 ran Colombian instead of scheduled Brazilian — X units of Brazilian still needed"

**Given** no schedule exists for the requested date
**When** the endpoint is called
**Then** the response returns a 200 with an empty result and message "No schedule data for this date"

**Technical Notes:**
- Join `production_schedule` with `production_actuals` on (asset_id, date, shift)
- Join with `products` for product names and `assets` for area grouping
- Identify mismatches where actual product_id differs from scheduled product_id

**Files to Create/Modify:**
- `apps/api/app/api/production.py` - Add schedule attainment endpoint
- `apps/api/app/schemas/production.py` - Add `ScheduleAttainmentResponse` schema

---

### Story 12.6: Schedule Attainment UI Section

**As a** Plant Manager,
**I want** a schedule attainment section on the morning report showing planned vs. actual by product,
**So that** I can see at a glance whether we made the right stuff.

**Acceptance Criteria:**

**Given** schedule attainment data exists for the report date
**When** the morning report loads
**Then** a "Schedule Attainment" section appears between the workcenter scorecard and action items
**And** each workcenter shows: scheduled products, actual products, attainment % per product
**And** variance callouts are highlighted (wrong product runs, underproduction by SKU)

**Given** a product was swapped (different product than scheduled)
**When** the attainment section renders
**Then** the swap is highlighted in amber/orange with text like "Ran Colombian instead of scheduled Brazilian"

**Given** no schedule data exists for the date
**When** the attainment section renders
**Then** a prompt appears: "No schedule uploaded for this date. Upload schedule →" with a link to the upload page

**Given** the overall product mix is shown
**When** the user views the section
**Then** a simple bar comparison shows planned vs. actual mix percentages

**Technical Notes:**
- New component in `apps/web/src/components/production/`
- Hook: `useScheduleAttainment(date)` calling the new API
- Position in morning report: between workcenter scorecard and action items

**Files to Create/Modify:**
- `apps/web/src/components/production/ScheduleAttainment.tsx` - Main section component
- `apps/web/src/components/production/ProductVarianceCallout.tsx` - Variance highlight
- `apps/web/src/hooks/useScheduleAttainment.ts` - Data fetching hook
- `apps/web/src/app/morning-report/page.tsx` - Integrate section
