"""
EOD Service Tests (Story 9.10)

Tests for the End of Day summary service including:
- EOD generation trigger (AC#1)
- Summary content structure (AC#2)
- No morning briefing fallback (AC#3)

References:
- [Source: prd/prd-functional-requirements.md#FR31-FR34]
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
from datetime import datetime, date, time, timezone

from app.services.briefing.eod import (
    EODService,
    get_eod_service,
    MorningBriefingRecord,
    EOD_TOTAL_TIMEOUT_SECONDS,
)
from app.models.briefing import (
    BriefingData,
    ToolResultData,
    BriefingSectionStatus,
    EODSection,
    EODSummaryResponse,
    MorningComparisonResult,
)


class TestEODService:
    """Tests for EODService."""

    @pytest.fixture
    def service(self):
        """Create a test service."""
        return EODService()

    @pytest.fixture
    def mock_briefing_data(self):
        """Create mock briefing data with successful tools."""
        return BriefingData(
            production_status=ToolResultData(
                tool_name="production_status",
                success=True,
                data={
                    "summary": {
                        "total_output": 10500,
                        "total_target": 10000,
                        "total_variance_percent": 5.0,
                        "ahead_count": 5,
                        "behind_count": 2,
                        "assets_needing_attention": ["Packer 3"],
                    },
                    "assets": [
                        {"asset_name": "Packer 1", "status": "ahead"},
                        {"asset_name": "Packer 2", "status": "ahead"},
                    ],
                },
            ),
            safety_events=ToolResultData(
                tool_name="safety_events",
                success=True,
                data={"total_events": 0},
            ),
            oee_data=ToolResultData(
                tool_name="oee_data",
                success=True,
                data={"oee_percentage": 87.5},
            ),
            downtime_analysis=ToolResultData(
                tool_name="downtime_analysis",
                success=True,
                data={
                    "top_reasons": [
                        {"reason": "Material shortage", "duration_minutes": 45}
                    ]
                },
            ),
            action_list=ToolResultData(
                tool_name="action_list",
                success=True,
                data={
                    "actions": [
                        {"title": "Review Packer 3", "status": "pending"}
                    ]
                },
            ),
        )

    @pytest.fixture
    def mock_morning_briefing(self):
        """Create mock morning briefing record."""
        return MorningBriefingRecord(
            id="morning-123",
            generated_at=datetime.now(timezone.utc).replace(hour=7),
            concerns=["Monitor Packer 3 closely"],
            wins=["Roasting on track for 5% ahead"],
            sections=[],
        )

    @pytest.mark.asyncio
    async def test_generate_eod_summary_success(self, service, mock_briefing_data):
        """Test successful EOD summary generation (AC#1)."""
        with patch.object(service, '_orchestrate_eod_tools') as mock_orchestrate:
            mock_orchestrate.return_value = mock_briefing_data

            with patch.object(service, '_find_morning_briefing') as mock_find:
                mock_find.return_value = None  # No morning briefing

                result = await service.generate_eod_summary(
                    user_id="test-user",
                    summary_date=date.today(),
                )

                assert result is not None
                assert result.id is not None
                assert result.user_id == "test-user"
                assert result.scope == "eod"
                assert len(result.sections) >= 5  # All 5 EOD sections
                assert not result.metadata.timed_out

    @pytest.mark.asyncio
    async def test_generate_eod_summary_with_morning_comparison(
        self, service, mock_briefing_data, mock_morning_briefing
    ):
        """Test EOD summary with morning briefing comparison (AC#2)."""
        with patch.object(service, '_orchestrate_eod_tools') as mock_orchestrate:
            mock_orchestrate.return_value = mock_briefing_data

            with patch.object(service, '_find_morning_briefing') as mock_find:
                mock_find.return_value = mock_morning_briefing

                result = await service.generate_eod_summary(
                    user_id="test-user",
                    summary_date=date.today(),
                )

                assert result.comparison_available is True
                assert result.morning_briefing_id == "morning-123"
                assert result.morning_comparison is not None

    @pytest.mark.asyncio
    async def test_generate_eod_summary_no_morning_briefing(
        self, service, mock_briefing_data
    ):
        """Test EOD summary without morning briefing (AC#3)."""
        with patch.object(service, '_orchestrate_eod_tools') as mock_orchestrate:
            mock_orchestrate.return_value = mock_briefing_data

            with patch.object(service, '_find_morning_briefing') as mock_find:
                mock_find.return_value = None

                result = await service.generate_eod_summary(
                    user_id="test-user",
                )

                assert result.comparison_available is False
                assert result.morning_briefing_id is None
                assert result.morning_comparison is None

                # Check comparison section has fallback message
                comparison_sections = [
                    s for s in result.sections
                    if s.section_type == EODSection.COMPARISON.value
                ]
                assert len(comparison_sections) == 1
                assert "No morning briefing" in comparison_sections[0].content

    @pytest.mark.asyncio
    async def test_generate_eod_summary_timeout(self, service):
        """Test EOD summary timeout handling."""
        async def slow_orchestrate(*args, **kwargs):
            await asyncio.sleep(35)
            return BriefingData()

        with patch.object(service, '_orchestrate_eod_tools', side_effect=slow_orchestrate):
            result = await service.generate_eod_summary(
                user_id="test-user",
            )

            assert result is not None
            assert result.metadata.timed_out is True

    @pytest.mark.asyncio
    async def test_generate_eod_summary_with_tool_failures(self, service):
        """Test EOD summary with partial tool failures."""
        partial_data = BriefingData(
            production_status=ToolResultData(
                tool_name="production_status",
                success=True,
                data={"summary": {"total_output": 1000, "total_target": 1000}},
            ),
            safety_events=ToolResultData(
                tool_name="safety_events",
                success=False,
                error_message="Connection timeout",
            ),
            oee_data=ToolResultData(
                tool_name="oee_data",
                success=False,
                error_message="Data unavailable",
            ),
        )

        with patch.object(service, '_orchestrate_eod_tools') as mock_orchestrate:
            mock_orchestrate.return_value = partial_data

            with patch.object(service, '_find_morning_briefing') as mock_find:
                mock_find.return_value = None

                result = await service.generate_eod_summary(
                    user_id="test-user",
                )

                assert result is not None
                assert "safety_events" in result.metadata.tool_failures
                assert "oee_data" in result.metadata.tool_failures

    def test_generate_performance_section(self, service, mock_briefing_data):
        """Test performance section generation (AC#2)."""
        citations = []
        section = service._generate_performance_section(mock_briefing_data, citations)

        assert section.section_type == EODSection.PERFORMANCE.value
        assert section.title == "Day's Performance"
        assert "output" in section.content.lower() or "target" in section.content.lower()
        assert section.status == BriefingSectionStatus.COMPLETE

    def test_generate_comparison_section_with_morning(
        self, service, mock_morning_briefing
    ):
        """Test comparison section with morning briefing."""
        comparison = MorningComparisonResult(
            morning_briefing_id=mock_morning_briefing.id,
            morning_generated_at=mock_morning_briefing.generated_at,
            prediction_summary="Day went as predicted",
        )

        section = service._generate_comparison_section(
            mock_morning_briefing, comparison, []
        )

        assert section.section_type == EODSection.COMPARISON.value
        assert "Day went as predicted" in section.content

    def test_generate_comparison_section_no_morning(self, service):
        """Test comparison section fallback (AC#3)."""
        section = service._generate_comparison_section(None, None, [])

        assert section.section_type == EODSection.COMPARISON.value
        assert "No morning briefing" in section.content

    def test_generate_wins_section(self, service, mock_briefing_data):
        """Test wins section generation."""
        comparison = MorningComparisonResult(
            morning_briefing_id="test",
            morning_generated_at=datetime.now(timezone.utc),
            actual_wins=["5 assets exceeded targets"],
        )

        section = service._generate_wins_section(mock_briefing_data, comparison, [])

        assert section.section_type == EODSection.WINS.value
        assert section.status == BriefingSectionStatus.COMPLETE

    def test_generate_concerns_section(self, service, mock_briefing_data):
        """Test concerns section generation."""
        comparison = MorningComparisonResult(
            morning_briefing_id="test",
            morning_generated_at=datetime.now(timezone.utc),
            concerns_resolved=["Issue resolved"],
            concerns_escalated=["New issue emerged"],
        )

        section = service._generate_concerns_section(mock_briefing_data, comparison, [])

        assert section.section_type == EODSection.CONCERNS.value

    def test_generate_outlook_section(self, service, mock_briefing_data):
        """Test outlook section generation."""
        section = service._generate_outlook_section(mock_briefing_data, [])

        assert section.section_type == EODSection.OUTLOOK.value
        assert section.status == BriefingSectionStatus.COMPLETE

    def test_get_eod_title(self, service):
        """Test EOD title generation."""
        test_date = date(2024, 1, 15)
        title = service._get_eod_title(test_date)

        assert "End of Day Summary" in title
        assert "Monday" in title
        assert "January 15" in title

    def test_create_error_response(self, service):
        """Test error response generation."""
        result = service._create_error_response(
            summary_id="test-id",
            user_id="test-user",
            error_message="Test error",
        )

        assert result.id == "test-id"
        assert result.scope == "error"
        assert len(result.sections) == 1
        assert result.sections[0].status == BriefingSectionStatus.FAILED
        assert result.comparison_available is False

    @pytest.mark.asyncio
    async def test_compare_to_morning_success(self, service, mock_morning_briefing, mock_briefing_data):
        """Test morning comparison logic."""
        result = await service._compare_to_morning(
            mock_morning_briefing,
            mock_briefing_data
        )

        assert result.morning_briefing_id == mock_morning_briefing.id
        assert isinstance(result.prediction_summary, str)
        # Should have wins (production exceeded target)
        assert len(result.actual_wins) > 0


class TestMorningComparisonResult:
    """Tests for MorningComparisonResult model."""

    def test_morning_comparison_defaults(self):
        """Test comparison result with defaults."""
        result = MorningComparisonResult(
            morning_briefing_id="test-123",
            morning_generated_at=datetime.now(timezone.utc),
        )

        assert result.flagged_concerns == []
        assert result.concerns_resolved == []
        assert result.concerns_escalated == []
        assert result.predicted_wins == []
        assert result.actual_wins == []
        assert result.prediction_summary == ""


class TestGetEODService:
    """Tests for singleton getter."""

    def test_get_eod_service_returns_singleton(self):
        """Test singleton pattern."""
        import app.services.briefing.eod as module
        module._eod_service = None

        service1 = get_eod_service()
        service2 = get_eod_service()

        assert service1 is service2


class TestEODSummaryResponse:
    """Tests for EODSummaryResponse model."""

    def test_eod_summary_response_defaults(self):
        """Test EOD response with defaults."""
        from app.models.briefing import BriefingResponseMetadata

        response = EODSummaryResponse(
            id="test-eod-123",
            title="Test EOD",
            scope="eod",
            user_id="test-user",
            sections=[],
            metadata=BriefingResponseMetadata(),
        )

        assert response.morning_briefing_id is None
        assert response.comparison_available is False
        assert response.morning_comparison is None
        assert response.prediction_accuracy is None

    def test_eod_summary_response_with_comparison(self):
        """Test EOD response with morning comparison."""
        from app.models.briefing import BriefingResponseMetadata

        comparison = MorningComparisonResult(
            morning_briefing_id="morning-456",
            morning_generated_at=datetime.now(timezone.utc),
            prediction_summary="Good match",
        )

        response = EODSummaryResponse(
            id="test-eod-789",
            title="Test EOD",
            scope="eod",
            user_id="test-user",
            sections=[],
            metadata=BriefingResponseMetadata(),
            morning_briefing_id="morning-456",
            comparison_available=True,
            morning_comparison=comparison,
        )

        assert response.comparison_available is True
        assert response.morning_comparison.prediction_summary == "Good match"
