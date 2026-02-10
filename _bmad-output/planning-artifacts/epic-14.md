---
stepsCompleted: ["step-01-validate-prerequisites", "step-02-design-epics", "step-03-create-stories"]
inputDocuments:
  - "docs/improvements.md"
  - "docs/architecture-api.md"
  - "docs/architecture-web.md"
  - "docs/data-models.md"
epic: 14
status: "ready"
---

# Epic 14: Trend Intelligence & Downtime Pareto

## Overview

**Goal:** Plant managers can see historical context on every action item — is this new or recurring? — and understand *why* downtime happened with reason code breakdowns, enabling targeted investigations instead of generic ones.

**Dependencies:** None (queries existing `daily_summaries` for trends; introduces new `downtime_events` table for Pareto)

**User Value:** Transforms the report from "here's what happened" to "here's the pattern." Repeat offender badges and downtime Pareto turn vague "go look at Grinder 5" into "go look at why Grinder 5 had 45 minutes of mechanical downtime for the 3rd day in a row."

## Requirements Coverage

| Requirement | Coverage |
|-------------|----------|
| FR-I6 (Trend Indicators on Action Items) | Full |
| FR-I9 (Downtime Pareto) | Full |
| NFR-I5 (Data Integration Flexibility) | Partial (downtime_events supports future Redzone integration) |

## Stories

---

### Story 14.1: Downtime Events Data Model & Seed Data

**As a** developer,
**I want** a `downtime_events` table that stores individual downtime events with reason codes,
**So that** the system can display Pareto breakdowns of why downtime occurred.

**Acceptance Criteria:**

**Given** the migration runs successfully
**When** the database is queried
**Then** the `downtime_events` table exists with columns:
  - `id` (UUID PK)
  - `asset_id` (UUID FK → assets)
  - `event_date` (DATE)
  - `shift` (TEXT CHECK ('morning', 'afternoon', 'night'))
  - `reason_code` (TEXT — e.g., "Mechanical", "Changeover", "Material Shortage", "Quality Hold", "Operator Unavailable", "Planned Maintenance")
  - `reason_detail` (TEXT — freeform description)
  - `duration_minutes` (INTEGER)
  - `is_planned` (BOOLEAN)
  - `source_system` (TEXT DEFAULT 'manual')
  - `source_event_id` (TEXT nullable)
  - `created_at` (TIMESTAMPTZ)
**And** indexes exist on `asset_id`, `event_date`, `reason_code`
**And** RLS is enabled following existing patterns

**Given** the seed script runs
**When** downtime events are queried for the past 7 days
**Then** realistic downtime events exist for assets that have downtime in `daily_summaries`
**And** reason codes are distributed realistically (Mechanical highest, then Changeover, etc.)
**And** the sum of event durations per asset per day approximately matches `daily_summaries.downtime_minutes`

**Technical Notes:**
- Migration: `supabase/migrations/0029_downtime_events.sql`
- Seed data should align with existing `daily_summaries` downtime_minutes values
- Standard reason codes: Mechanical, Changeover, Material Shortage, Quality Hold, Operator Unavailable, Planned Maintenance

**Files to Create/Modify:**
- `supabase/migrations/0029_downtime_events.sql` - New table
- `scripts/seed-data.mjs` - Add downtime events seed data

---

### Story 14.2: Trend Data API Endpoint

**As a** Plant Manager,
**I want** the action items API to include 7-day trend data for each asset,
**So that** I can see whether a problem is new or recurring.

**Acceptance Criteria:**

**Given** an action item exists for an asset with 7 days of history in `daily_summaries`
**When** `GET /api/v1/actions/daily?date={date}` is called
**Then** each action item includes a `trend_data` field containing:
  - 7-day array of the relevant metric (OEE for OEE items, downtime for downtime items, safety event count for safety items)
  - `days_on_report` — number of days this asset+category appeared as an action item in the last 7 days
  - `consecutive_days` — number of consecutive days this has been an issue
  - `week_over_week_change` — percentage change vs. same metric 7 days ago

**Given** an asset has fewer than 7 days of history
**When** trend data is calculated
**Then** only available days are returned
**And** `days_on_report` and `consecutive_days` use available data

**Given** an asset has no prior history (first appearance)
**When** trend data is calculated
**Then** `days_on_report` = 1, `consecutive_days` = 1, `week_over_week_change` = null
**And** the 7-day array contains only today's value

**Technical Notes:**
- Enhance the existing action engine to query trailing 7 days of `daily_summaries` per asset
- Add `trend_data` field to the ActionItem response model
- Cache trend data with 15min TTL (daily tier)

**Files to Create/Modify:**
- `apps/api/app/services/action_engine.py` - Add trend data calculation
- `apps/api/app/schemas/action.py` - Add `TrendData` schema to ActionItem

---

### Story 14.3: Downtime Pareto API Endpoint

**As a** Plant Manager,
**I want** an API endpoint that returns downtime reason code breakdown for an asset or workcenter,
**So that** the frontend can display a Pareto chart showing top downtime drivers.

**Acceptance Criteria:**

**Given** downtime events exist for an asset on a given date
**When** `GET /api/v1/downtime/pareto?date={date}&asset_id={id}` is called
**Then** the response includes:
  - Array of reason codes sorted by total duration (descending)
  - Each entry: reason_code, total_minutes, percentage of total, event_count, is_planned
  - Total downtime minutes
  - Planned vs. unplanned split

