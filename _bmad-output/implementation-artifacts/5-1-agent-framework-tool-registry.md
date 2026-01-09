# Story 5.1: Agent Framework & Tool Registry

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer**,
I want **a LangChain agent framework with automatic tool registration**,
so that **new tools can be added without modifying the agent core**.

## Acceptance Criteria

1. **Agent Framework Initialization**
   - GIVEN the API server is running
   - WHEN the agent service is initialized
   - THEN it creates a LangChain AgentExecutor with OpenAI Functions agent
   - AND the agent is configured via environment variables (LLM_PROVIDER, LLM_MODEL, AGENT_TEMPERATURE)
   - AND the agent has access to all registered tools

2. **ManufacturingTool Base Class**
   - GIVEN a developer creates a new tool class
   - WHEN the class extends ManufacturingTool
   - THEN the tool has required properties: name, description, args_schema
   - AND the tool has a citations_required flag (default: True)
   - AND the tool implements async _arun() method returning ToolResult

3. **Tool Auto-Discovery and Registration**
   - GIVEN the API server is starting
   - WHEN the tool registry scans the tools directory
   - THEN all ManufacturingTool subclasses are discovered
   - AND each tool is registered with the agent automatically
   - AND the tool's description is used for intent matching

4. **Intent-Based Tool Selection**
   - GIVEN a user sends a message to the chat endpoint
   - WHEN the agent processes the message
   - THEN the agent selects the appropriate tool based on the message intent
   - AND the tool is invoked with parsed parameters
   - AND the response includes tool output with citations

5. **Structured Response with Citations**
   - GIVEN a tool returns data
   - WHEN the agent formats the response
   - THEN the response includes a citations array with source, query, and timestamp
   - AND the response follows the ToolResult schema
   - AND the response is suitable for display in the chat UI

6. **Graceful Handling of Unknown Intents**
   - GIVEN no tool matches the user's intent
   - WHEN the agent processes the message
   - THEN the agent responds honestly that it cannot help with that request
   - AND the response suggests what types of questions it can answer
   - AND the response does NOT fabricate data or make up capabilities

7. **Agent Chat Endpoint**
   - GIVEN the FastAPI backend is running
   - WHEN a POST request is made to /api/agent/chat
   - THEN the request is authenticated via Supabase JWT
   - AND the message is processed by the agent
   - AND the response follows the AgentResponse schema

8. **Error Handling and Logging**
   - GIVEN an error occurs during tool execution
   - WHEN the agent handles the error
   - THEN the error is logged with full context
   - AND the user receives a helpful error message
   - AND the agent does not crash or hang

## Tasks / Subtasks

