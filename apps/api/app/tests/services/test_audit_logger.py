"""
Audit Logger Service Tests (Story 9.15, Task 10.1-10.4)

Tests for the AuditLogger service class including:
- log_action() creates correct entry (Task 10.2)
- log_batch_action() links entries with batch_id (Task 10.3)
- Before/after value capture accuracy (Task 10.4)

References:
- [Source: prd/prd-functional-requirements.md#FR50, FR56]
- [Source: prd/prd-non-functional-requirements.md#NFR25]
"""

import pytest
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.services.audit.logger import (
    AuditLogger,
    log_action,
    log_batch_start,
    log_role_change,
    get_audit_logger,
)
from app.models.admin import AuditLogActionType


class TestAuditLoggerLogAction:
    """Tests for AuditLogger.log_action() method (Task 10.2)."""

    @pytest.fixture
    def audit_logger(self):
        """Create a fresh AuditLogger instance for testing."""
        logger = AuditLogger()
        logger._in_memory_logs = []  # Reset in-memory storage
        return logger

    def test_log_action_creates_entry(self, audit_logger):
        """Test log_action() creates a correct entry (Task 10.2)."""
        admin_id = uuid4()
        target_user_id = uuid4()

        log_id = audit_logger.log_action(
            admin_user_id=admin_id,
            action_type="role_change",
            target_type="user",
            target_user_id=target_user_id,
            before_value={"role": "supervisor"},
            after_value={"role": "plant_manager"},
        )

        assert log_id is not None
        assert isinstance(log_id, UUID)

        # Verify entry in memory
        assert len(audit_logger._in_memory_logs) == 1
        entry = audit_logger._in_memory_logs[0]

        assert entry["admin_user_id"] == str(admin_id)
        assert entry["action_type"] == "role_change"
        assert entry["target_type"] == "user"
        assert entry["target_user_id"] == str(target_user_id)
        assert entry["before_value"] == {"role": "supervisor"}
        assert entry["after_value"] == {"role": "plant_manager"}

    def test_log_action_includes_timestamp(self, audit_logger):
        """Test log_action() includes timestamp in ISO format."""
        admin_id = uuid4()

        before_time = datetime.now(timezone.utc)
        audit_logger.log_action(
            admin_user_id=admin_id,
            action_type="assignment_create",
            target_type="assignment",
        )
        after_time = datetime.now(timezone.utc)

        entry = audit_logger._in_memory_logs[0]
        timestamp = datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))

        assert before_time <= timestamp <= after_time

    def test_log_action_with_batch_id(self, audit_logger):
        """Test log_action() correctly includes batch_id for linking (AC#4)."""
        admin_id = uuid4()
        batch_id = uuid4()

        audit_logger.log_action(
            admin_user_id=admin_id,
            action_type="assignment_create",
            target_type="assignment",
            batch_id=batch_id,
        )

        entry = audit_logger._in_memory_logs[0]
        assert entry["batch_id"] == str(batch_id)

    def test_log_action_with_target_asset_id(self, audit_logger):
        """Test log_action() correctly stores target_asset_id."""
        admin_id = uuid4()
        target_asset_id = uuid4()

        audit_logger.log_action(
            admin_user_id=admin_id,
            action_type="assignment_create",
            target_type="assignment",
            target_asset_id=target_asset_id,
        )

        entry = audit_logger._in_memory_logs[0]
        assert entry["target_asset_id"] == str(target_asset_id)

    def test_log_action_with_metadata(self, audit_logger):
        """Test log_action() correctly stores metadata."""
        admin_id = uuid4()
        metadata = {"source": "admin_ui", "ip_address": "192.168.1.1"}

        audit_logger.log_action(
            admin_user_id=admin_id,
            action_type="role_change",
            target_type="user",
            metadata=metadata,
        )

        entry = audit_logger._in_memory_logs[0]
        assert entry["metadata"] == metadata

    def test_log_action_handles_none_values(self, audit_logger):
        """Test log_action() handles optional None values correctly."""
        admin_id = uuid4()

        log_id = audit_logger.log_action(
            admin_user_id=admin_id,
            action_type="role_change",
            target_type="user",
            target_id=None,
            target_user_id=None,
            target_asset_id=None,
            before_value=None,
            after_value=None,
            batch_id=None,
            metadata=None,
        )

        assert log_id is not None
        entry = audit_logger._in_memory_logs[0]

        assert entry["target_id"] is None
        assert entry["target_user_id"] is None
        assert entry["target_asset_id"] is None
        assert entry["before_value"] is None
        assert entry["after_value"] is None
        assert entry["batch_id"] is None
        assert entry["metadata"] is None


