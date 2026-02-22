# Workcenter Production Scorecard - User Acceptance Testing

**Epic**: 11
**Version**: 1.1
**Generated**: 2026-02-11
**Stories Covered**: 3

---

## Overview

### What Was Built

Plant managers can now see a production scorecard on the Morning Report page that shows how much each workcenter (Roasting, Grinding, Filling, Packaging) produced compared to its target. Each workcenter row can be expanded to see individual machine performance. The scorecard uses color coding — green, yellow, and red — so you can absorb the whole plant's status in about 5 seconds.

### Who Should Test

A Plant Manager or Operations Lead who regularly reviews the Morning Report. No technical knowledge is required — you just need familiarity with workcenter names and what "hitting target" means for production.

### Time Estimate

20–30 minutes

---

## Prerequisites

### Before You Begin

1. **Environment**
   - URL: Your staging/test environment URL (e.g., `https://staging.tfn-aihub.app`)
   - Browser: Chrome (recommended) or Firefox

2. **Test Account**
   - Use your existing test account credentials
   - Or: Ask your administrator for a test login with access to the Morning Report

3. **Test Data Setup**
   - Seed data must be loaded so production numbers exist for yesterday's date
   - If the scorecard appears empty, ask a developer to run the seed script:
     ```bash
     node scripts/seed-data.mjs
     ```

4. **Clean State**
   - No special reset is needed between test runs
   - If re-testing after a data change, refresh the Morning Report page

---

## Test Scenarios

### Scenario 1: Scorecard Appears on the Morning Report

**Purpose**: Confirm the production scorecard is visible and positioned correctly on the Morning Report page.

**Starting Point**: You are logged in and on the home page.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to the Morning Report page | The Morning Report page loads successfully |
| 2 | Look for a section titled "Production Scorecard" | A "Production Scorecard" section is visible on the page |
| 3 | Confirm where the scorecard sits relative to other sections | The scorecard appears below the Morning Summary section and above the Action Items list |
| 4 | Count the number of workcenter rows displayed | You see exactly 4 rows: Roasting, Grinding, Filling, and Packaging |

**Success Criteria**: The Production Scorecard section is visible with all 4 workcenters listed, positioned between the Morning Summary and Action Items.

**Result**: ☑ Pass  ☐ Fail

**Notes**: All 4 workcenter rows (Roasting, Grinding, Filling, Packaging) visible and correctly positioned.

---

### Scenario 2: Workcenter Row Shows Key Production Numbers

**Purpose**: Verify that each workcenter row displays actual output, target, attainment percentage, and asset count.

**Starting Point**: The Morning Report page is loaded and the Production Scorecard is visible.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Look at any workcenter row (e.g., Grinding) | You see the workcenter name displayed in bold |
| 2 | Check for production numbers | Actual output and target are shown side-by-side (e.g., "9,450 / 9,750") with comma-formatted numbers |
| 3 | Check for attainment percentage | A large percentage number is displayed (e.g., "96.9%"), and it is the most prominent number in the row |
| 4 | Check for asset count | An asset summary is shown (e.g., "3 of 5 assets on target") |
| 5 | Repeat for all 4 workcenter rows | Every row shows workcenter name, actual/target, attainment %, and asset count |

**Success Criteria**: All 4 workcenter rows display their name, actual vs. target output, attainment percentage, and how many assets hit vs. missed target.

**Result**: ☑ Pass  ☐ Fail

**Notes**: All fields present and correctly formatted across all 4 workcenter rows.

---

### Scenario 3: Color Coding Reflects Performance

**Purpose**: Verify that attainment percentages are color-coded so you can instantly see which workcenters are doing well and which need attention.

**Starting Point**: The Morning Report page is loaded and the Production Scorecard is visible.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Find a workcenter with attainment at or above 95% | The attainment percentage is displayed in **green** |
| 2 | Find a workcenter with attainment between 85% and 94% | The attainment percentage is displayed in **yellow/amber** |
| 3 | Find a workcenter with attainment below 85% | The attainment percentage is displayed in **red** |
| 4 | Visually scan all 4 rows at once | You can tell at a glance which workcenters are on track (green), borderline (yellow), or behind (red) without reading the numbers |

