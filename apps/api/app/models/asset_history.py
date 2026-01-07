"""
Asset History Models (Story 4.4)

Pydantic models for asset history API request/response schemas.

AC#1: Asset History Data Model
AC#3: History Storage API
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EventType(str, Enum):
    """Types of asset history events (AC#1 Task 3.5)."""
    DOWNTIME = "downtime"
    MAINTENANCE = "maintenance"
    RESOLUTION = "resolution"
    NOTE = "note"
    INCIDENT = "incident"


class Outcome(str, Enum):
    """Possible outcomes for asset history events."""
    RESOLVED = "resolved"
    ONGOING = "ongoing"
    ESCALATED = "escalated"
    DEFERRED = "deferred"


class Source(str, Enum):
    """Source of asset history entries (AC#5)."""
    MANUAL = "manual"
    SYSTEM = "system"
    AI_GENERATED = "ai-generated"


class AssetHistoryBase(BaseModel):
    """
    Base model for asset history entries (AC#1 Task 3.2).

    Contains common fields used across create and read operations.
    """

    event_type: EventType = Field(
        ...,
        description="Type of event: downtime, maintenance, resolution, note, incident"
    )
    title: str = Field(
        ...,
        description="Short title describing the event",
        min_length=1,
        max_length=255
    )
    description: Optional[str] = Field(
        None,
        description="Detailed description of the event"
    )
    resolution: Optional[str] = Field(
        None,
        description="How the issue was resolved (if applicable)"
    )
    outcome: Optional[Outcome] = Field(
        None,
        description="Current status: resolved, ongoing, escalated, deferred"
    )
    source: Source = Field(
        default=Source.MANUAL,
        description="How the entry was created: manual, system, ai-generated"
    )
    related_record_type: Optional[str] = Field(
        None,
        description="Type of related record (e.g., downtime_event, safety_event)"
    )
    related_record_id: Optional[UUID] = Field(
        None,
        description="UUID of the related record"
    )


class AssetHistoryCreate(AssetHistoryBase):
    """
    Request schema for creating an asset history entry (AC#3 Task 6.2).

    POST /api/assets/{asset_id}/history
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "event_type": "maintenance",
                "title": "Bearing replacement on Grinder 5",
                "description": "Replaced worn bearing assembly due to excessive vibration",
                "resolution": "Installed new SKF bearing assembly, recalibrated alignment",
                "outcome": "resolved",
                "source": "manual",
                "related_record_type": "downtime_event",
                "related_record_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }
    )


class AssetHistoryRead(AssetHistoryBase):
    """
    Response schema for reading an asset history entry (AC#3 Task 3.2).

    Includes all database fields.
    """

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "asset_id": "550e8400-e29b-41d4-a716-446655440000",
                "event_type": "maintenance",
                "title": "Bearing replacement on Grinder 5",
                "description": "Replaced worn bearing assembly due to excessive vibration",
                "resolution": "Installed new SKF bearing assembly, recalibrated alignment",
                "outcome": "resolved",
                "source": "manual",
                "created_at": "2026-01-06T10:30:00Z",
                "updated_at": "2026-01-06T10:30:00Z"
            }
        }
    )

    id: UUID = Field(
        ...,
        description="Unique identifier for the history entry"
    )
    asset_id: UUID = Field(
        ...,
        description="Asset this history entry belongs to"
    )
    created_at: datetime = Field(
        ...,
        description="When the entry was created"
    )
    updated_at: datetime = Field(
        ...,
        description="When the entry was last modified"
    )
    created_by: Optional[UUID] = Field(
        None,
        description="User who created this entry"
    )


class AssetHistorySearchQuery(BaseModel):
    """
    Request schema for searching asset history (AC#3 Task 3.3).

    GET /api/assets/{asset_id}/history/search?q=...
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "bearing failure vibration",
                "limit": 5,
                "event_types": ["downtime", "maintenance"]
            }
        }
    )

    query: str = Field(
        ...,
        description="Search query text for semantic search",
        min_length=1
    )
    limit: int = Field(
        default=5,
        description="Maximum number of results",
        ge=1,
        le=50
    )
    event_types: Optional[List[EventType]] = Field(
        None,
        description="Filter by event types"
    )


