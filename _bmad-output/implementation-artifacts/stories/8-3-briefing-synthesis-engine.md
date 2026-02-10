# Story 8.3: Briefing Synthesis Engine

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **system component**,
I want **to compose existing LangChain tools into coherent narrative briefings**,
So that **users receive synthesized insights rather than raw data**.

## Acceptance Criteria

1. **AC1: Tool Orchestration Sequence**
   - **Given** a briefing is requested
   - **When** the BriefingService is invoked
   - **Then** it orchestrates the following tools in sequence:
     - Production Status (current output vs target)
     - Safety Events (any incidents)
     - OEE Query (plant-wide or scoped)
     - Downtime Analysis (top reasons)
     - Action List (prioritized issues)
   - **And** results are aggregated into a unified data structure

2. **AC2: Narrative Generation**
   - **Given** tool results are aggregated
   - **When** narrative generation is triggered
   - **Then** the LLM formats data into natural language sections:
     - Headline summary
     - Top wins (areas >100% target)
     - Top concerns (gaps, issues)
     - Recommended actions
   - **And** all metrics include citations

3. **AC3: 30-Second Timeout Compliance (NFR8)**
   - **Given** briefing generation starts
   - **When** 30 seconds have elapsed
   - **Then** the system returns whatever is complete
   - **And** indicates any sections that timed out

4. **AC4: Graceful Tool Failure Handling**
   - **Given** a tool fails during orchestration
   - **When** the failure is detected
   - **Then** the briefing continues with available data
   - **And** the failed section is noted: "Unable to retrieve [section] data"

## Tasks / Subtasks

