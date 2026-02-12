# Action Plans & Continuous Improvement - User Acceptance Testing

**Epic**: 16
**Version**: 1.0
**Generated**: 2026-02-12
**Stories Covered**: 6

---

## Overview

### What Was Built

Plant managers can now create structured action plans from investigation findings, tracking the full cycle from root cause identification through corrective action to verified fix. Active action plans appear as badges on morning report action cards, a dedicated Action Plans dashboard lets managers oversee all plans grouped by status, and the daily AI-generated summary automatically references active plans when discussing relevant assets.

### Who Should Test

A **Plant Manager** or **Operations Lead** who regularly uses the morning report, assigns follow-up investigations, and is responsible for tracking corrective and preventive actions across the plant floor.

### Time Estimate

45-60 minutes

---

## Prerequisites

### Before You Begin

1. **Environment**
   - URL: Your staging/UAT environment URL (e.g., `https://uat.yourapp.com`)
   - Browser: Chrome (recommended) or Firefox

2. **Test Account**
   - Log in with a Plant Manager account that has permission to assign follow-ups and create action plans
   - You need at least one other user account (e.g., an engineer) to simulate follow-up responses

3. **Test Data Setup**
   - At least one morning report should exist with action items for identifiable assets (e.g., "Grinder 5", "Packaging Line 2")
   - At least one follow-up investigation should be assigned and have a response from the assignee (status is not "assigned")
   - If no follow-ups with responses exist, create one: assign a follow-up from the morning report, then log in as the assignee and submit a response with investigation findings

4. **Clean State**
   - Note any existing action plans in the system before testing so you can distinguish your test data
   - Optionally, start with no action plans to get the cleanest test experience

---

## Test Scenarios

### Scenario 1: Create an Action Plan from a Follow-Up Investigation

**Purpose**: Verify that a manager can create a structured action plan directly from a follow-up that has investigation findings, with key fields pre-populated from the follow-up context.

**Starting Point**: Morning report or follow-up list — find a follow-up that has a response from the assignee.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Open a follow-up that has received a response from the assigned engineer | The follow-up detail dialog opens showing the investigation response |
| 2 | Look for a "Create Action Plan" button on the follow-up detail | The button is visible because the follow-up has a response |
| 3 | Click "Create Action Plan" | An action plan creation form opens |
| 4 | Check the pre-filled fields in the form | The form is pre-populated with: the asset from the original action item, a description combining the action summary and the engineer's findings, and the root cause from the engineer's response |
| 5 | Fill in the remaining required fields: Title (edit the suggested title if desired), Category (corrective/preventive/improvement), Priority (low/medium/high/critical), and Due Date | The form accepts your entries without errors |
| 6 | Click Save/Submit | The action plan is created successfully; the form closes |
| 7 | Look at the follow-up detail again | A link to the newly created action plan is now visible on the follow-up, and the "Create Action Plan" button is no longer shown |

**Success Criteria**: An action plan is created from a follow-up with pre-populated context, and the follow-up now shows the linked plan.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 2: Verify the "Create Action Plan" Button Only Appears When Appropriate

**Purpose**: Confirm that the button to create an action plan does not appear on follow-ups that have no response yet.

**Starting Point**: Morning report or follow-up list.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Find a follow-up that is still in "assigned" status (no response received yet) | You can identify it by its status label |
| 2 | Open the follow-up detail | The follow-up detail dialog opens |
| 3 | Look for a "Create Action Plan" button | The button is NOT shown — it only appears once the assignee has responded |
| 4 | Now open a follow-up that already has a linked action plan (from Scenario 1) | The follow-up detail shows a link to the action plan instead of a "Create Action Plan" button |

**Success Criteria**: The "Create Action Plan" button only appears on follow-ups with responses and disappears once a plan is linked.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 3: View the Action Plans Dashboard

**Purpose**: Verify that the Action Plans dashboard displays all plans grouped by status with correct information.

**Starting Point**: The main navigation sidebar.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Click "Action Plans" in the sidebar navigation | The Action Plans dashboard page loads at `/action-plans` |
| 2 | Review the page layout | Plans are grouped into sections by status: Open, In Progress, Completed, and Verified |
| 3 | Look at the action plan you created in Scenario 1 | It appears in the "Open" section with its title, asset name, priority, your name as owner, due date, and days until due |
| 4 | Check the count in each section header | The section headers show the correct number of plans in each status group (e.g., "Open (1)") |
| 5 | If no plans exist in some status groups | Those sections are either hidden or show an appropriate empty indicator |

**Success Criteria**: The dashboard correctly displays all action plans organized by status with accurate details.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 4: Use Dashboard Filters

**Purpose**: Verify that filters on the Action Plans dashboard work correctly and their state is preserved in the URL.

