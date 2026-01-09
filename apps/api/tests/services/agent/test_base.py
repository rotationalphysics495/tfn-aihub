"""
Tests for ManufacturingTool Base Class (Story 5.1)

AC#2: ManufacturingTool Base Class
- Tool has required properties: name, description, args_schema
- Tool has citations_required flag (default: True)
- Tool implements async _arun() method returning ToolResult
"""

import pytest
from datetime import datetime
from typing import Type
from pydantic import BaseModel, Field

from app.services.agent.base import (
    ManufacturingTool,
    ToolResult,
    Citation,
)


class MockToolInput(BaseModel):
    """Mock input schema for testing."""
    query: str = Field(description="Test query")
    asset_id: str = Field(default=None, description="Optional asset ID")


class MockTool(ManufacturingTool):
    """Mock tool for testing."""
    name: str = "mock_tool"
    description: str = "A mock tool for testing"
    args_schema: Type[BaseModel] = MockToolInput
    citations_required: bool = True

    async def _arun(self, query: str, asset_id: str = None) -> ToolResult:
        """Mock implementation."""
        return self._create_success_result(
            data={"query": query, "asset_id": asset_id},
            citations=[
                self._create_citation(
                    source="test_source",
                    query=query,
                    table="test_table",
                )
            ],
        )


class MockToolNoCitations(ManufacturingTool):
    """Mock tool without citations."""
    name: str = "mock_tool_no_citations"
    description: str = "A mock tool without citations"
    args_schema: Type[BaseModel] = MockToolInput
    citations_required: bool = False

    async def _arun(self, query: str, asset_id: str = None) -> ToolResult:
        return self._create_success_result(data={"query": query})


class TestCitation:
    """Tests for Citation model."""

    def test_citation_creation(self):
        """Test Citation can be created with required fields."""
        citation = Citation(
            source="daily_summaries",
            query="SELECT * FROM daily_summaries",
        )

        assert citation.source == "daily_summaries"
        assert citation.query == "SELECT * FROM daily_summaries"
        assert citation.timestamp is not None
        assert citation.confidence == 1.0

    def test_citation_with_optional_fields(self):
        """Test Citation with all optional fields."""
        citation = Citation(
            source="daily_summaries",
            query="SELECT * FROM daily_summaries WHERE asset_id = 'grinder-5'",
            table="daily_summaries",
            record_id="123-456",
            asset_id="grinder-5",
            confidence=0.95,
        )

        assert citation.table == "daily_summaries"
        assert citation.record_id == "123-456"
        assert citation.asset_id == "grinder-5"
        assert citation.confidence == 0.95

    def test_citation_display_text_with_table_and_record(self):
        """Test display text generation with table and record."""
        citation = Citation(
            source="daily_summaries",
            query="SELECT *",
            table="daily_summaries",
            record_id="abc123",
        )

        assert citation.to_display_text() == "[Source: daily_summaries/abc123]"

    def test_citation_display_text_with_table_only(self):
        """Test display text generation with table only."""
        citation = Citation(
            source="daily_summaries",
            query="SELECT *",
            table="daily_summaries",
        )

        assert citation.to_display_text() == "[Source: daily_summaries]"

    def test_citation_display_text_source_only(self):
        """Test display text generation with source only."""
        citation = Citation(
            source="calculation",
            query="OEE calculation",
        )

        assert citation.to_display_text() == "[Source: calculation]"


class TestToolResult:
    """Tests for ToolResult model."""

    def test_tool_result_success(self):
        """Test successful ToolResult creation."""
        result = ToolResult(
            data={"oee": 87.5},
            success=True,
        )

        assert result.data == {"oee": 87.5}
        assert result.success is True
        assert result.citations == []
        assert result.error_message is None

    def test_tool_result_with_citations(self):
        """Test ToolResult with citations."""
        citation = Citation(source="test", query="test query")
        result = ToolResult(
            data={"value": 100},
            citations=[citation],
        )

        assert len(result.citations) == 1
        assert result.citations[0].source == "test"

    def test_tool_result_error(self):
        """Test error ToolResult."""
        result = ToolResult(
            data=None,
            success=False,
            error_message="Database connection failed",
        )

        assert result.success is False
        assert result.error_message == "Database connection failed"

    def test_tool_result_to_agent_response_success(self):
        """Test converting successful result to agent response."""
        citation = Citation(source="daily_summaries", query="SELECT *", table="daily_summaries")
        result = ToolResult(
            data={"oee": 87.5},
            citations=[citation],
            success=True,
        )

        response = result.to_agent_response()

        assert "87.5" in response
        assert "daily_summaries" in response

    def test_tool_result_to_agent_response_error(self):
        """Test converting error result to agent response."""
        result = ToolResult(
            data=None,
            success=False,
            error_message="Failed to fetch data",
        )

        response = result.to_agent_response()

        assert response == "Error: Failed to fetch data"


class TestManufacturingToolBase:
    """Tests for ManufacturingTool base class."""

    def test_tool_has_required_properties(self):
        """AC#2: Tool has required properties: name, description, args_schema."""
        tool = MockTool()

        assert tool.name == "mock_tool"
        assert tool.description == "A mock tool for testing"
        assert tool.args_schema == MockToolInput

    def test_tool_citations_required_default(self):
        """AC#2: Tool has citations_required flag (default: True)."""
        tool = MockTool()
        assert tool.citations_required is True

    def test_tool_citations_required_override(self):
        """Test citations_required can be set to False."""
        tool = MockToolNoCitations()
        assert tool.citations_required is False

    @pytest.mark.asyncio
    async def test_tool_arun_returns_tool_result(self):
        """AC#2: Tool implements async _arun() method returning ToolResult."""
        tool = MockTool()
        result = await tool._arun(query="test query")

        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.data["query"] == "test query"

    @pytest.mark.asyncio
    async def test_tool_arun_with_citations(self):
        """Test _arun returns citations."""
        tool = MockTool()
        result = await tool._arun(query="test query")

        assert len(result.citations) == 1
        assert result.citations[0].source == "test_source"
        assert result.citations[0].table == "test_table"

    def test_tool_run_raises_not_implemented(self):
        """Test synchronous _run raises NotImplementedError."""
        tool = MockTool()

        with pytest.raises(NotImplementedError) as exc_info:
            tool._run(query="test")

        assert "must be called asynchronously" in str(exc_info.value)

    def test_create_citation_helper(self):
        """Test _create_citation helper method."""
        tool = MockTool()
        citation = tool._create_citation(
            source="test_source",
            query="test query",
            table="test_table",
            record_id="123",
            confidence=0.9,
        )

        assert citation.source == "test_source"
        assert citation.query == "test query"
        assert citation.table == "test_table"
        assert citation.record_id == "123"
        assert citation.confidence == 0.9
        assert isinstance(citation.timestamp, datetime)

    def test_create_error_result_helper(self):
        """Test _create_error_result helper method."""
        tool = MockTool()
        result = tool._create_error_result("Something went wrong")

        assert result.success is False
        assert result.error_message == "Something went wrong"
        assert result.data is None

    def test_create_success_result_helper(self):
        """Test _create_success_result helper method."""
        tool = MockTool()
        citation = Citation(source="test", query="test")
        result = tool._create_success_result(
            data={"value": 42},
            citations=[citation],
            metadata={"key": "value"},
        )

        assert result.success is True
        assert result.data == {"value": 42}
        assert len(result.citations) == 1
        assert result.metadata == {"key": "value"}
