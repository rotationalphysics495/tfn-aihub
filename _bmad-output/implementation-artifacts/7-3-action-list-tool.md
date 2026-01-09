# Story 7.3: Action List Tool

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Plant Manager**,
I want **to ask "What should I focus on today?" and get a prioritized action list**,
so that I can **start my day with clear priorities based on data and focus on the highest-impact items first**.

## Acceptance Criteria

1. **Daily Action List Generation**
   - Given a user asks "What should I focus on today?"
   - When the Action List tool is invoked
   - Then the response includes:
     - Prioritized list of action items (max 5)
     - For each action: priority rank, asset, issue, recommended action
     - Supporting evidence for each item
     - Estimated impact (financial or operational)
   - And items are sorted: Safety first, then Financial Impact, then OEE gaps

2. **Area-Filtered Actions**
   - Given a user asks for actions for a specific area (e.g., "What should I focus on in Grinding?")
   - When the Action List tool is invoked
   - Then the response filters to that area
   - And maintains the same priority logic (Safety > Financial > OEE)

3. **No Issues Scenario**
   - Given no significant issues exist
   - When the Action List tool is invoked
   - Then the response states "No critical issues identified - operations look healthy"
   - And suggests proactive improvements if patterns indicate opportunities

4. **Action Engine Integration**
   - Given the Action Engine has already run for today
   - When the Action List tool is invoked
   - Then results from the existing Action Engine are returned
   - And response indicates data freshness

5. **Priority Logic**
   - Safety events (severity > 0) are always highest priority
   - OEE gaps (< target) are medium priority, sorted by gap size
   - Financial losses are sorted by dollar impact
   - Each action includes confidence level

6. **Data Freshness & Caching**
   - Cache TTL: 5 minutes (or invalidate on safety event)
   - Data freshness timestamp included in response
   - Support for `force_refresh` parameter

## Tasks / Subtasks

