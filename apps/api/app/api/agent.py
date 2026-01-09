"""
Agent API Endpoints (Story 5.1)

REST API for the Manufacturing Agent chat interface.

AC#7: Agent Chat Endpoint
- POST /api/agent/chat processes messages via the agent
- Request is authenticated via Supabase JWT
- Response follows the AgentResponse schema

AC#8: Error Handling and Logging
- Errors are logged with full context
- User receives helpful error messages
"""

import logging
import time
from collections import defaultdict
from functools import lru_cache
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import get_settings
from app.core.security import get_current_user
from app.models.user import CurrentUser
from app.models.agent import (
    AgentChatRequest,
    AgentResponse,
    AgentCitation,
    AgentServiceStatus,
)
from app.services.agent.executor import (
    ManufacturingAgent,
    get_manufacturing_agent,
    AgentError,
)
from app.services.agent.registry import get_tool_registry

logger = logging.getLogger(__name__)

router = APIRouter()


@lru_cache()
def _get_rate_limit_config():
    """Get rate limit configuration from settings."""
    settings = get_settings()
    return (
        settings.agent_rate_limit_requests,
        settings.agent_rate_limit_window,
    )


# Simple in-memory rate limiter (per-user)
_rate_limit_store: dict = defaultdict(list)


def get_agent() -> ManufacturingAgent:
    """Dependency to get ManufacturingAgent instance."""
    return get_manufacturing_agent()


def check_rate_limit(user_id: str) -> None:
    """
    Check if user has exceeded rate limit.

    AC#7: Rate limiting (configurable via settings)

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
    "/chat",
    response_model=AgentResponse,
    summary="Chat with the manufacturing agent",
    description="""
    Send a natural language message to the manufacturing agent.

    The agent will:
    1. Analyze your message to understand the intent
    2. Select and invoke appropriate tools for your query
    3. Return a response with data and citations

    **Supported Query Types (when tools are available):**
    - Asset status and performance queries
    - OEE (Overall Equipment Effectiveness) analysis
    - Downtime analysis and breakdown
    - Production status vs targets

    **Story 5.1 Features:**
    - Automatic tool selection based on intent (AC#4)
    - Structured responses with citations (AC#5)
    - Graceful handling of unknown intents (AC#6)
    - Full error handling and logging (AC#8)

    **Rate Limiting:**
    - Default: 10 requests per minute per user
    - Configurable via AGENT_RATE_LIMIT_* environment variables
    """,
)
async def chat(
    request: AgentChatRequest,
    current_user: CurrentUser = Depends(get_current_user),
    agent: ManufacturingAgent = Depends(get_agent),
) -> AgentResponse:
    """
    Process a message through the manufacturing agent.

    AC#7: Agent Chat Endpoint
    - POST request to /api/agent/chat
    - Authenticated via Supabase JWT
    - Message processed by the agent
    - Response follows AgentResponse schema

    Args:
        request: Chat request with message and optional context
        current_user: Authenticated user from JWT
        agent: ManufacturingAgent instance

    Returns:
        AgentResponse with content, citations, and metadata

    Raises:
        HTTPException 429: If rate limit exceeded
        HTTPException 503: If agent not configured
        HTTPException 500: If unexpected error
    """
    # Check rate limit
    check_rate_limit(current_user.id)

    # Check if agent is configured
    if not agent.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent service not configured. Please check API keys.",
        )

    try:
        # Convert chat history to list of dicts if provided
        chat_history = None
        if request.chat_history:
            chat_history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.chat_history
            ]

        # Process message through agent
        result = await agent.process_message(
            message=request.message,
            user_id=current_user.id,
            chat_history=chat_history,
        )

        # Convert internal response to API response format
        citations = [
            AgentCitation(
                source=c.get("source", ""),
                query=c.get("query", ""),
                timestamp=c.get("timestamp", ""),
                table=c.get("table"),
                record_id=c.get("record_id"),
                asset_id=c.get("asset_id"),
                confidence=c.get("confidence", 1.0),
                display_text=c.get("display_text", f"[Source: {c.get('source', '')}]"),
            )
            for c in result.citations
        ]

        # Log for analytics
        logger.info(
            f"Agent chat: user={current_user.id}, "
            f"tool={result.tool_used}, "
            f"citations={len(citations)}, "
            f"time={result.execution_time_ms:.2f}ms"
        )

        return AgentResponse(
            content=result.content,
            tool_used=result.tool_used,
            citations=citations,
            suggested_questions=result.suggested_questions,
            execution_time_ms=result.execution_time_ms,
            meta=result.meta,
            error=result.error,
        )

    except AgentError as e:
        logger.error(
            f"Agent error for user {current_user.id}: {e.message}",
            extra={"details": e.details}
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=e.message,
        )
    except Exception as e:
        logger.exception(f"Unexpected error in agent chat for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again.",
        )


@router.get(
    "/status",
    response_model=AgentServiceStatus,
    summary="Get agent service status",
    description="Check if the agent service is properly configured and initialized.",
)
async def get_status(
    agent: ManufacturingAgent = Depends(get_agent),
) -> AgentServiceStatus:
    """
    Get agent service status (public endpoint, no auth required).

    Returns:
        AgentServiceStatus with configuration and initialization status
    """
    settings = get_settings()
    registry = get_tool_registry()

    configured = agent.is_configured
    initialized = agent.is_initialized

    if initialized:
        status_str = "ready"
    elif configured:
        status_str = "not_initialized"
    else:
        status_str = "not_configured"

    return AgentServiceStatus(
        configured=configured,
        initialized=initialized,
        status=status_str,
        available_tools=registry.get_tool_names() if initialized else [],
        model=settings.llm_model if configured else None,
    )


@router.get(
    "/capabilities",
    summary="Get agent capabilities",
    description="Get a list of what the agent can help with based on registered tools.",
)
async def get_capabilities(
    agent: ManufacturingAgent = Depends(get_agent),
) -> dict:
    """
    Get list of agent capabilities.

    AC#6: Suggests what types of questions it can answer.

    Returns:
        Dict with capabilities list
    """
    registry = get_tool_registry()
    tools = registry.get_tools()

    capabilities = []
    for tool in tools:
        capabilities.append({
            "name": tool.name,
            "description": tool.description,
            "citations_required": tool.citations_required,
        })

    return {
        "capabilities": capabilities,
        "tool_count": len(tools),
        "status": "ready" if agent.is_initialized else "not_initialized",
    }


@router.get(
    "/health",
    summary="Health check",
    description="Simple health check for the agent service.",
)
async def health_check(
    agent: ManufacturingAgent = Depends(get_agent),
) -> dict:
    """
    Health check endpoint.

    Returns:
        Simple health status
    """
    return {
        "status": "healthy" if agent.is_configured else "degraded",
        "service": "manufacturing-agent",
        "configured": agent.is_configured,
        "initialized": agent.is_initialized,
    }
