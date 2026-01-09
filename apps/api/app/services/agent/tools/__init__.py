"""
Agent Tools Module (Story 5.1)

This package contains all ManufacturingTool implementations.
Tools are automatically discovered and registered with the agent
on startup via the ToolRegistry.

To create a new tool:
1. Create a new file in this directory (e.g., my_tool.py)
2. Define a class extending ManufacturingTool
3. Implement the async _arun() method
4. The tool will be auto-discovered on next startup

Example:
    from app.services.agent.base import ManufacturingTool, ToolResult
    from pydantic import BaseModel, Field

    class MyToolInput(BaseModel):
        query: str = Field(description="User query")

    class MyTool(ManufacturingTool):
        name = "my_tool"
        description = "Description used for intent matching"
        args_schema = MyToolInput
        citations_required = True

        async def _arun(self, query: str) -> ToolResult:
            # Implementation
            return ToolResult(data={"result": "..."}, citations=[])
"""
