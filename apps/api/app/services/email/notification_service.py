"""
Follow-Up Notification Service - orchestrates email sending and message logging.

Story: 15.2 - Email Notification Service
Story: 15.3 - Response Capture via Token Link (token integration)
AC#1: Email sent on follow-up assignment
AC#2: Graceful degradation when SMTP not configured
AC#3: Graceful failure on send error
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from app.core.config import get_settings
from app.services.email.templates import render_assignment_email


def get_token_service():
    """Lazy import to avoid circular dependency."""
    from app.services.email import get_token_service as _get_token_service
    return _get_token_service()

logger = logging.getLogger(__name__)


class FollowUpNotificationService:
    """Orchestrates email notification sending and followup_messages record creation."""

    def __init__(self, email_provider: Any, supabase_client: Any):
        self.email_provider = email_provider
        self.supabase_client = supabase_client

    async def send_assignment_notification(self, followup_data: Dict[str, Any]) -> None:
        """Send an assignment notification email and log to followup_messages.

        This method never raises exceptions. All errors are caught and logged.

        AC#2: Returns early with warning if SMTP not configured.
        AC#3: Creates followup_messages with failed_at on send failure.
        """
        try:
            settings = get_settings()

            if not settings.smtp_configured:
                logger.warning(
                    "Email notification not sent: SMTP not configured. "
                    f"Follow-up {followup_data.get('followup_id')} will not receive email."
                )
                return

            # Resolve assignee email from auth.users
            assigned_to = followup_data.get("assigned_to")
            assignee_email = None
            try:
                user_result = self.supabase_client.auth.admin.get_user_by_id(assigned_to)
                if user_result and user_result.user:
                    assignee_email = user_result.user.email
            except Exception as e:
                logger.error(f"Failed to resolve assignee {assigned_to}: {e}")

            if not assignee_email:
                logger.error(
                    f"Could not resolve email for assignee {assigned_to}. "
                    f"Follow-up {followup_data.get('followup_id')} notification skipped."
                )
                # Record failed notification attempt for audit trail
                try:
                    self.supabase_client.table("followup_messages").insert({
                        "followup_id": followup_data.get("followup_id"),
                        "sender_id": followup_data.get("assigned_by"),
                        "sender_email": followup_data.get("sender_email", ""),
                        "direction": "outbound",
                        "message_type": "assignment",
                        "subject": f"[Action Required] {followup_data.get('category', '')} - {followup_data.get('asset_name', '')}: {followup_data.get('action_summary', '')}",
                        "body": "",
                        "sent_at": None,
                        "failed_at": datetime.now(timezone.utc).isoformat(),
                    }).execute()
                except Exception as insert_err:
                    logger.error(
                        f"Failed to create followup_messages record for unresolved assignee: {insert_err}"
                    )
                return

            # Generate response token (Story 15.3)
            response_token = None
            try:
                token_service = get_token_service()
                response_token = token_service.generate_token(
                    followup_data.get("followup_id", ""),
                    assignee_email,
                )
            except Exception as e:
                logger.error(f"Failed to generate response token: {e}")

            # Render email template
            email_content = render_assignment_email(
                category=followup_data.get("category", ""),
                asset_name=followup_data.get("asset_name", ""),
                action_summary=followup_data.get("action_summary", ""),
                recommendation=followup_data.get("recommendation", ""),
                evidence_summary=followup_data.get("evidence_summary", ""),
                financial_impact=followup_data.get("financial_impact"),
                assigner_name=followup_data.get("assigner_name", ""),
                note=followup_data.get("note"),
                followup_id=followup_data.get("followup_id", ""),
                app_base_url=settings.app_base_url,
                response_token=response_token,
            )

            # Send email
            result = await self.email_provider.send(
                recipient=assignee_email,
                subject=email_content["subject"],
                html_body=email_content["html_body"],
                text_body=email_content["text_body"],
            )

            # Log to followup_messages
            sent_at = result.sent_at if result.success else None
            failed_at = datetime.now(timezone.utc) if not result.success else None

            if not result.success:
                logger.error(
                    f"Email send failed for follow-up {followup_data.get('followup_id')} "
                    f"to {assignee_email}: {result.error}"
                )

            try:
                self.supabase_client.table("followup_messages").insert({
                    "followup_id": followup_data.get("followup_id"),
                    "sender_id": followup_data.get("assigned_by"),
                    "sender_email": followup_data.get("sender_email", ""),
                    "direction": "outbound",
                    "message_type": "assignment",
                    "subject": email_content["subject"],
                    "body": email_content["html_body"],
                    "sent_at": sent_at.isoformat() if sent_at else None,
                    "failed_at": failed_at.isoformat() if failed_at else None,
                }).execute()
            except Exception as e:
                logger.error(
                    f"Failed to create followup_messages record for {followup_data.get('followup_id')}: {e}"
                )

        except Exception as e:
            logger.error(f"Unexpected error in send_assignment_notification: {e}")
