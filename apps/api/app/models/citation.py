"""
Citation Models (Story 4.5)

Pydantic models for cited response generation with grounding validation.

AC#1: Response Citation Format
AC#2: Data Source Integration
AC#3: Grounding Validation
AC#5: Multi-Source Response Synthesis
AC#6: Mem0 Memory Citations
AC#7: NFR1 Compliance Validation
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SourceType(str, Enum):
    """Type of citation source."""
    DATABASE = "database"
    MEMORY = "memory"
    CALCULATION = "calculation"
    INFERENCE = "inference"


class ClaimType(str, Enum):
    """Type of factual claim in a response."""
    FACTUAL = "factual"
    RECOMMENDATION = "recommendation"
    INFERENCE = "inference"
    HISTORICAL = "historical"


class Citation(BaseModel):
    """
    A citation linking a claim to source data.

    AC#1: Citations follow format: [Source: table_name/record_id] or [Evidence: metric_name at timestamp]
    AC#2: Citations link to actual database records
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "cit-123456",
                "source_type": "database",
                "source_table": "daily_summaries",
                "record_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2026-01-04T10:30:00Z",
                "excerpt": "OEE: 87.5%, Downtime: 47 minutes",
                "confidence": 0.92,
                "display_text": "[Source: daily_summaries/2026-01-04/grinder-5]"
            }
        }
    )

    id: str = Field(
        ...,
        description="Unique identifier for this citation"
    )
    source_type: SourceType = Field(
        ...,
        description="Type of source: database, memory, calculation, inference"
    )
    source_table: Optional[str] = Field(
        None,
        description="Source table name (daily_summaries, live_snapshots, etc.)"
    )
    record_id: Optional[str] = Field(
        None,
        description="Unique identifier of the source record"
    )
    memory_id: Optional[str] = Field(
        None,
        description="Mem0 memory ID for memory citations (AC#6)"
    )
    asset_id: Optional[str] = Field(
        None,
        description="Asset identifier from Plant Object Model"
    )
    timestamp: Optional[str] = Field(
        None,
        description="Timestamp of the source data (ISO format)"
    )
    excerpt: str = Field(
        ...,
        description="Key supporting text/data from the source"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0-1.0) for this citation"
    )
    display_text: str = Field(
        ...,
        description="Human-readable citation text for display"
    )
    claim_text: Optional[str] = Field(
        None,
        description="The claim this citation supports"
    )


class Claim(BaseModel):
    """
    A single factual claim extracted from LLM response.

    AC#3: Claims require grounding validation.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "Grinder 5 had 47 minutes of downtime yesterday",
                "claim_type": "factual",
                "requires_grounding": True,
                "entity_mentions": ["Grinder 5"],
                "metric_mentions": ["downtime", "47 minutes"],
                "temporal_reference": "yesterday"
            }
        }
    )

    text: str = Field(
        ...,
        description="The claim text extracted from response"
    )
    claim_type: ClaimType = Field(
        ...,
        description="Type: factual, recommendation, inference, historical"
    )
    requires_grounding: bool = Field(
        default=True,
        description="Whether this claim requires supporting evidence"
    )
    entity_mentions: List[str] = Field(
        default_factory=list,
        description="Asset/entity names mentioned in the claim"
    )
    metric_mentions: List[str] = Field(
        default_factory=list,
        description="Metrics/values mentioned in the claim"
    )
    temporal_reference: Optional[str] = Field(
        None,
        description="Time reference in the claim (yesterday, last week, etc.)"
    )


class GroundingResult(BaseModel):
    """
    Result of grounding validation for a single claim.

    AC#3: Grounding validation with threshold (0.6 minimum).
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "claim_text": "Grinder 5 had 47 minutes of downtime",
                "is_grounded": True,
                "confidence": 0.92,
                "supporting_citations": [],
                "validation_time_ms": 150
            }
        }
    )

    claim_text: str = Field(
        ...,
        description="The claim being validated"
    )
    is_grounded: bool = Field(
        ...,
        description="Whether the claim is sufficiently grounded"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Grounding confidence score"
    )
    supporting_citations: List[Citation] = Field(
        default_factory=list,
        description="Citations that support this claim"
    )
    validation_time_ms: float = Field(
        default=0.0,
        description="Time taken for validation in milliseconds"
    )
    fallback_text: Optional[str] = Field(
        None,
        description="Alternative text if claim cannot be grounded"
    )


