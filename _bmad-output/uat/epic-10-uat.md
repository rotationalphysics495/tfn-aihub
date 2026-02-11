# Bug Fixes & Data Quality - User Acceptance Testing

**Epic**: 10
**Version**: 1.0
**Generated**: 2026-02-11
**Stories Covered**: 3

---

## Overview

### What Was Built

Three broken features in the plant management dashboard have been fixed. Safety alerts were failing to load due to an authentication error. The live production pulse view was crashing because it tried to read data columns that don't exist. The cost-of-loss financial view was returning incorrect ($0) values because it referenced a wrong column name. All three issues are now resolved so the dashboard and morning reports work end-to-end.

### Who Should Test

A Plant Manager or Shift Supervisor who regularly uses the dashboard to monitor safety alerts, live production status, and financial loss reports. No technical knowledge is required — you only need a login and access to the standard dashboard.

### Time Estimate

20–30 minutes

---

## Prerequisites

### Before You Begin

1. **Environment**
   - URL: Your staging/UAT environment URL (e.g., `https://uat.tfn-aihub.app`)
   - Browser: Chrome (recommended) or Firefox

2. **Test Account**
   - Use your standard Plant Manager test account
   - You must be logged in before starting each scenario
   - If your session expires, log in again — this is expected behavior

3. **Test Data Setup**
   - The environment should have seed data loaded, including:
     - At least one active safety alert/event
     - At least two production assets with recent live snapshot data
     - At least one day of daily summary data with waste counts and financial loss values
   - If no data exists, ask your administrator to run the seed data script

4. **Clean State**
   - No special reset is needed between scenarios
   - If you acknowledged a safety alert during testing and need to re-test, ask your administrator to reset alert status

---

## Test Scenarios

### Scenario 1: Safety Alerts Load on Dashboard

**Purpose**: Verify that safety alerts appear on the dashboard without errors after the authentication fix.

**Starting Point**: Logged into the application, viewing the main dashboard.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Log in with your Plant Manager credentials | You are taken to the main dashboard |
| 2 | Look at the safety alerts section of the dashboard | Safety alerts load and display without any error message |
| 3 | Verify that alert details are visible (event type, description, timestamp) | Each alert shows meaningful information — not blank or "undefined" |
| 4 | Check that no red error banner or "403 Forbidden" message appears | The page loads cleanly with no error notifications |

**Success Criteria**: Safety alerts section displays active safety events with no errors.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 2: Acknowledge a Safety Alert

**Purpose**: Verify that acknowledging a safety alert works without errors after the authentication fix.

**Starting Point**: Dashboard is open with at least one active (unacknowledged) safety alert visible.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Find an active safety alert on the dashboard | An unacknowledged alert is visible |
| 2 | Click the acknowledge button (or equivalent action) on the alert | The system accepts the acknowledgement without errors |
| 3 | Verify the alert status updates | The alert is marked as acknowledged (visual indicator changes) |
| 4 | Refresh the page | The acknowledged alert retains its new status |

**Success Criteria**: A safety alert can be acknowledged successfully and the status persists after refresh.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 3: Live Production Pulse View Loads

**Purpose**: Verify that the live pulse view displays real-time production data without crashing.

**Starting Point**: Logged in to the application.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to the Live Pulse view (production overview) | The page loads without a server error or blank screen |
| 2 | Look at the list of production assets | Each asset shows a status (e.g., on target, behind, ahead) |
| 3 | Verify production numbers are displayed for each asset | Current output and target output values are shown (numbers, not blank or "N/A") |
| 4 | Check the financial loss column | Financial loss values display as dollar amounts (e.g., "$0.00" or a positive value) |

**Success Criteria**: The live pulse view loads successfully and shows production data for all assets.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 4: Live Pulse OEE Displays Gracefully

**Purpose**: Verify that the OEE (Overall Equipment Effectiveness) field handles missing data without breaking the page.

**Starting Point**: Live Pulse view is open.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Look at the OEE metric on the live pulse view | The OEE field displays a value (may show "0%" or "N/A" if no OEE data is available) |
| 2 | Verify the page does not crash or show an error | The rest of the production data displays correctly regardless of OEE value |
| 3 | Check multiple assets if available | All assets show consistent OEE handling (no random errors on some assets) |

