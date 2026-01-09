---
stepsCompleted: ["draft"]
parentDocument: "_bmad/bmm/data/prd.md"
workflowType: "prd-addendum"
version: "1.1"
---

# PRD Addendum: AI Agent Tools

**Parent PRD:** Manufacturing Performance Assistant v1.0
**Author:** Caleb
**Date:** 2026-01-09
**Status:** Draft

---

## 1. Purpose & Context

### Why This Addendum

The base PRD (v1.0) established FR6 (AI Chat with Memory) which was implemented in Epic 4 with basic Text-to-SQL capabilities. While functional, the current implementation requires the LLM to generate SQL for every query, which introduces:

- **Latency:** Each query requires LLM reasoning + SQL generation + execution
- **Inconsistency:** Similar questions may produce different SQL and varying response formats
- **Fragility:** Complex queries can fail silently or return confusing results
- **Limited Scope:** Text-to-SQL struggles with multi-step reasoning (e.g., "What should I focus on today?")

This addendum defines a **LangChain Agent with specialized tools** that provides structured, reliable responses for the most common plant manager questions while maintaining the flexibility of natural language interaction.

### Relationship to Existing Requirements

| Existing Requirement | Enhancement |
|---------------------|-------------|
| FR6 (AI Chat with Memory) | Extended with structured tool calling |
| NFR1 (Accuracy/Citations) | Tools return cited, structured data by design |
| NFR3 (Read-Only) | All tools enforce read-only access |

---

## 2. Goals

### Primary Goals

1. **Reliability:** Common questions return consistent, structured responses every time
2. **Speed:** Pre-built tools execute faster than dynamic SQL generation
3. **Transparency:** Every response cites specific data sources and timestamps
4. **Extensibility:** Architecture supports adding new tools and data sources (MSSQL) without refactoring

### Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Tool Response Time | < 2 seconds (p95) | API latency tracking |
| Citation Coverage | 100% of factual claims | Audit log analysis |
| User Satisfaction | Reduced follow-up questions | Query session analysis |
| Tool Selection Accuracy | > 90% correct tool for intent | Manual review sample |

---

## 3. New Functional Requirements

### FR7: AI Agent Tools

The AI Chat interface SHALL provide specialized tools for common plant manager queries, organized into four tiers:

#### FR7.1: Core Operations Tools (Tier 1)

| Tool | Purpose | Input | Output |
|------|---------|-------|--------|
| **Asset Lookup** | Retrieve asset metadata, current status, and recent performance | Asset name or ID | Asset details, current state, 7-day performance summary |
| **OEE Query** | Calculate OEE with breakdown by component | Area, asset, or plant-wide; time range | OEE percentage, availability, performance, quality breakdown |
| **Downtime Analysis** | Investigate downtime reasons and patterns | Asset or area; time range | Downtime reasons ranked by duration, Pareto distribution |
| **Production Status** | Real-time output vs target across assets | Area filter (optional) | Current output, target, variance, status per asset |

#### FR7.2: Safety & Financial Tools (Tier 2)

| Tool | Purpose | Input | Output |
|------|---------|-------|--------|
| **Safety Events** | Query safety incidents | Time range; severity filter (optional) | Events with severity, resolution status, affected assets |
| **Financial Impact** | Calculate cost of downtime/waste | Asset or area; time range | Dollar loss breakdown by category |
| **Cost of Loss** | Rank issues by financial impact | Time range | Prioritized list of losses with root causes |

#### FR7.3: Intelligence & Memory Tools (Tier 3)

| Tool | Purpose | Input | Output |
|------|---------|-------|--------|
| **Trend Analysis** | Time-series performance analysis | Asset; metric; time range (7-90 days) | Trend direction, anomalies, comparison to baseline |
| **Memory Recall** | Retrieve relevant conversation history | Topic or asset reference | Previous discussions, decisions, context |
| **Comparative Analysis** | Side-by-side asset/area comparison | Two or more assets/areas; metrics | Comparison table with variance highlighting |

#### FR7.4: Proactive Action Tools (Tier 4)

| Tool | Purpose | Input | Output |
|------|---------|-------|--------|
| **Action List** | Get prioritized daily actions | Date (default: today) | Ranked action items with evidence and impact |
| **Alert Check** | Query active warnings/issues | Severity filter (optional) | Active alerts with status and recommended response |
| **Recommendation Engine** | Suggest improvements based on patterns | Asset or area; focus area (OEE, safety, cost) | Specific recommendations with supporting evidence |

