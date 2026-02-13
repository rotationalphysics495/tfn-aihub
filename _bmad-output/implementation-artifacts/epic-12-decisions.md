# Epic 12 Decision Log

This file tracks implementation decisions for context continuity across phases.

**Epic:** 12
**Started:** 2026-02-11 10:31:39

---


## DESIGN: 12-1-products-schedule-data-model
**Timestamp:** 2026-02-11 10:34:37

DESIGN START
story_id: 12-1-products-schedule-data-model

files_to_modify:
  - path: supabase/migrations/0026_products_and_schedule.sql
    action: create
    purpose: Single migration file containing all three new tables (products, production_schedule, production_actuals), their indexes, triggers, RLS policies, table/column comments, and verification queries

patterns_to_use:
  - idempotent_table_creation: Use `CREATE TABLE IF NOT EXISTS` for all three tables (matches 0002 pattern)
  - uuid_primary_key: Use `gen_random_uuid()` for PKs — NOT `uuid_generate_v4()` (matches 0002 pattern)
  - fk_cascade_delete: Use `REFERENCES <table>(id) ON DELETE CASCADE` inline on column definition (matches 0002 cost_centers/shift_targets pattern)
  - trigger_idempotency: Use `DROP TRIGGER IF EXISTS` then `CREATE TRIGGER` referencing the existing `update_updated_at_column()` function — do NOT recreate the function (matches 0002 pattern)
  - rls_policy_idempotency: Use `DROP POLICY IF EXISTS` then `CREATE POLICY` for each policy (matches 0002 pattern)
  - index_idempotency: Use `CREATE INDEX IF NOT EXISTS` (matches 0002 pattern)
  - text_columns: Use TEXT (not VARCHAR) for string columns, consistent with 0025 and epic specification
  - header_comment: Include story reference, date, and table descriptions at top (matches 0002 pattern)
  - section_separators: Use `-- ====...` comment blocks between sections (matches 0002 pattern)
  - table_comments: Use `COMMENT ON TABLE` and `COMMENT ON COLUMN` for documentation (matches 0002 pattern)
  - verification_queries: Include verification SQL as comments at bottom of file (matches 0002 pattern)

dependencies:
  - supabase: installed (existing project infrastructure)
  - assets_table: exists (created in 0002_plant_object_model.sql)
  - update_updated_at_column_function: exists (created in 0002_plant_object_model.sql)
  - gen_random_uuid: exists (built-in to PostgreSQL 13+; uuid-ossp extension also enabled in 0001)

acceptance_criteria_mapping:
  - AC1: supabase/migrations/0026_products_and_schedule.sql — CREATE TABLE IF NOT EXISTS products(...) with id (UUID PK DEFAULT gen_random_uuid()), name (TEXT NOT NULL), sku (TEXT nullable), product_family (TEXT), unit_of_measure (TEXT DEFAULT 'units'), created_at (TIMESTAMPTZ DEFAULT NOW()), updated_at (TIMESTAMPTZ DEFAULT NOW()); plus DROP TRIGGER IF EXISTS / CREATE TRIGGER for update_updated_at_column()
  - AC2: supabase/migrations/0026_products_and_schedule.sql — CREATE TABLE IF NOT EXISTS production_schedule(...) with id (UUID PK), asset_id (UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE), product_id (UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE), scheduled_quantity (INTEGER NOT NULL), scheduled_date (DATE NOT NULL), shift (TEXT), production_order_ref (TEXT nullable), timestamps; plus trigger
  - AC3: supabase/migrations/0026_products_and_schedule.sql — CREATE TABLE IF NOT EXISTS production_actuals(...) with id (UUID PK), asset_id (UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE), product_id (UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE), actual_quantity (INTEGER NOT NULL), production_date (DATE NOT NULL), shift (TEXT), timestamps; plus trigger
  - AC4: supabase/migrations/0026_products_and_schedule.sql — ALTER TABLE <table> ENABLE ROW LEVEL SECURITY for all 3 tables; CREATE POLICY for SELECT to authenticated USING (true); CREATE POLICY for ALL to service_role USING (true) WITH CHECK (true) — each with DROP POLICY IF EXISTS for idempotency
  - AC5: supabase/migrations/0026_products_and_schedule.sql — CREATE INDEX IF NOT EXISTS for all 6 indexes: idx_production_schedule_asset_id, idx_production_schedule_product_id, idx_production_schedule_scheduled_date, idx_production_actuals_asset_id, idx_production_actuals_product_id, idx_production_actuals_production_date
  - AC6: File is named exactly 0026_products_and_schedule.sql in supabase/migrations/; follows 0002 structural pattern; all DDL uses IF NOT EXISTS / IF EXISTS for idempotency

risks:
  - Migration ordering conflict: Another developer could create a 0026 migration on a parallel branch. Mitigation: verify no 0026 file exists before creating; Supabase applies migrations in filename order so naming collisions would cause a clear failure at deploy time.
  - Assets table dependency: production_schedule and production_actuals both reference assets(id). If the assets table doesn't exist (e.g., migration 0002 failed or was rolled back), this migration will fail on FK creation. Mitigation: The `IF NOT EXISTS` on table creation won't help with FK resolution — this is an expected hard dependency; assets table is well-established and present in all environments.
  - No UNIQUE constraint on schedule: Per anti-pattern prevention, we intentionally do NOT add a unique constraint on (asset_id, product_id, scheduled_date, shift). This means duplicate rows are possible. Mitigation: Story 12.3 (Upload API) will handle deduplication via upsert logic; the data model is deliberately permissive for MVP.
  - Products table has no UNIQUE on sku or name: The story spec makes sku nullable and doesn't call for uniqueness constraints. Duplicate product names could occur. Mitigation: Story 12.2 seed data and 12.3 upload API will enforce application-level uniqueness where needed.

estimated_test_files:
  - No automated test files for this story: This is a pure SQL migration. Verification is done via the SQL verification queries embedded as comments at the bottom of the migration file, plus manual verification steps documented in the story's Dev Notes (run migration, check tables in Supabase Table Editor, test RLS policies, test CASCADE deletes).

implementation_order:
  1. Create file supabase/migrations/0026_products_and_schedule.sql with header comment block (story reference 12-1, date, description of all three tables)
  2. Write CREATE TABLE IF NOT EXISTS products(...) with all 7 columns per AC1 spec
  3. Write COMMENT ON TABLE/COLUMN statements for products table
  4. Write CREATE TABLE IF NOT EXISTS production_schedule(...) with all 9 columns and both FK constraints per AC2 spec
  5. Write COMMENT ON TABLE/COLUMN statements for production_schedule table
  6. Write CREATE TABLE IF NOT EXISTS production_actuals(...) with all 8 columns and both FK constraints per AC3 spec
  7. Write COMMENT ON TABLE/COLUMN statements for production_actuals table
  8. Write CREATE INDEX IF NOT EXISTS for all 6 performance indexes per AC5 spec (3 on production_schedule, 3 on production_actuals)
  9. Write DROP TRIGGER IF EXISTS / CREATE TRIGGER for update_updated_at_column() on all 3 tables (referencing existing function, NOT recreating it)
  10. Write ALTER TABLE ... ENABLE ROW LEVEL SECURITY for all 3 tables per AC4
  11. Write DROP POLICY IF EXISTS / CREATE POLICY for authenticated SELECT on each of the 3 tables per AC4
  12. Write DROP POLICY IF EXISTS / CREATE POLICY for service_role ALL on each of the 3 tables per AC4
  13. Write verification queries as comments at bottom of file per AC6 (table columns, FK checks, index checks, RLS status checks)
  14. Review complete migration for idempotency: confirm every CREATE uses IF NOT EXISTS, every DROP uses IF EXISTS, no recreation of update_updated_at_column() function, gen_random_uuid() used (not uuid_generate_v4()), TEXT used (not VARCHAR), no extra columns beyond spec
DESIGN END

---

## DESIGN: 12-2-products-schedule-seed-data
**Timestamp:** 2026-02-11 10:51:05

DESIGN START
story_id: 12-2-products-schedule-seed-data

files_to_modify:
  - path: _bmad/scripts/seed-data.mjs
    action: modify
    purpose: Add product definitions, production schedule entries, and production actuals seed data (sections 5.5 and clearing logic). This is the ONLY file modified.

patterns_to_use:
  - deterministic_uuids: Use `p0000001-0000-0000-0000-00000000XXXX` pattern for product IDs (mirrors `a0000001-...` pattern for assets) and `s0000001-...` / `t0000001-...` patterns for schedule and actuals entries, ensuring idempotent re-runs
  - upsert_on_conflict: Use `supabase.from('table').upsert(data, { onConflict: 'id' })` for products, schedule, and actuals (matching existing asset upsert pattern at line 67)
  - delete_neq_pattern: Use `await supabase.from('table').delete().neq('id', '00000000-0000-0000-0000-000000000000')` for clearing data (matching lines 42-44)
  - daysAgo_helper: Reuse existing `daysAgo(n)` helper (line 19) for generating schedule/actual dates relative to today
  - emoji_logging: Use emoji-prefixed console.log for each section (matching pattern throughout file, e.g., lines 38, 41, 48, 103)
  - section_comment_pattern: Use numbered section comments like `// 5.5. Products, Schedule & Actuals (Epic 12)` (matching existing `// 1. Assets`, `// 2. Cost Centers` pattern)
  - fk_safe_delete_order: Delete production_actuals first, then production_schedule, then products (reverse of insert order) to respect FK constraints
  - fk_safe_insert_order: Insert products first, then production_schedule, then production_actuals

dependencies:
  - @supabase/supabase-js: installed (already imported at line 9)
  - migration_0026: must be applied (creates products, production_schedule, production_actuals tables)

acceptance_criteria_mapping:
  - AC1: _bmad/scripts/seed-data.mjs — Define `products` array with 11 coffee manufacturing products (5 Roasting, 3 Grinding, 3 Filling) using deterministic UUIDs; upsert into `products` table. Products array defined per story spec: Colombian Single Origin, Brazilian Santos, Ethiopian Yirgacheffe, House Blend, Dark Roast Blend (Roasting/lbs), Espresso Grind, Medium Grind, Coarse Grind (Grinding/lbs), K-Cup, 12oz Bag, 5lb Bag (Filling/units).
  - AC2: _bmad/scripts/seed-data.mjs — Define `productionSchedule` array with entries for daysAgo(1) through daysAgo(7) mapping products to correct workcenters: Roasting products (IDs 001-005) to Roaster 1-3 (asset IDs 001-003), Grinding products (IDs 006-008) to Grinder 1-5 (asset IDs 004-007,014), Filling products (IDs 009-011) to Filler A-C (asset IDs 008-010). NO packaging lines. Include shift assignments (Day/Night). Scheduled quantities aligned with existing daily_summaries targets (~130-143 lbs/day roasters, ~1800-1950 lbs/day grinders, ~3200-4600 units/day fillers).
  - AC3: _bmad/scripts/seed-data.mjs — Define `productionActuals` array with variance patterns: ~60% on-schedule (actual_quantity within +/-5% of scheduled, same product_id), ~15% product swaps (different product_id than scheduled), ~25% underproduction (same product_id, actual_quantity at 60-85% of scheduled). Sum of actuals per asset per date must broadly match the `actual_output` in `daily_summaries` for that asset/date. Specific scenarios: daysAgo(1) Roaster 1 swap (Brazilian instead of Colombian), daysAgo(1) Grinder 5 underproduction (1608 total matching daily_summaries), daysAgo(2) Filler A exceeds K-Cup target, daysAgo(3) multiple grinder swaps, at least one shift-level variance (Day on-target, Night underproduced).

risks:
  - daily_summaries_consistency: production_actuals sums per asset/date must approximately match the existing daily_summaries.actual_output values. Mitigation: Manually verify each day's actuals sum against the daily_summaries values already in the script (lines 104-1413). For assets with only a single product per day, the actual_quantity should equal the daily_summaries actual_output. For assets with shift-level or multi-product entries, the sum of actuals must match.
  - table_not_exists: If migration 0026 hasn't been applied, all three inserts will fail with "relation does not exist". Mitigation: The delete statements will fail silently (matching existing pattern), and the upsert/insert calls already have error logging. The script doesn't crash on individual section failures.
  - uuid_collisions: Deterministic UUIDs for schedule and actuals entries must be unique across all 7 days × 11 assets × 2 shifts. Mitigation: Use a systematic ID pattern encoding asset index, day, and shift into the UUID suffix (e.g., `s0000001-0000-0000-0000-{assetIdx}{day}{shift}`) to guarantee uniqueness.
  - product_swap_fk_integrity: Product swap actuals reference product IDs from different families. Mitigation: All product IDs are deterministic and inserted before schedule/actuals, so FK references will always resolve.
  - shift_naming: The production_schedule.shift column and existing shift_targets use 'morning'/'afternoon'/'night'. The story spec mentions 'Day'/'Night'. Mitigation: Use 'Day'/'Night' as specified in the story since these are new tables with no dependency on shift_targets shift naming.

estimated_test_files:
  - No automated test files: This is seed data (manually verified). Verification is done by running the seed script and querying the three tables. Verification queries: (1) `SELECT COUNT(*), product_family FROM products GROUP BY product_family` should return Roasting:5, Grinding:3, Filling:3. (2) `SELECT COUNT(*) FROM production_schedule` should return ~154 entries (11 non-packaging assets × 7 days × 2 shifts). (3) `SELECT COUNT(*) FROM production_actuals` should return ~154 entries. (4) Cross-check: `SELECT a.asset_id, a.production_date, SUM(a.actual_quantity) as total_actual FROM production_actuals a GROUP BY a.asset_id, a.production_date ORDER BY a.asset_id, a.production_date` should broadly match daily_summaries.actual_output for each asset/date.