- [ ] **Task 1: BriefingService Package Structure** (AC: #1, #4)
  - [ ] 1.1 Create `apps/api/app/services/briefing/__init__.py` - Package init with exports
  - [ ] 1.2 Define service module structure following existing patterns

- [ ] **Task 2: Briefing Data Models** (AC: #1, #2)
  - [ ] 2.1 Create `apps/api/app/models/briefing.py` - Pydantic models
  - [ ] 2.2 Define `BriefingSection` model (title, content, metrics, citations, status)
  - [ ] 2.3 Define `BriefingResponse` model (sections, audio_stream_url?, total_duration_estimate)
  - [ ] 2.4 Define `BriefingMetric` model (name, value, formatted_value, trend?)
  - [ ] 2.5 Define `BriefingSectionStatus` enum (complete, partial, failed, timed_out)

- [ ] **Task 3: BriefingService Core Implementation** (AC: #1, #3, #4)
  - [ ] 3.1 Create `apps/api/app/services/briefing/service.py` - BriefingService class
  - [ ] 3.2 Implement async `generate_briefing()` method as main entry point
  - [ ] 3.3 Implement `_orchestrate_tools()` to call tools in sequence with timeout
  - [ ] 3.4 Implement per-tool timeout handling (5-7 seconds per tool)
  - [ ] 3.5 Implement overall 30-second timeout with asyncio.wait_for
  - [ ] 3.6 Aggregate tool results into unified `BriefingData` structure
  - [ ] 3.7 Handle individual tool failures without blocking other tools
  - [ ] 3.8 Collect and merge all citations from tool results
  - [ ] 3.9 Write unit tests with mocked tool dependencies

- [ ] **Task 4: Tool Integration Layer** (AC: #1)
  - [ ] 4.1 Import and instantiate existing tools: ProductionStatusTool, SafetyEventsTool, OEEQueryTool, DowntimeAnalysisTool, ActionListTool
  - [ ] 4.2 Create wrapper methods for each tool with error handling
  - [ ] 4.3 Map tool outputs to briefing section data structures
  - [ ] 4.4 Parse and normalize tool ToolResult responses

- [ ] **Task 5: Narrative Generation** (AC: #2)
  - [ ] 5.1 Create `apps/api/app/services/briefing/narrative.py` - LLM narrative formatting
  - [ ] 5.2 Implement `generate_narrative_sections()` method
  - [ ] 5.3 Build LLM prompt for narrative synthesis with structured output
  - [ ] 5.4 Generate headline summary from aggregated data
  - [ ] 5.5 Generate "Top Wins" section (areas/assets >100% target)
  - [ ] 5.6 Generate "Top Concerns" section (safety, OEE gaps, downtime)
  - [ ] 5.7 Generate "Recommended Actions" section from action list data
  - [ ] 5.8 Ensure all numeric values include inline citations
  - [ ] 5.9 Use existing LLM client from `app.services.ai.llm_client`
  - [ ] 5.10 Write unit tests for narrative generation

- [ ] **Task 6: Timeout and Partial Response Handling** (AC: #3)
  - [ ] 6.1 Implement asyncio.timeout context manager for 30-second budget
  - [ ] 6.2 Track completion status per section
  - [ ] 6.3 Return partial response when timeout occurs
  - [ ] 6.4 Mark timed-out sections with status="timed_out"
  - [ ] 6.5 Include completion percentage in response metadata

- [ ] **Task 7: Data Source Integration** (AC: #1)
  - [ ] 7.1 Leverage existing `daily_summaries` cache via data source layer
  - [ ] 7.2 Ensure tools are configured to use cached T-1 data
  - [ ] 7.3 No direct MSSQL queries - all data via existing tool layer

- [ ] **Task 8: Integration Testing** (AC: #1-4)
  - [ ] 8.1 Integration test: full orchestration with real tool instances
  - [ ] 8.2 Integration test: timeout scenario with slow mock tools
  - [ ] 8.3 Integration test: partial failure scenario
  - [ ] 8.4 Integration test: all tools fail gracefully

## Dev Notes

### Critical Architecture Understanding

**BriefingService is NOT a ManufacturingTool**

From architecture docs: "BriefingService is a dedicated orchestration layer (not LangChain chains)". This is fundamentally different from the existing agent tools:

```python
# CORRECT: BriefingService pattern
class BriefingService:
    """Orchestrates briefing generation by composing existing tools."""

    async def generate_briefing(self, user_id: str, scope: BriefingScope) -> BriefingResponse:
        # Orchestrate tools, NOT a tool itself
        pass

# WRONG: Do NOT extend ManufacturingTool
class BriefingSynthesisTool(ManufacturingTool):  # NO!
```

### Existing Tools to Orchestrate

The BriefingService must call these existing tools in sequence:

| Tool | Import Path | Purpose |
|------|-------------|---------|
| ProductionStatusTool | `app.services.agent.tools.production_status` | Current output vs target |
| SafetyEventsTool | `app.services.agent.tools.safety_events` | Safety incidents |
| OEEQueryTool | `app.services.agent.tools.oee_query` | OEE breakdown |
| DowntimeAnalysisTool | `app.services.agent.tools.downtime_analysis` | Downtime reasons |
| ActionListTool | `app.services.agent.tools.action_list` | Prioritized actions |

### Tool Calling Pattern

All existing tools return `ToolResult` objects with this structure:

```python
class ToolResult(BaseModel):
    data: Any  # The actual tool output data
    citations: List[Citation]  # Source citations
    metadata: Dict[str, Any]  # Cache info, timestamps, etc.
    success: bool
    error_message: Optional[str]
```

Call tools using their async `_arun()` method:

```python
from app.services.agent.tools.production_status import ProductionStatusTool

tool = ProductionStatusTool()
result: ToolResult = await tool._arun(area=None)  # Plant-wide

if result.success:
    production_data = result.data
    citations.extend(result.citations)
else:
    # Handle failure gracefully
    section_status = BriefingSectionStatus.FAILED
```

### BriefingResponse Structure

From architecture/voice-briefing.md:

```python
class BriefingResponse(BaseModel):
    sections: List[BriefingSection]  # Text + citations (always present)
    audio_stream_url: Optional[str]  # Nullable = graceful degradation
    total_duration_estimate: int     # For progress UI (seconds)
```

**Note:** The `audio_stream_url` is NOT generated by this story - Story 8.1 (TTS Integration) handles that. This story focuses only on the synthesis engine producing sections.

### Section Structure

Each section should follow this pattern:

```python
class BriefingSection(BaseModel):
    section_type: str  # "headline", "wins", "concerns", "actions"
    title: str
    content: str  # Natural language narrative
    metrics: List[BriefingMetric]
    citations: List[Citation]
    status: BriefingSectionStatus
    pause_point: bool = True  # Natural pause for Q&A
```

### Timeout Strategy

NFR8 requires briefing generation within 30 seconds. Budget allocation:

| Phase | Budget |
|-------|--------|
| Tool Orchestration (5 tools) | 20 seconds max |
| Per-tool timeout | 5 seconds each (parallel where possible) |
| Narrative Generation | 8 seconds |
| Response Assembly | 2 seconds |
| **Total** | **30 seconds** |

Implementation pattern:

```python
import asyncio

async def generate_briefing(self, ...) -> BriefingResponse:
    try:
        async with asyncio.timeout(30):
            # Orchestrate tools
            tool_results = await self._orchestrate_tools()

            # Generate narrative
            sections = await self._generate_narrative(tool_results)

            return BriefingResponse(sections=sections, ...)
    except asyncio.TimeoutError:
        # Return whatever we have so far
        return self._build_partial_response(completed_sections)
```

### Data Source: daily_summaries Cache

From architecture: "Leverage existing `daily_summaries` cache (T-1 data, 06:00 AM refresh)".

The existing tools (ProductionStatusTool, OEEQueryTool, etc.) already query `daily_summaries` and `live_snapshots` tables. Do NOT bypass these tools to query directly.

### Narrative Formatting Guidelines

The narrative should be conversational, not just data dumps:

**BAD:** "Production Status: 145,230 units produced, 150,000 target, -3.2% variance"

**GOOD:** "Overall, we're tracking slightly behind target with about 145,000 units produced against a 150,000 unit goal - that's a 3% gap we'll want to watch. [Source: daily_summaries]"

### 7 Production Areas (for context)

When generating plant-wide briefings, data covers these areas:
- Packing (CAMA, Pack Cells, Variety Pack, Bag Lines, Nuspark)
- Rychigers (101-109, 1009)
- Grinding (Grinders 1-5)
- Powder (1002-1004 Fill & Pack, Manual Bulk)
- Roasting (Roasters 1-4)
- Green Bean (Manual, Silo Transfer)
- Flavor Room (Coffee Flavor Room)

### LLM Integration

Use the existing LLM client infrastructure:

```python
from app.services.ai.llm_client import get_llm_client

llm = get_llm_client()
# Use structured output prompting
narrative = await llm.agenerate(prompt=synthesis_prompt)
```

### Project Structure Notes

**Files to Create:**

```
apps/api/app/services/briefing/
├── __init__.py          # Package exports
├── service.py           # BriefingService class (main orchestrator)
└── narrative.py         # LLM narrative formatting

apps/api/app/models/
└── briefing.py          # BriefingResponse, BriefingSection models

apps/api/tests/services/briefing/
├── __init__.py
├── test_service.py      # BriefingService unit tests
└── test_narrative.py    # Narrative generation tests
```

**Directory Creation Required:**
- `apps/api/app/services/briefing/` (new package)
- `apps/api/tests/services/briefing/` (new test package)

### Testing Standards

**Unit Tests (with mocks):**
- Mock all 5 tools to return controlled ToolResult responses
- Test orchestration sequence and timeout handling
- Test partial failure scenarios
- Test narrative generation with sample data

**Integration Tests:**
- Use real tool instances with mocked data sources
- Test full flow from request to BriefingResponse
- Test 30-second timeout enforcement

### Dependencies & Integration Points

**Story Dependencies:**
- Epic 7 tools complete (confirmed - ActionListTool, etc. exist)
- No dependency on Story 8.1 (TTS) or 8.2 (STT) - audio is separate
- Stories 8.4+ depend on this story for BriefingService

**Integration Points:**
- Uses: ProductionStatusTool, SafetyEventsTool, OEEQueryTool, DowntimeAnalysisTool, ActionListTool
- Uses: `app.services.ai.llm_client` for narrative generation
- Used by: Story 8.4 (Morning Briefing Workflow), Story 8.5 (Supervisor Scoping)

### Error Handling Requirements

1. **Tool Failure:**
   - Log error, mark section as "failed"
   - Continue with other tools
   - Include failure message in section content

2. **LLM Failure:**
   - Fall back to structured data presentation
   - No narrative, just formatted metrics

3. **Timeout:**
   - Return partial response with completed sections
   - Mark remaining sections as "timed_out"
   - Log timeout event for monitoring

4. **All Tools Fail:**
   - Return minimal response explaining data unavailable
   - Suggest retrying in a few minutes

### Performance Considerations

- Run independent tools in parallel using `asyncio.gather()`
- Use tool caching (existing @cached_tool decorator)
- LLM call is the bottleneck - keep prompt concise
- Response should stream to frontend (future enhancement)

### References

- [Source: _bmad/bmm/data/architecture/voice-briefing.md#BriefingService Architecture]
- [Source: _bmad/bmm/data/architecture/voice-briefing.md#Performance Strategy]
- [Source: _bmad/bmm/data/architecture/implementation-patterns.md#BriefingService Pattern]
- [Source: _bmad/bmm/data/architecture/implementation-patterns.md#BriefingService Specific Rules]
- [Source: _bmad/bmm/data/prd/prd-functional-requirements.md#FR14-FR20]
- [Source: _bmad/bmm/data/prd/prd-non-functional-requirements.md#NFR8 (30s briefing)]
- [Source: _bmad-output/planning-artifacts/epic-8.md#Story 8.3]
- [Source: apps/api/app/services/agent/base.py] - ManufacturingTool and ToolResult patterns
- [Source: apps/api/app/services/agent/tools/production_status.py] - Example tool implementation
- [Source: apps/api/app/services/agent/tools/action_list.py] - Example tool implementation

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5

### Debug Log References

N/A

### Completion Notes List

- Created briefing models (BriefingSection, BriefingResponse, BriefingData, BriefingMetric, etc.)
- Implemented BriefingService as orchestration layer (NOT a ManufacturingTool)
- Added parallel tool execution with asyncio.gather for performance
- Implemented 30-second total timeout with per-tool 5-second timeouts (NFR8)
- Added graceful tool failure handling - continues with available data
- Created NarrativeGenerator with LLM integration and template fallback
- Template-based narrative generation for headline, wins, concerns, actions sections
- All sections include inline citations [Source: table_name]
- Conversational tone ("tracking behind" not "Variance: -3.2%")
- Created comprehensive unit tests for service and narrative generator

### File List

- apps/api/app/models/briefing.py
- apps/api/app/services/briefing/__init__.py
- apps/api/app/services/briefing/service.py
- apps/api/app/services/briefing/narrative.py
- apps/api/app/tests/services/briefing/__init__.py
- apps/api/app/tests/services/briefing/test_service.py
- apps/api/app/tests/services/briefing/test_narrative.py
