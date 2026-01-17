"""
Tests for Handoff Synthesis Service (Story 9.2)

Comprehensive test coverage for all acceptance criteria:
AC#1: Tool Composition for Synthesis - Orchestrates Production, Downtime, Safety, Alert
AC#2: Narrative Summary Structure - Overview, Issues, Concerns, Focus sections
AC#3: Graceful Degradation - Missing sections show "[Data unavailable]" placeholder
AC#4: Progressive Loading - 15-second timeout with partial results
AC#5: Supervisor Scope Filtering - Filters by assigned assets
AC#6: Citation Compliance - All data includes source citations
AC#7: Shift Time Range Detection - Auto-detects current shift
"""

import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, patch, MagicMock

from app.models.handoff import (
    HandoffSynthesisCitation,
    HandoffSynthesisData,
    HandoffSynthesisMetadata,
    HandoffSynthesisResponse,
    HandoffSection,
    HandoffSectionStatus,
    HandoffToolResultData,
    ShiftTimeRange,
    ShiftType,
)
from app.services.briefing.handoff import (
    HandoffSynthesisService,
    get_handoff_synthesis_service,
    TOTAL_TIMEOUT_SECONDS,
    PER_TOOL_TIMEOUT_SECONDS,
)


# =============================================================================
# Test Fixtures
# =============================================================================


def _utcnow() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


@pytest.fixture
def handoff_synthesis_service():
    """Create an instance of HandoffSynthesisService."""
    return HandoffSynthesisService()


@pytest.fixture
def mock_shift_info():
    """Create mock shift time range."""
    now = _utcnow()
    return ShiftTimeRange(
        shift_type=ShiftType.MORNING,
        start_time=now - timedelta(hours=8),
        end_time=now,
        shift_date=now.date(),
    )


@pytest.fixture
def mock_production_status_result():
    """Create mock production status tool result."""
    return HandoffToolResultData(
        tool_name="production_status",
        success=True,
        data={
            "summary": {
                "total_output": 15000,
                "total_target": 16000,
                "total_variance_percent": -6.25,
                "ahead_count": 2,
                "behind_count": 3,
                "on_track_count": 1,
                "total_assets": 6,
                "assets_needing_attention": ["Asset A", "Asset B", "Asset C"],
            },
            "assets": [
                {"asset_name": "Asset A", "status": "behind", "variance_percent": -15},
                {"asset_name": "Asset B", "status": "behind", "variance_percent": -10},
            ]
        },
        citations=[
            HandoffSynthesisCitation(
                source="supabase",
                table="live_snapshots",
                timestamp=_utcnow(),
            ),
        ],
    )


@pytest.fixture
def mock_downtime_result():
    """Create mock downtime analysis tool result."""
    return HandoffToolResultData(
        tool_name="downtime_analysis",
        success=True,
        data={
            "total_downtime_minutes": 120,
            "total_downtime_hours": 2.0,
            "no_downtime": False,
            "reasons": [
                {"reason_code": "Mechanical Failure", "total_minutes": 60},
                {"reason_code": "Material Shortage", "total_minutes": 45},
                {"reason_code": "Operator Error", "total_minutes": 15},
            ],
            "insight": "Mechanical failures are the primary concern.",
        },
        citations=[
            HandoffSynthesisCitation(
                source="supabase",
                table="downtime_events",
                timestamp=_utcnow(),
            ),
        ],
    )


@pytest.fixture
def mock_downtime_result_no_downtime():
    """Create mock downtime result with no downtime."""
    return HandoffToolResultData(
        tool_name="downtime_analysis",
        success=True,
        data={
            "total_downtime_minutes": 0,
            "total_downtime_hours": 0.0,
            "no_downtime": True,
            "reasons": [],
            "insight": "",
        },
        citations=[],
    )


@pytest.fixture
def mock_safety_events_result():
    """Create mock safety events tool result."""
    return HandoffToolResultData(
        tool_name="safety_events",
        success=True,
        data={
            "total_count": 2,
            "no_incidents": False,
            "summary": {
                "open_count": 1,
                "resolved_count": 1,
                "by_severity": {
                    "critical": 1,
                    "warning": 1,
                },
            },
        },
        citations=[
            HandoffSynthesisCitation(
                source="supabase",
                table="safety_incidents",
                timestamp=_utcnow(),
            ),
        ],
    )