---

## 4. Non-Functional Requirements

### NFR4: Agent Honesty

The AI Agent SHALL:
- Never fabricate data or statistics
- Clearly state when information is unavailable: *"I don't have data for [X] in the requested time range"*
- Distinguish between "no data" and "zero value" in responses
- Indicate data freshness: *"Based on data as of [timestamp]"*

### NFR5: Tool Extensibility

The tool architecture SHALL:
- Support adding new data sources (MSSQL) without modifying existing tools
- Use a data access abstraction layer that can route queries to appropriate sources
- Allow new tools to be registered without modifying the agent core
- Maintain backward compatibility when tools are updated

### NFR6: Response Structure

All tool responses SHALL:
- Include a `citations` array with source table, query, and timestamp
- Return structured data (JSON) that the agent formats for display
- Include confidence indicators where applicable
- Provide suggested follow-up questions when relevant

---

## 5. Technical Design

### 5.1 Architecture Overview

```
User Message
    │
    ▼
┌─────────────────────────────────────────────┐
│           Manufacturing Agent                │
│     (LangChain AgentExecutor + GPT-4)       │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │         Tool Selection              │    │
│  │  (Based on intent classification)   │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
    │
    ▼ selects tool(s)
┌─────────┬─────────┬─────────┬─────────┬─────────┐
│ Asset   │ OEE     │ Safety  │ Memory  │ Action  │
│ Lookup  │ Query   │ Events  │ Recall  │ List    │
│  ...    │  ...    │  ...    │  ...    │  ...    │
└────┬────┴────┬────┴────┬────┴────┬────┴────┬────┘
     │         │         │         │         │
     ▼         ▼         ▼         ▼         ▼
┌─────────────────────────────────────────────────┐
│           Data Access Layer                      │
│  ┌──────────────┐    ┌──────────────┐           │
│  │   Supabase   │    │    MSSQL     │           │
│  │   Adapter    │    │   Adapter    │           │
│  │   (Active)   │    │   (Future)   │           │
│  └──────────────┘    └──────────────┘           │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│         Citation & Grounding Layer              │
│   (Validates claims, attaches source refs)      │
└─────────────────────────────────────────────────┘
    │
    ▼
Response with Citations
```

### 5.2 Data Access Abstraction

To support future MSSQL integration, tools SHALL NOT query databases directly. Instead:

```python
# Abstract interface
class DataSource(Protocol):
    async def get_asset(self, asset_id: str) -> Asset | None
    async def get_oee(self, asset_id: str, start: datetime, end: datetime) -> OEEMetrics
    async def get_downtime(self, asset_id: str, start: datetime, end: datetime) -> list[DowntimeEvent]
    # ... etc

# Implementations
class SupabaseDataSource(DataSource):
    # Current implementation - queries Supabase tables

class MSSQLDataSource(DataSource):
    # Future implementation - queries source MSSQL (read-only)

class CompositeDataSource(DataSource):
    # Routes queries to appropriate source based on data type/freshness
```

### 5.3 Tool Registration Pattern

Tools SHALL be self-describing for automatic registration:

```python
class ManufacturingTool(BaseTool):
    name: str
    description: str  # Used by agent for tool selection
    args_schema: Type[BaseModel]  # Pydantic model for input validation
    citations_required: bool = True

    async def _arun(self, **kwargs) -> ToolResult:
        # Returns structured data + citations
        pass
```

### 5.4 Supabase Tables Used

| Tool | Primary Tables | Join Tables |
|------|---------------|-------------|
| Asset Lookup | `assets`, `live_snapshots` | `cost_centers`, `daily_summaries` |
| OEE Query | `daily_summaries` | `assets`, `shift_targets` |
| Downtime Analysis | `daily_summaries` | `assets` |
| Production Status | `live_snapshots` | `assets`, `shift_targets` |
| Safety Events | `safety_events` | `assets` |
| Financial Impact | `daily_summaries` | `cost_centers` |
| Trend Analysis | `daily_summaries` | `assets` |
| Memory Recall | `memories` | - |
| Action List | (Action Engine output) | Multiple |

---

## 6. User Experience

### 6.1 Example Interactions

