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

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi.security import HTTPAuthorizationCredentials
from supabase import create_client

from app.core.config import get_settings
from app.core.security import get_current_user, security
from app.models.user import CurrentUser
from app.schemas.action import (
    FollowUpCreateRequest,
    FollowUpMessageListResponse,
    FollowUpMessageResponse,
    FollowUpResponse,
    FollowUpViewedResponse,
    TokenResponseRequest,
    TokenContextResponse,
    TokenResponseResult,
)
from app.services.email import get_notification_service, get_token_service
from app.services.notifications import get_teams_client, build_followup_assignment_card

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
        # Use service role client with user JWT for RLS enforcement
        client = create_client(settings.supabase_url, settings.supabase_key)
        client.postgrest.auth(user_token)

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

        # Fire-and-forget Teams notification (Story 18.4)
        try:
            if settings.teams_configured:
                assigner_name = (current_user.email or "").split("@")[0] or "Unknown"

                teams_followup_data = {
                    "action_summary": body.action_summary,
                    "asset_name": body.asset_name,
                    "category": body.category,
                    "assigner_name": assigner_name,
                    "note": body.note,
                    "report_date": body.report_date,
                }

                card = build_followup_assignment_card(teams_followup_data, settings.app_base_url)
                teams_client = get_teams_client()

                asyncio.create_task(
                    teams_client.send_card(card)
                )
            else:
                logger.debug("Teams notification skipped: webhook not configured")
        except Exception as e:
            logger.error(f"Failed to dispatch Teams notification: {e}")

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


@router.get("/{followup_id}/messages", response_model=FollowUpMessageListResponse)
async def get_followup_messages(
    followup_id: str = Path(
        ...,
        pattern=r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
        description="Follow-up UUID",
    ),
    current_user: CurrentUser = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Get the chronological message thread for a follow-up.

    Story 15.4 AC#1, AC#3, AC#4, AC#5:
    - Returns messages sorted by sent_at ascending
    - Includes follow-up context wrapper with assignee info
    - Computes has_unread server-side
    - Application-level access control (assigner or assignee only)
    """
    settings = get_settings()
    user_token = credentials.credentials

    try:
        client = create_client(settings.supabase_url, settings.supabase_key)
        client.postgrest.auth(user_token)

        # Fetch the follow-up record for context and access control
        followup_result = (
            client.table("action_followups")
            .select("*")
            .eq("id", followup_id)
            .execute()
        )

        if not followup_result.data:
            raise HTTPException(status_code=404, detail="Follow-up not found")

        followup = followup_result.data[0]

        # Application-level access control: user must be assigner or assignee
        if (followup.get("assigned_by") != current_user.id and
                followup.get("assigned_to") != current_user.id):
            raise HTTPException(status_code=404, detail="Follow-up not found")

        # Fetch messages sorted chronologically
        messages_result = (
            client.table("followup_messages")
            .select("id, direction, message_type, sender_email, subject, body, sent_at")
            .eq("followup_id", followup_id)
            .order("sent_at")
            .execute()
        )

        messages_data = messages_result.data or []

        # Compute has_unread: any inbound message with sent_at > last_viewed_at
        last_viewed_at = followup.get("last_viewed_at")
        has_unread = False
        for msg in messages_data:
            if msg.get("direction") == "inbound":
                if last_viewed_at is None:
                    has_unread = True
                    break
                elif msg.get("sent_at", "") > last_viewed_at:
                    has_unread = True
                    break

        messages = [FollowUpMessageResponse(**msg) for msg in messages_data]

        return FollowUpMessageListResponse(
            followup_id=followup.get("id", followup_id),
            action_summary=followup.get("action_summary", ""),
            assignee_name=followup.get("assignee_name"),
            assignee_email=followup.get("assigned_to_email"),
            status=followup.get("status", ""),
            messages=messages,
            has_unread=has_unread,
            last_viewed_at=followup.get("last_viewed_at"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get followup messages: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve messages.",
        )


@router.patch("/{followup_id}/viewed", response_model=FollowUpViewedResponse)
async def mark_followup_viewed(
    followup_id: str = Path(
        ...,
        pattern=r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
        description="Follow-up UUID",
    ),
    current_user: CurrentUser = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Mark a follow-up as viewed, updating last_viewed_at to now.

    Story 15.4 AC#2: Updates last_viewed_at for unread indicator clearing.
    """
    settings = get_settings()
    user_token = credentials.credentials

    try:
        client = create_client(settings.supabase_url, settings.supabase_key)
        client.postgrest.auth(user_token)

        # Fetch the follow-up for access control
        followup_result = (
            client.table("action_followups")
            .select("*")
            .eq("id", followup_id)
            .execute()
        )

        if not followup_result.data:
            raise HTTPException(status_code=404, detail="Follow-up not found")

        followup = followup_result.data[0]

        # Application-level access control
        if (followup.get("assigned_by") != current_user.id and
                followup.get("assigned_to") != current_user.id):
            raise HTTPException(status_code=404, detail="Follow-up not found")

        # Update last_viewed_at
        now = datetime.now(timezone.utc).isoformat()
        update_result = (
            client.table("action_followups")
            .update({"last_viewed_at": now})
            .eq("id", followup_id)
            .execute()
        )

        viewed_at = now
        if update_result.data:
            viewed_at = update_result.data[0].get("last_viewed_at", now)

        return FollowUpViewedResponse(
            success=True,
            last_viewed_at=viewed_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark followup as viewed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update viewed status.",
        )
