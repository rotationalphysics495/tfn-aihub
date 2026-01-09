"""
Chat API Endpoints (Story 4.2, 4.5, 5.7)

REST API for AI chat interface routing to ManufacturingAgent with cited responses.

Story 5.7: Agent Chat Integration
- Routes chat messages to ManufacturingAgent (not Text-to-SQL directly)
- Preserves Mem0 memory storage for conversations
- Transforms agent response for frontend compatibility
- Maintains backward compatibility with existing chat UI

AC#8 (Story 4.2): API Endpoint Design
- POST /api/chat/query with body { "question": string, "context"?: object }
- Responses follow format { "answer": string, "sql": string, "data": object, "citations": array }
- Protected with Supabase JWT authentication
- Rate limiting implemented

Story 4.5 Integration:
- All responses include grounded citations (AC#1)
- Grounding score included in response metadata (AC#3)
- NFR1 compliance: All factual claims cite data sources (AC#7)
"""

import logging
import re
import time
from collections import defaultdict
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.config import get_settings
from app.core.security import get_current_user
from app.models.user import CurrentUser
from app.models.chat import (
    QueryInput,
    QueryResponse,
    Citation,
    TablesResponse,
    ChatServiceStatus,
)
from app.services.ai.text_to_sql import (
    TextToSQLService,
    TextToSQLError,
    get_text_to_sql_service,
)
from app.services.ai.text_to_sql.prompts import TABLE_DESCRIPTIONS
from app.services.cited_response_service import (
    CitedResponseService,
    get_cited_response_service,
)
from app.services.agent.executor import (
    ManufacturingAgent,
    get_manufacturing_agent,
    AgentError,
)
from app.services.memory.mem0_service import memory_service, MemoryServiceError

logger = logging.getLogger(__name__)

router = APIRouter()


@lru_cache()
def _get_rate_limit_config():
    """Get rate limit configuration from settings."""
    settings = get_settings()
    return (
        getattr(settings, 'chat_rate_limit_requests', 10),
        getattr(settings, 'chat_rate_limit_window', 60),
    )


# Simple in-memory rate limiter
_rate_limit_store: dict = defaultdict(list)


def get_service() -> TextToSQLService:
    """Dependency to get Text-to-SQL service instance."""
    return get_text_to_sql_service()


def get_cited_service() -> CitedResponseService:
    """Dependency to get Cited Response service instance."""
    return get_cited_response_service()


def get_agent() -> ManufacturingAgent:
    """Dependency to get ManufacturingAgent instance."""
    return get_manufacturing_agent()


def _extract_source_table(sql: Optional[str]) -> Optional[str]:
    """Extract the primary source table from SQL query."""
    if not sql:
        return None
    match = re.search(r"\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*)", sql, re.IGNORECASE)
    if match:
        return match.group(1).lower()
    return None


def check_rate_limit(user_id: str) -> None:
    """
    Check if user has exceeded rate limit.

    AC#8: Rate limiting (configurable via settings, default 10 requests/minute per user)

    Args:
        user_id: User identifier from JWT

    Raises:
        HTTPException 429: If rate limit exceeded
    """
    rate_limit_requests, rate_limit_window = _get_rate_limit_config()
    current_time = time.time()
    window_start = current_time - rate_limit_window

    # Get user's requests and filter to current window
    user_requests = _rate_limit_store[user_id]
    user_requests = [t for t in user_requests if t > window_start]
    _rate_limit_store[user_id] = user_requests

    if len(user_requests) >= rate_limit_requests:
        wait_time = max(1, int(user_requests[0] + rate_limit_window - current_time) + 1)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Please wait {wait_time} seconds before trying again.",
            headers={"Retry-After": str(wait_time)},
        )

    # Record this request
    user_requests.append(current_time)


