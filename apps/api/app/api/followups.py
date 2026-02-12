"""
Follow-Ups API Endpoints

Story: 15.2 - Email Notification Service
Story: 15.3 - Response Capture via Token Link

Provides follow-up creation with async email notification dispatch,
and public token-based response endpoints.
"""

import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials
from supabase import create_client

from app.core.config import get_settings
from app.core.security import get_current_user, security
from app.models.user import CurrentUser
from app.schemas.action import (
    FollowUpCreateRequest,
    FollowUpResponse,
    TokenResponseRequest,
    TokenContextResponse,
    TokenResponseResult,
)
from app.services.email import get_notification_service, get_token_service

logger = logging.getLogger(__name__)

router = APIRouter()


def get_service_role_client():
    """Get a Supabase client using the service_role key (bypasses RLS)."""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_key)


@router.post("", status_code=201, response_model=FollowUpResponse)
async def create_followup(
    body: FollowUpCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Create a follow-up assignment and trigger async email notification.

    Story 15.2 AC#1: Creates follow-up record and sends email notification.
    AC#2: Email failure does not block follow-up creation.
    AC#3: Email errors are logged and recorded in followup_messages.
    """
    settings = get_settings()
    user_token = credentials.credentials

    try:
        # Use user-scoped client for RLS enforcement (assigned_by = auth.uid())
        client = create_client(settings.supabase_url, user_token)

        insert_data = {
            "action_item_id": body.action_item_id,
            "action_summary": body.action_summary,
            "asset_name": body.asset_name,
            "category": body.category,
            "assigned_to": body.assigned_to,
            "assigned_by": current_user.id,
            "note": body.note,
            "report_date": body.report_date,
            "status": "assigned",
        }

        result = (
            client.table("action_followups")
            .insert(insert_data)
            .execute()
        )

        if not result.data:
            raise HTTPException(
                status_code=500,
                detail="Failed to create follow-up.",
            )

        record = result.data[0]

        # Fire-and-forget email notification
        notification_data = {
            "followup_id": record.get("id"),
            "action_item_id": body.action_item_id,
            "action_summary": body.action_summary,
            "asset_name": body.asset_name,
            "category": body.category,
            "assigned_to": body.assigned_to,
            "assigned_by": current_user.id,
            "sender_email": current_user.email or "",
            "assigner_name": current_user.email or "Unknown",
            "recommendation": body.action_summary,
            "evidence_summary": "",
            "note": body.note,
            "report_date": body.report_date,
        }

        try:
            notification_service = get_notification_service()
            asyncio.create_task(
                notification_service.send_assignment_notification(notification_data)
            )
        except Exception as e:
            logger.error(f"Failed to dispatch notification: {e}")

        return FollowUpResponse(**record)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create follow-up: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create follow-up. Please try again.",
        )


@router.get("/{followup_id}/context", response_model=TokenContextResponse)
async def get_followup_context(
    followup_id: str,
    token: str = Query(..., description="Response token from the email link"),
):
    """
    Fetch follow-up context for the response form (PUBLIC - no auth required).

    Story 15.3 AC#1: Response page renders via token link.
    The token serves as authentication — no JWT required.
    """
    token_service = get_token_service()
    service_client = get_service_role_client()

    try:
        validation = token_service.validate_token(token)

        if not validation.is_valid:
            if validation.error_reason == "expired":
                raise HTTPException(
                    status_code=400,
                    detail={"error_reason": "expired", "detail": "Token expired"},
                )
            else:
                raise HTTPException(
                    status_code=404,
                    detail={"error_reason": "invalid", "detail": "Invalid link"},
                )

        # Verify the URL followup_id matches the token's followup_id (prevent IDOR)
        if validation.followup_id != followup_id:
            raise HTTPException(
                status_code=404,
                detail={"error_reason": "invalid", "detail": "Invalid link"},
            )

        # Fetch follow-up context from action_followups
        result = (
            service_client.table("action_followups")
            .select("action_summary, asset_name, category, assigned_by, note, report_date")
            .eq("id", validation.followup_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Follow-up not found")

        record = result.data[0]

        # Resolve assigner details
        assigned_by_email = ""
        assigned_by_name = ""
        assigned_by_id = record.get("assigned_by")
        if assigned_by_id:
            try:
                user_result = service_client.auth.admin.get_user_by_id(assigned_by_id)
                if user_result and user_result.user:
                    assigned_by_email = user_result.user.email or ""
                    metadata = getattr(user_result.user, 'user_metadata', {}) or {}
                    assigned_by_name = metadata.get("full_name", assigned_by_email)
            except Exception as e:
                logger.error(f"Failed to resolve assigner {assigned_by_id}: {e}")
                assigned_by_name = assigned_by_email

        return TokenContextResponse(
            action_summary=record.get("action_summary", ""),
            asset_name=record.get("asset_name", ""),
            category=record.get("category", ""),
            assigned_by_email=assigned_by_email,
            assigned_by_name=assigned_by_name,
            note=record.get("note"),
            report_date=record.get("report_date", ""),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get followup context: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve follow-up context.",
        )


@router.post("/respond", response_model=TokenResponseResult)
async def submit_followup_response(
    body: TokenResponseRequest,
):
    """
    Submit a response via token link (PUBLIC - no auth required).

    Story 15.3 AC#2: Response submission creates message record.
    The token serves as authentication — no JWT required.
    """
    token_service = get_token_service()
    service_client = get_service_role_client()

    try:
        validation = token_service.validate_token(body.token)

        if not validation.is_valid:
            if validation.error_reason == "expired":
                raise HTTPException(
                    status_code=400,
                    detail="Token expired",
                )
            else:
                raise HTTPException(
                    status_code=404,
                    detail="Invalid link",
                )

        # Create inbound message record
        message_data = {
            "followup_id": validation.followup_id,
            "sender_email": validation.assignee_email,
            "direction": "inbound",
            "message_type": "response",
            "body": body.response_text,
            "sent_at": datetime.now(timezone.utc).isoformat(),
        }

        service_client.table("followup_messages").insert(message_data).execute()

        # Update action_followups status to 'in_progress' only if currently 'assigned'
        (
            service_client.table("action_followups")
            .update({"status": "in_progress"})
            .eq("id", validation.followup_id)
            .eq("status", "assigned")
            .execute()
        )

        # Mark token as used
        token_service.mark_token_used(body.token)

        return TokenResponseResult(success=True, message="Response recorded")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit followup response: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to submit response. Please try again.",
        )
