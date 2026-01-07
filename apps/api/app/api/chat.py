"""
Chat API Endpoints (Story 4.2)

REST API for Text-to-SQL natural language query interface.

AC#8: API Endpoint Design
- POST /api/chat/query with body { "question": string, "context"?: object }
- Responses follow format { "answer": string, "sql": string, "data": object, "citations": array }
- Protected with Supabase JWT authentication
- Rate limiting implemented
"""

import logging
import time
from collections import defaultdict
from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException, status

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

    The system will:
    1. Parse your question into a SQL query
    2. Execute the query against the manufacturing database
    3. Return a natural language answer with data citations

    **Supported Topics:**
    - OEE (Overall Equipment Effectiveness)
    - Downtime and production output
    - Financial loss calculations
    - Safety events and incidents
    - Asset comparisons

    **Example Questions:**
    - "What was Grinder 5's OEE yesterday?"
    - "Which asset had the most downtime last week?"
    - "Show me all safety events this month"
    - "What's the total financial loss for the Grinding area?"
    """,
)
async def query_data(
    query_input: QueryInput,
    current_user: CurrentUser = Depends(get_current_user),
    service: TextToSQLService = Depends(get_service),
) -> QueryResponse:
    """
    Process a natural language query about plant data.

    AC#2: Natural language question is processed
    AC#3: Query executes and returns formatted results
    AC#4: Response includes data citations
    AC#5: Input is validated for security
    AC#6: Errors are handled gracefully
    AC#7: Context is accepted for enhancement
    AC#8: Protected with Supabase JWT authentication

    Args:
        query_input: The question and optional context
        current_user: Authenticated user from JWT
        service: Text-to-SQL service instance

    Returns:
        QueryResponse with answer, SQL, data, and citations

    Raises:
        HTTPException 429: If rate limit exceeded
        HTTPException 503: If service not configured
        HTTPException 500: If unexpected error
    """
    # AC#8: Rate limiting
    check_rate_limit(current_user.id)

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

        # Log for analytics
        logger.info(
            f"Query processed: user={current_user.id}, "
            f"question='{query_input.question[:50]}...', "
            f"rows={result.get('row_count', 0)}"
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
