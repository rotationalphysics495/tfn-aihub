"""
Tests for Handoff API Endpoints (Story 9.4)

Tests for the persistent handoff storage API endpoints:
- POST /api/v1/handoff/{id}/supplemental-note
- GET /api/v1/handoff/pending
- GET /api/v1/handoff/{id}/supplemental-notes

AC#1: Handoff persistence and pending list
AC#2: Supplemental notes (append-only)
AC#3: Voice file references
AC#4: Error handling with retry hints
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import patch, MagicMock

from fastapi import status


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def auth_headers():
    """Headers with mock authorization."""
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
def sample_handoff_id():
    """Generate a sample handoff ID."""
    return str(uuid4())


@pytest.fixture
def sample_user_id():
    """Sample user ID."""
    return "123e4567-e89b-12d3-a456-426614174000"


# =============================================================================
# Test: Supplemental Note Endpoints (AC#2)
# =============================================================================


class TestSupplementalNoteEndpoints:
    """Tests for supplemental note API endpoints (AC#2)."""

    def test_add_supplemental_note_success(
        self,
        client,
        mock_verify_jwt,
        sample_handoff_id,
        sample_user_id,
        auth_headers,
    ):
        """AC#2: Test adding a supplemental note to submitted handoff."""
        # First, create a handoff in the in-memory store
        from app.api.handoff import _handoffs, _save_handoff

        now = datetime.now(timezone.utc)
        handoff = {
            "id": sample_handoff_id,
            "user_id": sample_user_id,
            "shift_date": "2026-01-15",
            "shift_type": "morning",
            "status": "pending_acknowledgment",  # Must be submitted
            "assets_covered": [str(uuid4())],
            "summary": "Test summary",
            "text_notes": "Test notes",
            "supplemental_notes": [],
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        _save_handoff(handoff)

        # Add supplemental note
        response = client.post(
            f"/api/v1/handoff/{sample_handoff_id}/supplemental-note",
            json={"note_text": "Additional observation about Line 3."},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["note_count"] == 1
        assert data["handoff_id"] == sample_handoff_id

        # Clean up
        del _handoffs[sample_handoff_id]

    def test_add_supplemental_note_to_draft_fails(
        self,
        client,
        mock_verify_jwt,
        sample_handoff_id,
        sample_user_id,
        auth_headers,
    ):
        """AC#2: Test that supplemental notes cannot be added to drafts."""
        from app.api.handoff import _handoffs, _save_handoff

        now = datetime.now(timezone.utc)
        handoff = {
            "id": sample_handoff_id,
            "user_id": sample_user_id,
            "shift_date": "2026-01-15",
            "shift_type": "morning",
            "status": "draft",  # Still in draft
            "assets_covered": [str(uuid4())],
            "summary": None,
            "text_notes": None,
            "supplemental_notes": [],
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        _save_handoff(handoff)

        response = client.post(
            f"/api/v1/handoff/{sample_handoff_id}/supplemental-note",
            json={"note_text": "This should fail."},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "detail" in data
        assert data["detail"]["code"] == "INVALID_STATUS"

        # Clean up
        del _handoffs[sample_handoff_id]

    def test_add_supplemental_note_handoff_not_found(
        self,
        client,
        mock_verify_jwt,
        auth_headers,
    ):
        """AC#4: Test error response when handoff not found."""
        fake_id = str(uuid4())

        response = client.post(
            f"/api/v1/handoff/{fake_id}/supplemental-note",
            json={"note_text": "Test note"},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_supplemental_notes_success(
        self,
        client,
        mock_verify_jwt,
        sample_handoff_id,
        sample_user_id,
        auth_headers,
    ):
        """AC#2: Test getting supplemental notes for a handoff."""
        from app.api.handoff import _handoffs, _save_handoff

        now = datetime.now(timezone.utc)
        handoff = {
            "id": sample_handoff_id,
            "user_id": sample_user_id,
            "shift_date": "2026-01-15",
            "shift_type": "morning",
            "status": "pending_acknowledgment",
            "assets_covered": [str(uuid4())],
            "summary": "Test",
            "text_notes": None,
            "supplemental_notes": [
                {
                    "added_at": now.isoformat(),
                    "added_by": sample_user_id,
                    "note_text": "First note",
                },
                {
                    "added_at": now.isoformat(),
                    "added_by": sample_user_id,
                    "note_text": "Second note",
                },
            ],
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        _save_handoff(handoff)

        response = client.get(
            f"/api/v1/handoff/{sample_handoff_id}/supplemental-notes",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["count"] == 2
        assert len(data["notes"]) == 2

        # Clean up
        del _handoffs[sample_handoff_id]


# =============================================================================
# Test: Pending Handoffs Endpoint (AC#1)
# =============================================================================


class TestPendingHandoffsEndpoint:
    """Tests for pending handoffs listing (AC#1)."""

    def test_list_pending_handoffs_empty(
        self,
        client,
        mock_verify_jwt,
        auth_headers,
    ):
        """AC#1: Test empty pending list when no handoffs exist."""
        response = client.get(
            "/api/v1/handoff/pending",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["handoffs"] == []
        assert data["total_count"] == 0

    def test_list_pending_handoffs_filters_own_handoffs(
        self,
        client,
        mock_verify_jwt,
        sample_user_id,
        auth_headers,
    ):
        """AC#1: Test that user's own handoffs are filtered out."""
        from app.api.handoff import _handoffs, _save_handoff

        now = datetime.now(timezone.utc)

        # Create a handoff from the same user
        own_handoff_id = str(uuid4())
        own_handoff = {
            "id": own_handoff_id,
            "user_id": sample_user_id,
            "shift_date": "2026-01-15",
            "shift_type": "morning",
            "status": "pending_acknowledgment",
            "assets_covered": [str(uuid4())],
            "summary": "Own handoff",
            "text_notes": None,
            "supplemental_notes": [],
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        _save_handoff(own_handoff)

        response = client.get(
            "/api/v1/handoff/pending",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should not include user's own handoffs
        for handoff in data["handoffs"]:
            assert handoff["id"] != own_handoff_id

        # Clean up
        del _handoffs[own_handoff_id]


# =============================================================================
# Test: Error Handling (AC#4)
# =============================================================================


class TestErrorHandling:
    """Tests for error handling with retry hints (AC#4)."""

    def test_supplemental_note_access_denied(
        self,
        client,
        mock_verify_jwt,
        sample_user_id,
        auth_headers,
    ):
        """AC#4: Test access denied error includes correct code."""
        from app.api.handoff import _handoffs, _save_handoff

        now = datetime.now(timezone.utc)
        handoff_id = str(uuid4())
        other_user_id = str(uuid4())

        # Create handoff owned by another user
        handoff = {
            "id": handoff_id,
            "user_id": other_user_id,  # Different user
            "shift_date": "2026-01-15",
            "shift_type": "morning",
            "status": "pending_acknowledgment",
            "assets_covered": [str(uuid4())],
            "summary": "Other user handoff",
            "text_notes": None,
            "supplemental_notes": [],
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        _save_handoff(handoff)

        response = client.post(
            f"/api/v1/handoff/{handoff_id}/supplemental-note",
            json={"note_text": "Should fail"},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert data["detail"]["code"] == "ACCESS_DENIED"
        assert data["detail"]["retry_hint"] is False

        # Clean up
        del _handoffs[handoff_id]