**Success Criteria**: OEE is shown gracefully (a default value or placeholder) and does not cause page errors.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 5: Cost of Loss View Loads with Financial Data

**Purpose**: Verify that the cost-of-loss view returns correct financial impact data after the column name fix.

**Starting Point**: Logged in to the application.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to the Cost of Loss view (financial section) | The page loads without a server error |
| 2 | Look at the waste cost breakdown | Waste-related costs display as dollar amounts, not "$0.00" (assuming waste data exists) |
| 3 | Check the overall financial loss total | The total includes waste loss as part of the calculation |
| 4 | If a date range filter is available, select a range with known production data | The financial figures update to reflect the selected period |

**Success Criteria**: Cost-of-loss data loads correctly and waste costs are reflected in the financial breakdown.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 6: Financial Summary Includes Waste Data

**Purpose**: Verify that the financial summary endpoint returns correct waste counts after the fix.

**Starting Point**: Logged in to the application.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to any view that shows a financial summary (e.g., morning report, dashboard summary) | The summary loads without errors |
| 2 | Look for a "Total Waste" or "Waste Count" field | The value is a number greater than zero (assuming waste data exists in the test environment) |
| 3 | Verify the total financial impact figure | The total reflects contributions from downtime, waste, and other loss categories |

**Success Criteria**: Financial summary shows non-zero waste counts and accurate total financial impact.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

## Edge Cases & Error Handling

### Scenario 7: Session Expiry During Dashboard Use

**Purpose**: Verify that an expired session is handled gracefully rather than showing confusing errors.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Log in and navigate to the dashboard so safety alerts are visible | Alerts load normally |
| 2 | Wait for your session to expire (or manually clear your session/token if possible) | — |
| 3 | Trigger a refresh or wait for the automatic data poll | You are redirected to the login page or see a clear "Session expired — please log in again" message |
| 4 | Verify no "403 Forbidden" or technical error is shown | The error message is user-friendly |

**Result**: ☐ Pass  ☐ Fail

---

### Scenario 8: Views Handle Empty Data Gracefully

**Purpose**: Verify that all three fixed views handle the case where no data exists without crashing.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | If possible, access the views with a date range or filter that returns no data | — |
| 2 | Check the safety alerts section when no active alerts exist | Shows an empty state message (e.g., "No active alerts") — not an error |
| 3 | Check the live pulse view when no snapshot data exists | Shows an empty state or placeholder — not a server error |
| 4 | Check the cost-of-loss view when no financial data exists for the period | Shows "$0.00" or an empty state — not a server error |

**Result**: ☐ Pass  ☐ Fail

---

## Success Criteria Summary

This epic is **successful** when a user can:

- [ ] View safety alerts on the dashboard without 403 errors
- [ ] Acknowledge a safety alert without errors
- [ ] Load the live production pulse view and see asset statuses, output, and financial loss data
- [ ] See OEE displayed gracefully (default value when unavailable, no errors)
- [ ] Load the cost-of-loss view with accurate waste costs (non-zero when waste data exists)
- [ ] View financial summaries that correctly include waste count data
- [ ] Experience user-friendly messages on session expiry (no raw 403 errors)
- [ ] See graceful empty states when no data is available (no server errors)

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

| Data Needed | Source | Notes |
|---|---|---|
| Active safety alerts | Seed data or manually created alerts | At least 1 unacknowledged alert required for Scenario 2 |
| Live snapshot data | Seed data (`live_snapshots` table) | At least 2 assets with recent snapshots |
| Daily summary data | Seed data (`daily_summaries` table) | Must include `waste_count > 0` for cost-of-loss validation |

### Environment Details

| Detail | Value |
|---|---|
| Application | TFN AI Hub |
| Epic | 10 — Bug Fixes & Data Quality |
| Stories | 10.1 Safety Alerts Auth Fix, 10.2 Live Pulse Schema Fix, 10.3 Cost of Loss Schema Fix |
| Backend | Python FastAPI with Supabase |
| Frontend | Next.js with React |

### Related Documentation

- Epic: `_bmad-output/planning-artifacts/epic-10.md`
- Stories: `_bmad-output/implementation-artifacts/stories/10-*.md`

---

*Generated by BMAD epic-execute workflow*