implementation_order:
  1. Add clearing/delete statements for the three new tables to the existing "Clear existing data" section (lines 40-45). Insert BEFORE existing deletes. Order: production_actuals first, production_schedule second, products third. Use the `.delete().neq('id', '00000000-...')` pattern.
  2. Define the `products` constant array with 11 entries matching the story spec exactly (IDs p0000001-...001 through ...011, names, SKUs, product_family, unit_of_measure). Place this as a new section after safety events (section 5, line 1512) and before test users (section 6, line 1514). Use section comment `// 5.5. Products, Schedule & Actuals (Epic 12)`.
  3. Add products upsert call: `await supabase.from('products').upsert(products, { onConflict: 'id' })` with error logging.
  4. Extract the daily_summaries actual_output values for all 11 relevant assets (Roasters 1-3, Grinders 1-5, Fillers A-C) for daysAgo(1) through daysAgo(7) from the existing seed data (lines 104-877). Create a reference mapping to ensure actuals will be consistent.
  5. Define the `productionSchedule` constant array. For each of the 11 assets × 7 days × 2 shifts (Day/Night), create entries with: deterministic UUID, asset_id, product_id (logically mapped per family), scheduled_quantity (split roughly 55%/45% between Day/Night shifts, totaling the daily target), scheduled_date (daysAgo(1)-daysAgo(7)), shift ('Day'/'Night'). Use weekly product rotation patterns from the story spec (e.g., Roaster 1: Colombian Mon-Wed, Brazilian Thu-Fri). Generate production_order_ref strings like `PO-{assetPrefix}-{date}` for realism.
  6. Add production_schedule upsert call with error logging.
  7. Define the `productionActuals` constant array. For each schedule entry, create a corresponding actual entry with variance applied: ~60% on-schedule (actual_quantity = scheduled_quantity × random factor between 0.95-1.05, same product_id), ~15% product swaps (different product_id from same family, actual_quantity approximately matches scheduled), ~25% underproduction (same product_id, actual_quantity = scheduled_quantity × 0.60-0.85). Constrain: the sum of all actuals for a given asset+date MUST approximately match the daily_summaries.actual_output value. Specific scenarios per story spec: daysAgo(1) Roaster 1 swap; daysAgo(1) Grinder 5 underproduction to total ~1608; daysAgo(2) Filler A exceeds on K-Cups; daysAgo(3) multiple grinder swaps; at least one Day/Night shift-level variance.
  8. Add production_actuals upsert call with error logging.
  9. Add summary console.log lines after each insert section (e.g., `console.log('  ✓ 11 products inserted')`, `console.log('  ✓ Production schedule entries inserted')`, `console.log('  ✓ Production actuals with variance patterns inserted')`).
  10. Final review: Verify all deterministic UUIDs are unique, all FK references (asset_id, product_id) are valid, all actuals sums match daily_summaries, no packaging line assets are included, and the script follows existing patterns for error handling and logging.
DESIGN END

---

## DESIGN: 12-3-schedule-upload-api
**Timestamp:** 2026-02-11 11:12:45

DESIGN START
story_id: 12-3-schedule-upload-api

files_to_modify:
  - path: apps/api/app/schemas/schedule.py
    action: create
    purpose: Pydantic models for schedule upload preview/confirm request-response cycle — ScheduleUploadRow, ScheduleRowPreview, SchedulePreviewResponse, ScheduleConfirmRequest, ScheduleConfirmResponse, RowValidationError

  - path: apps/api/app/services/schedule_parser.py
    action: create
    purpose: Business logic for CSV/Excel parsing, column header validation, per-row validation, fuzzy asset matching via difflib, product matching, and preview assembly

  - path: apps/api/app/api/schedule.py
    action: create
    purpose: FastAPI router with POST /upload (multipart file → preview) and POST /upload/confirm (commit validated data). Follows existing production.py patterns: get_supabase_client helper, Depends(get_current_user), try/except HTTPException error handling

  - path: apps/api/app/main.py
    action: modify
    purpose: Import schedule module and register router with prefix /api/v1/schedule and tag "Schedule" (story 12.3 comment)

  - path: apps/api/requirements.txt
    action: modify
    purpose: Add openpyxl>=3.1.0 and python-multipart>=0.0.6 (python-multipart is required by FastAPI for UploadFile but is not explicitly listed; openpyxl is new)

  - path: apps/api/tests/services/test_schedule_parser.py
    action: create
    purpose: Unit tests for schedule_parser service — CSV parsing, Excel parsing, validation errors, fuzzy asset matching, product matching

  - path: apps/api/tests/api/test_schedule.py
    action: create
    purpose: API endpoint integration tests — upload with valid CSV/Excel, preview response shape, confirm endpoint, upsert behavior, auth requirement, file type rejection, validation error propagation

patterns_to_use:
  - router_registration: Import `schedule` in the `from app.api import ...` line in main.py, register with `app.include_router(schedule.router, prefix="/api/v1/schedule", tags=["Schedule"])` with story reference comment (matches line 94-99 pattern)
  - supabase_client_helper: Copy `get_supabase_client()` async function from production.py (lines 108-119) into schedule.py for self-contained DB access
  - auth_dependency: Use `current_user: CurrentUser = Depends(get_current_user)` from `app.core.security` with `app.models.user.CurrentUser` import (matches production.py lines 18-20)
  - error_handling: try/except HTTPException re-raise, generic Exception → logger.error + 500 (matches production.py lines 308-315)
  - schema_conventions: Pydantic BaseModel with Field(..., description=), ConfigDict(json_schema_extra={}), str Enum classes (matches action.py pattern)
  - test_client_fixture: Use conftest.py fixtures (client, mock_verify_jwt, mock_supabase_client) — mock Supabase via patch("app.api.schedule.get_supabase_client") (matches test_production_api.py lines 60-66)
  - file_upload_pattern: Use `UploadFile = File(...)` from FastAPI (matches handoff.py line 1048)

dependencies:
  - openpyxl: needs-install (add >=3.1.0 to requirements.txt for Excel parsing)
  - python-multipart: needs-install (add >=0.0.6 to requirements.txt; required by FastAPI for form/file uploads — implicitly used by handoff.py but not listed)
  - csv: installed (stdlib)
  - difflib: installed (stdlib)
  - io: installed (stdlib)
  - fastapi: installed (>=0.109.0)
  - pydantic: installed (>=2.0.0)
  - supabase: installed (>=2.0.0)

acceptance_criteria_mapping:
  - AC1 (CSV Upload Preview): apps/api/app/api/schedule.py — `POST /upload` endpoint accepts multipart form data with `UploadFile`, calls `schedule_parser.parse_file()` which detects CSV from extension/content-type, uses `csv.DictReader` with `utf-8-sig` encoding, validates column headers, validates each row, fuzzy-matches asset names against DB `assets.name` values, exact-matches product names against DB `products.name`, returns `SchedulePreviewResponse` with parsed_rows_count, matched_assets, matched_products, new_products, and per-row validation_errors. No DB writes occur. apps/api/app/schemas/schedule.py — `SchedulePreviewResponse` model. apps/api/app/services/schedule_parser.py — `parse_csv()`, `validate_row()`, `match_asset()`, `match_product()`, `assemble_preview()` functions.

  - AC2 (Upload Confirmation): apps/api/app/api/schedule.py — `POST /upload/confirm` endpoint accepts `ScheduleConfirmRequest` JSON body containing the validated/corrected rows from the preview step. For each row: (a) find-or-create product in `products` table via Supabase upsert, (b) delete existing `production_schedule` rows matching `(asset_id, scheduled_date, shift)`, (c) insert new rows. Returns `ScheduleConfirmResponse` with inserted/updated counts. apps/api/app/schemas/schedule.py — `ScheduleConfirmRequest` (list of confirmed rows with resolved asset_id/product_name) and `ScheduleConfirmResponse` models.

  - AC3 (Excel Support): apps/api/app/services/schedule_parser.py — `parse_excel()` function using `openpyxl.load_workbook(BytesIO(file_bytes), read_only=True, data_only=True)`, reads first row as headers, subsequent rows as data, normalizes to same internal row dict format as CSV, then follows identical validation/matching pipeline. apps/api/app/api/schedule.py — file format detection based on filename extension (.xlsx → Excel, .csv → CSV) with fallback to content-type.

  - AC4 (Fuzzy Asset Matching): apps/api/app/services/schedule_parser.py — `match_asset(input_name, asset_names, cutoff=0.6)` function using `difflib.get_close_matches(input_name, asset_names, n=3, cutoff=0.6)`. Logic: (1) exact case-insensitive match → matched with asset_id, (2) close matches found → row flagged with warning + suggestions list, (3) no matches → row flagged as error. Results included in `ScheduleRowPreview.asset_match_status` and `ScheduleRowPreview.asset_suggestions`.

  - AC5 (Validation Errors): apps/api/app/services/schedule_parser.py — `validate_row()` function checks ALL rules per row and returns list of `RowValidationError` objects: date must be valid and within range (-90 to +365 days), shift must be non-empty, asset_name must be non-empty, product_name must be non-empty, scheduled_quantity must be positive integer. File-level validation: at least 1 data row, all required columns present, file size ≤ 5MB. apps/api/app/api/schedule.py — confirm endpoint rejects request if any rows have unresolved errors (400 response).

risks:
  - python-multipart not listed: FastAPI's UploadFile depends on python-multipart. The handoff.py endpoint works (presumably installed transitively), but it's not in requirements.txt. Mitigation: Explicitly add python-multipart>=0.0.6 to requirements.txt to make the dependency explicit and avoid runtime ImportError.
  - Supabase RLS and service key: The upload/confirm endpoints use the Supabase service key (from SUPABASE_KEY env var). If this is the anon key instead of the service_role key, INSERT/DELETE on products/production_schedule will be blocked by RLS policies (which only allow service_role for writes). Mitigation: Document that SUPABASE_KEY must be the service_role key for write operations; this is consistent with existing write endpoints in the codebase.
  - Large file memory: Reading entire file into memory (await file.read()) could be problematic for very large files. Mitigation: Enforce 5MB file size limit at the top of the upload endpoint before reading content; reject with 413 if exceeded.
  - Concurrent uploads race condition: Two users uploading for the same date range simultaneously could cause conflicting deletes/inserts during confirm. Mitigation: The delete-then-insert upsert pattern in a single Supabase request batch minimizes the window; for MVP this is acceptable. Document as known limitation.
  - Preview data not persisted: The preview response is returned to the client and must be sent back in the confirm request. If the client modifies the data or the DB state changes between preview and confirm, the confirm could produce unexpected results. Mitigation: The confirm endpoint re-validates asset_id existence before inserting; product find-or-create is idempotent. This is the standard two-step pattern per story requirements.
  - openpyxl version compatibility: openpyxl >=3.1.0 with read_only and data_only flags is well-established. Mitigation: Pin minimum version 3.1.0 which supports all required features.

estimated_test_files:
  - apps/api/tests/services/test_schedule_parser.py: Unit tests for parse_csv (valid CSV, UTF-8 BOM handling), parse_excel (valid XLSX), validate_row (negative quantity, invalid date, missing columns, date range validation), match_asset (exact match, close match with suggestions, no match), match_product (existing product, new product), file-level validation (empty file, missing headers), assemble_preview (grouped results with error/warning/ok rows)
  - apps/api/tests/api/test_schedule.py: API integration tests for POST /upload with valid CSV (200 with preview), POST /upload with valid XLSX (200 with preview), POST /upload with unsupported file type (400), POST /upload with oversized file (413), POST /upload without auth (401), POST /upload/confirm with valid data (200 with counts), POST /upload/confirm with unresolved errors (400), POST /upload/confirm upsert behavior (verifies delete + insert calls), POST /upload/confirm product auto-creation

implementation_order:
  1. Add dependencies to apps/api/requirements.txt: add `openpyxl>=3.1.0` and `python-multipart>=0.0.6`
  2. Create apps/api/app/schemas/schedule.py with all Pydantic models: ScheduleUploadRow (raw parsed row), RowValidationError (field + message), AssetMatchStatus (str Enum: matched/suggested/unmatched), ScheduleRowPreview (parsed row + validation errors + asset match status + suggestions + product match info), SchedulePreviewResponse (rows list, counts, has_errors flag), ScheduleConfirmRow (confirmed row with resolved asset_id, product_name, scheduled_date, shift, scheduled_quantity), ScheduleConfirmRequest (list of confirmed rows), ScheduleConfirmResponse (rows_inserted, rows_updated, products_created, total_processed)
  3. Create apps/api/app/services/schedule_parser.py with functions: detect_file_format(filename, content_type) → "csv"|"xlsx"|None, parse_csv(file_bytes) → list[dict], parse_excel(file_bytes) → list[dict], normalize_headers(headers) → dict mapping normalized→original, validate_headers(headers) → list[str] (missing required columns), validate_row(row, row_number) → list[RowValidationError], match_asset(input_name, asset_names_map) → tuple[status, asset_id|None, suggestions], match_products(product_names, existing_products) → dict[name→id|None], assemble_preview(parsed_rows, asset_names_map, existing_products) → SchedulePreviewResponse
  4. Create apps/api/app/api/schedule.py with: get_supabase_client() helper (copied from production.py), POST /upload endpoint (accept UploadFile, validate size ≤5MB, detect format, read file bytes, fetch assets from DB, fetch products from DB, call schedule_parser functions, return SchedulePreviewResponse), POST /upload/confirm endpoint (accept ScheduleConfirmRequest JSON, find-or-create products, delete-then-insert production_schedule rows, return ScheduleConfirmResponse)
  5. Modify apps/api/app/main.py: add `schedule` to the import line (line 7), add `app.include_router(schedule.router, prefix="/api/v1/schedule", tags=["Schedule"])` with story 12.3 comment after line 99
  6. Create apps/api/tests/services/test_schedule_parser.py with unit tests for all parser functions (CSV parsing, Excel parsing, row validation, fuzzy matching, product matching, header validation, preview assembly)
  7. Create apps/api/tests/api/test_schedule.py with API endpoint tests (upload CSV, upload XLSX, confirm, auth, error cases) using conftest fixtures and mock_supabase_client pattern from test_production_api.py
DESIGN END

---

## TEST_SPEC: 12-3-schedule-upload-api
**Timestamp:** 2026-02-11 11:16:34

TEST SPEC START
story_id: 12-3-schedule-upload-api
generated: 2026-02-11

test_specifications:

## AC1: CSV Upload Preview — Given a user uploads a valid CSV file with columns: date, shift, asset_name, product_name, scheduled_quantity, When POST /api/v1/schedule/upload is called with multipart form data, Then the file is parsed, validated, and a preview response is returned with: parsed rows count, matched assets (fuzzy match), matched products (exact match or new), and validation errors highlighted per row. No data is committed to the database yet (preview only).

