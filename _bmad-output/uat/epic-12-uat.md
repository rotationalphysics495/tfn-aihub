# Products, Schedule & Attainment - User Acceptance Testing

**Epic**: 12
**Version**: 1.0
**Generated**: 2026-02-11
**Stories Covered**: 6

---

## Overview

### What Was Built

Plant managers can now upload a weekly production schedule (CSV or Excel file) and see whether the plant made the right products. The system compares what was scheduled against what was actually produced, showing schedule attainment percentages by product for each workcenter, highlighting product swaps (when a machine ran the wrong product), and displaying an overall product mix comparison chart on the morning report.

### Who Should Test

A **Plant Manager** or **Production Planner** who understands the daily production schedule and can recognize whether the displayed data makes sense for the plant's operations. No technical knowledge is required — only familiarity with the plant's products, workcenters, and scheduling process.

### Time Estimate

45–60 minutes

---

## Prerequisites

### Before You Begin

1. **Environment**
   - URL: Your staging/UAT environment URL (e.g., `https://uat.your-app-domain.com`)
   - Browser: Chrome (recommended) or Firefox

2. **Test Account**
   - Log in with a test account that has Plant Manager or Planner access
   - If no account exists, create one through the normal sign-up flow or request one from your administrator

3. **Test Data Setup**
   - Seed data should already be loaded, providing ~11 coffee manufacturing products (Colombian Single Origin, Brazilian Santos, Ethiopian Yirgacheffe, House Blend, Dark Roast Blend, Espresso Grind, Medium Grind, Coarse Grind, K-Cup, 12oz Bag, 5lb Bag)
   - If test data is missing, run the seed script:
     ```bash
     node scripts/seed-data.mjs
     ```
   - Prepare two test files for upload testing:
     - **Valid CSV file** — a `.csv` file with columns: `date`, `shift`, `asset_name`, `product_name`, `scheduled_quantity` (sample rows with dates within the next 7 days, known asset names like "Roaster 1", product names like "Colombian Single Origin", and positive quantities)
     - **Valid Excel file** — a `.xlsx` file with the same column structure as the CSV

4. **Clean State**
   - No special cleanup is required between test runs. Uploading a new schedule replaces existing schedule entries for the same dates.

---

## Test Scenarios

### Scenario 1: View Schedule Attainment on Morning Report

**Purpose**: Verify that the morning report displays schedule attainment data comparing what was scheduled vs. what was actually produced.

**Starting Point**: Logged in, on the home page or dashboard.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Click on "Morning Report" in the sidebar navigation | The morning report page loads |
| 2 | Scroll down past the summary section | A "Schedule Attainment" section is visible between the workcenter scorecard and the action items |
| 3 | Look at the Schedule Attainment section | Each workcenter area (Roasting, Grinding, Filling) is shown as a card |
| 4 | Review a workcenter card (e.g., Roasting) | The card shows: product names, scheduled quantities, actual quantities, and an attainment percentage for each product |
| 5 | Check the overall attainment percentage for a workcenter | A summary attainment percentage is displayed for the workcenter overall |

**Success Criteria**: The morning report shows a Schedule Attainment section with per-workcenter, per-product breakdown of scheduled vs. actual production including attainment percentages.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 2: Identify Product Swaps on Morning Report

**Purpose**: Verify that when a machine ran a different product than what was scheduled, the swap is clearly highlighted.

**Starting Point**: Logged in, viewing the morning report.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to the Morning Report | The morning report loads with the Schedule Attainment section |
| 2 | Look for variance callouts in the Roasting section | An amber/orange highlighted callout is visible (seed data includes a product swap on Roaster 1) |
| 3 | Read the callout text | The message clearly explains what happened, e.g., "Ran Colombian instead of scheduled Brazilian" or similar wording identifying the swapped products |
| 4 | Check that the callout is visually distinct | The swap callout uses amber/orange coloring that stands out from normal rows |

**Success Criteria**: Product swaps are highlighted in amber/orange with a clear, human-readable description of what was scheduled vs. what was actually produced.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 3: View Product Mix Comparison Chart

**Purpose**: Verify that a bar chart compares the planned vs. actual product mix visually.

**Starting Point**: Logged in, viewing the morning report.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Scroll to the Schedule Attainment section on the morning report | The section is visible |
| 2 | Look for a bar chart in the section | A grouped bar chart is displayed comparing planned vs. actual product mix |
| 3 | Review the chart bars | Each product shows two bars side by side — one for planned percentage and one for actual percentage |
| 4 | Check the chart legend | A legend identifies which color represents "Planned" and which represents "Actual" |
| 5 | Resize the browser window | The chart adjusts responsively to the new window size without breaking |

