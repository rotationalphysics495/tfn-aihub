"""
Agent Pydantic Models (Story 5.1)

Request and response models for the Agent API endpoints.

AC#5: Structured Response with Citations
AC#7: Agent Chat Endpoint
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class FollowUpQuestion(BaseModel):
    """Suggested follow-up question for the user."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "What was the downtime breakdown?",
                "category": "analysis"
            }
        }
    )

    question: str = Field(
        ...,
        description="The suggested follow-up question text"
    )
    category: Optional[str] = Field(
        None,
        description="Category of the question (analysis, comparison, drill-down)"
    )


class AgentCitation(BaseModel):
    """
    Citation from agent tool execution.

    Follows the citation format from Story 4.5 for consistency.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source": "daily_summaries",
                "query": "SELECT * FROM daily_summaries WHERE asset_id = 'grinder-5'",
                "timestamp": "2026-01-09T10:30:00Z",
                "table": "daily_summaries",
                "record_id": "550e8400-e29b-41d4-a716-446655440000",
                "confidence": 0.95,
                "display_text": "[Source: daily_summaries/2026-01-08]"
            }
        }
    )

    source: str = Field(
        ...,
        description="Data source identifier"
    )
    query: str = Field(
        ...,
        description="Query or operation that retrieved the data"
    )
    timestamp: str = Field(
        ...,
        description="When the data was retrieved (ISO format)"
    )
    table: Optional[str] = Field(
        None,
        description="Database table name if applicable"
    )
    record_id: Optional[str] = Field(
        None,
        description="Specific record identifier"
    )
    asset_id: Optional[str] = Field(
        None,
        description="Asset identifier from Plant Object Model"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score for this citation"
    )
    display_text: str = Field(
        ...,
        description="Human-readable citation text for display"
    )


class QueryContext(BaseModel):
    """Optional context for enhancing agent queries."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "asset_focus": "Grinder 5",
                "time_range": "yesterday",
                "previous_queries": ["What is OEE?"]
            }
        }
    )

    asset_focus: Optional[str] = Field(
        None,
        description="Specific asset to focus on"
    )
    time_range: Optional[str] = Field(
        None,
        description="Time range context (today, yesterday, last week)"
    )
    previous_queries: Optional[List[str]] = Field(
        None,
        description="Previous queries in this conversation"
    )


class ChatMessage(BaseModel):
    """A single message in the chat history."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role": "user",
                "content": "What was Grinder 5's OEE yesterday?"
            }
        }
    )

    role: str = Field(
        ...,
        description="Message role: 'user' or 'assistant'"
    )
    content: str = Field(
        ...,
        description="Message content"
    )


class AgentChatRequest(BaseModel):
    """
    Request body for POST /api/agent/chat endpoint.

    AC#7: Agent Chat Endpoint
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "What was Grinder 5's OEE yesterday?",
                "context": {
                    "asset_focus": "Grinder 5",
                    "time_range": "yesterday"
                },
                "chat_history": [
                    {"role": "user", "content": "Show me Grinder 5 status"},
                    {"role": "assistant", "content": "Grinder 5 is currently running..."}
                ]
            }
        }
    )

    message: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="User's natural language message"
    )
    context: Optional[QueryContext] = Field(
        None,
        description="Optional context for enhancing the query"
    )
    chat_history: Optional[List[ChatMessage]] = Field(
        None,
        description="Previous messages in the conversation"
    )


class AgentResponse(BaseModel):
    """
    Response from POST /api/agent/chat endpoint.

    AC#5: Structured Response with Citations
    AC#7: Agent Chat Endpoint - response follows AgentResponse schema
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "Based on yesterday's data, Grinder 5 had an OEE of 87.5%. [Source: daily_summaries/2026-01-08]",
                "tool_used": "asset_status",
                "citations": [
                    {
                        "source": "daily_summaries",
                        "query": "SELECT * FROM daily_summaries",
                        "timestamp": "2026-01-09T10:30:00Z",
                        "table": "daily_summaries",
                        "confidence": 0.95,
                        "display_text": "[Source: daily_summaries/2026-01-08]"
                    }
                ],
                "suggested_questions": [
                    "What caused the downtime?",
                    "How does this compare to last week?"
                ],
                "execution_time_ms": 1250.5,
                "meta": {
                    "model": "gpt-4-turbo-preview",
                    "timestamp": "2026-01-09T10:30:00Z"
                }
            }
        }
    )

    content: str = Field(
        ...,
        description="Natural language response from the agent"
    )
    tool_used: Optional[str] = Field(
        None,
        description="Name of the tool that was invoked, if any"
    )
    citations: List[AgentCitation] = Field(
        default_factory=list,
        description="Data source citations for NFR1 compliance"
    )
    suggested_questions: List[str] = Field(
        default_factory=list,
        description="Suggested follow-up questions"
    )
    execution_time_ms: float = Field(
        default=0.0,
        description="Time taken to process the message in milliseconds"
    )
    meta: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional response metadata"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if processing failed"
    )


class AgentServiceStatus(BaseModel):
    """Status information for the agent service."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "configured": True,
                "initialized": True,
                "status": "ready",
                "available_tools": ["asset_status", "production_query"],
                "model": "gpt-4-turbo-preview"
            }
        }
    )

    configured: bool = Field(
        ...,
        description="Whether the agent is properly configured"
    )
    initialized: bool = Field(
        ...,
        description="Whether the agent has been initialized"
    )
    status: str = Field(
        ...,
        description="Current status: ready, not_initialized, not_configured"
    )
    available_tools: List[str] = Field(
        default_factory=list,
        description="List of available tool names"
    )
    model: Optional[str] = Field(
        None,
        description="LLM model being used"
    )