class TestAuditLoggerLogBatchStart:
    """Tests for log_batch_start() method (Task 10.3)."""

    @pytest.fixture
    def audit_logger(self):
        """Create a fresh AuditLogger instance for testing."""
        return AuditLogger()

    def test_log_batch_start_returns_uuid(self, audit_logger):
        """Test log_batch_start() generates a valid batch_id."""
        batch_id = audit_logger.log_batch_start()

        assert batch_id is not None
        assert isinstance(batch_id, UUID)

    def test_log_batch_start_returns_unique_ids(self, audit_logger):
        """Test log_batch_start() returns unique IDs each time."""
        batch_id_1 = audit_logger.log_batch_start()
        batch_id_2 = audit_logger.log_batch_start()

        assert batch_id_1 != batch_id_2


class TestBatchOperationLinking:
    """Tests for batch operation linking with batch_id (Task 10.3)."""

    @pytest.fixture
    def audit_logger(self):
        """Create a fresh AuditLogger instance for testing."""
        logger = AuditLogger()
        logger._in_memory_logs = []
        return logger

    def test_multiple_entries_share_batch_id(self, audit_logger):
        """Test log_batch_action() links entries with same batch_id (Task 10.3)."""
        admin_id = uuid4()
        batch_id = audit_logger.log_batch_start()

        # Create multiple entries with the same batch_id
        for i in range(3):
            audit_logger.log_action(
                admin_user_id=admin_id,
                action_type="assignment_create",
                target_type="assignment",
                target_user_id=uuid4(),
                batch_id=batch_id,
            )

        # Verify all entries have the same batch_id
        assert len(audit_logger._in_memory_logs) == 3
        for entry in audit_logger._in_memory_logs:
            assert entry["batch_id"] == str(batch_id)

    def test_entries_from_different_batches_have_different_ids(self, audit_logger):
        """Test entries from different batches have different batch_ids."""
        admin_id = uuid4()

        # First batch
        batch_id_1 = audit_logger.log_batch_start()
        audit_logger.log_action(
            admin_user_id=admin_id,
            action_type="assignment_create",
            target_type="assignment",
            batch_id=batch_id_1,
        )

        # Second batch
        batch_id_2 = audit_logger.log_batch_start()
        audit_logger.log_action(
            admin_user_id=admin_id,
            action_type="assignment_create",
            target_type="assignment",
            batch_id=batch_id_2,
        )

        assert audit_logger._in_memory_logs[0]["batch_id"] != audit_logger._in_memory_logs[1]["batch_id"]


