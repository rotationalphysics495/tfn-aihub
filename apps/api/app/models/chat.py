"""
Chat Models (Story 4.2)

Pydantic models for chat/query API request/response schemas.

AC#8: API Endpoint Design - Request/Response models
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class QueryContext(BaseModel):
    """
    Optional context for query enhancement.

    AC#7: Supports future memory enhancement with optional context.
    """

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "example": {
                "asset_focus": "Grinder 5",
                "previous_queries": ["What was the OEE yesterday?"],
                "session_id": "session-123",
            }
        }
    )

    asset_focus: Optional[str] = Field(
        None,
        description="Focus on a specific asset for context"
    )
    previous_queries: Optional[List[str]] = Field(
        None,
        description="Previous queries in the conversation for context"
    )
    session_id: Optional[str] = Field(
        None,
        description="Session identifier for conversation tracking"
    )


class QueryInput(BaseModel):
    """
    Input schema for natural language query.

    AC#8: Request body { "question": string, "context"?: object }
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "What was Grinder 5's OEE yesterday?",
                "context": {
                    "asset_focus": "Grinder 5"
                }
            }
        }
    )

    question: str = Field(
        ...,
        description="Natural language question about plant performance",
        min_length=3,
        max_length=1000,
        examples=[
            "What was Grinder 5's OEE yesterday?",
            "Which asset had the most downtime last week?",
            "Show me all safety events this month",
        ]
    )
    context: Optional[QueryContext] = Field(
        None,
        description="Optional context for query enhancement"
    )


class Citation(BaseModel):
    """
    Data citation for NFR1 compliance.

    AC#4: Specific data points are cited with source table and context.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "value": "87.5%",
                "field": "oee_percentage",
                "table": "daily_summaries",
                "context": "Grinder 5 on 2026-01-04",
            }
        }
    )

    value: str = Field(..., description="The cited value (e.g., '87%')")
    field: str = Field(..., description="The database column name")
    table: str = Field(..., description="The source table")
    context: str = Field(..., description="Business context (e.g., 'Grinder 5 on 2026-01-04')")


class QueryResponse(BaseModel):
    """
    Response schema for natural language query.

    AC#8: Response format { "answer": string, "sql": string, "data": object, "citations": array }
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "answer": "Grinder 5 had an OEE of 87.5% yesterday, which is above the plant target of 85%.",
                "sql": "SELECT a.name, ds.oee_percentage FROM daily_summaries ds JOIN assets a ON ds.asset_id = a.id WHERE a.name ILIKE '%Grinder 5%' AND ds.report_date = CURRENT_DATE - 1",
                "data": [{"name": "Grinder 5", "oee_percentage": 87.5}],
                "citations": [
                    {
                        "value": "87.5%",
                        "field": "oee_percentage",
                        "table": "daily_summaries",
                        "context": "Grinder 5 on 2026-01-04"
                    }
                ],
                "executed_at": "2026-01-05T10:30:00Z",
                "execution_time_seconds": 0.45,
                "row_count": 1,
            }
        }
    )

    answer: str = Field(
        ...,
        description="Natural language response to the question"
    )
    sql: Optional[str] = Field(
        None,
        description="The SQL query that was executed (for transparency)"
    )
    data: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Raw query results"
    )
    citations: List[Citation] = Field(
        default_factory=list,
        description="Data citations for NFR1 compliance"
    )
    executed_at: str = Field(
        ...,
        description="ISO timestamp when query was executed"
    )
    execution_time_seconds: float = Field(
        ...,
        description="Query execution time in seconds"
    )
    row_count: int = Field(
        ...,
        description="Number of rows returned"
    )
    error: bool = Field(
        default=False,
        description="Whether an error occurred"
    )
    suggestions: Optional[List[str]] = Field(
        None,
        description="Suggestions for improving the query (on error)"
    )


class TableInfo(BaseModel):
    """
    Information about available tables.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "daily_summaries",
                "description": "T-1 processed daily reports with OEE metrics",
                "columns": ["asset_id", "report_date", "oee_percentage", "downtime_minutes"],
            }
        }
    )

    name: str = Field(..., description="Table name")
    description: str = Field(..., description="Table description")
    columns: List[str] = Field(default_factory=list, description="Column names")


class TablesResponse(BaseModel):
    """
    Response schema for available tables endpoint.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tables": ["assets", "cost_centers", "daily_summaries", "live_snapshots", "safety_events"],
                "descriptions": {
                    "assets": "Physical equipment/machines in the manufacturing plant",
                    "daily_summaries": "T-1 processed daily reports with OEE metrics",
                }
            }
        }
    )

    tables: List[str] = Field(
        ...,
        description="List of available table names"
    )
    descriptions: Dict[str, str] = Field(
        default_factory=dict,
        description="Table descriptions"
    )


class ChatServiceStatus(BaseModel):
    """
    Response schema for service status endpoint.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "configured": True,
                "initialized": True,
                "status": "ready",
                "allowed_tables": ["assets", "cost_centers", "daily_summaries", "live_snapshots", "safety_events"],
            }
        }
    )

    configured: bool = Field(..., description="Whether required config is present")
    initialized: bool = Field(..., description="Whether service is initialized")
    status: str = Field(..., description="Service status: ready, not_configured, not_initialized")
    allowed_tables: List[str] = Field(
        default_factory=list,
        description="Tables available for querying"
    )