@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Query data with natural language",
    description="""
    Submit a natural language question about plant performance data.

    Story 5.7: Routes messages to ManufacturingAgent for intelligent tool selection.

    The system will:
    1. Route your question to the Manufacturing Agent
    2. Agent selects appropriate tools based on intent
    3. Execute queries and aggregate data with citations
    4. Store conversation in Mem0 for future context
    5. Return a natural language answer with verified data citations

    **Supported Topics:**
    - OEE (Overall Equipment Effectiveness)
    - Downtime and production output
    - Financial loss calculations
    - Safety events and incidents
    - Asset status and comparisons
    - Production targets and variance

    **Example Questions:**
    - "What was Grinder 5's OEE yesterday?"
    - "Which asset had the most downtime last week?"
    - "Show me all safety events this month"
    - "What's the total financial loss for the Grinding area?"
    - "How is production tracking against target?"

    **Features:**
    - All responses include inline citations [Source: table/record]
    - Suggested follow-up questions
    - Conversation memory for contextual responses
    - NFR1 compliant: All claims cite specific data points
    """,
)
async def query_data(
    query_input: QueryInput,
    use_agent: bool = Query(
        True,
        description="Route to ManufacturingAgent (Story 5.7) vs legacy Text-to-SQL"
    ),
    enable_grounding: bool = Query(
        True,
        description="Enable Story 4.5 grounding validation and citation generation"
    ),
    current_user: CurrentUser = Depends(get_current_user),
    agent: ManufacturingAgent = Depends(get_agent),
    service: TextToSQLService = Depends(get_service),
    cited_service: CitedResponseService = Depends(get_cited_service),
) -> QueryResponse:
    """
    Process a natural language query about plant data.

    Story 5.7: Agent Chat Integration
    AC#1: Message is routed to agent endpoint
    AC#6: Conversations are stored in Mem0

    Story 4.2:
    AC#2: Natural language question is processed
    AC#3: Query executes and returns formatted results
    AC#4: Response includes data citations
    AC#5: Input is validated for security
    AC#6: Errors are handled gracefully
    AC#7: Context is accepted for enhancement
    AC#8: Protected with Supabase JWT authentication

    Story 4.5:
    AC#1: Response includes inline citations
    AC#3: Grounding validation with 0.6 threshold
    AC#7: NFR1 compliance - all factual claims cite sources
    AC#8: Citation generation within 500ms

    Args:
        query_input: The question and optional context
        use_agent: Route to ManufacturingAgent (default) vs legacy Text-to-SQL
        enable_grounding: Enable Story 4.5 citation generation
        current_user: Authenticated user from JWT
        agent: ManufacturingAgent instance
        service: Text-to-SQL service instance (fallback)
        cited_service: Cited response service instance

    Returns:
        QueryResponse with answer, SQL, data, and citations

    Raises:
        HTTPException 429: If rate limit exceeded
        HTTPException 503: If service not configured
        HTTPException 500: If unexpected error
    """
    # AC#8: Rate limiting
    check_rate_limit(current_user.id)

    # Story 5.7: Route to agent if enabled and agent is configured
    if use_agent and agent.is_configured:
        return await _process_via_agent(
            query_input=query_input,
            current_user=current_user,
            agent=agent,
        )

    # Fallback to legacy Text-to-SQL path
    return await _process_via_text_to_sql(
        query_input=query_input,
        enable_grounding=enable_grounding,
        current_user=current_user,
        service=service,
        cited_service=cited_service,
    )