**Asset Lookup:**
```
User: "Tell me about Grinder 5"

Agent: Here's the current status for Grinder 5:

**Asset Details**
- Area: Grinding
- Cost Center: GR-001
- Status: Running

**Current Shift (as of 2:45 PM)**
- Output: 847 units (Target: 900)
- Variance: -53 units (-5.9%)

**Last 7 Days Performance**
- Avg OEE: 78.3%
- Total Downtime: 4.2 hours
- Top Issue: Material Jam (38% of downtime)

[Citations: live_snapshots @ 14:45:00, daily_summaries 01/02-01/08]

Would you like me to dig into the downtime details or show the trend over time?
```

**Honest "I Don't Know":**
```
User: "What was the OEE for Line 12 last month?"

Agent: I don't have data for "Line 12" in the system.

The assets I can see in the Grinding area are:
- Grinder 1, Grinder 2, Grinder 3, Grinder 5

Did you mean one of these? Or is Line 12 in a different area?
```

**Multi-Tool Query:**
```
User: "What should I focus on today?"

Agent: Based on this morning's data, here are your top priorities:

🔴 **SAFETY FIRST**
1. **Packaging Line 2** - Safety stop triggered at 6:42 AM
   - Status: Under investigation
   - Action: Confirm lockout/tagout complete before restart
   [Citation: safety_events @ 06:42:00]

⚠️ **OEE GAPS**
2. **Grinder 5** - OEE at 62% (Target: 85%)
   - Root cause: 47 minutes downtime from "Blade Change"
   - Impact: $2,340 estimated loss
   - Action: Review blade change SOP - frequency seems high
   [Citations: daily_summaries 01/08, cost_centers GR-001]

3. **CAMA 800-1** - Running 12% below target
   - Pattern: Slowing after lunch break (3 days in a row)
   - Action: Check operator staffing during shift change
   [Citation: daily_summaries 01/06-01/08]

Should I dive deeper into any of these?
```

### 6.2 Response Format Standards

All tool responses SHALL follow this structure:
1. **Direct answer** to the question asked
2. **Supporting data** in scannable format (bullets, tables)
3. **Citations** with source and timestamp
4. **Suggested follow-ups** (optional, context-dependent)

---

## 7. Epic Definitions

### Epic 5: Agent Foundation & Core Tools

**Goal:** Plant Managers can ask natural language questions about assets, OEE, downtime, and production status and receive fast, reliable, cited responses.

**Dependencies:** Epic 4 (AI Chat & Memory) - completed

**User Value:** The most common plant manager questions ("How is Grinder 5 doing?", "What's our OEE?", "Why were we down?") work reliably with consistent, cited responses.

**Stories:**

| Story | Title | Description |
|-------|-------|-------------|
| 5.1 | Agent Framework & Tool Registry | LangChain agent setup with tool registration pattern |
| 5.2 | Data Access Abstraction Layer | Supabase adapter with interface for future MSSQL |
| 5.3 | Asset Lookup Tool | Asset metadata, status, recent performance |
| 5.4 | OEE Query Tool | OEE calculation with component breakdown |
| 5.5 | Downtime Analysis Tool | Downtime reasons, Pareto, patterns |
| 5.6 | Production Status Tool | Real-time output vs target |
| 5.7 | Agent Chat Integration | Wire agent into existing chat UI |
| 5.8 | Tool Response Caching | Tiered caching with TTL and invalidation |

**Acceptance Criteria:**
- [ ] Agent framework operational with tool selection
- [ ] All 4 core tools (Asset, OEE, Downtime, Production) implemented and tested
- [ ] Agent correctly selects tools based on user intent (>90% accuracy)
- [ ] All responses include citations with source and timestamp
- [ ] Response time < 2 seconds (p95)
- [ ] Agent gracefully handles unknown queries ("I don't have data for...")
- [ ] Data access layer abstraction in place for future MSSQL
- [ ] Tool response caching implemented with appropriate TTLs
- [ ] Chat UI connected to new agent

---

### Epic 6: Safety & Financial Intelligence Tools

**Goal:** Plant Managers can query safety incidents and understand the financial impact of operational issues.

**Dependencies:** Epic 5 (Agent Foundation & Core Tools)

**User Value:** Safety-first visibility ("Any safety incidents?") and financial context ("What's this costing us?") are critical for prioritization decisions.

**Stories:**

