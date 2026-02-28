# Report History & Shift Granularity - User Acceptance Testing

**Epic**: 17
**Version**: 1.0
**Generated**: 2026-02-12
**Stories Covered**: 4

---

## Overview

### What Was Built

Plant managers can now navigate to any past date's morning report using a date picker, view AI-generated smart summaries for historical dates on demand, and drill down into shift-level performance data (Morning, Afternoon, Night) to identify which shift caused a production miss. Report links are shareable via URL for use in team meetings or incident reviews.

### Who Should Test

A Plant Manager or Operations Lead who regularly uses the Morning Report to review daily production performance. The tester should be familiar with the existing Morning Report layout, workcenter scorecard, and action items. No technical knowledge is required.

### Time Estimate

45–60 minutes

---

## Prerequisites

### Before You Begin

1. **Environment**
   - URL: `http://localhost:3000` (or your staging/UAT environment URL)
   - Browser: Chrome (recommended) or Firefox

2. **Test Account**
   - Use your existing plant manager login credentials
   - Or: Ask your administrator for a test account with plant manager access

3. **Test Data Setup**
   - The system should have production data for at least 7 past days (seed data covers this)
   - At least one historical date should have no smart summary pre-generated
   - Shift-level data (Morning, Afternoon, Night) should exist for the past 7 days
   ```bash
   # If starting from a fresh database, run the seed script
   npm run seed
   ```

4. **Clean State**
   - Open the Morning Report page (`/morning-report`) and confirm it loads with yesterday's data before starting tests
   - If testing summary generation, ensure at least one older date (e.g., 5+ days ago) has no pre-existing smart summary

---

## Test Scenarios

### Scenario 1: View Yesterday's Report (Default Behavior)

**Purpose**: Confirm the Morning Report still works as before — loading yesterday's data by default with the new date picker visible.

**Starting Point**: Log in and navigate to the Morning Report page (`/morning-report`).

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to `/morning-report` (no date in the URL) | The Morning Report page loads with yesterday's production data |
| 2 | Look at the header area near the top of the report | A date picker is visible showing yesterday's date (e.g., "Feb 11, 2026"). A badge reading "T-1 Data" appears nearby |
| 3 | Check the URL in the browser address bar | The URL may or may not include `?date=...` — either way, the report shows yesterday's data |
| 4 | Review the workcenter scorecard, action items, and smart summary sections | All sections display data consistent with yesterday's production performance |

**Success Criteria**: The Morning Report loads with yesterday's data by default, the date picker is visible, and all report sections display correctly.

**Result**: ☒ Pass

**Notes**: All steps pass.

---

### Scenario 2: Navigate to a Historical Date Using the Date Picker

**Purpose**: Verify that the date picker allows navigation to any past date and all report sections update accordingly.

**Starting Point**: Morning Report page showing yesterday's data.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Click the date picker button (showing the current date like "Feb 11, 2026") | A calendar popup opens |
| 2 | Select a date from 5 days ago on the calendar | The calendar closes. All report sections (workcenter scorecard, action items, smart summary) reload with data for the selected date |
| 3 | Check the badge that previously read "T-1 Data" | The badge now shows the selected date (e.g., "Feb 6 Data") |
| 4 | Check the URL in the browser address bar | The URL has updated to include `?date=2026-02-06` (or whichever date you selected) |
| 5 | Try to select today's date or a future date on the calendar | Today and future dates are grayed out and cannot be selected |

**Success Criteria**: Selecting a historical date reloads all report sections with that date's data, updates the badge text, and updates the URL.

**Result**: ☒ Pass

**Notes**: All steps pass.

---

### Scenario 3: Navigate Using Prev/Next Day Arrows

**Purpose**: Verify the arrow buttons step through dates one day at a time and the "next" arrow is properly disabled.

**Starting Point**: Morning Report page showing yesterday's data.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Look for left and right arrow buttons near the date picker | Two arrow buttons (‹ and ›) are visible on either side of the date picker |
| 2 | Look at the right arrow (next day) | The right arrow is disabled/grayed out because you are already viewing yesterday (you cannot go forward to today) |
| 3 | Click the left arrow (previous day) | The report reloads with data for 2 days ago. The date picker updates. The URL updates |
| 4 | Click the left arrow again | The report reloads with data for 3 days ago |
| 5 | Click the right arrow (next day) | The right arrow is now enabled. Clicking it returns to 2 days ago |
| 6 | Keep clicking the right arrow until you reach yesterday's date | The right arrow becomes disabled again once you reach yesterday |

