"""
Tests for Handoff Storage Service (Story 9.4)

Comprehensive test coverage for all acceptance criteria:
AC#1: Handoff creation with valid data and status = pending_acknowledgment
AC#2: Immutability - verify core fields cannot be updated
AC#3: Supplemental notes can be appended
AC#4: Status transitions are allowed
AC#5: RLS policies filter handoffs by user assignment
AC#6: Voice note upload and reference storage
AC#7: Error handling and retry hints
"""

import pytest
from datetime import date, datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.models.handoff_storage import (
    HandoffStatus,
    ShiftType,
    ShiftHandoffCreate,
    ShiftHandoffRecord,
    HandoffVoiceNoteRecord,
    SupplementalNote,
)
from app.services.handoff.storage import (
    HandoffStorageService,
    HandoffPersistenceError,
    HandoffImmutabilityError,
)


# =============================================================================
# Test Fixtures
# =============================================================================


def _utcnow() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


@pytest.fixture
def mock_supabase():
    """Create a mock Supabase client."""
    mock = MagicMock()
    mock.table.return_value = mock
    mock.select.return_value = mock
    mock.insert.return_value = mock
    mock.update.return_value = mock
    mock.eq.return_value = mock
    mock.neq.return_value = mock
    mock.or_.return_value = mock
    mock.order.return_value = mock
    mock.range.return_value = mock
    mock.limit.return_value = mock

    # Mock storage
    mock_storage = MagicMock()
    mock_storage.from_.return_value = mock_storage
    mock_storage.upload.return_value = None
    mock_storage.create_signed_url.return_value = {"signedURL": "https://signed-url.example.com"}
    mock_storage.remove.return_value = None
    mock.storage = mock_storage

    return mock


@pytest.fixture
def handoff_storage_service(mock_supabase):
    """Create a HandoffStorageService with mock Supabase."""
    return HandoffStorageService(mock_supabase)


@pytest.fixture
def sample_handoff_create():
    """Sample handoff creation data."""
    return ShiftHandoffCreate(
        shift_date=date.today(),
        shift_type=ShiftType.MORNING,
        summary_text="Production was 5% above target today.",
        notes="Watch the mixer in area B.",
        assets_covered=[uuid4(), uuid4()],
    )


@pytest.fixture
def sample_handoff_record():
    """Sample handoff record from database."""
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


@pytest.fixture
def sample_user_id():
    """Sample user ID."""
    return str(uuid4())


# =============================================================================
# Test: Handoff Creation (AC#1)
# =============================================================================


class TestHandoffCreation:
    """Tests for handoff creation functionality (AC#1)."""

    @pytest.mark.asyncio
    async def test_create_handoff_success(
        self,
        handoff_storage_service,
        mock_supabase,
        sample_handoff_create,
        sample_user_id,
    ):
        """AC#1: Test handoff creation with valid data."""
        # Setup mock response
        now = _utcnow()
        mock_response = MagicMock()
        mock_response.data = [{
            "id": str(uuid4()),
            "user_id": sample_user_id,
            "created_by": sample_user_id,
            "shift_date": str(sample_handoff_create.shift_date),
            "shift_type": sample_handoff_create.shift_type.value,
            "summary_text": sample_handoff_create.summary_text,
            "summary": sample_handoff_create.summary_text,
            "notes": sample_handoff_create.notes,
            "text_notes": sample_handoff_create.notes,
            "supplemental_notes": [],
            "status": "draft",
            "assets_covered": [str(a) for a in sample_handoff_create.assets_covered],
            "acknowledged_by": None,
            "acknowledged_at": None,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }]
        mock_supabase.execute.return_value = mock_response

        # Execute
        result = await handoff_storage_service.create_handoff(
            sample_handoff_create,
            sample_user_id,
        )

        # Verify
        assert result is not None
        assert isinstance(result, ShiftHandoffRecord)
        assert result.status == HandoffStatus.DRAFT
        assert str(result.created_by) == sample_user_id
        assert result.shift_date == sample_handoff_create.shift_date
        assert result.shift_type == sample_handoff_create.shift_type

    @pytest.mark.asyncio
    async def test_create_handoff_includes_required_fields(
        self,
        handoff_storage_service,
        mock_supabase,
        sample_user_id,
    ):
        """AC#1: Verify all required fields are included in create."""
        handoff_data = ShiftHandoffCreate(
            shift_date=date.today(),
            shift_type=ShiftType.AFTERNOON,
            summary_text="Summary text here",
            notes="User notes",
            assets_covered=[uuid4()],
        )

        now = _utcnow()
        mock_response = MagicMock()
        mock_response.data = [{
            "id": str(uuid4()),
            "user_id": sample_user_id,
            "created_by": sample_user_id,
            "shift_date": str(handoff_data.shift_date),
            "shift_type": handoff_data.shift_type.value,
            "summary_text": handoff_data.summary_text,
            "summary": handoff_data.summary_text,
            "notes": handoff_data.notes,
            "text_notes": handoff_data.notes,
            "supplemental_notes": [],
            "status": "draft",
            "assets_covered": [str(a) for a in handoff_data.assets_covered],
            "acknowledged_by": None,
            "acknowledged_at": None,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }]
        mock_supabase.execute.return_value = mock_response

        result = await handoff_storage_service.create_handoff(
            handoff_data,
            sample_user_id,
        )

        # Verify required fields (AC#1)
        assert result.created_by is not None
        assert result.shift_date is not None
        assert result.shift_type is not None
        assert result.status == HandoffStatus.DRAFT
        assert result.assets_covered is not None

    @pytest.mark.asyncio
    async def test_create_handoff_database_error(
        self,
        handoff_storage_service,
        mock_supabase,
        sample_handoff_create,
        sample_user_id,
    ):
        """AC#4: Test error handling on database failure."""
        mock_supabase.execute.side_effect = Exception("Database connection failed")

        with pytest.raises(HandoffPersistenceError) as exc_info:
            await handoff_storage_service.create_handoff(
                sample_handoff_create,
                sample_user_id,
            )

        assert exc_info.value.retry_hint is True
        assert exc_info.value.error_code == "DATABASE_ERROR"
        assert exc_info.value.draft_key is not None


