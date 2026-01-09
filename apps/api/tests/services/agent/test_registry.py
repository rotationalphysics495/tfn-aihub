"""
Tests for Tool Registry (Story 5.1)

AC#3: Tool Auto-Discovery and Registration
- All ManufacturingTool subclasses are discovered
- Each tool is registered with the agent automatically
- Tool's description is used for intent matching
"""

import pytest
from typing import Type
from unittest.mock import patch, MagicMock
from pydantic import BaseModel, Field

from app.services.agent.base import ManufacturingTool, ToolResult
from app.services.agent.registry import (
    ToolRegistry,
    get_tool_registry,
    discover_tools,
    register_tool,
    get_all_tools,
)


class MockRegistryInput(BaseModel):
    """Mock input schema for registry testing."""
    query: str = Field(description="Test query")


class MockRegistryTool1(ManufacturingTool):
    """First mock tool for registry testing."""
    name: str = "test_tool_1"
    description: str = "First test tool for registry testing"
    args_schema: Type[BaseModel] = MockRegistryInput

    async def _arun(self, query: str) -> ToolResult:
        return ToolResult(data={"result": "tool1"})


class MockRegistryTool2(ManufacturingTool):
    """Second mock tool for registry testing."""
    name: str = "test_tool_2"
    description: str = "Second test tool for registry testing"
    args_schema: Type[BaseModel] = MockRegistryInput

    async def _arun(self, query: str) -> ToolResult:
        return ToolResult(data={"result": "tool2"})


class TestToolRegistry:
    """Tests for ToolRegistry class."""

    def setup_method(self):
        """Reset registry before each test."""
        # Get the singleton and clear it
        registry = get_tool_registry()
        registry.clear()

    def test_registry_creation(self):
        """Test ToolRegistry can be created."""
        registry = ToolRegistry()

        assert registry.tool_count == 0
        assert not registry.is_discovered

    def test_register_tool(self):
        """AC#3: Each tool is registered with the agent automatically."""
        registry = ToolRegistry()
        tool = MockRegistryTool1()

        registry.register_tool(tool)

        assert registry.tool_count == 1
        assert registry.get_tool("test_tool_1") is tool

    def test_register_multiple_tools(self):
        """Test registering multiple tools."""
        registry = ToolRegistry()
        tool1 = MockRegistryTool1()
        tool2 = MockRegistryTool2()

        registry.register_tool(tool1)
        registry.register_tool(tool2)

        assert registry.tool_count == 2
        assert registry.get_tool("test_tool_1") is tool1
        assert registry.get_tool("test_tool_2") is tool2

    def test_register_duplicate_tool_skipped(self):
        """Test duplicate tool registration is skipped."""
        registry = ToolRegistry()
        tool1 = MockRegistryTool1()
        tool1_dup = MockRegistryTool1()

        registry.register_tool(tool1)
        registry.register_tool(tool1_dup)

        assert registry.tool_count == 1

    def test_register_non_tool_raises_error(self):
        """Test registering non-ManufacturingTool raises TypeError."""
        registry = ToolRegistry()

        with pytest.raises(TypeError):
            registry.register_tool("not a tool")

    def test_get_tool_not_found(self):
        """Test get_tool returns None for unknown tool."""
        registry = ToolRegistry()

        result = registry.get_tool("nonexistent")

        assert result is None

    def test_get_tools(self):
        """AC#3: Returns list of tools for agent initialization."""
        registry = ToolRegistry()
        tool1 = MockRegistryTool1()
        tool2 = MockRegistryTool2()

        registry.register_tool(tool1)
        registry.register_tool(tool2)

        tools = registry.get_tools()

        assert len(tools) == 2
        assert tool1 in tools
        assert tool2 in tools

    def test_get_tool_names(self):
        """Test get_tool_names returns list of names."""
        registry = ToolRegistry()
        registry.register_tool(MockRegistryTool1())
        registry.register_tool(MockRegistryTool2())

        names = registry.get_tool_names()

        assert "test_tool_1" in names
        assert "test_tool_2" in names

    def test_get_tool_descriptions(self):
        """AC#3: Tool's description is used for intent matching."""
        registry = ToolRegistry()
        registry.register_tool(MockRegistryTool1())
        registry.register_tool(MockRegistryTool2())

        descriptions = registry.get_tool_descriptions()

        assert descriptions["test_tool_1"] == "First test tool for registry testing"
        assert descriptions["test_tool_2"] == "Second test tool for registry testing"

    def test_clear_registry(self):
        """Test clear resets the registry."""
        registry = ToolRegistry()
        registry.register_tool(MockRegistryTool1())

        registry.clear()

        assert registry.tool_count == 0
        assert not registry.is_discovered


class TestToolDiscovery:
    """Tests for tool auto-discovery."""

    def setup_method(self):
        """Reset registry before each test."""
        registry = get_tool_registry()
        registry.clear()

    def test_discover_tools_empty_directory(self):
        """Test discovery with no tools in directory."""
        registry = ToolRegistry()

        # Mock the tools package to be empty
        with patch("app.services.agent.registry.pkgutil.iter_modules") as mock_iter:
            mock_iter.return_value = []

            count = registry.discover_tools()

            assert count == 0
            assert registry.is_discovered

    def test_discover_tools_only_runs_once(self):
        """Test discovery only runs once."""
        registry = ToolRegistry()
        registry._discovered = True
        registry._tools = {"test": MagicMock()}

        count = registry.discover_tools()

        assert count == 1  # Returns existing count

    def test_discover_tools_imports_modules(self):
        """AC#3: When the tool registry scans the tools directory."""
        # This test verifies the discovery mechanism works
        # The actual tools are in the tools/ directory
        registry = get_tool_registry()

        # Force re-discovery
        registry.clear()

        count = registry.discover_tools()

        # Should complete without error
        # Count depends on tools in directory
        assert registry.is_discovered


class TestModuleLevelFunctions:
    """Tests for module-level convenience functions."""

    def setup_method(self):
        """Reset registry before each test."""
        registry = get_tool_registry()
        registry.clear()

    def test_get_tool_registry_singleton(self):
        """Test get_tool_registry returns singleton."""
        registry1 = get_tool_registry()
        registry2 = get_tool_registry()

        assert registry1 is registry2

    def test_discover_tools_function(self):
        """Test discover_tools convenience function."""
        # Should complete without error
        count = discover_tools()
        assert isinstance(count, int)

    def test_register_tool_function(self):
        """Test register_tool convenience function."""
        tool = MockRegistryTool1()

        register_tool(tool)

        registry = get_tool_registry()
        assert registry.get_tool("test_tool_1") is tool

    def test_get_all_tools_function(self):
        """Test get_all_tools convenience function."""
        register_tool(MockRegistryTool1())
        register_tool(MockRegistryTool2())

        tools = get_all_tools()

        assert len(tools) == 2