**Success Criteria**: Arrow buttons navigate one day at a time, and the "next" arrow is disabled when viewing yesterday's date.

**Result**: ☒ Pass

**Notes**: All steps pass.

---

### Scenario 4: Share a Report Link via URL

**Purpose**: Confirm that report URLs with a date parameter are shareable and load the correct date when opened directly.

**Starting Point**: Morning Report page showing any historical date (e.g., Feb 6).

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Copy the full URL from the browser address bar (e.g., `http://localhost:3000/morning-report?date=2026-02-06`) | URL is copied |
| 2 | Open a new browser tab (or incognito window) and paste the URL | The Morning Report loads directly with Feb 6 data |
| 3 | Verify the date picker shows "Feb 6, 2026" | The date picker reflects the URL date |
| 4 | Verify the badge reads "Feb 6 Data" | Badge matches the selected date |
| 5 | Verify the workcenter scorecard and action items show Feb 6 data | All sections are consistent with the date in the URL |

**Success Criteria**: A URL with a `?date=` parameter loads the correct historical report when opened directly.

**Result**: ☒ Pass

**Notes**: All steps pass.

---

### Scenario 5: Generate a Smart Summary for a Historical Date

**Purpose**: Verify that users can generate an AI smart summary on demand for historical dates that do not already have one.

**Starting Point**: Navigate to a historical date that has production data but no pre-existing smart summary (e.g., a date from 5–7 days ago that has not been viewed before).

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Use the date picker to navigate to the target historical date | The report loads. The workcenter scorecard and action items show data for that date |
| 2 | Scroll to the Smart Summary section | Instead of a summary, you see a message: "No summary exists for this date. Generate one?" with a "Generate Summary" button |
| 3 | Click the "Generate Summary" button | A loading indicator appears while the AI summary is being generated |
| 4 | Wait for generation to complete (may take a few seconds) | The summary appears in the normal summary section with formatted text |
| 5 | Navigate away to a different date and then return to the same date | The previously generated summary is displayed immediately — no generation prompt |

**Success Criteria**: Users can generate smart summaries on demand for historical dates, and generated summaries are saved for future visits.

**Result**: ☒ Fail

**Notes**: Steps 1–4 pass. Step 5 fails — **Issue #1**: After navigating away and returning to the same date, the generated summary carries over from the most recently generated date. For example, a summary generated on 2/27 appears on 2/26, 2/25, and so on until the summary is manually regenerated for each date. The system does not correctly scope the displayed summary to the selected date. See Issues Log.

---

### Scenario 6: Regenerate an Existing Smart Summary

**Purpose**: Verify that an existing smart summary can be regenerated (refreshed) on demand.

**Starting Point**: Navigate to a date that already has a smart summary (e.g., yesterday, or the date from Scenario 5).

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | View the Smart Summary section — it should display a summary | Summary text is visible |
| 2 | Look for a "Regenerate" button (refresh icon) near the summary | A regenerate button is visible |
| 3 | Click the "Regenerate" button | A loading indicator appears. After a few seconds, the summary refreshes with potentially updated text |
| 4 | Verify the regenerated summary is now displayed | New summary text appears in the same section |

**Success Criteria**: Existing summaries can be regenerated on demand and the refreshed version replaces the old one.

**Result**: ☒ Pass

**Notes**: All steps pass.

---

### Scenario 7: View Shift-Level Breakdown on Workcenter Scorecard

**Purpose**: Verify that the workcenter scorecard shows per-shift performance data and the shift tabs filter the view.

**Starting Point**: Morning Report page for any date that has shift data (e.g., yesterday or a recent date).

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Look at the workcenter scorecard section | A set of tabs appears above or near the scorecard: "All", "Morning", "Afternoon", "Night" |
| 2 | Confirm "All" tab is selected by default | The scorecard shows the daily aggregate data (same as before this feature was added) |
| 3 | Click the "Morning" tab | The scorecard updates to show only Morning shift metrics (output, OEE, downtime) for each workcenter |
| 4 | Click the "Afternoon" tab | The scorecard updates to show Afternoon shift metrics |
| 5 | Click the "Night" tab | The scorecard updates to show Night shift metrics |
| 6 | Click the "All" tab again | The scorecard returns to the daily aggregate view |

