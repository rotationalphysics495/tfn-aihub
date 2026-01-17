"""
Tests for Handoff Q&A Service (Story 9.6)

Tests the HandoffQAService for processing Q&A questions and responses.

AC#1: Process questions with handoff context
AC#2: Generate responses with citations (FR52)
AC#3: Support human responses from outgoing supervisor
AC#6: Partial failure handling

References:
- [Source: apps/api/app/services/handoff/qa.py]
"""

import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.handoff.qa import (
    HandoffQAService,
    HandoffQAError,
    get_handoff_qa_service,
)
from app.models.handoff import (
    HandoffQAContentType,
    HandoffQAContext,
    HandoffQAEntry,
    HandoffQAThread,
    ShiftTimeRange,
    ShiftType,
)


@pytest.fixture
def qa_service():
    """Create a fresh HandoffQAService for each test."""
    return HandoffQAService()


@pytest.fixture
def sample_handoff_id():
    """Generate a sample handoff ID."""
    return str(uuid.uuid4())


@pytest.fixture
def sample_user_id():
    """Generate a sample user ID."""
    return str(uuid.uuid4())


@pytest.fixture
def sample_handoff_context():
    """Create a sample handoff context."""
    return HandoffQAContext(
        handoff_summary="Production was 5% behind target. Main issue was downtime on Grinder 5.",
        shift_time_range=ShiftTimeRange(
            shift_type=ShiftType.MORNING,
            start_time=datetime.now(timezone.utc).replace(hour=6, minute=0),
            end_time=datetime.now(timezone.utc).replace(hour=14, minute=0),
            shift_date=datetime.now(timezone.utc).date(),
        ),
        assets_covered=[uuid.uuid4(), uuid.uuid4()],
        outgoing_supervisor="John Smith",
        text_notes="Watch the temperature on Line 3",
        voice_note_transcripts=["Need to check valve on mixer"],
    )


