---
stepsCompleted: ["step-01-validate-prerequisites", "step-02-design-epics", "step-03-create-stories", "step-04-final-validation"]
inputDocuments:
  - "docs/improvements.md"
  - "docs/architecture-api.md"
  - "docs/architecture-web.md"
  - "docs/data-models.md"
  - "docs/api-contracts.md"
  - "docs/integration-architecture.md"
  - "_bmad-output/planning-artifacts/epics.md"
lastUpdated: "2026-02-10"
---

# TFN AI Hub Improvements - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for TFN AI Hub improvements, decomposing the planned features from the improvements tracker into implementable stories. These epics continue from the existing Epic 1-9 series (Epic 10+).

## Requirements Inventory

### Functional Requirements

- **FR-I1 (Workcenter Production Summary):** Display aggregated production output by workcenter (Roasting, Grinding, Filling, Packaging) showing actual vs. target, attainment %, and per-asset breakdown with hit/miss indicators.
- **FR-I2 (Schedule Attainment & Product Mix):** Track what products were produced vs. what was scheduled, show variance callouts for wrong-product runs and underproduction, with overall product mix comparison.
- **FR-I3 (Schedule Upload):** Allow CSV/Excel upload of weekly production schedules with validation, fuzzy asset name matching, auto-creation of new products, preview before commit, and upsert behavior for re-uploads.
- **FR-I4 (Action Item Acknowledgment):** Enable users to mark action items as reviewed/completed with persistence in the database, following the `handoff_acknowledgments` pattern.
- **FR-I5 (Follow-Up Status Tracking):** Provide a "My Assignments" panel showing open follow-ups grouped by status, assignee status updates (in-progress/resolved with notes), assignment badges on action cards, and RLS updates for assignee write access.
- **FR-I6 (Trend Indicators):** Show 7-day sparkline or trend arrow on each action item, "repeat offender" badges for consecutive appearances, and week-over-week comparison in the AI summary header.
- **FR-I7 (Email Notifications):** Send email to assignees when follow-ups are assigned, capture responses via link-based form (MVP) or email reply parsing (future), log all messages in `followup_messages` table with full conversation thread.
- **FR-I8 (Action Plans):** Create structured action plans from investigation findings linking root cause to corrective/preventive actions, with status tracking (draft/open/in_progress/completed/verified), progress updates, and integration with morning report AI summary.
- **FR-I9 (Downtime Pareto):** Display downtime reason code breakdown per asset as a Pareto chart (horizontal bars sorted by duration), with workcenter-level and plant-level aggregation, distinguishing planned vs. unplanned downtime.
- **FR-I10 (Report History):** Add date picker to morning report allowing navigation to any historical date, with prev/next day arrows, URL-driven date parameter, and on-demand smart summary generation for historical dates.
- **FR-I11 (Shift-Level Granularity):** Break daily aggregates into per-shift data (morning/afternoon/night), show shift tabs on workcenter scorecard, attribute action item misses to responsible shifts, and enable shift-over-shift comparison.
- **FR-I12 (Morning Meeting Mode):** Provide condensed "meeting mode" toggle showing top 3-5 items as large talking points, with clear Safety/Performance/Priorities section headers and prominent assignment controls.
- **FR-I13 (Teams Push Notifications):** Post morning summary cards to Teams channels via webhook at 6:15 AM, send follow-up assignment notifications to assignees, and send escalation nudges for unacknowledged items.
- **FR-I14 (Conversational Follow-Up):** Add "Ask about this" button on smart summary that opens AI chat pre-loaded with morning report context, with drill-down links on asset names in summary text.
- **FR-I15 (Safety Alerts Auth Fix):** Fix `useSafetyAlerts.ts` to use Bearer token in Authorization header instead of `credentials: 'include'` cookie-based auth.
- **FR-I16 (Live Pulse Schema Fix):** Fix `/api/live-pulse` endpoint to query correct column names in `live_snapshots` table (remove reference to non-existent `oee_percentage`).
- **FR-I17 (Cost of Loss Schema Fix):** Fix `/api/financial/cost-of-loss` endpoint to query `waste_count` instead of non-existent `waste` column in `daily_summaries`.

### NonFunctional Requirements

- **NFR-I1 (Glanceability):** Workcenter scorecard must be scannable in 5 seconds — manager absorbs whole plant performance at a glance.
- **NFR-I2 (Upload Validation):** Schedule upload must validate all rows before committing, with clear error highlighting and preview step.
- **NFR-I3 (Audit Trail):** All acknowledgments, follow-up assignments, responses, and action plan updates must be persisted with timestamps and user attribution for accountability.
- **NFR-I4 (Email Delivery):** Email notifications must be sent within 60 seconds of follow-up assignment.
- **NFR-I5 (Data Integration Flexibility):** New data models (products, schedule, actuals, downtime_events) must support both seed/manual data entry (MVP) and future system integration (Redzone, AX/D365).
- **NFR-I6 (Backward Compatibility):** New shift-level data must not break existing daily aggregate views — daily remains the default with shift as drill-down.
- **NFR-I7 (URL Shareability):** Historical report dates must be URL-driven so report links can be shared via Teams or email.
- **NFR-I8 (RLS Compliance):** All new tables must follow existing Row Level Security patterns — users only see data they're authorized for.