**Success Criteria**: Shift tabs filter the workcenter scorecard to show per-shift or aggregate data as selected.

**Result**: ☒ Pass

**Notes**: All steps pass.

---

### Scenario 8: Shift Attribution on Action Items

**Purpose**: Verify that action items display which shift caused a production miss when one shift is primarily responsible, and show no shift attribution for systemic issues.

**Starting Point**: Morning Report page for any date with shift data. "All" tab selected.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Review the action items (insight cards) in the report | Action items are listed with recommendations |
| 2 | Look for action items that show a shift badge (e.g., "Afternoon Shift") | Some items that had a miss concentrated in one shift display a shift attribution badge (e.g., "afternoon shift — 58 min downtime") |
| 3 | Look for action items without a shift badge | Items where all three shifts missed target similarly (systemic issue) do not show shift attribution |
| 4 | Click a shift tab (e.g., "Afternoon") | The action items filter to show only items attributed to the Afternoon shift, plus any systemic (unattributed) items |
| 5 | Click "All" tab | All action items return to view |

**Success Criteria**: Action items correctly show shift attribution when one shift is primarily responsible and omit it for systemic issues. Shift tab filtering applies to both the scorecard and action items.

**Result**: ☒ Fail

**Notes**: Steps 1–3 pass (shift attribution badge visible on Grinder 5 — night shift 50 min). Step 4 fails — **Issue #2**: Clicking a shift tab (e.g., "Afternoon") does not filter the action items list; all items remain visible regardless of the selected shift tab. Step 5 is dependent on Step 4 and could not be meaningfully verified.

---

## Edge Cases & Error Handling

### Empty State: No Data for Selected Date

**Purpose**: Verify the system handles dates with no production data gracefully.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Use the date picker to navigate to a very old date unlikely to have data (e.g., Jan 1, 2025) | The page shows an empty state message: "No production data available for Jan 1, 2025" |
| 2 | Verify the date picker and arrow buttons still work | The date picker and arrows remain interactive — you can navigate to other dates |
| 3 | Navigate back to yesterday using the arrow buttons or date picker | The report loads normally with yesterday's data |

**Result**: ☒ Pass

**Notes**: All steps pass.

---

### Invalid URL Date Parameter

**Purpose**: Verify the system handles invalid date values in the URL gracefully.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Manually type an invalid date in the URL: `/morning-report?date=not-a-date` | The page loads with yesterday's data (graceful fallback) |
| 2 | Try a future date in the URL: `/morning-report?date=2027-01-01` | The page loads with yesterday's data (cannot view future dates) |
| 3 | Try an empty date parameter: `/morning-report?date=` | The page loads with yesterday's data |

**Result**: ☒ Pass

**Notes**: All steps pass.

---

### Summary Generation Failure

**Purpose**: Verify the system handles errors during summary generation without crashing.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to a historical date with no smart summary | The "Generate Summary" button appears |
| 2 | Disconnect from the network (turn off Wi-Fi or VPN) | (Preparation step) |
| 3 | Click "Generate Summary" | An error message appears (e.g., "Failed to generate summary") with a retry option |
| 4 | Reconnect to the network and click "Retry" | The summary generates successfully |
| 5 | Verify the page remained functional throughout the error | Date picker, arrows, and other sections still work during and after the error |

**Result**: ☒ Fail

**Notes**: Step 3 fails — **Issue #3**: After disconnecting from the network and clicking "Generate Summary", the page displayed "No production data available for yesterday" instead of the expected "Failed to generate summary" error message with a retry option. The error state is misleading — the absence of network connectivity manifests as an empty state message rather than a distinct generation failure error. Steps 4–5 could not be verified. The page itself remained navigable throughout.

---

## Success Criteria Summary

This epic is **successful** when a user can:

