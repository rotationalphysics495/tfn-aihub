"""
Tests for Memory Recall Tool (Story 7.1)

Comprehensive test coverage for all acceptance criteria:
AC#1: Topic-Based Memory Recall - Summary, decisions, dates, related topics
AC#2: Time-Range Memory Query - Category grouping, unresolved items
AC#3: No Memory Found Handling - Clear message, no hallucination
AC#4: Stale Memory Notification - Warning for >30 day old memories
AC#5: Memory Provenance & Citations - memory_id, timestamps, relevance scores
AC#6: Performance Requirements - <2s response, no caching
"""

import pytest
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.agent import (
    MemoryCitation,
    MemoryRecallInput,
    MemoryRecallOutput,
    RecalledMemory,
)
from app.services.agent.base import Citation, ToolResult
from app.services.agent.tools.memory_recall import (
    MemoryRecallTool,
    RELEVANCE_THRESHOLD,
    STALE_THRESHOLD_DAYS,
    UNRESOLVED_PATTERNS,
    set_current_user_id,
    get_current_user_id,
    _utcnow,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def memory_recall_tool():
    """Create an instance of MemoryRecallTool."""
    return MemoryRecallTool()


@pytest.fixture
def mock_user_id():
    """Set and return a mock user ID."""
    user_id = "test-user-123"
    set_current_user_id(user_id)
    return user_id


@pytest.fixture
def mock_memories_recent():
    """Create mock memory objects - recent (within 30 days)."""
    now = _utcnow()
    return [
        {
            "id": "mem-001",
            "memory": "Discussed Grinder 5 blade change schedule - concluded SOP review needed",
            "score": 0.92,
            "metadata": {
                "timestamp": (now - timedelta(days=5)).isoformat(),
                "asset_id": "grinder-5",
                "topic": "maintenance",
            },
        },
        {
            "id": "mem-002",
            "memory": "Output variance during shift changes - still monitoring the situation",
            "score": 0.85,
            "metadata": {
                "timestamp": (now - timedelta(days=3)).isoformat(),
                "asset_id": "grinder-5",
                "topic": "production",
            },
        },
        {
            "id": "mem-003",
            "memory": "Safety stop incident on Grinder 5 - resolved, lockout procedure updated",
            "score": 0.78,
            "metadata": {
                "timestamp": (now - timedelta(days=7)).isoformat(),
                "asset_id": "grinder-5",
                "topic": "safety",
            },
        },
    ]


@pytest.fixture
def mock_memories_stale():
    """Create mock memory objects - stale (>30 days old)."""
    now = _utcnow()
    return [
        {
            "id": "mem-old-001",
            "memory": "Previous maintenance schedule for Grinder 5 - decided quarterly check",
            "score": 0.88,
            "metadata": {
                "timestamp": (now - timedelta(days=45)).isoformat(),
                "asset_id": "grinder-5",
                "topic": "maintenance",
            },
        },
        {
            "id": "mem-old-002",
            "memory": "Old production targets discussed - pending review",
            "score": 0.75,
            "metadata": {
                "timestamp": (now - timedelta(days=60)).isoformat(),
                "asset_id": "grinder-5",
                "topic": "production",
            },
        },
    ]


@pytest.fixture
def mock_memories_mixed_relevance():
    """Create mock memories with mixed relevance scores."""
    now = _utcnow()
    return [
        {"id": "mem-high", "memory": "High relevance memory", "score": 0.95,
         "metadata": {"timestamp": now.isoformat()}},
        {"id": "mem-medium", "memory": "Medium relevance memory", "score": 0.75,
         "metadata": {"timestamp": now.isoformat()}},
        {"id": "mem-low", "memory": "Low relevance memory", "score": 0.5,
         "metadata": {"timestamp": now.isoformat()}},
        {"id": "mem-very-low", "memory": "Very low relevance", "score": 0.3,
         "metadata": {"timestamp": now.isoformat()}},
    ]


# =============================================================================
# Test: Tool Properties
# =============================================================================


class TestMemoryRecallToolProperties:
    """Tests for tool class properties."""

    def test_tool_name(self, memory_recall_tool):
        """Tool name is 'memory_recall'."""
        assert memory_recall_tool.name == "memory_recall"

    def test_tool_description_for_intent_matching(self, memory_recall_tool):
        """Tool description enables correct intent matching."""
        description = memory_recall_tool.description.lower()
        assert "recall" in description or "retrieve" in description
        assert "past" in description or "previous" in description
        assert "conversations" in description or "discussions" in description

    def test_tool_args_schema(self, memory_recall_tool):
        """Args schema is MemoryRecallInput."""
        assert memory_recall_tool.args_schema == MemoryRecallInput

    def test_tool_citations_required(self, memory_recall_tool):
        """Citations are required."""
        assert memory_recall_tool.citations_required is True


# =============================================================================
# Test: Input Schema Validation
# =============================================================================


class TestMemoryRecallInput:
    """Tests for MemoryRecallInput validation."""

    def test_valid_input_minimal(self):
        """Test valid input with minimal required fields."""
        input_model = MemoryRecallInput(query="Grinder 5")
        assert input_model.query == "Grinder 5"
        assert input_model.asset_id is None
        assert input_model.time_range_days is None
        assert input_model.max_results == 5

    def test_valid_input_all_fields(self):
        """Test valid input with all fields."""
        input_model = MemoryRecallInput(
            query="maintenance issues",
            asset_id="grinder-5",
            time_range_days=30,
            max_results=10
        )
        assert input_model.query == "maintenance issues"
        assert input_model.asset_id == "grinder-5"
        assert input_model.time_range_days == 30
        assert input_model.max_results == 10

    def test_max_results_bounds(self):
        """Test max_results validation."""
        # Valid ranges
        assert MemoryRecallInput(query="test", max_results=1).max_results == 1
        assert MemoryRecallInput(query="test", max_results=20).max_results == 20

        # Default value
        assert MemoryRecallInput(query="test").max_results == 5


# =============================================================================
# Test: Topic-Based Memory Recall (AC#1)
# =============================================================================


class TestTopicBasedMemoryRecall:
    """Tests for AC#1: Topic-Based Memory Recall."""

    @pytest.mark.asyncio
    async def test_basic_recall_returns_success(
        self,
        memory_recall_tool,
        mock_user_id,
        mock_memories_recent,
    ):
        """AC#1: Successful basic query returns all expected data."""
        with patch.object(
            memory_recall_tool, "_get_memory_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.is_configured.return_value = True
            mock_service.search_memory = AsyncMock(return_value=mock_memories_recent)
            mock_get_service.return_value = mock_service

            result = await memory_recall_tool._arun(query="Grinder 5")

            assert result.success is True
            assert result.data is not None
            assert result.data["query"] == "Grinder 5"

    @pytest.mark.asyncio
    async def test_recall_includes_summary(
        self,
        memory_recall_tool,
        mock_user_id,
        mock_memories_recent,
    ):
        """AC#1: Response includes summary of past conversations."""
        with patch.object(
            memory_recall_tool, "_get_memory_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.is_configured.return_value = True
            mock_service.search_memory = AsyncMock(return_value=mock_memories_recent)
            mock_get_service.return_value = mock_service

            result = await memory_recall_tool._arun(query="Grinder 5")

            assert result.data["summary"] is not None
            assert "Grinder 5" in result.data["summary"]
            assert "conversation" in result.data["summary"].lower()

    @pytest.mark.asyncio
    async def test_recall_includes_related_topics(
        self,
        memory_recall_tool,
        mock_user_id,
        mock_memories_recent,
    ):
        """AC#1: Response includes links to related topics."""
        with patch.object(
            memory_recall_tool, "_get_memory_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.is_configured.return_value = True
            mock_service.search_memory = AsyncMock(return_value=mock_memories_recent)
            mock_get_service.return_value = mock_service

            result = await memory_recall_tool._arun(query="Grinder 5")

            assert "related_topics" in result.data
            assert len(result.data["related_topics"]) > 0

    @pytest.mark.asyncio
    async def test_memories_sorted_by_relevance_then_recency(
        self,
        memory_recall_tool,
        mock_user_id,
        mock_memories_recent,
    ):
        """AC#1: Results are sorted by relevance, then recency."""
        with patch.object(
            memory_recall_tool, "_get_memory_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.is_configured.return_value = True
            mock_service.search_memory = AsyncMock(return_value=mock_memories_recent)
            mock_get_service.return_value = mock_service

            result = await memory_recall_tool._arun(query="Grinder 5")

            memories = result.data["memories"]
            # First memory should have highest relevance score
            assert memories[0]["relevance_score"] >= memories[1]["relevance_score"]


# =============================================================================
# Test: Time-Range Memory Query (AC#2)
# =============================================================================


class TestTimeRangeMemoryQuery:
    """Tests for AC#2: Time-Range Memory Query."""

    @pytest.mark.asyncio
    async def test_time_range_filter_applied(
        self,
        memory_recall_tool,
        mock_user_id,
    ):
        """AC#2: Time range filter is applied correctly."""
        now = _utcnow()
        memories = [
            {"id": "recent", "memory": "Recent discussion", "score": 0.9,
             "metadata": {"timestamp": (now - timedelta(days=3)).isoformat()}},
            {"id": "old", "memory": "Old discussion", "score": 0.85,
             "metadata": {"timestamp": (now - timedelta(days=10)).isoformat()}},
        ]

        with patch.object(
            memory_recall_tool, "_get_memory_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.is_configured.return_value = True
            mock_service.search_memory = AsyncMock(return_value=memories)
            mock_get_service.return_value = mock_service

            result = await memory_recall_tool._arun(
                query="test",
                time_range_days=7  # Only get last 7 days
            )

            # Should only return the recent memory
            assert len(result.data["memories"]) == 1
            assert result.data["memories"][0]["memory_id"] == "recent"

    @pytest.mark.asyncio
    async def test_unresolved_items_extracted(
        self,
        memory_recall_tool,
        mock_user_id,
        mock_memories_recent,
    ):
        """AC#2: Highlights unresolved items."""
        with patch.object(
            memory_recall_tool, "_get_memory_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.is_configured.return_value = True
            mock_service.search_memory = AsyncMock(return_value=mock_memories_recent)
            mock_get_service.return_value = mock_service

            result = await memory_recall_tool._arun(query="Grinder 5")

            # Should extract "still monitoring" from the output variance memory
            assert "unresolved_items" in result.data
            assert len(result.data["unresolved_items"]) > 0

    @pytest.mark.asyncio
    async def test_memories_grouped_by_topic(
        self,
        memory_recall_tool,
        mock_user_id,
        mock_memories_recent,
    ):
        """AC#2: Groups conversations by topic area."""
        with patch.object(
            memory_recall_tool, "_get_memory_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.is_configured.return_value = True
            mock_service.search_memory = AsyncMock(return_value=mock_memories_recent)
            mock_get_service.return_value = mock_service

            result = await memory_recall_tool._arun(query="Grinder 5")

            # Should have related topics extracted from different memory categories
            related_topics = result.data["related_topics"]
            # Check that topic categories are extracted
            topic_names = [t.lower() for t in related_topics if not t.startswith("Asset:")]
            assert len(topic_names) > 0


# =============================================================================
# Test: No Memory Found Handling (AC#3)
# =============================================================================


class TestNoMemoryFoundHandling:
    """Tests for AC#3: No Memory Found Handling."""

    @pytest.mark.asyncio
    async def test_no_memories_returns_clear_message(
        self,
        memory_recall_tool,
        mock_user_id,
    ):
        """AC#3: States 'I don't have any previous conversations about [topic]'."""
        with patch.object(
            memory_recall_tool, "_get_memory_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.is_configured.return_value = True
            mock_service.search_memory = AsyncMock(return_value=[])
            mock_get_service.return_value = mock_service

            result = await memory_recall_tool._arun(query="nonexistent topic")

            assert result.success is True
            assert result.data["no_memories_found"] is True
            assert "don't have any previous conversations" in result.data["summary"]
            assert "nonexistent topic" in result.data["summary"]

    @pytest.mark.asyncio
    async def test_no_memories_offers_fresh_inquiry(
        self,
        memory_recall_tool,
        mock_user_id,
    ):
        """AC#3: Offers to help with a fresh inquiry."""
        with patch.object(
            memory_recall_tool, "_get_memory_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.is_configured.return_value = True
            mock_service.search_memory = AsyncMock(return_value=[])
            mock_get_service.return_value = mock_service

            result = await memory_recall_tool._arun(query="test topic")

            # Should have follow-up suggestions
            assert "follow_up_questions" in result.metadata
            follow_ups = result.metadata["follow_up_questions"]
            assert len(follow_ups) > 0

    @pytest.mark.asyncio
    async def test_no_memories_empty_lists(
        self,
        memory_recall_tool,
        mock_user_id,
    ):
        """AC#3: Empty memories list when no results."""
        with patch.object(
            memory_recall_tool, "_get_memory_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.is_configured.return_value = True
            mock_service.search_memory = AsyncMock(return_value=[])
            mock_get_service.return_value = mock_service

            result = await memory_recall_tool._arun(query="test")

            assert len(result.data["memories"]) == 0
            assert len(result.data["unresolved_items"]) == 0
            assert len(result.data["citations"]) == 0


# =============================================================================
# Test: Stale Memory Notification (AC#4)
# =============================================================================


class TestStaleMemoryNotification:
    """Tests for AC#4: Stale Memory Notification."""

    @pytest.mark.asyncio
    async def test_stale_memory_flagged(
        self,
        memory_recall_tool,
        mock_user_id,
        mock_memories_stale,
    ):
        """AC#4: Old memories (>30 days) are flagged as stale."""
        with patch.object(
            memory_recall_tool, "_get_memory_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.is_configured.return_value = True
            mock_service.search_memory = AsyncMock(return_value=mock_memories_stale)
            mock_get_service.return_value = mock_service

            result = await memory_recall_tool._arun(query="Grinder 5")

            # All memories should be marked as stale
            for memory in result.data["memories"]:
                assert memory["is_stale"] is True

    @pytest.mark.asyncio
    async def test_stale_memory_includes_note(
        self,
        memory_recall_tool,
        mock_user_id,
        mock_memories_stale,
    ):
        """AC#4: Response includes note about stale memories."""
        with patch.object(
            memory_recall_tool, "_get_memory_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.is_configured.return_value = True
            mock_service.search_memory = AsyncMock(return_value=mock_memories_stale)
            mock_get_service.return_value = mock_service

            result = await memory_recall_tool._arun(query="Grinder 5")

            assert result.data["has_stale_memories"] is True
            assert result.data["stale_memory_note"] is not None
            assert "days ago" in result.data["stale_memory_note"]
            assert "may have changed" in result.data["stale_memory_note"]

    @pytest.mark.asyncio
    async def test_stale_threshold_is_30_days(
        self,
        memory_recall_tool,
        mock_user_id,
    ):
        """AC#4: Stale threshold is 30 days."""
        now = _utcnow()
        memories = [
            {"id": "just-fresh", "memory": "Just fresh memory", "score": 0.9,
             "metadata": {"timestamp": (now - timedelta(days=29)).isoformat()}},
            {"id": "just-stale", "memory": "Just stale memory", "score": 0.85,
             "metadata": {"timestamp": (now - timedelta(days=31)).isoformat()}},
        ]

        with patch.object(
            memory_recall_tool, "_get_memory_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.is_configured.return_value = True
            mock_service.search_memory = AsyncMock(return_value=memories)
            mock_get_service.return_value = mock_service

            result = await memory_recall_tool._arun(query="test")

            # Check each memory's staleness
            memory_by_id = {m["memory_id"]: m for m in result.data["memories"]}
            assert memory_by_id["just-fresh"]["is_stale"] is False
            assert memory_by_id["just-stale"]["is_stale"] is True


# =============================================================================
# Test: Memory Provenance & Citations (AC#5)
# =============================================================================


class TestMemoryProvenanceCitations:
    """Tests for AC#5: Memory Provenance & Citations."""

    @pytest.mark.asyncio
    async def test_memory_includes_memory_id(
        self,
        memory_recall_tool,
        mock_user_id,
        mock_memories_recent,
    ):
        """AC#5: All recalled memories include memory_id."""
        with patch.object(
            memory_recall_tool, "_get_memory_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.is_configured.return_value = True
            mock_service.search_memory = AsyncMock(return_value=mock_memories_recent)
            mock_get_service.return_value = mock_service

            result = await memory_recall_tool._arun(query="Grinder 5")

            for memory in result.data["memories"]:
                assert "memory_id" in memory
                assert memory["memory_id"] is not None

    @pytest.mark.asyncio
    async def test_memory_includes_timestamp(
        self,
        memory_recall_tool,
        mock_user_id,
        mock_memories_recent,
    ):
        """AC#5: Timestamps are displayed in user-friendly format."""
        with patch.object(
            memory_recall_tool, "_get_memory_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.is_configured.return_value = True
            mock_service.search_memory = AsyncMock(return_value=mock_memories_recent)
            mock_get_service.return_value = mock_service

            result = await memory_recall_tool._arun(query="Grinder 5")

            for memory in result.data["memories"]:
                assert "created_at" in memory
                # Should be ISO format string after serialization
                assert memory["created_at"] is not None

    @pytest.mark.asyncio
    async def test_memory_includes_relevance_score(
        self,
        memory_recall_tool,
        mock_user_id,
        mock_memories_recent,
    ):
        """AC#5: Each memory includes confidence/relevance score."""
        with patch.object(
            memory_recall_tool, "_get_memory_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.is_configured.return_value = True
            mock_service.search_memory = AsyncMock(return_value=mock_memories_recent)
            mock_get_service.return_value = mock_service

            result = await memory_recall_tool._arun(query="Grinder 5")

            for memory in result.data["memories"]:
                assert "relevance_score" in memory
                assert 0.0 <= memory["relevance_score"] <= 1.0

    @pytest.mark.asyncio
    async def test_citations_generated_for_each_memory(
        self,
        memory_recall_tool,
        mock_user_id,
        mock_memories_recent,
    ):
        """AC#5: Citations are generated for each memory."""
        with patch.object(
            memory_recall_tool, "_get_memory_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.is_configured.return_value = True
            mock_service.search_memory = AsyncMock(return_value=mock_memories_recent)
            mock_get_service.return_value = mock_service

            result = await memory_recall_tool._arun(query="Grinder 5")

            # Should have citations for each memory
            assert len(result.citations) == len(result.data["memories"])
            assert len(result.data["citations"]) == len(result.data["memories"])

    @pytest.mark.asyncio
    async def test_citation_format_matches_story_4_5(
        self,
        memory_recall_tool,
        mock_user_id,
        mock_memories_recent,
    ):
        """AC#5: Citation format matches Story 4-5 standards."""
        with patch.object(
            memory_recall_tool, "_get_memory_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.is_configured.return_value = True
            mock_service.search_memory = AsyncMock(return_value=mock_memories_recent)
            mock_get_service.return_value = mock_service

            result = await memory_recall_tool._arun(query="Grinder 5")

            for citation in result.data["citations"]:
                assert citation["source_type"] == "memory"
                assert "memory_id" in citation
                assert "timestamp" in citation
                assert "display_text" in citation


# =============================================================================
# Test: Performance Requirements (AC#6)
# =============================================================================


class TestPerformanceRequirements:
    """Tests for AC#6: Performance Requirements."""

    @pytest.mark.asyncio
    async def test_no_caching_applied(
        self,
        memory_recall_tool,
        mock_user_id,
        mock_memories_recent,
    ):
        """AC#6: No caching (always fetch fresh for accuracy)."""
        with patch.object(
            memory_recall_tool, "_get_memory_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.is_configured.return_value = True
            mock_service.search_memory = AsyncMock(return_value=mock_memories_recent)
            mock_get_service.return_value = mock_service

            result = await memory_recall_tool._arun(query="Grinder 5")

            # Should indicate no caching
            assert result.metadata.get("cache_tier") == "none"


# =============================================================================
# Test: Relevance Threshold Filtering
# =============================================================================


class TestRelevanceThresholdFiltering:
    """Tests for relevance threshold filtering."""

    @pytest.mark.asyncio
    async def test_low_relevance_filtered_by_service(
        self,
        memory_recall_tool,
        mock_user_id,
    ):
        """Test that service filters by relevance threshold."""
        with patch.object(
            memory_recall_tool, "_get_memory_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.is_configured.return_value = True
            # Service should receive threshold parameter
            mock_service.search_memory = AsyncMock(return_value=[])
            mock_get_service.return_value = mock_service

            await memory_recall_tool._arun(query="test")

            # Verify threshold was passed to search
            call_args = mock_service.search_memory.call_args
            assert call_args.kwargs.get("threshold") == RELEVANCE_THRESHOLD


# =============================================================================
# Test: Asset ID Filtering
# =============================================================================


class TestAssetIdFiltering:
    """Tests for asset ID filtering."""

    @pytest.mark.asyncio
    async def test_asset_id_passed_to_service(
        self,
        memory_recall_tool,
        mock_user_id,
    ):
        """Test that asset_id filter is passed to memory service."""
        with patch.object(
            memory_recall_tool, "_get_memory_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.is_configured.return_value = True
            mock_service.search_memory = AsyncMock(return_value=[])
            mock_get_service.return_value = mock_service

            await memory_recall_tool._arun(query="issues", asset_id="grinder-5")

            # Verify asset_id was passed to search
            call_args = mock_service.search_memory.call_args
            assert call_args.kwargs.get("asset_id") == "grinder-5"


# =============================================================================
# Test: Error Handling
# =============================================================================


class TestErrorHandling:
    """Tests for error handling scenarios."""

    @pytest.mark.asyncio
    async def test_memory_service_not_configured(
        self,
        memory_recall_tool,
        mock_user_id,
    ):
        """Graceful handling when memory service not configured."""
        with patch.object(
            memory_recall_tool, "_get_memory_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.is_configured.return_value = False
            mock_get_service.return_value = mock_service

            result = await memory_recall_tool._arun(query="test")

            assert result.success is True
            assert result.data["no_memories_found"] is True
            assert "not configured" in result.data["summary"]

    @pytest.mark.asyncio
    async def test_memory_service_exception_handled(
        self,
        memory_recall_tool,
        mock_user_id,
    ):
        """Unexpected exceptions are caught and logged."""
        with patch.object(
            memory_recall_tool, "_get_memory_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.is_configured.return_value = True
            mock_service.search_memory = AsyncMock(
                side_effect=RuntimeError("Unexpected error")
            )
            mock_get_service.return_value = mock_service

            result = await memory_recall_tool._arun(query="test")

            assert result.success is False
            assert result.error_message is not None
            assert "unexpected error" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_no_user_id_graceful_handling(
        self,
        memory_recall_tool,
    ):
        """Graceful handling when user_id not available."""
        # Clear the user context
        set_current_user_id(None)

        result = await memory_recall_tool._arun(query="test")

        # Should return success with no memories message
        assert result.success is True
        assert result.data["no_memories_found"] is True


# =============================================================================
# Test: Tool Registration
# =============================================================================


class TestToolRegistration:
    """Tests for tool registration with the registry."""

    def test_tool_can_be_instantiated(self):
        """Tool can be instantiated without errors."""
        tool = MemoryRecallTool()
        assert tool is not None
        assert tool.name == "memory_recall"

    def test_tool_is_manufacturing_tool(self):
        """Tool extends ManufacturingTool."""
        tool = MemoryRecallTool()
        from app.services.agent.base import ManufacturingTool

        assert isinstance(tool, ManufacturingTool)


# =============================================================================
# Test: Summary Generation
# =============================================================================


class TestSummaryGeneration:
    """Tests for memory summary generation."""

    def test_generate_summary_single_memory(self, memory_recall_tool):
        """Summary for single memory."""
        now = _utcnow()
        memories = [
            RecalledMemory(
                memory_id="mem-1",
                content="Test memory",
                created_at=now - timedelta(days=3),
                relevance_score=0.9,
                asset_id=None,
                topic_category=None,
                is_stale=False,
                days_ago=3,
            )
        ]

        summary = memory_recall_tool._generate_summary(memories, "test topic")

        assert "1 relevant conversation" in summary
        assert "test topic" in summary

    def test_generate_summary_multiple_memories(self, memory_recall_tool):
        """Summary for multiple memories."""
        now = _utcnow()
        memories = [
            RecalledMemory(
                memory_id="mem-1",
                content="Memory 1",
                created_at=now - timedelta(days=1),
                relevance_score=0.9,
                asset_id=None,
                topic_category=None,
                is_stale=False,
                days_ago=1,
            ),
            RecalledMemory(
                memory_id="mem-2",
                content="Memory 2",
                created_at=now - timedelta(days=5),
                relevance_score=0.85,
                asset_id=None,
                topic_category=None,
                is_stale=False,
                days_ago=5,
            ),
        ]

        summary = memory_recall_tool._generate_summary(memories, "test")

        assert "2 relevant conversations" in summary


# =============================================================================
# Test: Unresolved Items Extraction
# =============================================================================


class TestUnresolvedItemsExtraction:
    """Tests for unresolved items extraction."""

    def test_extract_unresolved_patterns(self, memory_recall_tool):
        """Detects unresolved patterns in memory content."""
        now = _utcnow()
        memories = [
            RecalledMemory(
                memory_id="mem-1",
                content="Issue still monitoring - need to check later",
                created_at=now,
                relevance_score=0.9,
                asset_id=None,
                topic_category=None,
                is_stale=False,
                days_ago=0,
            ),
            RecalledMemory(
                memory_id="mem-2",
                content="Complete and resolved issue",
                created_at=now,
                relevance_score=0.85,
                asset_id=None,
                topic_category=None,
                is_stale=False,
                days_ago=0,
            ),
        ]

        unresolved = memory_recall_tool._extract_unresolved_items(memories)

        assert len(unresolved) == 1
        assert "still monitoring" in unresolved[0].lower()

    def test_extract_max_three_unresolved(self, memory_recall_tool):
        """Limits unresolved items to max 3."""
        now = _utcnow()
        memories = [
            RecalledMemory(
                memory_id=f"mem-{i}",
                content=f"Issue {i} is pending review",
                created_at=now,
                relevance_score=0.9,
                asset_id=None,
                topic_category=None,
                is_stale=False,
                days_ago=0,
            )
            for i in range(5)
        ]

        unresolved = memory_recall_tool._extract_unresolved_items(memories)

        assert len(unresolved) <= 3


# =============================================================================
# Test: Context Variable Functions
# =============================================================================


class TestContextVariables:
    """Tests for context variable functions."""

    def test_set_and_get_user_id(self):
        """Test setting and getting user ID."""
        set_current_user_id("test-user-456")
        assert get_current_user_id() == "test-user-456"

    def test_get_user_id_default(self):
        """Test default user ID when not set."""
        # Reset to default
        set_current_user_id(None)
        assert get_current_user_id() is None
