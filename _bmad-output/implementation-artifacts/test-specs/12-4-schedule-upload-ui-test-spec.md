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
