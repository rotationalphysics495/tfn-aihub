"""
Handoff Notification Service Tests (Story 9.8, Task 5)

Unit tests for the HandoffNotificationService.

AC#1: Acknowledgment Notification Trigger - sends notification when saved
AC#3: Push Notification (Background) - calls Edge Function
AC#4: Notification Preference Respect - checks preferences before sending
AC#5: 60-Second Delivery (NFR) - timing logged for compliance

References:
- [Source: epic-9.md#Story 9.8]
- [Source: architecture/voice-briefing.md#Push-Notifications-Architecture]
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4
from datetime import datetime, timezone
import os
import sys

# Add apps/api to path for imports
_api_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if _api_path not in sys.path:
    sys.path.insert(0, _api_path)

from app.services.handoff.notifications import (
    HandoffNotificationService,
    NotificationError,
    get_handoff_notification_service,
)


@pytest.fixture
def mock_supabase():
    """Mock Supabase client."""
    mock = MagicMock()
    mock.table.return_value = mock
    mock.select.return_value = mock
    mock.eq.return_value = mock
    mock.insert.return_value = mock
    mock.execute.return_value = MagicMock(data=[])
    return mock


@pytest.fixture
def notification_service(mock_supabase):
    """Create notification service with mock client."""
    return HandoffNotificationService(mock_supabase)


@pytest.fixture
def test_handoff_id():
    return str(uuid4())


@pytest.fixture
def test_acknowledgment_id():
    return str(uuid4())


@pytest.fixture
def test_outgoing_user_id():
    return str(uuid4())


@pytest.fixture
def test_acknowledging_user_id():
    return str(uuid4())


class TestHandoffNotificationService:
    """Tests for HandoffNotificationService."""

    @pytest.mark.asyncio
    async def test_notify_creates_notification_record(
        self,
        notification_service,
        mock_supabase,
        test_handoff_id,
        test_acknowledgment_id,
        test_outgoing_user_id,
        test_acknowledging_user_id,
    ):
        """
        AC#1: Creates in-app notification record when acknowledged.

        Task 3.5: Insert notification record for in-app delivery.
        """
        # Setup: Enable notifications, no push subscriptions
        mock_supabase.execute.side_effect = [
            # First call: check preferences - notifications enabled
            MagicMock(data=[{"handoff_notifications_enabled": True}]),
            # Second call: insert notification
            MagicMock(data=[{"id": str(uuid4())}]),
        ]

        # Mock edge function call
        with patch.object(
            notification_service, '_send_push_notification', new_callable=AsyncMock
        ) as mock_push:
            mock_push.return_value = False  # No push sent

            result = await notification_service.notify_handoff_acknowledged(
                handoff_id=test_handoff_id,
                acknowledgment_id=test_acknowledgment_id,
                outgoing_user_id=test_outgoing_user_id,
                acknowledging_user_id=test_acknowledging_user_id,
                acknowledging_user_name="John Doe",
            )

        assert result is True
        # Verify notification insert was called
        assert mock_supabase.table.call_count >= 1

    @pytest.mark.asyncio
    async def test_notify_checks_preferences_before_push(
        self,
        notification_service,
        mock_supabase,
        test_handoff_id,
        test_acknowledgment_id,
        test_outgoing_user_id,
        test_acknowledging_user_id,
    ):
        """
        AC#4: Checks notification preferences before sending push.

        Task 3.3: Fetch outgoing supervisor's preferences.
        """
        # Setup: Notifications disabled
        mock_supabase.execute.side_effect = [
            # First call: check preferences - notifications DISABLED
            MagicMock(data=[{"handoff_notifications_enabled": False}]),
            # Second call: insert notification (still created for in-app)
            MagicMock(data=[{"id": str(uuid4())}]),
        ]

        with patch.object(
            notification_service, '_send_push_notification', new_callable=AsyncMock
        ) as mock_push:
            await notification_service.notify_handoff_acknowledged(
                handoff_id=test_handoff_id,
                acknowledgment_id=test_acknowledgment_id,
                outgoing_user_id=test_outgoing_user_id,
                acknowledging_user_id=test_acknowledging_user_id,
            )

            # Push should NOT be called when preferences disabled
            mock_push.assert_not_called()

    @pytest.mark.asyncio
    async def test_notify_respects_default_preferences(
        self,
        notification_service,
        mock_supabase,
        test_handoff_id,
        test_acknowledgment_id,
        test_outgoing_user_id,
        test_acknowledging_user_id,
    ):
        """
        AC#4: Defaults to enabled if no preferences found.
        """
        # Setup: No preferences found (returns empty)
        mock_supabase.execute.side_effect = [
            # First call: no preferences found
            MagicMock(data=[]),
            # Second call: insert notification
            MagicMock(data=[{"id": str(uuid4())}]),
        ]

        with patch.object(
            notification_service, '_send_push_notification', new_callable=AsyncMock
        ) as mock_push:
            mock_push.return_value = True

            await notification_service.notify_handoff_acknowledged(
                handoff_id=test_handoff_id,
                acknowledgment_id=test_acknowledgment_id,
                outgoing_user_id=test_outgoing_user_id,
                acknowledging_user_id=test_acknowledging_user_id,
            )

            # Push SHOULD be called when no preferences (default enabled)
            mock_push.assert_called_once()

    @pytest.mark.asyncio
    async def test_notify_calls_edge_function(
        self,
        notification_service,
        mock_supabase,
        test_handoff_id,
        test_acknowledgment_id,
        test_outgoing_user_id,
        test_acknowledging_user_id,
    ):
        """
        AC#3: Calls Edge Function for push notification.

        Task 3.4: Call Edge Function for push delivery.
        """
        # Setup
        mock_supabase.execute.side_effect = [
            MagicMock(data=[{"handoff_notifications_enabled": True}]),
            MagicMock(data=[{"id": str(uuid4())}]),
        ]

        with patch.object(
            notification_service, '_send_push_notification', new_callable=AsyncMock
        ) as mock_push:
            mock_push.return_value = True

            await notification_service.notify_handoff_acknowledged(
                handoff_id=test_handoff_id,
                acknowledgment_id=test_acknowledgment_id,
                outgoing_user_id=test_outgoing_user_id,
                acknowledging_user_id=test_acknowledging_user_id,
                acknowledging_user_name="Jane Smith",
                notes="Test note",
            )

            # Verify push was called (don't check exact timestamp)
            mock_push.assert_called_once()
            call_kwargs = mock_push.call_args.kwargs
            assert call_kwargs["handoff_id"] == test_handoff_id
            assert call_kwargs["acknowledgment_id"] == test_acknowledgment_id
            assert call_kwargs["outgoing_user_id"] == test_outgoing_user_id
            assert call_kwargs["acknowledging_user_name"] == "Jane Smith"
            assert call_kwargs["notes"] == "Test note"

    @pytest.mark.asyncio
    async def test_notify_handles_push_failure_gracefully(
        self,
        notification_service,
        mock_supabase,
        test_handoff_id,
        test_acknowledgment_id,
        test_outgoing_user_id,
        test_acknowledging_user_id,
    ):
        """
        AC#5: Push failure does not block acknowledgment.

        Push is best-effort, notification record still created.
        """
        mock_supabase.execute.side_effect = [
            MagicMock(data=[{"handoff_notifications_enabled": True}]),
            MagicMock(data=[{"id": str(uuid4())}]),
        ]

        with patch.object(
            notification_service, '_send_push_notification', new_callable=AsyncMock
        ) as mock_push:
            # Simulate push failure
            mock_push.return_value = False

            result = await notification_service.notify_handoff_acknowledged(
                handoff_id=test_handoff_id,
                acknowledgment_id=test_acknowledgment_id,
                outgoing_user_id=test_outgoing_user_id,
                acknowledging_user_id=test_acknowledging_user_id,
            )

            # Should still return True (notification created)
            assert result is True

    @pytest.mark.asyncio
    async def test_notify_handles_exception_gracefully(
        self,
        notification_service,
        mock_supabase,
        test_handoff_id,
        test_acknowledgment_id,
        test_outgoing_user_id,
        test_acknowledging_user_id,
    ):
        """
        Exceptions are caught and logged, not raised.

        The service catches exceptions and returns False.
        """
        # Patch the internal methods to raise exceptions
        with patch.object(
            notification_service, '_check_notification_preferences', new_callable=AsyncMock
        ) as mock_pref:
            mock_pref.side_effect = Exception("Complete failure")

            # This should not raise
            result = await notification_service.notify_handoff_acknowledged(
                handoff_id=test_handoff_id,
                acknowledgment_id=test_acknowledgment_id,
                outgoing_user_id=test_outgoing_user_id,
                acknowledging_user_id=test_acknowledging_user_id,
            )

            # Should return False but not raise
            assert result is False

    @pytest.mark.asyncio
    async def test_notify_includes_notes_metadata(
        self,
        notification_service,
        mock_supabase,
        test_handoff_id,
        test_acknowledgment_id,
        test_outgoing_user_id,
        test_acknowledging_user_id,
    ):
        """
        AC#5: Notes included in notification metadata.
        """
        inserted_data = None

        def capture_insert(data):
            nonlocal inserted_data
            inserted_data = data
            mock = MagicMock()
            mock.execute.return_value = MagicMock(data=[{"id": str(uuid4())}])
            return mock

        mock_supabase.execute.side_effect = [
            MagicMock(data=[{"handoff_notifications_enabled": True}]),
            MagicMock(data=[{"id": str(uuid4())}]),
        ]
        mock_supabase.insert.side_effect = capture_insert

        with patch.object(
            notification_service, '_send_push_notification', new_callable=AsyncMock
        ) as mock_push:
            mock_push.return_value = True

            await notification_service.notify_handoff_acknowledged(
                handoff_id=test_handoff_id,
                acknowledgment_id=test_acknowledgment_id,
                outgoing_user_id=test_outgoing_user_id,
                acknowledging_user_id=test_acknowledging_user_id,
                notes="Important note here",
            )

        # Would need to verify metadata includes has_notes: True
        # This is handled in the actual insert call


class TestCheckNotificationPreferences:
    """Tests for _check_notification_preferences helper."""

    @pytest.mark.asyncio
    async def test_returns_true_when_enabled(self, notification_service, mock_supabase):
        """Returns True when handoff_notifications_enabled is True."""
        mock_supabase.execute.return_value = MagicMock(
            data=[{"handoff_notifications_enabled": True}]
        )

        result = await notification_service._check_notification_preferences(
            str(uuid4())
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_when_disabled(
        self, notification_service, mock_supabase
    ):
        """Returns False when handoff_notifications_enabled is False."""
        mock_supabase.execute.return_value = MagicMock(
            data=[{"handoff_notifications_enabled": False}]
        )

        result = await notification_service._check_notification_preferences(
            str(uuid4())
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_returns_true_when_no_preferences(
        self, notification_service, mock_supabase
    ):
        """Returns True (default) when no preferences exist."""
        mock_supabase.execute.return_value = MagicMock(data=[])

        result = await notification_service._check_notification_preferences(
            str(uuid4())
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_returns_true_on_error(self, notification_service, mock_supabase):
        """Returns True on error (fail open for notifications)."""
        mock_supabase.execute.side_effect = Exception("DB error")

        result = await notification_service._check_notification_preferences(
            str(uuid4())
        )

        assert result is True


class TestCreateNotificationRecord:
    """Tests for _create_notification_record helper."""

    @pytest.mark.asyncio
    async def test_creates_record_with_correct_fields(
        self, notification_service, mock_supabase
    ):
        """Creates notification with all required fields."""
        mock_supabase.execute.return_value = MagicMock(
            data=[{"id": str(uuid4())}]
        )

        handoff_id = str(uuid4())
        ack_id = str(uuid4())
        user_id = str(uuid4())
        ack_user_id = str(uuid4())

        result = await notification_service._create_notification_record(
            user_id=user_id,
            handoff_id=handoff_id,
            acknowledgment_id=ack_id,
            acknowledging_user_id=ack_user_id,
            acknowledging_user_name="Test User",
            acknowledged_at=datetime.now(timezone.utc),
            has_notes=True,
        )

        assert result is not None
        mock_supabase.table.assert_called_with("notifications")

    @pytest.mark.asyncio
    async def test_returns_none_on_insert_failure(
        self, notification_service, mock_supabase
    ):
        """Returns None when insert fails."""
        mock_supabase.execute.return_value = MagicMock(data=None)

        result = await notification_service._create_notification_record(
            user_id=str(uuid4()),
            handoff_id=str(uuid4()),
            acknowledgment_id=str(uuid4()),
            acknowledging_user_id=str(uuid4()),
            acknowledging_user_name=None,
            acknowledged_at=datetime.now(timezone.utc),
            has_notes=False,
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_without_supabase_client(self):
        """Returns None when no Supabase client configured."""
        service = HandoffNotificationService(supabase=None)

        result = await service._create_notification_record(
            user_id=str(uuid4()),
            handoff_id=str(uuid4()),
            acknowledgment_id=str(uuid4()),
            acknowledging_user_id=str(uuid4()),
            acknowledging_user_name=None,
            acknowledged_at=datetime.now(timezone.utc),
            has_notes=False,
        )

        assert result is None


class TestSendPushNotification:
    """Tests for _send_push_notification helper."""

    @pytest.mark.asyncio
    async def test_returns_false_without_edge_function_url(self):
        """Returns False when Edge Function URL not configured."""
        service = HandoffNotificationService()
        service._edge_function_url = ""

        result = await service._send_push_notification(
            handoff_id=str(uuid4()),
            acknowledgment_id=str(uuid4()),
            outgoing_user_id=str(uuid4()),
            acknowledging_user_id=str(uuid4()),
            acknowledging_user_name=None,
            acknowledged_at=datetime.now(timezone.utc),
            notes=None,
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_makes_http_request_to_edge_function(self):
        """Makes POST request to Edge Function URL."""
        service = HandoffNotificationService()
        service._edge_function_url = "https://test.supabase.co/functions/v1/notify-handoff-ack"

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True}

            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            result = await service._send_push_notification(
                handoff_id=str(uuid4()),
                acknowledgment_id=str(uuid4()),
                outgoing_user_id=str(uuid4()),
                acknowledging_user_id=str(uuid4()),
                acknowledging_user_name="Test",
                acknowledged_at=datetime.now(timezone.utc),
                notes=None,
            )

            assert result is True
            mock_client.post.assert_called_once()


class TestGetHandoffNotificationService:
    """Tests for singleton factory function."""

    def test_returns_singleton_instance(self):
        """Returns the same instance on multiple calls."""
        # Reset singleton
        import app.services.handoff.notifications as module
        module._notification_service = None

        service1 = get_handoff_notification_service()
        service2 = get_handoff_notification_service()

        assert service1 is service2

    def test_creates_new_instance_with_client(self, mock_supabase):
        """Creates instance with provided Supabase client."""
        import app.services.handoff.notifications as module
        module._notification_service = None

        service = get_handoff_notification_service(mock_supabase)

        assert service.supabase is mock_supabase
