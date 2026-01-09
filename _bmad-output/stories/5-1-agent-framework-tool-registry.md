# Story 5.1: Agent Framework & Tool Registry

Status: ready-for-dev

## Story

As a **developer**,
I want **a LangChain agent framework with automatic tool registration**,
so that **new tools can be added without modifying the agent core**.

## Acceptance Criteria

1. **AC1: Tool Auto-Registration**
   - Given the API server is running
   - When a new tool class is created following the ManufacturingTool pattern
   - Then the tool is automatically registered with the agent
   - And the tool's description is used for intent matching

2. **AC2: Agent Tool Selection**
   - Given a user sends a message to the chat endpoint
   - When the agent processes the message
   - Then the agent selects the appropriate tool based on intent
   - And returns a structured response with citations

3. **AC3: Graceful Unknown Intent Handling**
   - Given no tool matches the user's intent
   - When the agent processes the message
   - Then the agent responds honestly that it cannot help with that request
   - And suggests what types of questions it can answer

4. **AC4: Environment Configuration**
   - Agent behavior is configurable via environment variables:
     - `LLM_PROVIDER` - LLM provider selection (openai/anthropic)
     - `LLM_MODEL` - Model name override
     - `AGENT_TEMPERATURE` - Temperature setting for agent responses

5. **AC5: Citation-Ready Responses**
   - All tool responses include structured data with source metadata
   - Responses follow the existing citation format from Story 4.5
   - Agent formats citations inline using `[Source: table/field]` pattern

## Tasks / Subtasks