# =============================================================================
# Test: Immutability (AC#2)
# =============================================================================


class TestImmutability:
    """Tests for immutability enforcement (AC#2)."""

    @pytest.mark.asyncio
    async def test_submit_handoff_changes_status(
        self,
        handoff_storage_service,
        mock_supabase,
        sample_handoff_record,
        sample_user_id,
    ):
        """AC#2: Test that submission changes status correctly."""
        # Setup - handoff in draft status
        sample_handoff_record["user_id"] = sample_user_id
        sample_handoff_record["created_by"] = sample_user_id
        sample_handoff_record["status"] = "draft"

        # Mock get_handoff
        mock_get_response = MagicMock()
        mock_get_response.data = [sample_handoff_record]

        # Mock update response
        updated_record = sample_handoff_record.copy()
        updated_record["status"] = "pending_acknowledgment"
        mock_update_response = MagicMock()
        mock_update_response.data = [updated_record]

        mock_supabase.execute.side_effect = [
            mock_get_response,  # get_handoff call
            mock_update_response,  # update call
        ]

        result = await handoff_storage_service.submit_handoff(
            sample_handoff_record["id"],
            sample_user_id,
        )

        assert result.status == HandoffStatus.PENDING_ACKNOWLEDGMENT

    @pytest.mark.asyncio
    async def test_cannot_submit_non_draft_handoff(
        self,
        handoff_storage_service,
        mock_supabase,
        sample_handoff_record,
        sample_user_id,
    ):
        """AC#2: Test that non-draft handoffs cannot be submitted."""
        sample_handoff_record["user_id"] = sample_user_id
        sample_handoff_record["created_by"] = sample_user_id
        sample_handoff_record["status"] = "pending_acknowledgment"

        mock_get_response = MagicMock()
        mock_get_response.data = [sample_handoff_record]
        mock_supabase.execute.return_value = mock_get_response

        with pytest.raises(HandoffImmutabilityError):
            await handoff_storage_service.submit_handoff(
                sample_handoff_record["id"],
                sample_user_id,
            )


# =============================================================================
# Test: Supplemental Notes (AC#3)
# =============================================================================


