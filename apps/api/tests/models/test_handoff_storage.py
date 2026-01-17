"""
Tests for Handoff Storage Models (Story 9.4)

Tests for the Pydantic models used by the storage service.

AC#1: ShiftHandoffRecord with all required fields
AC#2: Validators for immutable field protection
AC#3: HandoffVoiceNoteRecord for voice note references
AC#4: HandoffStatus enum with all valid states
"""

import pytest
from datetime import date, datetime, timezone
from uuid import uuid4

from app.models.handoff_storage import (
    HandoffStatus,
    ShiftType,
    ShiftHandoffCreate,
    ShiftHandoffRecord,
    HandoffVoiceNoteRecord,
    SupplementalNote,
    HandoffPersistenceErrorResponse,
)


# =============================================================================
# Test Fixtures
# =============================================================================


def _utcnow() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


@pytest.fixture
def sample_record_data():
    """Sample data for ShiftHandoffRecord."""
    now = _utcnow()
    handoff_id = uuid4()
    user_id = uuid4()

    return {
        "id": str(handoff_id),
        "user_id": str(user_id),
        "created_by": str(user_id),
        "shift_date": str(date.today()),
        "shift_type": "morning",
        "summary_text": "Production was 5% above target.",
        "summary": "Production was 5% above target.",
        "notes": "Watch the mixer.",
        "text_notes": "Watch the mixer.",
        "supplemental_notes": [],
        "status": "draft",
        "assets_covered": [str(uuid4()), str(uuid4())],
        "acknowledged_by": None,
        "acknowledged_at": None,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }


# =============================================================================
# Test: HandoffStatus Enum (AC#4)
# =============================================================================


class TestHandoffStatus:
    """Tests for HandoffStatus enum (AC#4)."""

    def test_all_status_values_exist(self):
        """AC#4: Verify all required status values exist."""
        assert HandoffStatus.DRAFT.value == "draft"
        assert HandoffStatus.PENDING_ACKNOWLEDGMENT.value == "pending_acknowledgment"
        assert HandoffStatus.ACKNOWLEDGED.value == "acknowledged"
        assert HandoffStatus.EXPIRED.value == "expired"

    def test_status_from_string(self):
        """AC#4: Test status parsing from string."""
        assert HandoffStatus("draft") == HandoffStatus.DRAFT
        assert HandoffStatus("pending_acknowledgment") == HandoffStatus.PENDING_ACKNOWLEDGMENT
        assert HandoffStatus("acknowledged") == HandoffStatus.ACKNOWLEDGED
        assert HandoffStatus("expired") == HandoffStatus.EXPIRED


# =============================================================================
# Test: ShiftType Enum
# =============================================================================


class TestShiftType:
    """Tests for ShiftType enum."""

    def test_all_shift_types_exist(self):
        """Verify all shift type values exist."""
        assert ShiftType.MORNING.value == "morning"
        assert ShiftType.AFTERNOON.value == "afternoon"
        assert ShiftType.NIGHT.value == "night"
        assert ShiftType.DAY.value == "day"
        assert ShiftType.SWING.value == "swing"


# =============================================================================
# Test: ShiftHandoffCreate
# =============================================================================


class TestShiftHandoffCreate:
    """Tests for ShiftHandoffCreate model."""

    def test_create_with_required_fields(self):
        """Test creation with required fields only."""
        data = ShiftHandoffCreate(
            shift_date=date.today(),
            shift_type=ShiftType.MORNING,
            assets_covered=[uuid4()],
        )

        assert data.shift_date == date.today()
        assert data.shift_type == ShiftType.MORNING
        assert len(data.assets_covered) == 1
        assert data.summary_text is None
        assert data.notes is None

    def test_create_with_all_fields(self):
        """Test creation with all fields."""
        asset_ids = [uuid4(), uuid4()]
        data = ShiftHandoffCreate(
            shift_date=date.today(),
            shift_type=ShiftType.AFTERNOON,
            summary_text="Summary here",
            notes="Notes here",
            assets_covered=asset_ids,
        )

        assert data.summary_text == "Summary here"
        assert data.notes == "Notes here"
        assert len(data.assets_covered) == 2