### 12-3-schedule-upload-api-INT-001: Valid CSV upload returns preview with parsed rows and matched entities
- Priority: P0
- Type: integration
- Given: A valid CSV file containing 3 rows with columns date, shift, asset_name, product_name, scheduled_quantity; assets "Grinder 1", "Filler Line A" exist in the database; product "Dark Roast 12oz" exists in the products table
- When: POST /api/v1/schedule/upload is called with the CSV as multipart form data and a valid JWT
- Then: Response status is 200; response body contains parsed_rows_count=3; matched assets include "Grinder 1" and "Filler Line A" with their asset_ids; matched products include "Dark Roast 12oz" with its product_id; new products are listed for any product names not found; no validation errors are present; no rows are inserted into production_schedule or products tables
- Data: CSV with headers "date,shift,asset_name,product_name,scheduled_quantity" and rows like "2026-02-16,Day,Grinder 1,Dark Roast 12oz,500"

### 12-3-schedule-upload-api-UNIT-001: CSV parsing handles UTF-8 BOM encoding correctly
- Priority: P1
- Type: unit
- Given: A CSV file encoded with UTF-8 BOM (byte order mark prefix \xef\xbb\xbf) containing valid schedule data
- When: parse_csv() is called with the file bytes
- Then: The headers are correctly parsed without BOM characters prefixed to the first column name; all rows are returned as valid dictionaries with correct key names
- Data: CSV bytes with BOM prefix followed by "date,shift,asset_name,product_name,scheduled_quantity\n2026-02-16,Day,Grinder 1,Coffee Blend,100"

### 12-3-schedule-upload-api-UNIT-002: CSV parsing returns correct row dictionaries for valid input
- Priority: P0
- Type: unit
- Given: A well-formed CSV byte string with 5 data rows and all required column headers
- When: parse_csv() is called with the file bytes
- Then: A list of 5 dictionaries is returned; each dictionary has keys matching the column headers; values match the CSV cell contents
- Data: CSV with 5 rows of valid schedule data

### 12-3-schedule-upload-api-UNIT-003: Preview assembly groups rows by match status and error state
- Priority: P0
- Type: unit
- Given: A list of parsed rows where 2 rows have exact asset matches, 1 row has a fuzzy asset match with suggestions, and 1 row has an unmatched asset; known asset_names_map and existing_products list are provided
- When: assemble_preview() is called with the parsed rows, asset_names_map, and existing_products
- Then: The returned SchedulePreviewResponse contains parsed_rows_count=4; each row has correct asset_match_status (matched/suggested/unmatched); rows with suggestions include the suggestion list; the has_errors flag is True (due to unmatched asset); new products are identified
- Data: Parsed row dicts with asset names "Grinder 1" (exact), "Grinder" (fuzzy), "Unknown Machine" (no match), "Filler Line A" (exact)

### 12-3-schedule-upload-api-INT-002: Upload endpoint does not commit any data to the database
- Priority: P0
- Type: integration
- Given: A valid CSV file with 3 rows of schedule data; Supabase client is mocked
- When: POST /api/v1/schedule/upload is called with the CSV file
- Then: The Supabase client's insert/upsert/delete methods are never called on the production_schedule or products tables; only select queries are made (to fetch assets and existing products for matching)
- Data: Valid CSV file; mock Supabase client tracking method calls

### 12-3-schedule-upload-api-INT-003: Upload endpoint requires JWT authentication
- Priority: P0
- Type: integration
- Given: A valid CSV file with schedule data
- When: POST /api/v1/schedule/upload is called without an Authorization header
- Then: Response status is 401 or 403; response body indicates authentication is required
- Data: Valid CSV file; no auth token

### 12-3-schedule-upload-api-UNIT-004: Column header matching is case-insensitive
- Priority: P1
- Type: unit
- Given: A CSV file with headers "Date,SHIFT,Asset_Name,Product_Name,Scheduled_Quantity" (mixed case)
- When: parse_csv() and normalize_headers() are called
- Then: All headers are recognized as valid required columns; parsing proceeds successfully and rows are returned with normalized keys
- Data: CSV with mixed-case headers

### 12-3-schedule-upload-api-INT-004: Upload rejects unsupported file types with 400 error
- Priority: P0
- Type: integration
- Given: A file with .txt extension or unsupported content type (e.g., application/pdf)
- When: POST /api/v1/schedule/upload is called with the unsupported file
- Then: Response status is 400; response body includes an error message indicating the file type is not supported; only .csv and .xlsx are accepted
- Data: A text file renamed or with unsupported MIME type

### 12-3-schedule-upload-api-INT-005: Upload rejects files exceeding 5MB size limit
- Priority: P1
- Type: integration
- Given: A CSV file that exceeds 5MB in size
- When: POST /api/v1/schedule/upload is called with the oversized file
- Then: Response status is 413 (or 400); response body includes an error message about file size exceeding the 5MB limit
- Data: A CSV file > 5MB (can be generated with repeated rows)


## AC2: Upload Confirmation — Given a user confirms the preview by calling POST /api/v1/schedule/upload/confirm, When the confirmation request includes the parsed data, Then matched products are inserted/found, new products are auto-created, schedule rows are upserted into production_schedule, and a success response includes count of rows inserted/updated.

### 12-3-schedule-upload-api-INT-006: Confirm endpoint inserts schedule rows and returns counts
- Priority: P0
- Type: integration
- Given: A valid ScheduleConfirmRequest JSON body containing 5 confirmed rows with resolved asset_ids and product_names; Supabase client is mocked to accept inserts
- When: POST /api/v1/schedule/upload/confirm is called with valid JWT
- Then: Response status is 200; response body contains rows_inserted count matching the number of confirmed rows; total_processed equals 5; Supabase delete was called for matching (asset_id, scheduled_date, shift) combinations; Supabase insert was called with the new rows on the production_schedule table
- Data: ScheduleConfirmRequest with 5 rows, each having asset_id (UUID), product_name, scheduled_date, shift, scheduled_quantity

### 12-3-schedule-upload-api-INT-007: Confirm endpoint auto-creates new products that do not exist
- Priority: P0
- Type: integration
- Given: A ScheduleConfirmRequest containing rows with product_name "New Blend XYZ" which does not exist in the products table; Supabase client is mocked to return empty result for product lookup and successful insert
- When: POST /api/v1/schedule/upload/confirm is called
- Then: Response status is 200; the products table insert is called with the new product name; response body includes products_created count >= 1; the new product's generated ID is used for the production_schedule insert
- Data: Confirm request with a product name not in the existing products table

### 12-3-schedule-upload-api-INT-008: Confirm endpoint upserts by replacing existing rows for same date range
- Priority: P0
- Type: integration
- Given: Existing production_schedule rows for asset_id=A, scheduled_date=2026-02-16, shift="Day"; a ScheduleConfirmRequest includes a row for the same (asset_id=A, 2026-02-16, "Day") combination with a different quantity
- When: POST /api/v1/schedule/upload/confirm is called
- Then: The Supabase client's delete is called with filters matching (asset_id=A, scheduled_date=2026-02-16, shift="Day"); then insert is called with the new row; existing rows for dates NOT in the upload are not affected
- Data: Confirm request overlapping with existing schedule data; mock Supabase to track delete/insert calls

### 12-3-schedule-upload-api-INT-009: Confirm endpoint finds existing products by exact name match
- Priority: P1
- Type: integration
- Given: A ScheduleConfirmRequest with product_name "Dark Roast 12oz" which already exists in the products table with a known UUID; Supabase returns the existing product on lookup
- When: POST /api/v1/schedule/upload/confirm is called
- Then: No new product is inserted; the existing product's UUID is used for the production_schedule row; products_created count is 0
- Data: Confirm request with existing product name; mock Supabase to return product record

### 12-3-schedule-upload-api-INT-010: Confirm endpoint requires JWT authentication
- Priority: P0
- Type: integration
- Given: A valid ScheduleConfirmRequest JSON body
- When: POST /api/v1/schedule/upload/confirm is called without an Authorization header
- Then: Response status is 401 or 403
- Data: Valid confirm request body; no auth token

### 12-3-schedule-upload-api-INT-011: Confirm endpoint rejects request with unresolved errors
- Priority: P0
- Type: integration
- Given: A ScheduleConfirmRequest containing rows that still have unresolved validation errors (e.g., unmatched asset_id is null)
- When: POST /api/v1/schedule/upload/confirm is called
- Then: Response status is 400; response body indicates that rows with errors cannot be confirmed
- Data: Confirm request with null asset_id or invalid data

### 12-3-schedule-upload-api-INT-012: Full two-step flow — upload preview then confirm
- Priority: P0
- Type: integration
- Given: A valid CSV file with 3 rows; all assets match exactly; 1 product exists, 1 is new; Supabase is mocked for both steps
- When: POST /api/v1/schedule/upload is called first, then POST /api/v1/schedule/upload/confirm is called with the confirmed rows derived from the preview
- Then: The upload step returns a preview with no errors; the confirm step returns success with rows_inserted=3 and products_created=1; database operations occur only during the confirm step
- Data: Complete flow with CSV → preview → confirm


## AC3: Excel Support — Given a user uploads an Excel (.xlsx) file, When the file is parsed, Then the same validation and preview flow applies as CSV.

### 12-3-schedule-upload-api-INT-013: Valid Excel (.xlsx) upload returns same preview structure as CSV
- Priority: P0
- Type: integration
- Given: A valid .xlsx file with the same column structure and data as a valid CSV; assets and products exist in the database
- When: POST /api/v1/schedule/upload is called with the .xlsx file as multipart form data
- Then: Response status is 200; response body has the same SchedulePreviewResponse structure as CSV uploads; parsed_rows_count matches the Excel data rows; matched assets and products are correctly identified
- Data: .xlsx file created with openpyxl containing headers and 3 data rows

### 12-3-schedule-upload-api-UNIT-005: Excel parsing reads first sheet and treats first row as headers
- Priority: P0
- Type: unit
- Given: An Excel file with multiple sheets; the first sheet contains headers in row 1 and data in subsequent rows
- When: parse_excel() is called with the file bytes
- Then: Only the first (active) sheet is read; row 1 values become dictionary keys; subsequent rows become data dictionaries; the correct number of rows is returned
- Data: .xlsx BytesIO with openpyxl, multiple sheets, headers in row 1

### 12-3-schedule-upload-api-UNIT-006: File format detection distinguishes CSV from XLSX correctly
- Priority: P1
- Type: unit
- Given: Files with various extensions and content types: "schedule.csv" (text/csv), "schedule.xlsx" (application/vnd.openxmlformats-officedocument.spreadsheetml.sheet), "schedule.CSV" (uppercase extension), "schedule.txt" (unsupported)
- When: detect_file_format() is called for each file
- Then: Returns "csv" for .csv files, "xlsx" for .xlsx files, None for unsupported types; detection is case-insensitive for extensions
- Data: Filename/content-type pairs for each format

### 12-3-schedule-upload-api-UNIT-007: Excel parsing with data_only mode returns calculated values not formulas
- Priority: P2
- Type: unit
- Given: An Excel file where the scheduled_quantity column contains a formula (e.g., =100+50)
- When: parse_excel() is called with data_only=True
- Then: The parsed value is the calculated result (150) not the formula string; note: data_only with read_only may return None for uncached formulas — test handles this edge case
- Data: .xlsx with formula cells (created and saved with cached values)

### 12-3-schedule-upload-api-INT-014: Excel upload validates and returns errors identically to CSV
- Priority: P1
- Type: integration
- Given: An Excel file with validation errors (negative quantity in row 2, invalid date in row 3)
- When: POST /api/v1/schedule/upload is called with the .xlsx file
- Then: Response contains per-row validation errors with the same error format and messages as would be returned for an equivalent CSV file with the same errors
- Data: .xlsx file with intentional validation errors


## AC4: Fuzzy Asset Matching — Given a CSV with an asset name that does not match any existing asset, When the preview is generated, Then the row is flagged with an error and suggestions for near-matches (fuzzy matching), and the user can correct or skip the row before confirming.

### 12-3-schedule-upload-api-UNIT-008: Exact case-insensitive asset match returns matched status with asset_id
- Priority: P0
- Type: unit
- Given: Input asset name "grinder 1" (lowercase); existing assets include "Grinder 1" with UUID
- When: match_asset("grinder 1", asset_names_map) is called
- Then: Returns status "matched" with the correct asset_id for "Grinder 1"; no suggestions are provided
- Data: asset_names_map = {"Grinder 1": "uuid-1", "Grinder 2": "uuid-2", ...}

### 12-3-schedule-upload-api-UNIT-009: Close typo match returns suggested status with suggestions list
- Priority: P0
- Type: unit
- Given: Input asset name "Grinder" (missing the number); existing assets include "Grinder 1", "Grinder 2", "Grinder 3"
- When: match_asset("Grinder", asset_names_map, cutoff=0.6) is called
- Then: Returns status "suggested"; suggestions list contains up to 3 close matches from the existing assets (e.g., ["Grinder 1", "Grinder 2", "Grinder 3"]); asset_id is None
- Data: asset_names_map with all grinder assets

### 12-3-schedule-upload-api-UNIT-010: Completely unrecognized asset name returns unmatched status with no suggestions
- Priority: P0
- Type: unit
- Given: Input asset name "XYZ Machine 99"; existing assets are the standard set (Roaster 1-3, Grinder 1-5, Filler Line A-C, Packaging Line 1-3)
- When: match_asset("XYZ Machine 99", asset_names_map, cutoff=0.6) is called
- Then: Returns status "unmatched"; suggestions list is empty; asset_id is None
- Data: asset_names_map with standard plant assets

### 12-3-schedule-upload-api-UNIT-011: Fuzzy match with minor typo suggests correct asset
- Priority: P1
- Type: unit
- Given: Input asset name "Filler Line a" (lowercase, close match); existing assets include "Filler Line A"
- When: match_asset("Filler Line a", asset_names_map) is called
- Then: Returns status "matched" (exact case-insensitive match) with the correct asset_id for "Filler Line A"
- Data: asset_names_map with filler line assets

### 12-3-schedule-upload-api-UNIT-012: Fuzzy match "Roaster" without number suggests all roasters
- Priority: P1
- Type: unit
- Given: Input asset name "Roaster"; existing assets include "Roaster 1", "Roaster 2", "Roaster 3"
- When: match_asset("Roaster", asset_names_map, cutoff=0.6) is called
- Then: Returns status "suggested"; suggestions include "Roaster 1", "Roaster 2", "Roaster 3" (up to 3)
- Data: asset_names_map with roaster assets