### Additional Requirements

**From Architecture (existing patterns to follow):**
- TurboRepo monorepo: frontend changes in `apps/web/src/`, backend in `apps/api/app/`
- Supabase migrations in `supabase/migrations/` with sequential numbering (next: 0026+)
- FastAPI route handlers in `apps/api/app/api/`, services in `apps/api/app/services/`
- Pydantic models in `apps/api/app/models/`, schemas in `apps/api/app/schemas/`
- React components follow domain-based organization (`components/{domain}/`)
- JWT Bearer auth pattern for all API calls (not cookie-based)
- Existing `action_followups` table (migration 0025) provides foundation for follow-up features
- DataSource Protocol pattern for data access abstraction
- ManufacturingTool base class for any new AI agent tools
- Tool caching with tiered TTLs (60s live, 15min daily, 1hr static)

**From Data Model (existing schema context):**
- `assets.area` column already supports workcenter grouping (Roasting, Grinding, Filling, Packaging)
- `daily_summaries` has `units_produced`, `downtime_minutes`, `oee` — but no shift or product breakdown
- `shift_targets` has per-shift targets but actuals are daily-only
- `live_snapshots` missing `oee_percentage` column (schema fix needed)
- `daily_summaries` has `waste_count` not `waste` (schema fix needed)
- `safety_events` table exists with severity, status, description
- New tables needed: `products`, `production_schedule`, `production_actuals`, `downtime_events`, `action_acknowledgments`, `followup_messages`, `action_plans`, `action_plan_updates`

**From UX (inline in improvements.md):**
- Workcenter scorecard at top of morning report, above action items
- Expandable asset detail within workcenter rows
- Date picker in morning report header next to "T-1 Data" badge
- "Meeting mode" as toggle on existing page or separate route
- Assignment badges visible on action cards
- Message thread UI for follow-up conversations
- Pareto chart as horizontal bar within action cards

### FR Coverage Map

| FR | Epic | Description |
|----|------|-------------|
| FR-I1 | Epic 11 | Workcenter Production Summary |
| FR-I2 | Epic 12 | Schedule Attainment & Product Mix |
| FR-I3 | Epic 12 | Schedule Upload (CSV/Excel) |
| FR-I4 | Epic 13 | Action Item Acknowledgment |
| FR-I5 | Epic 13 | Follow-Up Status Tracking & My Assignments |
| FR-I6 | Epic 14 | Trend Indicators on Action Items |
| FR-I7 | Epic 15 | Email Notifications with Response Tracking |
| FR-I8 | Epic 16 | Action Plans (Continuous Improvement) |
| FR-I9 | Epic 14 | Downtime Pareto (Reason Code Breakdown) |
| FR-I10 | Epic 17 | Report History (Date Picker) |
| FR-I11 | Epic 17 | Shift-Level Granularity |
| FR-I12 | Epic 18 | Morning Meeting Mode |
| FR-I13 | Epic 18 | Teams Push Notifications |
| FR-I14 | Epic 19 | Conversational Follow-Up on AI Summary |
| FR-I15 | Epic 10 | Safety Alerts Auth Fix |
| FR-I16 | Epic 10 | Live Pulse Schema Fix |
| FR-I17 | Epic 10 | Cost of Loss Schema Fix |

## Epic List

| Epic | Title | FRs | Priority | Status |
|------|-------|-----|----------|--------|
| 10 | Bug Fixes & Data Quality | FR-I15, FR-I16, FR-I17 | Immediate | Ready |
| 11 | Workcenter Production Scorecard | FR-I1 | P1 | Ready |
| 12 | Products, Schedule & Attainment | FR-I2, FR-I3 | P1 | Ready |
| 13 | Action Accountability Loop | FR-I4, FR-I5 | P1 | Ready |
| 14 | Trend Intelligence & Downtime Pareto | FR-I6, FR-I9 | P1 | Ready |
| 15 | Email Notifications & Response Tracking | FR-I7 | P1 | Ready |
| 16 | Action Plans & Continuous Improvement | FR-I8 | P1 | Ready |
| 17 | Report History & Shift Granularity | FR-I10, FR-I11 | P2 | Ready |
| 18 | Meeting Mode & Teams Integration | FR-I12, FR-I13 | P2 | Ready |
| 19 | Conversational AI Follow-Up | FR-I14 | P3 | Ready |