**Given** a `area` parameter is provided instead of `asset_id`
**When** the Pareto endpoint is called
**Then** downtime is aggregated across all assets in that workcenter area

**Given** no downtime events exist for the query
**When** the endpoint is called
**Then** the response returns an empty array with total_minutes = 0

**Technical Notes:**
- Query `downtime_events` grouped by `reason_code`, ordered by `SUM(duration_minutes) DESC`
- Support both asset-level and workcenter-level aggregation
- Cache with 15min TTL

**Files to Create/Modify:**
- `apps/api/app/api/downtime.py` - Add Pareto endpoint (or create if not exists)
- `apps/api/app/schemas/downtime.py` - Add `DowntimeParetoResponse` schema

---

### Story 14.4: Trend Indicators on Action Cards

**As a** Plant Manager,
**I want** to see trend arrows and repeat offender badges on each action item card,
**So that** I can instantly tell whether an issue is new, improving, or getting worse.

**Acceptance Criteria:**

**Given** an action item has trend data with `consecutive_days` >= 3
**When** the action card renders
**Then** a "repeat offender" badge is displayed (e.g., "3rd consecutive day" or "4 of last 7 days")
**And** the badge is styled prominently (amber/orange background)

**Given** an action item has `week_over_week_change` data
**When** the action card renders
**Then** a trend arrow is displayed:
  - Green down arrow if the metric improved (OEE up, downtime down)
  - Red up arrow if the metric worsened
  - Gray horizontal arrow if stable (< 2% change)

**Given** an action item has a 7-day sparkline array
**When** the action card renders
**Then** a small sparkline chart shows the 7-day trend next to the metric value

**Given** an action item has no trend data (first appearance)
**When** the action card renders
**Then** a "New" badge is shown instead of trend indicators

**Technical Notes:**
- Use a lightweight sparkline library (e.g., `recharts` SparklineChart or custom SVG)
- Trend arrow: simple SVG icons with color
- Repeat offender badge: Shadcn/UI `Badge` with count

**Files to Create/Modify:**
- `apps/web/src/components/action-engine/TrendIndicator.tsx` - Trend arrow + sparkline component
- `apps/web/src/components/action-engine/RepeatOffenderBadge.tsx` - Consecutive days badge
- `apps/web/src/components/action-engine/InsightEvidenceCard.tsx` - Integrate trend indicators
- `apps/web/src/components/action-engine/InsightSection.tsx` - Pass trend data to cards

---

### Story 14.5: Downtime Pareto Chart on Action Cards

**As a** Plant Manager,
**I want** to see a reason code breakdown chart on action items that have downtime,
**So that** I can understand *why* an asset lost time and direct investigations effectively.

**Acceptance Criteria:**

**Given** an action item is an OEE-miss or downtime-related item
**When** the action card renders and downtime Pareto data is available
**Then** a horizontal bar chart shows the top 3-5 reason codes sorted by duration
**And** each bar shows: reason code name, duration in minutes, percentage of total
**And** planned vs. unplanned downtime is visually distinguished (e.g., hatched vs. solid bars)

**Given** an action item is a safety-only or financial-only item (no downtime component)
**When** the card renders
**Then** no Pareto chart is shown

**Given** the Pareto data is loading
**When** the card renders
**Then** a skeleton loader placeholder is shown where the chart would be

**Technical Notes:**
- Use Recharts `BarChart` (horizontal) for Pareto visualization
- Fetch Pareto data per-asset via `useDowntimePareto(assetId, date)` hook
- Only show on cards where `category` is 'oee' or downtime-related

**Files to Create/Modify:**
- `apps/web/src/components/action-engine/DowntimePareto.tsx` - Pareto chart component
- `apps/web/src/hooks/useDowntimePareto.ts` - Data fetching hook
- `apps/web/src/components/action-engine/EvidenceSection.tsx` - Integrate Pareto into evidence area

---

### Story 14.6: AI Summary with Trend Context

**As a** Plant Manager,
**I want** the smart summary to include week-over-week comparison and trend commentary,
**So that** the AI narrative provides historical context alongside today's data.

**Acceptance Criteria:**

**Given** the smart summary is generated for a date
**When** trend data is available for the plant
**Then** the summary includes a line like: "Overall plant OEE 81.2%, down 3.1 points from last week"

**Given** an asset has been on the report for 3+ consecutive days
**When** the smart summary is generated
**Then** the summary mentions the pattern: "Grinder 5 has appeared on the report for 3 consecutive days — consider escalating to maintenance planning"

**Given** a downtime Pareto breakdown is available
**When** the smart summary is generated
**Then** the summary includes the top downtime driver: "Top downtime driver yesterday: Mechanical (187 min across 4 assets)"

**Technical Notes:**
- Update the smart summary context (`SummaryContext`) to include trend data and Pareto data
- Update the prompt template for the LLM to incorporate trend/Pareto context
- Feed aggregated plant-level week-over-week OEE change

**Files to Create/Modify:**
- `apps/api/app/services/ai/smart_summary.py` - Add trend and Pareto context to prompt
- `apps/api/app/services/action_engine.py` - Provide trend aggregates for summary context
