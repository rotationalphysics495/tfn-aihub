---
stepsCompleted: ["step-01-validate-prerequisites", "step-02-design-epics", "step-03-create-stories"]
inputDocuments:
  - "_bmad/bmm/data/prd.md"
  - "_bmad-output/planning-artifacts/prd-addendum-ai-agent-tools.md"
  - "_bmad/bmm/data/architecture.md"
  - "_bmad/bmm/data/ux-design.md"
epic: 5
status: "ready"
---

# Epic 5: Agent Foundation & Core Tools

## Overview

**Goal:** Plant Managers can ask natural language questions about assets, OEE, downtime, and production status and receive fast, reliable, cited responses.

**Dependencies:** Epic 4 (AI Chat & Memory) - completed

**User Value:** The most common plant manager questions ("How is Grinder 5 doing?", "What's our OEE?", "Why were we down?") work reliably with consistent, cited responses.

## Requirements Coverage

| Requirement | Coverage |
|-------------|----------|
| FR7.1 (Core Operations Tools) | Full |
| NFR4 (Agent Honesty) | Full |
| NFR5 (Tool Extensibility) | Full |
| NFR6 (Response Structure) | Full |
| NFR7 (Tool Response Caching) | Full |

## Stories

---

### Story 5.1: Agent Framework & Tool Registry

**As a** developer,
**I want** a LangChain agent framework with automatic tool registration,
**So that** new tools can be added without modifying the agent core.

**Acceptance Criteria:**

**Given** the API server is running
**When** a new tool class is created following the ManufacturingTool pattern
**Then** the tool is automatically registered with the agent
**And** the tool's description is used for intent matching

**Given** a user sends a message to the chat endpoint
**When** the agent processes the message
**Then** the agent selects the appropriate tool based on intent
**And** returns a structured response with citations

**Given** no tool matches the user's intent
**When** the agent processes the message
**Then** the agent responds honestly that it cannot help with that request
**And** suggests what types of questions it can answer

**Technical Notes:**
- Use LangChain AgentExecutor with OpenAI Functions agent
- Implement ManufacturingTool base class with citations_required flag
- Create tool registry that auto-discovers tools on startup
- Configure via environment: LLM_PROVIDER, LLM_MODEL, AGENT_TEMPERATURE

**Files to Create/Modify:**
- `apps/api/app/services/agent/base.py` - ManufacturingTool base class
- `apps/api/app/services/agent/registry.py` - Tool auto-discovery
- `apps/api/app/services/agent/executor.py` - AgentExecutor wrapper
- `apps/api/app/api/agent.py` - New agent chat endpoint

---

### Story 5.2: Data Access Abstraction Layer

**As a** developer,
**I want** a data access abstraction layer that tools use instead of direct database queries,
**So that** we can add MSSQL as a data source in the future without modifying tools.

**Acceptance Criteria:**

**Given** a tool needs to fetch asset data
**When** the tool calls `data_source.get_asset(asset_id)`
**Then** the data is returned from the configured data source (Supabase)
**And** the tool does not need to know which database was queried

**Given** a new data source (MSSQL) is implemented
**When** the CompositeDataSource is configured to use it
**Then** existing tools continue to work without modification
**And** queries are routed to the appropriate source

**Given** any data source method is called
**When** data is returned
**Then** the response includes source metadata (table, timestamp)
**And** this metadata is available for citation generation

**Technical Notes:**
- Define DataSource Protocol with async methods
- Implement SupabaseDataSource as primary adapter
- Create CompositeDataSource for future multi-source routing
- All methods return DataResult with data + source metadata

**Files to Create/Modify:**
- `apps/api/app/services/agent/data_source/protocol.py` - DataSource Protocol
- `apps/api/app/services/agent/data_source/supabase.py` - Supabase adapter
- `apps/api/app/services/agent/data_source/composite.py` - Router (future-ready)
- `apps/api/app/services/agent/data_source/__init__.py` - Factory function

---

### Story 5.3: Asset Lookup Tool

**As a** Plant Manager,
**I want** to ask about any asset by name and get its current status and recent performance,
**So that** I can quickly understand how a specific machine is doing.

**Acceptance Criteria:**

