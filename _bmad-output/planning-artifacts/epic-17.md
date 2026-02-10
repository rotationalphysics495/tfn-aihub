---
stepsCompleted: ["step-01-validate-prerequisites", "step-02-design-epics", "step-03-create-stories"]
inputDocuments:
  - "docs/improvements.md"
  - "docs/architecture-api.md"
  - "docs/architecture-web.md"
  - "docs/data-models.md"
epic: 17
status: "ready"
---

# Epic 17: Report History & Shift Granularity

## Overview

**Goal:** Plant managers can navigate to any historical date's report and drill down into shift-level performance — enabling weekly reviews, incident comparison, and shift-specific investigations.

**Dependencies:** None (backend already supports date parameters; shift data extends existing tables)

**User Value:** "Show me last Tuesday" and "which shift had the problem?" — both answered without leaving the app. URL-shareable report links for Teams messages or weekly review meetings.

## Requirements Coverage

| Requirement | Coverage |
|-------------|----------|
| FR-I10 (Report History - Date Picker) | Full |
| FR-I11 (Shift-Level Granularity) | Full |
| NFR-I6 (Backward Compatibility) | Full |
| NFR-I7 (URL Shareability) | Full |

## Stories

---

### Story 17.1: Date Picker on Morning Report

**As a** Plant Manager,
**I want** a date picker on the morning report page that lets me navigate to any past date,
**So that** I can review historical reports for weekly meetings or incident comparisons.

**Acceptance Criteria:**

**Given** the morning report page loads
**When** the header section renders
**Then** a date picker appears next to the "T-1 Data" badge
**And** it defaults to yesterday's date

**Given** the user selects a different date from the picker
**When** the date is changed
**Then** all report sections (workcenter scorecard, action items, smart summary) reload with data for the selected date
**And** the URL updates to `/morning-report?date=2026-02-05`
**And** the "T-1 Data" badge updates to reflect the selected date (e.g., "Feb 5 Data")