@pytest.fixture
def mock_safety_events_result_clear():
    """Create mock safety events result with no incidents."""
    return HandoffToolResultData(
        tool_name="safety_events",
        success=True,
        data={
            "total_count": 0,
            "no_incidents": True,
            "summary": {
                "open_count": 0,
                "resolved_count": 0,
                "by_severity": {},
            },
        },
        citations=[],
    )


@pytest.fixture
def mock_alert_check_result():
    """Create mock alert check tool result."""
    return HandoffToolResultData(
        tool_name="alert_check",
        success=True,
        data={
            "total_count": 3,
            "count_by_severity": {
                "critical": 1,
                "warning": 2,
            },
            "summary": "3 active alerts require attention",
        },
        citations=[
            HandoffSynthesisCitation(
                source="supabase",
                table="active_alerts",
                timestamp=_utcnow(),
            ),
        ],
    )


@pytest.fixture
def mock_alert_check_result_clear():
    """Create mock alert check result with no alerts."""
    return HandoffToolResultData(
        tool_name="alert_check",
        success=True,
        data={
            "total_count": 0,
            "count_by_severity": {},
            "summary": "No active alerts",
        },
        citations=[],
    )


@pytest.fixture
def mock_failed_tool_result():
    """Create mock failed tool result."""
    return HandoffToolResultData(
        tool_name="production_status",
        success=False,
        data=None,
        error_message="Database connection failed",
        citations=[],
    )


@pytest.fixture
def mock_synthesis_data_all_success(
    mock_production_status_result,
    mock_downtime_result,
    mock_safety_events_result,
    mock_alert_check_result,
):
    """Create mock synthesis data with all tools succeeding."""
    return HandoffSynthesisData(
        production_status=mock_production_status_result,
        downtime_analysis=mock_downtime_result,
        safety_events=mock_safety_events_result,
        alert_check=mock_alert_check_result,
    )


@pytest.fixture
def mock_synthesis_data_partial_failure(
    mock_failed_tool_result,
    mock_downtime_result,
    mock_safety_events_result,
    mock_alert_check_result,
):
    """Create mock synthesis data with one tool failing."""
    return HandoffSynthesisData(
        production_status=mock_failed_tool_result,
        downtime_analysis=mock_downtime_result,
        safety_events=mock_safety_events_result,
        alert_check=mock_alert_check_result,
    )


# =============================================================================
# Test: Service Instantiation
# =============================================================================


class TestHandoffSynthesisServiceInstantiation:
    """Tests for service instantiation."""

    def test_service_can_be_instantiated(self):
        """Service can be instantiated without errors."""
        service = HandoffSynthesisService()
        assert service is not None

    def test_get_singleton_returns_same_instance(self):
        """get_handoff_synthesis_service returns singleton."""
        service1 = get_handoff_synthesis_service()
        service2 = get_handoff_synthesis_service()
        assert service1 is service2


# =============================================================================
# Test: Tool Composition (AC#1)
# =============================================================================


class TestToolComposition:
    """Tests for tool composition (AC#1)."""

    @pytest.mark.asyncio
    async def test_orchestrates_all_four_tools(self, handoff_synthesis_service):
        """AC#1: Orchestrates Production, Downtime, Safety, Alert tools."""
        with patch.object(
            handoff_synthesis_service, '_get_production_status', new_callable=AsyncMock
        ) as mock_prod, patch.object(
            handoff_synthesis_service, '_get_downtime_analysis', new_callable=AsyncMock
        ) as mock_down, patch.object(
            handoff_synthesis_service, '_get_safety_events', new_callable=AsyncMock
        ) as mock_safe, patch.object(
            handoff_synthesis_service, '_get_alert_check', new_callable=AsyncMock
        ) as mock_alert:
            # Set up mock returns
            mock_prod.return_value = HandoffToolResultData(
                tool_name="production_status",
                success=True,
                data={"summary": {}},
            )
            mock_down.return_value = HandoffToolResultData(
                tool_name="downtime_analysis",
                success=True,
                data={"no_downtime": True},
            )
            mock_safe.return_value = HandoffToolResultData(
                tool_name="safety_events",
                success=True,
                data={"no_incidents": True},
            )
            mock_alert.return_value = HandoffToolResultData(
                tool_name="alert_check",
                success=True,
                data={"total_count": 0},
            )

            result = await handoff_synthesis_service.synthesize_shift_data(
                user_id="test-user"
            )

            # Verify all tools were called
            mock_prod.assert_called_once()
            mock_down.assert_called_once()
            mock_safe.assert_called_once()
            mock_alert.assert_called_once()

    @pytest.mark.asyncio
    async def test_tools_run_in_parallel(self, handoff_synthesis_service):
        """AC#1: Tools are run in parallel, not sequentially."""
        call_times = []

        async def mock_tool(*args, **kwargs):
            call_times.append(_utcnow())
            await asyncio.sleep(0.1)  # Simulate work
            return HandoffToolResultData(
                tool_name="test",
                success=True,
                data={},
            )

        with patch.object(
            handoff_synthesis_service, '_get_production_status', side_effect=mock_tool
        ), patch.object(
            handoff_synthesis_service, '_get_downtime_analysis', side_effect=mock_tool
        ), patch.object(
            handoff_synthesis_service, '_get_safety_events', side_effect=mock_tool
        ), patch.object(
            handoff_synthesis_service, '_get_alert_check', side_effect=mock_tool
        ):
            start_time = _utcnow()
            await handoff_synthesis_service.synthesize_shift_data(user_id="test-user")
            end_time = _utcnow()

            # If tools ran in parallel, total time should be ~0.1s
            # If sequential, it would be ~0.4s
            total_time = (end_time - start_time).total_seconds()
            assert total_time < 0.3  # Allow for some overhead