**Success Criteria**: A clear bar chart shows planned vs. actual product mix percentages with distinguishable colors and a legend.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 4: Navigate to Schedule Upload Page

**Purpose**: Verify that users can find and access the schedule upload page from the application navigation.

**Starting Point**: Logged in, on any page.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Look in the sidebar navigation under Settings | A "Schedule Upload" link is visible with an upload icon |
| 2 | Click the "Schedule Upload" link | The page at `/settings/schedule-upload` loads |
| 3 | Review the upload page | A drag-and-drop zone is displayed with text "Drop CSV or Excel file here" (or similar) and a "Browse Files" button |
| 4 | Verify accepted formats are shown | The page indicates accepted file types: `.csv` and `.xlsx` |

**Success Criteria**: The Schedule Upload page is accessible via sidebar navigation and presents a file upload zone with clear instructions.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 5: Upload a CSV Schedule File and Preview

**Purpose**: Verify that uploading a CSV file shows a preview of the data before committing it.

**Starting Point**: On the Schedule Upload page (`/settings/schedule-upload`) with a valid CSV file prepared.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Drag and drop a valid CSV file onto the upload zone (or click "Browse Files" and select the file) | The file is accepted and processing begins (a loading indicator appears) |
| 2 | Wait for the preview to load | A preview table appears showing all rows from the file |
| 3 | Review the preview table columns | Each row shows: row number, date, shift, asset name, product name, and scheduled quantity |
| 4 | Check matched assets | Assets that match existing workcenters (e.g., "Roaster 1") show a green checkmark |
| 5 | Check the summary statistics | The preview shows a count of total rows, matched assets, and any errors |
| 6 | Verify the "Confirm Upload" button is enabled | Since the file has no errors, the confirm button is clickable |

**Success Criteria**: A valid CSV file produces a preview table with matched asset indicators and a summary, with the confirm button enabled.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 6: Confirm Schedule Upload and Verify Success

**Purpose**: Verify that confirming an upload saves the data and provides success feedback.

**Starting Point**: On the Schedule Upload page with a valid file preview displayed (Scenario 5 completed).

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Click the "Confirm Upload" button | A loading indicator appears during processing |
| 2 | Wait for confirmation to complete | A success notification (toast) appears showing how many rows were inserted |
| 3 | Verify redirection | The application redirects to the Morning Report page |
| 4 | Check the morning report | The Schedule Attainment section now reflects the newly uploaded schedule data for the uploaded dates |

**Success Criteria**: Clicking confirm saves the schedule data, shows a success message with row count, and redirects to the morning report.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 7: Upload an Excel File

**Purpose**: Verify that Excel (.xlsx) files work the same as CSV files for schedule upload.

**Starting Point**: On the Schedule Upload page with a valid `.xlsx` file prepared.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Drag and drop an Excel (.xlsx) file onto the upload zone | The file is accepted and processing begins |
| 2 | Wait for the preview to load | A preview table appears with the same layout as a CSV preview |
| 3 | Verify the data matches the Excel content | Row data (dates, shifts, assets, products, quantities) matches what was in the spreadsheet |
| 4 | Click "Confirm Upload" | Data is saved with a success notification |

**Success Criteria**: Excel files produce the same preview and confirmation experience as CSV files.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

### Scenario 8: Handle No Schedule Data Gracefully

**Purpose**: Verify that the morning report handles dates with no uploaded schedule gracefully.

**Starting Point**: Logged in, morning report loaded for a date that has no schedule data uploaded.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to the Morning Report for a date with no schedule | The page loads normally without errors |
| 2 | Scroll to where the Schedule Attainment section would appear | Instead of attainment data, a helpful message is shown: "No schedule uploaded for this date" (or similar) |
| 3 | Look for an upload link | A link or button saying "Upload schedule" is displayed, pointing to the schedule upload page |
| 4 | Click the upload link | The browser navigates to `/settings/schedule-upload` |

**Success Criteria**: When no schedule exists for a date, the morning report shows a friendly prompt with a link to upload a schedule instead of an error or blank section.

**Result**: ☐ Pass  ☐ Fail

**Notes**: _________________________________

---

## Edge Cases & Error Handling

### Edge Case 1: Upload a File with an Unrecognized Asset Name

**Purpose**: Verify the system handles asset names that don't match existing workcenters.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Prepare a CSV file with an asset name like "Roaster 99" (does not exist) | — |
| 2 | Upload the file on the Schedule Upload page | The preview loads |
| 3 | Check the row with the unrecognized asset | The row is flagged with a red warning and shows suggested matches (e.g., "Roaster 1", "Roaster 2") |
| 4 | Check the "Confirm Upload" button | The button is disabled because there are unresolved errors |