async def _process_via_agent(
    query_input: QueryInput,
    current_user: CurrentUser,
    agent: ManufacturingAgent,
) -> QueryResponse:
    """
    Process query through ManufacturingAgent.

    Story 5.7: Agent Chat Integration
    AC#1: Routes to agent endpoint
    AC#6: Stores conversation in Mem0

    Args:
        query_input: The question and optional context
        current_user: Authenticated user from JWT
        agent: ManufacturingAgent instance

    Returns:
        QueryResponse with answer, citations, and follow-up questions
    """
    user_id = current_user.id
    start_time = time.time()

    try:
        # Build context for agent
        context = None
        if query_input.context:
            context = query_input.context.model_dump(exclude_none=True)

        # Story 5.7 AC#6: Get memory context for the query
        chat_history: List[Dict[str, str]] = []
        try:
            chat_history = await memory_service.get_context_for_query(
                query=query_input.question,
                user_id=user_id,
                asset_id=context.get("asset_focus") if context else None,
            )
        except MemoryServiceError as e:
            logger.warning(f"Memory context retrieval failed (graceful degradation): {e}")

        # Process through ManufacturingAgent
        agent_response = await agent.process_message(
            message=query_input.question,
            user_id=user_id,
            chat_history=chat_history,
        )

        # Story 5.7 AC#6: Store conversation in Mem0
        try:
            metadata = {"source": "chat_sidebar"}
            if context and context.get("asset_focus"):
                metadata["asset_id"] = context["asset_focus"]

            await memory_service.add_memory(
                messages=[
                    {"role": "user", "content": query_input.question},
                    {"role": "assistant", "content": agent_response.content},
                ],
                user_id=user_id,
                metadata=metadata,
            )
        except MemoryServiceError as e:
            logger.warning(f"Memory storage failed (graceful degradation): {e}")

        # Transform agent citations to QueryResponse format
        citations = _transform_agent_citations(agent_response.citations)

        execution_time = time.time() - start_time

        # Log for analytics
        logger.info(
            f"Agent query processed: user={user_id}, "
            f"question='{query_input.question[:50]}...', "
            f"tool={agent_response.tool_used}, "
            f"citations={len(citations)}, "
            f"time={execution_time:.2f}s"
        )

        return QueryResponse(
            answer=agent_response.content,
            sql=None,  # Agent doesn't expose SQL directly
            data=[],   # Agent formats data in response
            citations=citations,
            executed_at=datetime.now(timezone.utc).isoformat(),
            execution_time_seconds=execution_time,
            row_count=0,
            error=bool(agent_response.error),
            suggestions=agent_response.suggested_questions or None,
            # Story 5.7: Include agent metadata
            meta={
                "agent_tool": agent_response.tool_used,
                "follow_up_questions": agent_response.suggested_questions,
                "grounding_score": _calculate_grounding_score(agent_response.citations),
            },
        )

    except AgentError as e:
        logger.error(f"Agent error for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"Unexpected error in agent processing for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again.",
        )


async def _process_via_text_to_sql(
    query_input: QueryInput,
    enable_grounding: bool,
    current_user: CurrentUser,
    service: TextToSQLService,
    cited_service: CitedResponseService,
) -> QueryResponse:
    """
    Process query through legacy Text-to-SQL path.

    Maintained for backward compatibility and as fallback when agent is not configured.
    """
    try:
        # Build context dict if provided
        context = None
        if query_input.context:
            context = query_input.context.model_dump(exclude_none=True)

        # Execute query
        result = await service.query(
            question=query_input.question,
            user_id=current_user.id,
            context=context,
        )

        # Story 4.5: Enhance response with grounding validation and citations
        if enable_grounding and not result.get("error"):
            try:
                # Extract source table from SQL
                source_table = _extract_source_table(result.get("sql"))

                # Process response through citation service
                cited_result = await cited_service.process_chat_response(
                    raw_response=result["answer"],
                    query_text=query_input.question,
                    user_id=current_user.id,
                    sql=result.get("sql"),
                    data=result.get("data", []),
                    source_table=source_table,
                    context=context,
                )

                # Update result with cited response
                result["answer"] = cited_result["answer"]
                result["citations"] = cited_result["citations"]

                # Add Story 4.5 metadata
                if "meta" not in result:
                    result["meta"] = {}
                result["meta"]["grounding_score"] = cited_result.get("grounding_score", 0.0)
                result["meta"]["ungrounded_claims"] = cited_result.get("ungrounded_claims", [])
                result["meta"]["citation_meta"] = cited_result.get("meta", {})

            except Exception as e:
                # Story 4.5 graceful degradation - continue without citations
                logger.warning(f"Citation generation failed (graceful degradation): {e}")

        # Log for analytics
        logger.info(
            f"Query processed: user={current_user.id}, "
            f"question='{query_input.question[:50]}...', "
            f"rows={result.get('row_count', 0)}, "
            f"grounding={result.get('meta', {}).get('grounding_score', 'N/A')}"
        )

        # Convert citations to Pydantic models
        citations = [
            Citation(**c) for c in result.get("citations", [])
        ]

        return QueryResponse(
            answer=result["answer"],
            sql=result.get("sql"),
            data=result.get("data", []),
            citations=citations,
            executed_at=result.get("executed_at", ""),
            execution_time_seconds=result.get("execution_time_seconds", 0),
            row_count=result.get("row_count", 0),
            error=result.get("error", False),
            suggestions=result.get("suggestions"),
        )

    except TextToSQLError as e:
        logger.error(f"Text-to-SQL service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"Unexpected error processing query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again.",
        )


