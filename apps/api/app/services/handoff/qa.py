"""
Handoff Q&A Service (Story 9.6)

Orchestrates Q&A processing for shift handoffs.
Routes questions through ManufacturingAgent with handoff context injection.

AC#1: Process questions with handoff context
AC#2: Generate responses with citations (FR52)
AC#3: Support human responses from outgoing supervisor
AC#6: Partial failure handling

References:
- [Source: architecture/voice-briefing.md#BriefingService Architecture]
- [Source: prd/prd-functional-requirements.md#FR26,FR52]
- [Source: apps/api/app/api/chat.py] - Agent routing and citation patterns
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.models.handoff import (
    HandoffQACitation,
    HandoffQAContentType,
    HandoffQAContext,
    HandoffQAEntry,
    HandoffQARequest,
    HandoffQAResponse,
    HandoffQAThread,
    ShiftTimeRange,
)
from app.services.agent.executor import (
    ManufacturingAgent,
    get_manufacturing_agent,
    AgentError,
)
from app.services.handoff import get_shift_time_range

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    """Get current UTC time in a timezone-aware manner."""
    return datetime.now(timezone.utc)


# Timeout configuration
QA_TIMEOUT_SECONDS = 15  # Per FR26 - Q&A round-trip <2s target, 15s max


class HandoffQAService:
    """
    Handoff Q&A orchestration service.

    Story 9.6 Implementation:
    - AC#1: Processes questions with handoff context injected into agent
    - AC#2: Ensures citations are generated from tool responses (FR52)
    - AC#3: Supports human responses from outgoing supervisor
    - AC#6: Handles partial failures gracefully

    This is NOT a ManufacturingTool - it's an orchestration layer that:
    1. Loads handoff context (summary, metadata)
    2. Injects context into agent prompt
    3. Routes question to ManufacturingAgent
    4. Transforms response with proper citations
    5. Stores Q&A entries (append-only)

    Usage:
        service = get_handoff_qa_service()
        response = await service.process_question(
            handoff_id="uuid",
            question="Why was there downtime?",
            user_id="user123",
            handoff_context=context
        )
    """

    def __init__(self):
        """Initialize the handoff Q&A service."""
        self._qa_store: Dict[str, List[Dict[str, Any]]] = {}  # In-memory for MVP

    async def process_question(
        self,
        handoff_id: str,
        question: str,
        user_id: str,
        user_name: Optional[str] = None,
        handoff_context: Optional[HandoffQAContext] = None,
        voice_transcript: Optional[str] = None,
    ) -> HandoffQAResponse:
        """
        Process a Q&A question about a handoff.

        AC#1: Question processed with handoff context
        AC#2: Response includes citations from tools (FR52)

        Args:
            handoff_id: UUID of the handoff
            question: The question text
            user_id: ID of user asking the question
            user_name: Display name of user (optional)
            handoff_context: Handoff context for agent injection
            voice_transcript: Original voice transcript if spoken

        Returns:
            HandoffQAResponse with answer and citations

        Raises:
            HandoffQAError: If processing fails
        """
        logger.info(
            f"Processing Q&A question for handoff {handoff_id}: "
            f"'{question[:50]}...' from user {user_id}"
        )
        start_time = _utcnow()

        # 1. Create question entry
        question_entry = self._create_entry(
            handoff_id=handoff_id,
            user_id=user_id,
            user_name=user_name,
            content_type=HandoffQAContentType.QUESTION,
            content=question,
            voice_transcript=voice_transcript,
        )

        # Store question entry
        self._store_entry(handoff_id, question_entry)

        # 2. Process through agent with context injection
        try:
            answer_content, citations = await self._process_via_agent(
                question=question,
                user_id=user_id,
                handoff_context=handoff_context,
            )
        except asyncio.TimeoutError:
            logger.warning(
                f"Q&A processing timed out after {QA_TIMEOUT_SECONDS}s "
                f"for handoff {handoff_id}"
            )
            answer_content = (
                "I'm still processing your question. "
                "The response is taking longer than expected. "
                "Please try again in a moment."
            )
            citations = []
        except AgentError as e:
            logger.error(f"Agent error processing Q&A: {e}")
            answer_content = (
                "I encountered an issue processing your question. "
                "Please try rephrasing or ask a different question."
            )
            citations = []
        except Exception as e:
            logger.error(f"Unexpected error in Q&A processing: {e}", exc_info=True)
            answer_content = (
                "I had trouble processing that question. "
                "Please try again."
            )
            citations = []

        # 3. Create answer entry
        answer_entry = self._create_entry(
            handoff_id=handoff_id,
            user_id=user_id,  # System response attributed to requester for simplicity
            user_name="AI Assistant",
            content_type=HandoffQAContentType.AI_ANSWER,
            content=answer_content,
            citations=citations,
        )

        # Store answer entry
        self._store_entry(handoff_id, answer_entry)

        # 4. Get thread count
        thread_count = len(self._get_entries(handoff_id))

        duration_ms = int((_utcnow() - start_time).total_seconds() * 1000)
        logger.info(
            f"Q&A processed for handoff {handoff_id} in {duration_ms}ms, "
            f"{len(citations)} citations"
        )

        return HandoffQAResponse(
            entry=answer_entry,
            question_entry=question_entry,
            thread_count=thread_count,
            message="Question processed successfully",
        )

    async def add_human_response(
        self,
        handoff_id: str,
        response: str,
        user_id: str,
        user_name: Optional[str] = None,
        question_entry_id: Optional[str] = None,
    ) -> HandoffQAEntry:
        """
        Add a human response from the outgoing supervisor.

        AC#3: Outgoing supervisor can respond directly.

        Args:
            handoff_id: UUID of the handoff
            response: The response text
            user_id: ID of the responding supervisor
            user_name: Display name of supervisor
            question_entry_id: Optional ID of question being answered

        Returns:
            Created HandoffQAEntry
        """
        logger.info(
            f"Adding human response to handoff {handoff_id} from user {user_id}"
        )

        entry = self._create_entry(
            handoff_id=handoff_id,
            user_id=user_id,
            user_name=user_name,
            content_type=HandoffQAContentType.HUMAN_RESPONSE,
            content=response,
        )

        self._store_entry(handoff_id, entry)

        return entry

    def get_thread(self, handoff_id: str) -> HandoffQAThread:
        """
        Get the complete Q&A thread for a handoff.

        AC#4: All Q&A entries preserved and visible.

        Args:
            handoff_id: UUID of the handoff

        Returns:
            HandoffQAThread with all entries
        """
        entries_data = self._get_entries(handoff_id)

        entries = [
            HandoffQAEntry(
                id=uuid.UUID(e["id"]),
                handoff_id=uuid.UUID(e["handoff_id"]),
                user_id=uuid.UUID(e["user_id"]),
                user_name=e.get("user_name"),
                content_type=HandoffQAContentType(e["content_type"]),
                content=e["content"],
                citations=[
                    HandoffQACitation(**c) for c in e.get("citations", [])
                ],
                voice_transcript=e.get("voice_transcript"),
                created_at=datetime.fromisoformat(e["created_at"]),
            )
            for e in entries_data
        ]

        return HandoffQAThread.from_entries(
            handoff_id=uuid.UUID(handoff_id),
            entries=entries,
        )

    async def _process_via_agent(
        self,
        question: str,
        user_id: str,
        handoff_context: Optional[HandoffQAContext] = None,
    ) -> tuple[str, List[HandoffQACitation]]:
        """
        Process question through ManufacturingAgent with context injection.

        AC#1: Context injected into agent
        AC#2: Citations generated from tool responses (FR52)

        Args:
            question: The question to process
            user_id: User ID for agent
            handoff_context: Optional context to inject

        Returns:
            Tuple of (answer_content, citations)
        """
        agent = get_manufacturing_agent()

        # Build context-enriched message
        enriched_message = self._build_enriched_message(question, handoff_context)

        # Build chat history with handoff context
        chat_history = []
        if handoff_context:
            # Inject handoff summary as system context
            context_message = self._build_context_message(handoff_context)
            chat_history.append({
                "role": "assistant",
                "content": context_message,
            })

        # Process through agent with timeout
        response = await asyncio.wait_for(
            agent.process_message(
                message=enriched_message,
                user_id=user_id,
                chat_history=chat_history,
            ),
            timeout=QA_TIMEOUT_SECONDS,
        )

        # Transform agent citations to HandoffQACitation
        citations = self._transform_citations(response.citations)

        return response.content, citations

    def _build_enriched_message(
        self,
        question: str,
        handoff_context: Optional[HandoffQAContext] = None,
    ) -> str:
        """
        Build the enriched message with context hints.

        Adds context about what data is available without overwhelming the agent.
        """
        if not handoff_context:
            return question

        # Add time range context for accurate tool queries
        time_hint = ""
        if handoff_context.shift_time_range:
            start = handoff_context.shift_time_range.start_time
            end = handoff_context.shift_time_range.end_time
            time_hint = (
                f"[Context: This question is about shift data from "
                f"{start.strftime('%H:%M')} to {end.strftime('%H:%M')} "
                f"on {handoff_context.shift_time_range.shift_date}] "
            )

        return f"{time_hint}{question}"

    def _build_context_message(
        self,
        handoff_context: HandoffQAContext,
    ) -> str:
        """
        Build the context message to inject into chat history.

        This provides the agent with handoff summary for reference.
        """
        parts = []

        parts.append(
            f"I'm reviewing a shift handoff from {handoff_context.outgoing_supervisor}."
        )

        if handoff_context.handoff_summary:
            # Truncate if too long
            summary = handoff_context.handoff_summary
            if len(summary) > 2000:
                summary = summary[:2000] + "..."
            parts.append(f"\n\nShift Summary:\n{summary}")

        if handoff_context.text_notes:
            parts.append(f"\n\nSupervisor Notes:\n{handoff_context.text_notes}")

        if handoff_context.voice_note_transcripts:
            transcripts = "\n".join(handoff_context.voice_note_transcripts)
            if len(transcripts) > 1000:
                transcripts = transcripts[:1000] + "..."
            parts.append(f"\n\nVoice Note Transcripts:\n{transcripts}")

        return " ".join(parts)

    def _transform_citations(
        self,
        agent_citations: List[Any],
    ) -> List[HandoffQACitation]:
        """
        Transform agent citations to HandoffQACitation format.

        AC#2: Ensures citations are properly formatted (FR52).

        Args:
            agent_citations: Citations from agent response (can be dicts or HandoffQACitation)

        Returns:
            List of HandoffQACitation
        """
        citations = []
        for cit in agent_citations:
            try:
                # If already a HandoffQACitation, use directly
                if isinstance(cit, HandoffQACitation):
                    citations.append(cit)
                    continue

                # Otherwise transform from dict
                cit_dict = cit if isinstance(cit, dict) else {}

                # Parse timestamp if present
                timestamp = _utcnow()
                ts_value = cit_dict.get("timestamp")
                if ts_value:
                    if isinstance(ts_value, datetime):
                        timestamp = ts_value
                    elif isinstance(ts_value, str):
                        try:
                            timestamp = datetime.fromisoformat(
                                ts_value.replace("Z", "+00:00")
                            )
                        except (ValueError, AttributeError):
                            pass

                # Extract value - support multiple field names
                value = (
                    cit_dict.get("value") or
                    cit_dict.get("display_text") or
                    ""
                )

                # Extract field - support multiple field names
                field = (
                    cit_dict.get("field") or
                    cit_dict.get("source") or
                    "data"
                )

                citations.append(HandoffQACitation(
                    value=str(value),
                    field=str(field),
                    table=cit_dict.get("table", "agent_data"),
                    context=cit_dict.get("context", cit_dict.get("query", "")),
                    timestamp=timestamp,
                ))
            except Exception as e:
                logger.warning(f"Failed to transform citation: {e}")

        return citations

    def _create_entry(
        self,
        handoff_id: str,
        user_id: str,
        content_type: HandoffQAContentType,
        content: str,
        user_name: Optional[str] = None,
        citations: Optional[List[HandoffQACitation]] = None,
        voice_transcript: Optional[str] = None,
    ) -> HandoffQAEntry:
        """Create a new Q&A entry."""
        entry_id = uuid.uuid4()
        now = _utcnow()

        return HandoffQAEntry(
            id=entry_id,
            handoff_id=uuid.UUID(handoff_id),
            user_id=uuid.UUID(user_id),
            user_name=user_name,
            content_type=content_type,
            content=content,
            citations=citations or [],
            voice_transcript=voice_transcript,
            created_at=now,
        )

    def _store_entry(self, handoff_id: str, entry: HandoffQAEntry) -> None:
        """
        Store a Q&A entry (append-only per NFR24).

        In production, this would insert into handoff_qa_entries table.
        For MVP, uses in-memory storage.
        """
        if handoff_id not in self._qa_store:
            self._qa_store[handoff_id] = []

        # Convert to dict for storage
        entry_data = {
            "id": str(entry.id),
            "handoff_id": str(entry.handoff_id),
            "user_id": str(entry.user_id),
            "user_name": entry.user_name,
            "content_type": entry.content_type.value,
            "content": entry.content,
            "citations": [
                {
                    "value": c.value,
                    "field": c.field,
                    "table": c.table,
                    "context": c.context,
                    "timestamp": c.timestamp.isoformat() if c.timestamp else None,
                }
                for c in entry.citations
            ],
            "voice_transcript": entry.voice_transcript,
            "created_at": entry.created_at.isoformat(),
        }

        self._qa_store[handoff_id].append(entry_data)

    def _get_entries(self, handoff_id: str) -> List[Dict[str, Any]]:
        """Get all Q&A entries for a handoff."""
        return self._qa_store.get(handoff_id, [])


# Module-level singleton
_handoff_qa_service: Optional[HandoffQAService] = None


def get_handoff_qa_service() -> HandoffQAService:
    """
    Get the singleton HandoffQAService instance.

    Returns:
        HandoffQAService singleton instance
    """
    global _handoff_qa_service
    if _handoff_qa_service is None:
        _handoff_qa_service = HandoffQAService()
    return _handoff_qa_service


class HandoffQAError(Exception):
    """Custom exception for Q&A processing errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