| Story | Title | Description |
|-------|-------|-------------|
| 6.1 | Safety Events Tool | Safety incident queries with severity and resolution status |
| 6.2 | Financial Impact Tool | Cost of downtime/waste calculation by asset or area |
| 6.3 | Cost of Loss Tool | Ranked financial losses with root causes |
| 6.4 | Trend Analysis Tool | Time-series analysis, anomaly detection, baseline comparison |

**Acceptance Criteria:**
- [ ] Safety Events tool returns incidents with severity, status, affected assets
- [ ] Financial Impact tool calculates dollar losses using cost_centers data
- [ ] Cost of Loss tool ranks issues by financial impact
- [ ] Trend Analysis tool shows performance over 7-90 day windows
- [ ] All tools include citations
- [ ] Response time < 2 seconds (p95)

---

### Epic 7: Proactive Agent Capabilities

**Goal:** The AI Agent proactively helps plant managers by recalling context, comparing assets, and suggesting actions.

**Dependencies:** Epic 6 (Safety & Financial Intelligence Tools)

**User Value:** The agent becomes a true assistant - remembering past conversations, helping compare options, and proactively suggesting what to focus on.

**Stories:**

| Story | Title | Description |
|-------|-------|-------------|
| 7.1 | Memory Recall Tool | Retrieve relevant conversation history by topic or asset |
| 7.2 | Comparative Analysis Tool | Side-by-side asset/area comparison with variance highlighting |
| 7.3 | Action List Tool | Get prioritized daily actions from Action Engine |
| 7.4 | Alert Check Tool | Query active warnings and issues with severity filter |
| 7.5 | Recommendation Engine | Pattern-based suggestions with supporting evidence |

**Acceptance Criteria:**
- [ ] Memory Recall retrieves relevant past conversations via Mem0
- [ ] Comparative Analysis shows side-by-side metrics for 2+ assets
- [ ] Action List tool surfaces prioritized daily actions with evidence
- [ ] Alert Check returns active warnings with recommended responses
- [ ] Recommendation Engine suggests improvements based on patterns
- [ ] All tools include citations where applicable
- [ ] Response time < 3 seconds (p95) for intelligence tools

---

### Epic Summary

| Epic | Title | Stories | Focus |
|------|-------|---------|-------|
| 5 | Agent Foundation & Core Tools | 8 | Framework + most-used tools |
| 6 | Safety & Financial Intelligence | 4 | Safety visibility + financial context |
| 7 | Proactive Agent Capabilities | 5 | Memory, comparison, recommendations |

**Total:** 17 stories across 3 epics

---

## 8. Decisions & Resolved Questions

| # | Question | Decision |
|---|----------|----------|
| 1 | Should tools support batch queries (e.g., "OEE for all grinders")? | **Not required** - Single asset/area queries sufficient for MVP |
| 2 | Rate limiting per user for expensive tools? | **Not required** - Can be added later if needed |
| 3 | Should recommendations require human approval before display? | **No** - Display directly to user |
| 4 | Cache strategy for tool results? | **Yes, implement caching** - See NFR7 below |

---

## 8.1 NFR7: Tool Response Caching

Tool responses SHALL be cached to improve performance and reduce database load:

### Cache Tiers

| Data Type | TTL | Invalidation |
|-----------|-----|--------------|
| **Live Data** (Production Status, Alert Check) | 60 seconds | Time-based only |
| **Daily Data** (OEE, Downtime, Financial) | 15 minutes | Time-based; invalidate on new pipeline run |
| **Static Data** (Asset Lookup metadata) | 1 hour | Time-based; invalidate on asset table change |
| **Memory Recall** | No cache | Always fetch fresh |
| **Action List** | 5 minutes | Time-based; invalidate on safety event |

### Cache Key Strategy

Cache keys SHALL include:
- Tool name
- User ID (for personalized results where applicable)
- Query parameters (asset_id, time_range, filters)
- Data freshness timestamp

```
Example: oee_query:user_123:asset_grinder5:2026-01-09:shift_1
```

### Cache Implementation

- Use in-memory cache (e.g., `cachetools` or Redis if scaling required)
- Cache at the tool response level, not database query level
- Include `cached_at` timestamp in response metadata
- Allow cache bypass with `force_refresh=true` parameter for debugging

---

## 9. Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-01-09 | 1.1-draft | Initial addendum for AI Agent Tools | Caleb + PM Agent |