class TestHandoffQAService:
    """Tests for HandoffQAService."""

    @pytest.mark.asyncio
    async def test_process_question_creates_question_entry(
        self,
        qa_service: HandoffQAService,
        sample_handoff_id: str,
        sample_user_id: str,
    ):
        """Test that processing a question creates a question entry."""
        with patch.object(
            qa_service,
            '_process_via_agent',
            new_callable=AsyncMock,
            return_value=("This is the answer", []),
        ):
            response = await qa_service.process_question(
                handoff_id=sample_handoff_id,
                question="Why was there downtime?",
                user_id=sample_user_id,
                user_name="Test User",
            )

            # Check question entry was created
            assert response.question_entry is not None
            assert response.question_entry.content == "Why was there downtime?"
            assert response.question_entry.content_type == HandoffQAContentType.QUESTION
            assert str(response.question_entry.user_id) == sample_user_id
            assert response.question_entry.user_name == "Test User"

    @pytest.mark.asyncio
    async def test_process_question_creates_answer_entry(
        self,
        qa_service: HandoffQAService,
        sample_handoff_id: str,
        sample_user_id: str,
    ):
        """Test that processing a question creates an AI answer entry."""
        with patch.object(
            qa_service,
            '_process_via_agent',
            new_callable=AsyncMock,
            return_value=("The downtime was caused by equipment failure.", []),
        ):
            response = await qa_service.process_question(
                handoff_id=sample_handoff_id,
                question="Why was there downtime?",
                user_id=sample_user_id,
            )

            # Check answer entry was created
            assert response.entry is not None
            assert "downtime" in response.entry.content.lower()
            assert response.entry.content_type == HandoffQAContentType.AI_ANSWER
            assert response.entry.user_name == "AI Assistant"

    @pytest.mark.asyncio
    async def test_process_question_with_citations(
        self,
        qa_service: HandoffQAService,
        sample_handoff_id: str,
        sample_user_id: str,
        sample_handoff_context: HandoffQAContext,
    ):
        """Test that citations are included in the response (AC#2)."""
        from app.models.handoff import HandoffQACitation

        mock_citations = [
            HandoffQACitation(
                value="2.5 hours",
                field="downtime_analysis",
                table="daily_summaries",
                context="Grinder 5 downtime",
                timestamp=datetime.now(timezone.utc),
            )
        ]

        with patch.object(
            qa_service,
            '_process_via_agent',
            new_callable=AsyncMock,
            return_value=("Grinder 5 had 2.5 hours of downtime.", mock_citations),
        ):
            response = await qa_service.process_question(
                handoff_id=sample_handoff_id,
                question="How much downtime was there?",
                user_id=sample_user_id,
                handoff_context=sample_handoff_context,
            )

            # Check citations are present
            assert len(response.entry.citations) > 0
            assert response.entry.citations[0].value == "2.5 hours"
            assert response.entry.citations[0].table == "daily_summaries"

    @pytest.mark.asyncio
    async def test_process_question_with_voice_transcript(
        self,
        qa_service: HandoffQAService,
        sample_handoff_id: str,
        sample_user_id: str,
    ):
        """Test that voice transcript is preserved in question entry."""
        with patch.object(
            qa_service,
            '_process_via_agent',
            new_callable=AsyncMock,
            return_value=("Here is the answer.", []),
        ):
            response = await qa_service.process_question(
                handoff_id=sample_handoff_id,
                question="What happened on Line 3?",
                user_id=sample_user_id,
                voice_transcript="What happened on line three?",
            )

            # Check voice transcript is preserved
            assert response.question_entry.voice_transcript == "What happened on line three?"

    @pytest.mark.asyncio
    async def test_add_human_response(
        self,
        qa_service: HandoffQAService,
        sample_handoff_id: str,
        sample_user_id: str,
    ):
        """Test adding a human response (AC#3)."""
        entry = await qa_service.add_human_response(
            handoff_id=sample_handoff_id,
            response="I fixed the issue manually at 10:30.",
            user_id=sample_user_id,
            user_name="Outgoing Supervisor",
        )

        assert entry is not None
        assert entry.content == "I fixed the issue manually at 10:30."
        assert entry.content_type == HandoffQAContentType.HUMAN_RESPONSE
        assert entry.user_name == "Outgoing Supervisor"

    @pytest.mark.asyncio
    async def test_get_thread_returns_all_entries(
        self,
        qa_service: HandoffQAService,
        sample_handoff_id: str,
        sample_user_id: str,
    ):
        """Test that get_thread returns all Q&A entries (AC#4)."""
        # Add some entries
        with patch.object(
            qa_service,
            '_process_via_agent',
            new_callable=AsyncMock,
            return_value=("Answer 1", []),
        ):
            await qa_service.process_question(
                handoff_id=sample_handoff_id,
                question="Question 1",
                user_id=sample_user_id,
            )

        await qa_service.add_human_response(
            handoff_id=sample_handoff_id,
            response="Human response",
            user_id=sample_user_id,
        )

        # Get thread
        thread = qa_service.get_thread(sample_handoff_id)

        assert thread.count == 3  # question + AI answer + human response
        assert len(thread.entries) == 3

    @pytest.mark.asyncio
    async def test_thread_entries_ordered_by_time(
        self,
        qa_service: HandoffQAService,
        sample_handoff_id: str,
        sample_user_id: str,
    ):
        """Test that thread entries are ordered by creation time."""
        with patch.object(
            qa_service,
            '_process_via_agent',
            new_callable=AsyncMock,
            return_value=("Answer", []),
        ):
            await qa_service.process_question(
                handoff_id=sample_handoff_id,
                question="First question",
                user_id=sample_user_id,
            )

        thread = qa_service.get_thread(sample_handoff_id)

        # Entries should be sorted by created_at
        timestamps = [e.created_at for e in thread.entries]
        assert timestamps == sorted(timestamps)

    @pytest.mark.asyncio
    async def test_process_question_handles_timeout(
        self,
        qa_service: HandoffQAService,
        sample_handoff_id: str,
        sample_user_id: str,
    ):
        """Test graceful handling of agent timeout."""
        import asyncio

        # Mock the _process_via_agent to raise TimeoutError
        with patch.object(
            qa_service,
            '_process_via_agent',
            side_effect=asyncio.TimeoutError("Timeout"),
        ):
            response = await qa_service.process_question(
                handoff_id=sample_handoff_id,
                question="Test question",
                user_id=sample_user_id,
            )

            # Should still return a response with timeout message
            assert response is not None
            assert "still processing" in response.entry.content.lower() or \
                   "try again" in response.entry.content.lower() or \
                   "longer" in response.entry.content.lower()

    @pytest.mark.asyncio
    async def test_process_question_handles_agent_error(
        self,
        qa_service: HandoffQAService,
        sample_handoff_id: str,
        sample_user_id: str,
    ):
        """Test graceful handling of agent errors."""
        from app.services.agent.executor import AgentError

        with patch.object(
            qa_service,
            '_process_via_agent',
            side_effect=AgentError("Agent failed"),
        ):
            response = await qa_service.process_question(
                handoff_id=sample_handoff_id,
                question="Test question",
                user_id=sample_user_id,
            )

            # Should still return a response with error message
            assert response is not None
            assert "issue" in response.entry.content.lower() or \
                   "trouble" in response.entry.content.lower()


