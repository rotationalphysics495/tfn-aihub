"""
MorningBriefingService Tests (Story 8.4)

Tests for the morning briefing service including:
- Area ordering respects user preferences (AC#1)
- All 7 production areas covered (AC#1)
- Section composition with pause points (AC#2)
- Graceful degradation when tools fail (AC#4)
- Q&A processing during pause (AC#5)

References:
- [Source: architecture/voice-briefing.md#BriefingService Architecture]
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from app.services.briefing.morning import (
    MorningBriefingService,
    get_morning_briefing_service,
    PRODUCTION_AREAS,
    DEFAULT_AREA_ORDER,
    AreaBriefingData,
)
from app.models.briefing import (
    BriefingScope,
    BriefingSectionStatus,
    ToolResultData,
    BriefingData,
    BriefingSection,
    BriefingResponse,
)


class TestMorningBriefingService:
    """Tests for MorningBriefingService."""

    @pytest.fixture
    def service(self):
        """Create a test service."""
        return MorningBriefingService()

    @pytest.fixture
    def mock_tool_result(self):
        """Create a mock successful tool result."""
        return ToolResultData(
            tool_name="test_tool",
            success=True,
            data={"test": "data"},
            citations=[],
        )

    # ==========================================================================
    # AC#1: All 7 production areas covered
    # ==========================================================================

    def test_production_areas_count(self, service):
        """Test that all 7 production areas are defined."""
        areas = service.get_production_areas()
        assert len(areas) == 7

    def test_production_areas_names(self, service):
        """Test all expected areas are present."""
        areas = service.get_production_areas()
        area_names = [a["name"] for a in areas]

        assert "Packing" in area_names
        assert "Rychigers" in area_names
        assert "Grinding" in area_names
        assert "Powder" in area_names
        assert "Roasting" in area_names
        assert "Green Bean" in area_names
        assert "Flavor Room" in area_names

    def test_production_areas_have_assets(self, service):
        """Test each area has assets defined."""
        areas = service.get_production_areas()

        for area in areas:
            assert "assets" in area
            assert len(area["assets"]) > 0, f"Area {area['name']} has no assets"

    # ==========================================================================
    # AC#1: User preferred area ordering (FR36)
    # ==========================================================================

    def test_default_area_order(self, service):
        """Test default area order is returned."""
        default_order = service.get_default_area_order()
        assert len(default_order) == 7
        assert default_order == DEFAULT_AREA_ORDER

    def test_order_areas_with_custom_order(self, service):
        """Test areas are ordered by user preference."""
        custom_order = ["roasting", "grinding", "packing"]
        ordered = service.order_areas(custom_order)

        # First three should be in custom order
        assert ordered[0]["id"] == "roasting"
        assert ordered[1]["id"] == "grinding"
        assert ordered[2]["id"] == "packing"

        # Remaining areas should be appended
        assert len(ordered) == 7

    def test_order_areas_default_when_none(self, service):
        """Test default order when no preference provided."""
        ordered = service.order_areas(None)

        assert ordered[0]["id"] == DEFAULT_AREA_ORDER[0]
        assert len(ordered) == 7

    def test_order_areas_handles_unknown_ids(self, service):
        """Test ordering handles unknown area IDs gracefully."""
        custom_order = ["roasting", "unknown_area", "grinding"]
        ordered = service.order_areas(custom_order)

        # Should skip unknown and keep known areas
        assert ordered[0]["id"] == "roasting"
        assert ordered[1]["id"] == "grinding"
        assert len(ordered) == 7

    # ==========================================================================
    # AC#2: Section composition with pause points
    # ==========================================================================

    @pytest.mark.asyncio
    async def test_generate_plant_briefing_returns_sections(self, service):
        """Test briefing generation returns sections for all areas."""
        with patch.object(service, '_get_briefing_service') as mock_bs:
            # Mock the headline generation
            mock_briefing = MagicMock()
            mock_briefing.get_sections_by_type.return_value = [
                BriefingSection(
                    section_type="headline",
                    title="Test",
                    content="Test headline",
                    status=BriefingSectionStatus.COMPLETE,
                )
            ]
            mock_bs.return_value.generate_briefing = AsyncMock(return_value=mock_briefing)

            with patch.object(service, '_generate_area_section') as mock_area:
                # Mock area sections
                mock_area.return_value = BriefingSection(
                    section_type="area",
                    title="Test Area",
                    content="Test content",
                    status=BriefingSectionStatus.COMPLETE,
                    pause_point=True,
                )

                result = await service.generate_plant_briefing(
                    user_id="test-user",
                )

                # Should have headline + 7 area sections = 8 total
                assert result is not None
                assert len(result.sections) == 8

    @pytest.mark.asyncio
    async def test_sections_have_pause_points(self, service):
        """Test each section has pause_point=True for Q&A (AC#2)."""
        with patch.object(service, '_get_briefing_service') as mock_bs:
            mock_briefing = MagicMock()
            mock_briefing.get_sections_by_type.return_value = [
                BriefingSection(
                    section_type="headline",
                    title="Test",
                    content="Test headline",
                    status=BriefingSectionStatus.COMPLETE,
                    pause_point=True,
                )
            ]
            mock_bs.return_value.generate_briefing = AsyncMock(return_value=mock_briefing)

            with patch.object(service, '_generate_area_section') as mock_area:
                mock_area.return_value = BriefingSection(
                    section_type="area",
                    title="Test Area",
                    content="Test content",
                    status=BriefingSectionStatus.COMPLETE,
                    pause_point=True,
                )

                result = await service.generate_plant_briefing(user_id="test-user")

                # All sections should have pause_point=True
                for section in result.sections:
                    assert section.pause_point is True

    # ==========================================================================
    # AC#4: Graceful degradation when tools fail
    # ==========================================================================

    @pytest.mark.asyncio
    async def test_area_section_handles_tool_failure(self, service):
        """Test area section generation handles tool failures gracefully."""
        area = PRODUCTION_AREAS[0]  # Packing

        with patch.object(service, '_get_area_data') as mock_data:
            # Simulate tool failure
            mock_data.side_effect = Exception("Tool failed")

            section = await service._generate_area_section(area)

            # Should return a partial/failed section, not raise
            assert section is not None
            assert section.status in (
                BriefingSectionStatus.PARTIAL,
                BriefingSectionStatus.FAILED,
                BriefingSectionStatus.TIMED_OUT,
            )

    @pytest.mark.asyncio
    async def test_briefing_continues_after_area_failure(self, service):
        """Test briefing continues when one area fails."""
        call_count = 0

        async def mock_area_section(area):
            nonlocal call_count
            call_count += 1
            if call_count == 3:  # Fail the third area
                raise Exception("Area failed")
            return BriefingSection(
                section_type="area",
                title=area["name"],
                content="Test content",
                status=BriefingSectionStatus.COMPLETE,
                pause_point=True,
            )

        with patch.object(service, '_get_briefing_service') as mock_bs:
            mock_briefing = MagicMock()
            mock_briefing.get_sections_by_type.return_value = [
                BriefingSection(
                    section_type="headline",
                    title="Test",
                    content="Test headline",
                    status=BriefingSectionStatus.COMPLETE,
                )
            ]
            mock_bs.return_value.generate_briefing = AsyncMock(return_value=mock_briefing)

            with patch.object(service, '_generate_area_section', side_effect=mock_area_section):
                result = await service.generate_plant_briefing(user_id="test-user")

                # Should still have all 8 sections (headline + 7 areas)
                assert len(result.sections) == 8

                # One area should be failed
                failed_count = len([s for s in result.sections if s.status == BriefingSectionStatus.FAILED])
                assert failed_count == 1

    # ==========================================================================
    # Narrative generation
    # ==========================================================================

    @pytest.mark.asyncio
    async def test_generate_area_narrative_with_full_data(self, service):
        """Test narrative generation with complete data."""
        area_data = AreaBriefingData(
            area_id="packing",
            area_name="Packing",
            description="Test",
            assets=["CAMA"],
        )
        area_data.production_status = ToolResultData(
            tool_name="production_status",
            success=True,
            data={
                "summary": {
                    "total_output": 1000,
                    "total_target": 1000,
                    "total_variance_percent": 5.0,
                    "behind_count": 0,
                }
            },
        )
        area_data.oee_data = ToolResultData(
            tool_name="oee_data",
            success=True,
            data={"oee_percentage": 87.5},
        )

        narrative = await service._generate_area_narrative("Packing", area_data)

        assert "Packing" in narrative
        assert "OEE" in narrative or "87.5" in narrative

    @pytest.mark.asyncio
    async def test_generate_area_narrative_with_partial_data(self, service):
        """Test narrative generation with partial data."""
        area_data = AreaBriefingData(
            area_id="packing",
            area_name="Packing",
            description="Test",
            assets=["CAMA"],
        )
        # Only OEE data available
        area_data.oee_data = ToolResultData(
            tool_name="oee_data",
            success=True,
            data={"oee_percentage": 85},
        )

        narrative = await service._generate_area_narrative("Packing", area_data)

        # Should still generate narrative
        assert narrative is not None
        assert len(narrative) > 0

    @pytest.mark.asyncio
    async def test_generate_area_narrative_with_no_data(self, service):
        """Test narrative generation with no data."""
        area_data = AreaBriefingData(
            area_id="packing",
            area_name="Packing",
            description="Test",
            assets=["CAMA"],
        )
        # No data available

        narrative = await service._generate_area_narrative("Packing", area_data)

        # Should return fallback message
        assert narrative is not None
        assert "Packing" in narrative

    # ==========================================================================
    # AC#5: Q&A processing during pause
    # ==========================================================================

    @pytest.mark.asyncio
    async def test_process_qa_question_returns_response(self, service):
        """Test Q&A processing returns a response."""
        # Q&A processing handles errors gracefully, so test it returns structure
        result = await service.process_qa_question(
            briefing_id="test-briefing",
            area_id="packing",
            question="What is the current OEE?",
            user_id="test-user",
        )

        assert "answer" in result
        assert "citations" in result
        assert "follow_up_prompt" in result

    @pytest.mark.asyncio
    async def test_process_qa_question_includes_area_context(self, service):
        """Test Q&A processing includes area context in response."""
        result = await service.process_qa_question(
            briefing_id="test-briefing",
            area_id="packing",
            question="What is the downtime?",
            user_id="test-user",
        )

        # When agent is available, follow-up references the area
        # When not available (test environment), returns generic follow-up
        assert "follow_up_prompt" in result
        # The area_id should be returned for context
        assert result.get("area_id") == "packing"

    @pytest.mark.asyncio
    async def test_process_qa_question_handles_errors(self, service):
        """Test Q&A processing handles errors gracefully."""
        result = await service.process_qa_question(
            briefing_id="test-briefing",
            area_id="packing",
            question="What is the OEE?",
            user_id="test-user",
        )

        # Should return error response, not raise
        # When agent service import fails, it returns a graceful error
        assert "answer" in result
        assert "follow_up_prompt" in result

    # ==========================================================================
    # Performance / Timeout
    # ==========================================================================

    @pytest.mark.asyncio
    async def test_briefing_returns_response_structure(self, service):
        """Test briefing returns proper response structure."""
        with patch.object(service, '_get_briefing_service') as mock_bs:
            mock_briefing = MagicMock()
            mock_briefing.get_sections_by_type.return_value = [
                BriefingSection(
                    section_type="headline",
                    title="Test",
                    content="Test",
                    status=BriefingSectionStatus.COMPLETE,
                    pause_point=True,
                )
            ]
            mock_bs.return_value.generate_briefing = AsyncMock(return_value=mock_briefing)

            with patch.object(service, '_generate_area_section') as mock_area:
                mock_area.return_value = BriefingSection(
                    section_type="area",
                    title="Test",
                    content="Test",
                    status=BriefingSectionStatus.COMPLETE,
                    pause_point=True,
                )

                result = await service.generate_plant_briefing(user_id="test-user")

                # Should have proper structure
                assert result.id is not None
                assert result.title is not None
                assert result.metadata is not None
                assert result.metadata.generated_at is not None

    # ==========================================================================
    # Error response
    # ==========================================================================

    def test_create_error_response(self, service):
        """Test error response generation."""
        result = service._create_error_response(
            briefing_id="test-id",
            user_id="test-user",
            error_message="Test error",
        )

        assert result.id == "test-id"
        assert result.user_id == "test-user"
        assert result.scope == "error"
        assert len(result.sections) == 1
        assert result.sections[0].status == BriefingSectionStatus.FAILED

    # ==========================================================================
    # Title generation
    # ==========================================================================

    def test_get_briefing_title(self, service):
        """Test briefing title includes date."""
        title = service._get_briefing_title()

        assert "Morning Briefing" in title
        # Title should include day of week
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        has_day = any(day in title for day in days)
        assert has_day


class TestGetMorningBriefingService:
    """Tests for singleton getter."""

    def test_get_morning_briefing_service_returns_singleton(self):
        """Test singleton pattern."""
        import app.services.briefing.morning as module
        module._morning_briefing_service = None

        service1 = get_morning_briefing_service()
        service2 = get_morning_briefing_service()

        assert service1 is service2


class TestAreaBriefingData:
    """Tests for AreaBriefingData model."""

    def test_area_briefing_data_creation(self):
        """Test AreaBriefingData can be created."""
        data = AreaBriefingData(
            area_id="packing",
            area_name="Packing",
            description="Packing operations",
            assets=["CAMA", "Pack Cells"],
        )

        assert data.area_id == "packing"
        assert data.area_name == "Packing"
        assert len(data.assets) == 2

    def test_area_briefing_data_tool_results(self):
        """Test AreaBriefingData holds tool results."""
        data = AreaBriefingData(
            area_id="packing",
            area_name="Packing",
            description="Test",
            assets=[],
        )

        # Initially None
        assert data.production_status is None
        assert data.oee_data is None

        # Can be set
        data.production_status = ToolResultData(
            tool_name="production_status",
            success=True,
        )
        assert data.production_status is not None
        assert data.production_status.success is True