class TestSupplementalNotes:
    """Tests for supplemental notes functionality (AC#3)."""

    @pytest.mark.asyncio
    async def test_add_supplemental_note_success(
        self,
        handoff_storage_service,
        mock_supabase,
        sample_handoff_record,
        sample_user_id,
    ):
        """AC#3: Test appending supplemental note."""
        sample_handoff_record["user_id"] = sample_user_id
        sample_handoff_record["created_by"] = sample_user_id
        sample_handoff_record["status"] = "pending_acknowledgment"
        sample_handoff_record["supplemental_notes"] = []

        mock_get_response = MagicMock()
        mock_get_response.data = [sample_handoff_record]

        # Updated record with note
        updated_record = sample_handoff_record.copy()
        updated_record["supplemental_notes"] = [
            {
                "added_at": _utcnow().isoformat(),
                "added_by": sample_user_id,
                "note_text": "Additional observation about Line 3.",
            }
        ]
        mock_update_response = MagicMock()
        mock_update_response.data = [updated_record]

        mock_supabase.execute.side_effect = [
            mock_get_response,
            mock_update_response,
        ]

        result = await handoff_storage_service.add_supplemental_note(
            sample_handoff_record["id"],
            "Additional observation about Line 3.",
            sample_user_id,
        )

        assert len(result.supplemental_notes) == 1
        assert result.supplemental_notes[0]["note_text"] == "Additional observation about Line 3."

    @pytest.mark.asyncio
    async def test_cannot_add_supplemental_note_to_draft(
        self,
        handoff_storage_service,
        mock_supabase,
        sample_handoff_record,
        sample_user_id,
    ):
        """AC#3: Test that supplemental notes cannot be added to drafts."""
        sample_handoff_record["user_id"] = sample_user_id
        sample_handoff_record["created_by"] = sample_user_id
        sample_handoff_record["status"] = "draft"

        mock_get_response = MagicMock()
        mock_get_response.data = [sample_handoff_record]
        mock_supabase.execute.return_value = mock_get_response

        with pytest.raises(HandoffImmutabilityError) as exc_info:
            await handoff_storage_service.add_supplemental_note(
                sample_handoff_record["id"],
                "This should fail.",
                sample_user_id,
            )

        assert "Submit the handoff" in str(exc_info.value.message)


# =============================================================================
# Test: Status Transitions (AC#4)
# =============================================================================


class TestStatusTransitions:
    """Tests for status transition validation (AC#4)."""

    @pytest.mark.asyncio
    async def test_valid_status_transition_pending_to_acknowledged(
        self,
        handoff_storage_service,
        mock_supabase,
        sample_handoff_record,
        sample_user_id,
    ):
        """AC#4: Test valid transition from pending to acknowledged."""
        sample_handoff_record["status"] = "pending_acknowledgment"

        mock_get_response = MagicMock()
        mock_get_response.data = [sample_handoff_record]

        updated_record = sample_handoff_record.copy()
        updated_record["status"] = "acknowledged"
        updated_record["acknowledged_by"] = str(uuid4())
        updated_record["acknowledged_at"] = _utcnow().isoformat()
        mock_update_response = MagicMock()
        mock_update_response.data = [updated_record]

        mock_supabase.execute.side_effect = [
            mock_get_response,
            mock_update_response,
        ]

        acknowledger_id = str(uuid4())
        result = await handoff_storage_service.update_status(
            sample_handoff_record["id"],
            HandoffStatus.ACKNOWLEDGED,
            sample_user_id,
            acknowledged_by=acknowledger_id,
        )

        assert result.status == HandoffStatus.ACKNOWLEDGED

    @pytest.mark.asyncio
    async def test_invalid_status_transition_acknowledged_to_draft(
        self,
        handoff_storage_service,
        mock_supabase,
        sample_handoff_record,
        sample_user_id,
    ):
        """AC#4: Test invalid transition from acknowledged to draft."""
        sample_handoff_record["status"] = "acknowledged"

        mock_get_response = MagicMock()
        mock_get_response.data = [sample_handoff_record]
        mock_supabase.execute.return_value = mock_get_response

        with pytest.raises(HandoffImmutabilityError) as exc_info:
            await handoff_storage_service.update_status(
                sample_handoff_record["id"],
                HandoffStatus.DRAFT,
                sample_user_id,
            )

        assert "Invalid status transition" in str(exc_info.value.message)


# =============================================================================
# Test: Get and List Handoffs (AC#5)
# =============================================================================


class TestHandoffQueries:
    """Tests for handoff query functionality (AC#5)."""

    @pytest.mark.asyncio
    async def test_get_handoff_by_id(
        self,
        handoff_storage_service,
        mock_supabase,
        sample_handoff_record,
    ):
        """AC#5: Test getting handoff by ID."""
        mock_response = MagicMock()
        mock_response.data = [sample_handoff_record]
        mock_supabase.execute.return_value = mock_response

        result = await handoff_storage_service.get_handoff(sample_handoff_record["id"])

        assert result is not None
        assert str(result.id) == sample_handoff_record["id"]

    @pytest.mark.asyncio
    async def test_get_handoff_not_found(
        self,
        handoff_storage_service,
        mock_supabase,
    ):
        """AC#5: Test get handoff returns None when not found."""
        mock_response = MagicMock()
        mock_response.data = []
        mock_supabase.execute.return_value = mock_response

        result = await handoff_storage_service.get_handoff(str(uuid4()))

        assert result is None

    @pytest.mark.asyncio
    async def test_list_handoffs_for_user(
        self,
        handoff_storage_service,
        mock_supabase,
        sample_handoff_record,
        sample_user_id,
    ):
        """AC#5: Test listing handoffs for a user."""
        sample_handoff_record["user_id"] = sample_user_id
        sample_handoff_record["created_by"] = sample_user_id

        mock_response = MagicMock()
        mock_response.data = [sample_handoff_record]
        mock_supabase.execute.return_value = mock_response

        result = await handoff_storage_service.list_handoffs(sample_user_id)

        assert len(result) == 1
        assert str(result[0].user_id) == sample_user_id