def _transform_agent_citations(agent_citations: List[Dict[str, Any]]) -> List[Citation]:
    """
    Transform agent citations to QueryResponse Citation format.

    Story 5.7: Ensures agent citations are compatible with existing frontend.

    Args:
        agent_citations: Citations from agent response

    Returns:
        List of Citation models for QueryResponse
    """
    citations = []
    for cit in agent_citations:
        try:
            citations.append(Citation(
                value=cit.get("display_text", ""),
                field=cit.get("source", "agent"),
                table=cit.get("table", cit.get("source", "agent_data")),
                context=f"{cit.get('source', '')} at {cit.get('timestamp', '')}",
            ))
        except Exception as e:
            logger.warning(f"Failed to transform citation: {e}")
    return citations


def _calculate_grounding_score(citations: List[Dict[str, Any]]) -> float:
    """
    Calculate grounding score based on citation confidence.

    Story 5.7: Provides grounding score for UI display.

    Args:
        citations: List of agent citations with confidence scores

    Returns:
        Average grounding score (0.0 to 1.0)
    """
    if not citations:
        return 0.0

    confidences = [
        cit.get("confidence", 0.5)
        for cit in citations
        if isinstance(cit.get("confidence"), (int, float))
    ]

    if not confidences:
        return 0.5  # Default moderate confidence

    return sum(confidences) / len(confidences)


@router.get(
    "/tables",
    response_model=TablesResponse,
    summary="Get available tables",
    description="Get information about tables available for querying.",
)
async def get_tables(
    current_user: CurrentUser = Depends(get_current_user),
    service: TextToSQLService = Depends(get_service),
) -> TablesResponse:
    """
    Get information about available tables for querying.

    AC#8: GET /api/chat/tables endpoint

    Args:
        current_user: Authenticated user from JWT
        service: Text-to-SQL service instance

    Returns:
        TablesResponse with table names and descriptions
    """
    # Get table descriptions from prompts module
    descriptions = {
        table: desc.split("\n")[1].strip()  # First line of description
        for table, desc in TABLE_DESCRIPTIONS.items()
    }

    return TablesResponse(
        tables=service.ALLOWED_TABLES,
        descriptions=descriptions,
    )


@router.get(
    "/status",
    response_model=ChatServiceStatus,
    summary="Get chat service status",
    description="Check if the chat/Text-to-SQL service is properly configured and initialized.",
)
async def get_chat_status(
    service: TextToSQLService = Depends(get_service),
) -> ChatServiceStatus:
    """
    Get chat service status (public endpoint, no auth required).

    Returns:
        Dict with configuration and initialization status
    """
    configured = service.is_configured()
    initialized = service.is_initialized()

    if initialized:
        status_str = "ready"
    elif configured:
        status_str = "not_initialized"
    else:
        status_str = "not_configured"

    return ChatServiceStatus(
        configured=configured,
        initialized=initialized,
        status=status_str,
        allowed_tables=service.ALLOWED_TABLES if configured else [],
    )


@router.get(
    "/health",
    summary="Health check",
    description="Simple health check for the chat service.",
)
async def health_check(
    service: TextToSQLService = Depends(get_service),
) -> dict:
    """
    Health check endpoint.

    Returns:
        Simple health status
    """
    return {
        "status": "healthy" if service.is_configured() else "degraded",
        "service": "text-to-sql",
    }
