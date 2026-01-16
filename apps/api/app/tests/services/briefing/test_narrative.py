"""
Narrative Generator Tests (Story 8.3)

Tests for the LLM-powered narrative generation including:
- Template-based fallback generation
- LLM integration
- Section formatting

AC#2: Narrative Generation
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.briefing.narrative import (
    NarrativeGenerator,
    get_narrative_generator,
)
from app.models.briefing import (
    BriefingData,
    BriefingSectionStatus,
    ToolResultData,
    BriefingCitation,
)


class TestNarrativeGenerator:
    """Tests for NarrativeGenerator."""

    @pytest.fixture
    def generator(self):
        """Create a test generator without LLM."""
        return NarrativeGenerator(llm_client=None)

    @pytest.fixture
    def sample_briefing_data(self):
        """Create sample briefing data."""
        return BriefingData(
            production_status=ToolResultData(
                tool_name="production_status",
                success=True,
                data={
                    "summary": {
                        "total_output": 145230,
                        "total_target": 150000,
                        "total_variance_percent": -3.2,
                        "ahead_count": 5,
                        "behind_count": 3,
                        "assets_needing_attention": ["Grinder 1", "Roaster 2"],
                    },
                    "assets": [
                        {"asset_name": "Pack Cell 1", "status": "ahead"},
                        {"asset_name": "Pack Cell 2", "status": "ahead"},
                    ],
                },
                citations=[BriefingCitation(source="live_snapshots")],
            ),
            safety_events=ToolResultData(
                tool_name="safety_events",
                success=True,
                data={"total_events": 0},
                citations=[BriefingCitation(source="safety_incidents")],
            ),
            oee_data=ToolResultData(
                tool_name="oee_data",
                success=True,
                data={
                    "oee_percentage": 87.5,
                    "availability": 92.0,
                    "performance": 95.0,
                    "quality": 99.0,
                },
                citations=[BriefingCitation(source="daily_summaries")],
            ),
            downtime_analysis=ToolResultData(
                tool_name="downtime_analysis",
                success=True,
                data={
                    "top_reasons": [
                        {"reason": "Equipment failure", "duration_minutes": 45},
                        {"reason": "Material shortage", "duration_minutes": 20},
                    ],
                },
                citations=[BriefingCitation(source="downtime_events")],
            ),
            action_list=ToolResultData(
                tool_name="action_list",
                success=True,
                data={
                    "actions": [
                        {"title": "Review Grinder 1 performance"},
                        {"title": "Check material inventory"},
                        {"title": "Schedule preventive maintenance"},
                    ],
                },
                citations=[BriefingCitation(source="action_recommendations")],
            ),
        )

    @pytest.mark.asyncio
    async def test_generate_sections_with_template(self, generator, sample_briefing_data):
        """Test section generation using templates."""
        sections = await generator.generate_sections(sample_briefing_data)

        assert len(sections) > 0

        # Should have key sections
        section_types = [s.section_type for s in sections]
        assert "headline" in section_types
        assert "concerns" in section_types
        assert "actions" in section_types

        # All sections should be complete
        for section in sections:
            assert section.status == BriefingSectionStatus.COMPLETE

    @pytest.mark.asyncio
    async def test_generate_sections_with_wins(self, generator, sample_briefing_data):
        """Test wins section generation."""
        sections = await generator.generate_sections(sample_briefing_data)

        wins = [s for s in sections if s.section_type == "wins"]
        assert len(wins) > 0
        assert "ahead" in wins[0].content.lower() or "Pack Cell" in wins[0].content

    @pytest.mark.asyncio
    async def test_generate_sections_no_wins(self, generator):
        """Test when there are no wins to report."""
        data = BriefingData(
            production_status=ToolResultData(
                tool_name="production_status",
                success=True,
                data={
                    "summary": {
                        "ahead_count": 0,
                        "behind_count": 5,
                    },
                    "assets": [],
                },
            ),
        )

        sections = await generator.generate_sections(data)
        wins = [s for s in sections if s.section_type == "wins"]

        # No wins section if no assets ahead
        # (or wins section with "no wins" message)
        assert len(wins) == 0 or "no" in wins[0].content.lower()

    @pytest.mark.asyncio
    async def test_generate_headline_safety_first(self, generator):
        """Test headline mentions safety status."""
        data = BriefingData(
            safety_events=ToolResultData(
                tool_name="safety",
                success=True,
                data={"total_events": 0},
            ),
        )

        headline = generator._generate_headline_template(data)
        assert "safety" in headline.lower() or "good morning" in headline.lower()

    @pytest.mark.asyncio
    async def test_generate_headline_with_incidents(self, generator):
        """Test headline when safety incidents exist."""
        data = BriefingData(
            safety_events=ToolResultData(
                tool_name="safety",
                success=True,
                data={"total_events": 2},
            ),
        )

        headline = generator._generate_headline_template(data)
        assert "2" in headline or "safety" in headline.lower()

    @pytest.mark.asyncio
    async def test_generate_concerns_template(self, generator, sample_briefing_data):
        """Test concerns section generation."""
        concerns = generator._generate_concerns_template(sample_briefing_data)

        assert len(concerns) > 0
        # Should mention assets behind target
        assert "Grinder" in concerns or "behind" in concerns.lower()

    @pytest.mark.asyncio
    async def test_generate_concerns_no_issues(self, generator):
        """Test concerns when no issues exist."""
        data = BriefingData(
            safety_events=ToolResultData(
                tool_name="safety",
                success=True,
                data={"total_events": 0},
            ),
            production_status=ToolResultData(
                tool_name="production",
                success=True,
                data={"summary": {"assets_needing_attention": []}},
            ),
        )

        concerns = generator._generate_concerns_template(data)
        assert "no major concerns" in concerns.lower() or "good work" in concerns.lower()

    @pytest.mark.asyncio
    async def test_generate_actions_template(self, generator, sample_briefing_data):
        """Test actions section generation."""
        actions = generator._generate_actions_template(sample_briefing_data)

        assert len(actions) > 0
        assert "priorities" in actions.lower() or "focus" in actions.lower()

    def test_prepare_data_summary(self, generator, sample_briefing_data):
        """Test data summary preparation for LLM."""
        summary = generator._prepare_data_summary(sample_briefing_data)

        assert len(summary) > 0
        assert "PRODUCTION STATUS" in summary
        assert "SAFETY" in summary
        assert "OEE" in summary
        assert "[Source:" in summary

    def test_prepare_data_summary_empty(self, generator):
        """Test data summary with no data."""
        data = BriefingData()
        summary = generator._prepare_data_summary(data)

        assert summary == "No data available."

    @pytest.mark.asyncio
    async def test_generate_with_llm_success(self, generator):
        """Test LLM generation success."""
        mock_llm = AsyncMock()
        mock_response = MagicMock()
        mock_response.generations = [[MagicMock(text='''
        {
            "headline": {"title": "Test", "content": "Test headline"},
            "wins": {"title": "Wins", "content": "Test wins"},
            "concerns": {"title": "Concerns", "content": "Test concerns"},
            "actions": {"title": "Actions", "content": "Test actions"}
        }
        ''')]]
        mock_llm.agenerate.return_value = mock_response

        generator._llm_client = mock_llm

        data = BriefingData()
        sections = await generator._generate_with_llm("test data", data)

        assert sections is not None
        assert len(sections) == 4
        section_types = [s.section_type for s in sections]
        assert "headline" in section_types
        assert "wins" in section_types

    @pytest.mark.asyncio
    async def test_generate_with_llm_invalid_json(self, generator):
        """Test LLM generation with invalid JSON."""
        mock_llm = AsyncMock()
        mock_response = MagicMock()
        mock_response.generations = [[MagicMock(text="Not valid JSON")]]
        mock_llm.agenerate.return_value = mock_response

        generator._llm_client = mock_llm

        data = BriefingData()
        sections = await generator._generate_with_llm("test data", data)

        # Should return None and fall back to templates
        assert sections is None

    @pytest.mark.asyncio
    async def test_generate_with_llm_exception(self, generator):
        """Test LLM generation exception handling."""
        mock_llm = AsyncMock()
        mock_llm.agenerate.side_effect = Exception("LLM error")

        generator._llm_client = mock_llm

        data = BriefingData()
        sections = await generator._generate_with_llm("test data", data)

        assert sections is None


class TestGetNarrativeGenerator:
    """Tests for singleton getter."""

    def test_get_narrative_generator_returns_singleton(self):
        """Test singleton pattern."""
        import app.services.briefing.narrative as module
        module._narrative_generator = None

        gen1 = get_narrative_generator()
        gen2 = get_narrative_generator()

        assert gen1 is gen2


class TestNarrativeFormatting:
    """Tests for narrative formatting guidelines."""

    @pytest.fixture
    def generator(self):
        return NarrativeGenerator()

    def test_headline_is_conversational(self, generator):
        """Test headline uses conversational tone."""
        data = BriefingData(
            safety_events=ToolResultData(
                tool_name="safety",
                success=True,
                data={"total_events": 0},
            ),
            production_status=ToolResultData(
                tool_name="production",
                success=True,
                data={
                    "summary": {"total_variance_percent": -3.2},
                },
            ),
        )

        headline = generator._generate_headline_template(data)

        # Should not be robotic
        assert "Variance:" not in headline
        # Should be conversational
        assert any(word in headline.lower() for word in ["tracking", "behind", "ahead", "morning", "good"])

    def test_citations_included(self, generator):
        """Test citations are included in sections."""
        data = BriefingData(
            oee_data=ToolResultData(
                tool_name="oee",
                success=True,
                data={"oee_percentage": 87.5},
                citations=[BriefingCitation(source="daily_summaries")],
            ),
        )

        headline = generator._generate_headline_template(data)

        assert "[Source:" in headline

    def test_actions_numbered(self, generator):
        """Test actions are numbered for clarity."""
        data = BriefingData(
            action_list=ToolResultData(
                tool_name="actions",
                success=True,
                data={
                    "actions": [
                        {"title": "First action"},
                        {"title": "Second action"},
                    ],
                },
            ),
        )

        actions = generator._generate_actions_template(data)

        assert "1." in actions
        assert "2." in actions
