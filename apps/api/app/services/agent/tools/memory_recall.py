"""
Memory Recall Tool (Story 7.1)

Tool for recalling past conversations and context about specific assets or topics.
Helps plant managers build on previous discussions and leverage historical insights.

AC#1: Topic-Based Memory Recall - Returns summary, decisions, dates, related topics
AC#2: Time-Range Memory Query - Summarizes topics by category, highlights unresolved items
AC#3: No Memory Found Handling - Clear message without hallucination
AC#4: Stale Memory Notification - Warning for memories >30 days old
AC#5: Memory Provenance & Citations - Includes memory_id, timestamps, relevance scores
AC#6: Performance Requirements - <2s response time, no caching
"""

import logging
from contextvars import ContextVar
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel, Field

from app.models.agent import (
    MemoryCitation,
    MemoryRecallInput,
    MemoryRecallOutput,
    RecalledMemory,
)
from app.services.agent.base import Citation, ManufacturingTool, ToolResult
from app.services.memory.mem0_service import MemoryService, get_memory_service

logger = logging.getLogger(__name__)

# Relevance threshold for memory filtering (AC#1: sorted by relevance)
RELEVANCE_THRESHOLD = 0.7

# Stale memory threshold in days (AC#4)
STALE_THRESHOLD_DAYS = 30

# Patterns indicating unresolved items (AC#2)
UNRESOLVED_PATTERNS = [
    "still monitoring",
    "need more data",
    "unresolved",
    "pending",
    "to be determined",
    "to be discussed",
    "follow up",
    "tbd",
    "awaiting",
    "ongoing",
]

# Context variable for current user_id (set by executor before tool invocation)
_current_user_id: ContextVar[Optional[str]] = ContextVar("current_user_id", default=None)


def set_current_user_id(user_id: str) -> None:
    """Set the current user ID for memory operations."""
    _current_user_id.set(user_id)


def get_current_user_id() -> Optional[str]:
    """Get the current user ID for memory operations."""
    return _current_user_id.get()


def _utcnow() -> datetime:
    """Get current UTC time in a timezone-aware manner."""
    return datetime.now(timezone.utc)


