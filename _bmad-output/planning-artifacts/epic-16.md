---
stepsCompleted: ["step-01-validate-prerequisites", "step-02-design-epics", "step-03-create-stories"]
inputDocuments:
  - "docs/improvements.md"
  - "docs/architecture-api.md"
  - "docs/architecture-web.md"
  - "docs/data-models.md"
epic: 16
status: "ready"
---

# Epic 16: Action Plans & Continuous Improvement

## Overview

**Goal:** Plant managers can create structured action plans from investigation findings, tracking root cause to corrective action to verification — turning daily firefighting into a systematic improvement record.

**Dependencies:** Epic 13 (action plans are created from follow-up investigation responses)

**User Value:** Closes the full loop: issue → investigation → root cause → corrective action → verification. Active plans show on morning report action cards ("bearing replacement scheduled for Friday"). The AI summary references them. Over time, this becomes the plant's continuous improvement system.

## Requirements Coverage

| Requirement | Coverage |
|-------------|----------|
| FR-I8 (Action Plans - Continuous Improvement) | Full |
| NFR-I3 (Audit Trail) | Full (action plan updates + verification) |
| NFR-I8 (RLS Compliance) | Full |

## Stories

---

### Story 16.1: Action Plans Data Model

**As a** developer,
**I want** database tables for action plans and their progress updates,
**So that** the system can track corrective and preventive actions from investigation to completion.

**Acceptance Criteria:**

**Given** the migration runs successfully
**When** the database is queried
**Then** the `action_plans` table exists with columns:
  - `id` (UUID PK)
  - `title` (TEXT — e.g., "Replace worn bearing on Grinder 5")
  - `description` (TEXT — full context, root cause analysis)
  - `asset_id` (UUID FK → assets, nullable for plant-wide plans)
  - `category` (TEXT CHECK ('corrective', 'preventive', 'improvement'))
  - `root_cause` (TEXT)
  - `corrective_action` (TEXT)
  - `preventive_action` (TEXT — what changes to prevent recurrence)
  - `source_followup_id` (UUID FK → action_followups, nullable)
  - `owner_id` (UUID FK → auth.users)
  - `status` (TEXT CHECK ('draft', 'open', 'in_progress', 'completed', 'verified'))
  - `priority` (TEXT CHECK ('low', 'medium', 'high', 'critical'))
  - `due_date` (DATE)
  - `completed_at` (TIMESTAMPTZ)
  - `verified_by` (UUID FK → auth.users, nullable)
  - `verified_at` (TIMESTAMPTZ)
  - `created_at`, `updated_at` (TIMESTAMPTZ)

**And** the `action_plan_updates` table exists with columns:
  - `id` (UUID PK)
  - `action_plan_id` (UUID FK → action_plans)
  - `author_id` (UUID FK → auth.users)
  - `update_text` (TEXT)
  - `status_change` (TEXT nullable — e.g., "open → in_progress")
  - `created_at` (TIMESTAMPTZ)

**And** RLS is enabled: owners can CRUD their plans, authenticated users can read all plans
**And** indexes exist on `asset_id`, `status`, `owner_id`, `source_followup_id`

**Technical Notes:**
- Migration: `supabase/migrations/0031_action_plans.sql`
- Follow existing RLS patterns from `action_followups`

**Files to Create/Modify:**
- `supabase/migrations/0031_action_plans.sql` - New tables

---

### Story 16.2: Action Plans CRUD API

**As a** Plant Manager,
**I want** API endpoints to create, read, update, and list action plans,
**So that** the frontend can manage the full action plan lifecycle.

**Acceptance Criteria:**

**Given** an authenticated user calls `POST /api/v1/action-plans`
**When** the request includes title, description, category, root_cause, corrective_action, asset_id, priority, due_date
**Then** a new action plan is created with status='open' and the current user as owner
**And** the response includes the created plan with its ID

**Given** an authenticated user calls `GET /api/v1/action-plans`
**When** optional filters are provided (status, asset_id, owner_id, priority)
**Then** matching action plans are returned sorted by priority (critical first) then due_date

**Given** an action plan owner calls `PATCH /api/v1/action-plans/{id}`
**When** the request includes updated fields (status, corrective_action, due_date, etc.)
**Then** the plan is updated and an `action_plan_updates` record is created logging the change

**Given** a user calls `POST /api/v1/action-plans/{id}/updates`
**When** the request includes update_text and optional status_change
**Then** a progress update is recorded in `action_plan_updates`
**And** if status_change is provided, the plan's status is updated

**Given** a user calls `POST /api/v1/action-plans/{id}/verify`
**When** the user confirms the fix worked
**Then** the plan status is set to 'verified', `verified_by` and `verified_at` are recorded

**Technical Notes:**
- New router: `apps/api/app/api/action_plans.py`
- Pydantic schemas for create/update/response
- List endpoint supports pagination and filtering

**Files to Create/Modify:**
- `apps/api/app/api/action_plans.py` - CRUD endpoints
- `apps/api/app/schemas/action_plan.py` - Request/response schemas
- `apps/api/app/main.py` - Register action plans router

---

### Story 16.3: Create Action Plan from Follow-Up

**As a** Plant Manager,
**I want** to create an action plan directly from a follow-up investigation response,
**So that** the plan is pre-populated with the asset, issue context, and engineer's findings.

