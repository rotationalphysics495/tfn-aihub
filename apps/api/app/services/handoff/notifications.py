"""
Handoff Notification Service (Story 9.8)

Backend service for triggering notifications when handoffs are acknowledged.

Task 3: Create backend notification trigger service (AC: 1, 5)
- 3.1: Create notifications.py service
- 3.2: Add notification trigger to acknowledgment save workflow
- 3.3: Fetch outgoing supervisor's notification preferences
- 3.4: Call Edge Function for push notification if preferences allow
- 3.5: Insert notification record for in-app delivery tracking

References:
- [Source: architecture/voice-briefing.md#Push-Notifications-Architecture]
- [Source: epic-9.md#Story-9.8]
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4
import httpx

from supabase import Client

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class NotificationError(Exception):
    """Error raised when notification delivery fails."""

    def __init__(self, message: str, is_retryable: bool = False):
        self.message = message
        self.is_retryable = is_retryable
        super().__init__(self.message)


class HandoffNotificationService:
    """
    Handoff Notification Service.

    Story 9.8 Implementation:
    - AC#1: Trigger notification when acknowledgment is saved
    - AC#3: Send push notification (via Edge Function)
    - AC#4: Respect notification preferences
    - AC#5: Deliver within 60 seconds (NFR)

    Usage:
        service = HandoffNotificationService(supabase_client)
        await service.notify_handoff_acknowledged(
            handoff_id="...",
            acknowledgment_id="...",
            outgoing_user_id="...",
            acknowledging_user_id="...",
        )
    """

    def __init__(self, supabase: Optional[Client] = None):
        """
        Initialize the HandoffNotificationService.

        Args:
            supabase: Optional Supabase client instance
        """
        self.supabase = supabase
        self.settings = get_settings()
        self._edge_function_url = None

    @property
    def edge_function_url(self) -> str:
        """Get the Edge Function URL for notifications."""
        if self._edge_function_url:
            return self._edge_function_url

        if self.settings.supabase_url:
            self._edge_function_url = (
                f"{self.settings.supabase_url}/functions/v1/notify-handoff-ack"
            )
        else:
            self._edge_function_url = ""

        return self._edge_function_url

    async def notify_handoff_acknowledged(
        self,
        handoff_id: str,
        acknowledgment_id: str,
        outgoing_user_id: str,
        acknowledging_user_id: str,
        acknowledging_user_name: Optional[str] = None,
        acknowledged_at: Optional[datetime] = None,
        notes: Optional[str] = None,
    ) -> bool:
        """
        Notify outgoing supervisor that their handoff was acknowledged (AC#1).

        This method:
        1. Checks notification preferences (Task 3.3)
        2. Creates in-app notification record (Task 3.5)
        3. Calls Edge Function for push notification (Task 3.4)

        Args:
            handoff_id: UUID of the handoff
            acknowledgment_id: UUID of the acknowledgment record
            outgoing_user_id: User ID to notify (handoff creator)
            acknowledging_user_id: User ID who acknowledged
            acknowledging_user_name: Display name of acknowledging user
            acknowledged_at: Timestamp of acknowledgment
            notes: Optional acknowledgment notes

        Returns:
            True if notification was sent successfully

        Raises:
            NotificationError: If notification fails (non-fatal, logged only)
        """
        start_time = datetime.now(timezone.utc)

        if acknowledged_at is None:
            acknowledged_at = start_time

        logger.info(
            f"Notifying handoff acknowledgment: handoff={handoff_id}, "
            f"outgoing_user={outgoing_user_id}, acknowledging_user={acknowledging_user_id}"
        )

        try:
            # Task 3.3: Check notification preferences
            preferences_enabled = await self._check_notification_preferences(
                outgoing_user_id
            )

            # Task 3.5: Create in-app notification record
            notification_id = await self._create_notification_record(
                user_id=outgoing_user_id,
                handoff_id=handoff_id,
                acknowledgment_id=acknowledgment_id,
                acknowledging_user_id=acknowledging_user_id,
                acknowledging_user_name=acknowledging_user_name,
                acknowledged_at=acknowledged_at,
                has_notes=bool(notes),
            )

            if notification_id:
                logger.info(f"Created in-app notification record: {notification_id}")

            # Task 3.4: Call Edge Function for push notification
            if preferences_enabled:
                push_success = await self._send_push_notification(
                    handoff_id=handoff_id,
                    acknowledgment_id=acknowledgment_id,
                    outgoing_user_id=outgoing_user_id,
                    acknowledging_user_id=acknowledging_user_id,
                    acknowledging_user_name=acknowledging_user_name,
                    acknowledged_at=acknowledged_at,
                    notes=notes,
                )

                if push_success:
                    logger.info("Push notification sent successfully")
                else:
                    logger.warning("Push notification delivery failed")
            else:
                logger.info(
                    f"Push notifications disabled for user {outgoing_user_id}"
                )

            # AC#5: Log timing for NFR compliance
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.info(f"Notification delivery completed in {elapsed:.2f}s")

            if elapsed > 60:
                logger.warning(
                    f"Notification delivery exceeded 60-second target: {elapsed:.2f}s"
                )

            return True

        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            # Don't raise - notifications are best-effort, not critical path
            return False

    async def _check_notification_preferences(self, user_id: str) -> bool:
        """
        Check if user has notifications enabled (Task 3.3).

        Args:
            user_id: User ID to check

        Returns:
            True if notifications are enabled (default)
        """
        if not self.supabase:
            # Default to enabled if no database connection
            return True

        try:
            result = (
                self.supabase.table("user_preferences")
                .select("handoff_notifications_enabled")
                .eq("user_id", user_id)
                .execute()
            )

            if result.data and len(result.data) > 0:
                return result.data[0].get("handoff_notifications_enabled", True)

            # Default to enabled if no preferences exist
            return True

        except Exception as e:
            logger.warning(f"Error checking preferences for {user_id}: {e}")
            # Default to enabled on error
            return True

    async def _create_notification_record(
        self,
        user_id: str,
        handoff_id: str,
        acknowledgment_id: str,
        acknowledging_user_id: str,
        acknowledging_user_name: Optional[str],
        acknowledged_at: datetime,
        has_notes: bool,
    ) -> Optional[str]:
        """
        Create an in-app notification record (Task 3.5).

        Args:
            user_id: User to notify
            handoff_id: Related handoff ID
            acknowledgment_id: Related acknowledgment ID
            acknowledging_user_id: User who acknowledged
            acknowledging_user_name: Display name
            acknowledged_at: Timestamp
            has_notes: Whether notes were attached

        Returns:
            Notification ID if created, None otherwise
        """
        if not self.supabase:
            logger.warning("No Supabase client - skipping notification record")
            return None

        try:
            notification_id = str(uuid4())

            title = "Handoff Acknowledged"
            message = (
                f"{acknowledging_user_name} acknowledged your handoff"
                if acknowledging_user_name
                else "Your handoff was acknowledged"
            )

            data = {
                "id": notification_id,
                "user_id": user_id,
                "notification_type": "handoff_acknowledged",
                "title": title,
                "message": message,
                "entity_type": "shift_handoff",
                "entity_id": handoff_id,
                "metadata": {
                    "acknowledgment_id": acknowledgment_id,
                    "acknowledging_user_id": acknowledging_user_id,
                    "acknowledging_user_name": acknowledging_user_name,
                    "acknowledged_at": acknowledged_at.isoformat(),
                    "has_notes": has_notes,
                },
                "is_read": False,
                "is_dismissed": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            result = self.supabase.table("notifications").insert(data).execute()

            if result.data:
                return notification_id

            return None

        except Exception as e:
            logger.error(f"Error creating notification record: {e}")
            return None

    async def _send_push_notification(
        self,
        handoff_id: str,
        acknowledgment_id: str,
        outgoing_user_id: str,
        acknowledging_user_id: str,
        acknowledging_user_name: Optional[str],
        acknowledged_at: datetime,
        notes: Optional[str],
    ) -> bool:
        """
        Call Edge Function to send push notification (Task 3.4).

        Args:
            handoff_id: UUID of the handoff
            acknowledgment_id: UUID of the acknowledgment
            outgoing_user_id: User to notify
            acknowledging_user_id: User who acknowledged
            acknowledging_user_name: Display name
            acknowledged_at: Timestamp
            notes: Optional notes

        Returns:
            True if push was sent successfully
        """
        if not self.edge_function_url:
            logger.warning("Edge Function URL not configured")
            return False

        payload = {
            "acknowledgment_id": acknowledgment_id,
            "handoff_id": handoff_id,
            "outgoing_user_id": outgoing_user_id,
            "acknowledging_user_id": acknowledging_user_id,
            "acknowledging_user_name": acknowledging_user_name,
            "acknowledged_at": acknowledged_at.isoformat(),
            "notes": notes,
        }

        headers = {
            "Content-Type": "application/json",
        }

        # Add service role key for authorization if available
        if self.settings.supabase_key:
            headers["Authorization"] = f"Bearer {self.settings.supabase_key}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.edge_function_url,
                    json=payload,
                    headers=headers,
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("success", False)
                else:
                    logger.warning(
                        f"Edge Function returned {response.status_code}: "
                        f"{response.text}"
                    )
                    return False

        except httpx.TimeoutException:
            logger.warning("Edge Function call timed out")
            return False
        except Exception as e:
            logger.error(f"Error calling Edge Function: {e}")
            return False


# Module-level singleton
_notification_service: Optional[HandoffNotificationService] = None


def get_handoff_notification_service(
    supabase: Optional[Client] = None,
) -> HandoffNotificationService:
    """
    Get or create the HandoffNotificationService instance.

    Args:
        supabase: Optional Supabase client instance

    Returns:
        HandoffNotificationService instance
    """
    global _notification_service
    if _notification_service is None:
        _notification_service = HandoffNotificationService(supabase)
    return _notification_service
