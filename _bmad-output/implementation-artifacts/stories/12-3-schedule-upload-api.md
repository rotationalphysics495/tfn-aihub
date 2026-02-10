# Story 12.3: Schedule Upload API

Status: ready-for-dev

## Story

As a **Plant Manager or Planner**,
I want **to upload a CSV or Excel file with the weekly production schedule**,
so that **the system knows what should be produced without waiting for AX/D365 integration**.

## Acceptance Criteria

1. **AC1 - CSV Upload Preview:** Given a user uploads a valid CSV file with columns: `date`, `shift`, `asset_name`, `product_name`, `scheduled_quantity`, When `POST /api/v1/schedule/upload` is called with multipart form data, Then the file is parsed, validated, and a preview response is returned with: parsed rows count, matched assets (fuzzy match against `assets.name`), matched products (exact match or new products to create), and validation errors (if any) highlighted per row. No data is committed to the database yet (preview only).

2. **AC2 - Upload Confirmation:** Given a user confirms the preview by calling `POST /api/v1/schedule/upload/confirm`, When the confirmation request includes the parsed data, Then matched products are inserted (or found) in the `products` table, new products that do not exist are auto-created with a confirmation note, schedule rows are upserted into `production_schedule` (replacing existing rows for same date range), and a success response includes count of rows inserted/updated.

3. **AC3 - Excel Support:** Given a user uploads an Excel (.xlsx) file, When the file is parsed, Then the same validation and preview flow applies as CSV.

4. **AC4 - Fuzzy Asset Matching:** Given a CSV with an asset name that does not match any existing asset, When the preview is generated, Then the row is flagged with an error and suggestions for near-matches (fuzzy matching), and the user can correct or skip the row before confirming.

5. **AC5 - Validation Errors:** Given a CSV with invalid data (negative quantities, invalid dates, missing required columns), When the preview is generated, Then each invalid row is flagged with a specific error message, and the upload cannot be confirmed until errors are resolved.

## Tasks / Subtasks