class AssetHistorySearchResult(BaseModel):
    """
    Single result from semantic search (AC#3).

    Includes similarity score from vector search.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "asset_id": "550e8400-e29b-41d4-a716-446655440000",
                "event_type": "maintenance",
                "title": "Bearing replacement on Grinder 5",
                "description": "Replaced worn bearing assembly",
                "resolution": "Installed new SKF bearing assembly",
                "similarity_score": 0.89,
                "created_at": "2026-01-06T10:30:00Z"
            }
        }
    )

    id: UUID = Field(
        ...,
        description="History entry ID"
    )
    asset_id: UUID = Field(
        ...,
        description="Asset ID"
    )
    event_type: EventType = Field(
        ...,
        description="Type of event"
    )
    title: str = Field(
        ...,
        description="Event title"
    )
    description: Optional[str] = Field(
        None,
        description="Event description"
    )
    resolution: Optional[str] = Field(
        None,
        description="Resolution if applicable"
    )
    similarity_score: float = Field(
        ...,
        description="Semantic similarity score (0.0-1.0)",
        ge=0.0,
        le=1.0
    )
    created_at: datetime = Field(
        ...,
        description="When the entry was created"
    )


class AssetHistoryForAI(BaseModel):
    """
    Optimized model for LLM context injection (AC#4 Task 3.4).

    Includes citation markers for NFR1 compliance.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "citation_id": "a1b2c3d4",
                "date": "2026-01-06",
                "event_type": "maintenance",
                "title": "Bearing replacement on Grinder 5",
                "summary": "Replaced worn bearing assembly. Resolution: Installed new SKF bearing assembly.",
                "relevance_score": 0.89
            }
        }
    )

    citation_id: str = Field(
        ...,
        description="Short ID for citations (first 8 chars of UUID)"
    )
    date: str = Field(
        ...,
        description="Date of the event (YYYY-MM-DD)"
    )
    event_type: EventType = Field(
        ...,
        description="Type of event"
    )
    title: str = Field(
        ...,
        description="Event title"
    )
    summary: str = Field(
        ...,
        description="Combined description and resolution"
    )
    relevance_score: float = Field(
        ...,
        description="Combined similarity and temporal score",
        ge=0.0,
        le=1.0
    )


class AssetHistoryListResponse(BaseModel):
    """
    Response schema for paginated asset history list (AC#3 Task 6.3).

    GET /api/assets/{asset_id}/history
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "pagination": {
                    "total": 25,
                    "page": 1,
                    "page_size": 10,
                    "has_next": True
                }
            }
        }
    )

    items: List[AssetHistoryRead] = Field(
        default_factory=list,
        description="List of asset history entries"
    )
    pagination: Dict[str, Any] = Field(
        ...,
        description="Pagination information"
    )


class AssetHistorySearchResponse(BaseModel):
    """
    Response schema for semantic search results (AC#3 Task 6.4).

    GET /api/assets/{asset_id}/history/search
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "bearing failure",
                "asset_id": "550e8400-e29b-41d4-a716-446655440000",
                "results": [],
                "count": 0
            }
        }
    )

    query: str = Field(
        ...,
        description="Original search query"
    )
    asset_id: UUID = Field(
        ...,
        description="Asset searched"
    )
    results: List[AssetHistorySearchResult] = Field(
        default_factory=list,
        description="Search results ordered by relevance"
    )
    count: int = Field(
        ...,
        description="Number of results"
    )


class AssetHistoryCreateResponse(BaseModel):
    """
    Response schema for creating asset history (AC#3 Task 6.2).
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "created",
                "message": "Asset history entry created successfully"
            }
        }
    )

    id: UUID = Field(
        ...,
        description="ID of the created history entry"
    )
    status: str = Field(
        ...,
        description="Status of the operation"
    )
    message: Optional[str] = Field(
        None,
        description="Additional information"
    )


class AIContextRequest(BaseModel):
    """
    Request schema for retrieving AI context for an asset.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "Why does Grinder 5 keep failing?",
                "limit": 5,
                "include_temporal_weighting": True
            }
        }
    )

    query: str = Field(
        ...,
        description="The question or context query",
        min_length=1
    )
    limit: int = Field(
        default=5,
        description="Maximum number of history entries to include",
        ge=1,
        le=20
    )
    include_temporal_weighting: bool = Field(
        default=True,
        description="Apply temporal weighting (recent events ranked higher)"
    )


class AIContextResponse(BaseModel):
    """
    Response schema for AI context retrieval (AC#4 Task 8.2).

    Formatted for LLM prompt injection with citations.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "asset_id": "550e8400-e29b-41d4-a716-446655440000",
                "asset_name": "Grinder 5",
                "query": "Why does Grinder 5 keep failing?",
                "context_text": "[History:a1b2c3d4] 2026-01-06: Bearing replacement...",
                "entries": [],
                "entry_count": 3
            }
        }
    )

    asset_id: UUID = Field(
        ...,
        description="Asset ID"
    )
    asset_name: Optional[str] = Field(
        None,
        description="Human-readable asset name"
    )
    query: str = Field(
        ...,
        description="Original query"
    )
    context_text: str = Field(
        ...,
        description="Formatted context text for LLM prompt"
    )
    entries: List[AssetHistoryForAI] = Field(
        default_factory=list,
        description="Individual history entries used"
    )
    entry_count: int = Field(
        ...,
        description="Number of entries in context"
    )
