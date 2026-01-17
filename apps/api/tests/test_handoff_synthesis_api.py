"""
Integration Tests for Handoff Synthesis API (Story 9.2)

Tests for the /api/v1/handoff/synthesis endpoints.

AC#1: Tool Composition for Synthesis
AC#2: Narrative Summary Structure
AC#3: Graceful Degradation on Tool Failure
AC#4: Progressive Loading (15-second timeout)
AC#5: Supervisor Scope Filtering
AC#6: Citation Compliance
AC#7: Shift Time Range Detection
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from app.models.handoff import (
    HandoffSynthesisCitation,
    HandoffSynthesisMetadata,
    HandoffSynthesisResponse,
    HandoffSection,
    HandoffSectionStatus,
    ShiftTimeRange,
    ShiftType,
)


# =============================================================================
# Test Fixtures
# =============================================================================


def _utcnow() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


@pytest.fixture
def mock_synthesis_response():
    """Create mock synthesis response."""
    now = _utcnow()
    return HandoffSynthesisResponse(
        id=str(uuid4()),
        user_id="123e4567-e89b-12d3-a456-426614174000",
        shift_info=ShiftTimeRange(
            shift_type=ShiftType.MORNING,
            start_time=now,
            end_time=now,
            shift_date=now.date(),
        ),
        sections=[
            HandoffSection(
                section_type="overview",
                title="Shift Performance Overview",
                content="Production is running 5% ahead of target.",
                citations=[
                    HandoffSynthesisCitation(
                        source="supabase",
                        table="live_snapshots",
                        timestamp=now,
                    )
                ],
                status=HandoffSectionStatus.COMPLETE,
            ),
            HandoffSection(
                section_type="issues",
                title="Issues Encountered",
                content="No significant downtime recorded.",
                citations=[],
                status=HandoffSectionStatus.COMPLETE,
            ),
            HandoffSection(
                section_type="concerns",
                title="Ongoing Concerns",
                content="No safety incidents. No active alerts.",
                citations=[],
                status=HandoffSectionStatus.COMPLETE,
            ),
            HandoffSection(
                section_type="focus",
                title="Recommended Focus for Incoming Shift",
                content="Continue normal operations.",
                citations=[],
                status=HandoffSectionStatus.COMPLETE,
            ),
        ],
        citations=[
            HandoffSynthesisCitation(
                source="supabase",
                table="live_snapshots",
                timestamp=now,
            )
        ],
        total_sections=4,
        completed_sections=4,
        metadata=HandoffSynthesisMetadata(
            generated_at=now,
            generation_duration_ms=250,
            completion_percentage=100.0,
            timed_out=False,
            tool_failures=[],
        ),
    )


# =============================================================================
# Test: GET /api/v1/handoff/synthesis Endpoint
# =============================================================================


class TestSynthesisEndpoint:
    """Tests for the synthesis endpoint."""

    def test_synthesis_requires_authentication(self, client):
        """Synthesis endpoint requires authentication."""
        response = client.get("/api/v1/handoff/synthesis")
        # Should return 401 without auth
        assert response.status_code == 401

    def test_synthesis_returns_response_model(
        self,
        client,
        mock_verify_jwt,
        mock_synthesis_response,
    ):
        """Synthesis endpoint returns HandoffSynthesisResponse model."""
        with patch(
            "app.api.handoff._get_supervisor_assignments",
            return_value=[],
        ), patch(
            "app.api.handoff.get_handoff_synthesis_service"
        ) as mock_service:
            mock_instance = MagicMock()
            mock_instance.synthesize_shift_data = AsyncMock(
                return_value=mock_synthesis_response
            )
            mock_service.return_value = mock_instance

            response = client.get(
                "/api/v1/handoff/synthesis",
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200
            data = response.json()

            # Verify response structure
            assert "id" in data
            assert "sections" in data
            assert "shift_info" in data
            assert "citations" in data
            assert "metadata" in data

    def test_synthesis_includes_four_sections(
        self,
        client,
        mock_verify_jwt,
        mock_synthesis_response,
    ):
        """AC#2: Synthesis includes four narrative sections."""
        with patch(
            "app.api.handoff._get_supervisor_assignments",
            return_value=[],
        ), patch(
            "app.api.handoff.get_handoff_synthesis_service"
        ) as mock_service:
            mock_instance = MagicMock()
            mock_instance.synthesize_shift_data = AsyncMock(
                return_value=mock_synthesis_response
            )
            mock_service.return_value = mock_instance

            response = client.get(
                "/api/v1/handoff/synthesis",
                headers={"Authorization": "Bearer test-token"}
            )

            data = response.json()
            sections = data["sections"]

            assert len(sections) == 4

            section_types = [s["section_type"] for s in sections]
            assert "overview" in section_types
            assert "issues" in section_types
            assert "concerns" in section_types
            assert "focus" in section_types

    def test_synthesis_includes_shift_info(
        self,
        client,
        mock_verify_jwt,
        mock_synthesis_response,
    ):
        """AC#7: Synthesis includes shift time range."""
        with patch(
            "app.api.handoff._get_supervisor_assignments",
            return_value=[],
        ), patch(
            "app.api.handoff.get_handoff_synthesis_service"
        ) as mock_service:
            mock_instance = MagicMock()
            mock_instance.synthesize_shift_data = AsyncMock(
                return_value=mock_synthesis_response
            )
            mock_service.return_value = mock_instance

            response = client.get(
                "/api/v1/handoff/synthesis",
                headers={"Authorization": "Bearer test-token"}
            )

            data = response.json()
            shift_info = data["shift_info"]

            assert "shift_type" in shift_info
            assert "start_time" in shift_info
            assert "end_time" in shift_info

    def test_synthesis_includes_citations(
        self,
        client,
        mock_verify_jwt,
        mock_synthesis_response,
    ):
        """AC#6: Synthesis includes citations."""
        with patch(
            "app.api.handoff._get_supervisor_assignments",
            return_value=[],
        ), patch(
            "app.api.handoff.get_handoff_synthesis_service"
        ) as mock_service:
            mock_instance = MagicMock()
            mock_instance.synthesize_shift_data = AsyncMock(
                return_value=mock_synthesis_response
            )
            mock_service.return_value = mock_instance

            response = client.get(
                "/api/v1/handoff/synthesis",
                headers={"Authorization": "Bearer test-token"}
            )

            data = response.json()

            assert len(data["citations"]) > 0
            citation = data["citations"][0]
            assert "source" in citation
            assert "timestamp" in citation

    def test_synthesis_includes_metadata(
        self,
        client,
        mock_verify_jwt,
        mock_synthesis_response,
    ):
        """Synthesis includes generation metadata."""
        with patch(
            "app.api.handoff._get_supervisor_assignments",
            return_value=[],
        ), patch(
            "app.api.handoff.get_handoff_synthesis_service"
        ) as mock_service:
            mock_instance = MagicMock()
            mock_instance.synthesize_shift_data = AsyncMock(
                return_value=mock_synthesis_response
            )
            mock_service.return_value = mock_instance

            response = client.get(
                "/api/v1/handoff/synthesis",
                headers={"Authorization": "Bearer test-token"}
            )

            data = response.json()
            metadata = data["metadata"]

            assert "generated_at" in metadata
            assert "generation_duration_ms" in metadata
            assert "completion_percentage" in metadata
            assert "timed_out" in metadata


