TEST SPEC START
story_id: 16-5-action-plans-dashboard
generated: 2026-02-12

test_specifications:

## AC1: Given the user navigates to `/action-plans`, When the page loads, Then all action plans are displayed grouped by status (Open, In Progress, Completed, Verified) And each plan shows: title, asset name, priority, owner, due date, days until due (or overdue indicator).

### 16-5-action-plans-dashboard-UNIT-001: Dashboard page renders grouped sections with correct status headers
### 16-5-action-plans-dashboard-UNIT-002: ActionPlanCard renders title, priority badge, owner, due date, and days-until-due
### 16-5-action-plans-dashboard-UNIT-003: ActionPlanCard shows "Plant-wide" when asset_id is null
### 16-5-action-plans-dashboard-UNIT-004: ActionPlanCard renders correct status badge color per status
### 16-5-action-plans-dashboard-UNIT-005: ActionPlanCard renders correct priority badge colors
### 16-5-action-plans-dashboard-UNIT-006: Dashboard page header shows "Action Plans" title with total active count badge
### 16-5-action-plans-dashboard-UNIT-007: Dashboard renders loading skeleton cards while fetching
### 16-5-action-plans-dashboard-UNIT-008: Dashboard renders empty state when no plans exist
### 16-5-action-plans-dashboard-UNIT-009: Dashboard renders error state with retry button on API failure
### 16-5-action-plans-dashboard-UNIT-010: Dashboard handles auth error when session is expired
### 16-5-action-plans-dashboard-UNIT-011: Dashboard groups plans correctly when some status groups are empty
### 16-5-action-plans-dashboard-UNIT-012: ActionPlanCard due-soon indicator shows amber text for plans due within 3 days
### 16-5-action-plans-dashboard-UNIT-013: ActionPlanCard shows "Due in 1 day" (singular) when due tomorrow
### 16-5-action-plans-dashboard-INT-001: useActionPlansDashboard hook fetches with auth token and page_size=100
### 16-5-action-plans-dashboard-INT-002: useActionPlansDashboard hook groups plans by status client-side
### 16-5-action-plans-dashboard-INT-003: Navigation sidebar shows "Action Plans" link in Operations group
### 16-5-action-plans-dashboard-INT-004: Action Plans sidebar link highlights when on /action-plans route

## AC2: Overdue highlighting (7 specs)
### 16-5-action-plans-dashboard-UNIT-014 through UNIT-020

## AC3: Detail view with updates and status changes (18 specs)
### 16-5-action-plans-dashboard-UNIT-021 through UNIT-038, INT-005 through INT-006

## AC4: Filter persistence in URL params (6 unit + 4 integration specs)
### 16-5-action-plans-dashboard-UNIT-039 through UNIT-044, INT-007 through INT-010

TEST SPEC END