# =============================================================================
# Test: Narrative Summary Structure (AC#2)
# =============================================================================


class TestNarrativeSummaryStructure:
    """Tests for narrative summary structure (AC#2)."""

    @pytest.mark.asyncio
    async def test_generates_four_sections(
        self,
        handoff_synthesis_service,
        mock_synthesis_data_all_success,
    ):
        """AC#2: Generates overview, issues, concerns, focus sections."""
        sections = await handoff_synthesis_service._generate_narrative_sections(
            mock_synthesis_data_all_success
        )

        assert len(sections) == 4

        section_types = [s.section_type for s in sections]
        assert "overview" in section_types
        assert "issues" in section_types
        assert "concerns" in section_types
        assert "focus" in section_types

    @pytest.mark.asyncio
    async def test_overview_section_has_production_data(
        self,
        handoff_synthesis_service,
        mock_synthesis_data_all_success,
    ):
        """AC#2: Overview section includes production status."""
        sections = await handoff_synthesis_service._generate_narrative_sections(
            mock_synthesis_data_all_success
        )

        overview = next(s for s in sections if s.section_type == "overview")
        assert "production" in overview.content.lower() or "target" in overview.content.lower()

    @pytest.mark.asyncio
    async def test_issues_section_has_downtime_data(
        self,
        handoff_synthesis_service,
        mock_synthesis_data_all_success,
    ):
        """AC#2: Issues section includes downtime analysis."""
        sections = await handoff_synthesis_service._generate_narrative_sections(
            mock_synthesis_data_all_success
        )

        issues = next(s for s in sections if s.section_type == "issues")
        assert "downtime" in issues.content.lower() or "hours" in issues.content.lower()

    @pytest.mark.asyncio
    async def test_concerns_section_has_safety_and_alerts(
        self,
        handoff_synthesis_service,
        mock_synthesis_data_all_success,
    ):
        """AC#2: Concerns section includes safety events and alerts."""
        sections = await handoff_synthesis_service._generate_narrative_sections(
            mock_synthesis_data_all_success
        )

        concerns = next(s for s in sections if s.section_type == "concerns")
        content_lower = concerns.content.lower()
        assert "safety" in content_lower or "alert" in content_lower

    @pytest.mark.asyncio
    async def test_focus_section_has_recommendations(
        self,
        handoff_synthesis_service,
        mock_synthesis_data_all_success,
    ):
        """AC#2: Focus section includes prioritized recommendations."""
        sections = await handoff_synthesis_service._generate_narrative_sections(
            mock_synthesis_data_all_success
        )

        focus = next(s for s in sections if s.section_type == "focus")
        assert "Recommended" in focus.title or "Focus" in focus.title


# =============================================================================
# Test: Graceful Degradation (AC#3)
# =============================================================================


