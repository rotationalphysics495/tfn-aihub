"""
BriefingService Tests (Story 8.3)

Tests for the briefing synthesis service including:
- Tool orchestration sequence
- Timeout handling
- Graceful tool failure
- Partial response generation

AC#1: Tool Orchestration Sequence
AC#3: 30-Second Timeout Compliance
AC#4: Graceful Tool Failure Handling
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from app.services.briefing.service import (
    BriefingService,
    get_briefing_service,
    TOTAL_TIMEOUT_SECONDS,
    PER_TOOL_TIMEOUT_SECONDS,
)
from app.models.briefing import (
    BriefingScope,
    BriefingSectionStatus,
    ToolResultData,
    BriefingData,
)


class TestBriefingService:
    """Tests for BriefingService."""

    @pytest.fixture
    def service(self):
        """Create a test service."""
        return BriefingService()

    @pytest.fixture
    def mock_tool_result(self):
        """Create a mock successful tool result."""
        return ToolResultData(
            tool_name="test_tool",
            success=True,
            data={"test": "data"},
            citations=[],
        )

    @pytest.fixture
    def mock_failed_tool_result(self):
        """Create a mock failed tool result."""
        return ToolResultData(
            tool_name="test_tool",
            success=False,
            error_message="Tool failed",
        )

    @pytest.mark.asyncio
    async def test_generate_briefing_success(self, service):
        """Test successful briefing generation."""
        # Mock all tools to return success
        with patch.object(service, '_orchestrate_tools') as mock_orchestrate:
            mock_orchestrate.return_value = BriefingData(
                production_status=ToolResultData(
                    tool_name="production_status",
                    success=True,
                    data={"summary": {"total_output": 1000, "total_target": 1000}},
                ),
                safety_events=ToolResultData(
                    tool_name="safety_events",
                    success=True,
                    data={"total_events": 0},
                ),
            )

            with patch.object(service, '_generate_narrative_sections') as mock_narrative:
                from app.models.briefing import BriefingSection
                mock_narrative.return_value = [
                    BriefingSection(
                        section_type="headline",
                        title="Test",
                        content="Test content",
                        status=BriefingSectionStatus.COMPLETE,
                    )
                ]

                result = await service.generate_briefing(
                    user_id="test-user",
                    scope=BriefingScope.PLANT_WIDE,
                )

                assert result is not None
                assert result.id is not None
                assert result.user_id == "test-user"
                assert len(result.sections) > 0
                assert not result.metadata.timed_out

    @pytest.mark.asyncio
    async def test_generate_briefing_with_tool_failure(self, service):
        """Test briefing generation with tool failure (AC#4)."""
        with patch.object(service, '_orchestrate_tools') as mock_orchestrate:
            mock_orchestrate.return_value = BriefingData(
                production_status=ToolResultData(
                    tool_name="production_status",
                    success=False,
                    error_message="Tool failed",
                ),
                safety_events=ToolResultData(
                    tool_name="safety_events",
                    success=True,
                    data={"total_events": 0},
                ),
            )

            with patch.object(service, '_generate_narrative_sections') as mock_narrative:
                from app.models.briefing import BriefingSection
                mock_narrative.return_value = [
                    BriefingSection(
                        section_type="headline",
                        title="Test",
                        content="Test content",
                        status=BriefingSectionStatus.COMPLETE,
                    )
                ]

                result = await service.generate_briefing(
                    user_id="test-user",
                    scope=BriefingScope.PLANT_WIDE,
                )

                # Should still return a response
                assert result is not None
                assert "production_status" in result.metadata.tool_failures

    @pytest.mark.asyncio
    async def test_generate_briefing_timeout(self, service):
        """Test briefing generation timeout (AC#3)."""
        async def slow_orchestrate(*args, **kwargs):
            await asyncio.sleep(35)  # Exceed timeout
            return BriefingData()

        with patch.object(service, '_orchestrate_tools', side_effect=slow_orchestrate):
            result = await service.generate_briefing(
                user_id="test-user",
                scope=BriefingScope.PLANT_WIDE,
            )

            # Should return partial response
            assert result is not None
            assert result.metadata.timed_out is True

    @pytest.mark.asyncio
    async def test_orchestrate_tools_parallel(self, service):
        """Test tools run in parallel (AC#1)."""
        call_times = []

        async def track_call(name, *args, **kwargs):
            call_times.append((name, asyncio.get_event_loop().time()))
            await asyncio.sleep(0.1)
            return ToolResultData(tool_name=name, success=True, data={})

        with patch.object(service, '_run_tool_with_timeout', side_effect=track_call):
            await service._orchestrate_tools(area_id=None)

            # All tools should start nearly simultaneously
            if len(call_times) >= 2:
                time_diff = abs(call_times[0][1] - call_times[-1][1])
                # Should all start within 0.5 seconds of each other
                assert time_diff < 0.5

    @pytest.mark.asyncio
    async def test_run_tool_with_timeout_success(self, service):
        """Test tool runs successfully within timeout."""
        async def fast_tool(*args):
            return ToolResultData(tool_name="fast", success=True, data={"result": "ok"})

        result = await service._run_tool_with_timeout("fast", fast_tool)

        assert result.success is True
        assert result.data == {"result": "ok"}

    @pytest.mark.asyncio
    async def test_run_tool_with_timeout_exceeds(self, service):
        """Test tool timeout handling."""
        async def slow_tool(*args):
            await asyncio.sleep(10)  # Exceeds per-tool timeout
            return ToolResultData(tool_name="slow", success=True, data={})

        result = await service._run_tool_with_timeout("slow", slow_tool)

        assert result.success is False
        assert "timed out" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_run_tool_with_timeout_exception(self, service):
        """Test tool exception handling."""
        async def failing_tool(*args):
            raise ValueError("Tool crashed")

        result = await service._run_tool_with_timeout("failing", failing_tool)

        assert result.success is False
        assert "Tool crashed" in result.error_message

    @pytest.mark.asyncio
    async def test_create_fallback_sections(self, service):
        """Test fallback section generation."""
        briefing_data = BriefingData(
            production_status=ToolResultData(
                tool_name="production_status",
                success=True,
                data={
                    "summary": {
                        "total_output": 1000,
                        "total_target": 1000,
                        "behind_count": 2,
                    }
                },
            ),
            safety_events=ToolResultData(
                tool_name="safety_events",
                success=True,
                data={"total_events": 0},
            ),
        )

        sections = service._create_fallback_sections(briefing_data)

        assert len(sections) > 0
        # Should have headline and production sections at minimum
        section_types = [s.section_type for s in sections]
        assert "headline" in section_types

    def test_get_briefing_title_plant_wide(self, service):
        """Test briefing title for plant-wide scope."""
        title = service._get_briefing_title(BriefingScope.PLANT_WIDE)

        assert "Morning Briefing" in title

    def test_get_briefing_title_supervisor(self, service):
        """Test briefing title for supervisor scope."""
        title = service._get_briefing_title(BriefingScope.SUPERVISOR, area_id="Grinding")

        assert "Grinding" in title
        assert "Briefing" in title

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


class TestGetBriefingService:
    """Tests for singleton getter."""

    def test_get_briefing_service_returns_singleton(self):
        """Test singleton pattern."""
        import app.services.briefing.service as module
        module._briefing_service = None

        service1 = get_briefing_service()
        service2 = get_briefing_service()

        assert service1 is service2


class TestBriefingData:
    """Tests for BriefingData model."""

    def test_all_citations_aggregation(self):
        """Test citation aggregation from all tools."""
        from app.models.briefing import BriefingCitation

        data = BriefingData(
            production_status=ToolResultData(
                tool_name="prod",
                success=True,
                citations=[BriefingCitation(source="live_snapshots")],
            ),
            safety_events=ToolResultData(
                tool_name="safety",
                success=True,
                citations=[BriefingCitation(source="safety_incidents")],
            ),
        )

        all_citations = data.all_citations
        assert len(all_citations) == 2
        sources = [c.source for c in all_citations]
        assert "live_snapshots" in sources
        assert "safety_incidents" in sources

    def test_successful_tools_list(self):
        """Test successful tools tracking."""
        data = BriefingData(
            production_status=ToolResultData(tool_name="prod", success=True),
            safety_events=ToolResultData(tool_name="safety", success=False),
            oee_data=ToolResultData(tool_name="oee", success=True),
        )

        successful = data.successful_tools
        assert "production_status" in successful
        assert "oee_data" in successful
        assert "safety_events" not in successful

    def test_failed_tools_list(self):
        """Test failed tools tracking."""
        data = BriefingData(
            production_status=ToolResultData(tool_name="prod", success=False),
            safety_events=ToolResultData(tool_name="safety", success=True),
        )

        failed = data.failed_tools
        assert "production_status" in failed
        assert "safety_events" not in failed
