"""
Memory Models (Story 4.1)

Pydantic models for memory API request/response schemas.

AC#4: Task 4 - Pydantic models for memory operations
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class MemoryMessage(BaseModel):
    """
    Single message in a conversation.

    Compatible with LangChain message format.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role": "user",
                "content": "What's wrong with Grinder 5?",
            }
        }
    )

    role: str = Field(
        ...,
        description="Message role: 'user', 'assistant', or 'system'",
        examples=["user", "assistant", "system"]
    )
    content: str = Field(
        ...,
        description="Message content text",
        min_length=1
    )


class MemoryMetadata(BaseModel):
    """
    Metadata for a stored memory.

    AC#3: Includes user_id and timestamp
    AC#4: Includes optional asset_id
    """

    model_config = ConfigDict(
        extra="allow"  # Allow additional fields
    )

    user_id: Optional[str] = Field(
        None,
        description="User identifier from JWT claims"
    )
    asset_id: Optional[str] = Field(
        None,
        description="Asset identifier from Plant Object Model"
    )
    session_id: Optional[str] = Field(
        None,
        description="Session identifier for grouping conversations"
    )
    timestamp: Optional[str] = Field(
        None,
        description="ISO timestamp when memory was created"
    )


class MemoryInput(BaseModel):
    """
    Input schema for storing a memory.

    AC#3: User Session Memory Storage
    AC#4: Asset History Memory Storage
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "messages": [
                    {"role": "user", "content": "Why is Grinder 5 running slow?"},
                    {"role": "assistant", "content": "Grinder 5 shows 15% OEE gap..."}
                ],
                "metadata": {
                    "session_id": "session-123",
                    "asset_id": "asset-456"
                }
            }
        }
    )

    messages: List[MemoryMessage] = Field(
        ...,
        description="List of messages to store as memory",
        min_length=1
    )
    metadata: Optional[MemoryMetadata] = Field(
        None,
        description="Additional metadata for the memory"
    )


class MemoryOutput(BaseModel):
    """
    Output schema for a retrieved memory.

    AC#5: Memory Retrieval for Context
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "mem-123",
                "memory": "User asked about Grinder 5 performance issues",
                "score": 0.85,
                "metadata": {
                    "user_id": "user-123",
                    "asset_id": "asset-456",
                    "timestamp": "2026-01-06T10:30:00Z"
                }
            }
        }
    )

    id: str = Field(
        ...,
        description="Unique memory identifier"
    )
    memory: str = Field(
        ...,
        description="Memory content text"
    )
    score: Optional[float] = Field(
        None,
        description="Similarity score (0-1) for search results",
        ge=0.0,
        le=1.0
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Memory metadata including user_id, asset_id, timestamp"
    )


class MemoryStoreResponse(BaseModel):
    """
    Response schema for storing a memory.

    AC#6: Memory Service API response
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "mem-123",
                "status": "stored",
                "message": "Memory stored successfully"
            }
        }
    )

    id: str = Field(
        ...,
        description="Unique identifier for the stored memory"
    )
    status: str = Field(
        ...,
        description="Status of the operation: 'stored' or 'error'"
    )
    message: Optional[str] = Field(
        None,
        description="Additional message about the operation"
    )


class MemorySearchRequest(BaseModel):
    """
    Request schema for searching memories.

    AC#5: Memory Retrieval for Context
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "Grinder 5 performance issues",
                "limit": 5,
                "threshold": 0.7,
                "asset_id": "asset-456"
            }
        }
    )

    query: str = Field(
        ...,
        description="Search query text",
        min_length=1
    )
    limit: Optional[int] = Field(
        5,
        description="Maximum number of results",
        ge=1,
        le=50
    )
    threshold: Optional[float] = Field(
        0.7,
        description="Minimum similarity threshold",
        ge=0.0,
        le=1.0
    )
    asset_id: Optional[str] = Field(
        None,
        description="Filter by asset_id"
    )


class MemorySearchResponse(BaseModel):
    """
    Response schema for memory search.

    AC#5: Memory Retrieval for Context
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "Grinder 5 performance",
                "count": 3,
                "memories": []
            }
        }
    )

    query: str = Field(
        ...,
        description="Original search query"
    )
    count: int = Field(
        ...,
        description="Number of memories returned"
    )
    memories: List[MemoryOutput] = Field(
        default_factory=list,
        description="List of matching memories"
    )


class MemoryListResponse(BaseModel):
    """
    Response schema for listing all memories.

    AC#6: Memory Service API
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "user-123",
                "count": 10,
                "memories": []
            }
        }
    )

    user_id: str = Field(
        ...,
        description="User identifier"
    )
    count: int = Field(
        ...,
        description="Total number of memories"
    )
    memories: List[MemoryOutput] = Field(
        default_factory=list,
        description="List of user memories"
    )


class MemoryContextResponse(BaseModel):
    """
    Response schema for context retrieval.

    AC#8: LangChain Integration Preparation
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "What about Grinder 5?",
                "context": [
                    {"role": "system", "content": "Previous context: User asked about Grinder 5 OEE..."}
                ]
            }
        }
    )

    query: str = Field(
        ...,
        description="Original query"
    )
    context: List[Dict[str, str]] = Field(
        default_factory=list,
        description="LangChain-compatible context messages"
    )


class AssetHistoryResponse(BaseModel):
    """
    Response schema for asset-specific memory history.

    AC#4: Asset History Memory Storage
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "asset_id": "asset-456",
                "asset_name": "Grinder 5",
                "count": 5,
                "memories": []
            }
        }
    )

    asset_id: str = Field(
        ...,
        description="Asset identifier"
    )
    asset_name: Optional[str] = Field(
        None,
        description="Human-readable asset name"
    )
    count: int = Field(
        ...,
        description="Number of memories for this asset"
    )
    memories: List[MemoryOutput] = Field(
        default_factory=list,
        description="List of asset-related memories"
    )