**Given** prev/next day arrow buttons are clicked
**When** navigating forward or backward
**Then** the date increments/decrements by one day
**And** the report reloads for the new date
**And** the "next" arrow is disabled when viewing yesterday (can't go to today or future)

**Given** a URL with a `date` query parameter is loaded directly
**When** the page initializes
**Then** the report shows data for the specified date
**And** the date picker reflects the URL date

**Given** the selected date has no daily_summaries records
**When** the report loads
**Then** an empty state is shown: "No production data available for {date}"
**And** the date picker and navigation arrows remain functional

**Technical Notes:**
- Use Shadcn/UI `Calendar` + `Popover` for date picker
- Update URL via `useSearchParams` / `router.push` with shallow navigation
- Pass selected date to all hooks: `useDailyActions(date)`, `useSmartSummary(date)`, `useWorkcenterSummary(date)`
- The backend APIs already accept date parameters — this is primarily a frontend change

**Files to Create/Modify:**
- `apps/web/src/app/morning-report/page.tsx` - Add date state, picker, and URL sync
- `apps/web/src/components/report/DateNavigation.tsx` - Date picker + prev/next arrows
- `apps/web/src/hooks/useDailyActions.ts` - Accept date parameter (instead of hardcoded yesterday)
- `apps/web/src/hooks/useSmartSummary.ts` - Accept date parameter

---

### Story 17.2: Smart Summary On-Demand Generation for Historical Dates

**As a** Plant Manager,
**I want** to generate a smart summary for a historical date that doesn't have one,
**So that** I can get AI analysis even when reviewing past reports.

**Acceptance Criteria:**

**Given** the user navigates to a historical date that has production data but no saved smart summary
**When** the summary section loads
**Then** a prompt is shown: "No summary exists for this date. Generate one?"
**And** a "Generate Summary" button is displayed

**Given** the user clicks "Generate Summary"
**When** the summary generation API is called
**Then** a loading indicator shows while the summary is being generated
**And** once complete, the summary appears in the normal summary section
**And** the summary is saved for future viewing of this date

**Given** a summary already exists for the selected historical date
**When** the report loads
**Then** the existing summary is displayed immediately (no generation prompt)

**Technical Notes:**
- The backend `/api/summaries/smart/{date}` endpoint already supports arbitrary dates
- Frontend change: detect missing summary and show generation prompt
- Consider a "Regenerate" option for existing summaries too

**Files to Create/Modify:**
- `apps/web/src/components/action-list/MorningSummarySection.tsx` - Add missing summary detection and generation prompt
- `apps/web/src/hooks/useSmartSummary.ts` - Add generate/regenerate mutation

---

### Story 17.3: Shift Summaries Data Model

**As a** developer,
**I want** shift-level performance data alongside the existing daily aggregates,
**So that** the report can show which shift contributed to a daily miss.

**Acceptance Criteria:**

**Given** the migration runs successfully
**When** the database is queried
**Then** the `shift_summaries` table exists with columns:
  - `id` (UUID PK)
  - `asset_id` (UUID FK → assets)
  - `date` (DATE)
  - `shift` (TEXT CHECK ('morning', 'afternoon', 'night'))
  - `oee` (DECIMAL(5,2))
  - `availability` (DECIMAL(5,2))
  - `performance` (DECIMAL(5,2))
  - `quality` (DECIMAL(5,2))
  - `downtime_minutes` (INTEGER)
  - `units_produced` (INTEGER)
  - `created_at` (TIMESTAMPTZ)
**And** a unique constraint exists on (asset_id, date, shift)
**And** indexes exist on `asset_id`, `date`
**And** RLS follows existing patterns

**Given** the seed script runs
**When** shift summaries are queried
**Then** each asset has 3 shift records per day (morning/afternoon/night)
**And** the sum of shift values approximately matches the daily_summaries aggregate
**And** shifts have realistic variance (e.g., afternoon shift lower on some assets)

**Technical Notes:**
- Migration: `supabase/migrations/0032_shift_summaries.sql`
- Option B approach: new table alongside `daily_summaries` (backward compatible)
- Seed data should distribute daily totals across shifts with variation
- Daily views continue working unchanged

**Files to Create/Modify:**
- `supabase/migrations/0032_shift_summaries.sql` - New table
- `scripts/seed-data.mjs` - Add shift-level seed data

---

### Story 17.4: Shift Breakdown API & UI

**As a** Plant Manager,
**I want** to see per-shift performance breakdown on the workcenter scorecard and action items,
**So that** I can identify which shift caused a daily miss and direct investigations accordingly.

**Acceptance Criteria:**

**Given** the workcenter summary endpoint is called with shift data available
**When** the response is returned
**Then** each workcenter entry includes a `shift_breakdown` array with per-shift metrics:
  - Shift name
  - Actual output, target output, attainment %
  - OEE, downtime minutes
**And** the overall workcenter figures are the aggregation across shifts

**Given** the workcenter scorecard renders with shift data
**When** the user clicks a shift tab or toggle (Morning / Afternoon / Night / All)
**Then** the scorecard filters to show only that shift's data
**And** the action items below also filter to the selected shift

**Given** an action item missed target primarily on one shift
**When** the action card renders
**Then** it shows shift attribution: "Grinder 5: 72 min downtime (afternoon shift — 58 min mechanical)"
**And** the recommendation targets the responsible shift

**Given** all three shifts missed target (systemic issue)
**When** the action card renders
**Then** it remains a daily-level item without shift attribution
**And** the recommendation reflects a systemic rather than shift-specific issue

**Technical Notes:**
- Update workcenter summary endpoint to include optional shift breakdown
- Add shift tabs to the scorecard component
- Update action engine to check `shift_summaries` when attributing misses
- Daily aggregate view remains the default (NFR-I6 backward compatibility)

**Files to Create/Modify:**
- `apps/api/app/api/production.py` - Add shift breakdown to workcenter summary
- `apps/api/app/services/action_engine.py` - Add shift attribution logic
- `apps/web/src/components/production/WorkcenterScorecard.tsx` - Add shift tabs
- `apps/web/src/components/production/ShiftTabs.tsx` - Shift selector component
- `apps/web/src/components/action-engine/InsightSection.tsx` - Show shift attribution