### 12-3-schedule-upload-api-INT-015: Preview flags unmatched asset rows as errors preventing confirmation
- Priority: P0
- Type: integration
- Given: A CSV file where row 2 has asset_name "Unknown Machine" which has no match or near-match
- When: POST /api/v1/schedule/upload is called
- Then: The preview response includes the row with asset_match_status "unmatched"; the has_errors flag is True; the row's error list includes an asset matching error
- Data: CSV with one unmatched asset name among valid rows


## AC5: Validation Errors — Given a CSV with invalid data (negative quantities, invalid dates, missing required columns), When the preview is generated, Then each invalid row is flagged with a specific error message, and the upload cannot be confirmed until errors are resolved.

### 12-3-schedule-upload-api-UNIT-013: Negative scheduled_quantity flagged as validation error
- Priority: P0
- Type: unit
- Given: A parsed row with scheduled_quantity = -10
- When: validate_row(row, row_number=2) is called
- Then: Returns a list containing a RowValidationError with field "scheduled_quantity" and a message indicating the quantity must be a positive integer
- Data: Row dict with {"date": "2026-02-16", "shift": "Day", "asset_name": "Grinder 1", "product_name": "Blend", "scheduled_quantity": "-10"}

### 12-3-schedule-upload-api-UNIT-014: Zero scheduled_quantity flagged as validation error
- Priority: P1
- Type: unit
- Given: A parsed row with scheduled_quantity = 0
- When: validate_row(row, row_number=3) is called
- Then: Returns a RowValidationError for field "scheduled_quantity" indicating quantity must be greater than 0
- Data: Row dict with scheduled_quantity "0"

### 12-3-schedule-upload-api-UNIT-015: Invalid date format flagged as validation error
- Priority: P0
- Type: unit
- Given: A parsed row with date = "not-a-date"
- When: validate_row(row, row_number=1) is called
- Then: Returns a RowValidationError for field "date" indicating the date format is invalid
- Data: Row dict with date "not-a-date"

### 12-3-schedule-upload-api-UNIT-016: Date in distant past (>90 days ago) flagged as validation error
- Priority: P1
- Type: unit
- Given: A parsed row with date = "2025-01-01" (more than 90 days in the past from today 2026-02-11)
- When: validate_row(row, row_number=1) is called
- Then: Returns a RowValidationError for field "date" indicating the date is too far in the past
- Data: Row dict with date "2025-01-01"

### 12-3-schedule-upload-api-UNIT-017: Date in far future (>365 days ahead) flagged as validation error
- Priority: P1
- Type: unit
- Given: A parsed row with date = "2028-01-01" (more than 365 days in the future)
- When: validate_row(row, row_number=1) is called
- Then: Returns a RowValidationError for field "date" indicating the date is too far in the future
- Data: Row dict with date "2028-01-01"

### 12-3-schedule-upload-api-UNIT-018: Empty shift value flagged as validation error
- Priority: P1
- Type: unit
- Given: A parsed row with shift = "" (empty string)
- When: validate_row(row, row_number=1) is called
- Then: Returns a RowValidationError for field "shift" indicating shift must be non-empty
- Data: Row dict with shift ""

### 12-3-schedule-upload-api-UNIT-019: Empty product_name flagged as validation error
- Priority: P1
- Type: unit
- Given: A parsed row with product_name = "" (empty string)
- When: validate_row(row, row_number=1) is called
- Then: Returns a RowValidationError for field "product_name" indicating product name must be non-empty
- Data: Row dict with product_name ""

### 12-3-schedule-upload-api-UNIT-020: Empty asset_name flagged as validation error
- Priority: P1
- Type: unit
- Given: A parsed row with asset_name = "" (empty string)
- When: validate_row(row, row_number=1) is called
- Then: Returns a RowValidationError for field "asset_name" indicating asset name must be non-empty
- Data: Row dict with asset_name ""

### 12-3-schedule-upload-api-UNIT-021: Multiple errors per row are all reported (not just the first)
- Priority: P0
- Type: unit
- Given: A parsed row with date = "invalid", shift = "", scheduled_quantity = "-5" (three simultaneous errors)
- When: validate_row(row, row_number=1) is called
- Then: Returns a list of 3 RowValidationError objects, one for each invalid field; all errors are reported, not just the first encountered
- Data: Row dict with multiple invalid fields

### 12-3-schedule-upload-api-UNIT-022: Missing required column headers detected at file level
- Priority: P0
- Type: unit
- Given: A CSV file with headers "date,shift,quantity" (missing asset_name and product_name columns)
- When: validate_headers(headers) is called
- Then: Returns a list of missing column names: ["asset_name", "product_name"]
- Data: Headers list ["date", "shift", "quantity"]

### 12-3-schedule-upload-api-UNIT-023: Empty file with only headers and no data rows rejected
- Priority: P1
- Type: unit
- Given: A CSV file containing only the header row and no data rows
- When: File-level validation is performed after parsing
- Then: Validation fails with an error indicating the file must contain at least 1 data row
- Data: CSV bytes "date,shift,asset_name,product_name,scheduled_quantity\n"

### 12-3-schedule-upload-api-INT-016: Preview with validation errors sets has_errors flag and prevents confirmation
- Priority: P0
- Type: integration
- Given: A CSV file where row 2 has negative quantity and row 3 has invalid date
- When: POST /api/v1/schedule/upload is called
- Then: Response status is 200; the preview response has has_errors=True; rows 2 and 3 each have their specific validation errors listed; the errors include field name and descriptive message
- Data: CSV with intentional validation errors in specific rows

### 12-3-schedule-upload-api-UNIT-024: Non-integer scheduled_quantity flagged as validation error
- Priority: P1
- Type: unit
- Given: A parsed row with scheduled_quantity = "12.5" (decimal, not integer)
- When: validate_row(row, row_number=1) is called
- Then: Returns a RowValidationError for field "scheduled_quantity" indicating quantity must be a positive integer
- Data: Row dict with scheduled_quantity "12.5"

### 12-3-schedule-upload-api-UNIT-025: Non-numeric scheduled_quantity flagged as validation error
- Priority: P1
- Type: unit
- Given: A parsed row with scheduled_quantity = "abc" (non-numeric string)
- When: validate_row(row, row_number=1) is called
- Then: Returns a RowValidationError for field "scheduled_quantity" indicating quantity must be a positive integer
- Data: Row dict with scheduled_quantity "abc"

### 12-3-schedule-upload-api-UNIT-026: Valid date formats accepted (ISO and common US format)
- Priority: P1
- Type: unit
- Given: Parsed rows with dates in different valid formats: "2026-02-16" (ISO), "02/16/2026" (MM/DD/YYYY)
- When: validate_row() is called for each row
- Then: No validation errors are returned for the date field in either case; both formats are accepted
- Data: Row dicts with different date format strings