**Result**: ☐ Pass  ☐ Fail

---

### Edge Case 2: Upload a File with Invalid Data

**Purpose**: Verify the system catches and reports validation errors clearly.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Prepare a CSV file with invalid data: a negative quantity (e.g., `-100`), an invalid date (e.g., `not-a-date`), and a missing product name | — |
| 2 | Upload the file on the Schedule Upload page | The preview loads |
| 3 | Check the rows with invalid data | Each invalid row is highlighted in red with a specific error message (e.g., "Quantity must be a positive number", "Invalid date format") |
| 4 | Check the "Confirm Upload" button | The button is disabled; the upload cannot proceed until errors are resolved |

**Result**: ☐ Pass  ☐ Fail

---

### Edge Case 3: Upload an Unsupported File Type

**Purpose**: Verify the system rejects files that are not CSV or Excel.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Attempt to upload a `.pdf` or `.txt` file on the Schedule Upload page | The file is rejected with a clear error message indicating only `.csv` and `.xlsx` files are accepted |
| 2 | Verify no preview table appears | The page remains in its initial upload state |

**Result**: ☐ Pass  ☐ Fail

---

### Edge Case 4: New Product Auto-Creation

**Purpose**: Verify that uploading a schedule with a product name that doesn't exist in the system creates the product automatically.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Prepare a CSV file containing a product name not in the system (e.g., "Decaf Blend Special") | — |
| 2 | Upload the file on the Schedule Upload page | The preview loads |
| 3 | Check the row with the new product name | The product is shown with a blue "will be created" indicator (not flagged as an error) |
| 4 | Click "Confirm Upload" | The upload succeeds, and the new product is automatically added to the system |

**Result**: ☐ Pass  ☐ Fail

---

## Success Criteria Summary

This epic is **successful** when a user can:

- [ ] See a Schedule Attainment section on the morning report showing scheduled vs. actual production by product per workcenter
- [ ] Identify product swaps through amber/orange highlighted callouts with clear descriptions
- [ ] View a product mix comparison bar chart showing planned vs. actual percentages
- [ ] Navigate to a Schedule Upload page via the sidebar
- [ ] Upload a CSV or Excel schedule file and see a preview before committing
- [ ] Confirm an upload and receive success feedback with a redirect to the morning report
- [ ] See a helpful "No schedule uploaded" prompt with an upload link when no data exists for a date
- [ ] See clear validation errors and disabled confirm button when an uploaded file has problems

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
| Edge Cases Tested | \_\_ / 4 |
| Edge Cases Passed | \_\_ / 4 |
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

**Products (from seed data):**
| Product | Family | Unit |
|---------|--------|------|
| Colombian Single Origin | Roasting | lbs |
| Brazilian Santos | Roasting | lbs |
| Ethiopian Yirgacheffe | Roasting | lbs |
| House Blend | Roasting | lbs |
| Dark Roast Blend | Roasting | lbs |
| Espresso Grind | Grinding | lbs |
| Medium Grind | Grinding | lbs |
| Coarse Grind | Grinding | lbs |
| K-Cup | Filling | units |
| 12oz Bag | Filling | units |
| 5lb Bag | Filling | units |

**Workcenters (assets):**
| Area | Assets |
|------|--------|
| Roasting | Roaster 1, Roaster 2, Roaster 3 |
| Grinding | Grinder 1, Grinder 2, Grinder 3, Grinder 4, Grinder 5 |
| Filling | Filler Line A, Filler Line B, Filler Line C |

**Sample CSV File for Upload Testing:**
```
date,shift,asset_name,product_name,scheduled_quantity
2026-02-12,Day,Roaster 1,Colombian Single Origin,130
2026-02-12,Night,Roaster 1,Colombian Single Origin,100
2026-02-12,Day,Grinder 1,Espresso Grind,1900
2026-02-12,Day,Filler Line A,K-Cup,4400
```

### Environment Details

- **Frontend**: Next.js application
- **Backend API**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL)
- **Schedule Upload API**: `POST /api/v1/schedule/upload` (preview), `POST /api/v1/schedule/upload/confirm` (commit)
- **Attainment API**: `GET /api/production/schedule-attainment?date=YYYY-MM-DD`

### Related Documentation

- Epic: `_bmad-output/planning-artifacts/epic-12.md`
- Stories: `_bmad-output/implementation-artifacts/stories/12-*.md`

---

*Generated by BMAD epic-execute workflow*