class TestGracefulDegradation:
    """Tests for graceful degradation on tool failure (AC#3)."""

    @pytest.mark.asyncio
    async def test_partial_failure_shows_unavailable_placeholder(
        self,
        handoff_synthesis_service,
        mock_synthesis_data_partial_failure,
    ):
        """AC#3: Failed sections show '[Data unavailable]' placeholder."""
        sections = await handoff_synthesis_service._generate_narrative_sections(
            mock_synthesis_data_partial_failure
        )

        overview = next(s for s in sections if s.section_type == "overview")
        assert "[Data unavailable]" in overview.content

    @pytest.mark.asyncio
    async def test_other_sections_still_generated(
        self,
        handoff_synthesis_service,
        mock_synthesis_data_partial_failure,
    ):
        """AC#3: Other sections are still generated despite one failure."""
        sections = await handoff_synthesis_service._generate_narrative_sections(
            mock_synthesis_data_partial_failure
        )

        # All 4 sections should still be present
        assert len(sections) == 4

        # Issues section should have real data (downtime succeeded)
        issues = next(s for s in sections if s.section_type == "issues")
        assert "[Data unavailable]" not in issues.content

    @pytest.mark.asyncio
    async def test_failed_tools_tracked_in_metadata(
        self,
        handoff_synthesis_service,
        mock_failed_tool_result,
    ):
        """AC#3: Failed tools are tracked in metadata."""
        with patch.object(
            handoff_synthesis_service, '_orchestrate_tools', new_callable=AsyncMock
        ) as mock_orch:
            mock_orch.return_value = HandoffSynthesisData(
                production_status=mock_failed_tool_result,
                downtime_analysis=HandoffToolResultData(
                    tool_name="downtime_analysis",
                    success=True,
                    data={"no_downtime": True},
                ),
                safety_events=HandoffToolResultData(
                    tool_name="safety_events",
                    success=True,
                    data={"no_incidents": True},
                ),
                alert_check=HandoffToolResultData(
                    tool_name="alert_check",
                    success=True,
                    data={"total_count": 0},
                ),
            )

            result = await handoff_synthesis_service.synthesize_shift_data(
                user_id="test-user"
            )

            assert "production_status" in result.metadata.tool_failures


# =============================================================================
# Test: Progressive Loading / Timeout (AC#4)
# =============================================================================


class TestProgressiveLoading:
    """Tests for progressive loading and timeout handling (AC#4)."""

    def test_timeout_constant_is_15_seconds(self):
        """AC#4: Overall timeout is 15 seconds."""
        assert TOTAL_TIMEOUT_SECONDS == 15

    def test_per_tool_timeout_is_10_seconds(self):
        """Per-tool timeout is 10 seconds."""
        assert PER_TOOL_TIMEOUT_SECONDS == 10

    @pytest.mark.asyncio
    async def test_timeout_returns_partial_results(self, handoff_synthesis_service):
        """AC#4: Timeout returns partial results with metadata flag."""
        async def slow_tool(*args, **kwargs):
            await asyncio.sleep(20)  # Longer than total timeout
            return HandoffToolResultData(tool_name="test", success=True, data={})

        with patch.object(
            handoff_synthesis_service, '_orchestrate_tools', side_effect=slow_tool
        ):
            result = await handoff_synthesis_service.synthesize_shift_data(
                user_id="test-user"
            )

            assert result.metadata.timed_out is True
            assert result.metadata.partial_result is True

    @pytest.mark.asyncio
    async def test_metadata_tracks_generation_duration(self, handoff_synthesis_service):
        """Metadata includes generation duration in milliseconds."""
        with patch.object(
            handoff_synthesis_service, '_orchestrate_tools', new_callable=AsyncMock
        ) as mock_orch:
            mock_orch.return_value = HandoffSynthesisData()

            result = await handoff_synthesis_service.synthesize_shift_data(
                user_id="test-user"
            )

            assert result.metadata.generation_duration_ms is not None
            assert result.metadata.generation_duration_ms >= 0


# =============================================================================
# Test: Supervisor Scope Filtering (AC#5)
# =============================================================================


class TestSupervisorScopeFiltering:
    """Tests for supervisor scope filtering (AC#5)."""

    @pytest.mark.asyncio
    async def test_accepts_supervisor_assignments(self, handoff_synthesis_service):
        """AC#5: Service accepts supervisor assignments parameter."""
        with patch.object(
            handoff_synthesis_service, '_orchestrate_tools', new_callable=AsyncMock
        ) as mock_orch:
            mock_orch.return_value = HandoffSynthesisData()

            result = await handoff_synthesis_service.synthesize_shift_data(
                user_id="test-user",
                supervisor_assignments=["asset-1", "asset-2"],
            )

            # Verify assignments were passed to orchestration
            mock_orch.assert_called_once()
            call_args = mock_orch.call_args
            assert call_args[0][0] == ["asset-1", "asset-2"]  # First arg is assignments


# =============================================================================
# Test: Citation Compliance (AC#6)
# =============================================================================


