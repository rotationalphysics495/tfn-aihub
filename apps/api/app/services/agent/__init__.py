"""
Agent Service Module (Story 5.1)

Provides LangChain-based agent framework with automatic tool registration
for manufacturing performance queries.

Components:
- ManufacturingTool: Base class for all agent tools
- ToolRegistry: Auto-discovery and registration of tools
- ManufacturingAgent: AgentExecutor wrapper for message processing

AC#1: Agent Framework Initialization
AC#2: ManufacturingTool Base Class
AC#3: Tool Auto-Discovery and Registration
"""

from app.services.agent.base import (
    ManufacturingTool,
    ToolResult,
    Citation,
)
from app.services.agent.registry import (
    ToolRegistry,
    get_tool_registry,
    discover_tools,
    register_tool,
    get_all_tools,
    reset_registry,
)
from app.services.agent.executor import (
    ManufacturingAgent,
    get_manufacturing_agent,
    AgentError,
)

__all__ = [
    # Base class
    "ManufacturingTool",
    "ToolResult",
    "Citation",
    # Registry
    "ToolRegistry",
    "get_tool_registry",
    "discover_tools",
    "register_tool",
    "get_all_tools",
    "reset_registry",
    # Executor
    "ManufacturingAgent",
    "get_manufacturing_agent",
    "AgentError",
]