- [ ] Task 1: Define Action List Schemas (AC: #1, #2)
  - [ ] 1.1 Create `ActionListInput` Pydantic model with fields: `area_filter` (optional), `max_actions` (default: 5), `date` (default: today)
  - [ ] 1.2 Create `ActionItem` model with fields: `priority`, `asset`, `issue_type`, `description`, `recommended_action`, `evidence`, `estimated_impact`, `confidence`
  - [ ] 1.3 Create `ActionListOutput` model with fields: `actions`, `summary`, `data_freshness`, `citations`
  - [ ] 1.4 Add schemas to `apps/api/app/models/agent.py`

- [ ] Task 2: Implement Action List Tool (AC: #1, #2, #3)
  - [ ] 2.1 Create `apps/api/app/services/agent/tools/action_list.py`
  - [ ] 2.2 Integrate with existing Action Engine logic from Epic 3
  - [ ] 2.3 Query `daily_summaries`, `safety_events`, `cost_centers`
  - [ ] 2.4 Implement area filtering for scoped queries
  - [ ] 2.5 Implement "no issues" detection and proactive suggestions
  - [ ] 2.6 Return max 5 prioritized actions

- [ ] Task 3: Implement Priority Logic (AC: #5)
  - [ ] 3.1 Safety priority: Safety > 0 -> highest priority
  - [ ] 3.2 OEE priority: OEE < Target -> medium priority, sorted by gap
  - [ ] 3.3 Financial priority: Loss > Threshold -> sorted by $ impact
  - [ ] 3.4 Combine and sort: Safety first, then Financial, then OEE
  - [ ] 3.5 Add confidence scoring to each action

- [ ] Task 4: Integrate with LangChain Agent (AC: #1, #2)
  - [ ] 4.1 Create LangChain Tool wrapper for ActionListTool
  - [ ] 4.2 Define tool description for agent selection
  - [ ] 4.3 Register tool with ManufacturingAgent
  - [ ] 4.4 Test tool selection for "focus on" and "action" queries

- [ ] Task 5: Implement Caching (AC: #6)
  - [ ] 5.1 Add 5-minute cache for action list results
  - [ ] 5.2 Implement cache invalidation on safety event
  - [ ] 5.3 Cache key includes: area_filter, date
  - [ ] 5.4 Include `cached_at` in response metadata
  - [ ] 5.5 Support `force_refresh` parameter

- [ ] Task 6: Testing and Validation (AC: #1-6)
  - [ ] 6.1 Unit tests for action list generation
  - [ ] 6.2 Unit tests for priority sorting
  - [ ] 6.3 Unit tests for area filtering
  - [ ] 6.4 Unit tests for "no issues" scenario
  - [ ] 6.5 Integration tests for Action Engine integration
  - [ ] 6.6 Performance tests (< 2 second response time)

## Dev Notes

### Architecture Patterns

- **Backend Framework:** Python FastAPI (apps/api)
- **AI Orchestration:** LangChain AgentExecutor with tool registration
- **Action Engine:** Leverage existing logic from Epic 3 (Story 3.1, 3.2)
- **Citation System:** Integrate with existing citation infrastructure from Story 4-5

### Technical Requirements

**Action List Schemas:**
```python
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime, date
from decimal import Decimal

class ActionListInput(BaseModel):
    """Input schema for Action List tool"""
    area_filter: Optional[str] = Field(
        default=None,
        description="Filter to specific area (e.g., 'Grinding', 'Packaging')"
    )
    max_actions: int = Field(
        default=5,
        description="Maximum number of actions to return"
    )
    date: Optional[date] = Field(
        default=None,
        description="Date for actions (defaults to today)"
    )
    force_refresh: bool = Field(
        default=False,
        description="Bypass cache and fetch fresh data"
    )

class ActionItem(BaseModel):
    """A single prioritized action item"""
    priority: int  # 1 = highest
    priority_category: Literal["safety", "financial", "oee"]
    asset: str
    issue_type: str  # e.g., "Safety Stop", "OEE Gap", "High Downtime"
    description: str
    recommended_action: str
    evidence: str  # Supporting data
    estimated_impact: Optional[str]  # "$2,340 loss" or "15% OEE gap"
    confidence: float  # 0.0 - 1.0

class ActionListOutput(BaseModel):
    """Output schema for Action List tool"""
    actions: List[ActionItem]
    summary: str
    total_financial_impact: Optional[Decimal]
    data_freshness: datetime
    is_healthy: bool  # True if no critical issues
    proactive_suggestions: List[str]  # When operations healthy
    citations: List[dict]
```

**Action List Tool Implementation:**
```python
from langchain.tools import BaseTool
from typing import Type
from apps.api.app.services.action_engine import ActionEngine

# Priority thresholds
SAFETY_THRESHOLD = 0  # Any safety event is critical
OEE_GAP_THRESHOLD = 0.10  # 10% below target triggers action
FINANCIAL_THRESHOLD = 1000  # $1000+ loss triggers action

class ActionListTool(BaseTool):
    name: str = "action_list"
    description: str = """Get a prioritized list of daily actions based on safety events,
    OEE gaps, and financial impact. Use this when the user asks 'What should I focus on?',
    'What needs attention?', 'Any priorities for today?', or wants a morning briefing.
    Returns max 5 items sorted by: Safety (critical) > Financial Impact > OEE Gaps."""
    args_schema: Type[ActionListInput] = ActionListInput

    async def _arun(
        self,
        area_filter: Optional[str] = None,
        max_actions: int = 5,
        date: Optional[date] = None,
        force_refresh: bool = False
    ) -> ActionListOutput:

        target_date = date or datetime.now().date()

        # Check cache first (unless force_refresh)
        cache_key = f"action_list:{area_filter or 'all'}:{target_date}"
        if not force_refresh:
            cached = await self.cache.get(cache_key)
            if cached:
                return cached

        # Leverage existing Action Engine from Epic 3
        raw_actions = await self.action_engine.generate_actions(
            date=target_date,
            area=area_filter
        )

        # Categorize and prioritize
        safety_actions = []
        financial_actions = []
        oee_actions = []

        for action in raw_actions:
            if action.safety_severity > SAFETY_THRESHOLD:
                safety_actions.append(self._to_action_item(action, "safety"))
            elif action.financial_loss > FINANCIAL_THRESHOLD:
                financial_actions.append(self._to_action_item(action, "financial"))
            elif action.oee_gap > OEE_GAP_THRESHOLD:
                oee_actions.append(self._to_action_item(action, "oee"))

        # Sort within categories
        safety_actions.sort(key=lambda x: -x.confidence)  # By severity
        financial_actions.sort(key=lambda x: -float(action.financial_loss))
        oee_actions.sort(key=lambda x: -action.oee_gap)

        # Combine with priority ordering
        all_actions = []
        priority = 1
        for action in safety_actions + financial_actions + oee_actions:
            action.priority = priority
            all_actions.append(action)
            priority += 1
            if len(all_actions) >= max_actions:
                break

        # Handle no issues case
        is_healthy = len(all_actions) == 0
        proactive = []
        if is_healthy:
            proactive = await self._get_proactive_suggestions(area_filter)

        # Calculate total financial impact
        total_impact = sum(
            a.financial_loss for a in raw_actions
            if hasattr(a, 'financial_loss')
        )

        result = ActionListOutput(
            actions=all_actions,
            summary=self._generate_summary(all_actions, is_healthy),
            total_financial_impact=total_impact if total_impact > 0 else None,
            data_freshness=datetime.now(),
            is_healthy=is_healthy,
            proactive_suggestions=proactive,
            citations=self._generate_citations(raw_actions)
        )

        # Cache for 5 minutes
        await self.cache.set(cache_key, result, ttl=300)

        return result

    def _to_action_item(
        self,
        raw: ActionEngineResult,
        category: str
    ) -> ActionItem:
        """Convert Action Engine result to ActionItem"""
        return ActionItem(
            priority=0,  # Will be set during sorting
            priority_category=category,
            asset=raw.asset_name,
            issue_type=raw.issue_type,
            description=raw.description,
            recommended_action=raw.recommendation,
            evidence=raw.evidence,
            estimated_impact=self._format_impact(raw, category),
            confidence=raw.confidence
        )

    def _format_impact(self, raw: ActionEngineResult, category: str) -> str:
        """Format impact based on category"""
        if category == "safety":
            return f"Safety severity: {raw.safety_severity}"
        elif category == "financial":
            return f"${raw.financial_loss:,.0f} estimated loss"
        else:
            return f"{raw.oee_gap * 100:.1f}% below OEE target"
```

**Action Engine Integration (from Epic 3):**
```python
# Reference existing Action Engine logic
# Located in: apps/api/app/services/action_engine.py (from Story 3.1)

from apps.api.app.services.action_engine import ActionEngine

class ActionListTool(BaseTool):
    def __init__(self, db_session, cache):
        self.action_engine = ActionEngine(db_session)
        self.cache = cache
```

### Database Tables Referenced

| Table | Usage |
|-------|-------|
| `daily_summaries` | OEE, downtime, financial metrics |
| `safety_events` | Safety incidents with severity |
| `cost_centers` | Financial impact calculation |
| `assets` | Asset names and area mapping |
| `shift_targets` | Target values for gap calculation |

### Dependencies

**Requires (must be completed):**
- Story 3.1: Action Engine Logic (provides core prioritization logic)
- Story 3.2: Daily Action List API (provides Action Engine service)
- Story 5.1: Agent Framework & Tool Registry (provides tool registration pattern)
- Story 5.2: Data Access Abstraction Layer (provides data source interface)
- Story 4.5: Cited Response Generation (provides citation infrastructure)

**Enables:**
- FR7.4: Proactive Action Tools capability
- Natural language access to Action Engine insights
- Morning briefing automation for plant managers

### Project Structure Notes

```
apps/api/app/
  services/
    agent/
      tools/
        action_list.py            # Action List tool (NEW)
    action_engine.py              # Existing from Epic 3 (REFERENCE)
  models/
    agent.py                      # Add ActionListInput/Output (MODIFY)

apps/api/tests/
  test_action_list_tool.py        # Unit and integration tests (NEW)
```

### NFR Compliance

- **NFR1 (Accuracy):** All actions cite specific data sources
- **NFR4 (Agent Honesty):** Clear "operations healthy" when no issues
- **NFR6 (Response Structure):** Prioritized list with evidence and impact
- **NFR7 (Caching):** 5-minute cache with safety event invalidation

### Testing Guidance

**Unit Tests:**
```python
import pytest
from datetime import date
from decimal import Decimal

@pytest.mark.asyncio
async def test_action_list_generation():
    """Test basic action list generation with priorities"""
    tool = ActionListTool(
        action_engine=mock_action_engine,
        cache=mock_cache
    )
    result = await tool._arun()

    assert len(result.actions) <= 5
    # Verify priority ordering: safety first
    for i, action in enumerate(result.actions):
        assert action.priority == i + 1
        if i > 0:
            prev = result.actions[i-1]
            # Safety should come before non-safety
            if prev.priority_category == "safety":
                continue  # OK if current is anything
            elif action.priority_category == "safety":
                pytest.fail("Safety action should come before non-safety")

@pytest.mark.asyncio
async def test_safety_first_priority():
    """Test that safety events are always highest priority"""
    # Mock with mixed safety, financial, OEE issues
    tool = ActionListTool(action_engine=mock_engine_mixed, cache=mock_cache)
    result = await tool._arun()

    safety_indices = [
        i for i, a in enumerate(result.actions)
        if a.priority_category == "safety"
    ]
    non_safety_indices = [
        i for i, a in enumerate(result.actions)
        if a.priority_category != "safety"
    ]

    if safety_indices and non_safety_indices:
        assert max(safety_indices) < min(non_safety_indices)

@pytest.mark.asyncio
async def test_area_filtering():
    """Test filtering actions by area"""
    tool = ActionListTool(action_engine=mock_action_engine, cache=mock_cache)
    result = await tool._arun(area_filter="Grinding")

    for action in result.actions:
        assert action.asset in GRINDING_ASSETS  # All assets from Grinding area

@pytest.mark.asyncio
async def test_no_issues_healthy():
    """Test 'operations healthy' response when no issues"""
    tool = ActionListTool(action_engine=mock_engine_healthy, cache=mock_cache)
    result = await tool._arun()

    assert result.is_healthy == True
    assert len(result.actions) == 0
    assert len(result.proactive_suggestions) > 0
    assert "healthy" in result.summary.lower()

@pytest.mark.asyncio
async def test_cache_behavior():
    """Test 5-minute caching"""
    tool = ActionListTool(action_engine=mock_action_engine, cache=mock_cache)

    # First call - should hit action engine
    result1 = await tool._arun()
    assert mock_action_engine.call_count == 1

    # Second call - should use cache
    result2 = await tool._arun()
    assert mock_action_engine.call_count == 1  # No additional call

    # Force refresh - should bypass cache
    result3 = await tool._arun(force_refresh=True)
    assert mock_action_engine.call_count == 2

@pytest.mark.asyncio
async def test_financial_impact_calculation():
    """Test total financial impact aggregation"""
    tool = ActionListTool(action_engine=mock_action_engine, cache=mock_cache)
    result = await tool._arun()

    if result.total_financial_impact:
        assert result.total_financial_impact > 0
```

**Integration Tests:**
```python
@pytest.mark.asyncio
async def test_tool_agent_integration():
    """Test tool is correctly selected by agent"""
    agent = ManufacturingAgent(tools=[action_list_tool])
    response = await agent.invoke("What should I focus on today?")

    assert "action_list" in response.tool_calls

@pytest.mark.asyncio
async def test_morning_briefing_query():
    """Test various morning briefing queries select this tool"""
    queries = [
        "What should I focus on today?",
        "Any priorities for this morning?",
        "What needs attention?",
        "Give me my daily action list",
        "What are today's priorities?"
    ]

    agent = ManufacturingAgent(tools=[action_list_tool])
    for query in queries:
        response = await agent.invoke(query)
        assert "action_list" in response.tool_calls
```

### Response Format Examples

**Normal Action List:**
```markdown
## Daily Action List
*As of 7:15 AM - Data from morning pipeline*

### SAFETY FIRST

**#1 - Packaging Line 2** [CRITICAL]
- Issue: Safety stop triggered at 6:42 AM
- Action: Confirm lockout/tagout complete before restart
- Evidence: safety_events record showing unresolved incident
- Impact: Safety severity HIGH
[Citation: safety_events @ 06:42:00]

### OEE GAPS

**#2 - Grinder 5**
- Issue: OEE at 62% (Target: 85%)
- Action: Review blade change SOP - frequency seems high
- Evidence: 47 minutes downtime from "Blade Change" yesterday
- Impact: $2,340 estimated loss
[Citation: daily_summaries 2026-01-08, cost_centers GR-001]

**#3 - CAMA 800-1**
- Issue: Running 12% below target
- Action: Check operator staffing during shift change
- Evidence: Pattern - slowing after lunch break (3 days in a row)
- Impact: 12% OEE gap
[Citation: daily_summaries 2026-01-06 to 2026-01-08]

---
**Total Financial Impact Today:** $4,890

Should I dive deeper into any of these?
```

**Healthy Operations:**
```markdown
## Daily Action List
*As of 7:15 AM - Data from morning pipeline*

**No critical issues identified - operations look healthy!**

All systems are within normal parameters:
- No safety events in last 24 hours
- All OEE metrics above target
- Financial losses below threshold

### Proactive Suggestions

Since things are running smoothly, consider:
1. Review Grinder 5 preventive maintenance schedule (due in 3 days)
2. Analyze last week's best practices from Packaging area
3. Update shift handoff documentation

[Citation: daily_summaries 2026-01-08]
```

### References

- [Source: _bmad-output/planning-artifacts/epic-7.md#Story 7.3] - Action List Tool requirements
- [Source: _bmad-output/planning-artifacts/prd-addendum-ai-agent-tools.md#FR7.4] - Proactive Action Tools specification
- [Source: _bmad/bmm/data/architecture.md#7. AI & Memory Architecture] - Action Engine logic reference
- [Source: _bmad-output/implementation-artifacts/3-1-action-engine-logic.md] - Action Engine implementation
- [Source: _bmad-output/implementation-artifacts/3-2-daily-action-list-api.md] - Action List API patterns
- [Source: _bmad-output/implementation-artifacts/4-5-cited-response-generation.md] - Citation infrastructure

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