**Given** a user asks "Tell me about Grinder 5"
**When** the Asset Lookup tool is invoked
**Then** the response includes:
  - Asset metadata (name, area, cost center)
  - Current status (running/down/idle)
  - Current shift output vs target
  - 7-day average OEE
  - Top downtime reason
**And** all data points include citations

**Given** a user asks about an asset that doesn't exist
**When** the Asset Lookup tool is invoked
**Then** the response states "I don't have data for [asset name]"
**And** lists similar assets the user might have meant

**Given** the asset exists but has no recent data
**When** the Asset Lookup tool is invoked
**Then** the response shows available metadata
**And** indicates "No production data available for the last 7 days"

**Technical Notes:**
- Query: assets, live_snapshots, daily_summaries (last 7 days)
- Fuzzy match on asset name for suggestions
- Cache TTL: 1 hour for metadata, 60 seconds for live status

**Files to Create/Modify:**
- `apps/api/app/services/agent/tools/asset_lookup.py` - Tool implementation
- `apps/api/app/models/agent.py` - AssetLookupInput/Output schemas

---

### Story 5.4: OEE Query Tool

**As a** Plant Manager,
**I want** to ask about OEE for any asset, area, or plant-wide with a breakdown,
**So that** I can understand where we're losing efficiency.

**Acceptance Criteria:**

**Given** a user asks "What's the OEE for Grinder 5?"
**When** the OEE Query tool is invoked
**Then** the response includes:
  - Overall OEE percentage
  - Availability component
  - Performance component
  - Quality component
  - Comparison to target (if shift_targets exists)
**And** all values include citations with date range

**Given** a user asks "What's the OEE for the Grinding area?"
**When** the OEE Query tool is invoked
**Then** the response includes aggregated OEE across all assets in that area
**And** lists individual asset OEE values

**Given** a user asks about OEE for a time range (e.g., "last week")
**When** the OEE Query tool is invoked
**Then** the response covers the specified date range
**And** citations reflect the actual dates queried

**Given** no OEE data exists for the requested scope/time
**When** the OEE Query tool is invoked
**Then** the response states "No OEE data available for [scope] in [time range]"

**Technical Notes:**
- Query: daily_summaries, assets, shift_targets
- Support scopes: asset, area, plant-wide
- Default time range: yesterday (T-1)
- Cache TTL: 15 minutes

**Files to Create/Modify:**
- `apps/api/app/services/agent/tools/oee_query.py` - Tool implementation
- `apps/api/app/models/agent.py` - OEEQueryInput/Output schemas

---

### Story 5.5: Downtime Analysis Tool

**As a** Plant Manager,
**I want** to ask about downtime reasons and patterns for any asset or area,
**So that** I can identify and address the root causes of lost production time.

**Acceptance Criteria:**

**Given** a user asks "Why was Grinder 5 down yesterday?"
**When** the Downtime Analysis tool is invoked
**Then** the response includes:
  - Total downtime minutes
  - Downtime reasons ranked by duration (Pareto)
  - Percentage of total downtime per reason
  - Specific timestamps if available
**And** all data points include citations

**Given** a user asks "What are the top downtime reasons for the Grinding area this week?"
**When** the Downtime Analysis tool is invoked
**Then** the response aggregates across all assets in the area
**And** shows which assets contributed most to each reason

**Given** an asset had no downtime in the requested period
**When** the Downtime Analysis tool is invoked
**Then** the response states "[Asset] had no recorded downtime in [time range]"
**And** shows total uptime percentage

**Technical Notes:**
- Query: daily_summaries (downtime fields), assets
- Parse downtime_reasons JSON for Pareto analysis
- Support scopes: asset, area
- Default time range: yesterday (T-1)
- Cache TTL: 15 minutes

**Files to Create/Modify:**
- `apps/api/app/services/agent/tools/downtime_analysis.py` - Tool implementation
- `apps/api/app/models/agent.py` - DowntimeAnalysisInput/Output schemas

---

### Story 5.6: Production Status Tool

**As a** Plant Manager,
**I want** to ask about real-time production status across assets,
**So that** I can see at a glance how we're tracking against targets right now.

**Acceptance Criteria:**

