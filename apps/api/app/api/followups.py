"""
Follow-Ups API Endpoints

Story: 15.2 - Email Notification Service
Provides follow-up creation with async email notification dispatch.
"""

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from supabase import create_client

from app.core.config import get_settings
from app.core.security import get_current_user, security
from app.models.user import CurrentUser
from app.schemas.action import FollowUpCreateRequest, FollowUpResponse
from app.services.email import get_notification_service

logger = logging.getLogger(__name__)

router = APIRouter()


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
