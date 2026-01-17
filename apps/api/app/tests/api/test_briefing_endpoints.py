"""
Briefing API Endpoint Tests (Story 8.4)

Tests for briefing API endpoints including:
- POST /api/v1/briefing/morning (AC#1)
- GET /api/v1/briefing/{briefing_id} (AC#2)
- POST /api/v1/briefing/{briefing_id}/qa (AC#5)
- POST /api/v1/briefing/{briefing_id}/continue (AC#3)

References:
- [Source: architecture/voice-briefing.md#BriefingService Architecture]
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.models.briefing import (
    BriefingResponse,
    BriefingSection,
    BriefingSectionStatus,
    BriefingResponseMetadata,
    BriefingScope,
)


# Test client
client = TestClient(app)


class TestBriefingAreasEndpoint:
    """Tests for GET /api/v1/briefing/areas endpoint."""

    def test_get_areas_returns_all_seven_areas(self):
        """Test areas endpoint returns all 7 production areas."""
        response = client.get("/api/v1/briefing/areas")

        assert response.status_code == 200
        data = response.json()

        assert "areas" in data
        assert "default_order" in data
        assert len(data["areas"]) == 7
        assert len(data["default_order"]) == 7

    def test_get_areas_includes_required_fields(self):
        """Test each area has required fields."""
        response = client.get("/api/v1/briefing/areas")
        data = response.json()

        for area in data["areas"]:
            assert "id" in area
            assert "name" in area
            assert "description" in area
            assert "assets" in area
            assert isinstance(area["assets"], list)

    def test_get_areas_includes_expected_names(self):
        """Test areas include expected production area names."""
        response = client.get("/api/v1/briefing/areas")
        data = response.json()

        area_names = [area["name"] for area in data["areas"]]

        assert "Packing" in area_names
        assert "Rychigers" in area_names
        assert "Grinding" in area_names
        assert "Powder" in area_names
        assert "Roasting" in area_names
        assert "Green Bean" in area_names
        assert "Flavor Room" in area_names


class TestMorningBriefingEndpoint:
    """Tests for POST /api/v1/briefing/morning endpoint."""

    @pytest.fixture
    def mock_briefing_response(self):
        """Create a mock briefing response."""
        from datetime import datetime, timezone

        return BriefingResponse(
            id="test-briefing-123",
            title="Morning Briefing - Thursday, January 16",
            scope=BriefingScope.PLANT_WIDE.value,
            user_id="test-user",
            sections=[
                BriefingSection(
                    section_type="headline",
                    title="Morning Briefing Overview",
                    content="Good morning! Here's your plant overview.",
                    status=BriefingSectionStatus.COMPLETE,
                    pause_point=True,
                ),
                BriefingSection(
                    section_type="area",
                    title="Packing",
                    content="Packing is performing well at 5% ahead of target.",
                    area_id="packing",
                    status=BriefingSectionStatus.COMPLETE,
                    pause_point=True,
                ),
            ],
            audio_stream_url=None,
            total_duration_estimate=75,
            metadata=BriefingResponseMetadata(
                generated_at=datetime.now(timezone.utc),
                generation_duration_ms=500,
                completion_percentage=100.0,
                timed_out=False,
                tool_failures=[],
            ),
        )

    def test_generate_morning_briefing_success(self, mock_briefing_response):
        """Test successful morning briefing generation."""
        with patch('app.api.briefing.get_morning_briefing_service') as mock_service:
            mock_service.return_value.generate_plant_briefing = AsyncMock(
                return_value=mock_briefing_response
            )

            response = client.post(
                "/api/v1/briefing/morning",
                json={
                    "user_id": "test-user",
                    "include_audio": True,
                },
            )

            assert response.status_code == 200
            data = response.json()

            assert "briefing_id" in data
            assert "title" in data
            assert "sections" in data
            assert len(data["sections"]) == 2

    def test_generate_morning_briefing_with_custom_order(self, mock_briefing_response):
        """Test briefing generation with custom area order."""
        with patch('app.api.briefing.get_morning_briefing_service') as mock_service:
            mock_service.return_value.generate_plant_briefing = AsyncMock(
                return_value=mock_briefing_response
            )

            response = client.post(
                "/api/v1/briefing/morning",
                json={
                    "user_id": "test-user",
                    "area_order": ["roasting", "grinding", "packing"],
                    "include_audio": True,
                },
            )

            assert response.status_code == 200

            # Verify custom order was passed
            mock_service.return_value.generate_plant_briefing.assert_called_once()
            call_args = mock_service.return_value.generate_plant_briefing.call_args
            assert call_args.kwargs.get("area_order") == ["roasting", "grinding", "packing"]

    def test_generate_morning_briefing_returns_sections_with_pause_points(self, mock_briefing_response):
        """Test sections have pause_point flag (AC#2)."""
        with patch('app.api.briefing.get_morning_briefing_service') as mock_service:
            mock_service.return_value.generate_plant_briefing = AsyncMock(
                return_value=mock_briefing_response
            )

            response = client.post(
                "/api/v1/briefing/morning",
                json={"user_id": "test-user"},
            )

            data = response.json()

            for section in data["sections"]:
                assert "pause_point" in section
                assert section["pause_point"] is True

    def test_generate_morning_briefing_error_handling(self):
        """Test error handling during briefing generation."""
        with patch('app.api.briefing.get_morning_briefing_service') as mock_service:
            mock_service.return_value.generate_plant_briefing = AsyncMock(
                side_effect=Exception("Generation failed")
            )

            response = client.post(
                "/api/v1/briefing/morning",
                json={"user_id": "test-user"},
            )

            assert response.status_code == 500
            assert "Failed to generate" in response.json()["detail"]


class TestBriefingDetailsEndpoint:
    """Tests for GET /api/v1/briefing/{briefing_id} endpoint."""

    def test_get_briefing_not_found(self):
        """Test 404 when briefing not found."""
        response = client.get("/api/v1/briefing/nonexistent-id")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_briefing_success(self):
        """Test successful briefing retrieval."""
        # First create a briefing
        with patch('app.api.briefing.get_morning_briefing_service') as mock_service:
            from datetime import datetime, timezone

            mock_response = BriefingResponse(
                id="test-briefing-456",
                title="Test Briefing",
                scope=BriefingScope.PLANT_WIDE.value,
                user_id="test-user",
                sections=[
                    BriefingSection(
                        section_type="headline",
                        title="Test",
                        content="Test content",
                        status=BriefingSectionStatus.COMPLETE,
                        pause_point=True,
                    ),
                ],
                metadata=BriefingResponseMetadata(
                    generated_at=datetime.now(timezone.utc),
                    completion_percentage=100.0,
                ),
            )
            mock_service.return_value.generate_plant_briefing = AsyncMock(
                return_value=mock_response
            )

            # Create briefing
            create_response = client.post(
                "/api/v1/briefing/morning",
                json={"user_id": "test-user"},
            )
            briefing_id = create_response.json()["briefing_id"]

            # Retrieve it
            get_response = client.get(f"/api/v1/briefing/{briefing_id}")

            assert get_response.status_code == 200
            data = get_response.json()
            assert data["briefing_id"] == briefing_id


class TestQAEndpoint:
    """Tests for POST /api/v1/briefing/{briefing_id}/qa endpoint."""

    def test_qa_briefing_not_found(self):
        """Test 404 when briefing not found for Q&A."""
        response = client.post(
            "/api/v1/briefing/nonexistent-id/qa",
            json={
                "question": "What is the OEE?",
                "user_id": "test-user",
            },
        )

        assert response.status_code == 404

    def test_qa_success(self):
        """Test successful Q&A processing (AC#5)."""
        # First create a briefing
        with patch('app.api.briefing.get_morning_briefing_service') as mock_service:
            from datetime import datetime, timezone

            mock_response = BriefingResponse(
                id="test-qa-briefing",
                title="Test Briefing",
                scope=BriefingScope.PLANT_WIDE.value,
                user_id="test-user",
                sections=[
                    BriefingSection(
                        section_type="area",
                        title="Packing",
                        content="Test content",
                        area_id="packing",
                        status=BriefingSectionStatus.COMPLETE,
                        pause_point=True,
                    ),
                ],
                metadata=BriefingResponseMetadata(
                    generated_at=datetime.now(timezone.utc),
                    completion_percentage=100.0,
                ),
            )
            mock_service.return_value.generate_plant_briefing = AsyncMock(
                return_value=mock_response
            )
            mock_service.return_value.process_qa_question = AsyncMock(
                return_value={
                    "answer": "The OEE is 87.5%",
                    "citations": ["daily_summaries"],
                    "follow_up_prompt": "Anything else on Packing?",
                    "area_id": "packing",
                }
            )

            # Create briefing
            create_response = client.post(
                "/api/v1/briefing/morning",
                json={"user_id": "test-user"},
            )
            briefing_id = create_response.json()["briefing_id"]

            # Ask a question
            qa_response = client.post(
                f"/api/v1/briefing/{briefing_id}/qa",
                json={
                    "question": "What is the OEE?",
                    "area_id": "packing",
                    "user_id": "test-user",
                },
            )

            assert qa_response.status_code == 200
            data = qa_response.json()

            assert "answer" in data
            assert "citations" in data
            assert "follow_up_prompt" in data

    def test_qa_returns_follow_up_prompt(self):
        """Test Q&A returns follow-up prompt for continued interaction (AC#5)."""
        with patch('app.api.briefing.get_morning_briefing_service') as mock_service:
            from datetime import datetime, timezone

            mock_response = BriefingResponse(
                id="test-qa-followup",
                title="Test Briefing",
                scope=BriefingScope.PLANT_WIDE.value,
                user_id="test-user",
                sections=[
                    BriefingSection(
                        section_type="area",
                        title="Grinding",
                        content="Test content",
                        area_id="grinding",
                        status=BriefingSectionStatus.COMPLETE,
                        pause_point=True,
                    ),
                ],
                metadata=BriefingResponseMetadata(
                    generated_at=datetime.now(timezone.utc),
                    completion_percentage=100.0,
                ),
            )
            mock_service.return_value.generate_plant_briefing = AsyncMock(
                return_value=mock_response
            )
            mock_service.return_value.process_qa_question = AsyncMock(
                return_value={
                    "answer": "Downtime was 30 minutes",
                    "citations": ["downtime_events"],
                    "follow_up_prompt": "Anything else on Grinding?",
                    "area_id": "grinding",
                }
            )

            # Create and Q&A
            create_response = client.post(
                "/api/v1/briefing/morning",
                json={"user_id": "test-user"},
            )
            briefing_id = create_response.json()["briefing_id"]

            qa_response = client.post(
                f"/api/v1/briefing/{briefing_id}/qa",
                json={
                    "question": "What was the downtime?",
                    "area_id": "grinding",
                    "user_id": "test-user",
                },
            )

            data = qa_response.json()
            assert "Grinding" in data["follow_up_prompt"]


class TestContinueEndpoint:
    """Tests for POST /api/v1/briefing/{briefing_id}/continue endpoint."""

    def test_continue_briefing_not_found(self):
        """Test 404 when briefing not found."""
        response = client.post(
            "/api/v1/briefing/nonexistent-id/continue",
            params={"section_index": 0},
        )

        assert response.status_code == 404

    def test_continue_to_next_section(self):
        """Test continuing to next section (AC#3)."""
        with patch('app.api.briefing.get_morning_briefing_service') as mock_service:
            from datetime import datetime, timezone

            mock_response = BriefingResponse(
                id="test-continue-briefing",
                title="Test Briefing",
                scope=BriefingScope.PLANT_WIDE.value,
                user_id="test-user",
                sections=[
                    BriefingSection(
                        section_type="headline",
                        title="Overview",
                        content="Overview content",
                        status=BriefingSectionStatus.COMPLETE,
                        pause_point=True,
                    ),
                    BriefingSection(
                        section_type="area",
                        title="Packing",
                        content="Packing content",
                        area_id="packing",
                        status=BriefingSectionStatus.COMPLETE,
                        pause_point=True,
                    ),
                    BriefingSection(
                        section_type="area",
                        title="Grinding",
                        content="Grinding content",
                        area_id="grinding",
                        status=BriefingSectionStatus.COMPLETE,
                        pause_point=True,
                    ),
                ],
                metadata=BriefingResponseMetadata(
                    generated_at=datetime.now(timezone.utc),
                    completion_percentage=100.0,
                ),
            )
            mock_service.return_value.generate_plant_briefing = AsyncMock(
                return_value=mock_response
            )

            # Create briefing
            create_response = client.post(
                "/api/v1/briefing/morning",
                json={"user_id": "test-user"},
            )
            briefing_id = create_response.json()["briefing_id"]

            # Continue from section 0
            continue_response = client.post(
                f"/api/v1/briefing/{briefing_id}/continue",
                params={"section_index": 0},
            )

            assert continue_response.status_code == 200
            data = continue_response.json()

            assert data["status"] == "continuing"
            assert data["next_section_index"] == 1
            assert data["next_section"]["title"] == "Packing"

    def test_continue_at_end_returns_complete(self):
        """Test continuing at last section returns complete status."""
        with patch('app.api.briefing.get_morning_briefing_service') as mock_service:
            from datetime import datetime, timezone

            mock_response = BriefingResponse(
                id="test-continue-end",
                title="Test Briefing",
                scope=BriefingScope.PLANT_WIDE.value,
                user_id="test-user",
                sections=[
                    BriefingSection(
                        section_type="headline",
                        title="Overview",
                        content="Overview content",
                        status=BriefingSectionStatus.COMPLETE,
                        pause_point=True,
                    ),
                ],
                metadata=BriefingResponseMetadata(
                    generated_at=datetime.now(timezone.utc),
                    completion_percentage=100.0,
                ),
            )
            mock_service.return_value.generate_plant_briefing = AsyncMock(
                return_value=mock_response
            )

            # Create briefing
            create_response = client.post(
                "/api/v1/briefing/morning",
                json={"user_id": "test-user"},
            )
            briefing_id = create_response.json()["briefing_id"]

            # Continue from last section
            continue_response = client.post(
                f"/api/v1/briefing/{briefing_id}/continue",
                params={"section_index": 0},
            )

            assert continue_response.status_code == 200
            data = continue_response.json()

            assert data["status"] == "complete"
            assert data["next_section_index"] is None


class TestEndBriefingEndpoint:
    """Tests for POST /api/v1/briefing/{briefing_id}/end endpoint."""

    def test_end_briefing_not_found(self):
        """Test 404 when briefing not found."""
        response = client.post("/api/v1/briefing/nonexistent-id/end")

        assert response.status_code == 404

    def test_end_briefing_success(self):
        """Test successful briefing end."""
        with patch('app.api.briefing.get_morning_briefing_service') as mock_service:
            from datetime import datetime, timezone

            mock_response = BriefingResponse(
                id="test-end-briefing",
                title="Test Briefing",
                scope=BriefingScope.PLANT_WIDE.value,
                user_id="test-user",
                sections=[
                    BriefingSection(
                        section_type="headline",
                        title="Overview",
                        content="Overview content",
                        status=BriefingSectionStatus.COMPLETE,
                        pause_point=True,
                    ),
                ],
                metadata=BriefingResponseMetadata(
                    generated_at=datetime.now(timezone.utc),
                    completion_percentage=100.0,
                ),
            )
            mock_service.return_value.generate_plant_briefing = AsyncMock(
                return_value=mock_response
            )

            # Create briefing
            create_response = client.post(
                "/api/v1/briefing/morning",
                json={"user_id": "test-user"},
            )
            briefing_id = create_response.json()["briefing_id"]

            # End briefing
            end_response = client.post(f"/api/v1/briefing/{briefing_id}/end")

            assert end_response.status_code == 200
            data = end_response.json()

            assert data["status"] == "ended"
            assert data["briefing_id"] == briefing_id


# ============================================================================
# EOD Summary Endpoint Tests (Story 9.10)
# ============================================================================


class TestEODSummaryEndpoint:
    """Tests for POST /api/v1/briefing/eod endpoint."""

    @pytest.fixture
    def mock_eod_response(self):
        """Create a mock EOD summary response."""
        from datetime import datetime, timezone
        from app.models.briefing import (
            EODSummaryResponse,
            MorningComparisonResult,
        )

        return EODSummaryResponse(
            id="test-eod-123",
            title="End of Day Summary - Thursday, January 16",
            scope="eod",
            user_id="test-user",
            sections=[
                BriefingSection(
                    section_type="performance",
                    title="Day's Performance",
                    content="Today's total output: about 10 thousand units.",
                    status=BriefingSectionStatus.COMPLETE,
                    pause_point=True,
                ),
                BriefingSection(
                    section_type="comparison",
                    title="Morning vs Actual",
                    content="No morning briefing was generated today.",
                    status=BriefingSectionStatus.COMPLETE,
                    pause_point=False,
                ),
                BriefingSection(
                    section_type="wins",
                    title="Wins That Materialized",
                    content="5 assets exceeded targets.",
                    status=BriefingSectionStatus.COMPLETE,
                    pause_point=True,
                ),
                BriefingSection(
                    section_type="concerns",
                    title="Concerns Status",
                    content="No major concerns.",
                    status=BriefingSectionStatus.COMPLETE,
                    pause_point=True,
                ),
                BriefingSection(
                    section_type="outlook",
                    title="Tomorrow's Outlook",
                    content="Focus on maintaining momentum.",
                    status=BriefingSectionStatus.COMPLETE,
                    pause_point=True,
                ),
            ],
            audio_stream_url=None,
            total_duration_estimate=90,
            metadata=BriefingResponseMetadata(
                generated_at=datetime.now(timezone.utc),
                generation_duration_ms=500,
                completion_percentage=100.0,
                timed_out=False,
                tool_failures=[],
            ),
            morning_briefing_id=None,
            comparison_available=False,
            morning_comparison=None,
            summary_date=datetime.now(timezone.utc),
            time_range_start=datetime.now(timezone.utc).replace(hour=6, minute=0),
            time_range_end=datetime.now(timezone.utc),
        )

    def test_generate_eod_summary_success(self, mock_eod_response):
        """Test successful EOD summary generation (Story 9.10 AC#1)."""
        with patch('app.api.briefing.get_eod_service') as mock_service:
            mock_service.return_value.generate_eod_summary = AsyncMock(
                return_value=mock_eod_response
            )

            response = client.post(
                "/api/v1/briefing/eod",
                json={
                    "user_id": "test-user",
                    "include_audio": True,
                },
            )

            assert response.status_code == 200
            data = response.json()

            assert "summary_id" in data
            assert "title" in data
            assert "sections" in data
            assert len(data["sections"]) == 5  # All 5 EOD sections
            assert data["comparison_available"] is False

    def test_generate_eod_summary_with_date(self, mock_eod_response):
        """Test EOD summary generation with specific date."""
        with patch('app.api.briefing.get_eod_service') as mock_service:
            mock_service.return_value.generate_eod_summary = AsyncMock(
                return_value=mock_eod_response
            )

            response = client.post(
                "/api/v1/briefing/eod",
                json={
                    "user_id": "test-user",
                    "date": "2024-01-15",
                    "include_audio": False,
                },
            )

            assert response.status_code == 200

            # Verify date was passed to service
            mock_service.return_value.generate_eod_summary.assert_called_once()
            call_args = mock_service.return_value.generate_eod_summary.call_args
            from datetime import date as date_type
            assert call_args.kwargs.get("summary_date") == date_type(2024, 1, 15)

    def test_generate_eod_summary_invalid_date(self):
        """Test EOD summary with invalid date format."""
        response = client.post(
            "/api/v1/briefing/eod",
            json={
                "user_id": "test-user",
                "date": "invalid-date",
            },
        )

        assert response.status_code == 400
        assert "Invalid date format" in response.json()["detail"]

    def test_generate_eod_summary_includes_section_structure(self, mock_eod_response):
        """Test EOD response includes proper section structure (AC#2)."""
        with patch('app.api.briefing.get_eod_service') as mock_service:
            mock_service.return_value.generate_eod_summary = AsyncMock(
                return_value=mock_eod_response
            )

            response = client.post(
                "/api/v1/briefing/eod",
                json={"user_id": "test-user"},
            )

            data = response.json()
            section_types = [s["section_type"] for s in data["sections"]]

            # AC#2: Should include all 5 section types
            assert "performance" in section_types
            assert "comparison" in section_types
            assert "wins" in section_types
            assert "concerns" in section_types
            assert "outlook" in section_types

    def test_generate_eod_summary_with_morning_comparison(self):
        """Test EOD summary with morning briefing comparison."""
        from datetime import datetime, timezone
        from app.models.briefing import (
            EODSummaryResponse,
            MorningComparisonResult,
        )

        mock_comparison = MorningComparisonResult(
            morning_briefing_id="morning-456",
            morning_generated_at=datetime.now(timezone.utc).replace(hour=7),
            flagged_concerns=["Watch Packer 3"],
            concerns_resolved=["Packer 3 back on track"],
            concerns_escalated=[],
            predicted_wins=["Roasting ahead"],
            actual_wins=["Roasting exceeded by 10%"],
            prediction_summary="Morning predictions were accurate.",
        )

        mock_response = EODSummaryResponse(
            id="test-eod-with-comparison",
            title="End of Day Summary",
            scope="eod",
            user_id="test-user",
            sections=[
                BriefingSection(
                    section_type="performance",
                    title="Day's Performance",
                    content="Great day overall.",
                    status=BriefingSectionStatus.COMPLETE,
                    pause_point=True,
                ),
            ],
            metadata=BriefingResponseMetadata(
                generated_at=datetime.now(timezone.utc),
                completion_percentage=100.0,
            ),
            morning_briefing_id="morning-456",
            comparison_available=True,
            morning_comparison=mock_comparison,
            summary_date=datetime.now(timezone.utc),
            time_range_start=datetime.now(timezone.utc).replace(hour=6),
            time_range_end=datetime.now(timezone.utc),
        )

        with patch('app.api.briefing.get_eod_service') as mock_service:
            mock_service.return_value.generate_eod_summary = AsyncMock(
                return_value=mock_response
            )

            response = client.post(
                "/api/v1/briefing/eod",
                json={"user_id": "test-user"},
            )

            assert response.status_code == 200
            data = response.json()

            assert data["comparison_available"] is True
            assert data["morning_briefing_id"] == "morning-456"
            assert data["morning_comparison"] is not None
            assert data["morning_comparison"]["concerns_resolved"] == ["Packer 3 back on track"]
            assert data["morning_comparison"]["actual_wins"] == ["Roasting exceeded by 10%"]

    def test_generate_eod_summary_error_handling(self):
        """Test error handling during EOD summary generation."""
        with patch('app.api.briefing.get_eod_service') as mock_service:
            mock_service.return_value.generate_eod_summary = AsyncMock(
                side_effect=Exception("Database connection failed")
            )

            response = client.post(
                "/api/v1/briefing/eod",
                json={"user_id": "test-user"},
            )

            assert response.status_code == 500
            assert "Failed to generate EOD summary" in response.json()["detail"]