**Starting Point**: The Action Plans dashboard (`/action-plans`).

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Use the Status filter to select "Open" | Only action plans with "Open" status are displayed |
| 2 | Check the browser address bar | The URL includes a query parameter like `?status=open` |
| 3 | Use the Priority filter to select "High" | Only plans matching both the status and priority filters are shown |
| 4 | Copy the URL and open it in a new browser tab | The same filtered view loads with the same filters applied |
| 5 | Clear all filters (select "All" or reset) | All action plans reappear, grouped by status |

**Success Criteria**: Filters narrow down the displayed plans correctly and the filter state persists in the URL.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 5: View Action Plan Details and Add Progress Updates

**Purpose**: Verify that clicking a plan card opens its full detail view and that a user can add progress updates and change the plan status.

**Starting Point**: The Action Plans dashboard with at least one plan visible.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Click on an action plan card | A detail dialog opens showing the full plan information |
| 2 | Review the detail view | It displays: title, full description, root cause, corrective action, preventive action (if any), asset info, priority, owner, due date, and creation date |
| 3 | If the plan was created from a follow-up, look for a "View Source Follow-Up" link | The link is present and clicking it would navigate to the original follow-up |
| 4 | Find the "Add Update" section in the detail view | A text input area is available for adding progress notes |
| 5 | Type a progress update (e.g., "Ordered replacement parts, expected delivery Thursday") and submit it | The update appears in the progress timeline below with your name and a timestamp |
| 6 | Click "Mark In Progress" (or the appropriate status change button) | The plan status changes to "In Progress" and a status change entry appears in the timeline (e.g., "Status: open → in_progress") |
| 7 | Close the detail dialog and return to the dashboard | The plan now appears in the "In Progress" section |

**Success Criteria**: A user can view complete plan details, add progress updates, and change the plan status — all reflected immediately in the UI.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 6: Complete and Verify an Action Plan

**Purpose**: Verify the full lifecycle of an action plan from in-progress through completion and verification.

**Starting Point**: An action plan in "In Progress" status (from Scenario 5).

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Open the in-progress action plan from the dashboard | The detail dialog opens showing the plan details |
| 2 | Add a progress update noting that the corrective action has been completed | The update appears in the timeline |
| 3 | Click "Mark Completed" | The plan status changes to "Completed" and the timeline records the status change |
| 4 | Close the detail, then reopen the plan from the "Completed" section | A "Verify" button is now available |
| 5 | Click "Verify" to confirm the fix was effective | The plan status changes to "Verified" with your name and the current date/time recorded as the verifier |
| 6 | Return to the dashboard | The plan now appears in the "Verified" section |

**Success Criteria**: An action plan moves through the complete lifecycle: Open → In Progress → Completed → Verified, with all transitions recorded.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 7: Active Plan Badge on Morning Report Action Cards

**Purpose**: Verify that when an asset has an active action plan, a badge appears on the corresponding morning report action card.

**Starting Point**: The morning report page with action items for assets that have active action plans.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to the morning report that includes an action item for an asset with an active action plan | The morning report loads with action cards |
| 2 | Find the action card for the asset that has an active plan | A badge is displayed on the card showing the action plan title, due date, and status (e.g., "Plan: Replace worn bearing (due Feb 14, in_progress)") |
| 3 | Click on the badge | You are navigated to the action plan detail view |
| 4 | Go back to the morning report and find an action card for an asset with NO active action plans | No action plan badge is shown on that card |
| 5 | If an asset has multiple active plans, check the badge | A summary badge appears (e.g., "2 active action plans") that can be expanded to see individual plan titles |

**Success Criteria**: Action cards show badges for active plans on their associated assets, and cards without active plans show no badge.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 8: Overdue Plan Highlighting

**Purpose**: Verify that overdue action plans are visually highlighted on the dashboard.