---

## Epic 10: Bug Fixes & Data Quality

**Goal:** Fix three broken features so existing views work correctly.

**Stories:** 3 | **Details:** See [epic-10.md](epic-10.md)

- Story 10.1: Safety Alerts Auth Fix
- Story 10.2: Live Pulse Schema Fix
- Story 10.3: Cost of Loss Schema Fix

---

## Epic 11: Workcenter Production Scorecard

**Goal:** Plant managers see "how much did we make?" broken down by workcenter with per-asset drill-down.

**Stories:** 3 | **Details:** See [epic-11.md](epic-11.md)

- Story 11.1: Workcenter Summary API Endpoint
- Story 11.2: Workcenter Scorecard UI Component
- Story 11.3: Workcenter Seed Data

---

## Epic 12: Products, Schedule & Attainment

**Goal:** Upload production schedules and see "did we make the right stuff?" with product-level detail.

**Stories:** 6 | **Details:** See [epic-12.md](epic-12.md)

- Story 12.1: Products & Schedule Data Model
- Story 12.2: Products & Schedule Seed Data
- Story 12.3: Schedule Upload API
- Story 12.4: Schedule Upload UI
- Story 12.5: Schedule Attainment API
- Story 12.6: Schedule Attainment UI Section

---

## Epic 13: Action Accountability Loop

**Goal:** Acknowledge action items, track follow-ups with status visibility, and see assignment badges.

**Stories:** 5 | **Details:** See [epic-13.md](epic-13.md)

- Story 13.1: Action Acknowledgment Backend
- Story 13.2: Action Acknowledgment UI
- Story 13.3: Follow-Up Status Updates & RLS
- Story 13.4: Assignment Badge on Action Cards
- Story 13.5: "My Assignments" Panel

---

## Epic 14: Trend Intelligence & Downtime Pareto

**Goal:** See historical context (is this new or recurring?) and understand why downtime happened.

**Stories:** 6 | **Details:** See [epic-14.md](epic-14.md)

- Story 14.1: Downtime Events Data Model & Seed Data
- Story 14.2: Trend Data API Endpoint
- Story 14.3: Downtime Pareto API Endpoint
- Story 14.4: Trend Indicators on Action Cards
- Story 14.5: Downtime Pareto Chart on Action Cards
- Story 14.6: AI Summary with Trend Context

---

## Epic 15: Email Notifications & Response Tracking

**Goal:** Assignees get email notifications and can respond via link, creating an auditable conversation thread.

**Stories:** 4 | **Details:** See [epic-15.md](epic-15.md)

- Story 15.1: Follow-Up Messages Data Model
- Story 15.2: Email Notification Service
- Story 15.3: Response Capture via Token Link
- Story 15.4: Message Thread UI

---

## Epic 16: Action Plans & Continuous Improvement

**Goal:** Create structured action plans from investigations, track root cause to corrective action to verification.

**Stories:** 6 | **Details:** See [epic-16.md](epic-16.md)

- Story 16.1: Action Plans Data Model
- Story 16.2: Action Plans CRUD API
- Story 16.3: Create Action Plan from Follow-Up
- Story 16.4: Active Plans Badge on Action Cards
- Story 16.5: Action Plans Dashboard
- Story 16.6: AI Summary with Action Plan Context

---

## Epic 17: Report History & Shift Granularity

**Goal:** Navigate to any historical date's report and drill into shift-level performance.

**Stories:** 4 | **Details:** See [epic-17.md](epic-17.md)

- Story 17.1: Date Picker on Morning Report
- Story 17.2: Smart Summary On-Demand Generation for Historical Dates
- Story 17.3: Shift Summaries Data Model
- Story 17.4: Shift Breakdown API & UI

---

## Epic 18: Meeting Mode & Teams Integration

**Goal:** Run standups from the app with talking-points view, and get daily Teams summary cards.

**Stories:** 5 | **Details:** See [epic-18.md](epic-18.md)

- Story 18.1: Meeting Mode Toggle & Talking Points View
- Story 18.2: Teams Webhook Configuration
- Story 18.3: Morning Summary Teams Card
- Story 18.4: Follow-Up Assignment Teams Notification
- Story 18.5: Escalation Nudge Notifications

---

## Epic 19: Conversational AI Follow-Up

**Goal:** Ask follow-up questions about the smart summary with morning report context pre-loaded.

**Stories:** 3 | **Details:** See [epic-19.md](epic-19.md)

- Story 19.1: "Ask About This" Button on Smart Summary
- Story 19.2: Clickable Asset Links in Smart Summary
- Story 19.3: Context-Aware Follow-Up Suggestions