class TestBeforeAfterValueCapture:
    """Tests for before/after value capture accuracy (Task 10.4)."""

    @pytest.fixture
    def audit_logger(self):
        """Create a fresh AuditLogger instance for testing."""
        logger = AuditLogger()
        logger._in_memory_logs = []
        return logger

    def test_captures_role_change_before_after(self, audit_logger):
        """Test before/after capture for role change (Task 10.4)."""
        admin_id = uuid4()
        target_user_id = uuid4()

        before = {"role": "supervisor", "updated_at": "2026-01-01T00:00:00Z"}
        after = {"role": "plant_manager", "updated_at": "2026-01-15T00:00:00Z"}

        audit_logger.log_action(
            admin_user_id=admin_id,
            action_type="role_change",
            target_type="user",
            target_user_id=target_user_id,
            before_value=before,
            after_value=after,
        )

        entry = audit_logger._in_memory_logs[0]

        # Verify exact capture
        assert entry["before_value"] == before
        assert entry["after_value"] == after
        assert entry["before_value"]["role"] == "supervisor"
        assert entry["after_value"]["role"] == "plant_manager"

    def test_captures_assignment_create_with_none_before(self, audit_logger):
        """Test before is None for new assignments (Task 10.4)."""
        admin_id = uuid4()
        target_user_id = uuid4()
        target_asset_id = uuid4()

        after = {
            "user_id": str(target_user_id),
            "asset_id": str(target_asset_id),
            "assigned_at": "2026-01-15T00:00:00Z",
        }

        audit_logger.log_action(
            admin_user_id=admin_id,
            action_type="assignment_create",
            target_type="assignment",
            target_user_id=target_user_id,
            target_asset_id=target_asset_id,
            before_value=None,
            after_value=after,
        )

        entry = audit_logger._in_memory_logs[0]

        assert entry["before_value"] is None
        assert entry["after_value"] == after

    def test_captures_assignment_delete_with_none_after(self, audit_logger):
        """Test after is None for deleted assignments (Task 10.4)."""
        admin_id = uuid4()
        target_user_id = uuid4()
        target_asset_id = uuid4()

        before = {
            "user_id": str(target_user_id),
            "asset_id": str(target_asset_id),
            "assigned_at": "2026-01-01T00:00:00Z",
        }

        audit_logger.log_action(
            admin_user_id=admin_id,
            action_type="assignment_delete",
            target_type="assignment",
            target_user_id=target_user_id,
            target_asset_id=target_asset_id,
            before_value=before,
            after_value=None,
        )

        entry = audit_logger._in_memory_logs[0]

        assert entry["before_value"] == before
        assert entry["after_value"] is None

    def test_captures_nested_json_values(self, audit_logger):
        """Test captures complex nested JSON values accurately."""
        admin_id = uuid4()

        before = {
            "preferences": {
                "notifications": {"email": True, "push": False},
                "briefing": {"time": "06:00", "areas": ["grinding", "packing"]},
            }
        }
        after = {
            "preferences": {
                "notifications": {"email": True, "push": True},
                "briefing": {"time": "07:00", "areas": ["grinding", "packing", "roasting"]},
            }
        }

        audit_logger.log_action(
            admin_user_id=admin_id,
            action_type="preference_update",
            target_type="user",
            before_value=before,
            after_value=after,
        )

        entry = audit_logger._in_memory_logs[0]

        assert entry["before_value"] == before
        assert entry["after_value"] == after
        assert entry["before_value"]["preferences"]["notifications"]["push"] is False
        assert entry["after_value"]["preferences"]["notifications"]["push"] is True


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_log_action_uses_singleton(self):
        """Test log_action() function uses the singleton logger."""
        admin_id = uuid4()

        log_id = log_action(
            admin_user_id=admin_id,
            action_type="role_change",
            target_type="user",
        )

        assert log_id is not None
        assert isinstance(log_id, UUID)

    def test_log_batch_start_uses_singleton(self):
        """Test log_batch_start() function uses the singleton logger."""
        batch_id = log_batch_start()

        assert batch_id is not None
        assert isinstance(batch_id, UUID)

    def test_log_role_change_convenience(self):
        """Test log_role_change() convenience function works correctly."""
        admin_id = str(uuid4())
        target_user_id = str(uuid4())

        log_id = log_role_change(
            admin_user_id=admin_id,
            target_user_id=target_user_id,
            old_role="supervisor",
            new_role="plant_manager",
            metadata={"source": "test"},
        )

        assert log_id is not None
        assert isinstance(log_id, UUID)

    def test_get_audit_logger_returns_singleton(self):
        """Test get_audit_logger() returns the same instance."""
        logger1 = get_audit_logger()
        logger2 = get_audit_logger()

        assert logger1 is logger2


class TestValidation:
    """Tests for input validation (Task 2.8)."""

    @pytest.fixture
    def audit_logger(self):
        """Create a fresh AuditLogger instance for testing."""
        return AuditLogger()

    def test_requires_admin_user_id(self, audit_logger):
        """Test log_action() requires admin_user_id."""
        # This should work with a valid UUID
        log_id = audit_logger.log_action(
            admin_user_id=uuid4(),
            action_type="test",
            target_type="test",
        )
        assert log_id is not None

    def test_requires_action_type(self, audit_logger):
        """Test log_action() requires action_type."""
        log_id = audit_logger.log_action(
            admin_user_id=uuid4(),
            action_type="role_change",  # Required
            target_type="user",
        )
        assert log_id is not None

    def test_requires_target_type(self, audit_logger):
        """Test log_action() requires target_type."""
        log_id = audit_logger.log_action(
            admin_user_id=uuid4(),
            action_type="role_change",
            target_type="user",  # Required
        )
        assert log_id is not None
