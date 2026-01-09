"""
ManufacturingTool Base Class (Story 5.1)

Defines the base class for all agent tools with:
- Structured ToolResult responses
- Citation support for NFR1 compliance
- Async execution pattern

AC#2: ManufacturingTool Base Class
- Tool has required properties: name, description, args_schema
- Tool has citations_required flag (default: True)
- Tool implements async _arun() method returning ToolResult

AC#5: Structured Response with Citations
- Response includes citations array with source, query, and timestamp
- Response follows the ToolResult schema
"""

import json
import logging
from abc import abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    """Get current UTC time in a timezone-aware manner."""
    return datetime.now(timezone.utc)

logger = logging.getLogger(__name__)


class Citation(BaseModel):
    """
    Citation for data source tracking.

    Follows the citation format from Story 4.5 for consistency.
    Used to track where tool data came from for NFR1 compliance.
    """

    source: str = Field(
        ...,
        description="Data source identifier (e.g., 'daily_summaries', 'live_snapshots')"
    )
    query: str = Field(
        ...,
        description="Query or operation that retrieved the data"
    )
    timestamp: datetime = Field(
        default_factory=_utcnow,
        description="When the data was retrieved"
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

    def to_display_text(self) -> str:
        """Generate display text for inline citation."""
        if self.table and self.record_id:
            return f"[Source: {self.table}/{self.record_id}]"
        elif self.table:
            return f"[Source: {self.table}]"
        else:
            return f"[Source: {self.source}]"


class ToolResult(BaseModel):
    """
    Structured result from a ManufacturingTool execution.

    AC#5: Response includes citations array with source, query, and timestamp.
    All tool responses follow this schema for consistent formatting.
    """

    data: Any = Field(
        ...,
        description="The actual data returned by the tool"
    )
    citations: List[Citation] = Field(
        default_factory=list,
        description="List of citations for data sources"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the tool execution"
    )
    cached_at: Optional[datetime] = Field(
        None,
        description="Timestamp if result was served from cache"
    )
    success: bool = Field(
        default=True,
        description="Whether the tool execution was successful"
    )
    error_message: Optional[str] = Field(
        None,
        description="Error message if success is False"
    )

    def to_agent_response(self) -> str:
        """
        Convert ToolResult to string for agent consumption.

        Returns formatted data with inline citations.
        """
        if not self.success:
            return f"Error: {self.error_message}"

        # Format data as string
        if isinstance(self.data, dict):
            data_str = json.dumps(self.data, indent=2, default=str)
        elif isinstance(self.data, list):
            data_str = json.dumps(self.data, indent=2, default=str)
        else:
            data_str = str(self.data)

        # Append citation references
        if self.citations:
            citation_refs = " ".join(
                c.to_display_text() for c in self.citations
            )
            return f"{data_str}\n\nData sources: {citation_refs}"

        return data_str


class ManufacturingTool(BaseTool):
    """
    Base class for all manufacturing agent tools.

    AC#2: ManufacturingTool Base Class
    - All tools must define: name, description, args_schema
    - citations_required flag controls citation generation
    - _arun() method returns structured ToolResult

    Subclasses should:
    1. Define name, description, and args_schema class attributes
    2. Implement async _arun() method
    3. Return ToolResult with data and citations

    Example:
        class AssetStatusTool(ManufacturingTool):
            name = "asset_status"
            description = "Get current status of a manufacturing asset"
            args_schema = AssetStatusInput
            citations_required = True

            async def _arun(self, asset_id: str) -> ToolResult:
                # Fetch asset status...
                return ToolResult(
                    data={"status": "running"},
                    citations=[Citation(source="live_snapshots", query="...")]
                )
    """

    # Required class attributes (must be overridden by subclasses)
    name: str
    description: str
    args_schema: Type[BaseModel]

    # Tool configuration
    citations_required: bool = Field(
        default=True,
        description="Whether this tool should generate citations"
    )

    # Internal state
    return_direct: bool = Field(
        default=False,
        description="If True, return tool output directly without LLM processing"
    )

    @abstractmethod
    async def _arun(self, **kwargs) -> ToolResult:
        """
        Execute the tool asynchronously and return structured results.

        This method must be implemented by all subclasses.

        Args:
            **kwargs: Arguments matching the args_schema

        Returns:
            ToolResult with data and citations

        Raises:
            NotImplementedError: If not overridden by subclass
        """
        raise NotImplementedError("Subclasses must implement _arun()")

    def _run(self, **kwargs) -> ToolResult:
        """
        Synchronous execution - raises error to enforce async usage.

        All tools should use async _arun() for consistency with
        the async FastAPI environment.
        """
        raise NotImplementedError(
            f"Tool '{self.name}' must be called asynchronously. "
            "Use _arun() or ainvoke() instead of _run()."
        )

    def _create_citation(
        self,
        source: str,
        query: str,
        table: Optional[str] = None,
        record_id: Optional[str] = None,
        asset_id: Optional[str] = None,
        confidence: float = 1.0,
    ) -> Citation:
        """
        Helper method to create a citation.

        Args:
            source: Data source identifier
            query: Query or operation description
            table: Database table name
            record_id: Specific record identifier
            asset_id: Asset identifier
            confidence: Confidence score (0.0-1.0)

        Returns:
            Citation instance
        """
        return Citation(
            source=source,
            query=query,
            table=table,
            record_id=record_id,
            asset_id=asset_id,
            confidence=confidence,
            timestamp=_utcnow(),
        )

    def _create_error_result(self, error_message: str) -> ToolResult:
        """
        Helper method to create an error result.

        Args:
            error_message: Description of the error

        Returns:
            ToolResult with success=False
        """
        logger.error(f"Tool '{self.name}' error: {error_message}")
        return ToolResult(
            data=None,
            citations=[],
            metadata={"error": True},
            success=False,
            error_message=error_message,
        )

    def _create_success_result(
        self,
        data: Any,
        citations: Optional[List[Citation]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ToolResult:
        """
        Helper method to create a successful result.

        Args:
            data: The tool output data
            citations: List of citations
            metadata: Additional metadata

        Returns:
            ToolResult with success=True
        """
        return ToolResult(
            data=data,
            citations=citations or [],
            metadata=metadata or {},
            success=True,
        )
