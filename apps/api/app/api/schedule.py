"""
Schedule Upload API Endpoints

Provides endpoints for schedule file upload preview and confirmation.

Story: 12.3 - Schedule Upload API
AC: #1 - CSV Upload Preview
AC: #2 - Upload Confirmation
AC: #3 - Excel Support
AC: #4 - Fuzzy Asset Matching
AC: #5 - Validation Errors
"""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.config import get_settings
from app.core.security import get_current_user
from app.models.user import CurrentUser
from app.schemas.schedule import (
    ScheduleConfirmRequest,
    ScheduleConfirmResponse,
    SchedulePreviewResponse,
)
from app.services.schedule_parser import (
    assemble_preview,
    detect_file_format,
    parse_csv,
    parse_excel,
    validate_headers,
)

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_ROWS = 50_000  # Maximum number of data rows allowed


async def get_supabase_client():
    """Get Supabase client for database operations."""
    from supabase import create_client

    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase not configured",
        )

    return create_client(settings.supabase_url, settings.supabase_key)


@router.post(
    "/upload",
    response_model=SchedulePreviewResponse,
    summary="Upload Schedule File for Preview",
    description="Upload a CSV or Excel file to preview schedule data before committing.",
)
async def upload_schedule(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
) -> SchedulePreviewResponse:
    """
    Parse and validate an uploaded schedule file, returning a preview.

    No data is committed to the database. The preview includes:
    - Parsed row count
    - Asset matching results (exact, fuzzy, unmatched)
    - Product matching results (existing vs new)
    - Per-row validation errors

    AC#1: CSV Upload Preview
    AC#3: Excel Support
    AC#4: Fuzzy Asset Matching
    AC#5: Validation Errors
    """
    try:
        # Detect file format
        file_format = detect_file_format(file.filename or "", file.content_type)
        if file_format is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file type. Only .csv and .xlsx files are accepted.",
            )

        # Check file size before reading full content
        # Read a chunk slightly larger than the limit to detect oversized files
        file_bytes = await file.read(MAX_FILE_SIZE + 1)
        if len(file_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds the 5MB limit.",
            )

        # Check empty file
        if len(file_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty.",
            )

        # Parse file based on format
        if file_format == "csv":
            parsed_rows = parse_csv(file_bytes)
        else:
            try:
                parsed_rows = parse_excel(file_bytes)
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to parse Excel file. Ensure it is a valid .xlsx file.",
                )

        # Validate headers (check first row keys)
        if parsed_rows:
            headers = list(parsed_rows[0].keys())
            missing = validate_headers(headers)
            if missing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required columns: {', '.join(missing)}",
                )

        # Check row count limits
        if len(parsed_rows) > MAX_ROWS:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File is too large. Maximum {MAX_ROWS} rows allowed, found {len(parsed_rows)}.",
            )

        # Check at least 1 data row
        if len(parsed_rows) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must contain at least 1 data row.",
            )

        # Fetch assets from DB for matching
        client = await get_supabase_client()
        assets_response = client.table("assets").select("id, name").execute()
        asset_names_map: Dict[str, str] = {}
        for asset in (assets_response.data or []):
            asset_names_map[asset["name"]] = asset["id"]

        # Fetch existing products from DB for matching
        products_response = client.table("products").select("id, name").execute()
        existing_products: Dict[str, str] = {}
        for product in (products_response.data or []):
            existing_products[product["name"]] = product["id"]

        # Assemble preview
        preview = assemble_preview(parsed_rows, asset_names_map, existing_products)
        return preview

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error processing schedule upload: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process schedule upload",
        )


@router.post(
    "/upload/confirm",
    response_model=ScheduleConfirmResponse,
    summary="Confirm and Commit Schedule Data",
    description="Commit validated schedule data from the preview step to the database.",
)
async def confirm_schedule(
    body: ScheduleConfirmRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> ScheduleConfirmResponse:
    """
    Commit confirmed schedule rows to the database.

    For each row:
    1. Find or create the product in the products table
    2. Delete existing production_schedule rows matching (asset_id, scheduled_date, shift)
    3. Insert new production_schedule row

    AC#2: Upload Confirmation
    """
    try:
        client = await get_supabase_client()

        # Fetch existing products for lookup
        products_response = client.table("products").select("id, name").execute()
        existing_products: Dict[str, str] = {}
        for product in (products_response.data or []):
            existing_products[product["name"]] = product["id"]

        products_created = 0
        rows_inserted = 0

        # Resolve all product IDs before mutating production_schedule,
        # so that a failure during product creation doesn't leave orphaned schedule deletes.
        row_product_ids: list = []
        for row in body.rows:
            product_id = existing_products.get(row.product_name)
            if product_id is None:
                insert_result = client.table("products").insert({
                    "name": row.product_name,
                }).execute()
                if insert_result.data:
                    product_id = insert_result.data[0]["id"]
                    existing_products[row.product_name] = product_id
                    products_created += 1
            row_product_ids.append(product_id)

        # Perform delete-then-insert upserts for each row
        for row, product_id in zip(body.rows, row_product_ids):
            # Delete existing rows for this (asset_id, scheduled_date, shift) combo
            client.table("production_schedule") \
                .delete() \
                .eq("asset_id", row.asset_id) \
                .eq("scheduled_date", row.scheduled_date) \
                .eq("shift", row.shift) \
                .execute()

            # Insert new row
            client.table("production_schedule").insert({
                "asset_id": row.asset_id,
                "product_id": product_id,
                "scheduled_quantity": row.scheduled_quantity,
                "scheduled_date": row.scheduled_date,
                "shift": row.shift,
            }).execute()
            rows_inserted += 1

        return ScheduleConfirmResponse(
            rows_inserted=rows_inserted,
            products_created=products_created,
            total_processed=len(body.rows),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error confirming schedule upload: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to confirm schedule upload",
        )
