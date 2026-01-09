---
stepsCompleted: ["step-01-validate-prerequisites", "step-02-design-epics", "step-03-create-stories"]
inputDocuments:
  - "_bmad/bmm/data/prd.md"
  - "_bmad-output/planning-artifacts/prd-addendum-ai-agent-tools.md"
  - "_bmad/bmm/data/architecture.md"
  - "_bmad/bmm/data/ux-design.md"
epic: 6
status: "ready"
---

# Epic 6: Safety & Financial Intelligence Tools

## Overview

**Goal:** Plant Managers can query safety incidents and understand the financial impact of operational issues.

**Dependencies:** Epic 5 (Agent Foundation & Core Tools)

**User Value:** Safety-first visibility ("Any safety incidents?") and financial context ("What's this costing us?") are critical for prioritization decisions.

## Requirements Coverage

| Requirement | Coverage |
|-------------|----------|
| FR7.2 (Safety & Financial Tools) | Full |
| FR7.3 (Trend Analysis) | Partial |
| NFR4 (Agent Honesty) | Continued |
| NFR6 (Response Structure) | Continued |

## Stories

---

### Story 6.1: Safety Events Tool

**As a** Plant Manager,
**I want** to ask about safety incidents and get immediate, detailed responses,
**So that** I can ensure safety issues are being addressed and track resolution status.

**Acceptance Criteria:**

**Given** a user asks "Any safety incidents today?"
**When** the Safety Events tool is invoked
**Then** the response includes:
  - Count of safety events in the time range
  - For each event: timestamp, asset, severity, description
  - Resolution status (resolved/under investigation/open)
  - Affected area
**And** events are sorted by severity (critical first), then recency

**Given** a user asks "Show me safety incidents for the Packaging area this week"
**When** the Safety Events tool is invoked
**Then** the response filters to events in that area
**And** shows summary statistics (total events, resolved vs open)

**Given** a user asks about safety with a severity filter (e.g., "critical safety incidents")
**When** the Safety Events tool is invoked
**Then** only events matching that severity are returned

**Given** no safety incidents exist in the requested scope/time
**When** the Safety Events tool is invoked
**Then** the response states "No safety incidents recorded for [scope] in [time range]"
**And** this is presented as positive news

**Technical Notes:**
- Query: safety_events, assets
- Severity levels: critical, high, medium, low
- Resolution statuses: resolved, under_investigation, open
- Default time range: today
- Cache TTL: 60 seconds (safety data should be fresh)

**Files to Create/Modify:**
- `apps/api/app/services/agent/tools/safety_events.py` - Tool implementation
- `apps/api/app/models/agent.py` - SafetyEventsInput/Output schemas

---

### Story 6.2: Financial Impact Tool

**As a** Plant Manager,
**I want** to understand the financial cost of downtime and waste for any asset or area,
**So that** I can prioritize issues by business impact, not just operational metrics.

**Acceptance Criteria:**

**Given** a user asks "What's the cost of downtime for Grinder 5 yesterday?"
**When** the Financial Impact tool is invoked
**Then** the response includes:
  - Total financial loss (dollars)
  - Breakdown by category (downtime cost, waste cost)
  - Hourly rate used for calculation (from cost_centers)
  - Comparison to average loss for this asset
**And** all calculations include citations with formulas

**Given** a user asks "What's the financial impact for the Grinding area this week?"
**When** the Financial Impact tool is invoked
**Then** the response aggregates across all assets in the area
**And** shows per-asset breakdown
**And** identifies the highest-cost asset

**Given** cost_centers data is missing for an asset
**When** the Financial Impact tool is invoked
**Then** the response indicates "Unable to calculate financial impact for [asset] - no cost center data"
**And** returns available non-financial metrics

**Technical Notes:**
- Query: daily_summaries, cost_centers, assets
- Calculation: downtime_minutes * standard_hourly_rate / 60
- Waste cost: waste_count * cost_per_unit
- Default time range: yesterday (T-1)
- Cache TTL: 15 minutes

