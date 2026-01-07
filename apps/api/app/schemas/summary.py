"""
Smart Summary Schemas

Pydantic models for Smart Summary API requests and responses.

Story: 3.5 - Smart Summary Generator
AC: #7 - API Endpoint Response Schema
"""

from datetime import date as date_type, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Citation(BaseModel):
    """
    Structured citation from summary text.

    AC#5: Citations reference specific asset names, timestamps, or metric values.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "asset_name": "Grinder 5",
                "metric_name": "OEE",
                "metric_value": "72%",
                "source_table": "daily_summaries",
                "timestamp": "2024-01-15",
            }
        }
    )

    asset_name: Optional[str] = Field(None, description="Referenced asset name")
    metric_name: str = Field(..., description="Name of the metric")
    metric_value: str = Field(..., description="Value of the metric")
    source_table: str = Field(..., description="Source database table")
    timestamp: Optional[str] = Field(None, description="Reference timestamp")


class SmartSummaryResponse(BaseModel):
    """
    Smart Summary API response model.

    AC#6: Response includes id, date, summary_text, citations_json,
    model_used, prompt_tokens, completion_tokens.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "date": "2024-01-15",
                "summary_text": "## Executive Summary\n\nProduction targets were missed...",
                "citations": [
                    {
                        "asset_name": "Grinder 5",
                        "metric_name": "OEE",
                        "metric_value": "72%",
                        "source_table": "daily_summaries",
                    }
                ],
                "model_used": "gpt-4-turbo-preview",
                "prompt_tokens": 1200,
                "completion_tokens": 500,
                "generation_duration_ms": 2500,
                "is_fallback": False,
                "created_at": "2024-01-16T06:30:00Z",
            }
        }
    )

    id: Optional[str] = Field(None, description="UUID of the summary")
    date: date_type = Field(..., description="Report date (T-1)")
    summary_text: str = Field(..., description="Markdown-formatted summary")
    citations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Structured citations for verification"
    )
    model_used: str = Field(..., description="LLM model identifier")
    prompt_tokens: int = Field(0, ge=0, description="Prompt tokens used")
    completion_tokens: int = Field(0, ge=0, description="Completion tokens used")
    generation_duration_ms: int = Field(0, ge=0, description="Generation time in ms")
    is_fallback: bool = Field(False, description="Whether fallback template was used")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")


class GenerateSummaryRequest(BaseModel):
    """
    Request model for manual summary generation.

    AC#7: Supports POST /api/summaries/generate endpoint.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "target_date": "2024-01-15",
                "regenerate": False,
            }
        }
    )

    target_date: Optional[date_type] = Field(
        None,
        description="Date to generate summary for (defaults to T-1)"
    )
    regenerate: bool = Field(
        False,
        description="Force regeneration even if cached"
    )


class TokenUsageSummary(BaseModel):
    """
    Token usage summary for cost management.

    AC#10: Aggregated token usage tracking.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "period_start": "2024-01-01",
                "period_end": "2024-01-31",
                "total_generations": 31,
                "total_prompt_tokens": 37200,
                "total_completion_tokens": 15500,
                "total_tokens": 52700,
                "estimated_cost_usd": 1.23,
            }
        }
    )

    period_start: str = Field(..., description="Start of reporting period")
    period_end: str = Field(..., description="End of reporting period")
    total_generations: int = Field(0, ge=0, description="Number of generations")
    total_prompt_tokens: int = Field(0, ge=0, description="Total prompt tokens")
    total_completion_tokens: int = Field(0, ge=0, description="Total completion tokens")
    total_tokens: int = Field(0, ge=0, description="Combined token count")
    estimated_cost_usd: float = Field(0.0, ge=0, description="Estimated cost in USD")
    error: Optional[str] = Field(None, description="Error message if query failed")


class LLMHealthResponse(BaseModel):
    """
    LLM health check response.

    AC#1: Connection validated with health check.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "provider": "openai",
                "model": "gpt-4-turbo-preview",
                "message": "LLM service is responding",
                "healthy": True,
            }
        }
    )

    status: str = Field(..., description="Health status")
    provider: str = Field(..., description="LLM provider name")
    model: Optional[str] = Field(None, description="Model being used")
    message: str = Field(..., description="Status message")
    healthy: bool = Field(..., description="Whether service is healthy")