class TestHandoffQAServiceContextInjection:
    """Tests for context injection into agent."""

    def test_build_enriched_message_without_context(
        self,
        qa_service: HandoffQAService,
    ):
        """Test enriched message without context is just the question."""
        result = qa_service._build_enriched_message("What happened?", None)
        assert result == "What happened?"

    def test_build_enriched_message_with_context(
        self,
        qa_service: HandoffQAService,
        sample_handoff_context: HandoffQAContext,
    ):
        """Test enriched message includes time range context."""
        result = qa_service._build_enriched_message(
            "What happened?",
            sample_handoff_context,
        )
        assert "[Context:" in result
        assert "What happened?" in result

    def test_build_context_message_includes_summary(
        self,
        qa_service: HandoffQAService,
        sample_handoff_context: HandoffQAContext,
    ):
        """Test context message includes handoff summary."""
        result = qa_service._build_context_message(sample_handoff_context)
        assert "Production was 5% behind target" in result
        assert "John Smith" in result

    def test_build_context_message_includes_notes(
        self,
        qa_service: HandoffQAService,
        sample_handoff_context: HandoffQAContext,
    ):
        """Test context message includes supervisor notes."""
        result = qa_service._build_context_message(sample_handoff_context)
        assert "Watch the temperature" in result

    def test_build_context_message_includes_voice_transcripts(
        self,
        qa_service: HandoffQAService,
        sample_handoff_context: HandoffQAContext,
    ):
        """Test context message includes voice note transcripts."""
        result = qa_service._build_context_message(sample_handoff_context)
        assert "check valve on mixer" in result


class TestHandoffQAServiceCitations:
    """Tests for citation transformation."""

    def test_transform_citations_empty(self, qa_service: HandoffQAService):
        """Test transforming empty citations list."""
        result = qa_service._transform_citations([])
        assert result == []

    def test_transform_citations_valid(self, qa_service: HandoffQAService):
        """Test transforming valid citations."""
        agent_citations = [
            {
                "display_text": "87.5%",
                "source": "oee_tool",
                "table": "daily_summaries",
                "context": "Grinder 5 OEE",
                "timestamp": "2026-01-16T10:00:00Z",
            }
        ]

        result = qa_service._transform_citations(agent_citations)

        assert len(result) == 1
        assert result[0].value == "87.5%"
        assert result[0].field == "oee_tool"
        assert result[0].table == "daily_summaries"
        assert result[0].context == "Grinder 5 OEE"

    def test_transform_citations_handles_missing_fields(
        self,
        qa_service: HandoffQAService,
    ):
        """Test handling citations with missing fields."""
        agent_citations = [
            {"value": "test"},  # Missing most fields
        ]

        result = qa_service._transform_citations(agent_citations)

        assert len(result) == 1
        assert result[0].value == "test"
        assert result[0].table == "agent_data"  # Default value


class TestGetHandoffQAService:
    """Tests for singleton getter."""

    def test_returns_same_instance(self):
        """Test that get_handoff_qa_service returns singleton."""
        service1 = get_handoff_qa_service()
        service2 = get_handoff_qa_service()
        assert service1 is service2

    def test_returns_handoff_qa_service_instance(self):
        """Test that returned instance is HandoffQAService."""
        service = get_handoff_qa_service()
        assert isinstance(service, HandoffQAService)