**Files to Create/Modify:**
- `apps/api/app/services/agent/tools/financial_impact.py` - Tool implementation
- `apps/api/app/models/agent.py` - FinancialImpactInput/Output schemas

---

### Story 6.3: Cost of Loss Tool

**As a** Plant Manager,
**I want** to see a ranked list of what's costing us the most money,
**So that** I can focus improvement efforts on the highest-impact issues.

**Acceptance Criteria:**

**Given** a user asks "What are we losing money on?"
**When** the Cost of Loss tool is invoked
**Then** the response includes:
  - Ranked list of losses (highest first)
  - For each loss: asset, category, amount, root cause
  - Total loss across all items
  - Percentage of total for each item
**And** losses are grouped by category (downtime, waste, quality)

**Given** a user asks "What are the top 3 cost drivers this week?"
**When** the Cost of Loss tool is invoked
**Then** the response limits to top 3 items
**And** includes trend vs previous week (up/down/stable)

**Given** a user asks about cost of loss for a specific area
**When** the Cost of Loss tool is invoked
**Then** the response filters to that area
**And** compares to plant-wide average

**Technical Notes:**
- Query: daily_summaries, cost_centers, assets
- Combine and rank all loss types
- Include root cause from downtime_reasons where available
- Default time range: yesterday (T-1)
- Cache TTL: 15 minutes

**Files to Create/Modify:**
- `apps/api/app/services/agent/tools/cost_of_loss.py` - Tool implementation
- `apps/api/app/models/agent.py` - CostOfLossInput/Output schemas

---

### Story 6.4: Trend Analysis Tool

**As a** Plant Manager,
**I want** to see how an asset's performance has changed over time,
**So that** I can identify patterns, anomalies, and the impact of changes.

**Acceptance Criteria:**

**Given** a user asks "How has Grinder 5 performed over the last 30 days?"
**When** the Trend Analysis tool is invoked
**Then** the response includes:
  - Trend direction (improving/declining/stable)
  - Average metric value over the period
  - Min and max values with dates
  - Notable anomalies (values >2 std dev from mean)
  - Comparison to baseline (first week of period)
**And** data supports the trend conclusion

**Given** a user asks about a specific metric (e.g., "OEE trend for Grinding area")
**When** the Trend Analysis tool is invoked
**Then** the response focuses on that metric
**And** shows the metric-specific trend

**Given** a user asks for trend over a custom time range (e.g., "last 90 days")
**When** the Trend Analysis tool is invoked
**Then** the response covers the specified range
**And** adjusts granularity appropriately (daily vs weekly)

**Given** insufficient data exists for trend analysis (<7 days)
**When** the Trend Analysis tool is invoked
**Then** the response states "Not enough data for trend analysis - need at least 7 days"
**And** shows available point-in-time data instead

**Technical Notes:**
- Query: daily_summaries (time series), assets
- Support time ranges: 7, 14, 30, 60, 90 days
- Metrics: OEE, output, downtime, waste
- Calculate: mean, std dev, trend slope
- Anomaly threshold: 2 standard deviations
- Cache TTL: 15 minutes

**Files to Create/Modify:**
- `apps/api/app/services/agent/tools/trend_analysis.py` - Tool implementation
- `apps/api/app/models/agent.py` - TrendAnalysisInput/Output schemas

---

## Epic Acceptance Criteria

- [ ] Safety Events tool returns incidents with severity, status, affected assets
- [ ] Financial Impact tool calculates dollar losses using cost_centers data
- [ ] Cost of Loss tool ranks issues by financial impact
- [ ] Trend Analysis tool shows performance over 7-90 day windows
- [ ] All tools include citations with source and timestamp
- [ ] Response time < 2 seconds (p95)
- [ ] Safety data is always fresh (60s cache max)
- [ ] Financial calculations are transparent (show formulas)
