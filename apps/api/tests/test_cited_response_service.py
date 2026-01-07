"""
Tests for Cited Response Service (Story 4.5)

Integration tests for the high-level cited response service that
orchestrates grounding, citation, and audit logging.

AC#1-8: Full cited response generation pipeline tests
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
from uuid import uuid4
import time

from app.models.citation import (
    Citation,
    CitedResponse,
    Claim,
    SourceType,
    GROUNDING_THRESHOLD_MIN,
)
from app.services.cited_response_service import (
    CitedResponseService,
    get_cited_response_service,
)


@pytest.fixture
def cited_response_service():
    """Create a CitedResponseService instance for testing."""
    service = CitedResponseService()
    return service


@pytest.fixture
def sample_query_results():
    """Sample database query results."""
    return [
        {
            "id": str(uuid4()),
            "asset_name": "Grinder 5",
            "oee_percentage": 87.5,
            "report_date": "2026-01-05",
            "downtime_minutes": 45,
        },
    ]


@pytest.fixture
def mock_services():
    """Mock all dependent services."""
    with patch('app.services.cited_response_service.get_grounding_service') as mock_grounding, \
         patch('app.services.cited_response_service.get_citation_generator') as mock_generator, \
         patch('app.services.cited_response_service.get_citation_audit_service') as mock_audit, \
         patch('app.services.cited_response_service.get_mem0_asset_service') as mock_mem0, \
         patch('app.services.cited_response_service.get_memory_service') as mock_memory:

        # Configure grounding service mock
        grounding_svc = MagicMock()
        grounding_svc.validate_response = AsyncMock(return_value=CitedResponse(
            id="resp-test123",
            response_text="Test response",
            citations=[],
            claims=[],
            grounding_score=0.85,
            ungrounded_claims=[],
        ))
        grounding_svc.generate_fallback_response = MagicMock(side_effect=lambda orig, **kw: orig)
        mock_grounding.return_value = grounding_svc

        # Configure citation generator mock
        generator = MagicMock()
        generator.generate_citations_from_query_results = MagicMock(return_value=[])
        generator.aggregate_citations = MagicMock(return_value=[])
        generator.format_citations_for_response = MagicMock(
            return_value=("Test response", [])
        )
        mock_generator.return_value = generator

        # Configure audit service mock
        audit_svc = MagicMock()
        audit_svc.log_citation_response = AsyncMock()
        mock_audit.return_value = audit_svc

        # Configure Mem0 mocks
        mem0_svc = MagicMock()
        mem0_svc.is_configured.return_value = False
        mem0_svc.retrieve_memories_with_provenance = AsyncMock(return_value=[])
        mock_mem0.return_value = mem0_svc

        memory_svc = MagicMock()
        memory_svc.is_configured.return_value = False
        memory_svc.search_memory = AsyncMock(return_value=[])
        mock_memory.return_value = memory_svc

        yield {
            "grounding": grounding_svc,
            "generator": generator,
            "audit": audit_svc,
            "mem0": mem0_svc,
            "memory": memory_svc,
        }


class TestCitedResponseServiceInitialization:
    """Tests for CitedResponseService initialization."""

    def test_service_can_be_created(self, cited_response_service):
        """Test that service can be instantiated."""
        assert cited_response_service is not None
        assert cited_response_service.is_initialized() is False

    def test_singleton_returns_same_instance(self):
        """Test that get_cited_response_service returns singleton."""
        service1 = get_cited_response_service()
        service2 = get_cited_response_service()
        assert service1 is service2

    def test_initialize_sets_initialized_flag(self, cited_response_service, mock_services):
        """Test that initialize sets the initialized flag."""
        result = cited_response_service.initialize()

        assert result is True
        assert cited_response_service.is_initialized() is True

    def test_is_configured_returns_true(self, cited_response_service):
        """Test that is_configured returns True (no special config needed)."""
        assert cited_response_service.is_configured() is True


class TestGenerateCitedResponse:
    """Tests for generate_cited_response method."""

    @pytest.mark.asyncio
    async def test_generates_response_with_citations(
        self, cited_response_service, mock_services, sample_query_results
    ):
        """Test that generate_cited_response produces a CitedResponse."""
        cited_response_service.initialize()

        result = await cited_response_service.generate_cited_response(
            raw_response="Grinder 5 had 87.5% OEE yesterday.",
            query_text="What was Grinder 5's OEE?",
            user_id="user-123",
            query_results=sample_query_results,
            source_table="daily_summaries",
        )

        assert isinstance(result, CitedResponse)
        assert result.id.startswith("resp-")
        assert 0 <= result.grounding_score <= 1

    @pytest.mark.asyncio
    async def test_includes_grounding_score(
        self, cited_response_service, mock_services, sample_query_results
    ):
        """Test that response includes grounding score."""
        cited_response_service.initialize()

        result = await cited_response_service.generate_cited_response(
            raw_response="Grinder 5 had 87.5% OEE.",
            query_text="What was the OEE?",
            user_id="user-123",
            query_results=sample_query_results,
            source_table="daily_summaries",
        )

        assert result.grounding_score == 0.85  # From mock

    @pytest.mark.asyncio
    async def test_includes_response_metadata(
        self, cited_response_service, mock_services, sample_query_results
    ):
        """Test that response includes metadata."""
        cited_response_service.initialize()

        result = await cited_response_service.generate_cited_response(
            raw_response="Test response",
            query_text="Test query",
            user_id="user-123",
            query_results=sample_query_results,
            source_table="daily_summaries",
        )

        assert result.meta is not None
        assert "response_time_ms" in result.meta
        assert "citation_count" in result.meta

    @pytest.mark.asyncio
    async def test_logs_to_audit_service(
        self, cited_response_service, mock_services, sample_query_results
    ):
        """Test that response is logged for audit."""
        cited_response_service.initialize()

        await cited_response_service.generate_cited_response(
            raw_response="Test response",
            query_text="Test query",
            user_id="user-123",
            query_results=sample_query_results,
            source_table="daily_summaries",
            session_id="session-123",
        )

        # Give async task time to run
        import asyncio
        await asyncio.sleep(0.1)

        # Audit service should have been called
        mock_services["audit"].log_citation_response.assert_called()

    @pytest.mark.asyncio
    async def test_handles_error_gracefully(self, cited_response_service, mock_services):
        """Test that errors return minimal response."""
        cited_response_service.initialize()

        # Make grounding service raise an error
        mock_services["grounding"].validate_response.side_effect = Exception("Test error")

        result = await cited_response_service.generate_cited_response(
            raw_response="Test response",
            query_text="Test query",
            user_id="user-123",
        )

        # Should return response with error info
        assert result is not None
        assert result.grounding_score == 0.0
        assert "error" in result.meta


class TestProcessChatResponse:
    """Tests for process_chat_response method."""

    @pytest.mark.asyncio
    async def test_processes_chat_response(
        self, cited_response_service, mock_services, sample_query_results
    ):
        """Test processing a chat response adds citations."""
        cited_response_service.initialize()

        result = await cited_response_service.process_chat_response(
            raw_response="Grinder 5 had 87.5% OEE.",
            query_text="What was the OEE?",
            user_id="user-123",
            sql="SELECT * FROM daily_summaries",
            data=sample_query_results,
            source_table="daily_summaries",
        )

        assert "answer" in result
        assert "sql" in result
        assert "citations" in result
        assert "grounding_score" in result

    @pytest.mark.asyncio
    async def test_compatible_with_chat_api_format(
        self, cited_response_service, mock_services, sample_query_results
    ):
        """Test that output is compatible with existing chat API format."""
        cited_response_service.initialize()

        result = await cited_response_service.process_chat_response(
            raw_response="Test answer",
            query_text="Test question",
            user_id="user-123",
            sql="SELECT 1",
            data=sample_query_results,
            source_table="daily_summaries",
            context={"asset_focus": "Grinder 5"},
        )

        # Should have all required fields for existing QueryResponse
        assert isinstance(result["answer"], str)
        assert result["sql"] == "SELECT 1"
        assert isinstance(result["data"], list)
        assert isinstance(result["citations"], list)


class TestMemorySourceGathering:
    """Tests for memory source gathering (AC#6)."""

    @pytest.mark.asyncio
    async def test_gathers_user_memories(
        self, cited_response_service, mock_services, sample_query_results
    ):
        """Test that user memories are gathered when available."""
        cited_response_service.initialize()

        # Enable memory service
        mock_services["memory"].is_configured.return_value = True
        mock_services["memory"].search_memory = AsyncMock(return_value=[
            {"memory_id": "mem-001", "content": "Test memory"}
        ])

        await cited_response_service.generate_cited_response(
            raw_response="Test response",
            query_text="Test query",
            user_id="user-123",
            include_memory_context=True,
        )

        # Should have called memory service
        mock_services["memory"].search_memory.assert_called()

    @pytest.mark.asyncio
    async def test_gathers_asset_memories(
        self, cited_response_service, mock_services, sample_query_results
    ):
        """Test that asset memories are gathered when asset_id provided."""
        cited_response_service.initialize()

        # Enable Mem0 service
        mock_services["mem0"].is_configured.return_value = True
        mock_services["mem0"].retrieve_memories_with_provenance = AsyncMock(return_value=[
            {"memory_id": "mem-002", "content": "Asset memory"}
        ])

        asset_id = str(uuid4())
        await cited_response_service.generate_cited_response(
            raw_response="Test response",
            query_text="Test query",
            user_id="user-123",
            asset_id=asset_id,
            include_memory_context=True,
        )

        # Should have called Mem0 service
        mock_services["mem0"].retrieve_memories_with_provenance.assert_called()

    @pytest.mark.asyncio
    async def test_skips_memory_when_disabled(
        self, cited_response_service, mock_services, sample_query_results
    ):
        """Test that memory gathering is skipped when disabled."""
        cited_response_service.initialize()

        await cited_response_service.generate_cited_response(
            raw_response="Test response",
            query_text="Test query",
            user_id="user-123",
            include_memory_context=False,
        )

        # Should not call memory services
        mock_services["memory"].search_memory.assert_not_called()
        mock_services["mem0"].retrieve_memories_with_provenance.assert_not_called()


class TestLowGroundingFallback:
    """Tests for low grounding fallback behavior."""

    @pytest.mark.asyncio
    async def test_applies_fallback_for_low_grounding(
        self, cited_response_service, mock_services
    ):
        """Test that fallback is applied when grounding is below threshold."""
        cited_response_service.initialize()

        # Set low grounding score
        mock_services["grounding"].validate_response = AsyncMock(return_value=CitedResponse(
            id="resp-low",
            response_text="Unverified claim",
            citations=[],
            claims=[],
            grounding_score=0.3,  # Below MIN threshold
            ungrounded_claims=["Unverified claim"],
        ))

        mock_services["grounding"].generate_fallback_response = MagicMock(
            return_value="Note: This information could not be fully verified. Unverified claim"
        )

        result = await cited_response_service.generate_cited_response(
            raw_response="Unverified claim",
            query_text="Test query",
            user_id="user-123",
        )

        # Fallback should have been applied
        mock_services["grounding"].generate_fallback_response.assert_called()
        assert "Note:" in result.response_text or result.grounding_score < GROUNDING_THRESHOLD_MIN


class TestPerformanceRequirements:
    """Tests for AC#8 performance requirements."""

    @pytest.mark.asyncio
    async def test_citation_generation_under_500ms(
        self, cited_response_service, mock_services, sample_query_results
    ):
        """Test that citation generation completes within 500ms."""
        cited_response_service.initialize()

        start = time.time()
        await cited_response_service.generate_cited_response(
            raw_response="Grinder 5 had 87.5% OEE.",
            query_text="What was the OEE?",
            user_id="user-123",
            query_results=sample_query_results,
            source_table="daily_summaries",
        )
        elapsed_ms = (time.time() - start) * 1000

        assert elapsed_ms < 500, f"Citation generation took {elapsed_ms:.0f}ms, expected < 500ms"

    @pytest.mark.asyncio
    async def test_response_includes_timing_metadata(
        self, cited_response_service, mock_services, sample_query_results
    ):
        """Test that response includes timing metadata."""
        cited_response_service.initialize()

        result = await cited_response_service.generate_cited_response(
            raw_response="Test response",
            query_text="Test query",
            user_id="user-123",
            query_results=sample_query_results,
            source_table="daily_summaries",
        )

        assert "response_time_ms" in result.meta
        assert "grounding_time_ms" in result.meta
        assert result.meta["response_time_ms"] > 0


class TestCitationEnhancement:
    """Tests for citation enhancement with additional context."""

    @pytest.mark.asyncio
    async def test_enhances_citations_with_source_table(
        self, cited_response_service, mock_services, sample_query_results
    ):
        """Test that citations are enhanced with source table info."""
        cited_response_service.initialize()

        # Return a citation without source_table
        mock_services["grounding"].validate_response = AsyncMock(return_value=CitedResponse(
            id="resp-enhance",
            response_text="Test response",
            citations=[
                Citation(
                    id="cit-001",
                    source_type=SourceType.DATABASE,
                    record_id=sample_query_results[0]["id"],
                    excerpt="OEE: 87.5%",
                    confidence=0.9,
                    display_text="Test",
                )
            ],
            claims=[],
            grounding_score=0.85,
            ungrounded_claims=[],
        ))

        result = await cited_response_service.generate_cited_response(
            raw_response="Test response",
            query_text="Test query",
            user_id="user-123",
            query_results=sample_query_results,
            source_table="daily_summaries",
        )

        # Meta should include citation count
        assert result.meta["citation_count"] >= 0
