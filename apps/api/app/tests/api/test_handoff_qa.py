"""
Tests for Handoff Q&A API Endpoints (Story 9.6)

Tests the Q&A API endpoints for shift handoffs.

AC#1: POST /handoff/{id}/qa - Submit Q&A question
AC#2: Response includes citations
AC#3: POST /handoff/{id}/qa/respond - Human response
AC#4: GET /handoff/{id}/qa - Get Q&A thread

References:
- [Source: apps/api/app/api/handoff.py]
"""

import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from app.main import app
from app.models.handoff import (
    HandoffQAContentType,
    HandoffQAEntry,
    HandoffQAResponse,
    HandoffQAThread,
    HandoffQACitation,
)


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def sample_handoff_id():
    """Generate a sample handoff ID."""
    return str(uuid.uuid4())


@pytest.fixture
def sample_user_id():
    """Generate a sample user ID."""
    return str(uuid.uuid4())


@pytest.fixture
def mock_current_user(sample_user_id):
    """Mock the current user dependency."""
    user = MagicMock()
    user.id = sample_user_id
    user.name = "Test User"
    return user


@pytest.fixture
def mock_handoff(sample_handoff_id, sample_user_id):
    """Create a mock handoff record."""
    return {
        "id": sample_handoff_id,
        "user_id": sample_user_id,
        "created_by": sample_user_id,
        "shift_date": "2026-01-16",
        "shift_type": "morning",
        "summary": "Production was on target. No major issues.",
        "text_notes": "Watch Line 3 temperature.",
        "assets_covered": [str(uuid.uuid4())],
        "status": "pending_acknowledgment",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def mock_qa_response(sample_handoff_id, sample_user_id):
    """Create a mock Q&A response."""
    now = datetime.now(timezone.utc)
    question_entry = HandoffQAEntry(
        id=uuid.uuid4(),
        handoff_id=uuid.UUID(sample_handoff_id),
        user_id=uuid.UUID(sample_user_id),
        user_name="Test User",
        content_type=HandoffQAContentType.QUESTION,
        content="Why was there downtime?",
        citations=[],
        created_at=now,
    )

    answer_entry = HandoffQAEntry(
        id=uuid.uuid4(),
        handoff_id=uuid.UUID(sample_handoff_id),
        user_id=uuid.UUID(sample_user_id),
        user_name="AI Assistant",
        content_type=HandoffQAContentType.AI_ANSWER,
        content="The downtime was due to scheduled maintenance.",
        citations=[
            HandoffQACitation(
                value="2.5 hours",
                field="downtime_analysis",
                table="daily_summaries",
                context="Grinder 5 maintenance",
                timestamp=now,
            )
        ],
        created_at=now,
    )

    return HandoffQAResponse(
        entry=answer_entry,
        question_entry=question_entry,
        thread_count=2,
        message="Question processed successfully",
    )


class TestSubmitQAQuestion:
    """Tests for POST /handoff/{id}/qa endpoint."""

    def test_submit_question_returns_response(
        self,
        client: TestClient,
        sample_handoff_id: str,
        mock_current_user,
        mock_handoff,
        mock_qa_response,
    ):
        """Test that submitting a question returns a response with answer."""
        with patch('app.api.handoff.get_current_user', return_value=mock_current_user), \
             patch('app.api.handoff._get_handoff_by_id', return_value=mock_handoff), \
             patch('app.api.handoff._get_voice_notes_for_handoff', return_value=[]), \
             patch('app.api.handoff.get_handoff_qa_service') as mock_service:

            mock_service.return_value.process_question = AsyncMock(
                return_value=mock_qa_response
            )

            response = client.post(
                f"/api/v1/handoff/{sample_handoff_id}/qa",
                json={"question": "Why was there downtime?"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "entry" in data
            assert "question_entry" in data
            assert data["thread_count"] == 2

    def test_submit_question_with_voice_transcript(
        self,
        client: TestClient,
        sample_handoff_id: str,
        mock_current_user,
        mock_handoff,
        mock_qa_response,
    ):
        """Test submitting question with voice transcript."""
        with patch('app.api.handoff.get_current_user', return_value=mock_current_user), \
             patch('app.api.handoff._get_handoff_by_id', return_value=mock_handoff), \
             patch('app.api.handoff._get_voice_notes_for_handoff', return_value=[]), \
             patch('app.api.handoff.get_handoff_qa_service') as mock_service:

            mock_service.return_value.process_question = AsyncMock(
                return_value=mock_qa_response
            )

            response = client.post(
                f"/api/v1/handoff/{sample_handoff_id}/qa",
                json={
                    "question": "Why was there downtime?",
                    "voice_transcript": "why was their downtime",
                },
            )

            assert response.status_code == 200
            # Verify voice_transcript was passed to service
            mock_service.return_value.process_question.assert_called_once()
            call_kwargs = mock_service.return_value.process_question.call_args.kwargs
            assert call_kwargs.get("voice_transcript") == "why was their downtime"

    def test_submit_question_handoff_not_found(
        self,
        client: TestClient,
        sample_handoff_id: str,
        mock_current_user,
    ):
        """Test 404 when handoff doesn't exist."""
        with patch('app.api.handoff.get_current_user', return_value=mock_current_user), \
             patch('app.api.handoff._get_handoff_by_id', return_value=None):

            response = client.post(
                f"/api/v1/handoff/{sample_handoff_id}/qa",
                json={"question": "Test question?"},
            )

            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

    def test_submit_question_unauthorized(
        self,
        client: TestClient,
        sample_handoff_id: str,
        mock_current_user,
    ):
        """Test 403 when user doesn't have access to handoff."""
        # Handoff created by different user
        different_user = str(uuid.uuid4())
        mock_handoff = {
            "user_id": different_user,
            "created_by": different_user,
            "assets_covered": [str(uuid.uuid4())],  # User not assigned to these
        }

        with patch('app.api.handoff.get_current_user', return_value=mock_current_user), \
             patch('app.api.handoff._get_handoff_by_id', return_value=mock_handoff), \
             patch('app.api.handoff._get_supervisor_assignments', return_value=[]):

            response = client.post(
                f"/api/v1/handoff/{sample_handoff_id}/qa",
                json={"question": "Test question?"},
            )

            assert response.status_code == 403


class TestGetQAThread:
    """Tests for GET /handoff/{id}/qa endpoint."""

    def test_get_thread_returns_entries(
        self,
        client: TestClient,
        sample_handoff_id: str,
        mock_current_user,
        mock_handoff,
    ):
        """Test that get thread returns all Q&A entries."""
        now = datetime.now(timezone.utc)
        mock_thread = HandoffQAThread(
            handoff_id=uuid.UUID(sample_handoff_id),
            entries=[
                HandoffQAEntry(
                    id=uuid.uuid4(),
                    handoff_id=uuid.UUID(sample_handoff_id),
                    user_id=uuid.UUID(mock_current_user.id),
                    content_type=HandoffQAContentType.QUESTION,
                    content="Question 1",
                    citations=[],
                    created_at=now,
                ),
                HandoffQAEntry(
                    id=uuid.uuid4(),
                    handoff_id=uuid.UUID(sample_handoff_id),
                    user_id=uuid.UUID(mock_current_user.id),
                    user_name="AI Assistant",
                    content_type=HandoffQAContentType.AI_ANSWER,
                    content="Answer 1",
                    citations=[],
                    created_at=now,
                ),
            ],
            count=2,
        )

        with patch('app.api.handoff.get_current_user', return_value=mock_current_user), \
             patch('app.api.handoff._get_handoff_by_id', return_value=mock_handoff), \
             patch('app.api.handoff.get_handoff_qa_service') as mock_service:

            mock_service.return_value.get_thread.return_value = mock_thread

            response = client.get(f"/api/v1/handoff/{sample_handoff_id}/qa")

            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 2
            assert len(data["entries"]) == 2

    def test_get_thread_empty(
        self,
        client: TestClient,
        sample_handoff_id: str,
        mock_current_user,
        mock_handoff,
    ):
        """Test get thread when no Q&A entries exist."""
        mock_thread = HandoffQAThread(
            handoff_id=uuid.UUID(sample_handoff_id),
            entries=[],
            count=0,
        )

        with patch('app.api.handoff.get_current_user', return_value=mock_current_user), \
             patch('app.api.handoff._get_handoff_by_id', return_value=mock_handoff), \
             patch('app.api.handoff.get_handoff_qa_service') as mock_service:

            mock_service.return_value.get_thread.return_value = mock_thread

            response = client.get(f"/api/v1/handoff/{sample_handoff_id}/qa")

            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 0
            assert data["entries"] == []

    def test_get_thread_handoff_not_found(
        self,
        client: TestClient,
        sample_handoff_id: str,
        mock_current_user,
    ):
        """Test 404 when handoff doesn't exist."""
        with patch('app.api.handoff.get_current_user', return_value=mock_current_user), \
             patch('app.api.handoff._get_handoff_by_id', return_value=None):

            response = client.get(f"/api/v1/handoff/{sample_handoff_id}/qa")

            assert response.status_code == 404


class TestSubmitHumanResponse:
    """Tests for POST /handoff/{id}/qa/respond endpoint."""

    def test_submit_human_response_by_creator(
        self,
        client: TestClient,
        sample_handoff_id: str,
        mock_current_user,
        mock_handoff,
    ):
        """Test that handoff creator can submit human response (AC#3)."""
        now = datetime.now(timezone.utc)
        mock_entry = HandoffQAEntry(
            id=uuid.uuid4(),
            handoff_id=uuid.UUID(sample_handoff_id),
            user_id=uuid.UUID(mock_current_user.id),
            user_name="Test User",
            content_type=HandoffQAContentType.HUMAN_RESPONSE,
            content="I fixed it manually.",
            citations=[],
            created_at=now,
        )

        with patch('app.api.handoff.get_current_user', return_value=mock_current_user), \
             patch('app.api.handoff._get_handoff_by_id', return_value=mock_handoff), \
             patch('app.api.handoff.get_handoff_qa_service') as mock_service:

            mock_service.return_value.add_human_response = AsyncMock(
                return_value=mock_entry
            )

            response = client.post(
                f"/api/v1/handoff/{sample_handoff_id}/qa/respond",
                json={"response": "I fixed it manually."},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["content"] == "I fixed it manually."
            assert data["content_type"] == "human_response"

    def test_submit_human_response_by_non_creator_fails(
        self,
        client: TestClient,
        sample_handoff_id: str,
        mock_current_user,
    ):
        """Test that non-creator cannot submit human response."""
        # Handoff created by different user
        different_user = str(uuid.uuid4())
        mock_handoff = {
            "user_id": different_user,
            "created_by": different_user,
        }

        with patch('app.api.handoff.get_current_user', return_value=mock_current_user), \
             patch('app.api.handoff._get_handoff_by_id', return_value=mock_handoff):

            response = client.post(
                f"/api/v1/handoff/{sample_handoff_id}/qa/respond",
                json={"response": "My response"},
            )

            assert response.status_code == 403
            assert "creator" in response.json()["detail"].lower()

    def test_submit_human_response_with_question_id(
        self,
        client: TestClient,
        sample_handoff_id: str,
        mock_current_user,
        mock_handoff,
    ):
        """Test submitting human response linked to specific question."""
        question_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        mock_entry = HandoffQAEntry(
            id=uuid.uuid4(),
            handoff_id=uuid.UUID(sample_handoff_id),
            user_id=uuid.UUID(mock_current_user.id),
            content_type=HandoffQAContentType.HUMAN_RESPONSE,
            content="Response to specific question",
            citations=[],
            created_at=now,
        )

        with patch('app.api.handoff.get_current_user', return_value=mock_current_user), \
             patch('app.api.handoff._get_handoff_by_id', return_value=mock_handoff), \
             patch('app.api.handoff.get_handoff_qa_service') as mock_service:

            mock_service.return_value.add_human_response = AsyncMock(
                return_value=mock_entry
            )

            response = client.post(
                f"/api/v1/handoff/{sample_handoff_id}/qa/respond",
                json={
                    "response": "Response to specific question",
                    "question_entry_id": question_id,
                },
            )

            assert response.status_code == 200
            # Verify question_entry_id was passed
            call_kwargs = mock_service.return_value.add_human_response.call_args.kwargs
            assert call_kwargs.get("question_entry_id") == question_id


class TestQAEndpointValidation:
    """Tests for request validation."""

    def test_submit_question_empty_question_fails(
        self,
        client: TestClient,
        sample_handoff_id: str,
        mock_current_user,
        mock_handoff,
    ):
        """Test that empty question is rejected."""
        with patch('app.api.handoff.get_current_user', return_value=mock_current_user), \
             patch('app.api.handoff._get_handoff_by_id', return_value=mock_handoff):

            response = client.post(
                f"/api/v1/handoff/{sample_handoff_id}/qa",
                json={"question": ""},
            )

            assert response.status_code == 422  # Validation error

    def test_submit_response_empty_response_fails(
        self,
        client: TestClient,
        sample_handoff_id: str,
        mock_current_user,
        mock_handoff,
    ):
        """Test that empty response is rejected."""
        with patch('app.api.handoff.get_current_user', return_value=mock_current_user), \
             patch('app.api.handoff._get_handoff_by_id', return_value=mock_handoff):

            response = client.post(
                f"/api/v1/handoff/{sample_handoff_id}/qa/respond",
                json={"response": ""},
            )

            assert response.status_code == 422  # Validation error