**Starting Point**: Create or have an action plan with a due date that has already passed (or change a plan's due date to yesterday).

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to the Action Plans dashboard | The dashboard loads |
| 2 | Look at the overdue plan (one with a due date in the past that is not Completed or Verified) | The plan card is highlighted in red and shows "X days overdue" (with the correct number of days) |
| 3 | Compare it to a plan that is due in the future | The non-overdue plan does not have red highlighting; if due within 3 days, it shows an amber "Due in X days" indicator |
| 4 | Check a completed or verified plan that has a past due date | It does NOT show as overdue, since the work is done |

**Success Criteria**: Overdue plans are clearly highlighted in red with accurate day counts, while completed/verified plans are not flagged as overdue.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

## Edge Cases & Error Handling

### Edge Case 1: AI Summary References Active Action Plans

**Purpose**: Verify that the daily AI-generated smart summary mentions active action plans when discussing relevant assets.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Ensure an asset (e.g., "Grinder 5") has an active action plan with a meaningful title and due date | The plan exists in the system |
| 2 | Generate or view the smart summary for a date where that asset appears in the action items | The summary mentions the active action plan in context (e.g., "Grinder 5 OEE is still below target — note that a corrective action plan is in progress (bearing replacement, due Friday)") |
| 3 | If no AI service is available (fallback mode), check the fallback summary | The fallback summary includes a brief note about the action plan next to the relevant asset entry |

**Result**: ☐ Pass  ☐ Fail

---

### Edge Case 2: Empty Dashboard State

**Purpose**: Verify the dashboard handles having zero action plans gracefully.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to the Action Plans dashboard when no action plans exist | The page loads without errors and displays a message like "No action plans found. Create action plans from follow-up investigations." |
| 2 | Apply a filter that matches no plans | The same empty state message appears; no errors or blank screens |

**Result**: ☐ Pass  ☐ Fail

---

### Edge Case 3: Summary Generates Normally Without Action Plans

**Purpose**: Verify that the smart summary works correctly even when no action plans exist in the system.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Generate a smart summary for a date where no action plans exist for any assets | The summary generates normally without errors — it simply does not mention action plans |
| 2 | The summary covers all other sections (safety, productivity, financial) as usual | No missing sections, no error messages, no degradation in summary quality |

**Result**: ☐ Pass  ☐ Fail

---

## Success Criteria Summary

This epic is **successful** when a user can:

- [ ] Create an action plan from a follow-up investigation with pre-populated fields
- [ ] See the linked action plan on the follow-up detail (and the "Create" button disappears)
- [ ] View all action plans on a dedicated dashboard grouped by status (Open, In Progress, Completed, Verified)
- [ ] Filter action plans by status, priority, asset, and owner — with filters preserved in the URL
- [ ] Open a plan detail view showing full information, root cause, corrective/preventive actions, and progress timeline
- [ ] Add progress updates and change a plan's status through the full lifecycle (Open → In Progress → Completed → Verified)
- [ ] See active action plan badges on morning report action cards for assets with open/in-progress plans
- [ ] See overdue plans highlighted in red with accurate "X days overdue" indicators
- [ ] See the AI smart summary reference active action plans when discussing affected assets
- [ ] Use the system normally when no action plans exist (no errors, graceful empty states)

**Minimum passing**: All checkboxes marked

---

## Issues Log

| # | Scenario | Issue Description | Severity | Screenshot |
|---|----------|-------------------|----------|------------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

### Severity Definitions

- **Critical**: Blocks core functionality, cannot proceed
- **Major**: Significant issue but workaround exists
- **Minor**: Cosmetic or minor inconvenience

---

## Sign-off

### Testing Summary

| Metric | Value |
|--------|-------|
| Scenarios Tested | \_\_ / 8 |
| Scenarios Passed | \_\_ / 8 |
| Edge Cases Tested | \_\_ / 3 |
| Edge Cases Passed | \_\_ / 3 |
| Critical Issues | |
| Major Issues | |
| Minor Issues | |

### Recommendation

☐ **Accept** - All criteria met, ready for production
☐ **Accept with conditions** - Minor issues noted, can proceed
☐ **Reject** - Critical/major issues must be resolved

### Signatures

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Tester | | | |
| Product Owner | | | |
| Tech Lead | | | |

---

## Appendix

### Test Data Reference

| Data Item | Description | Example |
|-----------|-------------|---------|
| Asset with action plan | An asset that has at least one active action plan | "Grinder 5" with plan "Replace worn bearing" |
| Follow-up with response | A follow-up investigation where the assignee has submitted findings | Follow-up on "Grinder 5" downtime with root cause "Worn bearing detected" |
| Overdue plan | An action plan with a due date in the past and status not completed/verified | Any plan with due_date < today and status = "open" or "in_progress" |
| Multiple plans for one asset | An asset with 2+ active plans to test the summary badge | "Packaging Line 2" with plans for "Seal replacement" and "Temperature calibration" |

### Environment Details

| Detail | Value |
|--------|-------|
| Application | TFN AI Hub |
| Epic | 16 - Action Plans & Continuous Improvement |
| Backend | FastAPI (Python) with Supabase PostgreSQL |
| Frontend | Next.js 14 with TypeScript, Tailwind CSS, Shadcn/UI |
| Key API Endpoints | `GET/POST /api/v1/action-plans`, `PATCH /api/v1/action-plans/{id}`, `POST /api/v1/action-plans/{id}/updates`, `POST /api/v1/action-plans/{id}/verify` |
| Dashboard Route | `/action-plans` |

### Related Documentation

- Epic: `_bmad-output/planning-artifacts/epic-16.md`
- Stories: `_bmad-output/implementation-artifacts/stories/16-*.md`

---

*Generated by BMAD epic-execute workflow*