**Acceptance Criteria:**

**Given** a follow-up has a response from the assignee with investigation findings
**When** the manager clicks "Create Action Plan" on the follow-up detail
**Then** an action plan creation form opens pre-populated with:
  - `asset_id` from the original action item
  - `description` from the action item summary + assignee's response
  - `root_cause` from the assignee's response text
  - `source_followup_id` linking back to the follow-up
**And** the manager can edit any pre-filled field before saving

**Given** the action plan is created from a follow-up
**When** the follow-up detail is viewed later
**Then** a link to the created action plan is visible
**And** the follow-up shows "Action plan created" status

**Technical Notes:**
- "Create Action Plan" button appears on follow-up entries that have responses
- Pre-populate fields via query params or a dedicated creation endpoint that accepts followup_id
- Link the plan back via `source_followup_id`

**Files to Create/Modify:**
- `apps/web/src/components/action-list/FollowUpEntry.tsx` - Add "Create Action Plan" button
- `apps/web/src/components/action-plans/ActionPlanForm.tsx` - Creation/edit form
- `apps/web/src/hooks/useActionPlans.ts` - CRUD hook for action plans

---

### Story 16.4: Active Plans Badge on Action Cards

**As a** Plant Manager,
**I want** to see on the morning report action card if an asset already has an active action plan,
**So that** I don't create redundant assignments and the team knows the issue is being addressed.

**Acceptance Criteria:**

**Given** an action item's asset has an open/in-progress action plan
**When** the action card renders
**Then** a badge is displayed: "Action plan: {title} (due {date}, {status})"
**And** clicking the badge opens the action plan detail

**Given** an asset has multiple active action plans
**When** the action card renders
**Then** a summary badge shows: "2 active action plans" with a dropdown or link to view them

**Given** an asset has no action plans or only completed/verified plans
**When** the action card renders
**Then** no action plan badge is shown

**Technical Notes:**
- Query action plans alongside action items (join on asset_id, filter status in ('open', 'in_progress'))
- Display as Shadcn/UI Badge with link behavior

**Files to Create/Modify:**
- `apps/web/src/components/action-engine/ActivePlanBadge.tsx` - Plan badge component
- `apps/web/src/components/action-engine/InsightEvidenceCard.tsx` - Integrate badge
- `apps/web/src/hooks/useActiveActionPlans.ts` - Fetch active plans for action item assets

---

### Story 16.5: Action Plans Dashboard

**As a** Plant Manager,
**I want** a dedicated view showing all action plans grouped by status,
**So that** I can manage the plant's continuous improvement efforts in one place.

**Acceptance Criteria:**

**Given** the user navigates to `/action-plans`
**When** the page loads
**Then** all action plans are displayed grouped by status:
  - **Open** — new plans awaiting action
  - **In Progress** — actively being worked on
  - **Completed** — corrective action done, awaiting verification
  - **Verified** — confirmed effective
**And** each plan shows: title, asset name, priority, owner, due date, days until due (or overdue indicator)

**Given** a plan is overdue (past due_date and not completed/verified)
**When** the dashboard renders
**Then** the overdue plan is highlighted in red with "X days overdue"

**Given** the user clicks on a plan
**When** the detail view opens
**Then** it shows: full description, root cause, corrective action, preventive action, progress updates timeline, source follow-up link (if applicable)
**And** the user can add progress updates or change status

**Given** filters are applied (by asset, priority, owner, status)
**When** the dashboard updates
**Then** only matching plans are shown
**And** filter state is preserved in URL params

**Technical Notes:**
- New page: `apps/web/src/app/action-plans/page.tsx`
- Add navigation link in sidebar/nav
- Kanban-style or list-grouped-by-status layout
- Use Shadcn/UI `Card`, `Badge`, `Tabs` components

**Files to Create/Modify:**
- `apps/web/src/app/action-plans/page.tsx` - Dashboard page
- `apps/web/src/components/action-plans/ActionPlanCard.tsx` - Individual plan card
- `apps/web/src/components/action-plans/ActionPlanDetail.tsx` - Detail/edit view
- `apps/web/src/components/action-plans/UpdateTimeline.tsx` - Progress updates timeline
- `apps/web/src/hooks/useActionPlans.ts` - List/filter hook (extend from Story 16.3)

---

### Story 16.6: AI Summary with Action Plan Context

**As a** Plant Manager,
**I want** the smart summary to mention active action plans when relevant assets appear,
**So that** I know the team is already working on recurring issues.

**Acceptance Criteria:**

**Given** the smart summary is generated for a date
**When** an asset in the action items has an active action plan
**Then** the summary mentions it: "Grinder 5 OEE is still below target — note that a corrective action plan is in progress (bearing replacement, due Friday)"

**Given** an action plan was recently verified (completed within last 7 days)
**When** the summary is generated and the asset's metric improved
**Then** the summary may note: "Grinder 5 OEE improved 5 points since bearing replacement last Monday"

**Technical Notes:**
- Query active action plans for assets that appear in today's action items
- Add to the `SummaryContext` object passed to the LLM
- Update the prompt template to incorporate action plan status

**Files to Create/Modify:**
- `apps/api/app/services/ai/smart_summary.py` - Add action plan context to prompt