# =============================================================================
# Test: POST /api/v1/handoff/{id}/synthesis Endpoint
# =============================================================================


class TestHandoffSynthesisAttachEndpoint:
    """Tests for attaching synthesis to a handoff."""

    def test_attach_requires_authentication(self, client):
        """Attach endpoint requires authentication."""
        handoff_id = str(uuid4())
        response = client.post(f"/api/v1/handoff/{handoff_id}/synthesis")
        assert response.status_code == 401

    def test_attach_handoff_not_found(self, client, mock_verify_jwt):
        """Returns 404 when handoff not found."""
        with patch(
            "app.api.handoff._get_handoff_by_id",
            return_value=None,
        ):
            handoff_id = str(uuid4())
            response = client.post(
                f"/api/v1/handoff/{handoff_id}/synthesis",
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 404

    def test_attach_forbidden_for_other_user(self, client, mock_verify_jwt):
        """Returns 403 when user is not the owner."""
        with patch(
            "app.api.handoff._get_handoff_by_id",
            return_value={
                "id": str(uuid4()),
                "user_id": "other-user-id",  # Different from JWT sub
            },
        ):
            handoff_id = str(uuid4())
            response = client.post(
                f"/api/v1/handoff/{handoff_id}/synthesis",
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 403

    def test_attach_only_draft_handoffs(
        self,
        client,
        mock_verify_jwt,
        valid_jwt_payload,
    ):
        """Returns 400 when handoff is not in draft status."""
        user_id = valid_jwt_payload["sub"]
        with patch(
            "app.api.handoff._get_handoff_by_id",
            return_value={
                "id": str(uuid4()),
                "user_id": user_id,
                "status": "pending_acknowledgment",  # Not draft
            },
        ):
            handoff_id = str(uuid4())
            response = client.post(
                f"/api/v1/handoff/{handoff_id}/synthesis",
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 400

    def test_attach_stores_summary_in_handoff(
        self,
        client,
        mock_verify_jwt,
        valid_jwt_payload,
        mock_synthesis_response,
    ):
        """Synthesis is stored in handoff's summary field."""
        handoff_id = str(uuid4())
        user_id = valid_jwt_payload["sub"]
        saved_handoff = None

        def mock_save(handoff):
            nonlocal saved_handoff
            saved_handoff = handoff
            return handoff

        with patch(
            "app.api.handoff._get_handoff_by_id",
            return_value={
                "id": handoff_id,
                "user_id": user_id,
                "status": "draft",
                "summary": None,
            },
        ), patch(
            "app.api.handoff._get_supervisor_assignments",
            return_value=[],
        ), patch(
            "app.api.handoff._save_handoff",
            side_effect=mock_save,
        ), patch(
            "app.api.handoff.get_handoff_synthesis_service"
        ) as mock_service:
            mock_instance = MagicMock()
            mock_instance.synthesize_shift_data = AsyncMock(
                return_value=mock_synthesis_response
            )
            mock_service.return_value = mock_instance

            response = client.post(
                f"/api/v1/handoff/{handoff_id}/synthesis",
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200
            assert saved_handoff is not None
            assert saved_handoff["summary"] is not None
            assert len(saved_handoff["summary"]) > 0


# =============================================================================
# Test: Partial Results and Timeout
# =============================================================================


class TestPartialResultsAndTimeout:
    """Tests for partial results and timeout handling."""

    def test_returns_partial_on_timeout(
        self,
        client,
        mock_verify_jwt,
    ):
        """AC#4: Returns partial results on timeout."""
        now = _utcnow()
        partial_response = HandoffSynthesisResponse(
            id=str(uuid4()),
            user_id="123e4567-e89b-12d3-a456-426614174000",
            shift_info=ShiftTimeRange(
                shift_type=ShiftType.MORNING,
                start_time=now,
                end_time=now,
                shift_date=now.date(),
            ),
            sections=[
                HandoffSection(
                    section_type="overview",
                    title="Shift Performance Overview",
                    content="Production data...",
                    status=HandoffSectionStatus.COMPLETE,
                ),
                HandoffSection(
                    section_type="issues",
                    title="Issues Encountered",
                    content="Loading...",
                    status=HandoffSectionStatus.LOADING,
                ),
            ],
            total_sections=4,
            completed_sections=1,
            metadata=HandoffSynthesisMetadata(
                timed_out=True,
                partial_result=True,
                completion_percentage=25.0,
            ),
        )

        with patch(
            "app.api.handoff._get_supervisor_assignments",
            return_value=[],
        ), patch(
            "app.api.handoff.get_handoff_synthesis_service"
        ) as mock_service:
            mock_instance = MagicMock()
            mock_instance.synthesize_shift_data = AsyncMock(
                return_value=partial_response
            )
            mock_service.return_value = mock_instance

            response = client.get(
                "/api/v1/handoff/synthesis",
                headers={"Authorization": "Bearer test-token"}
            )

            data = response.json()

            assert data["metadata"]["timed_out"] is True
            assert data["metadata"]["partial_result"] is True
            assert data["completed_sections"] < data["total_sections"]


# =============================================================================
# Test: Tool Failure Handling
# =============================================================================


class TestToolFailureHandling:
    """Tests for handling tool failures."""

    def test_reports_tool_failures_in_metadata(
        self,
        client,
        mock_verify_jwt,
    ):
        """AC#3: Reports failed tools in metadata."""
        now = _utcnow()
        failed_response = HandoffSynthesisResponse(
            id=str(uuid4()),
            user_id="123e4567-e89b-12d3-a456-426614174000",
            shift_info=ShiftTimeRange(
                shift_type=ShiftType.MORNING,
                start_time=now,
                end_time=now,
                shift_date=now.date(),
            ),
            sections=[
                HandoffSection(
                    section_type="overview",
                    title="Shift Performance Overview",
                    content="[Data unavailable] Unable to retrieve production status.",
                    status=HandoffSectionStatus.COMPLETE,
                ),
            ],
            total_sections=4,
            completed_sections=4,
            metadata=HandoffSynthesisMetadata(
                tool_failures=["production_status"],
            ),
        )

        with patch(
            "app.api.handoff._get_supervisor_assignments",
            return_value=[],
        ), patch(
            "app.api.handoff.get_handoff_synthesis_service"
        ) as mock_service:
            mock_instance = MagicMock()
            mock_instance.synthesize_shift_data = AsyncMock(
                return_value=failed_response
            )
            mock_service.return_value = mock_instance

            response = client.get(
                "/api/v1/handoff/synthesis",
                headers={"Authorization": "Bearer test-token"}
            )

            data = response.json()

            assert "production_status" in data["metadata"]["tool_failures"]