### 12-3-schedule-upload-api-UNIT-027: Product matching identifies existing vs new products
- Priority: P0
- Type: unit
- Given: Product names ["Dark Roast 12oz", "New Blend XYZ"]; existing products in DB include "Dark Roast 12oz" (with UUID) but not "New Blend XYZ"
- When: match_products(product_names, existing_products) is called
- Then: Returns a dict where "Dark Roast 12oz" maps to its existing UUID; "New Blend XYZ" maps to None (indicating it's new and needs creation)
- Data: Product names list and existing_products dict

### 12-3-schedule-upload-api-INT-017: Supabase unavailable returns 503 error
- Priority: P1
- Type: integration
- Given: Supabase URL or key is not configured (settings return None)
- When: POST /api/v1/schedule/upload is called
- Then: Response status is 503; response body indicates Supabase is not configured
- Data: Valid CSV file; settings with supabase_url=None


edge_cases:
  - CSV with extra columns beyond the required 5 (should be ignored, not cause errors)
  - CSV with columns in different order than expected (should work via header matching)
  - Excel file with empty rows interspersed between data rows (should skip empty rows)
  - Very large valid file just under 5MB limit (should be accepted)
  - File with exactly 5MB (boundary condition for size limit)
  - CSV with trailing whitespace in cell values (should be trimmed)
  - CSV with quoted fields containing commas (standard CSV escaping)
  - Schedule upload for a single day with a single row (minimum valid upload)
  - Product name with special characters or unicode (should be handled)
  - Concurrent confirm requests for the same date range (race condition — documented as known limitation)
  - Asset name that is an exact substring of another asset (e.g., "Line A" vs "Filler Line A")

error_scenarios:
  - Completely empty file (0 bytes) — should return 400
  - File with only whitespace — should return error about no data rows
  - Malformed CSV (inconsistent column counts per row) — should handle gracefully
  - Corrupted Excel file (not a valid .xlsx) — should return 400 with parse error
  - Confirm request with empty rows list — should return 400
  - Confirm request referencing an asset_id that no longer exists — should return error
  - Database connection failure during confirm — should return 500 with generic error
  - File with all rows having validation errors — preview returns with has_errors=True, 0 valid rows
  - Expired JWT token during upload — should return 401
  - Invalid JWT token during confirm — should return 401

test_file_mapping:
  - 12-3-schedule-upload-api-INT-*: apps/api/tests/api/test_schedule.py
  - 12-3-schedule-upload-api-UNIT-*: apps/api/tests/services/test_schedule_parser.py

TEST SPEC END

---

## DESIGN: 12-4-schedule-upload-ui
**Timestamp:** 2026-02-11 11:48:07

DESIGN START
story_id: 12-4-schedule-upload-ui

files_to_modify:
  - path: apps/web/src/hooks/useScheduleUpload.ts
    action: create
    purpose: Custom hook managing file upload for preview (FormData POST to /api/v1/schedule/upload) and confirmation (JSON POST to /api/v1/schedule/upload/confirm), with loading/error/preview/confirm states. Follows useDailyActions pattern exactly (mountedRef, Supabase auth session, API_BASE_URL env var).

  - path: apps/web/src/components/schedule/ScheduleUploadZone.tsx
    action: create
    purpose: Drag-and-drop zone component with file picker button. Handles dragOver/dragLeave/drop events, validates file type (.csv/.xlsx), displays file info after selection. Pure presentational + local drag state — calls parent onFileSelected callback.

  - path: apps/web/src/components/schedule/SchedulePreviewTable.tsx
    action: create
    purpose: Renders parsed preview rows in a Tailwind-styled HTML table with status icons (green checkmark for matched, red warning for unmatched with suggestions, blue indicator for new product, red highlight for validation errors). Shows summary stats bar above table. Scrollable container for large uploads.

  - path: apps/web/src/app/(main)/settings/schedule-upload/page.tsx
    action: create
    purpose: Page component at /settings/schedule-upload route. Orchestrates ScheduleUploadZone → useScheduleUpload → SchedulePreviewTable flow. Manages Confirm Upload button (disabled when has_errors), loading spinner, success inline message, and redirect to /morning-report on confirmation.

  - path: apps/web/src/components/navigation/AppSidebar.tsx
    action: modify
    purpose: Add "Schedule Upload" nav item to the Settings nav group with Upload icon from lucide-react. Add Upload to the import list from lucide-react.

  - path: apps/web/src/components/schedule/__tests__/ScheduleUploadZone.test.tsx
    action: create
    purpose: Tests for drag-and-drop zone — file drop handler, file type validation (.csv/.xlsx accepted, others rejected), drag-active visual state, file info display after selection, Browse Files button triggering hidden input.

  - path: apps/web/src/components/schedule/__tests__/SchedulePreviewTable.test.tsx
    action: create
    purpose: Tests for preview table — rendering matched/unmatched/error/new-product rows with correct status icons and colors, summary stats display, error messages inline, empty state.

  - path: apps/web/src/components/schedule/__tests__/useScheduleUpload.test.tsx
    action: create
    purpose: Tests for the hook — mock fetch, verify state transitions (idle → loading → preview data), error handling (network error, auth error, server error), confirm flow (loading → success response), mountedRef cleanup.

patterns_to_use:
  - useDailyActions_hook_pattern: Create useScheduleUpload.ts following the exact pattern from useDailyActions.ts — 'use client' directive, mountedRef for unmount safety, createClient() from @/lib/supabase/client for session/token, API_BASE_URL from process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000', Authorization Bearer header, error status code mapping (401 → auth error, 4xx/5xx → descriptive messages), setState callback pattern
  - preferences_page_pattern: Follow PreferencesPage structure — container max-w-3xl py-8, header section (h1 + description), Card/CardContent/CardHeader for sections, inline success message (bg-primary/10 border-primary/20 rounded-lg with checkmark SVG), inline error message (bg-destructive/10 border-destructive/20 rounded-lg), Button component for actions, loading spinner (w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin)
  - handoff_test_pattern: Follow HandoffCard.test.tsx structure — vitest (describe/it/expect/vi/beforeEach), @testing-library/react (render/screen/fireEvent), vi.mock for next/navigation, test data factories with createMock* helpers, vi.clearAllMocks in beforeEach
  - sidebar_nav_pattern: Add item to navGroups Settings group items array as { href, label, icon } object with lucide-react icon component. Import Upload from lucide-react.
  - formdata_upload_pattern: Use native FormData API with fetch — append file, NO Content-Type header (browser sets multipart boundary automatically), Authorization Bearer token from Supabase session. Matches VoiceNoteRecorder.tsx upload pattern.
  - inline_messaging_pattern: No toast library exists in the project. Use inline success/error divs with Tailwind classes following the PreferencesPage pattern. Success message persists briefly before redirect.
  - domain_component_organization: Create components/schedule/ directory following components/handoff/ pattern — each component in its own file, __tests__/ subdirectory mirroring component names.

dependencies:
  - lucide-react: installed (already imported in AppSidebar.tsx; Upload icon available)
  - next/navigation: installed (useRouter for redirect after confirm)
  - react: installed (useState, useCallback, useRef, useEffect, DragEvent)
  - @/lib/supabase/client: installed (createClient for auth session)
  - @/components/ui/button: installed (Button component)
  - @/components/ui/card: installed (Card, CardContent, CardHeader, CardTitle, CardDescription)
  - @/components/ui/badge: installed (Badge for status indicators)
  - vitest: installed (test runner)
  - @testing-library/react: installed (render, screen, fireEvent)

acceptance_criteria_mapping:
  - AC1 (Drag-and-drop zone with file picker): apps/web/src/components/schedule/ScheduleUploadZone.tsx — Implements drag-and-drop zone with dashed border, "Drop CSV or Excel file here" text, "Browse Files" button (triggers hidden <input type="file" accept=".csv,.xlsx">), displays accepted formats ".csv, .xlsx", visual drag-active state (border-primary bg-primary/5). apps/web/src/app/(main)/settings/schedule-upload/page.tsx — Page at /settings/schedule-upload route. apps/web/src/components/navigation/AppSidebar.tsx — "Schedule Upload" link in Settings nav group.

  - AC2 (Preview table with match/error indicators): apps/web/src/components/schedule/SchedulePreviewTable.tsx — Receives SchedulePreviewResponse from hook, renders HTML table with columns [Status, Row#, Date, Shift, Asset, Product, Quantity, Issues]. Status column: CheckCircle icon (text-green-500) for matched, AlertTriangle icon (text-destructive) for unmatched with suggestions tooltip, CirclePlus icon (text-blue-500) for is_new_product, XCircle icon (text-destructive) for validation errors. Error rows get bg-destructive/5 background. Unmatched assets show suggestions in the Asset cell. New products show "New" Badge (text-blue-500). Errors displayed in Issues column. Summary stats bar shows: total_rows / matched_assets / new_products / error_count (derived from rows with errors.length > 0).

  - AC3 (Confirm Upload → success toast → redirect): apps/web/src/hooks/useScheduleUpload.ts — confirmUpload() calls POST /api/v1/schedule/upload/confirm with JSON body { rows: ScheduleConfirmRow[] } constructed from preview rows (only matched rows with asset_id). apps/web/src/app/(main)/settings/schedule-upload/page.tsx — "Confirm Upload" button calls confirmUpload, on success shows inline success message with rows_inserted count ("Successfully imported X schedule rows"), then after 1.5s redirects to /morning-report via useRouter().push('/morning-report').

  - AC4 (Confirm button disabled when errors exist): apps/web/src/app/(main)/settings/schedule-upload/page.tsx — "Confirm Upload" Button component has disabled={previewData.has_errors || isConfirming} prop. Visual disabled state via Button component's built-in disabled styling. Error rows are highlighted with bg-destructive/5 and error messages in Issues column per AC2.

risks:
  - API contract mismatch: The story Dev Notes describe a response shape with nested summary and asset_match objects, but the actual API (story 12-3, already implemented) uses a flatter SchedulePreviewResponse with rows[].asset_match_status (string), rows[].errors (RowValidationError[]), and top-level has_errors/matched_assets/new_products. Mitigation: The hook's TypeScript types will match the ACTUAL API schema from apps/api/app/schemas/schedule.py, not the story Dev Notes spec. This is verified by reading the implemented schema.

  - No toast component: The project uses inline success/error messages, not a toast library. The story says "success toast" but the codebase pattern is inline divs. Mitigation: Use the inline success message pattern from PreferencesPage (bg-primary/10 border with checkmark), displayed briefly before redirect. This is consistent with the codebase.

  - Confirm button data construction: The preview API returns ScheduleRowPreview objects (with asset_match_status, asset_id, errors, etc.) but the confirm API expects ScheduleConfirmRow objects (asset_id, product_name, scheduled_date, shift, scheduled_quantity). The UI must transform preview rows into confirm rows, filtering out rows with errors or unmatched assets. Mitigation: The confirmUpload function in the hook will map preview rows → confirm rows, filtering only rows where asset_match_status === 'matched' and errors.length === 0. The Confirm button is already disabled when has_errors is true, so all rows should be confirmable when the button is enabled.

  - Large file preview rendering: A schedule file with thousands of rows could cause rendering performance issues in the preview table. Mitigation: Use CSS overflow-y-auto with max-height for scrollable table container. For MVP this is sufficient; virtualized scrolling would be a future optimization if needed.

  - Redirect timing after success: Immediate redirect after confirm would prevent the user from seeing the success message. Mitigation: Show the success message for 1.5 seconds using setTimeout, then redirect. The timeout ref is cleaned up on unmount to prevent memory leaks.

estimated_test_files:
  - apps/web/src/components/schedule/__tests__/ScheduleUploadZone.test.tsx: Tests drag-and-drop behavior (onDrop fires callback with file, drag-active state toggles, invalid file type rejected with error, file name/size displayed after selection, Browse Files button triggers file input click, accepts .csv and .xlsx)
  - apps/web/src/components/schedule/__tests__/SchedulePreviewTable.test.tsx: Tests table rendering (matched row shows green checkmark, unmatched row shows red warning + suggestions, new product row shows blue indicator, error row shows red background + error messages, summary stats bar shows correct counts, empty rows array shows appropriate message)
  - apps/web/src/components/schedule/__tests__/useScheduleUpload.test.tsx: Tests hook state machine (initial state is idle, uploadForPreview transitions loading → success/error, confirmUpload transitions loading → success/error, auth error when no session, network error handling, mountedRef prevents state updates after unmount)

implementation_order:
  1. Create apps/web/src/hooks/useScheduleUpload.ts — Define TypeScript interfaces matching the actual API schema (ScheduleRowPreview with row_number, date, shift, asset_name, product_name, scheduled_quantity, asset_match_status, asset_id, suggestions, product_id, is_new_product, errors; SchedulePreviewResponse with parsed_rows_count, rows, has_errors, matched_assets, matched_products, new_products; ScheduleConfirmResponse with rows_inserted, products_created, total_processed). Implement uploadForPreview(file: File) using FormData POST to /api/v1/schedule/upload. Implement confirmUpload(previewRows: ScheduleRowPreview[]) that maps rows to ScheduleConfirmRow format and POSTs JSON to /api/v1/schedule/upload/confirm. Manage state: isUploading, isConfirming, error, previewData, confirmResult. Follow useDailyActions pattern for auth (createClient, getSession, Bearer token), mountedRef, and error handling.

  2. Create apps/web/src/components/schedule/ScheduleUploadZone.tsx — Props: onFileSelected(file: File), disabled, error (optional string for file validation error). Internal state: isDragActive, selectedFile (File | null). Handlers: onDragOver (preventDefault, setDragActive), onDragLeave (setDragActive false), onDrop (preventDefault, validate file extension, call onFileSelected or set local error), onBrowse (click hidden input ref). Render: Card with dashed border (border-dashed border-2), Upload icon from lucide-react, "Drop CSV or Excel file here" text, "or" divider, Browse Files Button, ".csv, .xlsx accepted" muted text. Drag-active state: border-primary bg-primary/5. After file selected: show file name, file size (formatted), and "Remove" button to clear. Error state: text-destructive below the zone.

  3. Create apps/web/src/components/schedule/SchedulePreviewTable.tsx — Props: previewData (SchedulePreviewResponse). Render summary stats bar (Badge components showing total/matched/new/errors counts with appropriate colors). Render scrollable table container (max-h-96 overflow-y-auto). Table columns: Status (icon), Row# (row_number), Date, Shift, Asset (name + match status), Product (name + new indicator), Quantity, Issues (error messages). Row coloring: bg-destructive/5 for rows with errors. Status icons: CheckCircle (text-green-500), AlertTriangle (text-amber-500 for suggested), XCircle (text-destructive for unmatched/errors). Import CheckCircle, AlertTriangle, XCircle, PlusCircle from lucide-react.

  4. Create apps/web/src/app/(main)/settings/schedule-upload/page.tsx — 'use client' page. Use useScheduleUpload hook and useRouter from next/navigation. Container with max-w-4xl py-8 (slightly wider than preferences for table). Header: "Schedule Upload" h1 + description. Three states: (A) Upload zone visible when no preview data — wire ScheduleUploadZone onFileSelected to hook's uploadForPreview. (B) Preview visible when previewData exists — show SchedulePreviewTable + action buttons ("Upload Different File" outline button to reset, "Confirm Upload" primary button disabled when has_errors or isConfirming, with spinner during confirm). (C) Success state — inline success message with rows_inserted count, then setTimeout redirect to /morning-report after 1.5s. Loading states: spinner overlay during upload and confirm. Error display: inline error message with retry option.

  5. Modify apps/web/src/components/navigation/AppSidebar.tsx — Add Upload to the lucide-react import list. Add { href: '/settings/schedule-upload', label: 'Schedule Upload', icon: <Upload className="w-5 h-5" /> } to the Settings nav group items array (after Preferences entry).

  6. Create apps/web/src/components/schedule/__tests__/ScheduleUploadZone.test.tsx — Test file drop (valid .csv calls onFileSelected, invalid .txt does not), drag state changes (isDragActive border class), Browse Files button clicks hidden input, file info display after selection, Remove button clears file. Mock data: File objects with name/size/type.

  7. Create apps/web/src/components/schedule/__tests__/SchedulePreviewTable.test.tsx — Test table rendering with mock SchedulePreviewResponse data: matched row shows green icon, unmatched row shows warning icon + suggestions text, new product shows blue badge, error row shows red background + error text in Issues column, summary stats are correct. Mock data: createMockPreviewResponse factory.

  8. Create apps/web/src/components/schedule/__tests__/useScheduleUpload.test.tsx — Test hook using renderHook from @testing-library/react. Mock fetch globally. Test uploadForPreview: sets isUploading true, calls fetch with FormData, sets previewData on success, sets error on failure. Test confirmUpload: sets isConfirming true, posts JSON, returns confirmResult. Test auth: when no session returns auth error. Test unmount: mountedRef prevents setState after unmount.
DESIGN END

---

## TEST_SPEC: 12-4-schedule-upload-ui
**Timestamp:** 2026-02-11 11:51:04

TEST SPEC START
story_id: 12-4-schedule-upload-ui
generated: 2026-02-11

test_specifications:

## AC1: Given a user navigates to `/settings/schedule-upload`, When the page loads, Then a drag-and-drop zone is displayed with "Drop CSV or Excel file here" and a file picker button, And accepted formats are shown: .csv, .xlsx

### 12-4-schedule-upload-ui-UNIT-001: ScheduleUploadZone renders drag-and-drop zone with instructional text
- Priority: P0
- Type: unit
- Given: The ScheduleUploadZone component is rendered with default props (onFileSelected callback)
- When: The component mounts
- Then: A dashed-border drop zone is visible containing the text "Drop CSV or Excel file here", AND a "Browse Files" button is displayed, AND the accepted formats ".csv, .xlsx" text is visible
- Data: No file data required; default component props with vi.fn() for onFileSelected

### 12-4-schedule-upload-ui-UNIT-002: ScheduleUploadZone Browse Files button triggers hidden file input
- Priority: P0
- Type: unit
- Given: The ScheduleUploadZone component is rendered
- When: The user clicks the "Browse Files" button
- Then: The hidden file input element receives a click event (triggering the native file dialog), AND the file input has accept=".csv,.xlsx" attribute
- Data: Mock click on hidden input via ref spy

### 12-4-schedule-upload-ui-UNIT-003: ScheduleUploadZone shows visual drag-active state on drag over
- Priority: P1
- Type: unit
- Given: The ScheduleUploadZone component is rendered in its default (non-active) state
- When: A user drags a file over the drop zone (dragOver event fires)
- Then: The drop zone updates to a drag-active visual state (border-primary and bg-primary/5 classes applied), AND when the user drags out (dragLeave event fires), the zone returns to default styling
- Data: Simulate DragEvent with fireEvent.dragOver and fireEvent.dragLeave

### 12-4-schedule-upload-ui-UNIT-004: Schedule Upload page renders at /settings/schedule-upload route
- Priority: P0
- Type: unit
- Given: The Schedule Upload page component is rendered
- When: The page mounts
- Then: The page heading "Schedule Upload" is visible, AND the ScheduleUploadZone is displayed, AND the "Confirm Upload" button is NOT visible (no preview data yet)
- Data: Mock useScheduleUpload hook returning initial idle state (no previewData)

### 12-4-schedule-upload-ui-UNIT-005: AppSidebar includes Schedule Upload navigation link in Settings group
- Priority: P1
- Type: unit
- Given: The AppSidebar component is rendered for an authenticated user
- When: The Settings nav group is expanded/visible
- Then: A "Schedule Upload" link is present with href="/settings/schedule-upload", AND it includes an Upload icon from lucide-react
- Data: Mock auth context and sidebar rendering

### 12-4-schedule-upload-ui-UNIT-006: ScheduleUploadZone rejects invalid file types
- Priority: P0
- Type: unit
- Given: The ScheduleUploadZone component is rendered
- When: A user drops a file with an unsupported extension (e.g., .pdf, .txt, .json)
- Then: The onFileSelected callback is NOT called, AND an error message is shown indicating the file type is not supported
- Data: File object with name "report.pdf", type "application/pdf"

### 12-4-schedule-upload-ui-UNIT-007: ScheduleUploadZone accepts .csv file via drag and drop
- Priority: P0
- Type: unit
- Given: The ScheduleUploadZone component is rendered
- When: A user drops a valid .csv file onto the drop zone
- Then: The onFileSelected callback is called with the dropped File object, AND the file name and formatted file size are displayed in the zone, AND a "Remove" option is visible to clear the selection
- Data: File object with name "schedule.csv", size 2048, type "text/csv"

### 12-4-schedule-upload-ui-UNIT-008: ScheduleUploadZone accepts .xlsx file via drag and drop
- Priority: P0
- Type: unit
- Given: The ScheduleUploadZone component is rendered
- When: A user drops a valid .xlsx file onto the drop zone
- Then: The onFileSelected callback is called with the dropped File object, AND the file name and formatted file size are displayed
- Data: File object with name "schedule.xlsx", size 15360, type "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

### 12-4-schedule-upload-ui-UNIT-009: ScheduleUploadZone Remove button clears selected file
- Priority: P1
- Type: unit
- Given: The ScheduleUploadZone component has a file already selected (showing file name and size)
- When: The user clicks the "Remove" button/option
- Then: The file info is cleared, AND the drop zone returns to its initial state with "Drop CSV or Excel file here" text
- Data: Render with file selection, then fire click on Remove

### 12-4-schedule-upload-ui-UNIT-010: ScheduleUploadZone accepts .csv file via Browse Files button
- Priority: P1
- Type: unit
- Given: The ScheduleUploadZone component is rendered
- When: The user selects a .csv file via the hidden file input (change event fires)
- Then: The onFileSelected callback is called with the selected File object
- Data: File object with name "weekly_schedule.csv", simulate change event on hidden input


## AC2: Given a user drops or selects a valid file, When the file is uploaded to the preview endpoint, Then a preview table is shown with all parsed rows, And matched assets show with a green checkmark, And unmatched assets show with a red warning and suggested matches, And new products show with a blue "will be created" indicator, And validation errors are highlighted in red with specific messages

### 12-4-schedule-upload-ui-INT-001: useScheduleUpload hook uploads file and returns preview data
- Priority: P0
- Type: integration
- Given: The useScheduleUpload hook is initialized with a mock API URL, AND a valid Supabase session exists with access_token
- When: uploadForPreview(file) is called with a File object
- Then: A POST request is made to /api/v1/schedule/upload with FormData body containing the file, AND Authorization header includes "Bearer {access_token}", AND Content-Type header is NOT manually set (browser auto-sets multipart boundary), AND on success, previewData state is populated with the SchedulePreviewResponse, AND isUploading transitions from false → true → false
- Data: Mock fetch returning SchedulePreviewResponse with 3 rows (1 matched, 1 suggested, 1 with errors), mock Supabase session with access_token "mock-token"

### 12-4-schedule-upload-ui-UNIT-011: SchedulePreviewTable renders matched asset row with green checkmark
- Priority: P0
- Type: unit
- Given: The SchedulePreviewTable component receives previewData with a row where asset_match_status is "matched" and errors is empty
- When: The component renders
- Then: The row displays a green checkmark icon (text-green-500), AND the row_number, date, shift, asset_name, product_name, and scheduled_quantity are all visible in appropriate columns, AND no error highlights are present on the row
- Data: createMockPreviewResponse with one row: { row_number: 1, asset_match_status: "matched", asset_id: "uuid-1", errors: [], is_new_product: false }

### 12-4-schedule-upload-ui-UNIT-012: SchedulePreviewTable renders unmatched asset row with red warning and suggestions
- Priority: P0
- Type: unit
- Given: The SchedulePreviewTable component receives previewData with a row where asset_match_status is "suggested" and suggestions contains asset names
- When: The component renders
- Then: The row displays a warning icon (text-amber-500 or text-destructive), AND the suggestions are displayed in the Asset column or as a tooltip/inline list, AND the row has a warning visual treatment
- Data: createMockPreviewResponse with one row: { row_number: 2, asset_match_status: "suggested", asset_id: null, suggestions: ["Grinder 1", "Grinder 2"], errors: [] }

### 12-4-schedule-upload-ui-UNIT-013: SchedulePreviewTable renders unmatched asset row with no suggestions
- Priority: P1
- Type: unit
- Given: The SchedulePreviewTable component receives previewData with a row where asset_match_status is "unmatched" and suggestions is empty
- When: The component renders
- Then: The row displays a red warning/error icon (text-destructive), AND no suggestions are shown, AND the row has error visual treatment
- Data: createMockPreviewResponse with one row: { row_number: 3, asset_match_status: "unmatched", suggestions: [], errors: [] }

### 12-4-schedule-upload-ui-UNIT-014: SchedulePreviewTable renders new product row with blue indicator
- Priority: P0
- Type: unit
- Given: The SchedulePreviewTable component receives previewData with a row where is_new_product is true
- When: The component renders
- Then: The product column shows a blue "New" badge or "will be created" indicator (text-blue-500), AND the product name is displayed alongside the indicator
- Data: createMockPreviewResponse with one row: { row_number: 1, is_new_product: true, product_id: null, asset_match_status: "matched", errors: [] }

### 12-4-schedule-upload-ui-UNIT-015: SchedulePreviewTable renders validation error row with red highlight and messages
- Priority: P0
- Type: unit
- Given: The SchedulePreviewTable component receives previewData with a row that has validation errors
- When: The component renders
- Then: The row has a red background highlight (bg-destructive/5), AND error messages are displayed in the Issues column with specific field and message text, AND a red error icon is shown in the Status column
- Data: createMockPreviewResponse with one row: { row_number: 4, errors: [{ row_number: 4, field: "scheduled_quantity", message: "Scheduled quantity must be a positive integer" }], asset_match_status: "matched" }

### 12-4-schedule-upload-ui-UNIT-016: SchedulePreviewTable displays summary stats bar
- Priority: P0
- Type: unit
- Given: The SchedulePreviewTable component receives previewData with mixed row statuses
- When: The component renders
- Then: A summary stats bar is visible showing: total rows count (parsed_rows_count), number of matched assets (matched_assets.length), number of new products (new_products.length), AND error count (derived from rows with errors.length > 0)
- Data: createMockPreviewResponse with parsed_rows_count: 5, matched_assets: ["Grinder 1", "Grinder 2"], new_products: ["New Blend 1"], has_errors: true, rows containing 1 row with errors

### 12-4-schedule-upload-ui-UNIT-017: SchedulePreviewTable renders all expected columns
- Priority: P1
- Type: unit
- Given: The SchedulePreviewTable component receives previewData with at least one row
- When: The component renders
- Then: The table has columns for: Status, Row #, Date, Shift, Asset, Product, Quantity, and Issues
- Data: createMockPreviewResponse with a single matched row

### 12-4-schedule-upload-ui-UNIT-018: SchedulePreviewTable renders multiple error messages per row
- Priority: P1
- Type: unit
- Given: The SchedulePreviewTable component receives previewData with a row containing multiple validation errors
- When: The component renders
- Then: All error messages are displayed in the Issues column for that row
- Data: createMockPreviewResponse with one row having errors: [{ field: "date", message: "Invalid date format" }, { field: "scheduled_quantity", message: "Must be positive" }]

### 12-4-schedule-upload-ui-UNIT-019: SchedulePreviewTable is scrollable for large uploads
- Priority: P2
- Type: unit
- Given: The SchedulePreviewTable component receives previewData with many rows (e.g., 50+)
- When: The component renders
- Then: The table container has overflow-y-auto and a max-height constraint for scrollability
- Data: createMockPreviewResponse with 50+ rows

### 12-4-schedule-upload-ui-INT-002: Page shows preview table after successful file upload
- Priority: P0
- Type: integration
- Given: The Schedule Upload page is rendered and the upload zone is visible
- When: A user selects a valid file, AND the upload completes successfully with preview data
- Then: The upload zone is replaced/hidden, AND the SchedulePreviewTable is shown with the returned rows, AND the "Confirm Upload" button becomes visible
- Data: Mock useScheduleUpload returning previewData after file selection


## AC3: Given the preview has no errors, When the user clicks "Confirm Upload", Then the data is committed to the database, And a success toast shows with count of rows inserted, And the user is redirected to the morning report

### 12-4-schedule-upload-ui-INT-003: useScheduleUpload hook confirms upload and returns success response
- Priority: P0
- Type: integration
- Given: The useScheduleUpload hook has previewData loaded with no errors (has_errors: false), AND a valid Supabase session exists
- When: confirmUpload() is called with the preview rows
- Then: A POST request is made to /api/v1/schedule/upload/confirm with JSON body containing rows mapped to ScheduleConfirmRow format (asset_id, product_name, scheduled_date, shift, scheduled_quantity), AND Authorization header includes "Bearer {access_token}", AND on success, confirmResult state is populated with { rows_inserted, products_created, total_processed }, AND isConfirming transitions from false → true → false
- Data: Mock fetch returning ScheduleConfirmResponse { rows_inserted: 3, products_created: 1, total_processed: 3 }, preview rows with matched assets

### 12-4-schedule-upload-ui-INT-004: Page shows success message and redirects after confirm
- Priority: P0
- Type: integration
- Given: The Schedule Upload page is showing a preview table with no errors, AND the "Confirm Upload" button is enabled
- When: The user clicks "Confirm Upload" and the API returns success
- Then: A loading spinner is shown during the request, AND on success an inline success message appears with the count of rows inserted (e.g., "Successfully imported 3 schedule rows"), AND after approximately 1.5 seconds, the user is redirected to /morning-report via router.push
- Data: Mock useScheduleUpload returning confirmResult with rows_inserted: 3, mock useRouter with push spy, use vi.useFakeTimers for timing

### 12-4-schedule-upload-ui-UNIT-020: Confirm Upload button is enabled when preview has no errors
- Priority: P0
- Type: unit
- Given: The Schedule Upload page has previewData with has_errors: false
- When: The preview table and action buttons are rendered
- Then: The "Confirm Upload" button is enabled (not disabled), AND clicking it triggers the confirmUpload function
- Data: Mock useScheduleUpload with previewData { has_errors: false, rows: [...] }

### 12-4-schedule-upload-ui-UNIT-021: Confirm Upload button shows loading spinner during confirmation
- Priority: P1
- Type: unit
- Given: The Schedule Upload page is in the confirming state (isConfirming: true)
- When: The component renders
- Then: The "Confirm Upload" button shows a loading spinner, AND the button is disabled to prevent double-clicks
- Data: Mock useScheduleUpload with isConfirming: true

### 12-4-schedule-upload-ui-INT-005: Success message displays correct row count from API response
- Priority: P1
- Type: integration
- Given: The confirm API returns rows_inserted: 7, products_created: 2
- When: The success state is rendered on the page
- Then: The inline success message includes "7" (rows inserted count), AND optionally mentions "2" products created
- Data: Mock confirmResult { rows_inserted: 7, products_created: 2, total_processed: 7 }

### 12-4-schedule-upload-ui-INT-006: Redirect timeout is cleaned up on unmount
- Priority: P2
- Type: integration
- Given: The Schedule Upload page shows a success message with the redirect timeout pending
- When: The component unmounts before the 1.5s redirect fires
- Then: The timeout is cleared and no state updates occur (no "setState on unmounted component" error), AND router.push is NOT called
- Data: vi.useFakeTimers, unmount the component before advancing timers


## AC4: Given the preview has errors, When the user views the preview, Then the "Confirm Upload" button is disabled, And error rows are clearly highlighted with fix suggestions

### 12-4-schedule-upload-ui-UNIT-022: Confirm Upload button is disabled when preview has errors
- Priority: P0
- Type: unit
- Given: The Schedule Upload page has previewData with has_errors: true
- When: The preview table and action buttons are rendered
- Then: The "Confirm Upload" button is disabled (has disabled attribute), AND the button has visual disabled styling
- Data: Mock useScheduleUpload with previewData { has_errors: true, rows: [row with errors] }

### 12-4-schedule-upload-ui-UNIT-023: Error rows are visually distinct from valid rows
- Priority: P0
- Type: unit
- Given: The SchedulePreviewTable receives previewData with a mix of valid rows and error rows
- When: The component renders
- Then: Rows with errors have a red background highlight (bg-destructive/5), AND rows without errors do NOT have the red background, AND the visual distinction is clear between error and non-error rows
- Data: createMockPreviewResponse with 2 valid rows (no errors) and 2 error rows (with errors array populated)

### 12-4-schedule-upload-ui-UNIT-024: Error rows display fix suggestions for unmatched assets
- Priority: P1
- Type: unit
- Given: The SchedulePreviewTable receives previewData with a row where asset_match_status is "suggested" and suggestions are provided
- When: The component renders
- Then: The suggested asset names are displayed near the unmatched asset name as fix suggestions (e.g., "Did you mean: Grinder 1, Grinder 2?")
- Data: createMockPreviewResponse with one row: { asset_match_status: "suggested", suggestions: ["Grinder 1", "Grinder 2"] }

### 12-4-schedule-upload-ui-UNIT-025: Error rows display specific validation error messages
- Priority: P0
- Type: unit
- Given: The SchedulePreviewTable receives previewData with rows containing validation errors
- When: The component renders
- Then: Each error's field name and message are displayed in the Issues column (e.g., "scheduled_quantity: Must be a positive integer")
- Data: createMockPreviewResponse with errors: [{ row_number: 3, field: "scheduled_quantity", message: "Scheduled quantity must be a positive integer" }]


## Additional Hook Tests (Cross-cutting for AC1-AC4)

### 12-4-schedule-upload-ui-INT-007: useScheduleUpload returns auth error when no session exists
- Priority: P0
- Type: integration
- Given: The useScheduleUpload hook is initialized, AND Supabase getSession returns null session
- When: uploadForPreview(file) is called
- Then: The hook sets error state to an auth error message (e.g., "Your session has expired. Please log in again."), AND isUploading returns to false, AND no fetch request is made
- Data: Mock Supabase getSession returning { data: { session: null } }

### 12-4-schedule-upload-ui-INT-008: useScheduleUpload handles network error gracefully
- Priority: P0
- Type: integration
- Given: The useScheduleUpload hook is initialized with a valid session
- When: uploadForPreview(file) is called, AND fetch throws a network error (TypeError: Failed to fetch)
- Then: The hook sets error state to a network/server error message, AND isUploading returns to false, AND previewData remains null
- Data: Mock fetch rejecting with TypeError("Failed to fetch")

### 12-4-schedule-upload-ui-INT-009: useScheduleUpload handles 401 response
- Priority: P1
- Type: integration
- Given: The useScheduleUpload hook is initialized with a valid session
- When: uploadForPreview(file) is called, AND the API returns a 401 status
- Then: The hook sets error state to an auth error message, AND isUploading returns to false
- Data: Mock fetch returning { ok: false, status: 401 }

### 12-4-schedule-upload-ui-INT-010: useScheduleUpload handles 500 server error response
- Priority: P1
- Type: integration
- Given: The useScheduleUpload hook is initialized with a valid session
- When: uploadForPreview(file) is called, AND the API returns a 500 status
- Then: The hook sets error state to a server error message, AND isUploading returns to false
- Data: Mock fetch returning { ok: false, status: 500 }

### 12-4-schedule-upload-ui-INT-011: useScheduleUpload mountedRef prevents state updates after unmount
- Priority: P1
- Type: integration
- Given: The useScheduleUpload hook is rendered, AND uploadForPreview is called
- When: The component unmounts before the fetch resolves
- Then: No state update occurs (no React warning), AND the mountedRef prevents setState calls
- Data: renderHook, call uploadForPreview, unmount, then resolve the pending fetch

### 12-4-schedule-upload-ui-INT-012: useScheduleUpload confirmUpload filters and maps rows correctly
- Priority: P0
- Type: integration
- Given: The useScheduleUpload hook has previewData with mixed rows (matched, suggested, error)
- When: confirmUpload() is called
- Then: Only rows with asset_match_status "matched" and no errors are included in the POST body, AND each row is mapped to ScheduleConfirmRow format: { asset_id, product_name, scheduled_date (from date), shift, scheduled_quantity (as integer) }
- Data: Preview with 3 rows: 1 matched (no errors), 1 suggested, 1 with errors; verify only the matched row appears in fetch body

### 12-4-schedule-upload-ui-INT-013: useScheduleUpload handles confirm API error
- Priority: P1
- Type: integration
- Given: The useScheduleUpload hook has previewData loaded
- When: confirmUpload() is called, AND the confirm API returns a non-ok response (e.g., 422)
- Then: The hook sets error state to an appropriate error message, AND isConfirming returns to false, AND previewData is preserved (not cleared)
- Data: Mock fetch for confirm endpoint returning { ok: false, status: 422 }


## Page-Level Integration Tests

### 12-4-schedule-upload-ui-INT-014: Page shows loading spinner during file upload
- Priority: P1
- Type: integration
- Given: The Schedule Upload page is rendered with the upload zone visible
- When: A file is selected and upload begins (isUploading: true)
- Then: A loading spinner is displayed, AND the upload zone may be disabled or overlaid
- Data: Mock useScheduleUpload with isUploading: true

### 12-4-schedule-upload-ui-INT-015: Page displays error state with retry option
- Priority: P1
- Type: integration
- Given: The Schedule Upload page is rendered
- When: The file upload fails with an error
- Then: An error message is displayed (inline, following PreferencesPage pattern), AND a retry option/button is available, AND clicking retry re-triggers the upload
- Data: Mock useScheduleUpload with error: "Something went wrong on our end."

### 12-4-schedule-upload-ui-INT-016: Page allows uploading a different file after preview
- Priority: P1
- Type: integration
- Given: The Schedule Upload page is showing a preview table
- When: The user clicks "Upload Different File" button
- Then: The preview table is cleared, AND the upload zone is shown again for a new file selection
- Data: Mock useScheduleUpload with previewData, then verify reset behavior


edge_cases:
  - Empty file uploaded (0 bytes) — should show validation error before API call or API returns error
  - File with only headers and no data rows — API returns parsed_rows_count: 0, UI should show empty state message
  - Very large file (1000+ rows) — table should be scrollable, no browser freeze
  - File with all rows having errors — Confirm button disabled, all rows highlighted red
  - File with all rows matched perfectly — Confirm button enabled, all rows have green checkmarks
  - File with mixed new products and matched products — both blue and green indicators shown correctly
  - User drops multiple files at once — only the first file should be processed, or an error shown
  - User navigates away during upload — mountedRef prevents state updates, no memory leaks
  - Session expires between preview and confirm — auth error shown on confirm attempt
  - File with special characters in asset/product names — rendered correctly in table without XSS
  - Duplicate file upload (same file dropped twice) — should replace previous preview, not duplicate

error_scenarios:
  - Network disconnection during upload (fetch throws TypeError)
  - API returns 401 Unauthorized (expired/invalid session)
  - API returns 500 Internal Server Error
  - API returns 422 Unprocessable Entity (malformed file)
  - API returns unexpected response shape (non-JSON or missing fields)
  - Supabase getSession returns null (unauthenticated user reached page somehow)
  - Confirm API fails after successful preview
  - Browser does not support drag-and-drop (graceful degradation to file input only)
  - File input onChange fires with no files selected (user cancels file dialog)
  - Redirect to /morning-report fails or is interrupted by unmount

test_file_mapping:
  - 12-4-schedule-upload-ui-UNIT-001 to UNIT-010: apps/web/src/components/schedule/__tests__/ScheduleUploadZone.test.tsx
  - 12-4-schedule-upload-ui-UNIT-011 to UNIT-019: apps/web/src/components/schedule/__tests__/SchedulePreviewTable.test.tsx
  - 12-4-schedule-upload-ui-UNIT-020 to UNIT-025: apps/web/src/components/schedule/__tests__/SchedulePreviewTable.test.tsx (AC4 rows) and page-level tests in apps/web/src/app/(main)/settings/schedule-upload/__tests__/page.test.tsx
  - 12-4-schedule-upload-ui-INT-001, INT-007 to INT-013: apps/web/src/hooks/__tests__/useScheduleUpload.test.ts
  - 12-4-schedule-upload-ui-INT-002 to INT-006, INT-014 to INT-016: apps/web/src/app/(main)/settings/schedule-upload/__tests__/page.test.tsx
  - 12-4-schedule-upload-ui-UNIT-005: apps/web/src/components/navigation/__tests__/AppSidebar.test.tsx (if exists, otherwise inline in page test)

TEST SPEC END

---

## DESIGN: 12-5-schedule-attainment-api
**Timestamp:** 2026-02-11 12:56:10

DESIGN START
story_id: 12-5-schedule-attainment-api

files_to_modify:
  - path: apps/api/app/schemas/production.py
    action: modify
    purpose: Add ScheduleAttainmentResponse, WorkcenterAttainment, ProductAttainment, VarianceCallout Pydantic models alongside existing WorkcenterSummaryResponse models. This file already contains production schemas from Story 11.1 (AssetDetail, WorkcenterEntry, WorkcenterSummaryResponse) so adding schedule attainment models here is the natural location.

  - path: apps/api/app/api/production.py
    action: modify
    purpose: Add GET /schedule-attainment endpoint to the existing production router. The endpoint accepts `date` (required, str YYYY-MM-DD) and `area` (optional, str) query params, uses get_current_user dependency for auth, queries production_schedule/production_actuals/products/assets from Supabase, computes per-workcenter attainment and variance callouts, and returns ScheduleAttainmentResponse. Follows the existing get_workcenter_summary pattern closely.

  - path: apps/api/tests/api/test_schedule_attainment.py
    action: create
    purpose: API integration tests for the schedule-attainment endpoint covering all 5 acceptance criteria: happy path with matched schedule/actuals, product swap variance callouts, empty schedule response, authentication requirement, and area filtering.

patterns_to_use:
  - supabase_client_helper: Reuse existing `get_supabase_client()` async function already in production.py (lines 108-119); no duplication needed since the new endpoint is in the same file
  - auth_dependency: Use `current_user: CurrentUser = Depends(get_current_user)` from app.core.security (same pattern as get_throughput_data at line 140 and get_workcenter_summary at line 372)
  - error_handling: try/except HTTPException re-raise, generic Exception → logger.error + 500 (matching production.py lines 308-315 and 493-500)
  - schema_file_pattern: Add new models to existing apps/api/app/schemas/production.py (which already has AssetDetail, WorkcenterEntry, WorkcenterSummaryResponse), import them in production.py alongside existing imports
  - query_pattern: Use client.table().select().eq().execute() Supabase query builder pattern (matching production.py lines 160, 200, 336, 396, 412)
  - response_model_pattern: Use response_model parameter on @router.get() decorator (matching line 128)
  - test_fixture_pattern: Use conftest.py `client` and `mock_verify_jwt` fixtures; create local `mock_supabase_client` fixture patching `app.api.production.get_supabase_client` (matching test_production_workcenter.py lines 24-29 and _make_table_mock helper pattern)
  - empty_result_with_message: Return HTTP 200 with has_data=False and message string when no schedule exists, matching WorkcenterSummaryResponse message pattern (production.py lines 403-408)
  - area_filtering: Apply area filter via Python dict comprehension on assets_map, matching the throughput endpoint pattern (production.py lines 182-186)

dependencies:
  - fastapi: installed (>=0.109.0)
  - pydantic: installed (>=2.0.0)
  - supabase: installed (>=2.0.0)
  - pytest: installed (test runner)

acceptance_criteria_mapping:
  - AC1 (Per-workcenter schedule attainment with product breakdown): apps/api/app/api/production.py — new `get_schedule_attainment()` endpoint function. Queries `production_schedule` filtered by `scheduled_date=date`, queries `production_actuals` filtered by `production_date=date`, queries `assets` for area grouping and `products` for name resolution. Groups by asset area (workcenter). For each workcenter, builds a list of `ProductAttainment` objects with scheduled_quantity, actual_quantity, and attainment_pct. Calculates overall_attainment_pct as weighted average (sum actual / sum scheduled * 100). Identifies products scheduled but not produced and products produced but not scheduled. Response model: `ScheduleAttainmentResponse` from apps/api/app/schemas/production.py containing date, workcenters list, message, has_data.

  - AC2 (Product swap variance callouts): apps/api/app/api/production.py — within `get_schedule_attainment()`. After matching schedule and actuals on (asset_id, shift), when actual.product_id differs from schedule.product_id, generate a `VarianceCallout` with variance_type="swap", asset_name from assets lookup, and a human-readable message like "Roaster 1 ran Colombian instead of scheduled Brazilian — X units of Brazilian still needed". When a schedule entry has no matching actual → variance_type="missing" with message like "Scheduled Brazilian but no production recorded". When an actual has no matching schedule → variance_type="unscheduled" with message like "Produced Colombian but not scheduled". Schema: `VarianceCallout` model in apps/api/app/schemas/production.py.

  - AC3 (No schedule data returns 200 with message): apps/api/app/api/production.py — within `get_schedule_attainment()`. After querying `production_schedule` with the date filter, if no rows returned, immediately return `ScheduleAttainmentResponse(date=date, workcenters=[], has_data=False, message="No schedule data for this date")`.

  - AC4 (Authentication required — 401 without token): apps/api/app/api/production.py — the endpoint uses `current_user: CurrentUser = Depends(get_current_user)` which raises 401 via HTTPBearer(auto_error=True) when no Authorization header is provided. No additional code needed; verified by test. The endpoint is already accessible at both `/api/production/schedule-attainment` and `/api/v1/production/schedule-attainment` since main.py registers production.router at both prefixes (lines 68 and 70).

  - AC5 (Optional area query parameter filtering): apps/api/app/api/production.py — the endpoint accepts `area: Optional[str] = Query(None, ...)`. When area is provided, filter the assets_map to only include assets whose area matches (case-insensitive), so the response only contains workcenters for that area. This matches the exact pattern used in get_throughput_data (lines 182-186).

risks:
  - Supabase query limitations: The Supabase query builder cannot do JOINs. Mitigation: Fetch all four tables (production_schedule, production_actuals, products, assets) as separate queries filtered by date, then join in Python using dictionary lookups. This is consistent with the existing workcenter-summary endpoint pattern which also fetches assets, daily_summaries, and shift_targets as separate queries.

  - Matching schedule to actuals: The join key is (asset_id, shift) on a given date, not a single composite key. A single asset on a single shift may have multiple schedule entries (different products) and multiple actuals entries (different products). Mitigation: Group schedule entries by (asset_id, shift) into a dict of lists, and similarly for actuals. Then for each (asset_id, shift) pair, compare product sets to detect swaps, missing production, and unscheduled production.

  - Shift value inconsistency: Seed data uses 'Day'/'Night' shifts but production_schedule.shift is TEXT with no constraint. Mitigation: Match on exact shift string values; the endpoint is agnostic to shift naming conventions.

  - Large data volume: A date with many assets and products could return a large response. Mitigation: For MVP, this is acceptable. The area filter (AC5) provides a way to scope results. No pagination is specified in the story.

  - Division by zero in attainment calculation: If scheduled_quantity is 0 for a product. Mitigation: Guard with the same pattern as calculate_percentage (production.py line 99-105) — return 100.0 when scheduled is 0.

  - Weighted average calculation: overall_attainment_pct should be sum(actual) / sum(scheduled) * 100 across all products in a workcenter, not an average of individual attainment_pcts. Mitigation: Use weighted calculation explicitly (total_actual / total_scheduled * 100) with zero-division guard.

estimated_test_files:
  - apps/api/tests/api/test_schedule_attainment.py: Tests for all 5 ACs: (1) Happy path — schedule+actuals data returns per-workcenter breakdown with product attainment and overall %, (2) Product swap detection — different product on same asset/shift generates variance callout with correct message, (3) Missing production — schedule exists but no actual generates "missing" callout, (4) Unscheduled production — actual exists but no schedule generates "unscheduled" callout, (5) Empty response — no schedule data returns 200 with has_data=False and message, (6) Area filtering — only returns workcenters matching area param, (7) Authentication — 401 without token, (8) Both router paths accessible (/api/production and /api/v1/production), (9) Supabase error returns 500

implementation_order:
  1. Add schema models to apps/api/app/schemas/production.py: Add `ProductAttainment` (product_name, product_id, scheduled_quantity, actual_quantity, attainment_pct), `VarianceCallout` (asset_name, message, variance_type), `WorkcenterScheduleAttainment` (workcenter, products list, variances list, overall_attainment_pct), `ScheduleAttainmentResponse` (date, workcenters list, message, has_data). Use the name `WorkcenterScheduleAttainment` to avoid collision with the existing `WorkcenterEntry` model. Include ConfigDict with json_schema_extra example following the financial.py pattern.

  2. Update imports in apps/api/app/api/production.py: Add the new schema models to the existing import block from `app.schemas.production` (line 21-25). Add `ScheduleAttainmentResponse`, `WorkcenterScheduleAttainment`, `ProductAttainment`, `VarianceCallout` to the import list.

  3. Implement the GET /schedule-attainment endpoint in apps/api/app/api/production.py: Add `@router.get("/schedule-attainment", response_model=ScheduleAttainmentResponse, ...)` after the existing workcenter-summary endpoint (after line 500). The function signature: `async def get_schedule_attainment(date: str = Query(..., description="Date in YYYY-MM-DD format"), area: Optional[str] = Query(None, description="Filter by plant area"), current_user: CurrentUser = Depends(get_current_user)) -> ScheduleAttainmentResponse`. Implementation steps within the function:
     a. Get Supabase client via existing get_supabase_client()
     b. Query production_schedule filtered by scheduled_date=date
     c. If no schedule data, return early with has_data=False and message per AC3
     d. Query production_actuals filtered by production_date=date
     e. Query assets (id, name, area) and products (id, name) for name resolution
     f. Build assets_map (id → {name, area}), products_map (id → name)
     g. Apply area filter on assets_map if area param provided (AC5)
     h. Group schedule entries by (asset_id, shift) → list of {product_id, scheduled_quantity}
     i. Group actuals entries by (asset_id, shift) → list of {product_id, actual_quantity}
     j. For each asset_id that appears in schedule OR actuals (filtered to assets_map):
        - Determine workcenter from assets_map[asset_id]["area"]
        - For each shift on this asset:
          - Build product attainment: match schedule product_ids to actuals product_ids
          - For scheduled products with matching actuals: compute attainment_pct
          - For scheduled products with no matching actual: add "missing" VarianceCallout
          - For actual products with no matching schedule: add "unscheduled" VarianceCallout
          - For actual products that differ from scheduled on same (asset, shift): add "swap" VarianceCallout with message like "{asset_name} ran {actual_product} instead of scheduled {scheduled_product} — {remaining} units of {scheduled_product} still needed"
        - Compute overall_attainment_pct = (sum all actual_quantity / sum all scheduled_quantity) * 100
     k. Build WorkcenterScheduleAttainment entries grouped by area
     l. Return ScheduleAttainmentResponse with date, workcenters, has_data=True
     m. Wrap in try/except following existing error_handling pattern

  4. Create test file apps/api/tests/api/test_schedule_attainment.py: Use conftest.py `client` and `mock_verify_jwt` fixtures. Create local `mock_supabase_client` fixture patching `app.api.production.get_supabase_client`. Create `_make_table_mock` helper (same pattern as test_production_workcenter.py) that handles table routing for "production_schedule", "production_actuals", "assets", "products". Define sample data constants (SAMPLE_ASSETS with areas, SAMPLE_PRODUCTS, SAMPLE_SCHEDULE entries, SAMPLE_ACTUALS with on-schedule/swap/missing/unscheduled scenarios). Tests organized by AC:
     - TestScheduleAttainmentAuth: test_requires_authentication (401 without token), test_both_paths_accessible
     - TestScheduleAttainmentHappyPath: test_returns_per_workcenter_breakdown (AC1), test_product_attainment_calculation (AC1), test_overall_workcenter_attainment (AC1)
     - TestScheduleAttainmentVariances: test_product_swap_callout (AC2), test_missing_production_callout (AC2), test_unscheduled_production_callout (AC2)
     - TestScheduleAttainmentEmpty: test_no_schedule_returns_200_with_message (AC3)
     - TestScheduleAttainmentFiltering: test_area_filter (AC5), test_area_filter_no_match_returns_empty (AC5)
     - TestScheduleAttainmentErrors: test_supabase_error_returns_500

  5. Verify no changes needed in main.py: The production.router is already registered at both `/api/production` (line 68) and `/api/v1/production` (line 70). The new endpoint at `/schedule-attainment` is automatically available at both prefixes. No changes to main.py required.
DESIGN END

---

## DESIGN: 12-6-schedule-attainment-ui-section
**Timestamp:** 2026-02-11 13:27:33

DESIGN START
story_id: 12-6-schedule-attainment-ui-section

files_to_modify:
  - path: apps/web/src/hooks/useScheduleAttainment.ts
    action: create
    purpose: Custom data-fetching hook for GET /api/v1/production/schedule-attainment?date={date}. Returns typed schedule attainment data including workcenters, products, variances, and has_data boolean. Follows useWorkcenterSummary pattern exactly (mountedRef, createClient auth, Bearer token, error messages, auto-fetch on mount, getYesterday default).

  - path: apps/web/src/components/production/ScheduleAttainment.tsx
    action: create
    purpose: Main section component rendering workcenter-grouped attainment cards with per-product rows, overall attainment %, variance callouts, empty state with upload link, and loading skeleton. Uses Card mode="retrospective" and useScheduleAttainment hook. Client component ('use client').

  - path: apps/web/src/components/production/ProductVarianceCallout.tsx
    action: create
    purpose: Presentational component for rendering a single variance callout (swap, missing, unscheduled) with appropriate color coding — amber/orange for swaps, info-blue for unscheduled, warning-amber for missing.

  - path: apps/web/src/components/production/ProductMixChart.tsx
    action: create
    purpose: Recharts BarChart component showing planned vs. actual mix percentages as grouped bars per product. Uses ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend. Client component ('use client').

  - path: apps/web/src/app/(main)/morning-report/page.tsx
    action: modify
    purpose: Import ScheduleAttainment from @/components/production and place it between WorkcenterScorecard and the "Action items with evidence" section.

  - path: apps/web/src/components/production/index.ts
    action: modify
    purpose: Add barrel exports for ScheduleAttainment, ProductVarianceCallout, and ProductMixChart.

patterns_to_use:
  - useWorkcenterSummary_hook_pattern: Create useScheduleAttainment.ts following the exact structure from useWorkcenterSummary.ts — useState for {data, isLoading, error}, mountedRef, useCallback fetchData with createClient() Bearer token auth, getYesterday() default date, auto-fetch via useEffect, ERROR_MESSAGES constant, API_BASE_URL from env. The hook is the closest match since both fetch production data for a given date.
  - workcenter_scorecard_section_pattern: Structure ScheduleAttainment.tsx with four states (loading skeleton → error with refetch → empty state → success) matching WorkcenterScorecard.tsx exactly. Section header uses "section-header text-foreground mb-4" class. Each state wraps content in div with className prop.
  - card_mode_retrospective: All cards use <Card mode="retrospective"> since this is T-1 historical data, consistent with MorningSummarySection and WorkcenterScorecard.
  - attainment_color_function: Reuse the getAttainmentColor(pct) pattern from WorkcenterRow.tsx — >=95 success-green, >=85 warning-amber, <85 safety-red — for product-level and workcenter-level attainment percentages.
  - skeleton_pulse_pattern: Use animate-pulse with bg-industrial-200 dark:bg-industrial-700 rounded (matching ActionListSkeleton.tsx SkeletonPulse pattern) for loading state placeholders.
  - recharts_chart_pattern: Follow ParetoChart.tsx pattern — 'use client', ResponsiveContainer wrapping, hsl(var(--...)) color tokens, custom tooltip component, Card+CardContent wrapper, margin configuration, tick styling with muted-foreground.
  - barrel_export_pattern: Add named exports to components/production/index.ts matching existing pattern (export { ComponentName } from './ComponentName').
  - server_page_integration: Morning report page is a Server Component — new ScheduleAttainment is a Client Component (has 'use client') imported via barrel export, placed as a sibling to existing sections inside the space-y-6 container.

dependencies:
  - recharts: installed (already used in downtime/ParetoChart.tsx, version 3.6+)
  - lucide-react: installed (icons for callout types — AlertTriangle, ArrowRightLeft, Package, Upload)
  - @/lib/supabase/client: installed (createClient for auth)
  - @/components/ui/card: installed (Card, CardContent, CardHeader, CardTitle)
  - @/components/ui/badge: installed (Badge for attainment status)
  - @/lib/utils: installed (cn utility)
  - next/link: installed (Link for empty-state upload redirect)

acceptance_criteria_mapping:
  - AC1 (Schedule attainment section with workcenter/product breakdown): apps/web/src/hooks/useScheduleAttainment.ts — fetches GET /api/v1/production/schedule-attainment?date={yesterday} with Bearer token auth, returns typed ScheduleAttainmentResponse (workcenters[], has_data, date, message). apps/web/src/components/production/ScheduleAttainment.tsx — renders section with h2 "Schedule Attainment", iterates workcenters, for each renders a Card mode="retrospective" showing workcenter name + overall_attainment_pct, then a table/list of products with product_name, scheduled_quantity, actual_quantity, attainment_pct. Variance callouts rendered via ProductVarianceCallout sub-component. apps/web/src/app/(main)/morning-report/page.tsx — imports ScheduleAttainment from @/components/production and places <ScheduleAttainment /> between <WorkcenterScorecard /> and the action items <section>.

  - AC2 (Product swap highlighting in amber/orange): apps/web/src/components/production/ProductVarianceCallout.tsx — receives a VarianceCallout object (asset_name, message, variance_type). For variance_type="swap": renders with bg-warning-amber-light/50 dark:bg-warning-amber-dark/20 background, border-l-4 border-warning-amber, text-warning-amber-dark dark:text-warning-amber text, ArrowRightLeft icon. Message text already formatted by API as "Ran Colombian instead of scheduled Brazilian — X units still needed". For variance_type="missing": same amber styling with AlertTriangle icon. For variance_type="unscheduled": bg-info-blue-light/50 dark:bg-info-blue-dark/20 background with info-blue text and Package icon.

  - AC3 (No schedule data prompt with upload link): apps/web/src/hooks/useScheduleAttainment.ts — when API returns has_data=false, sets data with has_data: false and message string. apps/web/src/components/production/ScheduleAttainment.tsx — checks data.has_data === false, renders a Card with rounded-lg border p-6 text-center containing: message text "No schedule uploaded for this date.", a next/link Link to "/settings/schedule-upload" with text "Upload schedule →" styled as text-info-blue hover:underline.

  - AC4 (Product mix bar comparison chart): apps/web/src/components/production/ProductMixChart.tsx — receives workcenters data, computes planned vs actual mix percentages across all products (scheduled_quantity / total_scheduled * 100 and actual_quantity / total_actual * 100). Renders BarChart with grouped bars: "Planned %" in info-blue (hsl(210, 50%, 50%)) and "Actual %" in success-green (hsl(152, 69%, 47%)). Uses ResponsiveContainer width="100%" height={250}. Placed within ScheduleAttainment.tsx below the workcenter cards when data is available.

risks:
  - API response shape mismatch: The story Dev Notes describe a different response shape (workcenter_name, variance_callouts) than the actual implemented API (workcenter, variances). Mitigation: TypeScript interfaces in the hook will match the ACTUAL API schema from apps/api/app/schemas/production.py — fields are: workcenter (not workcenter_name), variances (not variance_callouts), variance_type (not type), has_data (not has_schedule). Verified by reading the actual endpoint code.

  - Morning report page is a Server Component: The page.tsx has no 'use client' directive and exports metadata. The new ScheduleAttainment component MUST be a Client Component ('use client') since it uses hooks for client-side data fetching. Mitigation: This is the exact same pattern used by MorningSummarySection, WorkcenterScorecard, and InsightEvidenceCardList — all are client components imported into the server page. No conflict.

  - Recharts bundle size: Adding a BarChart component imports additional Recharts modules. Mitigation: Recharts is already in the bundle (used by ParetoChart in downtime components). The BarChart is simpler than the existing ComposedChart usage, so marginal bundle impact.

  - Color token availability: The story specifies color tokens like text-success-green, text-warning-amber, bg-warning-amber/10 but these need to be verified against actual Tailwind config. Mitigation: Verified in tailwind.config.ts — success-green (#10B981), warning-amber (#F59E0B), info-blue (#3B82F6), safety-red (#DC2626) all exist with light/dark variants. StatusBadge.tsx confirms usage patterns: bg-success-green-light dark:bg-success-green-dark/20, text-success-green-dark dark:text-success-green.

  - Section ordering in morning report: The story says "between MorningSummarySection and Today's Action Items" but the current page has WorkcenterScorecard between them. Mitigation: Story AC#1 specifies "between MorningSummarySection and Action Items section". WorkcenterScorecard (Story 11.2) was added in a later epic. The natural placement is after WorkcenterScorecard and before the action items section, keeping the production data sections together. This aligns with the story's intent of being "in the production data area" of the morning report.

  - Empty products array in a workcenter: If a workcenter has only variance callouts and no matched products, the product table would be empty. Mitigation: Only render the product table rows when products.length > 0. Variance callouts always render if present.

estimated_test_files:
  - No new test files for this story: The story tasks do not include test tasks. The component follows established patterns (WorkcenterScorecard, MorningSummarySection) which are tested at the integration level. The hook follows useWorkcenterSummary pattern which is tested via the existing test infrastructure. Testing can be added in a follow-up if needed, following the same patterns as apps/web/src/__tests__/action-list.test.tsx and apps/web/src/components/schedule/__tests__/*.test.tsx.

implementation_order:
  1. Create apps/web/src/hooks/useScheduleAttainment.ts — Define TypeScript interfaces matching the ACTUAL API schema: ProductAttainment (product_name, product_id, scheduled_quantity, actual_quantity, attainment_pct), VarianceCallout (asset_name, message, variance_type), WorkcenterScheduleAttainment (workcenter, products, variances, overall_attainment_pct), ScheduleAttainmentResponse (date, workcenters, message, has_data). Implement hook following useWorkcenterSummary.ts pattern exactly: 'use client', useState for {data, isLoading, error}, mountedRef, useCallback fetchData that gets Supabase session → Bearer token → fetch GET /api/v1/production/schedule-attainment?date={date}, getYesterday() default, auto-fetch useEffect, ERROR_MESSAGES, API_BASE_URL. Return {data, isLoading, error, refetch, hasData}.

  2. Create apps/web/src/components/production/ProductVarianceCallout.tsx — 'use client', import AlertTriangle/ArrowRightLeft/Package from lucide-react, cn from @/lib/utils. Accept VarianceCallout prop. Render a div with border-l-4 and rounded-lg padding. For variance_type="swap": amber border + bg + text + ArrowRightLeft icon. For "missing": amber border + bg + text + AlertTriangle icon. For "unscheduled": info-blue border + bg + text + Package icon. Display the message text from the API.

  3. Create apps/web/src/components/production/ProductMixChart.tsx — 'use client', import BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer from recharts. Accept products array (ProductAttainment[]) and compute planned/actual mix percentages. Render grouped BarChart inside ResponsiveContainer height={250}. Planned bar in cool blue (hsl(210, 50%, 50%)), actual bar in green (hsl(152, 69%, 47%)). Custom tooltip showing product name, planned %, actual %. XAxis shows product names (truncated if needed). Add guard for empty products array.

  4. Create apps/web/src/components/production/ScheduleAttainment.tsx — 'use client', import useScheduleAttainment, Card/CardContent/CardHeader/CardTitle, Badge, cn, Link (next/link), ProductVarianceCallout, ProductMixChart, AlertCircle/RefreshCw from lucide-react. Props: className. Four render states following WorkcenterScorecard pattern:
     (a) Loading: section header + 2 animate-pulse skeleton cards
     (b) Error: section header + warning border card with AlertCircle icon + error text + "Try Again" Button calling refetch
     (c) Empty (has_data=false): section header + Card with message text + Link to /settings/schedule-upload "Upload schedule →"
     (d) Success: section header + for each workcenter: Card mode="retrospective" with CardHeader showing workcenter name + overall attainment Badge (color based on getAttainmentColor), CardContent with product rows table (product_name, scheduled_quantity, actual_quantity, attainment_pct with color coding), variance callouts via ProductVarianceCallout, and ProductMixChart below all workcenter cards showing overall mix comparison.

  5. Modify apps/web/src/components/production/index.ts — Add three new barrel exports:
     export { ScheduleAttainment } from './ScheduleAttainment'
     export { ProductVarianceCallout } from './ProductVarianceCallout'
     export { ProductMixChart } from './ProductMixChart'

  6. Modify apps/web/src/app/(main)/morning-report/page.tsx — Add ScheduleAttainment to the import from '@/components/production' (line 5). Place <ScheduleAttainment /> on a new line after <WorkcenterScorecard /> (after line 48) and before the action items <section> (line 52). Add a comment: {/* Schedule Attainment - Story 12.6 */}.
DESIGN END

---
