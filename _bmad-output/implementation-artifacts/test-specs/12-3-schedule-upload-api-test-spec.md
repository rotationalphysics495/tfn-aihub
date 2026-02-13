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