# =============================================================================
# Test: ShiftHandoffRecord (AC#1, AC#2)
# =============================================================================


class TestShiftHandoffRecord:
    """Tests for ShiftHandoffRecord model (AC#1, AC#2)."""

    def test_parse_from_database_response(self, sample_record_data):
        """AC#1: Test parsing from database response."""
        record = ShiftHandoffRecord.model_validate(sample_record_data)

        assert record.id is not None
        assert record.created_by is not None
        assert record.shift_date == date.today()
        assert record.shift_type == ShiftType.MORNING
        assert record.status == HandoffStatus.DRAFT

    def test_assets_covered_parsing(self, sample_record_data):
        """AC#1: Test assets_covered parsing from string array."""
        record = ShiftHandoffRecord.model_validate(sample_record_data)

        assert len(record.assets_covered) == 2
        # Verify UUIDs are parsed correctly
        for asset_id in record.assets_covered:
            assert isinstance(asset_id, type(uuid4()))

    def test_supplemental_notes_parsing(self, sample_record_data):
        """AC#2: Test supplemental_notes JSONB parsing."""
        sample_record_data["supplemental_notes"] = [
            {
                "added_at": _utcnow().isoformat(),
                "added_by": str(uuid4()),
                "note_text": "First note",
            },
            {
                "added_at": _utcnow().isoformat(),
                "added_by": str(uuid4()),
                "note_text": "Second note",
            },
        ]

        record = ShiftHandoffRecord.model_validate(sample_record_data)

        assert len(record.supplemental_notes) == 2
        assert record.supplemental_notes[0]["note_text"] == "First note"

    def test_is_immutable_property(self, sample_record_data):
        """AC#2: Test is_immutable property."""
        # Draft is not immutable
        sample_record_data["status"] = "draft"
        record = ShiftHandoffRecord.model_validate(sample_record_data)
        assert record.is_immutable is False

        # Pending is immutable
        sample_record_data["status"] = "pending_acknowledgment"
        record = ShiftHandoffRecord.model_validate(sample_record_data)
        assert record.is_immutable is True

        # Acknowledged is immutable
        sample_record_data["status"] = "acknowledged"
        record = ShiftHandoffRecord.model_validate(sample_record_data)
        assert record.is_immutable is True

    def test_can_be_acknowledged_property(self, sample_record_data):
        """AC#2: Test can_be_acknowledged property."""
        # Draft cannot be acknowledged
        sample_record_data["status"] = "draft"
        record = ShiftHandoffRecord.model_validate(sample_record_data)
        assert record.can_be_acknowledged is False

        # Pending can be acknowledged
        sample_record_data["status"] = "pending_acknowledgment"
        record = ShiftHandoffRecord.model_validate(sample_record_data)
        assert record.can_be_acknowledged is True

        # Acknowledged cannot be acknowledged again
        sample_record_data["status"] = "acknowledged"
        record = ShiftHandoffRecord.model_validate(sample_record_data)
        assert record.can_be_acknowledged is False

    def test_backward_compatibility_fields(self, sample_record_data):
        """AC#1: Test backward compatibility field syncing."""
        # Test summary/summary_text sync
        sample_record_data["summary_text"] = "New summary"
        sample_record_data["summary"] = None

        record = ShiftHandoffRecord.model_validate(sample_record_data)
        assert record.summary_text == "New summary"
        assert record.summary == "New summary"

        # Test notes/text_notes sync
        sample_record_data["notes"] = "New notes"
        sample_record_data["text_notes"] = None

        record = ShiftHandoffRecord.model_validate(sample_record_data)
        assert record.notes == "New notes"
        assert record.text_notes == "New notes"