- [ ] **Task 1: ManufacturingTool Base Class** (AC: #1, #5)
  - [ ] Create `apps/api/app/services/agent/base.py`
  - [ ] Define `ManufacturingTool` extending LangChain `BaseTool`
  - [ ] Implement `citations_required: bool = True` flag
  - [ ] Define `ToolResult` dataclass with data + citations + metadata
  - [ ] Implement async `_arun()` abstract method pattern
  - [ ] Add `args_schema` property for Pydantic input validation

- [ ] **Task 2: Tool Registry with Auto-Discovery** (AC: #1)
  - [ ] Create `apps/api/app/services/agent/registry.py`
  - [ ] Implement `ToolRegistry` class with singleton pattern
  - [ ] Add `discover_tools()` method scanning `services/agent/tools/` directory
  - [ ] Implement `register_tool(tool: ManufacturingTool)` method
  - [ ] Add `get_tools() -> List[ManufacturingTool]` method
  - [ ] Create `get_tool(name: str) -> ManufacturingTool | None` method
  - [ ] Log registered tools on startup

- [ ] **Task 3: AgentExecutor Wrapper** (AC: #2, #3, #4)
  - [ ] Create `apps/api/app/services/agent/executor.py`
  - [ ] Implement `ManufacturingAgent` class wrapping LangChain AgentExecutor
  - [ ] Configure OpenAI Functions agent type
  - [ ] Integrate with existing `LLMConfig` from `services/ai/llm_client.py`
  - [ ] Add `AGENT_TEMPERATURE` environment variable support
  - [ ] Implement `process_message(message: str, user_id: str) -> AgentResponse`
  - [ ] Handle no-tool-match scenario with helpful fallback message
  - [ ] Include suggested question types in fallback response

- [ ] **Task 4: Agent API Endpoint** (AC: #2, #5)
  - [ ] Create `apps/api/app/api/agent.py`
  - [ ] Implement `POST /api/agent/chat` endpoint
  - [ ] Define `AgentChatRequest` and `AgentChatResponse` Pydantic models
  - [ ] Add Supabase JWT authentication (reuse `get_current_user` dependency)
  - [ ] Integrate rate limiting (reuse existing pattern from `chat.py`)
  - [ ] Return structured response with citations array
  - [ ] Register router in `main.py`

- [ ] **Task 5: Unit Tests** (AC: #1-5)
  - [ ] Test ManufacturingTool base class instantiation
  - [ ] Test ToolRegistry discovery and registration
  - [ ] Test AgentExecutor tool selection logic
  - [ ] Test graceful handling of unknown intents
  - [ ] Test environment variable configuration
  - [ ] Test API endpoint authentication and response format

## Dev Notes

### Architecture Patterns

**LangChain Agent Pattern:**
```python
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# Use OpenAI Functions agent for reliable tool calling
agent = create_openai_functions_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
```

**Tool Registration Pattern:**
```python
class ManufacturingTool(BaseTool):
    name: str
    description: str  # Critical for intent matching
    args_schema: Type[BaseModel]
    citations_required: bool = True

    async def _arun(self, **kwargs) -> ToolResult:
        # Implementation returns structured data + citations
        pass
```

### Existing Code to Reuse

| Component | Location | Usage |
|-----------|----------|-------|
| LLM Client Factory | `services/ai/llm_client.py` | Use `get_llm_client()` for LLM instance |
| LLM Config | `services/ai/llm_client.py` | Extend `LLMConfig` for agent settings |
| Citation Models | `models/citation.py` | Use `Citation`, `SourceType` |
| Auth Dependency | `core/security.py` | Use `get_current_user` |
| Rate Limiting | `api/chat.py` | Reuse `check_rate_limit()` pattern |
| Response Service | `services/cited_response_service.py` | Reference for citation format |

### Environment Variables

```bash
# Existing (from LLMConfig)
LLM_PROVIDER=openai        # or anthropic
LLM_MODEL=gpt-4-turbo-preview
OPENAI_API_KEY=sk-...

# New for Agent
AGENT_TEMPERATURE=0.1      # Lower for more deterministic tool selection
AGENT_MAX_ITERATIONS=5     # Prevent runaway agent loops
AGENT_VERBOSE=false        # Debug logging
```

### Response Format

```python
@dataclass
class AgentResponse:
    """Response from ManufacturingAgent."""
    answer: str                    # Natural language response
    tool_used: str | None          # Tool name that was invoked
    citations: List[Citation]      # Data citations
    suggested_questions: List[str] # Follow-up suggestions
    execution_time_ms: float       # Performance tracking
    meta: Dict[str, Any]           # Additional metadata
```

### System Prompt Template

```text
You are a Manufacturing Performance Assistant helping plant managers
understand their factory operations. You have access to specialized tools
for querying production data.

IMPORTANT RULES:
1. Only use tools when you have relevant data to answer
2. If no tool matches the question, honestly say you cannot help
3. Always cite data sources in your responses
4. Suggest relevant follow-up questions

Available tools will help you answer questions about:
- Asset status and performance
- OEE (Overall Equipment Effectiveness)
- Downtime analysis
- Production status vs targets
```

### Project Structure Notes

**New files to create:**
```
apps/api/app/services/agent/
    __init__.py
    base.py          # ManufacturingTool base class
    registry.py      # Tool auto-discovery and registration
    executor.py      # AgentExecutor wrapper
apps/api/app/api/
    agent.py         # New agent chat endpoint
```

**Alignment with existing structure:**
- Services follow singleton pattern with `get_*_service()` functions
- API routes use FastAPI `APIRouter` with tags
- Models use Pydantic `BaseModel` with `ConfigDict`
- All endpoints protected with Supabase JWT auth

### Testing Standards

- Use `pytest` with `pytest-asyncio` for async tests
- Mock LLM calls with `unittest.mock.patch`
- Test file location: `apps/api/tests/services/agent/`
- Follow existing test patterns in `tests/services/ai/`

### Critical Implementation Notes

1. **Do NOT modify existing chat.py** - The agent endpoint is separate
2. **Reuse LLMConfig** - Extend, don't replace the existing configuration
3. **Tool descriptions are critical** - They determine intent matching accuracy
4. **Use async throughout** - All tool methods and agent calls must be async
5. **Graceful degradation** - If tool fails, return helpful error, don't crash

### NFR Compliance

| NFR | Implementation |
|-----|----------------|
| NFR4 (Agent Honesty) | Fallback message when no tool matches |
| NFR5 (Tool Extensibility) | Auto-discovery pattern, no core changes needed |
| NFR6 (Response Structure) | Structured ToolResult with citations |

### References

- [Source: _bmad-output/planning-artifacts/prd-addendum-ai-agent-tools.md#5.3 Tool Registration Pattern]
- [Source: _bmad-output/planning-artifacts/epic-5.md#Story 5.1]
- [Source: _bmad/bmm/data/architecture.md#Tech Stack]
- [Source: apps/api/app/services/ai/llm_client.py - LLM client factory pattern]
- [Source: apps/api/app/api/chat.py - API endpoint pattern with auth and rate limiting]
- [Source: apps/api/app/services/cited_response_service.py - Citation generation pattern]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
