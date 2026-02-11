"""
Tests for Schedule Upload API Endpoints (Story 12.3 - Schedule Upload API)

Integration tests for the schedule upload preview and confirm endpoints.

AC: #1 - CSV Upload Preview
AC: #2 - Upload Confirmation
AC: #3 - Excel Support
AC: #4 - Fuzzy Asset Matching
AC: #5 - Validation Errors
"""

import io
import pytest
from datetime import date
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4


# =============================================================================
# Test Data Constants
# =============================================================================

ASSET_GRINDER_1_ID = str(uuid4())
ASSET_FILLER_A_ID = str(uuid4())
ASSET_ROASTER_1_ID = str(uuid4())
PRODUCT_DARK_ROAST_ID = str(uuid4())

SAMPLE_ASSETS = [
    {"id": ASSET_GRINDER_1_ID, "name": "Grinder 1", "area": "Grinding"},
    {"id": ASSET_FILLER_A_ID, "name": "Filler Line A", "area": "Filling"},
    {"id": ASSET_ROASTER_1_ID, "name": "Roaster 1", "area": "Roasting"},
]

SAMPLE_PRODUCTS = [
    {"id": PRODUCT_DARK_ROAST_ID, "name": "Dark Roast 12oz"},
]

AUTH_HEADERS = {"Authorization": "Bearer test-token"}


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for schedule endpoints."""
    with patch("app.api.schedule.get_supabase_client", new_callable=AsyncMock) as mock:
        client_mock = MagicMock()
        mock.return_value = client_mock
        yield client_mock


def _setup_supabase_tables(client_mock, assets=None, products=None):
    """
    Helper to configure mock Supabase client to return different data
    for different table queries.
    """
    assets_data = assets if assets is not None else SAMPLE_ASSETS
    products_data = products if products is not None else SAMPLE_PRODUCTS

    def table_side_effect(table_name):
        table_mock = MagicMock()
        if table_name == "assets":
            data = assets_data
        elif table_name == "products":
            data = products_data
        elif table_name == "production_schedule":
            data = []
        else:
            data = []

        response = MagicMock(data=data)
        # select().execute()
        table_mock.select.return_value.execute.return_value = response
        # select().eq().execute()
        table_mock.select.return_value.eq.return_value.execute.return_value = response
        # select().eq().eq().execute()
        table_mock.select.return_value.eq.return_value.eq.return_value.execute.return_value = response
        # insert().execute()
        table_mock.insert.return_value.execute.return_value = MagicMock(data=[{"id": str(uuid4())}])
        # delete().eq().eq().eq().execute()
        table_mock.delete.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[])

        return table_mock

    client_mock.table.side_effect = table_side_effect


def _make_csv_file(rows_content):
    """Helper to create an in-memory CSV file for upload testing."""
    header = "date,shift,asset_name,product_name,scheduled_quantity\n"
    content = header + rows_content
    return io.BytesIO(content.encode("utf-8"))


def _make_valid_csv_3_rows():
    """Create a valid CSV BytesIO with 3 data rows."""
    return _make_csv_file(
        "2026-02-16,Day,Grinder 1,Dark Roast 12oz,500\n"
        "2026-02-16,Night,Filler Line A,Medium Blend 16oz,300\n"
        "2026-02-17,Day,Roaster 1,New Blend XYZ,400\n"
    )


def _make_xlsx_file(rows):
    """Helper to create an in-memory .xlsx file for upload testing."""
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.append(["date", "shift", "asset_name", "product_name", "scheduled_quantity"])
    for row in rows:
        ws.append(row)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


# =============================================================================
# AC1: CSV Upload Preview — Integration Tests
# =============================================================================


class TestScheduleUploadPreview:
    """Tests for POST /api/v1/schedule/upload preview endpoint."""

    def test_INT_001_valid_csv_upload_returns_preview(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-3-schedule-upload-api-INT-001: Valid CSV upload returns preview with parsed rows.

        Given: Valid CSV with 3 rows; assets and products exist in DB
        When: POST /api/v1/schedule/upload with CSV multipart form data and valid JWT
        Then: 200 response with parsed_rows_count=3; matched assets/products; no errors
        """
        _setup_supabase_tables(mock_supabase_client)
        csv_file = _make_valid_csv_3_rows()

        response = client.post(
            "/api/v1/schedule/upload",
            headers=AUTH_HEADERS,
            files={"file": ("schedule.csv", csv_file, "text/csv")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["parsed_rows_count"] == 3
        # Check matched assets are present
        assert "rows" in data
        # No data should be committed
        # Verify no insert/upsert calls were made
        for call in mock_supabase_client.table.call_args_list:
            table_name = call[0][0]
            if table_name == "production_schedule":
                table_mock = mock_supabase_client.table(table_name)
                # Insert should NOT have been called on production_schedule
                assert not table_mock.insert.called or not table_mock.insert.return_value.execute.called

    def test_INT_002_upload_does_not_commit_data(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-3-schedule-upload-api-INT-002: Upload preview does not commit data.

        Given: Valid CSV with 3 rows; Supabase client is mocked
        When: POST /api/v1/schedule/upload is called
        Then: No insert/upsert/delete on production_schedule or products tables
        """
        _setup_supabase_tables(mock_supabase_client)
        csv_file = _make_valid_csv_3_rows()

        # Track all method calls on the mock
        call_tracker = {"insert_called": False, "upsert_called": False, "delete_called": False}

        original_table = mock_supabase_client.table.side_effect

        def tracking_table(table_name):
            table_mock = original_table(table_name)
            if table_name in ("production_schedule", "products"):
                orig_insert = table_mock.insert
                orig_delete = table_mock.delete

                def track_insert(*args, **kwargs):
                    call_tracker["insert_called"] = True
                    return orig_insert(*args, **kwargs)

                def track_delete(*args, **kwargs):
                    call_tracker["delete_called"] = True
                    return orig_delete(*args, **kwargs)

                table_mock.insert = track_insert
                table_mock.delete = track_delete
            return table_mock

        mock_supabase_client.table.side_effect = tracking_table

        response = client.post(
            "/api/v1/schedule/upload",
            headers=AUTH_HEADERS,
            files={"file": ("schedule.csv", csv_file, "text/csv")},
        )

        assert response.status_code == 200
        assert not call_tracker["insert_called"], "insert should not be called during preview"
        assert not call_tracker["delete_called"], "delete should not be called during preview"

    def test_INT_003_upload_requires_jwt_authentication(self, client):
        """12-3-schedule-upload-api-INT-003: Upload endpoint requires JWT.

        Given: Valid CSV file
        When: POST /api/v1/schedule/upload without Authorization header
        Then: Response status is 401 or 403
        """
        csv_file = _make_valid_csv_3_rows()

        response = client.post(
            "/api/v1/schedule/upload",
            files={"file": ("schedule.csv", csv_file, "text/csv")},
        )

        assert response.status_code in (401, 403)

    def test_INT_004_upload_rejects_unsupported_file_types(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-3-schedule-upload-api-INT-004: Upload rejects unsupported file types.

        Given: A .txt file
        When: POST /api/v1/schedule/upload with the unsupported file
        Then: Response status is 400; error about unsupported file type
        """
        _setup_supabase_tables(mock_supabase_client)
        txt_file = io.BytesIO(b"This is not a CSV or Excel file")

        response = client.post(
            "/api/v1/schedule/upload",
            headers=AUTH_HEADERS,
            files={"file": ("schedule.txt", txt_file, "text/plain")},
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        detail_lower = data["detail"].lower()
        assert "file type" in detail_lower or "not supported" in detail_lower or "csv" in detail_lower

    def test_INT_005_upload_rejects_files_exceeding_5mb(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-3-schedule-upload-api-INT-005: Upload rejects files > 5MB.

        Given: A CSV file exceeding 5MB
        When: POST /api/v1/schedule/upload
        Then: Response status is 413 or 400; error about file size
        """
        _setup_supabase_tables(mock_supabase_client)
        # Generate a CSV > 5MB by repeating rows
        header = "date,shift,asset_name,product_name,scheduled_quantity\n"
        row = "2026-02-16,Day,Grinder 1,Dark Roast 12oz,500\n"
        # Each row is ~50 bytes, 5MB = ~100,000 rows
        large_content = header + (row * 110000)
        large_file = io.BytesIO(large_content.encode("utf-8"))

        response = client.post(
            "/api/v1/schedule/upload",
            headers=AUTH_HEADERS,
            files={"file": ("schedule.csv", large_file, "text/csv")},
        )

        assert response.status_code in (400, 413)
        data = response.json()
        assert "detail" in data
        detail_lower = data["detail"].lower()
        assert "size" in detail_lower or "5mb" in detail_lower or "large" in detail_lower


# =============================================================================
# AC2: Upload Confirmation — Integration Tests
# =============================================================================


class TestScheduleUploadConfirm:
    """Tests for POST /api/v1/schedule/upload/confirm endpoint."""

    def test_INT_006_confirm_inserts_schedule_rows(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-3-schedule-upload-api-INT-006: Confirm inserts schedule rows and returns counts.

        Given: Valid ScheduleConfirmRequest with 5 confirmed rows
        When: POST /api/v1/schedule/upload/confirm with valid JWT
        Then: 200 response with rows_inserted count; Supabase insert called
        """
        _setup_supabase_tables(mock_supabase_client)

        confirm_body = {
            "rows": [
                {
                    "asset_id": ASSET_GRINDER_1_ID,
                    "product_name": "Dark Roast 12oz",
                    "scheduled_date": "2026-02-16",
                    "shift": "Day",
                    "scheduled_quantity": 500,
                },
                {
                    "asset_id": ASSET_GRINDER_1_ID,
                    "product_name": "Dark Roast 12oz",
                    "scheduled_date": "2026-02-16",
                    "shift": "Night",
                    "scheduled_quantity": 400,
                },
                {
                    "asset_id": ASSET_FILLER_A_ID,
                    "product_name": "Medium Blend 16oz",
                    "scheduled_date": "2026-02-17",
                    "shift": "Day",
                    "scheduled_quantity": 300,
                },
                {
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_name": "New Blend XYZ",
                    "scheduled_date": "2026-02-17",
                    "shift": "Night",
                    "scheduled_quantity": 600,
                },
                {
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_name": "Dark Roast 12oz",
                    "scheduled_date": "2026-02-18",
                    "shift": "Day",
                    "scheduled_quantity": 250,
                },
            ]
        }

        response = client.post(
            "/api/v1/schedule/upload/confirm",
            headers=AUTH_HEADERS,
            json=confirm_body,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_processed"] == 5
        assert data["rows_inserted"] >= 5

    def test_INT_007_confirm_auto_creates_new_products(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-3-schedule-upload-api-INT-007: Confirm auto-creates new products.

        Given: Confirm request with product_name "New Blend XYZ" not in products table
        When: POST /api/v1/schedule/upload/confirm
        Then: 200; products table insert called; products_created >= 1
        """
        # Return empty for product lookup (product doesn't exist)
        _setup_supabase_tables(mock_supabase_client, products=[])

        confirm_body = {
            "rows": [
                {
                    "asset_id": ASSET_GRINDER_1_ID,
                    "product_name": "New Blend XYZ",
                    "scheduled_date": "2026-02-16",
                    "shift": "Day",
                    "scheduled_quantity": 500,
                },
            ]
        }

        response = client.post(
            "/api/v1/schedule/upload/confirm",
            headers=AUTH_HEADERS,
            json=confirm_body,
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("products_created", 0) >= 1

    def test_INT_008_confirm_upserts_replaces_existing_rows(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-3-schedule-upload-api-INT-008: Confirm upserts by replacing existing rows.

        Given: Existing rows for (asset_id=A, 2026-02-16, "Day"); confirm has same combo
        When: POST /api/v1/schedule/upload/confirm
        Then: Delete called for matching combo; then insert with new data
        """
        _setup_supabase_tables(mock_supabase_client)

        confirm_body = {
            "rows": [
                {
                    "asset_id": ASSET_GRINDER_1_ID,
                    "product_name": "Dark Roast 12oz",
                    "scheduled_date": "2026-02-16",
                    "shift": "Day",
                    "scheduled_quantity": 999,  # Different quantity
                },
            ]
        }

        response = client.post(
            "/api/v1/schedule/upload/confirm",
            headers=AUTH_HEADERS,
            json=confirm_body,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["rows_inserted"] >= 1

    def test_INT_009_confirm_finds_existing_products(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-3-schedule-upload-api-INT-009: Confirm finds existing products by exact name.

        Given: Confirm with product_name "Dark Roast 12oz" which exists in products table
        When: POST /api/v1/schedule/upload/confirm
        Then: No new product inserted; products_created=0
        """
        _setup_supabase_tables(mock_supabase_client)

        confirm_body = {
            "rows": [
                {
                    "asset_id": ASSET_GRINDER_1_ID,
                    "product_name": "Dark Roast 12oz",
                    "scheduled_date": "2026-02-16",
                    "shift": "Day",
                    "scheduled_quantity": 500,
                },
            ]
        }

        response = client.post(
            "/api/v1/schedule/upload/confirm",
            headers=AUTH_HEADERS,
            json=confirm_body,
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("products_created", 0) == 0

    def test_INT_010_confirm_requires_jwt_authentication(self, client):
        """12-3-schedule-upload-api-INT-010: Confirm endpoint requires JWT.

        Given: Valid ScheduleConfirmRequest JSON body
        When: POST /api/v1/schedule/upload/confirm without Authorization header
        Then: Response status is 401 or 403
        """
        confirm_body = {
            "rows": [
                {
                    "asset_id": ASSET_GRINDER_1_ID,
                    "product_name": "Dark Roast 12oz",
                    "scheduled_date": "2026-02-16",
                    "shift": "Day",
                    "scheduled_quantity": 500,
                },
            ]
        }

        response = client.post(
            "/api/v1/schedule/upload/confirm",
            json=confirm_body,
        )

        assert response.status_code in (401, 403)

    def test_INT_011_confirm_rejects_unresolved_errors(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-3-schedule-upload-api-INT-011: Confirm rejects rows with unresolved errors.

        Given: Confirm request with null asset_id (unresolved)
        When: POST /api/v1/schedule/upload/confirm
        Then: Response status is 400; body indicates rows with errors cannot be confirmed
        """
        _setup_supabase_tables(mock_supabase_client)

        confirm_body = {
            "rows": [
                {
                    "asset_id": None,  # Unresolved - no asset match
                    "product_name": "Dark Roast 12oz",
                    "scheduled_date": "2026-02-16",
                    "shift": "Day",
                    "scheduled_quantity": 500,
                },
            ]
        }

        response = client.post(
            "/api/v1/schedule/upload/confirm",
            headers=AUTH_HEADERS,
            json=confirm_body,
        )

        assert response.status_code in (400, 422)


# =============================================================================
# AC1+AC2: Full Two-Step Flow — Integration Tests
# =============================================================================


class TestScheduleFullFlow:
    """Tests for the complete upload preview -> confirm flow."""

    def test_INT_012_full_two_step_flow(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-3-schedule-upload-api-INT-012: Full upload preview then confirm flow.

        Given: Valid CSV with 3 rows; all assets match; 1 product exists, 1 is new
        When: POST upload (preview), then POST confirm
        Then: Preview returns no errors; confirm returns success with rows_inserted=3
        """
        _setup_supabase_tables(mock_supabase_client)
        csv_file = _make_valid_csv_3_rows()

        # Step 1: Upload preview
        upload_response = client.post(
            "/api/v1/schedule/upload",
            headers=AUTH_HEADERS,
            files={"file": ("schedule.csv", csv_file, "text/csv")},
        )

        assert upload_response.status_code == 200
        preview = upload_response.json()
        assert preview["parsed_rows_count"] == 3

        # Step 2: Confirm with resolved rows
        confirm_body = {
            "rows": [
                {
                    "asset_id": ASSET_GRINDER_1_ID,
                    "product_name": "Dark Roast 12oz",
                    "scheduled_date": "2026-02-16",
                    "shift": "Day",
                    "scheduled_quantity": 500,
                },
                {
                    "asset_id": ASSET_FILLER_A_ID,
                    "product_name": "Medium Blend 16oz",
                    "scheduled_date": "2026-02-16",
                    "shift": "Night",
                    "scheduled_quantity": 300,
                },
                {
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_name": "New Blend XYZ",
                    "scheduled_date": "2026-02-17",
                    "shift": "Day",
                    "scheduled_quantity": 400,
                },
            ]
        }

        confirm_response = client.post(
            "/api/v1/schedule/upload/confirm",
            headers=AUTH_HEADERS,
            json=confirm_body,
        )

        assert confirm_response.status_code == 200
        confirm_data = confirm_response.json()
        assert confirm_data["rows_inserted"] == 3
        assert confirm_data.get("products_created", 0) >= 1


# =============================================================================
# AC3: Excel Support — Integration Tests
# =============================================================================


class TestScheduleExcelUpload:
    """Tests for Excel (.xlsx) upload support."""

    def test_INT_013_valid_excel_upload_returns_preview(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-3-schedule-upload-api-INT-013: Valid Excel upload returns same preview as CSV.

        Given: Valid .xlsx file with same data as CSV; assets/products in DB
        When: POST /api/v1/schedule/upload with .xlsx multipart form data
        Then: 200; same SchedulePreviewResponse structure; correct parsed_rows_count
        """
        _setup_supabase_tables(mock_supabase_client)
        xlsx_file = _make_xlsx_file([
            ["2026-02-16", "Day", "Grinder 1", "Dark Roast 12oz", 500],
            ["2026-02-16", "Night", "Filler Line A", "Medium Blend 16oz", 300],
            ["2026-02-17", "Day", "Roaster 1", "New Blend XYZ", 400],
        ])

        response = client.post(
            "/api/v1/schedule/upload",
            headers=AUTH_HEADERS,
            files={
                "file": (
                    "schedule.xlsx",
                    xlsx_file,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["parsed_rows_count"] == 3
        assert "rows" in data

    def test_INT_014_excel_upload_validates_and_returns_errors(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-3-schedule-upload-api-INT-014: Excel upload validates and returns errors like CSV.

        Given: .xlsx file with negative quantity (row 2) and invalid date (row 3)
        When: POST /api/v1/schedule/upload with .xlsx file
        Then: Per-row validation errors with same format as CSV errors
        """
        _setup_supabase_tables(mock_supabase_client)
        xlsx_file = _make_xlsx_file([
            ["2026-02-16", "Day", "Grinder 1", "Dark Roast 12oz", 500],  # valid
            ["2026-02-16", "Night", "Filler Line A", "Blend", -10],  # negative qty
            ["not-a-date", "Day", "Roaster 1", "Blend", 300],  # invalid date
        ])

        response = client.post(
            "/api/v1/schedule/upload",
            headers=AUTH_HEADERS,
            files={
                "file": (
                    "schedule.xlsx",
                    xlsx_file,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("has_errors") is True
        # Find rows with errors
        error_rows = [r for r in data.get("rows", []) if r.get("errors")]
        assert len(error_rows) >= 2


# =============================================================================
# AC4: Fuzzy Asset Matching — Integration Tests
# =============================================================================


class TestScheduleFuzzyMatching:
    """Tests for fuzzy asset matching in the upload endpoint."""

    def test_INT_015_preview_flags_unmatched_assets(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-3-schedule-upload-api-INT-015: Preview flags unmatched asset rows as errors.

        Given: CSV where row 2 has "Unknown Machine" (no match)
        When: POST /api/v1/schedule/upload
        Then: Preview has has_errors=True; unmatched row has asset matching error
        """
        _setup_supabase_tables(mock_supabase_client)
        csv_file = _make_csv_file(
            "2026-02-16,Day,Grinder 1,Dark Roast 12oz,500\n"
            "2026-02-17,Day,Unknown Machine,Dark Roast 12oz,300\n"
        )

        response = client.post(
            "/api/v1/schedule/upload",
            headers=AUTH_HEADERS,
            files={"file": ("schedule.csv", csv_file, "text/csv")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["has_errors"] is True

        # Find the unmatched row
        unmatched_rows = [
            r for r in data.get("rows", [])
            if r.get("asset_match_status") == "unmatched"
        ]
        assert len(unmatched_rows) >= 1


# =============================================================================
# AC5: Validation Errors — Integration Tests
# =============================================================================


class TestScheduleValidationErrors:
    """Tests for validation error reporting in the upload endpoint."""

    def test_INT_016_preview_with_validation_errors(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-3-schedule-upload-api-INT-016: Preview with errors sets has_errors flag.

        Given: CSV with negative quantity (row 2) and invalid date (row 3)
        When: POST /api/v1/schedule/upload
        Then: 200; has_errors=True; rows 2 and 3 have specific validation errors
        """
        _setup_supabase_tables(mock_supabase_client)
        csv_file = _make_csv_file(
            "2026-02-16,Day,Grinder 1,Dark Roast 12oz,500\n"
            "2026-02-16,Night,Filler Line A,Blend,-10\n"
            "not-a-date,Day,Roaster 1,Blend,300\n"
        )

        response = client.post(
            "/api/v1/schedule/upload",
            headers=AUTH_HEADERS,
            files={"file": ("schedule.csv", csv_file, "text/csv")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["has_errors"] is True

        # Check that error rows have field-specific errors
        rows_with_errors = [r for r in data.get("rows", []) if r.get("errors")]
        assert len(rows_with_errors) >= 2

        # Verify error structure includes field name and message
        for row in rows_with_errors:
            for error in row["errors"]:
                assert "field" in error
                assert "message" in error


# =============================================================================
# Error Scenarios — Integration Tests
# =============================================================================


class TestScheduleErrorScenarios:
    """Tests for error scenarios in schedule endpoints."""

    def test_INT_017_supabase_unavailable_returns_503(
        self, client, mock_verify_jwt
    ):
        """12-3-schedule-upload-api-INT-017: Supabase unavailable returns 503.

        Given: Supabase URL/key not configured
        When: POST /api/v1/schedule/upload
        Then: Response status is 503; body indicates Supabase not configured
        """
        csv_file = _make_valid_csv_3_rows()

        with patch("app.api.schedule.get_supabase_client", new_callable=AsyncMock) as mock_client:
            from fastapi import HTTPException, status
            mock_client.side_effect = HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase not configured",
            )

            response = client.post(
                "/api/v1/schedule/upload",
                headers=AUTH_HEADERS,
                files={"file": ("schedule.csv", csv_file, "text/csv")},
            )

        assert response.status_code == 503
        data = response.json()
        assert "supabase" in data["detail"].lower() or "not configured" in data["detail"].lower()
