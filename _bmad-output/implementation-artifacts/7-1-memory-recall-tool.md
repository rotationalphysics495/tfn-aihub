# Story 7.1: Memory Recall Tool

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Plant Manager**,
I want **the agent to remember and recall our past conversations about specific assets or topics**,
so that I can **build on previous discussions without repeating context and leverage historical insights**.

## Acceptance Criteria

1. **Topic-Based Memory Recall**
   - Given a user asks "What did we discuss about Grinder 5?"
   - When the Memory Recall tool is invoked
   - Then the response includes:
     - Summary of past conversations mentioning "Grinder 5"
     - Key decisions or conclusions reached
     - Dates of relevant conversations
     - Links to related topics discussed
   - And results are sorted by relevance, then recency

2. **Time-Range Memory Query**
   - Given a user asks "What issues have we talked about this week?"
   - When the Memory Recall tool is invoked
   - Then the response summarizes topics by category
   - And highlights unresolved items
   - And groups conversations by asset or topic area

3. **No Memory Found Handling**
   - Given no relevant memories exist for the query
   - When the Memory Recall tool is invoked
   - Then the response states "I don't have any previous conversations about [topic]"
   - And offers to help with a fresh inquiry
   - And does NOT hallucinate fake memories

4. **Stale Memory Notification**
   - Given memories exist but are old (>30 days)
   - When the Memory Recall tool is invoked
   - Then the response includes a note: "This was discussed [X] days ago - things may have changed"
   - And suggests checking for updated data if applicable

5. **Memory Provenance & Citations**
   - All recalled memories include memory_id for traceability
   - Timestamps are displayed in user-friendly format
   - Citations follow established format from Story 4-5
   - Each memory includes confidence/relevance score

6. **Performance Requirements**
   - Memory recall completes within 2 seconds (p95)
   - No caching (always fetch fresh for accuracy)
   - Supports multiple simultaneous recall requests

## Tasks / Subtasks