- [ ] Task 1: Create ManufacturingTool Base Class (AC: #2)
  - [ ] 1.1 Create `apps/api/app/services/agent/__init__.py` module
  - [ ] 1.2 Create `apps/api/app/services/agent/base.py` with ManufacturingTool class
  - [ ] 1.3 Define ToolResult Pydantic model with data, citations, metadata fields
  - [ ] 1.4 Define Citation Pydantic model with source, query, timestamp, table fields
  - [ ] 1.5 Implement abstract _arun() method signature
  - [ ] 1.6 Add citations_required flag with default True
  - [ ] 1.7 Create unit tests for base class

- [ ] Task 2: Create Tool Registry (AC: #3)
  - [ ] 2.1 Create `apps/api/app/services/agent/registry.py`
  - [ ] 2.2 Implement discover_tools() function to scan tools directory
  - [ ] 2.3 Implement register_tool() function to add tools to registry
  - [ ] 2.4 Implement get_all_tools() function returning list of tools
  - [ ] 2.5 Add logging for tool discovery process
  - [ ] 2.6 Create unit tests for registry

- [ ] Task 3: Create AgentExecutor Wrapper (AC: #1, #4, #5)
  - [ ] 3.1 Create `apps/api/app/services/agent/executor.py`
  - [ ] 3.2 Implement ManufacturingAgent class wrapping LangChain AgentExecutor
  - [ ] 3.3 Configure with OpenAI Functions agent type
  - [ ] 3.4 Load tools from registry on initialization
  - [ ] 3.5 Implement process_message() async method
  - [ ] 3.6 Format tool outputs with citations
  - [ ] 3.7 Create unit tests for executor

- [ ] Task 4: Implement Unknown Intent Handling (AC: #6)
  - [ ] 4.1 Create fallback response when no tool matches
  - [ ] 4.2 Generate list of available tool capabilities
  - [ ] 4.3 Format helpful suggestions for user
  - [ ] 4.4 Ensure no fabrication of data or capabilities
  - [ ] 4.5 Create unit tests for fallback behavior

- [ ] Task 5: Create Agent API Endpoint (AC: #7)
  - [ ] 5.1 Create `apps/api/app/api/agent.py` router
  - [ ] 5.2 Define AgentChatRequest Pydantic model
  - [ ] 5.3 Define AgentResponse Pydantic model
  - [ ] 5.4 Implement POST /api/agent/chat endpoint
  - [ ] 5.5 Add Supabase JWT authentication dependency
  - [ ] 5.6 Register router in main.py
  - [ ] 5.7 Create integration tests for endpoint

- [ ] Task 6: Add Configuration Settings (AC: #1)
  - [ ] 6.1 Add LLM_PROVIDER to config.py (default: "openai")
  - [ ] 6.2 Add LLM_MODEL to config.py (default: "gpt-4-turbo-preview")
  - [ ] 6.3 Add AGENT_TEMPERATURE to config.py (default: 0.1)
  - [ ] 6.4 Update .env.example with new variables
  - [ ] 6.5 Create agent_configured property for validation

- [ ] Task 7: Implement Error Handling (AC: #8)
  - [ ] 7.1 Create custom AgentError exception class
  - [ ] 7.2 Add try/catch blocks in executor
  - [ ] 7.3 Implement logging with full context
  - [ ] 7.4 Create user-friendly error messages
  - [ ] 7.5 Create tests for error scenarios

- [ ] Task 8: Create Pydantic Models (AC: #5, #7)
  - [ ] 8.1 Create `apps/api/app/models/agent.py`
  - [ ] 8.2 Define Citation model
  - [ ] 8.3 Define ToolResult model
  - [ ] 8.4 Define AgentChatRequest model
  - [ ] 8.5 Define AgentResponse model
  - [ ] 8.6 Define FollowUpQuestion model

## Dev Notes

### Architecture Compliance

This story implements the **Agent Foundation** from the PRD Addendum (Section 5: Technical Design). It creates the LangChain agent framework that all subsequent tools (Stories 5.3-5.6) will use.

**Location:** `apps/api/` (Python FastAPI Backend)
**Module:** `app/services/agent/` for agent service logic
**Pattern:** Service-layer with dependency injection, async operations

### Technical Requirements

**Agent Architecture Diagram:**
```
User Message
    |
    v
+-------------------+
| /api/agent/chat   |
| (agent.py router) |
+-------------------+
    |
    v
+-------------------+
| ManufacturingAgent|
| (executor.py)     |
+-------------------+
    |
    +---> process_message(message, user_id)
    |         |
    |         v
    |     LangChain AgentExecutor
    |     (OpenAI Functions Agent)
    |         |
    |         v
    |     Tool Selection (based on intent)
    |         |
    |         v
    +---> Tool Registry
              |
              v
          [ManufacturingTool subclasses]
              |
              v
          ToolResult with Citations
```

### LangChain Agent Configuration

**executor.py Core Structure:**
```python
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.services.agent.registry import get_all_tools
from app.core.config import settings

class ManufacturingAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=settings.AGENT_TEMPERATURE,
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.tools = get_all_tools()
        self.agent = self._create_agent()
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True
        )

    def _create_agent(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        return create_openai_functions_agent(self.llm, self.tools, prompt)

    def _get_system_prompt(self):
        return """You are a manufacturing performance assistant. You help plant managers
        understand their production data by using specialized tools.

        IMPORTANT RULES:
        1. ONLY use the tools available to you - do not make up data
        2. If you cannot answer a question with available tools, say so honestly
        3. Always cite the source of your data with timestamps
        4. Be concise but comprehensive in your responses

        Available tools: {tool_descriptions}
        """

    async def process_message(
        self,
        message: str,
        user_id: str,
        chat_history: list = None
    ) -> AgentResponse:
        try:
            result = await self.executor.ainvoke({
                "input": message,
                "chat_history": chat_history or []
            })
            return self._format_response(result)
        except Exception as e:
            logger.error(f"Agent error: {e}")
            return self._create_error_response(str(e))
```

### ManufacturingTool Base Class

**base.py Core Structure:**
```python
from abc import abstractmethod
from typing import Type, Any, Optional, List
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from datetime import datetime

class Citation(BaseModel):
    source: str  # e.g., "daily_summaries"
    query: str   # e.g., "SELECT * FROM daily_summaries WHERE..."
    timestamp: datetime
    table: Optional[str] = None

class ToolResult(BaseModel):
    data: Any
    citations: List[Citation] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    cached_at: Optional[datetime] = None

class ManufacturingTool(BaseTool):
    name: str
    description: str
    args_schema: Type[BaseModel]
    citations_required: bool = True

    @abstractmethod
    async def _arun(self, **kwargs) -> ToolResult:
        """Execute the tool and return structured results with citations."""
        pass

    def _run(self, **kwargs) -> ToolResult:
        """Synchronous wrapper - raises error to enforce async usage."""
        raise NotImplementedError("Use async _arun() instead")
```

### Tool Registry Implementation

**registry.py Core Structure:**
```python
import importlib
import pkgutil
from typing import List
from app.services.agent.base import ManufacturingTool
import logging

logger = logging.getLogger(__name__)

_tool_registry: List[ManufacturingTool] = []

def discover_tools() -> None:
    """Scan tools directory and register all ManufacturingTool subclasses."""
    import app.services.agent.tools as tools_package

    for _, module_name, _ in pkgutil.iter_modules(tools_package.__path__):
        try:
            module = importlib.import_module(f"app.services.agent.tools.{module_name}")

            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and
                    issubclass(attr, ManufacturingTool) and
                    attr is not ManufacturingTool):
                    register_tool(attr())
                    logger.info(f"Registered tool: {attr_name}")
        except Exception as e:
            logger.error(f"Failed to load tool module {module_name}: {e}")

def register_tool(tool: ManufacturingTool) -> None:
    """Add a tool to the registry."""
    _tool_registry.append(tool)

def get_all_tools() -> List[ManufacturingTool]:
    """Return all registered tools."""
    if not _tool_registry:
        discover_tools()
    return _tool_registry
```

### Environment Variables

**Add to `apps/api/.env` and Railway Secrets:**

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `LLM_PROVIDER` | LLM provider (openai, azure) | No | `openai` |
| `LLM_MODEL` | Model identifier | No | `gpt-4-turbo-preview` |
| `AGENT_TEMPERATURE` | LLM temperature (0-1) | No | `0.1` |
| `OPENAI_API_KEY` | OpenAI API key | Yes | - |

### Project Structure Notes

**Files to create:**
```
apps/api/
├── app/
│   ├── services/
│   │   └── agent/
│   │       ├── __init__.py           # Exports agent components
│   │       ├── base.py               # ManufacturingTool, ToolResult, Citation
│   │       ├── registry.py           # Tool auto-discovery
│   │       ├── executor.py           # ManufacturingAgent class
│   │       └── tools/                # Tool implementations (Stories 5.3-5.6)
│   │           └── __init__.py
│   ├── api/
│   │   └── agent.py                  # Agent chat endpoint
│   └── models/
│       └── agent.py                  # Pydantic models for agent API
```

**Dependencies to add to requirements.txt:**
```
langchain>=0.1.0
langchain-openai>=0.0.5
```

### Dependencies

**Story Dependencies:**
- Story 4.1 (Mem0 Vector Memory Integration) - Memory service for context
- Story 4.2 (LangChain Text-to-SQL) - Existing LangChain patterns to follow

**Blocked By:** Epic 4 must be complete

**Enables:**
- Story 5.2 (Data Access Abstraction Layer) - Tools will use this layer
- Stories 5.3-5.6 (Core Tools) - All tools extend ManufacturingTool
- Story 5.7 (Agent Chat Integration) - Frontend connects to agent endpoint
- Story 5.8 (Tool Response Caching) - Cache decorator for tools

### Testing Strategy

1. **Unit Tests:**
   - ManufacturingTool base class instantiation
   - Tool registry discovery and registration
   - AgentExecutor configuration
   - Response formatting with citations
   - Unknown intent handling

2. **Integration Tests:**
   - Full message processing flow
   - Tool selection based on intent
   - JWT authentication on endpoint
   - Error handling and recovery

3. **Manual Testing:**
   - Send various messages via API
   - Verify tool selection is correct
   - Check citation format in responses
   - Test edge cases (no matching tool, errors)

### Error Handling Patterns

```python
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

class AgentError(Exception):
    """Custom exception for agent-related errors."""
    pass

class ManufacturingAgent:
    async def process_message(self, message: str, user_id: str) -> AgentResponse:
        try:
            result = await self.executor.ainvoke({"input": message})
            return self._format_response(result)
        except AgentError as e:
            logger.error(f"Agent error for user {user_id}: {e}")
            return AgentResponse(
                content="I encountered an issue processing your request. Please try again.",
                citations=[],
                error=str(e)
            )
        except Exception as e:
            logger.exception(f"Unexpected error in agent: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred. Please try again later."
            )
```

### NFR Compliance

- **NFR1 (Accuracy):** All responses include citations with source and timestamp
- **NFR4 (Agent Honesty):** Agent clearly states when it cannot help; never fabricates data
- **NFR5 (Tool Extensibility):** New tools auto-register without modifying agent core
- **NFR6 (Response Structure):** All responses follow ToolResult schema with citations

### References

- [Source: _bmad-output/planning-artifacts/prd-addendum-ai-agent-tools.md#5.1 Architecture Overview] - Agent architecture diagram
- [Source: _bmad-output/planning-artifacts/prd-addendum-ai-agent-tools.md#5.3 Tool Registration Pattern] - ManufacturingTool pattern
- [Source: _bmad-output/planning-artifacts/epic-5.md#Story 5.1] - Story requirements
- [Source: _bmad/bmm/data/architecture.md#7. AI & Memory Architecture] - LangChain integration
- [LangChain Agents Documentation](https://python.langchain.com/docs/modules/agents/) - Agent patterns
- [OpenAI Functions Agent](https://python.langchain.com/docs/modules/agents/agent_types/openai_functions_agent) - Agent type reference

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