class MemoryRecallTool(ManufacturingTool):
    """
    Retrieve and summarize past conversations and context.

    Story 7.1: Memory Recall Tool Implementation

    Use this tool when a user asks about previous discussions, past decisions,
    or wants to recall what was discussed before. Returns recalled memories
    with provenance information including memory_id, timestamps, and relevance scores.

    Examples:
        - "What did we discuss about Grinder 5?"
        - "What issues have we talked about this week?"
        - "Remind me what we decided about maintenance"
        - "What was our last conversation about safety incidents?"
    """

    name: str = "memory_recall"
    description: str = (
        "Retrieve and summarize past conversations and context about specific assets, "
        "topics, or issues. Use this tool when user asks about previous discussions, "
        "past decisions, or wants to recall what was discussed before. "
        "Returns memory summaries with key decisions, unresolved items, and timestamps. "
        "Examples: 'What did we discuss about Grinder 5?', "
        "'What issues have we talked about this week?', "
        "'Remind me what we decided about maintenance'"
    )
    args_schema: Type[BaseModel] = MemoryRecallInput
    citations_required: bool = True

    def __init__(self, **kwargs):
        """Initialize the Memory Recall tool."""
        super().__init__(**kwargs)
        self._memory_service: Optional[MemoryService] = None

    def _get_memory_service(self) -> MemoryService:
        """Get the memory service (lazy initialization)."""
        if self._memory_service is None:
            self._memory_service = get_memory_service()
        return self._memory_service

    def _get_user_id(self) -> Optional[str]:
        """Get the current user ID from context."""
        return get_current_user_id()

    # Note: No caching for memory recall (AC#6: always fetch fresh for accuracy)
    async def _arun(
        self,
        query: str,
        asset_id: Optional[str] = None,
        time_range_days: Optional[int] = None,
        max_results: int = 5,
        **kwargs,
    ) -> ToolResult:
        """
        Execute memory recall query and return structured results.

        AC#1-6: Complete memory recall implementation

        Args:
            query: The topic, asset, or question to recall memories about
            asset_id: Optional asset ID to filter memories
            time_range_days: Optional limit to memories within X days
            max_results: Maximum memories to return (default: 5)

        Returns:
            ToolResult with MemoryRecallOutput data and citations
        """
        # Get user_id from context
        user_id = self._get_user_id()

        logger.info(
            f"Memory recall requested: query='{query[:50]}...', "
            f"asset_id='{asset_id}', time_range_days={time_range_days}, "
            f"max_results={max_results}, user_id={user_id}"
        )

        # Validate user_id is available
        if not user_id:
            logger.warning("Memory recall attempted without user_id, using demo mode")
            # In demo mode, we still provide helpful response
            return self._no_memories_response(
                query=query,
                reason="User context not available for memory recall. "
                       "Memories are personalized per user session.",
            )

        try:
            memory_service = self._get_memory_service()

            # Check if memory service is configured
            if not memory_service.is_configured():
                logger.warning("Memory service not configured for recall")
                return self._no_memories_response(
                    query=query,
                    reason="Memory service is not configured.",
                )

            # Search memories with semantic similarity (AC#1, AC#2)
            memories_raw = await memory_service.search_memory(
                query=query,
                user_id=user_id,
                limit=max_results * 2,  # Fetch extra for filtering
                threshold=RELEVANCE_THRESHOLD,
                asset_id=asset_id,
            )

            # Handle no memories case (AC#3)
            if not memories_raw:
                return self._no_memories_response(query=query)

            # Process and filter memories
            now = _utcnow()
            recalled_memories: List[RecalledMemory] = []

            for mem in memories_raw:
                # Extract timestamp from memory
                created_at = self._parse_memory_timestamp(mem, now)

                # Apply time range filter if specified (AC#2)
                if time_range_days:
                    days_since = (now - created_at).days
                    if days_since > time_range_days:
                        continue

                # Calculate staleness (AC#4)
                days_ago = (now - created_at).days
                is_stale = days_ago > STALE_THRESHOLD_DAYS

                # Extract memory content and metadata
                content = mem.get("memory", mem.get("content", ""))
                memory_id = mem.get("id", mem.get("memory_id", f"mem-{hash(content) % 10000:04d}"))
                relevance_score = mem.get("score", mem.get("similarity", 0.0))
                metadata = mem.get("metadata", {})

                recalled_memories.append(RecalledMemory(
                    memory_id=memory_id,
                    content=content,
                    created_at=created_at,
                    relevance_score=relevance_score,
                    asset_id=metadata.get("asset_id", asset_id),
                    topic_category=metadata.get("topic"),
                    is_stale=is_stale,
                    days_ago=days_ago,
                ))

            # Limit to max_results after filtering
            recalled_memories = recalled_memories[:max_results]

            # Handle case where filtering removed all memories (AC#3)
            if not recalled_memories:
                return self._no_memories_response(
                    query=query,
                    reason=f"No memories within the last {time_range_days} days."
                    if time_range_days else None,
                )

            # Sort by relevance, then recency (AC#1)
            recalled_memories.sort(
                key=lambda m: (-m.relevance_score, -m.created_at.timestamp())
            )

            # Generate summary and insights (AC#1, AC#2)
            summary = self._generate_summary(recalled_memories, query)
            unresolved = self._extract_unresolved_items(recalled_memories)
            related_topics = self._extract_related_topics(recalled_memories)

            # Generate citations (AC#5)
            citations, memory_citations = self._generate_citations(recalled_memories)

            # Check for stale memories (AC#4)
            has_stale = any(m.is_stale for m in recalled_memories)
            stale_note = None
            if has_stale:
                oldest_stale = min(
                    (m for m in recalled_memories if m.is_stale),
                    key=lambda m: m.created_at
                )
                stale_note = (
                    f"Note: Some of this was discussed {oldest_stale.days_ago} days ago - "
                    "things may have changed. Consider checking for updated data."
                )

            # Build output
            output = MemoryRecallOutput(
                memories=recalled_memories,
                summary=summary,
                unresolved_items=unresolved,
                related_topics=related_topics,
                citations=memory_citations,
                has_stale_memories=has_stale,
                stale_memory_note=stale_note,
                query=query,
                no_memories_found=False,
            )

            # Generate follow-up suggestions
            follow_ups = self._generate_follow_ups(output, query)

            return self._create_success_result(
                data=output.model_dump(),
                citations=citations,
                metadata={
                    "cache_tier": "none",  # AC#6: No caching
                    "follow_up_questions": follow_ups,
                    "query_timestamp": now.isoformat(),
                    "memories_recalled": len(recalled_memories),
                },
            )

        except Exception as e:
            logger.exception(f"Unexpected error during memory recall: {e}")
            return self._create_error_result(
                "An unexpected error occurred while recalling memories. "
                "Please try again or rephrase your query."
            )

    # =========================================================================
    # Memory Processing (AC#1, AC#2)
    # =========================================================================

    def _parse_memory_timestamp(
        self,
        memory: Dict[str, Any],
        default: datetime
    ) -> datetime:
        """
        Parse timestamp from memory metadata.

        Args:
            memory: Raw memory dictionary
            default: Default datetime if parsing fails

        Returns:
            Parsed datetime or default
        """
        metadata = memory.get("metadata", {})
        timestamp_str = metadata.get("timestamp")

        if not timestamp_str:
            return default

        try:
            # Handle various ISO formats
            if "Z" in timestamp_str:
                timestamp_str = timestamp_str.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(timestamp_str)
            # Ensure timezone aware
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
        except (ValueError, TypeError):
            logger.warning(f"Failed to parse timestamp: {timestamp_str}")
            return default

    def _generate_summary(
        self,
        memories: List[RecalledMemory],
        query: str
    ) -> str:
        """
        Generate a summary of recalled memories.

        AC#1: Summary of past conversations about the topic.

        Args:
            memories: List of recalled memories
            query: Original query

        Returns:
            Human-readable summary
        """
        if not memories:
            return f"I don't have any previous conversations about '{query}'"

        # Build context-aware summary
        count = len(memories)
        oldest = min(memories, key=lambda m: m.created_at)
        newest = max(memories, key=lambda m: m.created_at)

        # Time span description
        if oldest.days_ago == newest.days_ago:
            time_desc = f"{newest.days_ago} days ago" if newest.days_ago > 0 else "today"
        else:
            time_desc = f"over the past {oldest.days_ago} days"

        summary = f"Found {count} relevant conversation{'s' if count > 1 else ''} about '{query}' from {time_desc}."

        # Add stale warning if applicable (AC#4)
        stale_memories = [m for m in memories if m.is_stale]
        if stale_memories:
            oldest_stale = min(stale_memories, key=lambda m: m.created_at)
            summary += (
                f" (Note: Some discussions were from {oldest_stale.days_ago} days ago - "
                "things may have changed)"
            )

        return summary

    def _extract_unresolved_items(
        self,
        memories: List[RecalledMemory]
    ) -> List[str]:
        """
        Extract unresolved items from memories.

        AC#2: Highlights unresolved items.

        Args:
            memories: List of recalled memories

        Returns:
            List of unresolved items (max 3)
        """
        unresolved = []

        for m in memories:
            content_lower = m.content.lower()
            for pattern in UNRESOLVED_PATTERNS:
                if pattern in content_lower:
                    # Format the unresolved item with date context
                    date_str = m.created_at.strftime("%b %d")
                    # Truncate content if too long
                    content_preview = m.content[:150] + "..." if len(m.content) > 150 else m.content
                    unresolved.append(f"From {date_str}: {content_preview}")
                    break  # Only match one pattern per memory

        return unresolved[:3]  # Limit to top 3

    def _extract_related_topics(
        self,
        memories: List[RecalledMemory]
    ) -> List[str]:
        """
        Extract related topics from memories.

        AC#1: Links to related topics discussed.

        Args:
            memories: List of recalled memories

        Returns:
            List of related topics (max 5)
        """
        topics = set()

        for m in memories:
            if m.topic_category:
                topics.add(m.topic_category.title())
            if m.asset_id:
                topics.add(f"Asset: {m.asset_id}")

        return list(topics)[:5]

    # =========================================================================
    # Citation Generation (AC#5)
    # =========================================================================

    def _generate_citations(
        self,
        memories: List[RecalledMemory]
    ) -> tuple[List[Citation], List[MemoryCitation]]:
        """
        Generate citations for recalled memories.

        AC#5: Memory citations with memory_id and timestamps.

        Args:
            memories: List of recalled memories

        Returns:
            Tuple of (tool citations, memory citations)
        """
        tool_citations: List[Citation] = []
        memory_citations: List[MemoryCitation] = []

        for m in memories:
            # Tool-level citation
            tool_citations.append(self._create_citation(
                source="memory",
                query=f"Memory recall for user",
                table="memories",
                record_id=m.memory_id,
                asset_id=m.asset_id,
                confidence=m.relevance_score,
            ))

            # Memory-specific citation with display text
            date_str = m.created_at.strftime("%b %d, %Y")
            stale_marker = " (stale)" if m.is_stale else ""
            display_text = f"[Memory: {m.memory_id} @ {date_str}]{stale_marker}"

            memory_citations.append(MemoryCitation(
                source_type="memory",
                memory_id=m.memory_id,
                timestamp=m.created_at.isoformat(),
                relevance_score=m.relevance_score,
                is_stale=m.is_stale,
                display_text=display_text,
            ))

        return tool_citations, memory_citations

    # =========================================================================
    # No Memories Response (AC#3)
    # =========================================================================

    def _no_memories_response(
        self,
        query: str,
        reason: Optional[str] = None,
    ) -> ToolResult:
        """
        Generate response when no memories are found.

        AC#3: Clear message without hallucination, offers to help fresh.

        Args:
            query: Original query
            reason: Optional additional reason

        Returns:
            ToolResult with no memories found response
        """
        # Build the message (AC#3: States "I don't have any previous conversations")
        summary = f"I don't have any previous conversations about '{query}'."
        if reason:
            summary += f" {reason}"

        output = MemoryRecallOutput(
            memories=[],
            summary=summary,
            unresolved_items=[],
            related_topics=[],
            citations=[],
            has_stale_memories=False,
            stale_memory_note=None,
            query=query,
            no_memories_found=True,
        )

        # Suggest fresh inquiry options
        follow_ups = [
            f"Would you like me to look up current data about {query}?",
            "Can I help you start a new discussion on this topic?",
        ]

        return self._create_success_result(
            data=output.model_dump(),
            citations=[],
            metadata={
                "cache_tier": "none",
                "follow_up_questions": follow_ups,
                "query_timestamp": _utcnow().isoformat(),
                "memories_recalled": 0,
            },
        )

    # =========================================================================
    # Follow-up Suggestions
    # =========================================================================

    def _generate_follow_ups(
        self,
        output: MemoryRecallOutput,
        query: str
    ) -> List[str]:
        """
        Generate context-aware follow-up suggestions.

        Args:
            output: Memory recall output
            query: Original query

        Returns:
            List of follow-up questions (max 3)
        """
        questions = []

        if output.unresolved_items:
            questions.append("Would you like to discuss the unresolved items?")

        if output.has_stale_memories:
            questions.append("Should I look up the latest data to compare?")

        if output.related_topics:
            topic = output.related_topics[0]
            questions.append(f"Would you like more details about {topic}?")

        # Default suggestions
        if len(questions) < 2:
            questions.append(f"Is there anything specific about {query} you'd like to explore?")

        return questions[:3]