class TestCitationCompliance:
    """Tests for citation compliance (AC#6)."""

    @pytest.mark.asyncio
    async def test_response_includes_citations(
        self,
        handoff_synthesis_service,
        mock_synthesis_data_all_success,
    ):
        """AC#6: Response includes citations array."""
        with patch.object(
            handoff_synthesis_service, '_orchestrate_tools', new_callable=AsyncMock
        ) as mock_orch:
            mock_orch.return_value = mock_synthesis_data_all_success

            result = await handoff_synthesis_service.synthesize_shift_data(
                user_id="test-user"
            )

            assert len(result.citations) > 0

    @pytest.mark.asyncio
    async def test_sections_include_citations(
        self,
        handoff_synthesis_service,
        mock_synthesis_data_all_success,
    ):
        """AC#6: Each section includes relevant citations."""
        sections = await handoff_synthesis_service._generate_narrative_sections(
            mock_synthesis_data_all_success
        )

        # At least overview section should have citations from production_status
        overview = next(s for s in sections if s.section_type == "overview")
        assert len(overview.citations) > 0

    @pytest.mark.asyncio
    async def test_citation_has_required_fields(
        self,
        handoff_synthesis_service,
        mock_synthesis_data_all_success,
    ):
        """AC#6: Citations have source, table, and timestamp."""
        with patch.object(
            handoff_synthesis_service, '_orchestrate_tools', new_callable=AsyncMock
        ) as mock_orch:
            mock_orch.return_value = mock_synthesis_data_all_success

            result = await handoff_synthesis_service.synthesize_shift_data(
                user_id="test-user"
            )

            for citation in result.citations:
                assert citation.source is not None
                assert citation.timestamp is not None


# =============================================================================
# Test: Shift Time Range Detection (AC#7)
# =============================================================================


class TestShiftTimeRangeDetection:
    """Tests for shift time range detection (AC#7)."""

    @pytest.mark.asyncio
    async def test_response_includes_shift_info(self, handoff_synthesis_service):
        """AC#7: Response includes detected shift information."""
        with patch.object(
            handoff_synthesis_service, '_orchestrate_tools', new_callable=AsyncMock
        ) as mock_orch:
            mock_orch.return_value = HandoffSynthesisData()

            result = await handoff_synthesis_service.synthesize_shift_data(
                user_id="test-user"
            )

            assert result.shift_info is not None
            assert result.shift_info.shift_type is not None
            assert result.shift_info.start_time is not None
            assert result.shift_info.end_time is not None


# =============================================================================
# Test: Response Structure
# =============================================================================


class TestResponseStructure:
    """Tests for response structure."""

    @pytest.mark.asyncio
    async def test_response_has_unique_id(self, handoff_synthesis_service):
        """Response includes unique synthesis ID."""
        with patch.object(
            handoff_synthesis_service, '_orchestrate_tools', new_callable=AsyncMock
        ) as mock_orch:
            mock_orch.return_value = HandoffSynthesisData()

            result1 = await handoff_synthesis_service.synthesize_shift_data(
                user_id="test-user"
            )
            result2 = await handoff_synthesis_service.synthesize_shift_data(
                user_id="test-user"
            )

            assert result1.id != result2.id

    @pytest.mark.asyncio
    async def test_response_includes_user_id(self, handoff_synthesis_service):
        """Response includes requesting user ID."""
        with patch.object(
            handoff_synthesis_service, '_orchestrate_tools', new_callable=AsyncMock
        ) as mock_orch:
            mock_orch.return_value = HandoffSynthesisData()

            result = await handoff_synthesis_service.synthesize_shift_data(
                user_id="test-user-123"
            )

            assert result.user_id == "test-user-123"

    @pytest.mark.asyncio
    async def test_response_tracks_section_completion(self, handoff_synthesis_service):
        """Response tracks completed vs total sections."""
        with patch.object(
            handoff_synthesis_service, '_orchestrate_tools', new_callable=AsyncMock
        ) as mock_orch:
            mock_orch.return_value = HandoffSynthesisData(
                production_status=HandoffToolResultData(
                    tool_name="production_status",
                    success=True,
                    data={"summary": {}},
                ),
                downtime_analysis=HandoffToolResultData(
                    tool_name="downtime_analysis",
                    success=True,
                    data={"no_downtime": True},
                ),
                safety_events=HandoffToolResultData(
                    tool_name="safety_events",
                    success=True,
                    data={"no_incidents": True},
                ),
                alert_check=HandoffToolResultData(
                    tool_name="alert_check",
                    success=True,
                    data={"total_count": 0},
                ),
            )

            result = await handoff_synthesis_service.synthesize_shift_data(
                user_id="test-user"
            )

            assert result.total_sections == 4
            assert result.completed_sections > 0