- [x] View any historical date's Morning Report by selecting a date from the date picker
- [x] Navigate day-by-day using prev/next arrow buttons, with the "next" arrow disabled at yesterday
- [x] Share a report URL (with `?date=` parameter) and have it load the correct date when opened
- [x] See an empty state message when a selected date has no production data
- [ ] Generate a smart summary on demand for a historical date that does not have one *(Issue #1 — summary carries over across dates)*
- [x] Regenerate an existing smart summary
- [x] Switch between shift views (All, Morning, Afternoon, Night) on the workcenter scorecard
- [x] See shift attribution on action items when one shift is primarily responsible for a miss
- [x] See no shift attribution for systemic issues affecting all shifts
- [ ] Use shift tab filtering to view both the scorecard and action items for a specific shift *(Issue #2 — action item filtering does not apply)*

**Minimum passing**: All checkboxes marked

---

## Issues Log

| # | Scenario | Issue Description | Severity |
|---|----------|-------------------|----------|
| 1 | Scenario 5 | **Summary carryover across dates**: A generated summary persists across all other historical dates until each is individually regenerated. Navigating from 2/27 to 2/26, 2/25, etc. displays the 2/27 summary instead of the correct date's summary or the "Generate" prompt. The `useSmartSummary` hook receives `reportDate` correctly but the displayed summary does not re-scope when the date changes. | Major |
| 2 | Scenario 8 Step 4 | **Shift tab does not filter action items**: Clicking "Morning", "Afternoon", or "Night" shift tabs filters the workcenter scorecard correctly but has no effect on the action items (insight cards) list — all cards remain visible regardless of shift selection. | Major |
| 3 | Edge Case 3 Step 3 | **Incorrect error message on network failure during summary generation**: When the network is disconnected and "Generate Summary" is clicked, the page shows "No production data available for yesterday" instead of a generation failure error with retry option. The error state does not distinguish between a missing-data empty state and a network/generation failure. | Minor |

### Severity Definitions

- **Critical**: Blocks core functionality, cannot proceed
- **Major**: Significant issue but workaround exists
- **Minor**: Cosmetic or minor inconvenience

---

## Sign-off

### Testing Summary

| Metric | Value |
|--------|-------|
| Scenarios Tested | 8 / 8 |
| Scenarios Passed | 6 / 8 |
| Edge Cases Tested | 3 / 3 |
| Edge Cases Passed | 2 / 3 |
| Critical Issues | 0 |
| Major Issues | 2 |
| Minor Issues | 1 |

### Recommendation

☐ **Accept** - All criteria met, ready for production
☒ **Accept with conditions** - Minor issues noted, can proceed
☐ **Reject** - Critical/major issues must be resolved

> **Conditions**: Issues #1 (summary carryover) and #2 (shift tab action item filtering) must be resolved before production release. Issue #3 (misleading error message) to be addressed in a follow-up. Core date navigation, scorecard shift filtering, URL sharing, and shift attribution badge are all functioning correctly.

### Signatures

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Tester | Dmitri Spiropoulos | 2026-02-28 | QA |
| Product Owner | | | |
| Tech Lead | | | |

---

## Appendix

### Test Data Reference

- **Assets with shift data**: Roaster 1, Roaster 2, Grinder 1–3, Grinder 5, Filler Line A, Packaging Line 1 (8 assets total)
- **Shift names**: Morning, Afternoon, Night
- **Date range with seed data**: Past 7 days plus today
- **Shift distribution pattern**: Morning ~35-40% output, Afternoon ~30-35%, Night ~25-30%
- **Shift attribution threshold**: A single shift must account for >60% of total downtime to receive attribution
- **UAT override**: Grinder 5 daysAgo(1) seeded with night shift at 50/72 min downtime (69%) to ensure attribution badge is visible in Scenario 8

### Environment Details

- **Frontend**: Next.js 14 App Router at `http://localhost:3000`
- **API**: FastAPI at `http://localhost:8000`
- **Database**: Supabase (PostgreSQL) with `shift_summaries` table alongside `daily_summaries`
- **Key URL pattern**: `/morning-report?date=YYYY-MM-DD`

### Related Documentation

- Epic: `_bmad-output/planning-artifacts/epic-17.md`
- Stories: `_bmad-output/implementation-artifacts/stories/17-*.md`

---

*Generated by BMAD epic-execute workflow*