- [ ] Task 1: Define Memory Recall Schemas (AC: #1, #5)
  - [ ] 1.1 Create `MemoryRecallInput` Pydantic model with fields: `query`, `asset_id` (optional), `time_range` (optional), `max_results` (default: 5)
  - [ ] 1.2 Create `RecalledMemory` model with fields: `memory_id`, `content`, `created_at`, `relevance_score`, `asset_id`, `topic_category`
  - [ ] 1.3 Create `MemoryRecallOutput` model with fields: `memories`, `summary`, `unresolved_items`, `citations`
  - [ ] 1.4 Add schemas to `apps/api/app/models/agent.py`

- [ ] Task 2: Implement Memory Recall Tool (AC: #1, #2, #3, #4)
  - [ ] 2.1 Create `apps/api/app/services/agent/tools/memory_recall.py`
  - [ ] 2.2 Implement Mem0 vector search with semantic similarity
  - [ ] 2.3 Apply relevance threshold (0.7 similarity score minimum)
  - [ ] 2.4 Filter by `user_id` and optional `asset_id`
  - [ ] 2.5 Implement time-range filtering for recency queries
  - [ ] 2.6 Add stale memory detection (>30 days threshold)
  - [ ] 2.7 Return top 5 most relevant memories

- [ ] Task 3: Implement Memory Summarization (AC: #1, #2)
  - [ ] 3.1 Create summarization logic for multiple memories
  - [ ] 3.2 Extract key decisions and conclusions from conversations
  - [ ] 3.3 Identify and highlight unresolved items
  - [ ] 3.4 Group memories by topic category

- [ ] Task 4: Integrate with LangChain Agent (AC: #1, #2)
  - [ ] 4.1 Create LangChain Tool wrapper for MemoryRecallTool
  - [ ] 4.2 Define tool description for agent selection
  - [ ] 4.3 Register tool with ManufacturingAgent
  - [ ] 4.4 Test tool selection accuracy

- [ ] Task 5: Implement Citation Generation (AC: #5)
  - [ ] 5.1 Integrate with CitationGenerator from Story 4-5
  - [ ] 5.2 Generate memory citations with `memory_id` and timestamps
  - [ ] 5.3 Format citations for display in response

- [ ] Task 6: Testing and Validation (AC: #1-6)
  - [ ] 6.1 Unit tests for MemoryRecallTool with mock Mem0 responses
  - [ ] 6.2 Unit tests for relevance threshold filtering
  - [ ] 6.3 Unit tests for stale memory detection
  - [ ] 6.4 Unit tests for "no memories found" handling
  - [ ] 6.5 Integration tests for LangChain tool registration
  - [ ] 6.6 Performance tests for 2-second latency requirement

## Dev Notes

### Architecture Patterns

- **Backend Framework:** Python FastAPI (apps/api)
- **AI Orchestration:** LangChain AgentExecutor with tool registration
- **Memory Layer:** Mem0 for long-term memory storage and retrieval
- **Citation System:** Integrate with existing citation infrastructure from Story 4-5

### Technical Requirements

**Mem0 Query Integration:**
```python
from mem0 import MemoryClient
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta

class MemoryRecallInput(BaseModel):
    """Input schema for Memory Recall tool"""
    query: str = Field(description="The topic, asset, or question to recall memories about")
    asset_id: Optional[str] = Field(default=None, description="Optional asset ID to filter memories")
    time_range_days: Optional[int] = Field(default=None, description="Limit to memories within X days")
    max_results: int = Field(default=5, description="Maximum memories to return")

class RecalledMemory(BaseModel):
    """A single recalled memory with provenance"""
    memory_id: str
    content: str
    created_at: datetime
    relevance_score: float
    asset_id: Optional[str]
    topic_category: Optional[str]
    is_stale: bool = False  # True if >30 days old

class MemoryRecallOutput(BaseModel):
    """Output schema for Memory Recall tool"""
    memories: List[RecalledMemory]
    summary: str
    unresolved_items: List[str]
    related_topics: List[str]
    citations: List[dict]  # Memory citations
```

**Memory Recall Tool Implementation:**
```python
from langchain.tools import BaseTool
from mem0 import MemoryClient

RELEVANCE_THRESHOLD = 0.7
STALE_THRESHOLD_DAYS = 30

class MemoryRecallTool(BaseTool):
    name: str = "memory_recall"
    description: str = """Retrieve and summarize past conversations and context about specific assets,
    topics, or issues. Use this when the user asks about previous discussions, past decisions,
    or wants to recall what was discussed before. Examples: 'What did we discuss about Grinder 5?',
    'What issues have we talked about this week?', 'Remind me what we decided about maintenance'."""
    args_schema: Type[MemoryRecallInput] = MemoryRecallInput

    async def _arun(
        self,
        query: str,
        asset_id: Optional[str] = None,
        time_range_days: Optional[int] = None,
        max_results: int = 5
    ) -> MemoryRecallOutput:
        # Build Mem0 search filters
        filters = {}
        if asset_id:
            filters["asset_id"] = asset_id

        # Search memories with semantic similarity
        memories = await self.mem0_client.search(
            query=query,
            user_id=self.user_id,
            filters=filters if filters else None,
            limit=max_results * 2  # Fetch extra for filtering
        )

        # Filter by relevance threshold
        relevant_memories = [
            m for m in memories
            if m.score >= RELEVANCE_THRESHOLD
        ][:max_results]

        # Handle no memories case
        if not relevant_memories:
            return MemoryRecallOutput(
                memories=[],
                summary=f"I don't have any previous conversations about '{query}'",
                unresolved_items=[],
                related_topics=[],
                citations=[]
            )

        # Process memories with provenance
        recalled = []
        for m in relevant_memories:
            is_stale = (datetime.now() - m.created_at).days > STALE_THRESHOLD_DAYS
            recalled.append(RecalledMemory(
                memory_id=m.id,
                content=m.content,
                created_at=m.created_at,
                relevance_score=m.score,
                asset_id=m.metadata.get("asset_id"),
                topic_category=m.metadata.get("topic"),
                is_stale=is_stale
            ))

        # Generate summary and extract insights
        summary = await self._summarize_memories(recalled, query)
        unresolved = await self._extract_unresolved_items(recalled)
        related = self._extract_related_topics(recalled)
        citations = self._generate_citations(recalled)

        return MemoryRecallOutput(
            memories=recalled,
            summary=summary,
            unresolved_items=unresolved,
            related_topics=related,
            citations=citations
        )
```

**LangChain Agent Integration:**
```python
# Register tool with the Manufacturing Agent
from langchain.agents import AgentExecutor

memory_recall_tool = MemoryRecallTool(
    mem0_client=mem0_client,
    user_id=current_user.id
)

# Add to agent's tool list
agent_tools = [
    asset_lookup_tool,
    oee_query_tool,
    # ... other tools from Epic 5/6
    memory_recall_tool,  # NEW - Epic 7.1
]
```

### Database Tables Referenced

| Table | Usage |
|-------|-------|
| `memories` (Mem0) | Primary memory storage with vector embeddings |
| `daily_summaries` | Cross-reference for asset-specific memories |
| `safety_events` | Cross-reference for safety discussion memories |

### Dependencies

**Requires (must be completed):**
- Story 4.1: Mem0 Vector Memory Integration (provides memory storage infrastructure)
- Story 4.4: Asset History Memory (provides asset-specific memory patterns)
- Story 4.5: Cited Response Generation (provides citation infrastructure)
- Story 5.1: Agent Framework & Tool Registry (provides tool registration pattern)

**Enables:**
- FR7.3: Memory Recall capability for conversational context
- Story 7.2: Comparative Analysis can leverage memory context
- Story 7.5: Recommendation Engine can use historical patterns

### Project Structure Notes

```
apps/api/app/
  services/
    agent/
      tools/
        memory_recall.py          # Memory Recall tool implementation (NEW)
  models/
    agent.py                      # Add MemoryRecallInput/Output schemas (MODIFY)

apps/api/tests/
  test_memory_recall_tool.py      # Unit and integration tests (NEW)
```

### NFR Compliance

- **NFR1 (Accuracy):** Memory citations provide traceability; no hallucinated memories
- **NFR4 (Agent Honesty):** Clear "no memories found" response; stale memory warnings
- **NFR6 (Response Structure):** Structured output with citations array and summary

### Testing Guidance

**Unit Tests:**
```python
import pytest
from datetime import datetime, timedelta

@pytest.mark.asyncio
async def test_memory_recall_with_results():
    """Test successful memory recall with relevant results"""
    tool = MemoryRecallTool(mem0_client=mock_mem0, user_id="test-user")
    result = await tool._arun(query="Grinder 5 maintenance")

    assert len(result.memories) > 0
    assert result.summary != ""
    assert all(m.relevance_score >= 0.7 for m in result.memories)

@pytest.mark.asyncio
async def test_memory_recall_no_results():
    """Test handling when no memories match query"""
    tool = MemoryRecallTool(mem0_client=mock_mem0_empty, user_id="test-user")
    result = await tool._arun(query="nonexistent topic")

    assert len(result.memories) == 0
    assert "don't have any previous conversations" in result.summary

@pytest.mark.asyncio
async def test_stale_memory_detection():
    """Test that old memories are flagged as stale"""
    mock_memory = MockMemory(
        created_at=datetime.now() - timedelta(days=45),
        score=0.85
    )
    tool = MemoryRecallTool(mem0_client=mock_mem0_stale, user_id="test-user")
    result = await tool._arun(query="old discussion")

    assert result.memories[0].is_stale == True

@pytest.mark.asyncio
async def test_relevance_threshold_filtering():
    """Test that low-relevance memories are filtered out"""
    # Mock returns memories with scores: 0.9, 0.75, 0.5, 0.3
    tool = MemoryRecallTool(mem0_client=mock_mem0_mixed, user_id="test-user")
    result = await tool._arun(query="test query")

    # Only 0.9 and 0.75 should pass threshold
    assert len(result.memories) == 2
    assert all(m.relevance_score >= 0.7 for m in result.memories)

@pytest.mark.asyncio
async def test_asset_filter():
    """Test filtering memories by asset_id"""
    tool = MemoryRecallTool(mem0_client=mock_mem0, user_id="test-user")
    result = await tool._arun(query="issues", asset_id="grinder-5")

    assert all(m.asset_id == "grinder-5" for m in result.memories)
```

**Integration Tests:**
```python
@pytest.mark.asyncio
async def test_tool_agent_integration():
    """Test tool is correctly selected by agent"""
    agent = ManufacturingAgent(tools=[memory_recall_tool])
    response = await agent.invoke("What did we discuss about Grinder 5?")

    # Verify memory_recall tool was invoked
    assert "memory_recall" in response.tool_calls

@pytest.mark.asyncio
async def test_memory_citations_format():
    """Test citation format matches Story 4-5 standards"""
    tool = MemoryRecallTool(mem0_client=mock_mem0, user_id="test-user")
    result = await tool._arun(query="Grinder 5")

    for citation in result.citations:
        assert "memory_id" in citation
        assert "timestamp" in citation
        assert citation["source_type"] == "memory"
```

### Response Format Examples

**Successful Recall:**
```markdown
Based on our previous conversations about Grinder 5:

**Summary:**
Over the past 2 weeks, we discussed 3 main topics related to Grinder 5:
1. Blade change frequency (discussed Jan 5) - concluded SOP review needed
2. Output variance during shift changes (discussed Jan 3) - still monitoring
3. Safety stop incident (discussed Dec 28) - resolved, lockout procedure updated

**Key Decisions:**
- Schedule blade changes every 72 hours instead of reactive replacement
- Add supervisor handoff checklist at shift change

**Unresolved Items:**
- Output variance still occurring - need more data

[Memory: mem-id-abc123 @ 2026-01-05]
[Memory: mem-id-def456 @ 2026-01-03]
[Memory: mem-id-ghi789 @ 2025-12-28] (Note: This was discussed 12 days ago)

Would you like me to look up current data on any of these topics?
```

**No Memories Found:**
```markdown
I don't have any previous conversations about "Line 12 maintenance".

This might be because:
- We haven't discussed this topic yet
- The topic was discussed under a different name

Would you like me to:
1. Look up current data for Line 12?
2. Search for similar topics we've discussed?
```

### References

- [Source: _bmad-output/planning-artifacts/epic-7.md#Story 7.1] - Memory Recall Tool requirements
- [Source: _bmad-output/planning-artifacts/prd-addendum-ai-agent-tools.md#FR7.3] - Intelligence & Memory Tools specification
- [Source: _bmad/bmm/data/architecture.md#7. AI & Memory Architecture] - Mem0 integration patterns
- [Source: _bmad-output/implementation-artifacts/4-1-mem0-vector-memory-integration.md] - Mem0 setup and patterns
- [Source: _bmad-output/implementation-artifacts/4-5-cited-response-generation.md] - Citation infrastructure
- [Source: _bmad/bmm/data/prd.md#FR6] - AI Chat with Memory requirements

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
