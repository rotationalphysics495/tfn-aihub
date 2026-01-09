---
stepsCompleted: ["step-01-validate-prerequisites", "step-02-design-epics", "step-03-create-stories"]
inputDocuments:
  - "_bmad/bmm/data/prd.md"
  - "_bmad-output/planning-artifacts/prd-addendum-ai-agent-tools.md"
  - "_bmad/bmm/data/architecture.md"
  - "_bmad/bmm/data/ux-design.md"
epic: 7
status: "ready"
---

# Epic 7: Proactive Agent Capabilities

## Overview

**Goal:** The AI Agent proactively helps plant managers by recalling context, comparing assets, and suggesting actions.

**Dependencies:** Epic 6 (Safety & Financial Intelligence Tools)

**User Value:** The agent becomes a true assistant - remembering past conversations, helping compare options, and proactively suggesting what to focus on.

## Requirements Coverage

| Requirement | Coverage |
|-------------|----------|
| FR7.3 (Memory Recall, Comparative Analysis) | Full |
| FR7.4 (Proactive Action Tools) | Full |
| NFR4 (Agent Honesty) | Continued |
| NFR6 (Response Structure) | Continued |

## Stories

---

### Story 7.1: Memory Recall Tool

**As a** Plant Manager,
**I want** the agent to remember and recall our past conversations about specific assets or topics,
**So that** I don't have to repeat context and can build on previous discussions.

**Acceptance Criteria:**

**Given** a user asks "What did we discuss about Grinder 5?"
**When** the Memory Recall tool is invoked
**Then** the response includes:
  - Summary of past conversations mentioning "Grinder 5"
  - Key decisions or conclusions reached
  - Dates of relevant conversations
  - Links to related topics discussed
**And** results are sorted by relevance, then recency

**Given** a user asks "What issues have we talked about this week?"
**When** the Memory Recall tool is invoked
**Then** the response summarizes topics by category
**And** highlights unresolved items

**Given** no relevant memories exist
**When** the Memory Recall tool is invoked
**Then** the response states "I don't have any previous conversations about [topic]"
**And** offers to help with a fresh inquiry

**Given** memories exist but are old (>30 days)
**When** the Memory Recall tool is invoked
**Then** the response includes a note: "This was discussed [X] days ago - things may have changed"

**Technical Notes:**
- Query: Mem0 vector search with semantic similarity
- Filter by user_id and optional asset_id
- Relevance threshold: 0.7 similarity score
- Return top 5 most relevant memories
- No cache (always fetch fresh for memory)

**Files to Create/Modify:**
- `apps/api/app/services/agent/tools/memory_recall.py` - Tool implementation
- `apps/api/app/models/agent.py` - MemoryRecallInput/Output schemas

---

### Story 7.2: Comparative Analysis Tool

**As a** Plant Manager,
**I want** to compare two or more assets or areas side-by-side,
**So that** I can identify best performers and understand differences.

**Acceptance Criteria:**

**Given** a user asks "Compare Grinder 5 vs Grinder 3"
**When** the Comparative Analysis tool is invoked
**Then** the response includes:
  - Side-by-side metrics table (OEE, output, downtime, waste)
  - Variance highlighting (better/worse indicators)
  - Summary of key differences
  - Winner/recommendation if one is clearly better
**And** all metrics include citations

**Given** a user asks "Compare all grinders this week"
**When** the Comparative Analysis tool is invoked
**Then** the response compares all assets matching "grinder"
**And** ranks them by overall performance

**Given** a user asks to compare areas (e.g., "Compare Grinding vs Packaging")
**When** the Comparative Analysis tool is invoked
**Then** the response aggregates metrics at the area level
**And** shows area-level totals and averages

**Given** assets have incompatible metrics (different units or targets)
**When** the Comparative Analysis tool is invoked
**Then** the response includes a note about comparability
**And** uses percentage-based comparisons where appropriate

**Technical Notes:**
- Query: daily_summaries, assets, shift_targets
- Support 2-10 assets/areas in a single comparison
- Normalize metrics to percentages for fair comparison
- Default time range: last 7 days
- Cache TTL: 15 minutes

**Files to Create/Modify:**
- `apps/api/app/services/agent/tools/comparative_analysis.py` - Tool implementation
- `apps/api/app/models/agent.py` - ComparativeAnalysisInput/Output schemas

---

### Story 7.3: Action List Tool

**As a** Plant Manager,
**I want** to ask "What should I focus on today?" and get a prioritized action list,
**So that** I can start my day with clear priorities based on data.

**Acceptance Criteria:**

**Given** a user asks "What should I focus on today?"
**When** the Action List tool is invoked
**Then** the response includes:
  - Prioritized list of action items (max 5)
  - For each action: priority rank, asset, issue, recommended action
  - Supporting evidence for each item
  - Estimated impact (financial or operational)
