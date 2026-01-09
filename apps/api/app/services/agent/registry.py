"""
Tool Registry (Story 5.1)

Auto-discovery and registration of ManufacturingTool classes.
Scans the tools directory on startup and registers all found tools.

AC#3: Tool Auto-Discovery and Registration
- All ManufacturingTool subclasses are discovered
- Each tool is registered with the agent automatically
- Tool's description is used for intent matching
"""

import importlib
import inspect
import logging
import pkgutil
from typing import Dict, List, Optional

from app.services.agent.base import ManufacturingTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Registry for ManufacturingTool instances with auto-discovery.

    AC#3: Tool Auto-Discovery and Registration
    - Scans the tools directory for ManufacturingTool subclasses
    - Maintains a registry of tool instances
    - Provides methods to access registered tools

    Usage:
        registry = get_tool_registry()
        tools = registry.get_tools()
    """

    def __init__(self):
        self._tools: Dict[str, ManufacturingTool] = {}
        self._discovered: bool = False

    def discover_tools(self) -> int:
        """
        Scan the tools directory and register all ManufacturingTool subclasses.

        AC#3: When the tool registry scans the tools directory,
        all ManufacturingTool subclasses are discovered.

        Returns:
            Number of tools discovered and registered
        """
        if self._discovered:
            logger.debug("Tools already discovered, skipping scan")
            return len(self._tools)

        discovered_count = 0

        try:
            # Import the tools package
            import app.services.agent.tools as tools_package

            # Iterate through all modules in the tools directory
            for _, module_name, is_pkg in pkgutil.iter_modules(tools_package.__path__):
                if is_pkg:
                    continue  # Skip sub-packages

                try:
                    # Import the module
                    full_module_name = f"app.services.agent.tools.{module_name}"
                    module = importlib.import_module(full_module_name)

                    # Find all ManufacturingTool subclasses in the module
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)

                        # Check if it's a class that's a subclass of ManufacturingTool
                        if (
                            inspect.isclass(attr)
                            and issubclass(attr, ManufacturingTool)
                            and attr is not ManufacturingTool
                        ):
                            try:
                                # Instantiate and register the tool
                                tool_instance = attr()
                                self.register_tool(tool_instance)
                                discovered_count += 1
                                logger.info(
                                    f"Registered tool: {tool_instance.name} "
                                    f"from {module_name}"
                                )
                            except Exception as e:
                                logger.error(
                                    f"Failed to instantiate tool {attr_name} "
                                    f"from {module_name}: {e}"
                                )

                except Exception as e:
                    logger.error(f"Failed to import tool module {module_name}: {e}")

        except ImportError as e:
            logger.warning(f"Tools package not found or empty: {e}")

        self._discovered = True
        logger.info(f"Tool discovery complete: {discovered_count} tools registered")

        return discovered_count

    def register_tool(self, tool: ManufacturingTool) -> None:
        """
        Register a tool with the registry.

        AC#3: Each tool is registered with the agent automatically.

        Args:
            tool: ManufacturingTool instance to register

        Raises:
            ValueError: If tool name is already registered
        """
        if not isinstance(tool, ManufacturingTool):
            raise TypeError(
                f"Tool must be a ManufacturingTool instance, got {type(tool)}"
            )

        if tool.name in self._tools:
            logger.warning(
                f"Tool '{tool.name}' is already registered, skipping duplicate"
            )
            return

        self._tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")

    def get_tool(self, name: str) -> Optional[ManufacturingTool]:
        """
        Get a specific tool by name.

        Args:
            name: Tool name to retrieve

        Returns:
            ManufacturingTool instance or None if not found
        """
        self._ensure_discovered()
        return self._tools.get(name)

    def get_tools(self) -> List[ManufacturingTool]:
        """
        Get all registered tools.

        AC#3: Returns list of tools for agent initialization.

        Returns:
            List of all registered ManufacturingTool instances
        """
        self._ensure_discovered()
        return list(self._tools.values())

    def get_tool_names(self) -> List[str]:
        """
        Get names of all registered tools.

        Returns:
            List of tool names
        """
        self._ensure_discovered()
        return list(self._tools.keys())

    def get_tool_descriptions(self) -> Dict[str, str]:
        """
        Get descriptions of all registered tools.

        AC#3: Tool's description is used for intent matching.

        Returns:
            Dict mapping tool names to descriptions
        """
        self._ensure_discovered()
        return {
            name: tool.description
            for name, tool in self._tools.items()
        }

    def clear(self) -> None:
        """
        Clear all registered tools.

        Primarily used for testing.
        """
        self._tools.clear()
        self._discovered = False
        logger.debug("Tool registry cleared")

    def _ensure_discovered(self) -> None:
        """Ensure tools have been discovered."""
        if not self._discovered:
            self.discover_tools()

    @property
    def tool_count(self) -> int:
        """Get the number of registered tools."""
        return len(self._tools)

    @property
    def is_discovered(self) -> bool:
        """Check if tool discovery has been performed."""
        return self._discovered


# Module-level singleton
_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """
    Get the singleton ToolRegistry instance.

    Returns:
        ToolRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry


def discover_tools() -> int:
    """
    Trigger tool discovery.

    Convenience function for discover_tools on the singleton.

    Returns:
        Number of tools discovered
    """
    return get_tool_registry().discover_tools()


def register_tool(tool: ManufacturingTool) -> None:
    """
    Register a tool with the global registry.

    Convenience function for registering tools.

    Args:
        tool: ManufacturingTool instance to register
    """
    get_tool_registry().register_tool(tool)


def get_all_tools() -> List[ManufacturingTool]:
    """
    Get all registered tools.

    Convenience function for getting all tools from singleton.

    Returns:
        List of registered ManufacturingTool instances
    """
    return get_tool_registry().get_tools()


def reset_registry() -> None:
    """
    Reset the singleton registry instance.

    Primarily used for testing.
    """
    global _registry
    _registry = None