# =============================================================================
# Test: HandoffVoiceNoteRecord (AC#3)
# =============================================================================


class TestHandoffVoiceNoteRecord:
    """Tests for HandoffVoiceNoteRecord model (AC#3)."""

    def test_parse_voice_note_record(self):
        """AC#3: Test parsing voice note from database."""
        now = _utcnow()
        note_id = uuid4()
        handoff_id = uuid4()
        user_id = uuid4()

        data = {
            "id": str(note_id),
            "handoff_id": str(handoff_id),
            "user_id": str(user_id),
            "storage_path": f"{user_id}/{handoff_id}/{note_id}.webm",
            "transcript": "Transcribed text here",
            "duration_seconds": 45,
            "sequence_order": 0,
            "created_at": now.isoformat(),
        }

        record = HandoffVoiceNoteRecord.model_validate(data)

        assert str(record.id) == str(note_id)
        assert str(record.handoff_id) == str(handoff_id)
        assert record.duration_seconds == 45
        assert record.sequence_order == 0
        assert "webm" in record.storage_path

    def test_voice_note_duration_constraints(self):
        """AC#3: Test duration constraints (1-60 seconds)."""
        now = _utcnow()
        base_data = {
            "id": str(uuid4()),
            "handoff_id": str(uuid4()),
            "user_id": str(uuid4()),
            "storage_path": "path/to/file.webm",
            "duration_seconds": 30,
            "sequence_order": 0,
            "created_at": now.isoformat(),
        }

        # Valid duration
        record = HandoffVoiceNoteRecord.model_validate(base_data)
        assert record.duration_seconds == 30

        # Max duration (60)
        base_data["duration_seconds"] = 60
        record = HandoffVoiceNoteRecord.model_validate(base_data)
        assert record.duration_seconds == 60

        # Invalid duration (too long)
        base_data["duration_seconds"] = 61
        with pytest.raises(ValueError):
            HandoffVoiceNoteRecord.model_validate(base_data)

        # Invalid duration (too short)
        base_data["duration_seconds"] = 0
        with pytest.raises(ValueError):
            HandoffVoiceNoteRecord.model_validate(base_data)


# =============================================================================
# Test: SupplementalNote
# =============================================================================


class TestSupplementalNote:
    """Tests for SupplementalNote model."""

    def test_create_supplemental_note(self):
        """Test creating a supplemental note."""
        user_id = str(uuid4())
        note = SupplementalNote(
            added_by=user_id,
            note_text="Additional observation about the mixer.",
        )

        assert note.added_by == user_id
        assert note.note_text == "Additional observation about the mixer."
        assert note.added_at is not None

    def test_note_text_constraints(self):
        """Test note text length constraints."""
        user_id = str(uuid4())

        # Valid note
        note = SupplementalNote(
            added_by=user_id,
            note_text="Valid note text",
        )
        assert len(note.note_text) > 0

        # Empty note should fail
        with pytest.raises(ValueError):
            SupplementalNote(
                added_by=user_id,
                note_text="",
            )


# =============================================================================
# Test: Error Response Model (AC#4)
# =============================================================================


class TestHandoffPersistenceErrorResponse:
    """Tests for error response model (AC#4)."""

    def test_error_response_with_retry_hint(self):
        """AC#4: Test error response with retry hint."""
        response = HandoffPersistenceErrorResponse(
            error="Database connection failed",
            code="DATABASE_ERROR",
            retry_hint=True,
            draft_key="draft_user123_2026-01-15_morning",
        )

        assert response.retry_hint is True
        assert response.draft_key is not None
        assert "draft_" in response.draft_key

    def test_error_response_without_retry(self):
        """AC#4: Test error response without retry hint."""
        response = HandoffPersistenceErrorResponse(
            error="Access denied",
            code="ACCESS_DENIED",
            retry_hint=False,
        )

        assert response.retry_hint is False
        assert response.draft_key is None