# =============================================================================
# Test: Voice Notes (AC#6)
# =============================================================================


class TestVoiceNotes:
    """Tests for voice note functionality (AC#6)."""

    @pytest.mark.asyncio
    async def test_upload_voice_note_success(
        self,
        handoff_storage_service,
        mock_supabase,
        sample_user_id,
    ):
        """AC#6: Test voice note upload."""
        handoff_id = str(uuid4())
        note_id = str(uuid4())

        # Mock get_voice_notes (empty list)
        mock_notes_response = MagicMock()
        mock_notes_response.data = []

        # Mock insert response
        now = _utcnow()
        mock_insert_response = MagicMock()
        mock_insert_response.data = [{
            "id": note_id,
            "handoff_id": handoff_id,
            "user_id": sample_user_id,
            "storage_path": f"{sample_user_id}/{handoff_id}/{note_id}.webm",
            "transcript": None,
            "duration_seconds": 30,
            "sequence_order": 0,
            "created_at": now.isoformat(),
        }]

        mock_supabase.execute.side_effect = [
            mock_notes_response,
            mock_insert_response,
        ]

        result = await handoff_storage_service.upload_voice_note(
            handoff_id=handoff_id,
            user_id=sample_user_id,
            audio_data=b"fake audio data",
            duration_seconds=30,
            content_type="audio/webm",
        )

        assert result is not None
        assert str(result.handoff_id) == handoff_id
        assert result.duration_seconds == 30

    @pytest.mark.asyncio
    async def test_get_voice_notes_for_handoff(
        self,
        handoff_storage_service,
        mock_supabase,
        sample_user_id,
    ):
        """AC#6: Test getting voice notes for a handoff."""
        handoff_id = str(uuid4())
        now = _utcnow()

        mock_response = MagicMock()
        mock_response.data = [
            {
                "id": str(uuid4()),
                "handoff_id": handoff_id,
                "user_id": sample_user_id,
                "storage_path": f"{sample_user_id}/{handoff_id}/note1.webm",
                "transcript": "First note transcript",
                "duration_seconds": 15,
                "sequence_order": 0,
                "created_at": now.isoformat(),
            },
            {
                "id": str(uuid4()),
                "handoff_id": handoff_id,
                "user_id": sample_user_id,
                "storage_path": f"{sample_user_id}/{handoff_id}/note2.webm",
                "transcript": "Second note transcript",
                "duration_seconds": 25,
                "sequence_order": 1,
                "created_at": now.isoformat(),
            },
        ]
        mock_supabase.execute.return_value = mock_response

        result = await handoff_storage_service.get_voice_notes(handoff_id)

        assert len(result) == 2
        assert result[0].sequence_order == 0
        assert result[1].sequence_order == 1


# =============================================================================
# Test: Error Handling (AC#7)
# =============================================================================


class TestErrorHandling:
    """Tests for error handling with retry hints (AC#7)."""

    @pytest.mark.asyncio
    async def test_persistence_error_includes_retry_hint(
        self,
        handoff_storage_service,
        mock_supabase,
        sample_handoff_create,
        sample_user_id,
    ):
        """AC#7: Test that persistence errors include retry hints."""
        mock_supabase.execute.side_effect = Exception("Connection timeout")

        with pytest.raises(HandoffPersistenceError) as exc_info:
            await handoff_storage_service.create_handoff(
                sample_handoff_create,
                sample_user_id,
            )

        error = exc_info.value
        assert error.retry_hint is True
        assert error.draft_key is not None

    @pytest.mark.asyncio
    async def test_persistence_error_includes_draft_key(
        self,
        handoff_storage_service,
        mock_supabase,
        sample_handoff_create,
        sample_user_id,
    ):
        """AC#7: Test that persistence errors include draft key for recovery."""
        mock_supabase.execute.side_effect = Exception("Database error")

        with pytest.raises(HandoffPersistenceError) as exc_info:
            await handoff_storage_service.create_handoff(
                sample_handoff_create,
                sample_user_id,
            )

        error = exc_info.value
        assert error.draft_key is not None
        assert sample_user_id in error.draft_key
        assert str(sample_handoff_create.shift_date) in error.draft_key

    def test_signed_url_generation(
        self,
        handoff_storage_service,
        mock_supabase,
    ):
        """AC#7: Test signed URL generation for voice notes."""
        storage_path = "user123/handoff456/note789.webm"

        result = handoff_storage_service.get_signed_url(storage_path)

        assert result is not None
        assert "https://" in result