**Success Criteria**: Color coding correctly matches performance — green for 95%+, yellow for 85–94%, red for below 85% — and the colors are immediately noticeable.

**Result**: ☑ Pass  ☐ Fail

**Notes**: Color coding correct and immediately distinguishable across all rows.

---

### Scenario 4: Expanding a Workcenter Shows Asset Details

**Purpose**: Confirm that clicking a workcenter row reveals a breakdown of individual machine performance.

**Starting Point**: The Morning Report page is loaded with all workcenter rows collapsed (no detail visible).

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Click on the "Grinding" workcenter row | The row expands to show a table of individual assets (machines) within Grinding |
| 2 | Review the detail table columns | The table shows: Asset Name, Actual vs. Target, OEE %, and Downtime Minutes for each asset |
| 3 | Check the color coding on asset rows | Assets that hit their target have a **green** background tint; assets that missed have a **red** background tint |
| 4 | Click the "Grinding" row again | The detail table collapses and is hidden |
| 5 | Click on a different workcenter (e.g., "Filling") | That workcenter's asset detail table expands and displays correctly |

**Success Criteria**: Clicking a workcenter row toggles the asset detail table open and closed. The table shows per-asset performance with green/red color coding for hit/miss.

**Result**: ☑ Pass  ☐ Fail

**Notes**: Expand/collapse works correctly. Asset detail table displays all columns with correct green/red row tinting.

---

### Scenario 5: Asset Detail Numbers Are Accurate and Readable

**Purpose**: Verify the per-asset breakdown shows realistic, well-formatted data.

**Starting Point**: A workcenter row is expanded, showing the asset detail table.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Check that each asset in the expanded table has a name | Each row shows a recognizable asset name (e.g., "Grinder 1", "Filler Line A") |
| 2 | Check actual vs. target numbers | Numbers are comma-formatted (e.g., "1,850 / 1,950") and make sense for a production environment |
| 3 | Check OEE percentage | An OEE percentage is shown (e.g., "88.5%") or a dash if unavailable |
| 4 | Check downtime minutes | Downtime is displayed as a number of minutes (e.g., "35") or a dash if unavailable |
| 5 | Verify asset count matches the workcenter header | The number of asset rows in the detail table matches the asset count shown in the workcenter summary row |

**Success Criteria**: Asset detail data is present, correctly formatted, and the number of assets matches the workcenter header count.

**Result**: ☑ Pass  ☐ Fail

**Notes**: Asset names, formatted numbers, OEE %, and downtime all display correctly. Asset counts match workcenter header.

---

### Scenario 6: Scorecard Is Readable on a Tablet

**Purpose**: Confirm the scorecard meets the glanceability requirement — text and numbers should be readable from about 3 feet away on a tablet.

**Starting Point**: Open the Morning Report on a tablet device (or resize your browser to tablet width, approximately 768px wide).

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | View the scorecard from about arm's length (3 feet) | The attainment percentages are large enough to read without squinting |
| 2 | Check the workcenter names | Names are bold and clearly readable |
| 3 | Check color coding visibility | Green, yellow, and red colors are clearly distinguishable |
| 4 | Tap on a workcenter row to expand it | The tap target is easy to hit (no mis-taps on a touchscreen) |
| 5 | Review the expanded detail table | Asset details are readable, though they may require being closer to the screen |

**Success Criteria**: Key scorecard numbers (especially attainment percentages and workcenter names) are readable from 3 feet away on a tablet, and touch interactions work reliably.

**Result**: ☑ Pass  ☐ Fail

**Notes**: Large attainment % numbers and bold workcenter names readable at arm's length. Touch targets adequate.

---

## Edge Cases & Error Handling

### No Data Available

**Purpose**: Verify the scorecard handles a date with no production data gracefully.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | If possible, navigate to the Morning Report for a date with no data (e.g., a future date or a date before the system was set up) | The scorecard section displays an empty state message (e.g., "No production data available") instead of crashing or showing a blank area |
| 2 | Verify the rest of the Morning Report page still works | Other sections (Morning Summary, Action Items) are not affected |

**Result**: ☑ Pass  ☐ Fail