class CitedResponse(BaseModel):
    """
    Response with embedded citations and grounding validation.

    AC#1: All AI responses include inline citations
    AC#3: Each response includes meta.grounding_score
    AC#5: Responses can cite multiple sources
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "resp-123456",
                "response_text": "Based on yesterday's data, Grinder 5 had the highest downtime at 47 minutes [Source: daily_summaries/2026-01-04/asset-grinder-5].",
                "citations": [],
                "claims": [],
                "grounding_score": 0.85,
                "ungrounded_claims": [],
                "meta": {
                    "response_time_ms": 450,
                    "grounding_time_ms": 180,
                    "citation_count": 3,
                    "claim_count": 2
                }
            }
        }
    )

    id: str = Field(
        ...,
        description="Unique identifier for this response"
    )
    response_text: str = Field(
        ...,
        description="Response text with inline citation markers"
    )
    citations: List[Citation] = Field(
        default_factory=list,
        description="List of citations supporting the response"
    )
    claims: List[Claim] = Field(
        default_factory=list,
        description="Extracted claims from the response"
    )
    grounding_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall grounding confidence (0.0-1.0)"
    )
    ungrounded_claims: List[str] = Field(
        default_factory=list,
        description="Claims that couldn't be sufficiently grounded"
    )
    meta: Dict[str, Any] = Field(
        default_factory=dict,
        description="Response metadata (timing, counts, etc.)"
    )


class CitationLogEntry(BaseModel):
    """
    Audit log entry for citation tracking.

    AC#7: Audit log records all citation-response pairs for compliance review.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "log-123456",
                "response_id": "resp-123456",
                "user_id": "user-123",
                "session_id": "session-456",
                "query_text": "Why did Grinder 5 have so much downtime yesterday?",
                "response_text": "Based on the data...",
                "citations": [],
                "grounding_score": 0.85,
                "ungrounded_claims": [],
                "validated_at": "2026-01-05T10:30:00Z",
                "created_at": "2026-01-05T10:30:00Z"
            }
        }
    )

    id: Optional[str] = Field(
        None,
        description="Unique identifier (UUID)"
    )
    response_id: str = Field(
        ...,
        description="ID of the cited response"
    )
    user_id: str = Field(
        ...,
        description="User who made the query"
    )
    session_id: Optional[str] = Field(
        None,
        description="Session identifier"
    )
    query_text: str = Field(
        ...,
        description="Original user query"
    )
    response_text: str = Field(
        ...,
        description="Full response text"
    )
    citations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Array of citation objects"
    )
    grounding_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall grounding score"
    )
    ungrounded_claims: List[str] = Field(
        default_factory=list,
        description="Claims that couldn't be grounded"
    )
    validated_at: Optional[str] = Field(
        None,
        description="When grounding validation completed"
    )
    created_at: Optional[str] = Field(
        None,
        description="When the log entry was created"
    )


class CitationDetailRequest(BaseModel):
    """Request schema for fetching citation details."""

    citation_id: str = Field(
        ...,
        description="The citation ID to fetch details for"
    )


class CitationDetailResponse(BaseModel):
    """
    Response schema for citation detail lookup.

    AC#4: Citation links resolve within 100ms (cached data).
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "cit-123456",
                "source_type": "database",
                "source_data": {
                    "asset_name": "Grinder 5",
                    "report_date": "2026-01-04",
                    "oee_percentage": 87.5,
                    "downtime_minutes": 47
                },
                "related_citations": ["cit-123457", "cit-123458"],
                "fetched_at": "2026-01-05T10:30:00Z"
            }
        }
    )

    id: str = Field(
        ...,
        description="Citation ID"
    )
    source_type: SourceType = Field(
        ...,
        description="Type of source"
    )
    source_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Full source record data"
    )
    related_citations: List[str] = Field(
        default_factory=list,
        description="Other citations from same source"
    )
    fetched_at: str = Field(
        ...,
        description="When the data was fetched"
    )


class SourceLookupRequest(BaseModel):
    """Request schema for source data lookup."""

    source_type: SourceType = Field(
        ...,
        description="Type of source to look up"
    )
    record_id: str = Field(
        ...,
        description="Record ID to fetch"
    )


class SourceLookupResponse(BaseModel):
    """Response schema for source data lookup."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source_type": "database",
                "source_table": "daily_summaries",
                "record_id": "abc123",
                "data": {},
                "fetched_at": "2026-01-05T10:30:00Z"
            }
        }
    )

    source_type: SourceType = Field(
        ...,
        description="Type of source"
    )
    source_table: Optional[str] = Field(
        None,
        description="Database table name"
    )
    record_id: str = Field(
        ...,
        description="Record identifier"
    )
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Source record data"
    )
    fetched_at: str = Field(
        ...,
        description="When the data was fetched"
    )


# Grounding threshold constants (per story spec)
GROUNDING_THRESHOLD_HIGH = 0.8   # Strong citations
GROUNDING_THRESHOLD_MIN = 0.6   # Minimum acceptable
GROUNDING_THRESHOLD_LOW = 0.4   # Weak/insufficient