- [ ] Task 1: Create schedule request/response schemas (AC: #1, #2, #3, #4, #5)
  - [ ] 1.1 Create `apps/api/app/schemas/schedule.py` with Pydantic models
  - [ ] 1.2 Define `ScheduleUploadRow` model for individual parsed rows
  - [ ] 1.3 Define `SchedulePreviewResponse` model with matched/unmatched/error rows
  - [ ] 1.4 Define `ScheduleConfirmRequest` model for the confirm step
  - [ ] 1.5 Define `ScheduleConfirmResponse` model with insert/update counts
  - [ ] 1.6 Define `ValidationError` model for per-row error reporting
- [ ] Task 2: Create schedule parser service (AC: #1, #3, #4, #5)
  - [ ] 2.1 Create `apps/api/app/services/schedule_parser.py`
  - [ ] 2.2 Implement CSV parsing using Python `csv` module
  - [ ] 2.3 Implement Excel parsing using `openpyxl`
  - [ ] 2.4 Implement column header validation (required columns check)
  - [ ] 2.5 Implement per-row validation (date format, positive quantities, non-empty fields)
  - [ ] 2.6 Implement fuzzy asset name matching using `difflib.get_close_matches()`
  - [ ] 2.7 Implement product name matching (exact match against existing `products` table)
  - [ ] 2.8 Implement preview assembly (group parsed rows with match status and errors)
- [ ] Task 3: Create schedule API endpoints (AC: #1, #2)
  - [ ] 3.1 Create `apps/api/app/api/schedule.py` with FastAPI router
  - [ ] 3.2 Implement `POST /upload` endpoint accepting multipart file upload
  - [ ] 3.3 Implement `POST /upload/confirm` endpoint for committing validated data
  - [ ] 3.4 Add JWT authentication via `get_current_user` dependency
  - [ ] 3.5 Add proper error handling and HTTP status codes
- [ ] Task 4: Register schedule router in main.py (AC: #1, #2)
  - [ ] 4.1 Import schedule module in `apps/api/app/main.py`
  - [ ] 4.2 Register router with prefix `/api/v1/schedule` and tag `Schedule`
- [ ] Task 5: Add openpyxl dependency (AC: #3)
  - [ ] 5.1 Add `openpyxl>=3.1.0` to `apps/api/requirements.txt`
- [ ] Task 6: Write tests (AC: #1, #2, #3, #4, #5)
  - [ ] 6.1 Create `apps/api/tests/services/test_schedule_parser.py`
  - [ ] 6.2 Test CSV parsing with valid data
  - [ ] 6.3 Test Excel parsing with valid data
  - [ ] 6.4 Test validation errors (negative quantities, invalid dates, missing columns)
  - [ ] 6.5 Test fuzzy asset matching (exact match, close match, no match)
  - [ ] 6.6 Test product matching (existing product, new product)
  - [ ] 6.7 Create `apps/api/tests/api/test_schedule.py` for endpoint tests
  - [ ] 6.8 Test upload endpoint with valid CSV
  - [ ] 6.9 Test upload endpoint with valid Excel
  - [ ] 6.10 Test confirm endpoint with valid preview data
  - [ ] 6.11 Test confirm endpoint with upsert behavior (replace existing date range)

## Dev Notes

### Architecture Patterns and Constraints

**Two-Step Upload Flow (Preview + Confirm):**
This story implements a two-step upload pattern. The preview step parses and validates without touching the database. The confirm step commits. This is critical for user confidence -- they must see what will happen before it happens.

**Router Registration Pattern:**
Follow the exact pattern in `apps/api/app/main.py`. Import the module in the import line at the top, then register with `app.include_router()`. Use the versioned prefix `/api/v1/schedule` (consistent with `/api/v1/voice`, `/api/v1/briefing`, `/api/v1/handoff`, etc.). Add a story reference comment.

**Authentication:**
All endpoints MUST use `current_user: CurrentUser = Depends(get_current_user)` from `app.core.security`. This is the standard auth pattern used across all protected endpoints. See `apps/api/app/api/production.py` for the exact import pattern.

**Supabase Client Pattern:**
Use the helper function pattern from existing routers to get the Supabase client:
```python
from app.core.config import get_settings
from supabase import create_client

async def get_supabase_client():
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase not configured"
        )
    return create_client(settings.supabase_url, settings.supabase_key)
```
See `apps/api/app/api/production.py` lines 103-114 for the existing implementation.

**Schema Pattern:**
Follow `apps/api/app/schemas/action.py` conventions:
- Use Pydantic `BaseModel` with `Field(...)` for all fields
- Add `model_config = ConfigDict(json_schema_extra={...})` with examples
- Include story and AC references in docstrings
- Use `str` Enum classes for categorical values

**Error Handling Pattern:**
Follow the established pattern: catch `HTTPException` and re-raise, catch generic `Exception` and return 500 with sanitized message. Log errors with `logger.error()`. Never expose internal details.

### Database Tables (from Story 12.1)

The following tables are expected to exist from Story 12.1 migration (`supabase/migrations/0026_products_and_schedule.sql`):

**`products` table:**
- `id` (UUID PK), `name` (TEXT), `sku` (TEXT), `product_family` (TEXT), `unit_of_measure` (TEXT DEFAULT 'units'), `created_at`, `updated_at`

**`production_schedule` table:**
- `id` (UUID PK), `asset_id` (UUID FK -> assets), `product_id` (UUID FK -> products), `scheduled_quantity` (INTEGER), `scheduled_date` (DATE), `shift` (TEXT), `production_order_ref` (TEXT nullable), `created_at`, `updated_at`

**`production_actuals` table:**
- `id` (UUID PK), `asset_id` (UUID FK -> assets), `product_id` (UUID FK -> products), `actual_quantity` (INTEGER), `production_date` (DATE), `shift` (TEXT), `created_at`, `updated_at`

All three tables have RLS enabled with the standard authenticated read / service_role full access policy pattern.

### Existing Assets (from seed data)

The fuzzy matching must work against these existing assets (from `scripts/seed-data.mjs`):
- Roasting area: Roaster 1, Roaster 2, Roaster 3
- Grinding area: Grinder 1, Grinder 2, Grinder 3, Grinder 4, Grinder 5
- Filling area: Filler Line A, Filler Line B, Filler Line C
- Packaging area: Packaging Line 1, Packaging Line 2, Packaging Line 3

### File Upload Handling

**FastAPI File Upload:**
```python
from fastapi import UploadFile, File

@router.post("/upload")
async def upload_schedule(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
):
    # file.filename - original filename
    # file.content_type - MIME type
    # await file.read() - get bytes content
```

Accept both `.csv` and `.xlsx` files. Detect format from file extension (`.xlsx`) or content type (`text/csv`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`). Reject all other file types with 400 error.

### CSV/Excel Parsing Details

**Expected Column Headers (case-insensitive matching):**
- `date` (required) - ISO format `YYYY-MM-DD` or common formats like `MM/DD/YYYY`
- `shift` (required) - Free text, e.g., "Day", "Night", "Swing"
- `asset_name` (required) - Must fuzzy-match against `assets.name`
- `product_name` (required) - Exact match or auto-create
- `scheduled_quantity` (required) - Positive integer

**CSV Parsing:** Use Python's built-in `csv.DictReader`. Handle UTF-8 BOM (`utf-8-sig` encoding).

**Excel Parsing:** Use `openpyxl` in read-only mode for memory efficiency:
```python
from openpyxl import load_workbook
wb = load_workbook(filename=io.BytesIO(file_bytes), read_only=True, data_only=True)
ws = wb.active
```
Read the first row as headers. Process subsequent rows as data. The `data_only=True` flag ensures formulas return calculated values.

### Fuzzy Matching Implementation

Use `difflib.get_close_matches()` for asset name matching:
```python
from difflib import get_close_matches

def match_asset(input_name: str, asset_names: list[str], cutoff: float = 0.6) -> list[str]:
    """Return up to 3 close matches for an asset name."""
    return get_close_matches(input_name, asset_names, n=3, cutoff=cutoff)
```

Matching logic:
1. First try exact case-insensitive match against `assets.name`
2. If no exact match, use `get_close_matches()` with cutoff 0.6
3. If close matches found, flag row with warning and include suggestions
4. If no matches at all, flag row as error

### Upsert Strategy (Confirm Step)

When confirming, upsert into `production_schedule` using a composite natural key of `(asset_id, scheduled_date, shift)`:
1. Delete existing rows for the same `(asset_id, scheduled_date, shift)` combinations present in the upload
2. Insert all new rows
3. This effectively replaces the schedule for the uploaded date range without touching dates not in the file

For products:
1. Query `products` table for exact name match
2. If product exists, use its `id`
3. If product does not exist, INSERT a new row with the product name and return the new `id`

### Validation Rules

Per-row validation (return ALL errors per row, not just the first):
- `date`: Must be a valid date, not in the distant past (>90 days ago) or far future (>365 days)
- `shift`: Must be non-empty string
- `asset_name`: Must be non-empty (fuzzy matching is separate from validation)
- `product_name`: Must be non-empty string
- `scheduled_quantity`: Must be a positive integer (> 0)

File-level validation:
- File must not be empty (at least 1 data row after headers)
- File must contain all required column headers
- File size limit: reject files > 5MB

### Technology Requirements

| Library | Version | Purpose |
|---------|---------|---------|
| `openpyxl` | >= 3.1.0 | Excel (.xlsx) file parsing |
| `csv` (stdlib) | built-in | CSV file parsing |
| `difflib` (stdlib) | built-in | Fuzzy string matching for asset names |
| `io` (stdlib) | built-in | BytesIO for in-memory file handling |
| `fastapi` | >= 0.109.0 (existing) | File upload via `UploadFile` |
| `pydantic` | >= 2.0.0 (existing) | Request/response schemas |
| `supabase-py` | >= 2.0.0 (existing) | Database operations |

**Note:** `openpyxl` is NOT currently in `requirements.txt` and MUST be added.

### Project Structure Notes

**Files to Create:**
- `apps/api/app/api/schedule.py` - Route handlers for upload and confirm endpoints
- `apps/api/app/services/schedule_parser.py` - CSV/Excel parsing, validation, fuzzy matching logic
- `apps/api/app/schemas/schedule.py` - Pydantic request/response models
- `apps/api/tests/services/test_schedule_parser.py` - Parser unit tests
- `apps/api/tests/api/test_schedule.py` - API endpoint integration tests

**Files to Modify:**
- `apps/api/app/main.py` - Add schedule router import and registration
- `apps/api/requirements.txt` - Add `openpyxl>=3.1.0`

**Alignment with Project Structure:**
- API routes go in `apps/api/app/api/` (matches existing `production.py`, `actions.py`, etc.)
- Business logic goes in `apps/api/app/services/` (matches existing `action_engine.py`, `financial.py`, etc.)
- Schemas go in `apps/api/app/schemas/` (matches existing `action.py`, `financial.py`, etc.)
- Tests mirror source structure under `apps/api/tests/`

### Testing Standards

- Use `pytest` with `pytest-asyncio` for async test support
- Create test fixtures for sample CSV/Excel file content as `io.BytesIO` objects
- Mock the Supabase client for unit tests
- Test both happy path and error cases
- Ensure fuzzy matching tests cover: exact match, close match (typo), no match scenarios
- Test file format detection (CSV vs XLSX)
- Test the full two-step flow: upload -> preview -> confirm

### Dependencies on Other Stories

- **Story 12.1 (Products & Schedule Data Model):** MUST be completed first. This story depends on the `products`, `production_schedule`, and `production_actuals` tables existing.
- **Story 12.2 (Products & Schedule Seed Data):** Should be completed first so fuzzy matching can be tested against realistic product data. However, this story can be developed in parallel if the developer seeds their own test data.
- **Story 12.4 (Schedule Upload UI):** Depends on THIS story. The UI will call these API endpoints.

### References

- [Source: _bmad-output/planning-artifacts/epic-12.md#Story 12.3]
- [Source: docs/architecture-api.md#Directory Structure]
- [Source: docs/architecture-api.md#API Endpoints]
- [Source: docs/data-models.md#Supabase Schema]
- [Source: docs/api-contracts.md#Error Responses]
- [Source: docs/development-guide.md#Backend Development]
- [Source: docs/source-tree-analysis.md#Repository Structure]
- [Source: apps/api/app/main.py - Router registration pattern]
- [Source: apps/api/app/api/production.py - Supabase client helper pattern]
- [Source: apps/api/app/schemas/action.py - Schema conventions]
- [Source: apps/api/app/core/security.py - Authentication dependency]
- [Source: apps/api/requirements.txt - Current dependencies]

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List