# =============================================================================
# Test: Narrative Content Quality
# =============================================================================


class TestNarrativeContentQuality:
    """Tests for narrative content quality."""

    @pytest.mark.asyncio
    async def test_overview_describes_variance(
        self,
        handoff_synthesis_service,
        mock_synthesis_data_all_success,
    ):
        """Overview section describes production variance."""
        sections = await handoff_synthesis_service._generate_narrative_sections(
            mock_synthesis_data_all_success
        )

        overview = next(s for s in sections if s.section_type == "overview")
        # Should mention being behind or ahead
        assert "behind" in overview.content.lower() or "ahead" in overview.content.lower()

    @pytest.mark.asyncio
    async def test_issues_describes_downtime_causes(
        self,
        handoff_synthesis_service,
        mock_synthesis_data_all_success,
    ):
        """Issues section describes downtime causes."""
        sections = await handoff_synthesis_service._generate_narrative_sections(
            mock_synthesis_data_all_success
        )

        issues = next(s for s in sections if s.section_type == "issues")
        # Should mention mechanical failure (top reason)
        assert "mechanical" in issues.content.lower()

    @pytest.mark.asyncio
    async def test_no_downtime_shows_positive_message(
        self,
        handoff_synthesis_service,
        mock_downtime_result_no_downtime,
    ):
        """Issues section shows positive message when no downtime."""
        synthesis_data = HandoffSynthesisData(
            production_status=HandoffToolResultData(
                tool_name="production_status",
                success=True,
                data={"summary": {}},
            ),
            downtime_analysis=mock_downtime_result_no_downtime,
        )

        sections = await handoff_synthesis_service._generate_narrative_sections(
            synthesis_data
        )

        issues = next(s for s in sections if s.section_type == "issues")
        assert "no significant downtime" in issues.content.lower() or "great news" in issues.content.lower()

    @pytest.mark.asyncio
    async def test_concerns_highlights_critical_safety(
        self,
        handoff_synthesis_service,
        mock_synthesis_data_all_success,
    ):
        """Concerns section highlights critical safety issues."""
        sections = await handoff_synthesis_service._generate_narrative_sections(
            mock_synthesis_data_all_success
        )

        concerns = next(s for s in sections if s.section_type == "concerns")
        # Should mention critical or attention
        assert "critical" in concerns.content.lower() or "attention" in concerns.content.lower()

    @pytest.mark.asyncio
    async def test_focus_prioritizes_safety_first(
        self,
        handoff_synthesis_service,
        mock_synthesis_data_all_success,
    ):
        """Focus section prioritizes safety issues."""
        sections = await handoff_synthesis_service._generate_narrative_sections(
            mock_synthesis_data_all_success
        )

        focus = next(s for s in sections if s.section_type == "focus")
        # Safety should be mentioned early in recommendations
        assert "safety" in focus.content.lower()


# =============================================================================
# Test: Error Handling
# =============================================================================


class TestErrorHandling:
    """Tests for error handling scenarios."""

    @pytest.mark.asyncio
    async def test_complete_failure_returns_error_response(
        self,
        handoff_synthesis_service,
    ):
        """Complete orchestration failure returns error response."""
        with patch.object(
            handoff_synthesis_service, '_orchestrate_tools',
            side_effect=RuntimeError("Complete failure")
        ):
            result = await handoff_synthesis_service.synthesize_shift_data(
                user_id="test-user"
            )

            assert result.completed_sections == 0
            assert len(result.sections) == 1
            assert result.sections[0].section_type == "error"
            assert result.sections[0].status == HandoffSectionStatus.FAILED

    @pytest.mark.asyncio
    async def test_individual_tool_timeout_handled(
        self,
        handoff_synthesis_service,
    ):
        """Individual tool timeout is handled gracefully."""
        async def slow_production_tool(*args, **kwargs):
            await asyncio.sleep(15)  # Longer than per-tool timeout
            return HandoffToolResultData(
                tool_name="production_status",
                success=True,
                data={},
            )

        result = await handoff_synthesis_service._run_tool_with_timeout(
            "production_status",
            slow_production_tool,
        )

        assert result.success is False
        assert "timed out" in result.error_message.lower()