**Given** a user asks "How are we doing today?"
**When** the Production Status tool is invoked
**Then** the response includes for each asset:
  - Current output vs target
  - Variance (units and percentage)
  - Status indicator (ahead/on-track/behind)
  - Data freshness timestamp
**And** assets are sorted by variance (worst first)

**Given** a user asks "How is the Grinding area doing?"
**When** the Production Status tool is invoked
**Then** the response filters to assets in that area
**And** shows area-level totals

**Given** a user asks about production status but live_snapshots is stale (>30 min old)
**When** the Production Status tool is invoked
**Then** the response includes a warning: "Data is from [timestamp], may not reflect current status"

**Technical Notes:**
- Query: live_snapshots, assets, shift_targets
- Check data freshness, warn if >30 minutes old
- Cache TTL: 60 seconds (live data)

**Files to Create/Modify:**
- `apps/api/app/services/agent/tools/production_status.py` - Tool implementation
- `apps/api/app/models/agent.py` - ProductionStatusInput/Output schemas

---

### Story 5.7: Agent Chat Integration

**As a** Plant Manager,
**I want** to use the existing chat sidebar to interact with the new AI agent,
**So that** I don't need to learn a new interface.

**Acceptance Criteria:**

**Given** a user opens the chat sidebar
**When** they send a message
**Then** the message is routed to the new agent endpoint
**And** the response is displayed in the existing chat UI

**Given** the agent returns a response with citations
**When** the response is displayed
**Then** citations are rendered as clickable links
**And** clicking a citation shows source details

**Given** the agent returns suggested follow-up questions
**When** the response is displayed
**Then** follow-ups appear as clickable chips below the response
**And** clicking a chip sends that question

**Given** the agent is processing a request
**When** the user is waiting
**Then** a loading indicator is shown
**And** the indicator matches the existing chat UI pattern

**Technical Notes:**
- Update chat API route to call new agent endpoint
- Modify ChatMessage component to render citations
- Add follow-up question chips component
- Preserve existing Mem0 memory storage

**Files to Create/Modify:**
- `apps/web/src/components/chat/ChatMessage.tsx` - Citation rendering
- `apps/web/src/components/chat/FollowUpChips.tsx` - New component
- `apps/api/app/api/chat.py` - Route to new agent

---

### Story 5.8: Tool Response Caching

**As a** developer,
**I want** tool responses to be cached with appropriate TTLs,
**So that** repeated queries are fast and database load is reduced.

**Acceptance Criteria:**

**Given** a user asks the same question twice within the cache TTL
**When** the second request is processed
**Then** the cached response is returned
**And** response includes `cached_at` timestamp in metadata

**Given** different cache tiers are configured:
| Data Type | TTL |
|-----------|-----|
| Live Data | 60 seconds |
| Daily Data | 15 minutes |
| Static Data | 1 hour |
**When** tools return responses
**Then** they are cached according to their tier

**Given** a safety event occurs
**When** the Action List cache is checked
**Then** the cache is invalidated
**And** the next request fetches fresh data

**Given** a developer needs to debug
**When** they call an endpoint with `force_refresh=true`
**Then** the cache is bypassed
**And** fresh data is fetched and cached

**Technical Notes:**
- Use `cachetools` TTLCache for in-memory caching
- Cache key format: `{tool_name}:{user_id}:{params_hash}`
- Implement cache decorator for tools
- Add cache stats endpoint for monitoring

**Files to Create/Modify:**
- `apps/api/app/services/agent/cache.py` - Caching implementation
- `apps/api/app/services/agent/tools/base.py` - Cache decorator
- `apps/api/app/api/agent.py` - force_refresh parameter

---

## Epic Acceptance Criteria

- [ ] Agent framework operational with tool selection
- [ ] All 4 core tools (Asset, OEE, Downtime, Production) implemented and tested
- [ ] Agent correctly selects tools based on user intent (>90% accuracy)
- [ ] All responses include citations with source and timestamp
- [ ] Response time < 2 seconds (p95)
- [ ] Agent gracefully handles unknown queries ("I don't have data for...")
- [ ] Data access layer abstraction in place for future MSSQL
- [ ] Tool response caching implemented with appropriate TTLs
- [ ] Chat UI connected to new agent
