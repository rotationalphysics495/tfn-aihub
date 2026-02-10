---
stepsCompleted: ["step-01-validate-prerequisites", "step-02-design-epics", "step-03-create-stories"]
inputDocuments:
  - "docs/improvements.md"
  - "docs/architecture-api.md"
  - "docs/architecture-web.md"
  - "docs/data-models.md"
epic: 11
status: "ready"
---

# Epic 11: Workcenter Production Scorecard

## Overview

**Goal:** Plant managers can see at a glance "how much did we make?" broken down by workcenter (Roasting, Grinding, Filling, Packaging), with actual vs. target and per-asset drill-down — answering the first question every morning.

**Dependencies:** None (uses existing `assets.area`, `daily_summaries`, `shift_targets`)

**User Value:** The morning report goes from "what went wrong" to "here's the full picture." All workcenters and assets are visible — not just the ones that missed targets. The manager absorbs the whole plant in 5 seconds.

## Requirements Coverage

| Requirement | Coverage |
|-------------|----------|
| FR-I1 (Workcenter Production Summary) | Full |
| NFR-I1 (Glanceability) | Full |

## Stories

---

### Story 11.1: Workcenter Summary API Endpoint

**As a** Plant Manager,
**I want** an API endpoint that returns production data grouped by workcenter,
**So that** the frontend can display a plant-wide production scorecard.

**Acceptance Criteria:**

**Given** daily summary data exists for multiple assets across workcenters
**When** `GET /api/v1/production/workcenter-summary?date={date}` is called
**Then** the response includes one entry per workcenter (grouped by `assets.area`) with:
  - Workcenter name (e.g., "Grinding")
  - Total actual output (sum of `daily_summaries.units_produced` for assets in that area)
  - Total target output (sum of `shift_targets.target_units` for assets in that area)
  - Attainment percentage (actual / target * 100)
  - Count of assets that hit target vs. missed
  - Per-asset breakdown array with: asset name, actual, target, OEE, downtime minutes

**Given** no daily summary data exists for the requested date
**When** the endpoint is called
**Then** the response returns an empty array with a 200 status
**And** the response includes a message indicating no data available for that date

**Given** a date parameter is not provided
**When** the endpoint is called
**Then** it defaults to yesterday (T-1)

**Technical Notes:**
- New endpoint in `apps/api/app/api/` — follows existing route pattern
- Query joins `assets` (for area grouping) with `daily_summaries` (for actuals) and `shift_targets` (for targets)
- Group by `assets.area`, aggregate within each group
- Pydantic response model: `WorkcenterSummary` with nested `AssetDetail` array

**Files to Create/Modify:**
- `apps/api/app/api/production.py` - Add workcenter summary endpoint
- `apps/api/app/schemas/production.py` - Create `WorkcenterSummaryResponse`, `WorkcenterEntry`, `AssetDetail` schemas
- `apps/api/app/main.py` - Register route if new router needed

---

### Story 11.2: Workcenter Scorecard UI Component

**As a** Plant Manager,
**I want** a visual scorecard at the top of the morning report showing each workcenter's production performance,
**So that** I can absorb the whole plant's performance in 5 seconds.

**Acceptance Criteria:**

**Given** the morning report page loads with workcenter summary data
**When** the scorecard section renders
**Then** it displays one row per workcenter showing:
  - Workcenter name
  - Actual output vs. target output (e.g., "4,200 / 5,000")
  - Attainment percentage with color coding (green >= 95%, yellow 85-94%, red < 85%)
  - Count of assets hit vs. missed (e.g., "3 of 4 assets on target")
**And** the scorecard appears above the action items section

**Given** a workcenter row is clicked or expanded
**When** the detail view opens
**Then** it shows per-asset breakdown: asset name, actual vs. target, OEE %, downtime minutes
**And** each asset row is color-coded green (hit target) or red (missed)

**Given** no workcenter data is available for the date
**When** the scorecard section renders
**Then** it shows an appropriate empty state message

**Given** the page is viewed on a tablet
**When** the scorecard renders
**Then** text and numbers are readable from 3 feet away (NFR-I1 glanceability)

**Technical Notes:**
- New component in `apps/web/src/components/production/`
- Use existing Shadcn/UI Card, Collapsible components
- Hook: `useWorkcenterSummary(date)` calling the new API endpoint
- Position in morning report page: above `ActionListContainer`

**Files to Create/Modify:**
- `apps/web/src/components/production/WorkcenterScorecard.tsx` - Main scorecard component
- `apps/web/src/components/production/WorkcenterRow.tsx` - Individual workcenter row with expand
- `apps/web/src/components/production/AssetDetailTable.tsx` - Expanded asset detail
- `apps/web/src/hooks/useWorkcenterSummary.ts` - Data fetching hook
- `apps/web/src/app/morning-report/page.tsx` - Integrate scorecard above action items

---

### Story 11.3: Workcenter Seed Data

**As a** developer or demo user,
**I want** the seed data script to populate realistic workcenter-level production data,
**So that** the workcenter scorecard has meaningful data to display out of the box.

**Acceptance Criteria:**

**Given** the seed script runs successfully
**When** the workcenter summary endpoint is called for yesterday's date
**Then** data exists for all 4 workcenters (Roasting, Grinding, Filling, Packaging)
**And** each workcenter has 2-4 assets with varied performance (some hit target, some miss)
**And** attainment ranges from ~70% to ~100% across workcenters to show realistic variation

**Given** the existing seed data assets already have `area` assignments
**When** the seed data is reviewed
**Then** all assets are assigned to their correct workcenter area
**And** `shift_targets` exist for all assets

**Technical Notes:**
- Update `scripts/seed-data.mjs` to ensure all assets have proper area assignments
- Verify existing `daily_summaries` seed data provides good variation per workcenter
- May need to adjust existing target values to create realistic hit/miss distribution

**Files to Create/Modify:**
- `scripts/seed-data.mjs` - Verify/update area assignments and target alignment