**And** items are sorted: Safety first, then Financial Impact, then OEE gaps

**Given** a user asks for actions for a specific area
**When** the Action List tool is invoked
**Then** the response filters to that area
**And** maintains the same priority logic

**Given** no significant issues exist
**When** the Action List tool is invoked
**Then** the response states "No critical issues identified - operations look healthy"
**And** suggests proactive improvements if patterns indicate opportunities

**Given** the Action Engine has already run for today
**When** the Action List tool is invoked
**Then** results from the existing Action Engine are returned
**And** response indicates data freshness

**Technical Notes:**
- Leverage existing Action Engine logic from Epic 3
- Query: daily_summaries, safety_events, cost_centers
- Priority logic: Safety > 0 → highest priority
- OEE < Target → medium priority
- Financial Loss > Threshold → sorted by $ impact
- Cache TTL: 5 minutes (or invalidate on safety event)

**Files to Create/Modify:**
- `apps/api/app/services/agent/tools/action_list.py` - Tool implementation
- `apps/api/app/models/agent.py` - ActionListInput/Output schemas

---

### Story 7.4: Alert Check Tool

**As a** Plant Manager,
**I want** to quickly check if there are any active alerts or warnings,
**So that** I can respond to emerging issues before they escalate.

**Acceptance Criteria:**

**Given** a user asks "Are there any alerts?"
**When** the Alert Check tool is invoked
**Then** the response includes:
  - Count of active alerts by severity
  - For each alert: type, asset, description, recommended response
  - Time since alert was triggered
  - Escalation status (if applicable)
**And** alerts are sorted by severity (critical first)

**Given** a user asks with a severity filter (e.g., "Any critical alerts?")
**When** the Alert Check tool is invoked
**Then** only alerts matching that severity are returned

**Given** no active alerts exist
**When** the Alert Check tool is invoked
**Then** the response states "No active alerts - all systems normal"
**And** shows time since last alert (if any)

**Given** an alert has been active for >1 hour without resolution
**When** the Alert Check tool is invoked
**Then** the alert is flagged as "Requires Attention"
**And** escalation is suggested

**Technical Notes:**
- Query: safety_events (unresolved), live_snapshots (anomalies)
- Alert sources: safety events, production variance >20%, equipment status changes
- Severity levels: critical, warning, info
- Cache TTL: 60 seconds (alerts should be fresh)

**Files to Create/Modify:**
- `apps/api/app/services/agent/tools/alert_check.py` - Tool implementation
- `apps/api/app/models/agent.py` - AlertCheckInput/Output schemas

---

### Story 7.5: Recommendation Engine

**As a** Plant Manager,
**I want** the agent to suggest improvements based on patterns it detects,
**So that** I can be proactive about optimization, not just reactive to problems.

**Acceptance Criteria:**

**Given** a user asks "How can we improve OEE for Grinder 5?"
**When** the Recommendation Engine is invoked
**Then** the response includes:
  - 2-3 specific recommendations
  - For each: what to do, expected impact, supporting evidence
  - Data patterns that led to the recommendation
  - Similar situations where this worked (from memory, if available)
**And** recommendations are actionable and specific

**Given** a user asks "What should we focus on improving?"
**When** the Recommendation Engine is invoked
**Then** the response analyzes plant-wide patterns
**And** identifies the highest-impact improvement opportunities
**And** ranks by potential ROI

**Given** a user asks about a specific focus area (e.g., "How do we reduce waste?")
**When** the Recommendation Engine is invoked
**Then** recommendations focus on that area
**And** cite relevant data supporting waste reduction strategies

**Given** insufficient data exists to make recommendations
**When** the Recommendation Engine is invoked
**Then** the response states "I need more data to make specific recommendations"
**And** suggests what data would help

**Technical Notes:**
- Query: daily_summaries (patterns), cost_centers, memories (past solutions)
- Pattern detection: recurring downtime reasons, time-of-day patterns, cross-asset correlations
- Recommendation confidence: high (>80% pattern match), medium (60-80%), low (<60%)
- Only show high/medium confidence recommendations
- Cache TTL: 15 minutes

**Files to Create/Modify:**
- `apps/api/app/services/agent/tools/recommendation_engine.py` - Tool implementation
- `apps/api/app/models/agent.py` - RecommendationInput/Output schemas

---

## Epic Acceptance Criteria

- [ ] Memory Recall retrieves relevant past conversations via Mem0
- [ ] Comparative Analysis shows side-by-side metrics for 2+ assets
- [ ] Action List tool surfaces prioritized daily actions with evidence
- [ ] Alert Check returns active warnings with recommended responses
- [ ] Recommendation Engine suggests improvements based on patterns
- [ ] All tools include citations where applicable
- [ ] Response time < 3 seconds (p95) for intelligence tools
- [ ] Recommendations are actionable and data-backed
- [ ] Memory recall respects user context and relevance thresholds