**Notes**: Navigated to ?date=2024-01-01. Scorecard displayed "No production data available for this date." Other page sections unaffected.

---

### Slow Connection / Loading State

**Purpose**: Verify the scorecard shows a loading indicator while data is being fetched.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Refresh the Morning Report page (or simulate a slow connection using browser dev tools) | A loading skeleton or placeholder appears in the scorecard area while data loads |
| 2 | Wait for data to finish loading | The loading indicator is replaced by the actual scorecard data |

**Result**: ☑ Pass  ☐ Fail

**Notes**: Loading skeleton visible on page refresh before data populates.

---

### Page Refresh Consistency

**Purpose**: Verify the scorecard shows the same data on repeated page loads.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Note the attainment percentages for all 4 workcenters | Record the numbers |
| 2 | Refresh the page | The same 4 workcenters appear with the same attainment percentages |
| 3 | Refresh again | Data remains consistent |

**Result**: ☑ Pass  ☐ Fail

**Notes**: Attainment percentages consistent across multiple page refreshes.

---

## Success Criteria Summary

This epic is **successful** when a user can:

- [x] See a Production Scorecard on the Morning Report with all 4 workcenters (Roasting, Grinding, Filling, Packaging)
- [x] Read actual output vs. target and attainment percentage for each workcenter at a glance
- [x] Instantly distinguish good, borderline, and poor performance through green/yellow/red color coding
- [x] Click any workcenter to expand and see individual asset (machine) performance details
- [x] View the scorecard comfortably on a tablet from about 3 feet away
- [x] See a helpful empty state message when no data is available instead of errors or blank space

**Minimum passing**: All checkboxes marked

---

## Issues Log

| # | Scenario | Issue Description | Severity | Status |
|---|----------|-------------------|----------|--------|
| E11-001 | 4 (pre-fix) | Clicking workcenter row rendered error card instead of expanding asset detail (field name mismatch: `actual`/`target` vs `actual_output`/`target_output`) | Major | Fixed |
| E11-002 | General (pre-fix) | Production Scorecard not rendering due to wrong DB column names in API and schema/frontend field name mismatches | Critical | Fixed |

### Severity Definitions

- **Critical**: Blocks core functionality, cannot proceed
- **Major**: Significant issue but workaround exists
- **Minor**: Cosmetic or minor inconvenience

---

## Sign-off

### Testing Summary

| Metric | Value |
|--------|-------|
| Scenarios Tested | 9 / 9 |
| Scenarios Passed | 9 / 9 |
| Critical Issues | 1 (E11-002, fixed during session) |
| Major Issues | 1 (E11-001, fixed during session) |
| Minor Issues | 0 |

### Recommendation

☑ **Accept** - All criteria met, ready for production

### Signatures

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Tester (QA) | Dmitri Spiropoulos | 2026-02-21 | Dmitri Spiropoulos |
| Product Owner | | | |
| Tech Lead | | | |

---

## Appendix

### Test Data Reference

The seed data populates 14 assets across 4 workcenters with 7 days of production history:

| Workcenter | Assets | Expected T-1 Attainment |
|------------|--------|------------------------|
| Roasting | Roaster 1, Roaster 2, Roaster 3 | ~92% |
| Grinding | Grinder 1, Grinder 2, Grinder 3, Grinder 4, Grinder 5 | ~89% |
| Filling | Filler Line A, Filler Line B, Filler Line C | ~85% |
| Packaging | Packaging Line 1, Packaging Line 2, Packaging Line 3 | ~93% |

Each workcenter should have at least one asset that hit its target and at least one that missed, creating a realistic mix of green and red rows in the detail view.

### Environment Details

- **Frontend**: Next.js web application
- **API**: FastAPI backend with Supabase database
- **Endpoint**: `GET /api/v1/production/workcenter-summary?date=YYYY-MM-DD`
- **Default date**: Yesterday (T-1) when no date is specified

### Related Documentation

- Epic: `_bmad-output/planning-artifacts/epic-11.md`
- Stories: `_bmad-output/implementation-artifacts/stories/11-*.md`

---

*Generated by BMAD epic-execute workflow*
