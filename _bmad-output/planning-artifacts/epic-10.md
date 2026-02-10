---
stepsCompleted: ["step-01-validate-prerequisites", "step-02-design-epics", "step-03-create-stories"]
inputDocuments:
  - "docs/improvements.md"
  - "docs/architecture-api.md"
  - "docs/architecture-web.md"
  - "docs/data-models.md"
epic: 10
status: "ready"
---

# Epic 10: Bug Fixes & Data Quality

## Overview

**Goal:** Plant managers see correct data in all existing views — safety alerts load, live pulse works, and cost-of-loss displays properly.

**Dependencies:** None

**User Value:** Three broken features are fixed. The morning report and dashboard work end-to-end without errors. Builds trust in the platform before new features are added.

## Requirements Coverage

| Requirement | Coverage |
|-------------|----------|
| FR-I15 (Safety Alerts Auth Fix) | Full |
| FR-I16 (Live Pulse Schema Fix) | Full |
| FR-I17 (Cost of Loss Schema Fix) | Full |

## Stories

---

### Story 10.1: Safety Alerts Auth Fix

**As a** Plant Manager,
**I want** safety alerts to load correctly on the dashboard,
**So that** I can see active safety events without encountering 403 errors.

**Acceptance Criteria:**

**Given** an authenticated user is viewing the dashboard
**When** the safety alerts component loads
**Then** the API request includes a `Bearer` token in the `Authorization` header (not `credentials: 'include'`)
**And** safety events are displayed without 403 errors

**Given** the user's session has expired
**When** the safety alerts component attempts to fetch data
**Then** the request fails gracefully with a redirect to login
**And** no confusing 403 error is shown to the user

**Technical Notes:**
- Fix: Change `useSafetyAlerts.ts` from `credentials: 'include'` to `Authorization: Bearer ${token}` pattern
- Follow the same pattern used in `useDailyActions`, `useLivePulse`, `useCostOfLoss` hooks
- Single-file fix

**Files to Create/Modify:**
- `apps/web/src/hooks/useSafetyAlerts.ts` - Fix auth header pattern

---

### Story 10.2: Live Pulse Schema Fix

**As a** Plant Manager,
**I want** the live production pulse view to load without errors,
**So that** I can see real-time production status across all assets.

**Acceptance Criteria:**

**Given** an authenticated user navigates to the live pulse view
**When** the `/api/live-pulse` endpoint is called
**Then** the response returns successfully (200) with current asset statuses
**And** no 500 error from querying non-existent `oee_percentage` column

**Given** live snapshot data exists for multiple assets
**When** the live pulse endpoint returns data
**Then** each asset entry includes correct status, current rate, and shift progress fields
**And** all column references match the actual `live_snapshots` table schema

**Technical Notes:**
- Fix: The endpoint queries `live_snapshots.oee_percentage` which doesn't exist in the table
- Actual columns available: `status`, `current_rate`, `shift_target`, `shift_actual`
- Update the query to use correct column names

**Files to Create/Modify:**
- `apps/api/app/api/live_pulse.py` (or wherever the live pulse route handler is) - Fix column references

---

### Story 10.3: Cost of Loss Schema Fix

**As a** Plant Manager,
**I want** the cost-of-loss view to load without errors,
**So that** I can see the financial impact of production losses.

**Acceptance Criteria:**

**Given** an authenticated user requests cost-of-loss data
**When** the `/api/financial/cost-of-loss` endpoint is called
**Then** the response returns successfully (200) with financial loss data
**And** no 500 error from querying non-existent `waste` column

**Given** daily summary data exists with waste counts
**When** the cost-of-loss calculation runs
**Then** it queries `daily_summaries.waste_count` (not `waste`)
**And** financial loss is correctly calculated using waste count * standard cost

**Technical Notes:**
- Fix: The endpoint queries `daily_summaries.waste` but the actual column is `waste_count`
- Update the query to reference `waste_count`
- Verify the financial calculation logic still works with the correct column

**Files to Create/Modify:**
- `apps/api/app/api/financial.py` (or relevant financial route handler) - Fix column reference
